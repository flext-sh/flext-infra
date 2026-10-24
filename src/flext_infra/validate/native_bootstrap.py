"""Own the stdlib-only cold import loader before framework initialization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, MutableMapping, Sequence
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
    msg = "Python setup admission is retired; native Mise/uv owns provisioning"
    raise RuntimeError(msg)
