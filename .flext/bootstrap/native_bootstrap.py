"""Own the stdlib-only cold import loader before framework initialization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import re
import shlex
import stat
import sys
import tomllib
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from email.parser import BytesParser
from importlib.machinery import (
    BuiltinImporter,
    ExtensionFileLoader,
    FrozenImporter,
    ModuleSpec,
    PathFinder,
    SourceFileLoader,
)
from pathlib import Path
from types import BuiltinMethodType, CodeType, MethodType, ModuleType
from typing import TYPE_CHECKING, ClassVar, override
from urllib.parse import unquote, urlsplit

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from datetime import date, datetime, time

    from flext_cli import m, p

_bootstrap_loader = sys.modules[__name__].__loader__
if _bootstrap_loader is not None and "get_code" in vars(_bootstrap_loader):
    _bootstrap_compiler = vars(_bootstrap_loader)["get_code"]
    if not (
        isinstance(_bootstrap_compiler, BuiltinMethodType)
        and _bootstrap_compiler.__name__ == "get"
        and type(_bootstrap_compiler.__self__) is dict
    ):
        msg = "native bootstrap compiler differs from its executed source"
        raise ImportError(msg)
    _bootstrap_code = _bootstrap_compiler(__name__)
    if not (
        type(_bootstrap_code) is CodeType
        and _bootstrap_code.co_filename == __file__
        and _bootstrap_code.co_name == "<module>"
    ):
        msg = "native bootstrap compiler differs from its physical module"
        raise ImportError(msg)
    del vars(_bootstrap_loader)["get_code"]
    del _bootstrap_code, _bootstrap_compiler
del _bootstrap_loader


type NativeValue = (
    str
    | int
    | float
    | bool
    | date
    | datetime
    | time
    | list[NativeValue]
    | dict[str, NativeValue]
    | None
)


class FlextInfraValidateNativeBootstrap:
    """Compile elected original bytes and retain their pre-execution receipts."""

    _roots: ClassVar[Mapping[str, Path]]
    _standard: ClassVar[Path]
    _packages: ClassVar[tuple[Path, ...]]
    _receipts: ClassVar[Mapping[Path, str]]
    _payloads: ClassVar[Mapping[Path, bytes]]
    _trace: ClassVar[MutableMapping[Path, str]]
    _atomic_ready: ClassVar[bool] = False
    _receipt_reader: ClassVar[Callable[[Path], p.Result[m.Cli.AtomicFileReceipt]]]
    _file_reader: ClassVar[
        Callable[
            [m.Cli.AtomicFileReceipt], AbstractContextManager[p.Cli.AtomicFileReader]
        ]
    ]
    _receipt_validator: ClassVar[Callable[[str], m.Cli.AtomicFileReceipt]]
    _record_columns: ClassVar[tuple[str, ...]] = ("path", "hash", "size")

    def __init__(self, consumer_root: Path, policy: Mapping[str, str]) -> None:
        """Bind one physical setup consumer and its existing declared policy."""
        self._consumer_root = consumer_root.resolve(strict=True)
        self._policy = policy

    @staticmethod
    def _selection_object(
        pairs: list[tuple[str, NativeValue]],
    ) -> dict[str, NativeValue]:
        """Reject duplicate JSON fields before a mapping can hide them.

        Returns:
            The original selection values indexed by their unique field names.

        Raises:
            ValueError: If one field occurs more than once.

        """
        result: dict[str, NativeValue] = {}
        for key, value in pairs:
            if key in result:
                msg = f"duplicate supplier selection field: {key}"
                raise ValueError(msg)
            result[key] = value
        return result

    @staticmethod
    def decode_additional_suppliers(value: str) -> tuple[Path, ...]:
        """Decode the explicit array without accepting empty strings or coercion.

        Returns:
            The original additional supplier paths in declared order.

        Raises:
            TypeError: If the decoded value is not a native array.
            ValueError: If an array member is not a nonempty path.

        """
        parsed: NativeValue = json.loads(value)
        if not isinstance(parsed, list):
            msg = "additional supplier roots must be a JSON array of nonempty paths"
            raise TypeError(msg)
        paths: list[Path] = []
        for item in parsed:
            if not isinstance(item, str) or not item:
                msg = "additional supplier roots must contain nonempty paths"
                raise ValueError(msg)
            paths.append(Path(item))
        return tuple(paths)

    @classmethod
    def decode_supplier_selection(
        cls,
        content: bytes,
    ) -> tuple[Path | None, tuple[Path, ...]]:
        """Decode only versioned elections; old receipts require explicit migration.

        Returns:
            The primary supplier and the complete ordered additional election.

        Raises:
            ValueError: If fields, version or absolute path values are invalid.

        """
        data: NativeValue = json.loads(
            content.decode("utf-8", errors="strict"),
            object_pairs_hook=cls._selection_object,
        )
        if not isinstance(data, dict) or set(data) != {
            "version",
            "primary",
            "additional",
        }:
            msg = "supplier selection requires exactly version, primary and additional"
            raise ValueError(msg)
        if type(data["version"]) is not int or data["version"] != 1:
            msg = "unsupported supplier selection version"
            raise ValueError(msg)
        primary = data["primary"]
        if primary is not None and (not isinstance(primary, str) or not primary):
            msg = "supplier selection primary must be a nonempty path or null"
            raise ValueError(msg)
        additional = cls.decode_additional_suppliers(json.dumps(data["additional"]))
        roots = (() if primary is None else (Path(primary),)) + additional
        if any(not path.is_absolute() for path in roots):
            msg = "supplier selection paths must be absolute"
            raise ValueError(msg)
        return (None if primary is None else Path(primary), additional)

    @staticmethod
    def encode_supplier_selection(
        primary: Path | None,
        additional: tuple[Path, ...],
    ) -> str:
        """Serialize the complete canonical election for atomic publication.

        Returns:
            The versioned selection document with its terminating newline.

        """
        return (
            json.dumps(
                {
                    "version": 1,
                    "primary": None if primary is None else str(primary),
                    "additional": [str(path) for path in additional],
                },
                separators=(",", ":"),
            )
            + "\n"
        )

    @classmethod
    def elect_suppliers(
        cls,
        consumer_root: Path,
        primary: str | None,
        additional: str | None,
        content: bytes | None,
        *,
        hosted: bool,
    ) -> tuple[Path | None, tuple[Path, ...]]:
        """Elect present fields over captured state before inspecting physical roots.

        Returns:
            The physical primary and additional suppliers, empty when hosted.

        Raises:
            ValueError: If roots are missing a primary, aliased or overlapping.

        """
        if hosted:
            return None, ()
        persisted = (
            (None, ())
            if (primary is not None and additional is not None) or content is None
            else cls.decode_supplier_selection(content)
        )
        selected = (
            persisted[0] if primary is None else Path(primary) if primary else None
        )
        extras = (
            persisted[1]
            if additional is None
            else cls.decode_additional_suppliers(additional)
        )
        if selected is None and extras:
            msg = (
                "additional suppliers require a primary; "
                "clear both settings to clear the election"
            )
            raise ValueError(msg)
        roots = (() if selected is None else (selected,)) + extras
        for index, path in enumerate(roots):
            if not path.is_absolute() or path != path.resolve(strict=True):
                msg = (
                    "supplier root must be an absolute physical nonaliased "
                    f"directory: {path}"
                )
                raise ValueError(msg)
            with os.scandir(path):
                pass
            if (
                path == consumer_root
                or path.is_relative_to(consumer_root)
                or consumer_root.is_relative_to(path)
            ):
                msg = f"supplier root overlaps consumer: {path}"
                raise ValueError(msg)
            if any(
                path == other
                or path.is_relative_to(other)
                or other.is_relative_to(path)
                for other in roots[:index]
            ):
                msg = f"duplicate or overlapping supplier root: {path}"
                raise ValueError(msg)
        return selected, extras

    @staticmethod
    def _distribution_name(name: str) -> str:
        """Apply the PEP 503 distribution-name equivalence rule.

        Args:
            name: The original distribution name.

        Returns:
            The normalized distribution name according to PEP 503.

        """
        return re.sub(r"[-_.]+", "-", name).lower()

    @staticmethod
    def _native_table(value: NativeValue) -> dict[str, NativeValue]:
        """Require a native parsed table without coercing malformed declarations.

        Args:
            value: The native value to check.

        Returns:
            The validated native table.

        Raises:
            TypeError: If the value is not a table.

        """
        if not isinstance(value, dict):
            msg = "native setup declaration must be a table"
            raise TypeError(msg)
        return value

    @staticmethod
    def _native_array(value: NativeValue) -> list[NativeValue]:
        """Require a native parsed array without coercion.

        Args:
            value: The native value to check.

        Returns:
            The validated native array.

        Raises:
            TypeError: If the value is not an array.

        """
        if not isinstance(value, list):
            msg = "native setup declaration must be an array"
            raise TypeError(msg)
        return value

    @staticmethod
    def _native_text(value: NativeValue) -> str:
        """Require a native string before using a declared identity or path.

        Args:
            value: The native value to check.

        Returns:
            The validated native string.

        Raises:
            TypeError: If the value is not a string.

        """
        if not isinstance(value, str):
            msg = "native setup declaration must be a string"
            raise TypeError(msg)
        return value

    @classmethod
    def _native_section(
        cls,
        value: dict[str, NativeValue],
        *keys: str,
    ) -> dict[str, NativeValue]:
        """Follow optional native tables while rejecting present non-table values.

        Args:
            value: The native table to check.
            *keys: The sequence of keys to follow.

        Returns:
            The final native table after following the keys.

        """
        for key in keys:
            value = cls._native_table(value.get(key, {}))
        return value

    @staticmethod
    def _native_document(path: Path) -> dict[str, NativeValue]:
        """Read native TOML and retain its original parser and filesystem causes.

        Args:
            path: The path to the TOML file.

        Returns:
            The parsed TOML document as a dictionary.

        """
        try:
            with path.open("rb") as stream:
                return tomllib.load(stream)
        except Exception as exc:
            exc.add_note(f"native setup declaration: {path}")
            raise

    @classmethod
    def _persisted_supplier(cls, selection_file: Path) -> bytes | None:
        """Read the strict receipt, retaining absence and all original read causes.

        Args:
            selection_file: The path to the selection file.

        Returns:
            Original selection bytes, or None if the file is absent.

        Raises:
            ValueError: If the selection file is aliased or not a regular file.

        """
        try:
            state = selection_file.lstat()
        except FileNotFoundError:
            return None
        if selection_file.absolute() != selection_file.resolve(strict=True):
            msg = f"aliased supplier selection file: {selection_file}"
            raise ValueError(msg)
        if not stat.S_ISREG(state.st_mode):
            msg = f"supplier selection is not a regular file: {selection_file}"
            raise ValueError(msg)
        try:
            return selection_file.read_bytes()
        except Exception as exc:
            exc.add_note(f"native supplier selection file: {selection_file}")
            raise

    def _effective_suppliers(
        self,
        supplier_root: str | None,
        *,
        hosted: bool,
    ) -> tuple[Path | None, tuple[Path, ...]]:
        """Resolve one present selection, preserving native directory failures.

        Args:
            supplier_root: The explicitly provided supplier root, if present.
            hosted: Whether the resolution is hosted.

        Returns:
            The physical primary and additional suppliers, empty when hosted.

        """
        if hosted:
            return None, ()
        raw = supplier_root
        supplier_environment = self._policy["supplier_environment"]
        if raw is None and supplier_environment in os.environ:
            raw = os.environ[supplier_environment]
        additional = os.environ.get(self._policy["additional_supplier_environment"])
        content = (
            None
            if raw is not None and additional is not None
            else self._persisted_supplier(
                self._consumer_root / self._policy["supplier_selection_file"]
            )
        )
        return self.elect_suppliers(
            self._consumer_root, raw, additional, content, hosted=False
        )

    def setup_selection(
        self,
        *,
        supplier_root: str | None = None,
        selection_output: str = "resolver",
    ) -> Path | str | None:
        """Elect one resolver; explicit presence, including empty, precedes state.

        Args:
            supplier_root: The explicitly provided supplier root, if present.
            selection_output: Resolver, primary supplier or additional JSON output.

        Returns:
            The selected path, absent primary, or canonical additional JSON array.

        Raises:
            ValueError: If the selection output is invalid or cannot be elected.

        """
        hosted = (
            os.environ.get(self._policy["hosted_variable"], "").strip()
            == self._policy["hosted_value"]
        )
        selected, additional = self._effective_suppliers(
            supplier_root,
            hosted=hosted,
        )
        if selection_output == "supplier":
            return selected
        if selection_output == "additional":
            return json.dumps([str(path) for path in additional], separators=(",", ":"))
        if selection_output != "resolver":
            msg_0 = f"invalid selection output: {selection_output!r}"
            raise ValueError(msg_0)
        if hosted:
            elected = self._policy["standalone_directory"]
        elif selected is not None:
            elected = self._policy["editable_directory"]
        else:
            elected = self._policy["local_directory"]
        return (self._consumer_root / elected).resolve(strict=True)

    @staticmethod
    def _supplier_paths(root: Path, module_records: Mapping[Path, bytes]) -> list[Path]:
        """Consume original host Git records bound to the actual composition marker.

        Returns:
            Native member paths from the original composition records.

        Raises:
            ValueError: If the records and original composition marker disagree.

        """
        modules = root / ".gitmodules"
        content = module_records[modules]
        try:
            state = modules.lstat()
        except FileNotFoundError as exc:
            if content:
                msg = f"Git records supplied for absent composition marker: {modules}"
                raise ValueError(msg) from exc
            return []
        if not stat.S_ISREG(state.st_mode):
            msg = f"composition marker is not a regular native file: {modules}"
            raise ValueError(msg)
        return FlextInfraValidateNativeBootstrap._module_paths(root, content)

    @staticmethod
    def _module_paths(root: Path, content: bytes) -> list[Path]:
        """Decode Git's NUL records and confine declared members to their owner.

        Returns:
            The original declared native member paths.

        Raises:
            ValueError: If records are malformed or a member escapes its owner.

        """
        if content and not content.endswith(b"\x00"):
            msg = (
                f"unterminated native Git configuration records: {root / '.gitmodules'}"
            )
            raise ValueError(msg)
        paths: list[Path] = []
        for entry in content.split(b"\x00")[:-1]:
            key, separator, value = entry.partition(b"\n")
            if key.startswith(b"submodule.") and key.endswith(b".path"):
                if not separator or not value:
                    msg = (
                        f"submodule path has no value: {root / '.gitmodules'}: {key!r}"
                    )
                    raise ValueError(msg)
                declared = Path(os.fsdecode(value))
                physical = (root / declared).resolve(strict=True)
                if (
                    declared.is_absolute()
                    or physical == root
                    or not physical.is_relative_to(root)
                ):
                    msg = (
                        "native Git member escapes composition owner: "
                        f"{root / '.gitmodules'}: {declared}"
                    )
                    raise ValueError(msg)
                paths.append(root / declared)
        return paths

    @classmethod
    def _workspace_paths(
        cls,
        root: Path,
        document: dict[str, NativeValue],
    ) -> list[Path]:
        """Expand native workspace membership and exclusions without name heuristics.

        Returns:
            Native member paths after the declared exclusions.

        """
        workspace = cls._native_section(document, "tool", "uv", "workspace")
        excluded = {
            path.resolve(strict=True)
            for pattern in cls._native_array(workspace.get("exclude", []))
            for path in root.glob(cls._native_text(pattern))
        }
        return [
            path
            for pattern in cls._native_array(workspace.get("members", []))
            for path in root.glob(cls._native_text(pattern))
            if path.resolve(strict=True) not in excluded
        ]

    @classmethod
    def _package_name(cls, path: Path) -> str | None:
        """Read one declared package, preserving non-Python Git members.

        Returns:
            Its normalized distribution name, or no name for non-packages.

        """
        with os.scandir(path):
            pass
        manifest = path / "pyproject.toml"
        try:
            manifest.stat()
        except FileNotFoundError:
            return None
        data = cls._native_document(manifest)
        name = cls._native_section(data, "project").get("name")
        if (
            name is None
            or cls._native_section(data, "tool", "uv").get("package") is False
        ):
            return None
        return cls._distribution_name(cls._native_text(name))

    @classmethod
    def _native_packages(
        cls,
        root: Path,
        module_records: Mapping[Path, bytes],
        *,
        supplier: bool,
    ) -> dict[str, Path]:
        """Derive packages from native Git composition or UV workspace membership.

        Returns:
            Distribution identities bound to their original physical roots.

        Raises:
            ValueError: If one identity declares competing physical roots.

        """
        root = root.resolve(strict=True)
        document = cls._native_document(root / "pyproject.toml")
        git_members = cls._supplier_paths(root, module_records)
        members = git_members if supplier else cls._workspace_paths(root, document)
        packages: dict[str, Path] = {}
        paths = [root, *members]
        for path in paths:
            name = cls._package_name(path)
            if name is None:
                continue
            physical = path.resolve(strict=True)
            if name in packages and packages[name] != physical:
                msg_0 = (
                    f"ambiguous native distribution {name}: "
                    f"{packages[name]}: {physical}"
                )
                raise ValueError(msg_0)
            packages[name] = physical
        return packages

    def _check_setup_election(
        self,
        *,
        supplier_root: Path | None,
        additional_supplier_roots: tuple[Path, ...],
        resolution_root: Path,
    ) -> None:
        """Compare supplied inputs with the independent physical election.

        Raises:
            ValueError: If any input differs from the physical selected resolver.

        """
        hosted = (
            os.environ.get(self._policy["hosted_variable"], "").strip()
            == self._policy["hosted_value"]
        )
        selected, extras = self._effective_suppliers(
            None,
            hosted=hosted,
        )
        directory = (
            self._policy["standalone_directory"]
            if hosted
            else self._policy["editable_directory"]
            if selected is not None
            else self._policy["local_directory"]
        )
        elected_resolver = (self._consumer_root / directory).resolve(strict=True)
        if (
            supplier_root != selected
            or additional_supplier_roots != extras
            or resolution_root != elected_resolver
            or not elected_resolver.is_relative_to(self._consumer_root)
        ):
            msg = "native setup inputs differ from the independent physical election"
            raise ValueError(msg)

    def _setup_packages(
        self,
        supplier_root: Path | None,
        additional_supplier_roots: tuple[Path, ...],
        module_records: Mapping[Path, bytes],
    ) -> dict[str, Path]:
        """Authenticate native package owners and standalone additional suppliers.

        Returns:
            Distribution identities bound to their selected physical packages.

        Raises:
            ValueError: If an additional supplier has a marker or competing name.

        """
        owned = self._native_packages(
            self._consumer_root, module_records, supplier=False
        )
        expected = (
            self._native_packages(supplier_root, module_records, supplier=True)
            if supplier_root is not None
            else owned
        )
        expected = {name: owned.get(name, path) for name, path in expected.items()}
        expected.update(owned)
        for root in additional_supplier_roots:
            marker = root / ".gitmodules"
            try:
                marker.lstat()
            except FileNotFoundError:
                pass
            else:
                msg = (
                    "additional supplier must be standalone without a composition "
                    f"marker: {marker}"
                )
                raise ValueError(msg)
            name = self._package_name(root)
            if name is None or name in expected:
                msg = (
                    "additional supplier has an absent or competing distribution: "
                    f"{root}: {name}"
                )
                raise ValueError(msg)
            expected[name] = root
        control = self._distribution_name(self._policy["control_distribution"])
        if control in owned:
            expected[control] = owned[control]
        return expected

    @classmethod
    def _native_requirement_demand(
        cls,
        requirement: str,
    ) -> tuple[str, tuple[str, ...]]:
        """Project only the original requirement's name and requested extra names.

        Bounds, URLs and conditional markers stay opaque for native UV. This is
        not a PEP 508 evaluator and never derives demands from resolver inputs.

        Returns:
            Normalized distribution and requested extras.

        Raises:
            ValueError: If a native name/extra projection cannot be proved.

        """
        match = re.match(
            r"\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)"
            r"(?:\s*\[([^\]]*)\])?\s*(?=$|[(@<>=!~;])",
            requirement,
        )
        if match is None:
            msg = f"cannot prove native dependency demand: {requirement!r}"
            raise ValueError(msg)
        extras: list[str] = []
        if match[2] is not None:
            for item in match[2].split(","):
                extra = item.strip()
                if (
                    re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", extra)
                    is None
                ):
                    msg = f"cannot prove native dependency extra: {requirement!r}"
                    raise ValueError(msg)
                extras.append(cls._distribution_name(extra))
        return cls._distribution_name(match[1]), tuple(extras)

    @classmethod
    def _native_requirement_lines(
        cls,
        document: dict[str, NativeValue],
        *,
        development: bool,
        extras: set[str] | None,
    ) -> list[str]:
        """Select original PEP package declarations under the native view roles.

        Returns:
            Runtime declarations and selected optional/development declarations.

        Raises:
            ValueError: If dynamic declarations or group references are unprovable.

        """
        project = cls._native_section(document, "project")
        dynamic = cls._native_array(project.get("dynamic", []))
        if any(
            cls._native_text(item) in {"dependencies", "optional-dependencies"}
            for item in dynamic
        ):
            msg = "cannot prove supplier reachability from dynamic dependencies"
            raise ValueError(msg)
        lines = [
            cls._native_text(item)
            for item in cls._native_array(project.get("dependencies", []))
        ]
        optional = cls._native_section(project, "optional-dependencies")
        for name, entries in optional.items():
            if extras is None or cls._distribution_name(name) in extras:
                lines.extend(
                    cls._native_text(item) for item in cls._native_array(entries)
                )
        if development:
            groups = cls._native_section(document, "dependency-groups")
            for entries in groups.values():
                for entry in cls._native_array(entries):
                    if isinstance(entry, str):
                        lines.append(entry)
                    elif (
                        isinstance(entry, dict)
                        and set(entry) == {"include-group"}
                        and cls._native_text(entry["include-group"]) in groups
                    ):
                        # Every consumer group is already selected by --all-groups.
                        continue
                    else:
                        msg = f"cannot prove native dependency group entry: {entry!r}"
                        raise ValueError(msg)
        return lines

    def _require_supplier_reachability(
        self,
        expected: Mapping[str, Path],
        extra_names: set[str],
    ) -> None:
        """Reject extras not demanded by original consumer/supplier declarations.

        All consumer groups/extras seed the graph. Only selected supplier runtime
        dependencies and requested extras extend it, matching the typed view.
        Conditional markers are retained for UV, not evaluated as host filters.

        Raises:
            ValueError: If an elected extra is outside the original closure.

        """
        consumer_paths = {
            self._consumer_root,
            *(
                path
                for path in expected.values()
                if path.is_relative_to(self._consumer_root)
            ),
        }
        declarations = {
            path: self._native_document(path / "pyproject.toml")
            for path in {*consumer_paths, *expected.values()}
        }
        demands: dict[str, set[str]] = {}
        pending = [
            line
            for path in consumer_paths
            for line in self._native_requirement_lines(
                declarations[path], development=True, extras=None
            )
        ]
        expanded: dict[str, frozenset[str]] = {}
        while pending:
            name, requested = self._native_requirement_demand(pending.pop())
            demands.setdefault(name, set()).update(requested)
            if name not in expected or expected[name] in consumer_paths:
                continue
            selected = frozenset(demands[name])
            if expanded.get(name) == selected:
                continue
            expanded[name] = selected
            pending.extend(
                self._native_requirement_lines(
                    declarations[expected[name]],
                    development=False,
                    extras=set(selected),
                )
            )
        if not extra_names.issubset(expanded):
            msg = (
                "elected additional suppliers are not reachable from original "
                f"consumer dependencies: {sorted(extra_names - expanded.keys())}"
            )
            raise ValueError(msg)

    def setup_inputs(
        self,
        *,
        supplier_root: Path | None,
        additional_supplier_roots: tuple[Path, ...],
        resolution_root: Path,
        module_records: Mapping[Path, bytes],
    ) -> Path | None:
        """Authenticate every supplier-capable native manifest and lock binding.

        Returns:
            The selected control package root, if it is an editable package.

        Raises:
            ValueError: If the selected control package or its lock entry is absent.

        """
        self._check_setup_election(
            supplier_root=supplier_root,
            additional_supplier_roots=additional_supplier_roots,
            resolution_root=resolution_root,
        )
        control_distribution = self._policy["control_distribution"]
        expected = self._setup_packages(
            supplier_root, additional_supplier_roots, module_records
        )
        extra_names = {
            name for name, path in expected.items() if path in additional_supplier_roots
        }
        self._require_supplier_reachability(expected, extra_names)
        control = self._distribution_name(control_distribution)
        manifest, lock = self._setup_documents(
            supplier_root,
            resolution_root,
            additional_supplier_roots,
        )
        manifest_path = resolution_root / "pyproject.toml"
        lock_path = resolution_root / "uv.lock"
        sources = self._manifest_sources(manifest, manifest_path)
        if supplier_root is not None and control not in expected:
            msg = (
                "control distribution has no selected native package: "
                f"{control_distribution}"
            )
            raise ValueError(msg)
        consumer_document = self._native_document(
            self._consumer_root / "pyproject.toml"
        )
        consumer_name = self._native_text(
            self._native_section(consumer_document, "project")["name"]
        )
        virtual = (
            self._distribution_name(
                consumer_name + self._policy["virtual_distribution_suffix"]
            ),
            resolution_root,
        )
        bound = self._manifest_bindings(sources, expected, manifest_path)
        present = self._lock_bindings(lock, bound, expected, lock_path, virtual)
        if not extra_names.issubset(present & bound):
            msg = (
                "elected additional supplier lacks its manifest and locked editable: "
                f"{sorted(extra_names - (present & bound))}"
            )
            raise ValueError(msg)
        if control not in present:
            msg = (
                "control distribution absent from lock: "
                f"{lock_path}: {control_distribution}"
            )
            raise ValueError(msg)
        self._lock_edges(lock, expected, lock_path, virtual, control)
        return expected.get(control)

    def _setup_documents(
        self,
        supplier_root: Path | None,
        resolution_root: Path,
        additional_supplier_roots: tuple[Path, ...],
    ) -> tuple[dict[str, NativeValue], dict[str, NativeValue]]:
        """Attach preparation instructions to the original missing-input exceptions.

        Returns:
            The original native resolution manifest and lock document.

        Raises:
            FileNotFoundError: If an input is absent, retaining preparation notes.

        """
        manifest_path = resolution_root / "pyproject.toml"
        lock_path = resolution_root / "uv.lock"
        try:
            manifest = self._native_document(manifest_path)
        except FileNotFoundError as exc:
            exc.add_note(
                "explicit generation required before setup: make gen "
                f"(consumer {self._consumer_root}; resolver {resolution_root})"
            )
            raise
        try:
            lock = self._native_document(lock_path)
        except FileNotFoundError as exc:
            command = "make upg"
            if supplier_root is not None:
                additional = json.dumps([
                    str(path) for path in additional_supplier_roots
                ])
                command = (
                    f"{self._policy['supplier_environment']}="
                    f"{shlex.quote(str(supplier_root))} "
                    f"{self._policy['additional_supplier_environment']}="
                    f"{shlex.quote(additional)} {command}"
                )
                exc.add_note(
                    "the editable resolution lock is runtime-local "
                    "and must NOT be committed"
                )
            exc.add_note(
                f"explicit lock preparation required before setup: {command} "
                f"(consumer {self._consumer_root}; resolver {resolution_root})"
            )
            raise
        return manifest, lock

    @classmethod
    def _manifest_sources(
        cls,
        manifest: dict[str, NativeValue],
        manifest_path: Path,
    ) -> dict[str, NativeValue]:
        """Normalize native source keys once and reject ambiguous declarations.

        Returns:
            The original source declarations indexed by normalized identity.

        Raises:
            ValueError: If normalization would merge competing declarations.

        """
        sources = cls._native_section(manifest, "tool", "uv", "sources")
        normalized_sources: dict[str, NativeValue] = {}
        for name, value in sources.items():
            normalized = cls._distribution_name(name)
            if normalized in normalized_sources:
                msg_0 = f"ambiguous manifest distribution: {manifest_path}: {name}"
                raise ValueError(msg_0)
            normalized_sources[normalized] = value
        return normalized_sources

    @classmethod
    def _manifest_bindings(
        cls,
        sources: dict[str, NativeValue],
        expected: Mapping[str, Path],
        manifest_path: Path,
    ) -> set[str]:
        """Authenticate every selected conditional manifest editable binding.

        Returns:
            Distribution identities with authenticated editable declarations.

        Raises:
            ValueError: If a selected distribution has no valid editable binding.

        """
        bound: set[str] = set()
        for name, declarations in sources.items():
            variants: NativeValue = (
                [declarations] if isinstance(declarations, dict) else declarations
            )
            if not variants:
                msg_0 = f"missing editable manifest binding: {manifest_path}: {name}"
                raise ValueError(msg_0)
            for value in cls._native_array(variants):
                declaration = cls._native_table(value)
                path = declaration.get("path")
                if name not in expected:
                    if (
                        path is not None
                        or declaration.get("editable") is True
                        or declaration.get("workspace") is True
                    ):
                        msg = (
                            "unauthorized local manifest binding: "
                            f"{manifest_path}: {name}: {declaration!r}"
                        )
                        raise ValueError(msg)
                    continue
                if (
                    path is None
                    and declaration.get("editable") is not True
                    and declaration.get("workspace") is not True
                ):
                    continue
                if declaration.get("editable") is not True or not isinstance(path, str):
                    msg_0 = (
                        "noneditable manifest binding: "
                        f"{manifest_path}: {name}: {declaration!r}"
                    )
                    raise ValueError(msg_0)
                cls._editable_path(
                    manifest_path.parent,
                    path,
                    expected[name],
                    manifest_path,
                    name,
                )
                bound.add(name)
        return bound

    @classmethod
    def _locked_control_source(
        cls,
        package: dict[str, NativeValue],
        lock_path: Path,
    ) -> None:
        """Require the native noneditable control source and its locked identity.

        Raises:
            ValueError: If the source, Git identity or locked version is absent.
            TypeError: If the locked version is not native text.

        """
        source = cls._native_section(package, "source")
        if set(source) not in ({"git"}, {"registry"}):
            msg = f"unprovable native control source: {lock_path}: {package!r}"
            raise ValueError(msg)
        location = urlsplit(cls._native_text(next(iter(source.values()))))
        if not location.scheme or not location.netloc:
            msg = f"invalid native control source: {lock_path}: {source!r}"
            raise ValueError(msg)
        if "git" in source and not location.fragment:
            msg = f"Git control source has no locked commit: {lock_path}: {source!r}"
            raise ValueError(msg)
        version = package.get("version")
        if version is None or not isinstance(version, str):
            msg = (
                f"native control source has no locked version: {lock_path}: {package!r}"
            )
            if version is None:
                raise ValueError(msg)
            raise TypeError(msg)

    def _lock_bindings(
        self,
        lock: dict[str, NativeValue],
        bindings: set[str],
        expected: Mapping[str, Path],
        lock_path: Path,
        virtual: tuple[str, Path],
    ) -> set[str]:
        """Validate package identities without conflating legitimate name forks.

        Returns:
            The distribution identities present in the authenticated lock.

        Raises:
            ValueError: If a selected package lacks its original editable binding.

        """
        control = self._distribution_name(self._policy["control_distribution"])
        present: set[str] = set()
        for value in self._native_array(lock.get("package", [])):
            package = self._native_table(value)
            name = self._distribution_name(self._native_text(package["name"]))
            if name == control and name not in expected:
                self._locked_control_source(package, lock_path)
                present.add(name)
            if name not in expected:
                source = self._native_section(package, "source")
                if name == virtual[0] and set(source) == {"virtual"}:
                    self._editable_path(
                        lock_path.parent,
                        self._native_text(source["virtual"]),
                        virtual[1],
                        lock_path,
                        name,
                    )
                    continue
                if any(
                    key in source
                    for key in ("editable", "path", "directory", "virtual")
                ):
                    msg = (
                        "unauthorized local lock binding: "
                        f"{lock_path}: {name}: {source!r}"
                    )
                    raise ValueError(msg)
                continue
            source = self._native_section(package, "source")
            if name != control and not any(
                key in source for key in ("editable", "path", "directory", "virtual")
            ):
                continue
            present.add(name)
            if name not in bindings:
                msg_0 = (
                    "missing editable manifest binding: "
                    f"{lock_path.parent / 'pyproject.toml'}: {name}: {expected[name]}"
                )
                raise ValueError(msg_0)
            source = self._native_section(package, "source")
            if set(source) != {"editable"}:
                msg_0 = f"noneditable lock binding: {lock_path}: {name}: {source!r}"
                raise ValueError(msg_0)
            self._editable_path(
                lock_path.parent,
                self._native_text(source["editable"]),
                expected[name],
                lock_path,
                name,
            )
        return present

    @classmethod
    def _lock_edge(
        cls,
        value: dict[str, NativeValue],
        expected: Mapping[str, Path],
        lock_path: Path,
        virtual: tuple[str, Path],
        control: str,
    ) -> None:
        """Authenticate one qualified native edge, including its copied source.

        Args:
            value: The native value representing the edge.
            expected: A mapping of expected distribution names to paths.
            lock_path: The path to the lock file being validated.
            virtual: The elected virtual distribution identity and physical resolver.
            control: The normalized control distribution identity.

        Raises:
            ValueError: If the edge does not conform to the expected structure.

        """
        name = value.get("name")
        if not isinstance(name, str):
            return
        normalized = cls._distribution_name(name)
        if normalized not in expected:
            source = cls._native_table(value["source"]) if "source" in value else {}
            if (
                normalized == virtual[0]
                and set(source) == {"virtual"}
                and not any(
                    key in value for key in ("editable", "path", "directory", "virtual")
                )
            ):
                cls._editable_path(
                    lock_path.parent,
                    cls._native_text(source["virtual"]),
                    virtual[1],
                    lock_path,
                    name,
                )
                return
            if any(
                key in value or key in source
                for key in ("editable", "path", "directory", "virtual")
            ):
                msg = f"unauthorized local lock edge: {lock_path}: {value!r}"
                raise ValueError(msg)
            return
        for key in ("editable", "path", "directory", "virtual"):
            if key not in value:
                continue
            if key != "editable":
                msg = f"noneditable lock edge: {lock_path}: {value!r}"
                raise ValueError(msg)
            cls._editable_path(
                lock_path.parent,
                cls._native_text(value[key]),
                expected[normalized],
                lock_path,
                name,
            )
        if "source" in value:
            cls._lock_edge_source(value, expected, lock_path, name, control)

    @classmethod
    def _lock_edge_source(
        cls,
        value: dict[str, NativeValue],
        expected: Mapping[str, Path],
        lock_path: Path,
        name: str,
        control: str,
    ) -> None:
        """Authenticate a copied source after the edge's direct bindings.

        Raises:
            ValueError: If the copied source is foreign or noneditable.

        """
        normalized = cls._distribution_name(name)
        source = cls._native_table(value["source"])
        if not any(
            key in source for key in ("editable", "path", "directory", "virtual")
        ):
            if normalized == control:
                msg = f"foreign control lock edge: {lock_path}: {value!r}"
                raise ValueError(msg)
            return
        if set(source) != {"editable"}:
            msg = f"foreign lock edge: {lock_path}: {value!r}"
            raise ValueError(msg)
        cls._editable_path(
            lock_path.parent,
            cls._native_text(source["editable"]),
            expected[normalized],
            lock_path,
            name,
        )

    @classmethod
    def _lock_edges(
        cls,
        value: NativeValue,
        expected: Mapping[str, Path],
        lock_path: Path,
        virtual: tuple[str, Path],
        control: str,
    ) -> None:
        """Visit native edge copies and conditional forks, retaining full identities.

        Args:
            value: The native value representing edges.
            expected: A mapping of expected distribution names to paths.
            lock_path: The path to the lock file being validated.
            virtual: The elected virtual distribution identity and physical resolver.
            control: The normalized control distribution identity.

        """
        if isinstance(value, list):
            for item in value:
                cls._lock_edges(item, expected, lock_path, virtual, control)
        elif isinstance(value, dict):
            cls._lock_edge(value, expected, lock_path, virtual, control)
            for item in value.values():
                cls._lock_edges(item, expected, lock_path, virtual, control)

    @staticmethod
    def _editable_path(
        root: Path, value: str, expected: Path, declaration: Path, name: str
    ) -> None:
        """Compare physical editable paths without discarding native failures.

        Args:
            root: The root directory for the editable path.
            value: The relative path value from the lock file.
            expected: The expected resolved path.
            declaration: The path to the lock file declaring the editable path.
            name: The name of the distribution.

        Raises:
            ValueError: If the resolved path does not match the expected path.

        """
        actual = (root / value).resolve(strict=True)
        if actual != expected:
            msg_0 = (
                f"foreign editable binding: {declaration}: {name}: "
                f"{root / value}: expected {expected}"
            )
            raise ValueError(msg_0)

    def setup_producer(
        self,
        *,
        supplier_root: Path | None,
        additional_supplier_roots: tuple[Path, ...],
        resolution_root: Path,
        environment_root: Path,
        module_records: Mapping[Path, bytes],
    ) -> None:
        """Check passive control evidence and stop at the unproved startup boundary.

        Native UV can consume existing startup before installation. Independent
        startup authority remains open in algar-723.1.2.1; this method deliberately
        cannot report a successful setup from metadata and module election alone.

        Raises:
            ValueError: If startup reaches an unproved implementation boundary.
            ImportError: If the installed module resolves to another source.

        """
        expected = self.setup_inputs(
            supplier_root=supplier_root,
            additional_supplier_roots=additional_supplier_roots,
            resolution_root=resolution_root,
            module_records=module_records,
        )
        if expected is None:
            msg = (
                "implementation boundary: noneditable control startup admission "
                "is not yet proved"
            )
            raise ValueError(msg)
        environment = environment_root.absolute()
        site = self._environment_site(self._consumer_root, environment)
        control_distribution = self._policy["control_distribution"]
        control_module = self._policy["control_module"]
        metadata = self._installed_control(site, control_distribution)
        direct_path = self._control_editable(metadata, expected, control_distribution)
        records = self._control_records(site, metadata, environment)
        for required in (direct_path, metadata / "METADATA"):
            if required.resolve() not in records:
                msg = f"missing control RECORD entry: {metadata / 'RECORD'}: {required}"
                raise ValueError(msg)
        search = self._pointer_paths(site, records, expected)
        declared_paths = self._declared_paths(expected)
        if not control_module or not all(
            part.isidentifier() for part in control_module.split(".")
        ):
            msg = f"invalid control module identity: {control_module!r}"
            raise ValueError(msg)
        actual = self._elect_module(control_module, search)
        wanted = self._elect_module(control_module, declared_paths)
        if (
            actual.origin is None
            or wanted.origin is None
            or Path(actual.origin).resolve(strict=True)
            != Path(wanted.origin).resolve(strict=True)
        ):
            msg = (
                f"foreign native control election: {control_module}: "
                f"{actual.origin}: expected {wanted.origin}"
            )
            raise ImportError(msg)
        msg = (
            "implementation boundary: native environment startup admission "
            "is not yet proved"
        )
        raise ValueError(msg)

    @staticmethod
    def _environment_site(consumer_root: Path, environment: Path) -> Path:
        """Prove the physical consumer environment and its native site directory.

        Args:
            consumer_root: The root directory of the consumer.
            environment: The path to the consumer environment.

        Returns:
            The path to the native site-packages directory.

        Raises:
            ValueError: If the environment is aliased, foreign, or misconfigured.

        """
        if environment != environment.resolve(strict=True):
            msg_0 = f"aliased consumer environment: {environment}"
            raise ValueError(msg_0)
        if not environment.is_relative_to(consumer_root.resolve(strict=True)):
            msg_0 = f"foreign consumer environment: {environment}"
            raise ValueError(msg_0)
        configuration = (environment / "pyvenv.cfg").read_text(encoding="utf-8")
        if re.search(
            r"(?im)^include-system-site-packages\s*=\s*true\s*$", configuration
        ):
            msg_0 = (
                f"system site packages cannot be proved: {environment / 'pyvenv.cfg'}"
            )
            raise ValueError(msg_0)
        sites = sorted(environment.glob("lib/python*/site-packages"))
        if len(sites) != 1:
            msg_0 = (
                "cannot elect one native site-packages directory: "
                f"{environment}: {sites}"
            )
            raise ValueError(msg_0)
        site = sites[0]
        if site != site.resolve(strict=True):
            msg_0 = f"aliased consumer site-packages: {site}"
            raise ValueError(msg_0)
        return site

    @classmethod
    def _installed_control(cls, site: Path, control_distribution: str) -> Path:
        """Elect exactly one native installed control metadata directory.

        Args:
            site: The path to the native site-packages directory.
            control_distribution: The name of the control distribution.

        Returns:
            The path to the installed control metadata directory.

        Raises:
            ValueError: If control metadata is ambiguous or foreign.

        """
        matches: list[Path] = []
        for metadata in sorted(site.glob("*.dist-info")):
            payload = (metadata / "METADATA").read_bytes()
            names = BytesParser().parsebytes(payload).get_all("Name")
            if names is None or len(names) != 1:
                msg_0 = f"ambiguous distribution name: {metadata / 'METADATA'}"
                raise ValueError(msg_0)
            if cls._distribution_name(names[0]) == cls._distribution_name(
                control_distribution
            ):
                matches.append(metadata)
        if len(matches) != 1:
            msg_0 = (
                "expected one installed control distribution: "
                f"{control_distribution}: {matches}"
            )
            raise ValueError(msg_0)
        metadata = matches[0]
        if not metadata.resolve(strict=True).is_relative_to(site):
            msg_0 = f"foreign control metadata directory: {metadata}"
            raise ValueError(msg_0)
        return metadata

    @classmethod
    def _control_editable(
        cls,
        metadata: Path,
        expected: Path,
        control_distribution: str,
    ) -> Path:
        """Authenticate PEP 610 editable control metadata without executing it.

        Args:
            metadata: The path to the control metadata directory.
            expected: The expected path to the editable control directory.
            control_distribution: The name of the control distribution.

        Returns:
            The path to the direct URL JSON file.

        Raises:
            ValueError: If control metadata is not a valid native editable directory.

        """
        direct_path = metadata / "direct_url.json"
        direct = cls._native_table(json.loads(direct_path.read_bytes()))
        url = urlsplit(cls._native_text(direct["url"]))
        if (
            url.scheme != "file"
            or any((url.netloc, url.query, url.fragment))
            or cls._native_section(direct, "dir_info").get("editable") is not True
            or "vcs_info" in direct
            or "archive_info" in direct
        ):
            msg_0 = (
                f"control is not a native editable directory: {direct_path}: {direct!r}"
            )
            raise ValueError(msg_0)
        directory = unquote(url.path, errors="strict")
        if not Path(directory).is_absolute():
            msg_0 = f"relative editable direct URL: {direct_path}: {direct['url']!r}"
            raise ValueError(msg_0)
        cls._editable_path(
            Path("/"), directory, expected, direct_path, control_distribution
        )
        return direct_path

    @staticmethod
    def _record_content(row: list[str], path: Path, record_path: Path) -> None:
        """Verify the exact bytes described by one native installed RECORD row.

        Args:
            row: A list representing one row from the RECORD file.
            path: The path to the installed file corresponding to the RECORD row.
            record_path: The path to the RECORD file.

        Raises:
            ValueError: If the RECORD row or its content cannot be authenticated.

        """
        if not row[1] or not row[2]:
            msg = f"unverifiable RECORD entry: {record_path}: {path}"
            raise ValueError(msg)
        algorithm, separator, digest = row[1].partition("=")
        if not separator:
            msg = f"invalid RECORD digest: {record_path}: {path}"
            raise ValueError(msg)
        content = path.read_bytes()
        actual = (
            base64
            .urlsafe_b64encode(hashlib.new(algorithm, content).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        if actual != digest or len(content) != int(row[2]):
            msg = f"installed RECORD mismatch: {record_path}: {path}"
            raise ValueError(msg)

    @classmethod
    def _control_records(
        cls,
        site: Path,
        metadata: Path,
        environment: Path,
    ) -> set[Path]:
        """Authenticate unique physical installed RECORD paths and their bytes.

        Args:
            site: The path to the native site-packages directory.
            metadata: The path to the control metadata directory.
            environment: The path to the environment root.

        Returns:
            A set of paths corresponding to the authenticated installed RECORD entries.

        Raises:
            ValueError: If any RECORD row is invalid, foreign, or duplicated.

        """
        records: set[Path] = set()
        record_path = metadata / "RECORD"
        for row in csv.reader(io.StringIO(record_path.read_text(encoding="utf-8"))):
            if len(row) != len(cls._record_columns):
                msg_0 = f"invalid RECORD row: {record_path}: {row!r}"
                raise ValueError(msg_0)
            path = (site / row[0]).resolve(strict=True)
            if not path.is_relative_to(environment):
                msg_0 = f"foreign installed RECORD path: {record_path}: {path}"
                raise ValueError(msg_0)
            if path in records:
                msg_0 = f"duplicate RECORD path: {record_path}: {path}"
                raise ValueError(msg_0)
            records.add(path)
            if path == record_path.resolve():
                continue
            cls._record_content(row, path, record_path)
        return records

    @staticmethod
    def _pointer_paths(site: Path, records: set[Path], expected: Path) -> list[str]:
        """Read native path data, failing explicitly on unproved executable startup.

        Args:
            site: The path to the native site-packages directory.
            records: A set of authenticated installed RECORD paths.
            expected: The expected path for editable control directories.

        Returns:
            A list of paths to be used for module search.

        Raises:
            ValueError: If startup code or editable pointers cannot be proved.

        """
        search = [str(site)]
        for pointer in sorted(site.glob("*.pth")):
            for line in pointer.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#"):
                    continue
                if line.startswith(("import ", "import\t")):
                    msg_0 = (
                        "implementation boundary: executable .pth cannot be proved "
                        f"without execution: {pointer}"
                    )
                    raise ValueError(msg_0)
                path = (site / line.rstrip()).resolve(strict=True)
                if pointer.resolve() in records and not path.is_relative_to(expected):
                    msg_0 = (
                        f"foreign control editable pointer: {pointer}: "
                        f"{path}: expected {expected}"
                    )
                    raise ValueError(msg_0)
                search.append(str(path))
        return search

    @staticmethod
    def _elect_module(control_module: str, paths: list[str]) -> ModuleSpec:
        """Use native PathFinder without importing package initializers.

        Returns:
            The native specification of the elected module.

        Raises:
            ModuleNotFoundError: If a module or one of its package parents is absent.

        """
        parts = control_module.split(".")
        spec = None
        for index in range(1, len(parts) + 1):
            name = ".".join(parts[:index])
            spec = PathFinder.find_spec(name, paths)
            if spec is None:
                msg = f"native setup module has no elected origin: {name}: {paths}"
                raise ModuleNotFoundError(msg, name=name)
            if index < len(parts):
                if spec.submodule_search_locations is None:
                    msg = f"native setup parent is not a package: {name}: {spec.origin}"
                    raise ModuleNotFoundError(msg, name=name)
                paths = list(spec.submodule_search_locations)
        if spec is None:
            msg = (
                f"native setup module has no elected origin: {control_module}: {paths}"
            )
            raise ModuleNotFoundError(msg, name=control_module)
        return spec

    @classmethod
    def _declared_paths(cls, expected: Path) -> list[str]:
        """Derive import roots only from the selected package's declared mapping.

        Returns:
            The original physical source roots declared by the selected package.

        Raises:
            ValueError: If mappings are absent, remapped or outside the owner.

        """
        declared = cls._native_document(expected / "pyproject.toml")
        wheel = cls._native_section(
            declared, "tool", "hatch", "build", "targets", "wheel"
        )
        mappings = wheel.get("sources")
        if not isinstance(mappings, dict) or not mappings:
            msg_0 = (
                "implementation boundary: no declared native wheel source mapping: "
                f"{expected / 'pyproject.toml'}"
            )
            raise ValueError(msg_0)
        declared_paths: list[str] = []
        for source, destination in mappings.items():
            source_path = expected / source
            destination_parts = Path(cls._native_text(destination)).parts
            if (
                destination_parts
                and tuple(source_path.parts[-len(destination_parts) :])
                != destination_parts
            ):
                msg_0 = (
                    "implementation boundary: remapped native package source: "
                    f"{source}: {destination}"
                )
                raise ValueError(msg_0)
            for _ in destination_parts:
                source_path = source_path.parent
            physical_source = source_path.resolve(strict=True)
            if not physical_source.is_relative_to(expected):
                msg_0 = (
                    f"foreign declared native source: {expected / 'pyproject.toml'}: "
                    f"{physical_source}"
                )
                raise ValueError(msg_0)
            declared_paths.append(str(physical_source))
        return declared_paths

    @classmethod
    def _worker_policy(cls) -> dict[str, str]:
        """Validate the generated policy transport without supplying policy defaults.

        Returns:
            The existing policy fields with their original native text values.

        Raises:
            ValueError: If a declared policy field is missing or an extra is present.

        """
        data = cls._native_table(json.loads(os.environ["FLEXT_INFRA_SETUP_POLICY"]))
        keys = (
            "local_directory",
            "editable_directory",
            "standalone_directory",
            "supplier_selection_file",
            "bootstrap_artifact",
            "control_distribution",
            "control_module",
            "virtual_distribution_suffix",
            "hosted_variable",
            "hosted_value",
            "supplier_environment",
            "additional_supplier_environment",
        )
        if set(data) != set(keys):
            msg = "native setup policy transport has missing or undeclared fields"
            raise ValueError(msg)
        return {key: cls._native_text(data[key]) for key in keys}

    @staticmethod
    def _record_file(path: Path) -> bytes:
        """Read the explicitly supplied host output without following a file alias.

        Returns:
            The original host command output bytes.

        Raises:
            ValueError: If the supplied path is not an absolute regular file.

        """
        state = path.lstat()
        if not path.is_absolute() or not stat.S_ISREG(state.st_mode):
            msg = f"native Git output is not an absolute regular file: {path}"
            raise ValueError(msg)
        return path.read_bytes()

    @classmethod
    def _module_records(
        cls,
        consumer: Path,
        supplier: Path | None,
    ) -> Mapping[Path, bytes]:
        """Bind host Git output to the consumer and elected supplier markers.

        Returns:
            Original host output bytes indexed by their composition marker.

        """
        inputs = [(consumer, "FLEXT_INFRA_SETUP_CONSUMER_GIT_CONFIG")]
        if supplier is not None:
            inputs.append((supplier, "FLEXT_INFRA_SETUP_SUPPLIER_GIT_CONFIG"))
        return {
            root / ".gitmodules": cls._record_file(Path(os.environ[variable]))
            for root, variable in inputs
        }

    @classmethod
    def main(cls) -> int:
        """Run the private setup data worker using only the declared environment ABI.

        Returns:
            Zero when the requested private setup operation succeeds.

        Raises:
            ValueError: If arguments, phase or supplied roots violate the declared ABI.

        """
        if len(sys.argv) != 1:
            msg = "native setup data worker does not accept command-line arguments"
            raise ValueError(msg)
        policy = cls._worker_policy()
        consumer = Path(os.environ["RUNTIME_ROOT"])
        if not consumer.is_absolute():
            msg = f"native runtime root must be absolute: {consumer}"
            raise ValueError(msg)
        worker = cls(consumer, policy)
        consumer = worker._consumer_root
        phase = os.environ["FLEXT_INFRA_SETUP_PHASE"]
        if phase == "selection":
            output = os.environ.get("FLEXT_INFRA_SETUP_OUTPUT", "resolver")
            selected = worker.setup_selection(selection_output=output)
            sys.stdout.write(("" if selected is None else str(selected)) + "\n")
            return 0
        if phase not in {"inputs", "producer"}:
            msg = f"invalid native setup phase: {phase!r}"
            raise ValueError(msg)
        hosted = (
            os.environ.get(policy["hosted_variable"], "").strip()
            == policy["hosted_value"]
        )
        supplier, additional = worker._effective_suppliers(
            None,
            hosted=hosted,
        )
        records = cls._module_records(consumer, supplier)
        resolution = Path(os.environ["FLEXT_INFRA_SETUP_RESOLUTION"])
        if not resolution.is_absolute():
            msg = f"native setup resolution root must be absolute: {resolution}"
            raise ValueError(msg)
        if phase == "inputs":
            worker.setup_inputs(
                supplier_root=supplier,
                additional_supplier_roots=additional,
                resolution_root=resolution,
                module_records=records,
            )
        else:
            worker.setup_producer(
                supplier_root=supplier,
                additional_supplier_roots=additional,
                resolution_root=resolution,
                environment_root=Path(os.environ["UV_PROJECT_ENVIRONMENT"]),
                module_records=records,
            )
        return 0

    @staticmethod
    def source_code(loader: SourceFileLoader, fullname: str) -> CodeType:
        """Authenticate source through the native loader before module execution.

        Returns:
            Code compiled from the authenticated original bytes.

        Raises:
            ImportError: If the elected source has no byte payload.

        """
        filename = loader.get_filename(fullname)
        content = FlextInfraValidateNativeBootstrap.before_load(
            fullname, filename, source=True
        )
        if content is None:
            msg = f"native source compilation has no pinned payload: {fullname}"
            raise ImportError(msg)
        code = loader.source_to_code(content, filename, _optimize=sys.flags.optimize)
        del vars(loader)["get_code"]
        return code

    @staticmethod
    def extension_module(loader: ExtensionFileLoader, spec: ModuleSpec) -> ModuleType:
        """Authenticate an extension before invoking its original native creation.

        Returns:
            The original native extension module.

        """
        FlextInfraValidateNativeBootstrap.before_load(
            spec.name, loader.path, source=False
        )
        del vars(loader)["create_module"]
        return loader.create_module(spec)

    class Finder(PathFinder):
        """Elect the original source or native supplier before loading it."""

        @classmethod
        @override
        def find_spec(
            cls,
            fullname: str,
            path: Sequence[str] | None = None,
            target: ModuleType | None = None,
        ) -> ModuleSpec:
            """Retain native builtin and frozen imports and authenticate file loads.

            Returns:
                The native import specification with its authenticated loader.

            Raises:
                ImportError: If a module has no authenticated loader or source.
                ModuleNotFoundError: If no native import specification exists.

            """
            native = BuiltinImporter.find_spec(fullname)
            if native is not None:
                return native
            native = FrozenImporter.find_spec(fullname)
            if native is not None:
                return native
            native = PathFinder.find_spec(fullname, path, target)
            if native is None:
                msg = f"native import has no elected module: {fullname}"
                raise ModuleNotFoundError(msg, name=fullname)
            owner = FlextInfraValidateNativeBootstrap
            if native.origin is None:
                if native.submodule_search_locations is None:
                    msg = (
                        "native module has neither source nor namespace portions: "
                        f"{fullname}"
                    )
                    raise ImportError(msg)
                for portion in native.submodule_search_locations:
                    owner.source_path(fullname, portion)
                return native
            owner.source_path(fullname, native.origin)
            if type(native.loader) is SourceFileLoader:
                vars(native.loader)["get_code"] = MethodType(
                    owner.source_code, native.loader
                )
            elif type(native.loader) is ExtensionFileLoader:
                vars(native.loader)["create_module"] = MethodType(
                    owner.extension_module, native.loader
                )
            else:
                msg = f"native source loader cannot prove compilation: {fullname}"
                raise ImportError(msg)
            return native

    @classmethod
    def install(
        cls,
        roots: Mapping[str, Path],
        standard_library: tuple[Path, tuple[Path, ...]],
        *,
        receipts: Mapping[Path, str],
        payloads: Mapping[Path, bytes],
        trace: MutableMapping[Path, str],
    ) -> None:
        """Bind the original authenticated inputs without copying their storage."""
        cls._roots = roots
        cls._standard, cls._packages = standard_library
        cls._receipts = receipts
        cls._payloads = payloads
        cls._trace = trace
        cls._atomic_ready = False
        sys.meta_path.insert(0, cls.Finder)

    @classmethod
    def enable_atomic_reader(
        cls,
        receipt_reader: Callable[[Path], p.Result[m.Cli.AtomicFileReceipt]],
        file_reader: Callable[
            [m.Cli.AtomicFileReceipt], AbstractContextManager[p.Cli.AtomicFileReader]
        ],
        receipt_validator: Callable[[str], m.Cli.AtomicFileReceipt],
    ) -> None:
        """Complete bootstrap only after the canonical reader imports under guard."""
        cls._receipt_reader = receipt_reader
        cls._file_reader = file_reader
        cls._receipt_validator = receipt_validator
        cls._atomic_ready = True

    @classmethod
    def source_path(cls, fullname: str, filename: str) -> Path:
        """Elect the physical source within its original provider.

        Returns:
            The original absolute path, without changing its import identity.

        Raises:
            ImportError: If the path belongs to no elected source provider.

        """
        path = Path(filename).absolute()
        physical = path.resolve()
        root = cls._roots.get(fullname.partition(".")[0])
        if root is not None:
            allowed = (
                physical.is_relative_to(root.resolve())
                if root.is_dir()
                else physical == root.resolve()
            )
        else:
            allowed = physical.is_relative_to(cls._standard) and not any(
                physical.is_relative_to(package) for package in cls._packages
            )
        if not allowed:
            msg = f"source has no elected physical provider: {fullname}: {path}"
            raise ImportError(msg)
        return path

    @classmethod
    def before_load(cls, fullname: str, filename: str, *, source: bool) -> bytes | None:
        """Record the original receipt before consuming or compiling its bytes.

        Returns:
            Pinned source bytes, or no payload for a native extension.

        Raises:
            ImportError: If a source is absent, changed or not pinned for bootstrap.

        """
        path = cls.source_path(fullname, filename)
        if not cls._atomic_ready:
            if path not in cls._receipts or (source and path not in cls._payloads):
                msg = f"source is not pinned before atomic-reader bootstrap: {path}"
                raise ImportError(msg)
            encoded = cls._receipts[path]
            content = cls._payloads[path] if source else None
        else:
            receipt = cls._receipt_reader(path).unwrap()
            previous = cls._trace.get(path, cls._receipts.get(path))
            if previous is not None and (receipt != cls._receipt_validator(previous)):
                msg = f"native source changed before compilation: {path}"
                raise ImportError(msg)
            encoded = receipt.model_dump_json()
            content = None
            if source:
                if receipt.size is None:
                    msg = f"native source receipt has no size: {path}"
                    raise ImportError(msg)
                with cls._file_reader(receipt) as reader:
                    content = reader.read_range(0, receipt.size)
        cls._trace[path] = encoded
        return content


if __name__ == "__main__":
    raise SystemExit(FlextInfraValidateNativeBootstrap.main())
