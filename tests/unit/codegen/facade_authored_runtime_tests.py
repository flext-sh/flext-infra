"""Generation preserves authored runtime outside declared family composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack, nullcontext
from pathlib import Path
from re import escape
from typing import Literal

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenGeneration
from tests import c, m, p, tm, u


class TestsFlextInfraFacadeAuthoredRuntime:
    """Exercise preservation through generation and a fresh public consumer."""

    @staticmethod
    @pytest.mark.parametrize("consume", [False, True])
    def test_capture_pins_originals_without_promoting_unused_inputs(
        tmp_path: Path,
        *,
        consume: bool,
    ) -> None:
        """Prefetch is not consumption; actual readers still get the original epoch."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        text = "__all__ = []\n"
        source.write_text(text, encoding=c.DEFAULT_ENCODING)
        expectation = (
            pytest.raises(ValueError, match=escape(str(source)))
            if consume
            else nullcontext()
        )
        with expectation, u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            with project.source_capture():
                original = project.source_state(source)
            tm.that(
                source in {state.path for state in project.consumed_source_states()},
                eq=False,
            )
            source.write_text(
                text + "# Changed after capture\n", encoding=c.DEFAULT_ENCODING
            )
            with project.source_consumption() as scope:
                if consume:
                    tm.that(project.source_text(source), eq=text)
            tm.that(scope.receipt().inputs, eq=(original,) if consume else ())

    @staticmethod
    @pytest.mark.parametrize("directory", [False, True])
    def test_negative_query_below_original_file_uses_native_ancestor_proof(
        tmp_path: Path,
        *,
        directory: bool,
    ) -> None:
        """Reject a file-to-directory change, not irrelevant ancestor file bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        expectation = (
            pytest.raises(ValueError, match=escape(str(source)))
            if directory
            else nullcontext()
        )
        with expectation, u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            with project.source_consumption() as scope:
                predicates: tuple[Literal["exists", "isfile", "isdir"], ...] = (
                    "exists",
                    "isfile",
                    "isdir",
                )
                for predicate in predicates:
                    tm.that(
                        project.source_query(source / "child.py", predicate), eq=False
                    )
            tm.that(scope.receipt().inputs, eq=())
            tm.that(
                any(
                    inventory.root.path == package
                    and (source.name, "isdir") in inventory.queries
                    for inventory in scope.receipt().source_directories
                ),
                eq=True,
            )
            if directory:
                source.unlink()
                source.mkdir()
            else:
                source.write_text(
                    "# Changed bytes, still not a directory\n",
                    encoding=c.DEFAULT_ENCODING,
                )

    @staticmethod
    def test_declared_retirement_and_binary_reads_keep_original_effect_inputs(
        tmp_path: Path,
    ) -> None:
        """Use the native selected view without restoring retired or binary bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        dependency = package / "dependency.py"
        binary = package / "opaque.bin"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        dependency.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        binary.write_bytes(b"\x00\xff")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        incoming = tm.ok(u.Cli.atomic_read_binary_file_state(dependency))
        opaque = tm.ok(u.Cli.atomic_read_binary_file_state(binary))
        plans = (
            m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=original,
                desired_content=None,
                desired_mode=None,
                source_states=(incoming,),
            ),
            m.Infra.CodegenFilePlan(
                project=root,
                path=binary,
                before=opaque,
                desired_content=b"\xff\x00",
                desired_mode=opaque.mode,
                source_states=(incoming,),
            ),
        )
        with u.Infra.facade_source_project(
            root, source_states=(original, incoming, opaque), declared_files=plans
        ) as binding:
            project = binding[0]
            with project.source_consumption() as scope:
                tm.that(project.source_query(source, "isfile"), eq=False)
                tm.that(source in project.source_children(package), eq=False)
                tm.that(project.source_bytes(binary), eq=b"\xff\x00")
            states = {state.path: state for state in scope.receipt().inputs}
            tm.that(states[source], eq=original)
            tm.that(states[dependency], eq=incoming)
            tm.that(states[binary], eq=opaque)
            with pytest.raises(FileNotFoundError, match="retired"):
                project.source_bytes(source)
        tm.that(binary.read_bytes(), eq=opaque.content)
        tm.that(source.read_bytes(), eq=original.content)

    @staticmethod
    def test_isolated_native_consumers_share_original_transitive_receipts(
        tmp_path: Path,
    ) -> None:
        """Warming one PyCore cannot hide provider reads from another artifact."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                "class Provider: pass\n__all__ = ['Provider']\n",
            ),
        )
        for name in ("first", "second"):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    package / f"{name}.py",
                    f"from {package.name}.provider import Provider\n"
                    "class Consumer(Provider): pass\n__all__ = ['Consumer']\n",
                ),
            )
        with u.Infra.facade_source_project(root) as (project, _, _):
            warmed = u.Infra.require_semantic_module(
                project.get_module(f"{package.name}.first"),
            )
            tm.that(
                len(warmed.get_attribute("Consumer").get_object().get_superclasses()),
                eq=1,
            )
            with (
                project.source_consumption() as first,
                project.source_consumer() as consumer,
            ):
                module = u.Infra.require_semantic_module(
                    consumer.get_module(f"{package.name}.first"),
                )
                tm.that(
                    len(
                        module.get_attribute("Consumer").get_object().get_superclasses()
                    ),
                    eq=1,
                )
            with (
                project.source_consumption() as second,
                project.source_consumer() as consumer,
            ):
                module = u.Infra.require_semantic_module(
                    consumer.get_module(f"{package.name}.second"),
                )
                tm.that(
                    len(
                        module.get_attribute("Consumer").get_object().get_superclasses()
                    ),
                    eq=1,
                )
            first_provider = tuple(
                state for state in first.receipt().inputs if state.path == provider
            )
            second_provider = tuple(
                state for state in second.receipt().inputs if state.path == provider
            )
            tm.that(len(first_provider), eq=1)
            tm.that(second_provider, eq=first_provider)
            with (
                project.source_consumption() as replayed,
                project.source_consumer() as consumer,
            ):
                consumer.replay_source_consumption(first.receipt())
            tm.that(replayed.receipt().inputs, eq=first.receipt().inputs)

    @staticmethod
    def test_source_scopes_retain_repeated_original_reads(tmp_path: Path) -> None:
        """A cache consumer receives the original bytes, never a cumulative delta."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        unrelated = package / "unrelated.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        tm.ok(u.Cli.atomic_write_text_file(unrelated, "__all__ = []\n"))
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as first:
                original = project.source_state(source)
            with project.source_consumption() as separate:
                project.source_state(unrelated)
            with project.source_consumption() as repeated:
                tm.that(project.source_state(source), eq=original)
            with project.source_consumption() as consumer:
                project.replay_source_consumption(first.receipt())
            tm.that(first.receipt().inputs, eq=(original,))
            tm.that(repeated.receipt().inputs, eq=(original,))
            tm.that(consumer.receipt().inputs, eq=(original,))
            tm.that(
                tuple(state.path for state in separate.receipt().inputs),
                eq=(unrelated,),
            )

    @staticmethod
    def test_source_scopes_keep_exact_negative_queries(tmp_path: Path) -> None:
        """Repeated misses do not inherit unrelated selectors or membership reads."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as first:
                tm.that(project.root.has_child("missing.py"), eq=False)
            with project.source_consumption():
                tm.that(project.root.has_child("other.py"), eq=False)
                project.root.get_children()
            with project.source_consumption() as repeated:
                tm.that(project.root.has_child("missing.py"), eq=False)
            with project.source_consumption() as cached:
                project.replay_source_consumption(first.receipt())
            for scope in (first, repeated, cached):
                inventories = tuple(
                    inventory
                    for inventory in scope.receipt().source_directories
                    if inventory.root.path == root
                )
                tm.that(len(inventories), eq=1)
                tm.that(inventories[0].queries, eq=(("missing.py", "exists"),))
                tm.that(inventories[0].membership_queried, eq=False)

    @staticmethod
    def test_source_scopes_reject_unissued_and_incomplete_receipts(
        tmp_path: Path,
    ) -> None:
        """A copied receipt and an unfinished consumer cannot authenticate a hit."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as scope:
                project.source_state(package / "absent.py", required=False)
                with pytest.raises(ValueError, match="no completed receipt"):
                    scope.receipt()
            with pytest.raises(ValueError, match="original epoch"):
                project.replay_source_consumption(scope.receipt().model_copy())
            with pytest.raises(ValueError, match="active consumer"):
                project.replay_source_consumption(scope.receipt())
            failure = RuntimeError("consumer failed")
            scopes: list[p.Infra.RopeSourceConsumption] = []

            def fail_consumer() -> None:
                with project.source_consumption() as failed:
                    scopes.append(failed)
                    project.source_state(package / "absent.py", required=False)
                    raise failure

            with pytest.raises(RuntimeError, match="consumer failed") as caught:
                fail_consumer()
            tm.that(caught.value is failure, eq=True)
            with pytest.raises(ValueError, match="no completed receipt"):
                scopes[0].receipt()

    @staticmethod
    def test_nested_source_scopes_propagate_original_receipts(tmp_path: Path) -> None:
        """Nested cache work belongs both to its own result and to its consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        with u.Infra.facade_source_project(root) as (project, _, _):
            with (
                project.source_consumption() as outer,
                project.source_consumption() as inner,
            ):
                project.source_state(source)
                tm.that(project.root.has_child("missing.py"), eq=False)
            tm.that(outer.receipt().inputs, eq=inner.receipt().inputs)
            tm.that(
                outer.receipt().source_directories,
                eq=inner.receipt().source_directories,
            )
            tm.that(
                outer.receipt().source_query_topology,
                eq=inner.receipt().source_query_topology,
            )

    @staticmethod
    def test_replayed_source_receipt_never_recaptures_changed_bytes(
        tmp_path: Path,
    ) -> None:
        """A replay retains old evidence and the epoch verifier rejects the edit."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            with project.source_consumption() as provider:
                original = project.source_state(source)
            tm.ok(u.Cli.atomic_write_text_file(source, "# Changed epoch\n"))
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
                tm.that(project.source_state(source), eq=original)
            tm.that(consumer.receipt().inputs, eq=(original,))
            with pytest.raises(ValueError, match="atomic source changed"):
                contexts.close()

    @staticmethod
    def test_identical_in_place_rewrite_keeps_source_epoch_valid(
        tmp_path: Path,
    ) -> None:
        """A byte-identical same-inode rewrite is not a divergent source change."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        content = "__all__ = []\n"
        tm.ok(u.Cli.atomic_write_text_file(source, content))
        inode_before = source.stat().st_ino
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as provider:
                original = project.source_state(source)
            with source.open("wb") as handle:
                handle.write(content.encode(c.DEFAULT_ENCODING))
            tm.that(source.stat().st_ino, eq=inode_before)
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
            tm.that(project.source_state(source), eq=original)
            tm.that(consumer.receipt().inputs, eq=(original,))

    @staticmethod
    def test_divergent_in_place_rewrite_fails_source_epoch(
        tmp_path: Path,
    ) -> None:
        """A genuinely divergent same-inode rewrite fails with content evidence."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))

        def diverge() -> None:
            with u.Infra.facade_source_project(root) as (project, _, _):
                with project.source_consumption() as provider:
                    expected = project.source_state(source)
                with source.open("wb") as handle:
                    handle.write(b"__all__ = ['diverged']\n")
                tm.that(source.stat().st_ino, eq=expected.inode)
                with project.source_consumption():
                    project.replay_source_consumption(provider.receipt())

        with pytest.raises(ValueError, match="atomic source changed") as rejected:
            diverge()
        tm.that("content_changed=True" in str(rejected.value), eq=True)

    @staticmethod
    def test_negative_query_receipts_keep_original_absent_topology(
        tmp_path: Path,
    ) -> None:
        """An absent candidate under an absent parent is guarded after replay."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        missing = root / "absent"
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            folder = project.get_folder(missing.relative_to(root).as_posix())
            with project.source_consumption() as provider:
                tm.that(folder.has_child("provider.py"), eq=False)
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
            witnesses = tuple(
                witness
                for witness in consumer.receipt().source_query_topology
                if witness.target == missing
            )
            tm.that(len(witnesses), eq=1)
            tm.that(witnesses[0].queries, eq=(("provider.py", "exists"),))
            missing.mkdir()
            tm.ok(
                u.Cli.atomic_write_text_file(
                    missing / "provider.py",
                    "__all__ = []\n",
                ),
            )
            with pytest.raises(ValueError, match="source directory"):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize("depth", [1, 2])
    @pytest.mark.parametrize("relative", [False, True])
    @pytest.mark.parametrize(
        "segment", ["child", "descriptive_namespace_for_deep_native_owner_projection"]
    )
    def test_generated_imports_preserve_relative_alias_levels(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        depth: int,
        segment: str,
        *,
        relative: bool,
    ) -> None:
        """Execute short own imports alongside ancestor and external imports."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        children = (segment,) * depth
        child = package.joinpath(*children)
        child.mkdir(parents=True)
        namespace = ".".join((package.name, *children))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "sibling.py",
                "SENTINEL = 'native-sibling'\n",
            )
        )
        provider = child / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(provider, "LOCAL_SENTINEL = 'native-child'\n")
        )
        imports = FlextInfraCodegenGeneration.generate_type_checking(
            {
                (
                    f"{'.' * (depth + 1)}sibling"
                    if relative
                    else f"{package.name}.sibling"
                ): (("sibling", ""),),
                "pathlib": (("Path", "Path"),),
                f"{namespace}.{provider.stem}": (("LOCAL_SENTINEL", "LOCAL_SENTINEL"),),
            },
            include_flext_types=False,
            local_package_root=namespace,
        )
        tm.that("\n".join(imports), has=f"from .{provider.stem} import LOCAL_SENTINEL")
        tm.ok(
            u.Cli.atomic_write_text_file(
                child / c.Infra.INIT_PY,
                "TYPE_CHECKING = True\n\n" + "\n".join(imports) + "\n",
            )
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pathlib\n"
            f"from {namespace} import LOCAL_SENTINEL, Path, sibling\n"
            "assert Path is pathlib.Path\n"
            "assert sibling.SENTINEL == 'native-sibling'\n"
            "assert LOCAL_SENTINEL == 'native-child'\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("generated_name", config.Infra.codegen.generated_sources)
    def test_generated_barrel_does_not_elect_an_authored_facade(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        generated_name: str,
    ) -> None:
        """Ignored generated providers remain importable without owning facades."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        generated = package / generated_name
        generated.mkdir()
        provider = generated / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                "class GeneratedProvider:\n"
                "    marker = 'native-provider'\n"
                "__all__ = ['GeneratedProvider']\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".gitignore",
                f"/{generated.relative_to(root).as_posix()}/\n",
            )
        )
        service = u.Tests.create_lazy_init_service(root)
        analysis = tm.ok(service.plan_files())
        with u.Infra.facade_source_project(
            root, declared_files=analysis.files
        ) as binding:
            project, consumed, sources = binding
            tm.that(any(path.is_relative_to(generated) for path in sources), eq=False)
            planned = {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                for file in analysis.files
                if file.path.suffix == c.Infra.EXT_PYTHON
                and file.desired_content is not None
            }
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    {**sources, **planned},
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
            tm.that(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                ),
                eq=None,
            )
            module = u.Infra.require_semantic_module(
                project.get_module(f"{package.name}.{generated.name}.{provider.stem}")
            )
            tm.not_none(module.get_attribute("GeneratedProvider").get_object())
            tm.that({state.path for state in consumed()[0]}, has=provider.resolve())
        tm.ok(u.Tests.materialize_lazy_init(service))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"provider = importlib.import_module("
            f"{f'{package.name}.{generated.name}.{provider.stem}'!r})\n"
            "assert provider.GeneratedProvider.marker == 'native-provider'\n",
            cwd=root,
        )

    @staticmethod
    def test_shared_source_project_keeps_native_stdlib_election(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """The authenticated graph resolves the interpreter's virtual stdlib."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                "from collections.abc import Mapping\n"
                "class Consumer(Mapping):\n"
                '    """Native stdlib inheritance contract."""\n'
                "__all__ = ['Consumer']\n",
            )
        )
        with u.Infra.facade_source_project(root) as binding:
            project, _, sources = binding
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    sources,
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from collections.abc import Mapping\n"
            f"from {package.name} import Consumer\n"
            "assert issubclass(Consumer, Mapping)\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("consumer_fails", [False, True])
    def test_source_epoch_failure_preserves_consumer_exception(
        tmp_path: Path,
        *,
        consumer_fails: bool,
    ) -> None:
        """Changed inputs reject success but never replace a consumer's exception."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(path, ""))
        failure = RuntimeError("consumer failed before source verification")

        def consume_changed_source() -> None:
            """Exercise one complete public source epoch."""
            with u.Infra.facade_source_project(root) as (project, _, _):
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                )
                tm.ok(u.Cli.atomic_write_text_file(path, "# Changed source epoch\n"))
                if consumer_fails:
                    raise failure

        with pytest.raises(
            RuntimeError if consumer_fails else ValueError,
            match=r"consumer failed|atomic source changed",
        ) as caught:
            consume_changed_source()
        tm.that(caught.value is failure, eq=consumer_fails)

    @staticmethod
    def test_declared_projection_preserves_authored_bindings(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Unrelated authored bindings keep working after the family is published."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "owner.py": (
                "class Owner:\n    marker = 'owner'\n__all__ = ['Owner']\n"
            ),
            package / family.directory / "support.py": (
                "class AuthoredSupport:\n"
                "    @staticmethod\n"
                "    def render(value):\n"
                "        return value.upper()\n"
                "__all__ = []\n"
            ),
            facade: (
                f"from {package.name}.{family.directory}.owner import Owner\n"
                f"from {package.name}.{family.directory}.support "
                "import AuthoredSupport\n"
                "def authored_value(value):\n"
                "    return AuthoredSupport.render(value)\n"
                "class Utilities(Owner):\n"
                "    @classmethod\n"
                "    def read(cls, value):\n"
                "        return authored_value(value) + ':' + cls.marker\n"
                "u = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            "assert u.read('value') == 'VALUE:owner'\n"
            "class Receiver(u):\n"
            "    marker = 'receiver'\n"
            "assert Receiver.read('value') == 'VALUE:receiver'\n",
            cwd=root,
        )

    @staticmethod
    def test_checkout_environment_is_never_a_planning_source(tmp_path: Path) -> None:
        """Dependency modules read from the checkout environment stay inputs only.

        Premise (70dc29f1b9 regression): the lazy-init plans carry every state
        their native reads consumed, including dependency modules installed in
        the checkout-local environment. Those states entered the planned-source
        map, so the facade planner treated the installed dependency as a
        project package and republished its facade inside the environment
        (cosmos-charts lost an importable flext_cli this way).
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        installed = (
            root
            / c.Infra.ENVIRONMENT_DIRECTORY
            / "lib"
            / "site-packages"
            / "flext_dependency"
        )
        files = {
            package / c.Infra.INIT_PY: "",
            installed / c.Infra.INIT_PY: "",
            installed / c.Infra.UTILITIES_PY: "class Dependency:\n    pass\n",
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in files
        )
        with u.Infra.facade_source_project(root, source_states=states) as binding:
            project, consumed, sources = binding
            project.get_pymodule(
                project.get_resource(
                    (installed / c.Infra.UTILITIES_PY).relative_to(root).as_posix()
                )
            )
            tm.that(
                {path.resolve() for path in sources},
                eq={(package / c.Infra.INIT_PY).resolve()},
            )
            tm.that(
                {state.path.resolve() for state in consumed()[0]},
                has=(installed / c.Infra.UTILITIES_PY).resolve(),
            )

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_planned_provider_export_precedes_native_consumer(
        native_consumer: p.Tests.NativeConsumer,
        installed_dependency_path: Path,
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """A stale live barrel never replaces the provider's planned export."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider = u.Tests.create_lazy_init_workspace(
            installed_dependency_path,
            project_name="provider_project",
            package_name="provider_package",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        barrel = provider / family.directory / c.Infra.INIT_PY
        barrel.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(barrel, ""))
        public_name = "ProviderBase" if declared else "OtherProviderBase"
        tm.ok(
            u.Cli.atomic_write_text_file(
                barrel.parent / "base.py",
                u.Tests.runtime_root_import() + f"class {public_name}(RuntimeRoot):\n"
                '    """Explicitly published empty protocol owner."""\n'
                f"__all__ = [{public_name!r}]\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                "class Consumer(ProviderBase):\n"
                '    """Consumer of the generated provider barrel."""\n'
                "__all__ = ['Consumer']\n",
            ),
        )
        provider_service = u.Tests.create_lazy_init_service(provider_root)
        provider_analysis = tm.ok(provider_service.plan_files())
        original_barrel = tm.ok(
            u.Cli.atomic_read_binary_file_state(barrel, required=True)
        )
        with ExitStack() as stack:
            stack.enter_context(tm.scope(python_paths=(str(provider.parent),)))
            if not declared:
                stack.enter_context(
                    pytest.raises(
                        u.Infra.rope_attribute_not_found_error_types(),
                        match="Attribute ProviderBase not found",
                    )
                )
            project, consumed, sources = stack.enter_context(
                u.Infra.facade_source_project(
                    root,
                    declared_files=provider_analysis.files,
                )
            )
            roots = u.Infra.runtime_evaluated_base_classes(
                root,
                sources,
                u.Tests.runtime_evaluated_roots(),
                source_project=project,
            )
            tm.that(
                roots,
                has=f"{provider.name}.{family.directory}.ProviderBase",
            )
            tm.that(
                {state.path for state in consumed()[0]},
                has=barrel.resolve(),
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(barrel, required=True)),
            eq=original_barrel,
        )
        if declared:
            with tm.scope(python_paths=(str(provider.parent),)):
                tm.ok(u.Tests.materialize_lazy_init(provider_service))
                tm.ok(
                    u.Tests.materialize_lazy_init(
                        u.Tests.create_lazy_init_service(root)
                    )
                )
            native_consumer(
                f"sys.path.insert(0, {str(provider.parent)!r})\n"
                f"sys.path.insert(0, {str(package.parent)!r})\n"
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                f"from {package.name} import Consumer\n"
                "assert ProviderBase.__module__ == "
                f"{f'{provider.name}.{family.directory}.base'!r}\n"
                "assert issubclass(Consumer, ProviderBase)\n",
                cwd=root,
            )
