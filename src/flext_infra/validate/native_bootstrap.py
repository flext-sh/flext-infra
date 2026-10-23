"""Own the stdlib-only cold import loader before framework initialization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tomllib
import traceback
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from datetime import date, datetime, time
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
    str | int | float | bool | None | date | datetime | time
    | list[NativeValue] | dict[str, NativeValue]
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

    @staticmethod
    def decode_supplier_selection(content: bytes) -> Path | None:
        """Decode the one-line receipt without consulting environment or disk."""
        text = content.decode("utf-8", errors="strict")
        if (
            not text.endswith("\n")
            or text.count("\n") != 1
            or "\r" in text
            or "\x00" in text
        ):
            msg_0 = "supplier selection must contain exactly one UTF-8 LF line"
            raise ValueError(msg_0)
        value = text[:-1]
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute():
            msg_0 = f"supplier selection is not an absolute path: {value!r}"
            raise ValueError(msg_0)
        return path

    @staticmethod
    def distribution_name(name: str) -> str:
        """Apply the PEP 503 distribution-name equivalence rule."""
        return re.sub(r"[-_.]+", "-", name).lower()

    @staticmethod
    def native_table(value: NativeValue) -> dict[str, NativeValue]:
        """Require a native parsed table without coercing malformed declarations."""
        if not isinstance(value, dict):
            msg = "native setup declaration must be a table"
            raise TypeError(msg)
        return value

    @staticmethod
    def native_array(value: NativeValue) -> list[NativeValue]:
        """Require a native parsed array without coercion."""
        if not isinstance(value, list):
            msg = "native setup declaration must be an array"
            raise TypeError(msg)
        return value

    @staticmethod
    def native_text(value: NativeValue) -> str:
        """Require a native string before using a declared identity or path."""
        if not isinstance(value, str):
            msg = "native setup declaration must be a string"
            raise TypeError(msg)
        return value

    @classmethod
    def native_section(
        cls, value: dict[str, NativeValue], *keys: str,
    ) -> dict[str, NativeValue]:
        """Follow optional native tables while rejecting present non-table values."""
        for key in keys:
            value = cls.native_table(value.get(key, {}))
        return value

    @staticmethod
    def native_document(path: Path) -> dict[str, NativeValue]:
        """Read native TOML and retain its original parser and filesystem causes."""
        try:
            with path.open("rb") as stream:
                return tomllib.load(stream)
        except Exception as exc:
            exc.add_note(f"native setup declaration: {path}")
            raise

    @classmethod
    def persisted_supplier(cls, selection_file: Path) -> Path | None:
        """Read the strict receipt, retaining absence and all original read causes."""
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
            return cls.decode_supplier_selection(selection_file.read_bytes())
        except Exception as exc:
            exc.add_note(f"native supplier selection file: {selection_file}")
            raise

    @classmethod
    def effective_supplier(
        cls, consumer_root: Path, supplier_root: str | None,
        supplier_environment: str, selection_file: Path, *, hosted: bool,
    ) -> Path | None:
        """Resolve one present selection, preserving native directory failures."""
        if hosted:
            return None
        raw = supplier_root
        if raw is None and supplier_environment in os.environ:
            raw = os.environ[supplier_environment]
        selected = cls.persisted_supplier(selection_file) if raw is None else Path(raw) if raw else None
        if selected is None:
            return None
        if not selected.is_absolute():
            msg = f"supplier root must be absolute: {str(selected)!r}"
            raise ValueError(msg)
        physical = selected.resolve(strict=True)
        with os.scandir(selected):
            pass
        return None if physical == consumer_root else physical

    @classmethod
    def setup_selection(
        cls,
        *,
        consumer_root: Path,
        supplier_root: str | None,
        supplier_environment: str,
        selection_file: Path,
        resolution_root: Path,
        local_resolution: Path,
        editable_resolution: Path,
        standalone_resolution: Path,
        hosted: bool,
        selection_output: str = "resolver",
    ) -> Path | None:
        """Elect one resolver; explicit presence, including empty, precedes state."""
        consumer_root = consumer_root.resolve(strict=True)
        selected = cls.effective_supplier(
            consumer_root, supplier_root, supplier_environment, selection_file,
            hosted=hosted,
        )
        if selection_output == "supplier":
            return selected
        if selection_output != "resolver":
            msg_0 = f"invalid selection output: {selection_output!r}"
            raise ValueError(msg_0)
        if hosted:
            elected = standalone_resolution
        elif selected is not None:
            elected = editable_resolution
        else:
            elected = local_resolution
        return (resolution_root / elected).resolve(strict=True)

    @staticmethod
    def supplier_paths(root: Path) -> list[Path]:
        """Ask Git to decode its own composition and NUL-delimited path values."""
        modules = root / ".gitmodules"
        try:
            modules.stat()
        except FileNotFoundError:
            return []
        result = subprocess.run(
            ["git", "config", "--null", "--file", str(modules), "--list"],
            stdout=subprocess.PIPE, check=True,
        )
        paths = []
        for entry in result.stdout.split(b"\x00"):
            if not entry:
                continue
            key, separator, value = entry.partition(b"\n")
            if key.startswith(b"submodule.") and key.endswith(b".path"):
                if not separator:
                    msg = f"submodule path has no value: {modules}: {key!r}"
                    raise ValueError(msg)
                paths.append(root / os.fsdecode(value))
        return paths

    @classmethod
    def workspace_paths(
        cls, root: Path, document: dict[str, NativeValue],
    ) -> list[Path]:
        """Expand native workspace membership and exclusions without name heuristics."""
        workspace = cls.native_section(document, "tool", "uv", "workspace")
        excluded = {
            path.resolve(strict=True)
            for pattern in cls.native_array(workspace.get("exclude", []))
            for path in root.glob(cls.native_text(pattern))
        }
        return [
            path
            for pattern in cls.native_array(workspace.get("members", []))
            for path in root.glob(cls.native_text(pattern))
            if path.resolve(strict=True) not in excluded
        ]

    @classmethod
    def package_name(cls, path: Path) -> str | None:
        """Read one declared package, preserving non-Python Git members."""
        with os.scandir(path):
            pass
        manifest = path / "pyproject.toml"
        try:
            manifest.stat()
        except FileNotFoundError:
            return None
        data = cls.native_document(manifest)
        name = cls.native_section(data, "project").get("name")
        if name is None or cls.native_section(data, "tool", "uv").get("package") is False:
            return None
        return cls.distribution_name(cls.native_text(name))

    @classmethod
    def native_packages(cls, root: Path, *, supplier: bool) -> dict[str, Path]:
        """Derive packages from native Git composition or UV workspace membership."""
        root = root.resolve(strict=True)
        document = cls.native_document(root / "pyproject.toml")
        members = cls.supplier_paths(root) if supplier else cls.workspace_paths(root, document)
        packages: dict[str, Path] = {}
        paths = [root, *members]
        for path in paths:
            name = cls.package_name(path)
            if name is None:
                continue
            physical = path.resolve(strict=True)
            if name in packages and packages[name] != physical:
                msg_0 = f"ambiguous native distribution {name}: {packages[name]}: {physical}"
                raise ValueError(msg_0)
            packages[name] = physical
        return packages

    @classmethod
    def setup_inputs(
        cls,
        *,
        consumer_root: Path,
        supplier_root: Path | None,
        resolution_root: Path,
        control_distribution: str,
        supplier_environment: str | None = None,
    ) -> Path | None:
        """Authenticate every supplier-capable native manifest and lock binding."""
        import shlex
        from urllib.parse import urlsplit

        owned = cls.native_packages(consumer_root, supplier=False)
        if supplier_root is not None:
            supplier_root = supplier_root.resolve(strict=True)
            if supplier_root == consumer_root.resolve(strict=True):
                supplier_root = None
        expected = (
            cls.native_packages(supplier_root, supplier=True)
            if supplier_root is not None
            else owned
        )
        expected = {name: owned.get(name, path) for name, path in expected.items()}
        control = cls.distribution_name(control_distribution)
        if control in owned:
            expected[control] = owned[control]
        manifest_path = resolution_root / "pyproject.toml"
        lock_path = resolution_root / "uv.lock"
        try:
            manifest = cls.native_document(manifest_path)
        except FileNotFoundError as exc:
            exc.add_note(
                f"explicit generation required before setup: make gen (consumer {consumer_root}; resolver {resolution_root})"
            )
            raise
        try:
            lock = cls.native_document(lock_path)
        except FileNotFoundError as exc:
            command = "make upg"
            if supplier_root is not None:
                if supplier_environment is not None:
                    command = f"{supplier_environment}={shlex.quote(str(supplier_root))} {command}"
                else:
                    exc.add_note(
                        "pass --supplier-environment with the policy variable name to qualify explicit lock preparation"
                    )
                exc.add_note(
                    "the editable resolution lock is runtime-local and must NOT be committed"
                )
            exc.add_note(
                f"explicit lock preparation required before setup: {command} (consumer {consumer_root}; resolver {resolution_root})"
            )
            raise
        sources = manifest.get("tool", {}).get("uv", {}).get("sources", {})
        normalized_sources = {}
        for name, value in sources.items():
            normalized = cls.distribution_name(name)
            if normalized in normalized_sources:
                msg_0 = f"ambiguous manifest distribution: {manifest_path}: {name}"
                raise ValueError(msg_0)
            normalized_sources[normalized] = value
        sources = normalized_sources
        if supplier_root is not None and control not in expected:
            msg_0 = f"control distribution has no selected native package: {control_distribution}"
            raise ValueError(msg_0)
        for name, declarations in sources.items():
            if name not in expected:
                continue
            if isinstance(declarations, dict):
                declarations = [declarations]
            if not declarations:
                msg_0 = f"missing editable manifest binding: {manifest_path}: {name}: {expected[name]}"
                raise ValueError(msg_0)
            for declaration in declarations:
                if declaration.get("editable") is not True or not isinstance(
                    declaration.get("path"), str
                ):
                    msg_0 = f"noneditable manifest binding: {manifest_path}: {name}: {declaration!r}"
                    raise ValueError(msg_0)
                cls.editable_path(
                    resolution_root,
                    declaration["path"],
                    expected[name],
                    manifest_path,
                    name,
                )
        present = set()
        for package in lock.get("package", []):
            name = cls.distribution_name(package["name"])
            if name == control and name not in expected:
                source = package.get("source", {})
                if set(source) not in ({"git"}, {"registry"}):
                    msg_0 = (
                        f"unprovable native control source: {lock_path}: {package!r}"
                    )
                    raise ValueError(msg_0)
                location = urlsplit(next(iter(source.values())))
                if not location.scheme or not location.netloc:
                    msg_0 = f"invalid native control source: {lock_path}: {source!r}"
                    raise ValueError(msg_0)
                if "git" in source and not location.fragment:
                    msg_0 = f"Git control source has no locked commit: {lock_path}: {source!r}"
                    raise ValueError(msg_0)
                if not isinstance(package.get("version"), str):
                    msg_0 = f"native control source has no locked version: {lock_path}: {package!r}"
                    raise ValueError(msg_0)
                present.add(name)
            if name not in expected:
                continue
            present.add(name)
            if name not in sources:
                msg_0 = f"missing editable manifest binding: {manifest_path}: {name}: {expected[name]}"
                raise ValueError(msg_0)
            source = package.get("source", {})
            if set(source) != {"editable"}:
                msg_0 = f"noneditable lock binding: {lock_path}: {name}: {source!r}"
                raise ValueError(msg_0)
            cls.editable_path(
                resolution_root, source["editable"], expected[name], lock_path, name
            )
        if control not in present:
            msg_0 = f"control distribution absent from lock: {lock_path}: {control_distribution}"
            raise ValueError(msg_0)
        # UV repeats qualified edges in metadata, groups, overrides and forks.
        # Check each occurrence; repeated names are not duplicate identities.

        def edges(value: dict | list) -> None:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, (dict, list)):
                        edges(item)
                return
            name = value.get("name")
            if isinstance(name, str) and cls.distribution_name(name) in expected:
                normalized = cls.distribution_name(name)
                for key in ("editable", "path", "directory", "virtual"):
                    if key in value:
                        if key != "editable":
                            msg_0 = f"noneditable lock edge: {lock_path}: {value!r}"
                            raise ValueError(msg_0)
                        cls.editable_path(
                            resolution_root,
                            value[key],
                            expected[normalized],
                            lock_path,
                            name,
                        )
                if "source" in value:
                    source = value["source"]
                    if set(source) != {"editable"}:
                        msg_0 = f"foreign lock edge: {lock_path}: {value!r}"
                        raise ValueError(msg_0)
                    cls.editable_path(
                        resolution_root,
                        source["editable"],
                        expected[normalized],
                        lock_path,
                        name,
                    )
            for item in value.values():
                if isinstance(item, (dict, list)):
                    edges(item)

        edges(lock)
        return expected.get(control)

    @staticmethod
    def editable_path(
        root: Path, value: str, expected: Path, declaration: Path, name: str
    ) -> None:
        """Compare physical editable paths without discarding native failures."""
        actual = (root / value).resolve(strict=True)
        if actual != expected:
            msg_0 = f"foreign editable binding: {declaration}: {name}: {root / value}: expected {expected}"
            raise ValueError(msg_0)

    @classmethod
    def setup_producer(
        cls,
        *,
        consumer_root: Path,
        supplier_root: Path | None,
        resolution_root: Path,
        environment_root: Path,
        control_distribution: str,
        control_module: str,
    ) -> None:
        """Prove installed control metadata and PathFinder election without imports."""
        import base64
        import csv
        import hashlib
        import io
        import json
        import re
        from email.parser import BytesParser
        from urllib.parse import unquote, urlsplit

        expected = cls.setup_inputs(
            consumer_root=consumer_root,
            supplier_root=supplier_root,
            resolution_root=resolution_root,
            control_distribution=control_distribution,
        )
        environment = environment_root.absolute()
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
            msg_0 = f"cannot elect one native site-packages directory: {environment}: {sites}"
            raise ValueError(msg_0)
        site = sites[0]
        if site != site.resolve(strict=True):
            msg_0 = f"aliased consumer site-packages: {site}"
            raise ValueError(msg_0)
        matches = []
        records = {}
        for metadata in sorted(site.glob("*.dist-info")):
            payload = (metadata / "METADATA").read_bytes()
            names = BytesParser().parsebytes(payload).get_all("Name", [])
            if len(names) != 1:
                msg_0 = f"ambiguous distribution name: {metadata / 'METADATA'}"
                raise ValueError(msg_0)
            if cls.distribution_name(names[0]) == cls.distribution_name(
                control_distribution
            ):
                matches.append(metadata)
        if len(matches) != 1:
            msg_0 = f"expected one installed control distribution: {control_distribution}: {matches}"
            raise ValueError(msg_0)
        metadata = matches[0]
        if not metadata.resolve(strict=True).is_relative_to(site):
            msg_0 = f"foreign control metadata directory: {metadata}"
            raise ValueError(msg_0)
        direct_path = metadata / "direct_url.json"
        direct = json.loads(direct_path.read_bytes())
        url = urlsplit(direct["url"])
        if (
            url.scheme != "file"
            or url.netloc
            or url.query
            or url.fragment
            or direct.get("dir_info", {}).get("editable") is not True
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
        cls.editable_path(
            Path("/"), directory, expected, direct_path, control_distribution
        )
        record_path = metadata / "RECORD"
        for row in csv.reader(io.StringIO(record_path.read_text(encoding="utf-8"))):
            if len(row) != 3:
                msg_0 = f"invalid RECORD row: {record_path}: {row!r}"
                raise ValueError(msg_0)
            path = (site / row[0]).resolve(strict=True)
            if not path.is_relative_to(environment):
                msg_0 = f"foreign installed RECORD path: {record_path}: {path}"
                raise ValueError(msg_0)
            if path in records:
                msg_0 = f"duplicate RECORD path: {record_path}: {path}"
                raise ValueError(msg_0)
            records[path] = row
            if path == record_path.resolve():
                continue
            if not row[1] or not row[2]:
                msg_0 = f"unverifiable RECORD entry: {record_path}: {path}"
                raise ValueError(msg_0)
            algorithm, separator, digest = row[1].partition("=")
            if not separator:
                msg_0 = f"invalid RECORD digest: {record_path}: {path}"
                raise ValueError(msg_0)
            content = path.read_bytes()
            actual = (
                base64
                .urlsafe_b64encode(hashlib.new(algorithm, content).digest())
                .rstrip(b"=")
                .decode("ascii")
            )
            if actual != digest or len(content) != int(row[2]):
                msg_0 = f"installed RECORD mismatch: {record_path}: {path}"
                raise ValueError(msg_0)
        for required in (direct_path, metadata / "METADATA"):
            if required.resolve() not in records:
                msg_0 = f"missing control RECORD entry: {record_path}: {required}"
                raise ValueError(msg_0)
        search = [str(site)]
        for pointer in sorted(site.glob("*.pth")):
            for line in pointer.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#"):
                    continue
                if line.startswith(("import ", "import\t")):
                    msg_0 = f"implementation boundary: executable .pth cannot be proved without execution: {pointer}"
                    raise ValueError(msg_0)
                path = (site / line.rstrip()).resolve(strict=True)
                if pointer.resolve() in records and not path.is_relative_to(expected):
                    msg_0 = f"foreign control editable pointer: {pointer}: {path}: expected {expected}"
                    raise ValueError(msg_0)
                search.append(str(path))
        # Use the native PathFinder directly, never import parent initializers.

        def elect(paths: list[str]) -> ModuleSpec:
            for index in range(1, len(control_module.split(".")) + 1):
                name = ".".join(control_module.split(".")[:index])
                spec = PathFinder.find_spec(name, paths)
                if spec is None:
                    msg_0 = (
                        f"native setup module has no elected origin: {name}: {paths}"
                    )
                    raise ModuleNotFoundError(msg_0, name=name)
                if index < len(control_module.split(".")):
                    if spec.submodule_search_locations is None:
                        msg_0 = f"native setup parent is not a package: {name}: {spec.origin}"
                        raise ModuleNotFoundError(msg_0, name=name)
                    paths = list(spec.submodule_search_locations)
            return spec

        declared = cls.native_document(expected / "pyproject.toml")
        wheel = (
            declared
            .get("tool", {})
            .get("hatch", {})
            .get("build", {})
            .get("targets", {})
            .get("wheel", {})
        )
        mappings = wheel.get("sources")
        if not isinstance(mappings, dict) or not mappings:
            msg_0 = f"implementation boundary: no declared native wheel source mapping: {expected / 'pyproject.toml'}"
            raise ValueError(msg_0)
        declared_paths = []
        for source, destination in mappings.items():
            source_path = expected / source
            destination_parts = Path(destination).parts
            if (
                destination_parts
                and tuple(source_path.parts[-len(destination_parts) :])
                != destination_parts
            ):
                msg_0 = f"implementation boundary: remapped native package source: {source}: {destination}"
                raise ValueError(msg_0)
            for _ in destination_parts:
                source_path = source_path.parent
            physical_source = source_path.resolve(strict=True)
            if not physical_source.is_relative_to(expected):
                msg_0 = f"foreign declared native source: {expected / 'pyproject.toml'}: {physical_source}"
                raise ValueError(msg_0)
            declared_paths.append(str(physical_source))
        if not control_module or not all(
            part.isidentifier() for part in control_module.split(".")
        ):
            msg_0 = f"invalid control module identity: {control_module!r}"
            raise ValueError(msg_0)
        actual = elect(search)
        wanted = elect(declared_paths)
        if (
            actual.origin is None
            or wanted.origin is None
            or Path(actual.origin).resolve(strict=True)
            != Path(wanted.origin).resolve(strict=True)
        ):
            msg_0 = f"foreign native control election: {control_module}: {actual.origin}: expected {wanted.origin}"
            raise ImportError(msg_0)

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> int:
        """Run the copied original owner with base Python and explicit policy inputs."""
        import argparse

        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            "--setup-admission",
            choices=("inputs", "producer", "selection"),
            required=True,
        )
        parser.add_argument("--consumer-root", type=Path, required=True)
        parser.add_argument("--supplier-root")
        parser.add_argument("--selection-file", type=Path)
        parser.add_argument(
            "--selection-output", choices=("resolver", "supplier"), default="resolver"
        )
        parser.add_argument("--resolution-root", type=Path, required=True)
        parser.add_argument("--environment-root", type=Path)
        parser.add_argument("--local-resolution", type=Path)
        parser.add_argument("--editable-resolution", type=Path)
        parser.add_argument("--standalone-resolution", type=Path)
        parser.add_argument("--hosted", action="store_true")
        parser.add_argument("--control-distribution")
        parser.add_argument("--control-module")
        parser.add_argument("--supplier-environment")
        args = parser.parse_args(argv)
        required = (
            (
                "selection_file",
                "local_resolution",
                "editable_resolution",
                "standalone_resolution",
                "supplier_environment",
            )
            if args.setup_admission == "selection"
            else ("control_distribution",)
        )
        if args.setup_admission == "producer":
            required += ("control_module", "environment_root")
        for name in required:
            if getattr(args, name) is None:
                parser.error(
                    f"--{name.replace('_', '-')} is required for {args.setup_admission}"
                )
        if args.setup_admission == "selection":
            selected = cls.setup_selection(
                consumer_root=args.consumer_root,
                supplier_root=args.supplier_root,
                supplier_environment=args.supplier_environment,
                selection_file=args.selection_file,
                resolution_root=args.resolution_root,
                local_resolution=args.local_resolution,
                editable_resolution=args.editable_resolution,
                standalone_resolution=args.standalone_resolution,
                hosted=args.hosted,
                selection_output=args.selection_output,
            )
            print("" if selected is None else selected)
        else:
            supplier = (
                Path(args.supplier_root).resolve(strict=True)
                if args.supplier_root
                else None
            )
            if args.setup_admission == "inputs":
                cls.setup_inputs(
                    consumer_root=args.consumer_root,
                    supplier_root=supplier,
                    resolution_root=args.resolution_root,
                    control_distribution=args.control_distribution,
                    supplier_environment=args.supplier_environment,
                )
            else:
                cls.setup_producer(
                    consumer_root=args.consumer_root,
                    supplier_root=supplier,
                    resolution_root=args.resolution_root,
                    environment_root=args.environment_root,
                    control_distribution=args.control_distribution,
                    control_module=args.control_module,
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
    import subprocess
    import traceback

    try:
        raise SystemExit(FlextInfraValidateNativeBootstrap.main())
    except subprocess.CalledProcessError as exc:
        traceback.print_exc()
        raise SystemExit(exc.returncode) from exc
