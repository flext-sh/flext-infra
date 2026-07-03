"""Rope-backed fix adapter for enforcement rules with semantic refactoring.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.constants import c
from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor.classvar_constant_autofix import (
    FlextInfraRefactorClassvarConstantAutofix,
)
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraRopeFixerAdapter(FlextInfraFixerAdapter):
    """Apply fixes by running rope-backed refactor operations per violation.

    Targets are canonical rope refactor short-names declared in the enforcement
    catalog.  Each target uses rope (and the existing detector infrastructure)
    to locate violations and rewrite source safely.
    """

    kind: ClassVar[str] = "rope"

    def __init__(self, workspace_root: Path) -> None:
        """Bind the workspace root used to open rope projects."""
        super().__init__(workspace_root)

    @override
    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        return fix_action.kind == self.kind

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Apply rope fixes grouped by target."""
        if not violations:
            return fr.ProjectFixResult(project=project_dir.name)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        for target, target_violations in self._group_by_target(violations).items():
            handler = self._target_dispatch().get(target)
            if handler is None:
                rule_id = target_violations[0][0].id
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(project_dir),
                        error=f"rope target {target} not registered",
                    ),
                )
                continue
            result = handler(project_dir, target_violations, ctx)
            fixed.extend(result.fixed)
            skipped.extend(result.skipped)
            failed.extend(result.failed)
            files_modified.update(result.files_modified)
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _target_dispatch(
        self,
    ) -> dict[
        str,
        Callable[
            [
                Path,
                t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
                m.Infra.FixEnforcementCommand,
            ],
            fr.ProjectFixResult,
        ],
    ]:
        """Return bound rope target handlers for this adapter instance."""
        return {
            "classvar_relocation": self._fix_classvar_relocation,
        }

    @staticmethod
    def _package_name_for_dir(package_dir: Path, *, project_root: Path) -> str:
        """Return the import package for a directory inside a project."""
        try:
            relative_parts = package_dir.relative_to(project_root).parts
        except ValueError:
            return ""
        if not relative_parts:
            return ""
        root_name = relative_parts[0]
        if root_name == c.Infra.DEFAULT_SRC_DIR:
            package_parts = relative_parts[1:]
        elif root_name in c.Infra.ROOT_WRAPPER_SEGMENTS:
            package_parts = relative_parts
        else:
            package_parts = ()
        return ".".join(package_parts)

    @classmethod
    def _module_name_for_file(cls, file_path: Path, *, project_root: Path) -> str:
        """Return the import module for a Python file inside a project."""
        package_name = cls._package_name_for_dir(
            file_path.parent,
            project_root=project_root,
        )
        if file_path.name == c.Infra.INIT_PY:
            return package_name
        return f"{package_name}.{file_path.stem}" if package_name else ""

    def _group_by_target(
        self,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
    ) -> dict[str, list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]]]:
        """Group violations by the rope target declared in their fix_action."""
        grouped: dict[str, list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]]] = {}
        for rule, probe in violations:
            fix_action = rule.fix_action
            if fix_action is None:
                continue
            grouped.setdefault(fix_action.target, []).append((rule, probe))
        return grouped

    def _fix_classvar_relocation(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Move class-level constants to canonical _constants modules."""
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()

        with u.Infra.open_project(self._workspace_root) as rope_project:
            for _rule, probe in violations:
                file_path_str = getattr(probe, "file_path", "")
                file_path = Path(file_path_str)
                if not file_path.is_file():
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id="ENFORCE-079",
                            file_path=file_path_str,
                            reason="file not found",
                        ),
                    )
                    continue
                detect_ctx = m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    project_name=project_dir.name,
                    project_root=project_dir,
                )
                try:
                    all_violations = FlextInfraClassPlacementDetector.detect_file(
                        detect_ctx,
                    )
                except c.EXC_BROAD_RUNTIME:
                    failed.append(
                        fr.FailedFix(
                            rule_id="ENFORCE-079",
                            file_path=file_path_str,
                            error="detector raised runtime error",
                        ),
                    )
                    continue
                classvar_violations = [
                    v for v in all_violations if v.action == "classvar_relocation"
                ]
                if not classvar_violations:
                    continue
                module_name = self._module_name_for_file(
                    file_path,
                    project_root=project_dir,
                )
                if not module_name:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id="ENFORCE-079",
                            file_path=file_path_str,
                            reason="could not resolve module name",
                        ),
                    )
                    continue
                constants_module = (
                    f"{module_name.rsplit('.', maxsplit=1)[0]}._constants"
                    if "." in module_name
                    else f"{module_name}._constants"
                )
                for violation in classvar_violations:
                    class_full_name = f"{module_name}.{violation.base_class}"
                    try:
                        result = FlextInfraRefactorClassvarConstantAutofix.apply(
                            self._workspace_root,
                            class_full_name,
                            violation.name,
                            constants_module,
                            dry_run=not ctx.apply,
                        )
                    except c.EXC_BROAD_RUNTIME as exc:
                        failed.append(
                            fr.FailedFix(
                                rule_id="ENFORCE-079",
                                file_path=file_path_str,
                                error=f"autofix failed: {exc}",
                            ),
                        )
                        continue
                    touched_raw = result.get("touched_files", ())
                    if not isinstance(touched_raw, (list, tuple)):
                        failed.append(
                            fr.FailedFix(
                                rule_id="ENFORCE-079",
                                file_path=file_path_str,
                                error="autofix returned invalid touched_files",
                            ),
                        )
                        continue
                    touched = tuple(str(path) for path in touched_raw)
                    if ctx.apply:
                        files_modified.update(str(project_dir / p) for p in touched)
                    fixed.append(
                        fr.FixedViolation(
                            rule_id="ENFORCE-079",
                            file_path=file_path_str,
                            message=(
                                f"{'would move' if not ctx.apply else 'moved'} "
                                f"{violation.base_class}.{violation.name} -> "
                                f"{constants_module}"
                            ),
                        ),
                    )

        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )
