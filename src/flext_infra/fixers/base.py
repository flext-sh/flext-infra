"""Base adapter interface for enforcement fixers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

    from flext_core._models.enforcement import FlextModelsEnforcement as me
    from flext_infra.fixers.result import FlextInfraFixersResult as fr
    from flext_infra.models import m
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraFixerAdapter:
    """Abstract adapter that routes enforcement-catalog violations to fixes.

    Subclasses declare a ``kind`` ClassVar matching ``EnforcementFixAction.kind``
    and implement ``can_fix`` / ``fix_project``.
    """

    kind: ClassVar[str] = ""

    def __init__(self, workspace_root: Path) -> None:
        """Bind the workspace root used during fix execution."""
        self._workspace_root = workspace_root

    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        return fix_action.kind == self.kind

    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Apply fixes for the given violations in ``project_dir``."""
        msg = f"{self.__class__.__name__}.fix_project must be implemented"
        raise NotImplementedError(msg)


__all__: list[str] = ["FlextInfraFixerAdapter"]
