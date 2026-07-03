"""Rope-backed fix adapter for enforcement rules with semantic refactoring.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.constants import c
from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.detectors.compatibility_alias_detector import (
    FlextInfraCompatibilityAliasDetector,
)
from flext_infra.detectors.inline_import_detector import (
    FlextInfraInlineImportDetector,
)
from flext_infra.detectors.private_import_bypass_detector import (
    FlextInfraPrivateImportBypassDetector,
)
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor.classvar_constant_autofix import (
    FlextInfraRefactorClassvarConstantAutofix,
)
from flext_infra.transformers.project_alias_migrator import (
    FlextInfraRefactorProjectAliasMigrator,
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
            "rewrite_compatibility_alias": self._fix_compatibility_alias,
            "fix_silent_failure_sentinels": self._fix_silent_failure_sentinels,
            "hoist_inline_import": self._fix_hoist_inline_import,
            "rewrite_private_import_bypass": self._fix_private_import_bypass,
            "rewrite_library_abstraction": self._fix_library_abstraction,
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

    @staticmethod
    def _collect_file_paths(
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
    ) -> tuple[Path, ...]:
        """Extract unique existing file paths from violation probes."""
        seen: set[Path] = set()
        paths: list[Path] = []
        for _rule, probe in violations:
            raw_path = getattr(probe, "file_path", None) or getattr(probe, "file", "")
            if not raw_path:
                continue
            file_path = Path(str(raw_path))
            if not file_path.is_absolute():
                file_path = project_dir / file_path
            file_path = file_path.resolve()
            if file_path.is_file() and file_path not in seen:
                seen.add(file_path)
                paths.append(file_path)
        return tuple(paths)

    @staticmethod
    def _rule_id(
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
    ) -> str:
        """Return the first rule id in a grouped violation batch."""
        return violations[0][0].id if violations else ""

    def _fix_foreign_canonical_alias(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Rewrite foreign canonical aliases to the owning project facade."""
        rule_id = self._rule_id(violations)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        for file_path in self._collect_file_paths(project_dir, violations):
            read = u.Cli.files_read_text(file_path)
            if read.failure:
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        error=read.error or "unable to read file",
                    )
                )
                continue
            transformer = FlextInfraRefactorProjectAliasMigrator(file_path=file_path)
            try:
                updated, changes = transformer.apply_to_source(read.value)
            except c.EXC_BROAD_RUNTIME as exc:
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        error=f"alias migration failed: {exc}",
                    )
                )
                continue
            if not changes:
                skipped.append(
                    fr.SkippedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        reason="no changes produced",
                    )
                )
                continue
            if not ctx.apply:
                fixed.append(
                    fr.FixedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=f"would rewrite {len(changes)} alias import(s)",
                    )
                )
                continue
            write = u.Cli.files_write_text(file_path, updated)
            if write.failure:
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        error=write.error or "unable to write file",
                    )
                )
                continue
            files_modified.add(str(file_path))
            fixed.append(
                fr.FixedViolation(
                    rule_id=rule_id,
                    file_path=str(file_path),
                    message=f"rewrote {len(changes)} alias import(s)",
                )
            )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _fix_silent_failure_sentinels(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Rewrite deterministic silent-failure sentinels to failed Results."""
        rule_id = self._rule_id(violations)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        with u.Infra.open_project(self._workspace_root) as rope_project:
            for file_path in self._collect_file_paths(project_dir, violations):
                resource = u.Infra.get_resource_from_path(rope_project, file_path)
                if resource is None:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="rope resource not found",
                        )
                    )
                    continue
                try:
                    _updated, changes = u.Infra.fix_silent_failure_sentinels(
                        rope_project,
                        resource,
                        apply=ctx.apply,
                    )
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"silent failure sentinel fix failed: {exc}",
                        )
                    )
                    continue
                if not changes:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="no changes produced",
                        )
                    )
                    continue
                if ctx.apply:
                    files_modified.add(str(file_path))
                fixed.append(
                    fr.FixedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=(
                            f"{'rewrote' if ctx.apply else 'would rewrite'} "
                            f"{len(changes)} silent sentinel fix(es)"
                        ),
                    )
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _fix_compatibility_alias(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Rewrite compatibility aliases using the canonical detector + rewriter."""
        rule_id = self._rule_id(violations)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        file_paths = self._collect_file_paths(project_dir, violations)
        if not file_paths:
            return fr.ProjectFixResult(
                project=project_dir.name,
                skipped=(
                    fr.SkippedViolation(
                        rule_id=rule_id,
                        file_path=str(project_dir),
                        reason="no files in violation batch",
                    ),
                ),
            )
        with u.Infra.open_project(self._workspace_root) as rope_project:
            for file_path in file_paths:
                detect_ctx = m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    project_name=project_dir.name,
                    project_root=project_dir,
                )
                try:
                    file_violations = FlextInfraCompatibilityAliasDetector.detect_file(
                        detect_ctx,
                    )
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"compatibility alias detector failed: {exc}",
                        )
                    )
                    continue
                if not file_violations:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="no compatibility alias violations",
                        )
                    )
                    continue
                if ctx.apply:
                    try:
                        u.Infra.rewrite_compatibility_alias_violations(
                            violations=file_violations,
                            parse_failures=[],
                        )
                    except c.EXC_BROAD_RUNTIME as exc:
                        failed.append(
                            fr.FailedFix(
                                rule_id=rule_id,
                                file_path=str(file_path),
                                error=f"compatibility alias rewrite failed: {exc}",
                            )
                        )
                        continue
                    files_modified.add(str(file_path))
                fixed.append(
                    fr.FixedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=(
                            f"{'rewrote' if ctx.apply else 'would rewrite'} "
                            f"{len(file_violations)} compatibility alias violation(s)"
                        ),
                    )
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _fix_private_import_bypass(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Rewrite private-module imports to their canonical facade equivalents."""
        rule_id = self._rule_id(violations)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        file_paths = self._collect_file_paths(project_dir, violations)
        if not file_paths:
            return fr.ProjectFixResult(
                project=project_dir.name,
                skipped=(
                    fr.SkippedViolation(
                        rule_id=rule_id,
                        file_path=str(project_dir),
                        reason="no files in violation batch",
                    ),
                ),
            )
        with u.Infra.open_project(self._workspace_root) as rope_project:
            for file_path in file_paths:
                detect_ctx = m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    project_name=project_dir.name,
                    project_root=project_dir,
                )
                try:
                    file_violations = FlextInfraPrivateImportBypassDetector.detect_file(
                        detect_ctx,
                    )
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"private import bypass detector failed: {exc}",
                        )
                    )
                    continue
                auto_fixable = tuple(v for v in file_violations if v.symbol_exported)
                if not auto_fixable:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="no auto-fixable private import bypass violations",
                        )
                    )
                    continue
                try:
                    u.Infra.rewrite_private_import_bypass_violations(
                        rope_project=rope_project,
                        violations=auto_fixable,
                        parse_failures=[],
                        apply=ctx.apply,
                    )
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"private import bypass rewrite failed: {exc}",
                        )
                    )
                    continue
                if ctx.apply:
                    files_modified.add(str(file_path))
                fixed.append(
                    fr.FixedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=(
                            f"{'rewrote' if ctx.apply else 'would rewrite'} "
                            f"{len(auto_fixable)} private import bypass violation(s)"
                        ),
                    )
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _fix_library_abstraction(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Library abstraction rewrites require human review; report skipped."""
        _ = ctx
        rule_id = self._rule_id(violations)
        skipped: list[fr.SkippedViolation] = []
        for _rule, probe in violations:
            file_path = getattr(probe, "file_path", "") or getattr(probe, "file", "")
            skipped.append(
                fr.SkippedViolation(
                    rule_id=rule_id,
                    file_path=str(file_path),
                    reason=(
                        "library abstraction rewrite must be reviewed manually "
                        "(hoist + facade routing)"
                    ),
                )
            )
        return fr.ProjectFixResult(
            project=project_dir.name,
            skipped=tuple(skipped),
        )

    def _fix_hoist_inline_import(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Hoist detector-approved inline stdlib imports to module scope."""
        rule_id = self._rule_id(violations)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        with u.Infra.open_project(self._workspace_root) as rope_project:
            for file_path in self._collect_file_paths(project_dir, violations):
                detect_ctx = m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    project_name=project_dir.name,
                    project_root=project_dir,
                )
                try:
                    detected = FlextInfraInlineImportDetector.detect_file(detect_ctx)
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"inline import detector failed: {exc}",
                        )
                    )
                    continue
                hoistable = tuple(
                    violation
                    for violation in detected
                    if FlextInfraInlineImportDetector.fix_action_for(
                        module_name=violation.module_name,
                        is_importlib=violation.is_importlib,
                    )
                    == "hoist_inline_import"
                )
                if not hoistable:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="no hoistable inline imports",
                        )
                    )
                    continue
                resource = u.Infra.get_resource_from_path(rope_project, file_path)
                if resource is None:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="rope resource not found",
                        )
                    )
                    continue
                try:
                    updated, changes = self._hoist_inline_import_source(
                        resource.read(),
                        hoistable,
                        file_path=file_path,
                    )
                except c.EXC_BROAD_RUNTIME as exc:
                    failed.append(
                        fr.FailedFix(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            error=f"inline import hoist failed: {exc}",
                        )
                    )
                    continue
                if not changes:
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=rule_id,
                            file_path=str(file_path),
                            reason="no changes produced",
                        )
                    )
                    continue
                if ctx.apply:
                    resource.write(updated)
                    files_modified.add(str(file_path))
                fixed.append(
                    fr.FixedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        message=(
                            f"{'hoisted' if ctx.apply else 'would hoist'} "
                            f"{len(changes)} inline import(s)"
                        ),
                    )
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    @classmethod
    def _hoist_inline_import_source(
        cls,
        source: str,
        violations: t.SequenceOf[m.Infra.InlineImportViolation],
        *,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        """Return source with hoistable inline import statements at module scope."""
        tree = ast.parse(source, filename=str(file_path))
        lines = source.splitlines(keepends=True)
        line_ranges: list[tuple[int, int]] = []
        import_lines: list[str] = []
        for violation in violations:
            node = cls._find_inline_import_node(tree, violation.line)
            if node is None:
                continue
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line) or start_line
            line_ranges.append((start_line, end_line))
            import_lines.append(cls._import_line_for_node(node))
        if not line_ranges:
            return source, []
        updated_lines = list(lines)
        for start_line, end_line in sorted(line_ranges, reverse=True):
            del updated_lines[start_line - 1 : end_line]
        insert_at = u.Infra.find_import_insert_position(updated_lines)
        unique_imports = cls._unique_new_imports(updated_lines, import_lines)
        for index, import_line in enumerate(unique_imports):
            updated_lines.insert(insert_at + index, import_line)
        updated = "".join(updated_lines)
        compile(updated, str(file_path), "exec")
        return updated, unique_imports

    @staticmethod
    def _find_inline_import_node(
        tree: ast.Module,
        line: int,
    ) -> ast.Import | ast.ImportFrom | None:
        """Find the import statement at a detector-reported line."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and node.lineno == line:
                return node
        return None

    @staticmethod
    def _import_line_for_node(node: ast.Import | ast.ImportFrom) -> str:
        """Render a top-level import line from an AST import node."""
        if isinstance(node, ast.Import):
            names = ", ".join(
                f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                for alias in node.names
            )
            return f"import {names}\n"
        module_prefix = "." * node.level
        module_name = f"{module_prefix}{node.module or ''}"
        names = ", ".join(
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in node.names
        )
        return f"from {module_name} import {names}\n"

    @staticmethod
    def _unique_new_imports(
        lines: t.StrSequence,
        import_lines: t.StrSequence,
    ) -> list[str]:
        """Return import lines that are not already present."""
        existing = {line.strip() for line in lines if line.strip()}
        unique: list[str] = []
        for import_line in import_lines:
            stripped = import_line.strip()
            if stripped in existing or stripped in {line.strip() for line in unique}:
                continue
            unique.append(import_line)
        return unique

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
