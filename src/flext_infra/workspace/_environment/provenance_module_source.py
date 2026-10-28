"""Native module-origin observation for environment provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import sysconfig
from importlib.machinery import (
    BuiltinImporter,
    ExtensionFileLoader,
    FrozenImporter,
    ModuleSpec,
)
from pathlib import Path
from sys import modules
from types import ModuleType

from flext_infra import p, r, t, u


class FlextInfraWorkspaceEnvironmentProvenanceModuleSource:
    """Resolve loaded modules to their authenticated physical origins."""

    @classmethod
    def module_source(cls, module_name: str) -> p.Result[Path]:
        """Observe native module origin; the isolated import authenticates election.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        registered = cls._registered_module(module_name)
        if registered.failure:
            return r[Path].from_failure(registered)
        module = registered.value
        namespace = vars(ModuleType)["__dict__"].__get__(module, type(module))
        native = namespace.get("__spec__")
        if native is None:
            return cls._native_child_source(module_name, module, namespace)
        if type(native) is not ModuleSpec or modules.get(native.name) is not module:
            return r[Path].fail(f"producer module lacks its native spec: {module_name}")
        return cls._module_spec_source(module_name, namespace, native)

    @classmethod
    def _module_spec_source(
        cls,
        module_name: str,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        native: ModuleSpec,
    ) -> p.Result[Path]:
        """Resolve an authenticated native spec through its declared loader.

        Returns:
            Its original interpreter, namespace or physical file authority.

        """
        if namespace.get("__loader__") is not native.loader:
            return r[Path].fail(
                f"producer module loader differs from native spec: {module_name}"
            )
        interpreter = Path(sys.executable).resolve()
        if native.origin in {"built-in", "frozen"}:
            return cls._interpreter_module_source(
                module_name, native.name, native.origin, native.loader, interpreter
            )
        if native.origin is None:
            locations = native.submodule_search_locations
            if locations is None or namespace.get("__path__") is not locations:
                return r[Path].fail(
                    f"producer namespace paths differ from native spec: {module_name}"
                )
            return cls._namespace_module_source(
                module_name,
                locations,
                tuple(locations),
            )
        return cls._file_module_source(
            module_name,
            native.name,
            native.origin,
            namespace.get("__file__"),
            interpreter,
        )

    @staticmethod
    def _native_child_parent(
        module_name: str,
        module: ModuleType,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> p.Result[t.Pair[str, ModuleType]]:
        """Observe the exact registrations used by native module construction.

        Returns:
            The canonical parent registration or the first identity mismatch.

        """
        result_type = r[t.Pair[str, ModuleType]]
        name = namespace.get("__name__")
        if type(module) is not ModuleType or not isinstance(name, str):
            return result_type.fail(
                f"native child module lacks canonical registration: {module_name}"
            )
        if (
            type(name) is not str
            or modules.get(name) is not module
            or modules.get(module_name) is not module
            or namespace.get("__file__") is not None
            or namespace.get("__loader__") is not None
        ):
            return result_type.fail(
                f"native child module lacks canonical registration: {module_name}"
            )
        parent_name, separator, attribute = name.rpartition(".")
        parent = modules.get(parent_name)
        if not separator or type(parent) is not ModuleType:
            return result_type.fail(
                f"native child module lacks its registered parent: {module_name}"
            )
        parent_namespace = vars(ModuleType)["__dict__"].__get__(parent, ModuleType)
        if parent_namespace.get(attribute) is not module:
            return result_type.fail(
                f"native child module differs from its parent binding: {module_name}"
            )
        return result_type.ok((parent_name, parent))

    @classmethod
    def _native_child_source(
        cls,
        module_name: str,
        module: ModuleType,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> p.Result[Path]:
        """Bind a spec-less native child to its parent's real binary authority.

        Returns:
            The authenticated parent binary, without manufacturing a child spec.

        """
        result_type = r[Path]
        owner = cls._native_child_parent(module_name, module, namespace)
        if owner.failure:
            return result_type.from_failure(owner)
        parent_name, parent = owner.value
        parent_namespace = vars(ModuleType)["__dict__"].__get__(parent, ModuleType)
        native = parent_namespace.get("__spec__")
        if type(native) is not ModuleSpec or not (
            isinstance(native.loader, ExtensionFileLoader)
            or native.origin == "built-in"
        ):
            return result_type.fail(
                f"native child module has no binary parent: {module_name}"
            )
        source = cls.module_source(parent_name)
        if source.failure:
            return result_type.from_failure(source)
        current = cls._native_child_parent(module_name, module, namespace)
        if current.failure:
            return result_type.from_failure(current)
        if current.value[0] != parent_name or current.value[1] is not parent:
            return result_type.fail(
                f"native child parent changed during observation: {module_name}"
            )
        return source

    @staticmethod
    def _registered_module(module_name: str) -> p.Result[ModuleType]:
        """Prove the supplier has native module storage before reading its slots.

        Returns:
            The exact registered module or the original supplier failure.

        """
        module = modules.get(module_name)
        if module is None:
            return r[ModuleType].fail(
                f"producer source module is not registered: {module_name}"
            )
        ancestry = vars(type)["__mro__"].__get__(type(module), type(type(module)))
        if not any(owner is ModuleType for owner in ancestry):
            return r[ModuleType].fail(
                f"producer source supplier has no native module storage: {module_name}"
            )
        return r[ModuleType].ok(module)

    @staticmethod
    def _interpreter_module_source(
        module_name: str,
        native_name: str,
        origin: str,
        loader: p.AttributeProbe | None,
        interpreter: Path,
    ) -> p.Result[Path]:
        """Authenticate a built-in or frozen supplier through its native importer.

        Returns:
            The actual interpreter path after exact loader election.

        """
        importer = BuiltinImporter if origin == "built-in" else FrozenImporter
        expected = importer.find_spec(native_name)
        if expected is None or loader is not expected.loader:
            return r[Path].fail(
                f"producer native interpreter loader differs: {module_name}"
            )
        return r[Path].ok(interpreter)

    @staticmethod
    def _namespace_module_source(
        module_name: str,
        locations: t.SequenceOf[str] | None,
        declared_paths: t.VariadicTuple[t.Infra.NativeOperand],
    ) -> p.Result[Path]:
        """Bind a namespace's native search path to exactly one physical origin.

        Returns:
            Its authenticated directory, rejecting every multiple-origin supplier.

        """
        if locations is None or declared_paths != tuple(locations):
            return r[Path].fail(
                f"producer namespace paths differ from native spec: {module_name}"
            )
        if len(locations) != 1:
            return r[Path].fail(
                "producer namespace requires explicit multiple physical origins: "
                f"{module_name}={tuple(locations)}",
            )
        root = Path(locations[0]).absolute()
        physical = u.Cli.atomic_plan_directory_chain(root)
        if physical.failure:
            return r[Path].from_failure(physical)
        return r[Path].ok(root)

    @staticmethod
    def standard_library_root() -> Path:
        """Return the standard library owned by the current base interpreter.

        Returns:
            The resolved native standard-library directory.

        """
        return Path(
            sysconfig.get_path(
                "stdlib",
                vars={
                    "base": sys.base_prefix,
                    "platbase": sys.base_exec_prefix,
                },
            )
        ).resolve()

    @staticmethod
    def standard_library_package_roots() -> t.VariadicTuple[Path]:
        """Elect package-installation trees inside the interpreter's base scheme.

        Returns:
            Physical purelib and platlib roots, kept outside stdlib authority.

        """
        variables = {
            "base": sys.base_prefix,
            "platbase": sys.base_exec_prefix,
        }
        return tuple(
            dict.fromkeys(
                Path(sysconfig.get_path(key, vars=variables)).resolve()
                for key in ("purelib", "platlib")
            )
        )

    @classmethod
    def _file_module_source(
        cls,
        module_name: str,
        native_name: str,
        native_origin: str,
        declared_file: t.Infra.NativeOperand,
        interpreter: Path,
    ) -> p.Result[Path]:
        """Verify the native file slot and the interpreter-owned stdlib ancestry.

        Returns:
            The same physical origin after file and standard-library proof.

        """
        if declared_file != native_origin:
            return r[Path].fail(
                f"producer module file differs from native origin: {module_name}"
            )
        origin = Path(native_origin).absolute()
        if native_name.partition(".")[0] in sys.stdlib_module_names:
            base = Path(sys.base_prefix).resolve()
            standard = cls.standard_library_root()
            if not interpreter.is_relative_to(
                base
            ) or not origin.resolve().is_relative_to(standard):
                return r[Path].fail(
                    f"producer standard library differs from interpreter base: "
                    f"{module_name}"
                )
        return r[Path].ok(origin)


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentProvenanceModuleSource"]
