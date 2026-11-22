"""Per-test Testmon dependencies on project config files and typed config leaves.

pytest-testmon tracks Python coverage. Its database also fingerprints any
other file a test's batch names, as one whole-file block, and selects the
test again when that file's content changes. This recorder names config in
that batch, so an edited YAML selects only the tests that consume it instead
of the whole inventory:

- a project ``config/*.yaml`` file opened while a test runs is a dependency of
  that test (the ``open`` audit event);
- a typed config leaf (``root.namespace.file.section``) read from the project
  package's ``config`` singleton is a dependency on that leaf's receipt, a
  one-line digest of its value that the controller refreshes before Testmon
  compares fingerprints, so an edit that leaves the value unchanged (a
  comment) selects nothing;
- a child process outside the declared config-insensitive programs reads
  config Testmon cannot observe, so its test depends on every config file.

A read during module-level code (an import, a class body, a parametrize
argument) belongs to every module on that import stack: Testmon already ties
each test to every project module it covers, so the module's tests receive the
read exactly as they receive the module's own top-level code. Any other read
outside a test (a collection hook) is a dependency of every test.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import sysconfig
from collections.abc import Callable, Mapping, MutableMapping
from hashlib import sha256
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesPytest,
)


class FlextInfraUtilitiesPytestConfigDependencies:
    """The runner's per-test config dependency recorder for pytest-testmon."""

    class ConfigDependencyRecorder:
        """Record config reads per test and name them in Testmon's batches."""

        def __init__(
            self,
            *,
            rootdir: Path,
            receipts: Path,
            insensitive: frozenset[str],
            controller: bool,
            executes: bool,
        ) -> None:
            self.rootdir = rootdir.resolve()
            self.receipts = receipts
            self.insensitive = insensitive
            self.controller = controller
            self.executes = executes
            self.excluded = tuple(
                Path(path).resolve()
                for key, path in sysconfig.get_paths().items()
                if key.endswith("lib")
            )
            self.sources: dict[str, str] = {}
            self.current: str | None = None
            self.armed = False
            self.by_test: dict[str, set[str]] = {}
            self.by_module: dict[str, set[str]] = {}
            self.common: set[str] = set()
            self.module_files: dict[str, str | None] = {}
            self.retained: tuple[p.BaseModel, ...] = ()
            self.observed: dict[
                type[p.BaseModel],
                Callable[[p.BaseModel, str], t.Infra.ConfigLeafValue] | None,
            ] = {}

        def bind(self) -> None:
            """Elect the config sources and leaves, then start observing reads."""
            root = self.receipts.parent
            layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
            package_dir = None if layout is None else layout.package_dir
            for directory in (root, *(() if package_dir is None else (package_dir,))):
                for source in sorted((directory / c.CONFIG_DIR_NAME).glob("*.yaml")):
                    self.sources[os.path.realpath(source)] = self.relative(source)
            if package_dir is not None and find_spec(package_dir.name) is not None:
                singleton = getattr(import_module(package_dir.name), "config", None)
                if not isinstance(singleton, p.BaseModel):
                    # A FLEXT package publishes its root as a lazy stand-in;
                    # the root's own fetch_global() publishes and returns it.
                    fetch = getattr(singleton, "fetch_global", None)
                    singleton = fetch() if callable(fetch) else None
                if isinstance(singleton, p.BaseModel):
                    self.observe(singleton)
            sys.addaudithook(self.audit)
            self.armed = True

        def unbind(self) -> None:
            """Stop observing; the process-wide audit hook stays inert."""
            self.armed = False
            for model, original in self.observed.items():
                if original is None:
                    del model.__getattribute__
                else:
                    model.__getattribute__ = original
            self.observed.clear()

        def relative(self, path: Path | str) -> str:
            """Return ``path`` as Testmon names it: relative to pytest's rootdir.

            Returns:
                The rootdir-relative path.

            """
            return os.path.relpath(Path(path).resolve(), self.rootdir)

        def observe(self, singleton: p.BaseModel) -> None:
            """Write one receipt per typed leaf and record reads of each leaf.

            Reads resolve through the singleton node's own path. Another
            instance of an observed model (a reloaded or test-built config)
            records the union of that model's leaves.
            """
            depth = c.Infra.PYTEST_CONFIG_RECEIPT_DEPTH
            leaves: dict[tuple[str, ...], str] = {}
            nodes: list[tuple[tuple[str, ...], p.BaseModel, dict[str, str]]] = []
            pending: list[tuple[tuple[str, ...], p.BaseModel]] = [((), singleton)]
            while pending:
                path, node = pending.pop()
                owned: dict[str, str] = {}
                nodes.append((path, node, owned))
                for name in type(node).model_fields:
                    key = (*path, name)
                    value = node.__dict__[name]
                    if isinstance(value, p.BaseModel) and len(key) < depth:
                        pending.append((key, value))
                        continue
                    owned[name] = leaves[key] = self.receipt(key, value)
            if self.controller:
                current = {self.receipts / Path(name).name for name in leaves.values()}
                suffix = c.Infra.PYTEST_CONFIG_RECEIPT_SUFFIX
                for stale in self.receipts.glob(f"*{suffix}"):
                    if stale not in current:
                        stale.unlink()
            reads: dict[int, t.Infra.ConfigLeafReads] = {}
            unions: dict[type[p.BaseModel], t.Infra.ConfigLeafReads] = {}
            for path, node, owned in nodes:
                whole = frozenset(
                    receipt
                    for key, receipt in leaves.items()
                    if key[: len(path)] == path
                )
                fields = {name: frozenset({receipt}) for name, receipt in owned.items()}
                reads[id(node)] = (fields, whole)
                union_fields, union_whole = unions.get(type(node), ({}, frozenset()))
                unions[type(node)] = (
                    {
                        name: union_fields.get(name, frozenset())
                        | fields.get(name, frozenset())
                        for name in union_fields.keys() | fields.keys()
                    },
                    union_whole | whole,
                )
            self.retained = tuple(node for _, node, _ in nodes)
            for model, union in unions.items():
                self.install(model, reads, union)

        def receipt(self, key: tuple[str, ...], value: t.Infra.ConfigLeafValue) -> str:
            """Refresh one leaf receipt in the controller and return its name.

            Returns:
                The receipt's rootdir-relative path.

            """
            path = self.receipts / (
                ".".join(key) + c.Infra.PYTEST_CONFIG_RECEIPT_SUFFIX
            )
            if self.controller:
                canonical = json.dumps(self.canonical(value), separators=(",", ":"))
                digest = sha256(canonical.encode()).hexdigest() + "\n"
                if not path.is_file() or path.read_text(encoding="utf-8") != digest:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(digest, encoding="utf-8")
            return self.relative(path)

        @classmethod
        def canonical(cls, value: t.Infra.ConfigLeafValue) -> t.JsonValue:
            """Return a hash-seed independent JSON form of one leaf value.

            Returns:
                The value with models as mappings, sets sorted and other
                scalars as their text.

            """
            match value:
                case p.BaseModel():
                    return {
                        name: cls.canonical(value.__dict__[name])
                        for name in type(value).model_fields
                    }
                case Mapping():
                    return {key: cls.canonical(item) for key, item in value.items()}
                case set() | frozenset():
                    return sorted(
                        (cls.canonical(item) for item in value),
                        key=json.dumps,
                    )
                case list() | tuple():
                    return [cls.canonical(item) for item in value]
                case str() | int() | float() | bool() | None:
                    return value
                case _:
                    return str(value)

        def install(
            self,
            model: type[p.BaseModel],
            reads: Mapping[int, t.Infra.ConfigLeafReads],
            union: t.Infra.ConfigLeafReads,
        ) -> None:
            """Record each read of an observed model's leaf fields."""
            original = model.__getattribute__
            record = self.record
            whole_reads = c.Infra.PYTEST_CONFIG_WHOLE_READS

            def observed(instance: p.BaseModel, name: str) -> t.Infra.ConfigLeafValue:
                value = original(instance, name)
                fields, whole = reads.get(id(instance), union)
                receipts = fields.get(name)
                if receipts is not None:
                    record(receipts)
                elif name in whole_reads:
                    record(whole)
                return value

            self.observed.setdefault(model, vars(model).get("__getattribute__"))
            model.__getattribute__ = observed

        def record(self, dependencies: frozenset[str], *, spawn: bool = False) -> None:
            """Attribute config dependencies to the test and import stack in effect."""
            if not self.armed:
                return
            modules = self.import_stack()
            for module in modules:
                self.by_module.setdefault(module, set()).update(dependencies)
            if self.current is not None:
                self.by_test.setdefault(self.current, set()).update(dependencies)
            elif not modules and not spawn:
                self.common.update(dependencies)

        def import_stack(self) -> tuple[str, ...]:
            """Return the project modules whose top-level code is executing.

            Returns:
                The rootdir-relative files of every executing ``<module>`` frame.

            """
            frame = inspect.currentframe()
            modules: list[str] = []
            while frame is not None:
                code = frame.f_code
                if code.co_name == "<module>":
                    module = self.module_file(code.co_filename)
                    if module is not None:
                        modules.append(module)
                frame = frame.f_back
            return tuple(modules)

        def module_file(self, filename: str) -> str | None:
            """Return a project source file's Testmon name, or None outside it.

            Returns:
                The rootdir-relative path of a project module, else None.

            """
            if filename not in self.module_files:
                path = Path(filename).resolve()
                inside = (
                    path.suffix == ".py"
                    and path.is_relative_to(self.rootdir)
                    and not any(path.is_relative_to(lib) for lib in self.excluded)
                )
                self.module_files[filename] = self.relative(path) if inside else None
            return self.module_files[filename]

        def audit(self, event: str, arguments: tuple[object, ...]) -> None:
            """Record config file opens and config-reading child processes."""
            if not self.armed:
                return
            if event == "open":
                target = arguments[0]
                if isinstance(target, (str, bytes, os.PathLike)):
                    name = os.fsdecode(target)
                    if name.endswith(".yaml"):
                        source = self.sources.get(os.path.realpath(name))
                        if source is not None:
                            self.record(frozenset({source}))
            elif (
                event in c.Infra.PYTEST_CONFIG_SPAWN_EVENTS
                and self.program(event, arguments) not in self.insensitive
            ):
                self.record(frozenset(self.sources.values()), spawn=True)

        @staticmethod
        def program(event: str, arguments: tuple[object, ...]) -> str:
            """Return the started program's basename, or empty when unknown.

            Returns:
                The executable basename, empty for shells and forks.

            """
            match event:
                case "subprocess.Popen" | "os.posix_spawn":
                    executable = arguments[0]
                case "os.spawn":
                    executable = arguments[1]
                case _:
                    return ""
            if isinstance(executable, (str, bytes, os.PathLike)):
                return Path(os.fsdecode(executable)).name
            return ""

        def pytest_runtest_logstart(self, nodeid: str) -> None:
            """Attribute reads from setup through teardown to the running test."""
            self.current = nodeid

        def pytest_runtest_logfinish(self) -> None:
            """End the running test's attribution after its teardown report."""
            self.current = None

        @FlextInfraUtilitiesPytest.Pytest.hookimpl(tryfirst=True)
        def pytest_runtest_logreport(self, report: t.Infra.Pytest.TestReport) -> None:
            """Name config dependencies in the batch Testmon attaches on teardown.

            Testmon attaches each flushed batch to the teardown report of the
            process that ran the tests: a worker sends it to the controller,
            a single process saves it in its own report hook. This hook runs
            first, in that process only, so the batch carries config too.
            """
            batch = report.__dict__.get("nodes_files_lines")
            if (
                not self.executes
                or report.when != "teardown"
                or not isinstance(batch, MutableMapping)
            ):
                return
            for nodeid, files in batch.items():
                if not isinstance(files, MutableMapping):
                    continue
                dependencies = set(self.common)
                dependencies.update(self.by_test.pop(nodeid, ()))
                for module in tuple(files):
                    dependencies.update(self.by_module.get(module, ()))
                for dependency in dependencies:
                    files.setdefault(dependency, {1})


__all__ = ["FlextInfraUtilitiesPytestConfigDependencies"]
