"""Detect imports of private modules or symbols via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from flext_infra import FlextInfraScanFileMixin, c, m, p, u


class FlextInfraInternalImportDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect private module/symbol imports via rope semantic resolution."""

    _rule_id: ClassVar[str] = "namespace.internal_import"
    _MESSAGE_TEMPLATE: ClassVar[str] = "Internal import '{current_import}': {detail}"

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.InternalImportViolation]:
        """Detect private module/symbol imports in a single file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if file_path.name == c.Infra.Files.INIT_PY:
            return []
        current_package = u.Infra.discover_package_from_file(file_path)
        current_root = current_package.split(".", 1)[0] if current_package else ""
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        imports = u.Infra.get_semantic_module_imports(rope_project, res)
        return [
            m.Infra.InternalImportViolation(
                file=str(file_path),
                line=1,
                current_import=f"from ... import {local}  # {fqn}",
                detail="private module import"
                if "._" in fqn
                else "private symbol import",
            )
            for local, fqn in imports.items()
            if local.startswith("_")
            or (
                "._" in fqn
                and cls._is_first_party_private_import(
                    fqn=fqn,
                    current_root=current_root,
                )
            )
        ]

    @staticmethod
    def _is_first_party_private_import(*, fqn: str, current_root: str) -> bool:
        root = fqn.split(".", 1)[0]
        if root.startswith("flext_"):
            return True
        if current_root and root == current_root:
            return True
        return root in {
            c.Infra.Directories.TESTS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
        }


__all__ = ["FlextInfraInternalImportDetector"]
