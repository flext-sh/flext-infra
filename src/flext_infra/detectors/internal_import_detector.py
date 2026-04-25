"""Detect imports of private modules or symbols via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import c, m, u


class FlextInfraInternalImportDetector:
    """Detect private module/symbol imports via rope semantic resolution."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.InternalImportViolation]:
        """Detect private module/symbol imports in a single file."""
        res = u.Infra.fetch_python_resource(
            ctx.rope_project, ctx.file_path, skip_init_py=True
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        current_package = u.Infra.package_name(file_path)
        current_root = current_package.split(".", 1)[0] if current_package else ""
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
                and (
                    fqn.split(".", 1)[0].startswith("flext_")
                    or (current_root and fqn.split(".", 1)[0] == current_root)
                    or fqn.split(".", 1)[0]
                    in {
                        c.Infra.DIR_TESTS,
                        c.Infra.DIR_EXAMPLES,
                        c.Infra.DIR_SCRIPTS,
                    }
                )
            )
        ]


__all__: list[str] = ["FlextInfraInternalImportDetector"]
