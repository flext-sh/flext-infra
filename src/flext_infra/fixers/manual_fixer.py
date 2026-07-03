"""Manual-fix adapter for enforcement rules that require human judgment.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraManualFixerAdapter(FlextInfraFixerAdapter):
    """Preview violations whose catalog fix_action is ``manual``.

    This adapter never mutates source files.  In dry-run it reports each
    violation as a preview; in apply mode it records a failed fix so that
    callers cannot accidentally believe an unsupported automatic rewrite
    happened.
    """

    kind: ClassVar[str] = "manual"

    @override
    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Accept every ``manual`` fix action."""
        return fix_action.kind == self.kind

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Return previews for manual fixes; fail if apply was requested."""
        previewed: list[fr.PreviewedViolation] = []
        failed: list[fr.FailedFix] = []
        for rule, probe in violations:
            rule_id = rule.id
            file_path = getattr(probe, "file_path", "") or getattr(probe, "file", "")
            line = getattr(probe, "line", 0)
            object_name = getattr(probe, "object_name", "")
            literal = getattr(probe, "literal", "")
            message = self._message(rule, object_name=object_name, literal=literal)
            if ctx.apply:
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        error=(
                            f"manual fix required for {rule_id}: "
                            f"{project_dir.name}/{Path(file_path).name}:{line} {message}"
                        ),
                    ),
                )
            else:
                previewed.append(
                    fr.PreviewedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=f"line {line}: {message}",
                    ),
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            previewed=tuple(previewed),
            failed=tuple(failed),
        )

    @staticmethod
    def _message(
        rule: me.EnforcementRuleSpec,
        *,
        object_name: str,
        literal: str,
    ) -> str:
        """Build a concise human-readable preview message."""
        if rule.id == "ENFORCE-097" and literal:
            return f"magic literal {literal} should become a named constant"
        if object_name:
            return f"{object_name} requires manual relocation/remediation"
        return "requires manual remediation"
