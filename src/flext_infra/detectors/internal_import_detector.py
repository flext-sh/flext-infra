"""Detect imports of private modules or symbols via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import m, t, u


class FlextInfraInternalImportDetector:
    """Detect private module/symbol imports via rope semantic resolution.

    Same-package facade assembly is the sanctioned FLEXT MRO-composition
    pattern: a facade module (or any module of the owning package subtree)
    importing a private ``_x`` module/subpackage that hangs off one of its
    own ancestor packages is NOT a violation. Cross-package private module
    imports and private ``_symbol`` imports remain violations.
    """

    @staticmethod
    def _facade_assembly_exempt(importer_module: str, fqn: str) -> bool:
        """Return whether a private-module import is sanctioned facade assembly."""
        if not importer_module:
            return False
        importer_parts = importer_module.split(".")
        fqn_parts = fqn.split(".")
        if fqn_parts and fqn_parts[0].startswith("_"):
            return True
        private_index = next(
            (
                index
                for index, part in enumerate(fqn_parts)
                if index > 0 and part.startswith("_")
            ),
            None,
        )
        if private_index is None:
            return False
        public_prefix = fqn_parts[:private_index]
        return importer_parts[: len(public_prefix)] == public_prefix

    @staticmethod
    def _has_private_module_part(fqn: str) -> bool:
        """Return whether the resolved import path crosses a private module."""
        parts = fqn.split(".")
        return any(part.startswith("_") for part in parts[:-1])

    @classmethod
    def facade_assembly_exempt(cls, importer_module: str, fqn: str) -> bool:
        """Public accessor for same-package facade-assembly exemption."""
        return cls._facade_assembly_exempt(importer_module, fqn)

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.InternalImportViolation]:
        """Detect private module/symbol imports in a single file."""
        res = u.Infra.fetch_python_resource(
            ctx.rope_project, ctx.file_path, skip_init_py=True
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        current_module = u.Infra.package_name(file_path)
        imports = u.Infra.get_semantic_module_imports(rope_project, res)

        def violates_internal_import(local: str, fqn: str) -> bool:
            private_module = (
                FlextInfraInternalImportDetector._has_private_module_part(fqn)
            )
            facade_exempt = private_module and (
                FlextInfraInternalImportDetector._facade_assembly_exempt(
                    current_module,
                    fqn,
                )
            )
            return (local.startswith("_") or private_module) and not facade_exempt

        return [
            m.Infra.InternalImportViolation(
                file=str(file_path),
                line=1,
                current_import=f"from ... import {local}  # {fqn}",
                detail="private module import"
                if FlextInfraInternalImportDetector._has_private_module_part(fqn)
                else "private symbol import",
            )
            for local, fqn in imports.items()
            if violates_internal_import(local, fqn)
        ]


__all__: list[str] = ["FlextInfraInternalImportDetector"]
