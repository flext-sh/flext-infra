"""Detect imports of private modules or symbols via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import FlextInfraScanFileMixin, m, p, t, u


class FlextInfraInternalImportDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect private module/symbol imports via rope semantic resolution."""

    _rule_id: ClassVar[str] = "namespace.internal_import"
    _MESSAGE_TEMPLATE: ClassVar[str] = "Internal import '{current_import}': {detail}"

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.InternalImportViolation]:
        """Detect private module/symbol imports in a single file."""
        del parse_failures
        if file_path.name == "__init__.py":
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        imports = u.Infra.get_module_imports(rope_project, res)
        return [
            m.Infra.InternalImportViolation.create(
                file=str(file_path),
                line=1,
                current_import=f"from ... import {local}  # {fqn}",
                detail="private module import"
                if "._" in fqn
                else "private symbol import",
            )
            for local, fqn in imports.items()
            if "._" in fqn or local.startswith("_")
        ]


__all__ = ["FlextInfraInternalImportDetector"]
