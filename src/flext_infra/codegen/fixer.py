"""Auto-fix engine for namespace violations.

Orchestrates NS rule fixes, MRO migration, refactor engine passes,
namespace enforcement, and lazy init propagation for each project.

Rule implementations live in ``_utilities_codegen_fixer_rules``.
Pipeline passes live in ``_utilities_codegen_fixer_passes``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from pydantic import Field

from flext_core import r
from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraNamespaceEnforcer,
    FlextInfraNamespaceValidator,
    FlextInfraRefactorEngine,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    s,
    t,
    u,
)


class FlextInfraCodegenFixer(s[str]):
    """Rope-oriented auto-fixer for namespace violations (Rules 1-5)."""

    dry_run: bool = Field(
        default=False, description="Preview changes without modifying files"
    )
    rules_only: bool = Field(
        default=False, description="Only apply rule-based fixes, skip heuristic ones"
    )

    @override
    def execute(self) -> r[str]:
        """Execute auto-fix directly from the validated CLI service model."""
        dry_run = self.dry_run or not self.apply_changes
        results = self.fix_workspace()
        total_fixed = sum(len(result.violations_fixed) for result in results)
        total_skipped = sum(len(result.violations_skipped) for result in results)
        lines: MutableSequence[str] = []
        if dry_run:
            lines.append("Dry-run mode: no files will be modified")
        lines.extend(
            (f"  {result.project}: fixed {len(result.violations_fixed)} violations")
            for result in results
            if result.violations_fixed
        )
        lines.append(
            (
                f"Auto-fix: {total_fixed} fixed, {total_skipped} skipped"
                f" across {len(results)} projects"
            ),
        )
        return r[str].ok("\n".join(lines))

    @staticmethod
    def _empty_result(project_name: str) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=[],
            violations_skipped=[],
            files_modified=[],
        )

    @staticmethod
    def _build_result(
        project_name: str,
        ctx: m.Infra.FixContext,
    ) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=list(ctx.violations_fixed),
            violations_skipped=list(ctx.violations_skipped),
            files_modified=sorted(ctx.files_modified),
        )

    def fix_project(self, project_path: Path) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project."""
        prefix = FlextInfraNamespaceValidator.derive_prefix(project_path)
        if not prefix:
            return self._empty_result(project_path.name)
        src_dir_for_pkg = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        pkg_dir: Path | None = None
        if src_dir_for_pkg.is_dir():
            for child in sorted(src_dir_for_pkg.iterdir()):
                if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                    pkg_dir = child
                    break
        if pkg_dir is None:
            return self._empty_result(project_path.name)
        ctx = m.Infra.FixContext()
        src_dir = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        initial_violations_result = self._namespace_violations(project_path)
        initial_violations = initial_violations_result.unwrap_or(())
        if initial_violations_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=initial_violations_result.error
                or "namespace validation failed",
            )
        py_files = list(project_path.rglob(c.Infra.Extensions.PYTHON_GLOB))
        bak_paths = u.Infra.backup_files(py_files)
        if self.dry_run or self.rules_only:
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        self._normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=project_path,
        ).run(target="all", apply=True)
        for migration in report.migrations:
            ctx.files_modified.add(migration.file)
            symbols = ", ".join(migration.moved_symbols) or "symbols"
            ctx.fix(
                module=migration.module,
                rule="MRO",
                line=1,
                message=f"migrated {symbols} into facade MRO",
            )
        for rewrite in report.rewrites:
            ctx.files_modified.add(rewrite.file)
            ctx.fix(
                module=rewrite.file,
                rule="MRO-REWRITE",
                line=1,
                message=f"rewrote {rewrite.replacements} consumer references",
            )
        for error in report.errors:
            ctx.skip(
                module=project_path.name,
                rule="MRO",
                line=0,
                message=error,
            )
        engine = FlextInfraRefactorEngine()
        config_result = engine.load_config()
        rules_result = engine.load_rules() if config_result.is_success else None
        if config_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=config_result.error or "refactor config load failed",
            )
        elif rules_result is not None and rules_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=rules_result.error or "refactor rule load failed",
            )
        else:
            for result in engine.refactor_project(
                project_path,
                dry_run=False,
                apply_safety=False,
            ):
                if result.success:
                    ctx.files_modified.add(str(result.file_path))
                if result.modified:
                    changes = tuple(result.changes) or ("refactor applied",)
                    for change in changes:
                        ctx.fix(
                            module=str(result.file_path),
                            rule="REFACTOR",
                            line=1,
                            message=change,
                        )
                elif not result.success:
                    ctx.skip(
                        module=str(result.file_path),
                        rule="REFACTOR",
                        line=1,
                        message=result.error or "refactor failed",
                    )
        enforcement = FlextInfraNamespaceEnforcer(
            workspace_root=project_path,
        ).enforce(apply=True)
        for project_report in enforcement.projects:
            if project_report.has_violations:
                ctx.skip(
                    module=project_report.project,
                    rule="NAMESPACE",
                    line=0,
                    message="violations remain after namespace enforcement",
                )
        lazy_generator = FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": project_path},
        )
        lazy_errors = lazy_generator.generate_inits(check_only=False)
        for f in lazy_generator.modified_files:
            ctx.files_modified.add(f)
        if lazy_errors > 0:
            ctx.skip(
                module=project_path.name,
                rule="LAZY-INIT",
                line=0,
                message=f"lazy propagation finished with {lazy_errors} errors",
            )
        try:
            for modified_file in sorted(ctx.files_modified):
                path = Path(modified_file)
                if path.is_file():
                    u.Infra.run_ruff_fix(path, quiet=True)
        except (OSError, UnicodeDecodeError):
            u.Infra.restore_files(bak_paths)
            raise
        self._reconcile_namespace_violations(
            project_path=project_path,
            ctx=ctx,
            initial_violations=initial_violations,
        )
        return self._build_result(project_path.name, ctx)

    @classmethod
    def _normalize_canonical_facades(
        cls,
        *,
        pkg_dir: Path,
        ctx: m.Infra.FixContext,
    ) -> None:
        cls._normalize_facade_base(
            file_path=pkg_dir / c.Infra.Files.CONSTANTS_PY,
            base_import="from flext_core import FlextConstants as Constants",
            base_name="Constants",
            ctx=ctx,
        )
        cls._normalize_facade_base(
            file_path=pkg_dir / c.Infra.Files.TYPINGS_PY,
            base_import="from flext_core import FlextTypes as Types",
            base_name="Types",
            ctx=ctx,
        )

    @staticmethod
    def _normalize_facade_base(
        *,
        file_path: Path,
        base_import: str,
        base_name: str,
        ctx: m.Infra.FixContext,
    ) -> None:
        if not file_path.is_file():
            return
        rope_project = u.Infra.init_rope_project(file_path.parent)
        try:
            resource = u.Infra.get_resource_from_path(rope_project, file_path)
            if resource is None:
                return
            source = u.Infra.read_source(resource)
            updated, class_name = FlextInfraCodegenFixer._normalize_facade_base_source(
                rope_project=rope_project,
                resource=resource,
                source=source,
                base_import=base_import,
                base_name=base_name,
            )
            if updated == source or not class_name:
                return
            u.Infra.write_source(
                rope_project,
                resource,
                updated,
                description=f"normalize facade base in <{resource.path}>",
            )
        finally:
            rope_project.close()
        ctx.files_modified.add(str(file_path))
        ctx.fix(
            module=str(file_path),
            rule="NAMESPACE",
            line=1,
            message=f"normalized {class_name} to inherit from {base_name}",
        )

    @staticmethod
    def _normalize_facade_base_source(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        base_import: str,
        base_name: str,
    ) -> tuple[str, str]:
        class_infos = sorted(
            u.Infra.get_class_info(rope_project, resource),
            key=lambda item: item.line,
        )
        if not class_infos:
            return source, ""
        class_name = class_infos[0].name
        lines = source.splitlines()
        header_idx = class_infos[0].line - 1
        if header_idx < 0 or header_idx >= len(lines):
            return source, ""
        rewritten_header = FlextInfraCodegenFixer._normalize_class_header(
            line=lines[header_idx],
            class_name=class_name,
            base_name=base_name,
        )
        if rewritten_header == lines[header_idx] and base_import in source:
            return source, class_name
        lines[header_idx] = rewritten_header
        updated = "\n".join(lines)
        if source.endswith("\n"):
            updated += "\n"
        if base_import not in updated:
            updated = FlextInfraCodegenFixer._insert_import_line(
                source=updated,
                import_line=base_import,
            )
        return updated, class_name

    @staticmethod
    def _normalize_class_header(*, line: str, class_name: str, base_name: str) -> str:
        stripped = line.strip()
        prefix = f"class {class_name}"
        if not stripped.startswith(prefix) or not stripped.endswith(":"):
            return line
        indent = line[: len(line) - len(line.lstrip())]
        return f"{indent}class {class_name}({base_name}):"

    @staticmethod
    def _insert_import_line(*, source: str, import_line: str) -> str:
        lines = source.splitlines()
        if import_line in lines:
            return source
        insert_at = u.Infra.find_import_insert_position(lines, past_existing=False)
        before = lines[:insert_at]
        after = lines[insert_at:]
        inserted: MutableSequence[str] = list(before)
        if inserted and inserted[-1]:
            inserted.append("")
        inserted.append(import_line)
        if after and after[0]:
            inserted.append("")
        inserted.extend(after)
        return "\n".join(inserted) + ("\n" if source.endswith("\n") else "")

    @staticmethod
    def _namespace_violations(
        project_path: Path,
    ) -> r[tuple[m.Infra.CensusViolation, ...]]:
        """Return parsed namespace violations for one project."""
        validation = FlextInfraNamespaceValidator().validate(project_path)
        if validation.is_failure:
            return r[tuple[m.Infra.CensusViolation, ...]].fail(
                validation.error or "namespace validation failed",
            )
        violations: MutableSequence[m.Infra.CensusViolation] = []
        for violation_str in validation.value.violations:
            violation = FlextInfraCodegenFixer._parse_violation(violation_str)
            if violation is not None:
                violations.append(violation)
        return r[tuple[m.Infra.CensusViolation, ...]].ok(tuple(violations))

    @staticmethod
    def _parse_violation(violation_str: str) -> m.Infra.CensusViolation | None:
        """Parse a namespace violation string into a typed model."""
        match = c.Infra.VIOLATION_PATTERN.match(violation_str)
        if match is None:
            return None
        rule = match.group("rule")
        module = match.group("module")
        message = match.group("message")
        return m.Infra.CensusViolation(
            module=module,
            rule=rule,
            line=int(match.group("line")),
            message=message,
            fixable=u.Infra.is_rule_fixable(rule, module),
        )

    @staticmethod
    def _violation_key(
        violation: m.Infra.CensusViolation,
    ) -> tuple[str, str, int, str]:
        return (
            violation.module,
            violation.rule,
            violation.line,
            violation.message,
        )

    @classmethod
    def _reconcile_namespace_violations(
        cls,
        *,
        project_path: Path,
        ctx: m.Infra.FixContext,
        initial_violations: Sequence[m.Infra.CensusViolation],
    ) -> None:
        """Classify initial namespace violations as fixed or still skipped."""
        if not initial_violations:
            return
        remaining_result = cls._namespace_violations(project_path)
        if remaining_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=remaining_result.error or "namespace validation failed",
            )
            return
        remaining_keys = {
            cls._violation_key(violation)
            for violation in remaining_result.unwrap_or(())
        }
        for violation in initial_violations:
            if (
                violation.fixable
                and cls._violation_key(violation) not in remaining_keys
            ):
                ctx.violations_fixed.append(violation)
                continue
            ctx.violations_skipped.append(violation)

    def fix_workspace(self) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on all projects in workspace."""
        projects_result = u.Infra.discover_projects(self.workspace_root)
        if not projects_result.is_success:
            return []
        results: MutableSequence[m.Infra.AutoFixResult] = []
        discovered: Sequence[m.Infra.ProjectInfo] = projects_result.unwrap()
        for project in discovered:
            if project.name in c.Infra.EXCLUDED_PROJECTS:
                continue
            if (project.path / c.Infra.Files.GO_MOD).exists():
                continue
            results.append(self.fix_project(project.path))
        return results


__all__ = ["FlextInfraCodegenFixer"]
