"""Workspace-wide ENFORCE-039/041/043/044 auditor.

Walks every flext project's source tree and emits ``m.Infra.Census.Violation``
records for the four AST-detectable A-PT rules. Detection is delegated to
the canonical pure-AST finders on
``FlextUtilitiesBeartypeEngine.find_<rule>`` — the same SSOT consumed by
the runtime ``check_<tag>`` hooks. This auditor handles workspace
discovery, per-file source-skipping (third-party paths via
``c.ENFORCE_NON_WORKSPACE_PATH_MARKERS``), and violation construction —
nothing about AST detection lives in this module.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import (
    Iterator,
    Sequence,
)
from pathlib import Path
from typing import Final

from flext_cli import cli
from flext_core import (
    FlextConstantsEnforcement as cce,
    FlextUtilitiesBeartypeEngine as ube,
)

from flext_infra import c, m, p, r, t, u

_ENFORCE_039: Final[str] = "ENFORCE-039"
_ENFORCE_041: Final[str] = "ENFORCE-041"
_ENFORCE_043: Final[str] = "ENFORCE-043"
_ENFORCE_044: Final[str] = "ENFORCE-044"
_KIND: Final[str] = "enforcement"


class FlextInfraEnforcementAuditor:
    """Workspace walker that emits violations for the 4 A-PT runtime rules."""

    def __init__(self, *, workspace_root: Path) -> None:
        """Bind auditor to a workspace root."""
        self._workspace_root = workspace_root.resolve()

    def audit_workspace(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Run the audit across selected projects, return aggregated report."""
        project_roots = self._select_projects(project_names=project_names)
        project_reports: list[m.Infra.Census.ProjectReport] = [
            self._audit_project(project_root) for project_root in project_roots
        ]
        return r[m.Infra.Census.WorkspaceReport].ok(
            m.Infra.Census.WorkspaceReport(
                projects=tuple(project_reports),
                total_violations=sum(rep.violations_total for rep in project_reports),
            ),
        )

    def _select_projects(
        self,
        *,
        project_names: t.StrSequence | None,
    ) -> Sequence[Path]:
        roots = u.Infra.discover_project_roots(workspace_root=self._workspace_root)
        if project_names is None:
            return roots
        wanted = set(project_names)
        return [root for root in roots if root.name in wanted]

    def _audit_project(
        self,
        project_root: Path,
    ) -> m.Infra.Census.ProjectReport:
        violations: list[m.Infra.Census.Violation] = []
        for py_file in self._iter_py_files(project_root):
            violations.extend(self._audit_file(project_root.name, py_file))
        return m.Infra.Census.ProjectReport(
            project=project_root.name,
            violations=tuple(violations),
            violations_total=len(violations),
        )

    def _iter_py_files(self, project_root: Path) -> Iterator[Path]:
        src_dir = project_root / "src"
        root = src_dir if src_dir.is_dir() else project_root
        for path in root.rglob("*.py"):
            path_str = str(path)
            if any(
                marker in path_str for marker in cce.ENFORCE_NON_WORKSPACE_PATH_MARKERS
            ):
                continue
            yield path

    def _audit_file(
        self,
        project_name: str,
        path: Path,
    ) -> Iterator[m.Infra.Census.Violation]:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return
        is_flext_core = any(
            marker in str(path) for marker in cce.ENFORCE_FLEXT_CORE_PATH_MARKERS
        )
        if not is_flext_core:
            for cast_node in ube.find_cast_calls(tree):
                yield self._violation(
                    project_name=project_name,
                    path=path,
                    line=cast_node.lineno,
                    rule_id=_ENFORCE_039,
                    obj_name="cast",
                    obj_kind="call",
                )
        for mr_node in ube.find_model_rebuild_calls(tree):
            yield self._violation(
                project_name=project_name,
                path=path,
                line=mr_node.lineno,
                rule_id=_ENFORCE_041,
                obj_name=cce.EnforceAstHookSymbol.MODEL_REBUILD_ATTR,
                obj_kind="call",
            )
        for func_node in ube.find_pass_through_wrappers(tree):
            yield self._violation(
                project_name=project_name,
                path=path,
                line=func_node.lineno,
                rule_id=_ENFORCE_043,
                obj_name=func_node.name,
                obj_kind="function",
            )
        for probe_node, builtin, attr in ube.find_private_attr_probes(tree):
            yield self._violation(
                project_name=project_name,
                path=path,
                line=probe_node.lineno,
                rule_id=_ENFORCE_044,
                obj_name=f"{builtin}({attr!r})",
                obj_kind="attr_probe",
            )

    @staticmethod
    def _violation(
        *,
        project_name: str,
        path: Path,
        line: int,
        rule_id: str,
        obj_name: str,
        obj_kind: str,
    ) -> m.Infra.Census.Violation:
        return m.Infra.Census.Violation(
            project=project_name,
            object_name=obj_name,
            object_kind=obj_kind,
            kind=_KIND,
            severity=c.Infra.GateSeverity.ERROR.value,
            file_path=str(path),
            line=line,
            fixable=rule_id in {_ENFORCE_039, _ENFORCE_041, _ENFORCE_043},
            fix_action=rule_id,
        )

    @staticmethod
    def render_text(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render a workspace audit report as plain text."""
        lines = [
            "SSOT Enforcement Audit Report",
            f"Projects scanned: {len(report.projects)}",
            f"Total violations: {report.total_violations}",
        ]
        for proj in report.projects:
            if proj.violations_total == 0:
                continue
            lines.append(f"  {proj.project} ({proj.violations_total}):")
            lines.extend(
                f"    {viol.fix_action} @ {viol.file_path}:{viol.line} "
                f"({viol.object_kind}={viol.object_name})"
                for viol in proj.violations
            )
        return "\n".join(lines)

    @classmethod
    def _apply_fixes(
        cls,
        *,
        workspace_root: Path,
        violations: Sequence[m.Infra.Census.Violation],
    ) -> int:
        """Apply rope-backed inline refactor for every ENFORCE-043 violation.

        Returns the count of successfully inlined wrappers. ENFORCE-039 and
        ENFORCE-041 stay manual-review-only — their auto-fix is semantically
        risky (cast removal narrows types, model_rebuild deletion breaks
        forward-ref resolution); the audit report flags them but does not
        rewrite. ENFORCE-044 is detect-only by design.
        """
        targets = tuple(v for v in violations if v.fix_action == _ENFORCE_043)
        if not targets:
            return 0
        rope_project = u.Infra.init_rope_project(workspace_root.resolve())
        try:
            return sum(
                1
                for viol in targets
                if cls._inline_pass_through(rope_project=rope_project, violation=viol)
            )
        finally:
            rope_project.close()

    @staticmethod
    def _inline_pass_through(
        *,
        rope_project: t.Infra.RopeProject,
        violation: m.Infra.Census.Violation,
    ) -> bool:
        """Inline one ENFORCE-043 pass-through wrapper via rope.

        Safe by design: ``rope.refactor.inline.create_inline`` rewrites every
        call site of the wrapper to invoke the inner callable directly, then
        deletes the wrapper definition. Failures (rope cannot resolve the
        symbol, the wrapper is recursively used, etc.) return ``False`` and
        leave the source untouched.
        """
        from rope.base.exceptions import RopeError  # noqa: PLC0415
        from rope.base.resources import File  # noqa: PLC0415
        from rope.refactor.inline import create_inline  # noqa: PLC0415

        path = Path(violation.file_path).resolve()
        try:
            resource = rope_project.get_resource(
                str(path.relative_to(Path(rope_project.address).resolve()))
            )
        except (ValueError, RopeError):
            return False
        if not isinstance(resource, File):
            return False
        source = resource.read()
        lines = source.splitlines(keepends=False)
        if violation.line < 1 or violation.line > len(lines):
            return False
        target_line = lines[violation.line - 1]
        if violation.object_name not in target_line:
            return False
        offset = sum(
            len(line) + 1 for line in lines[: violation.line - 1]
        ) + target_line.index(violation.object_name)
        try:
            inline = create_inline(rope_project, resource, offset)
            changes = inline.get_changes(remove=True, only_current=False)
            changes.do()
        except (RopeError, ValueError, IndexError):
            return False
        return True

    @classmethod
    def execute_command(
        cls,
        params: m.Infra.RefactorAuditInput,
    ) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Run the audit from the canonical CLI input model.

        When ``params.apply`` is true, rope-rewrite every fixable violation
        (ENFORCE-043 only — see ``_apply_fixes``) and re-audit to surface
        remaining violations. Otherwise, render the dry-run report and fail
        the result when violations are present.
        """
        auditor = cls(workspace_root=params.workspace_path)
        result = auditor.audit_workspace(project_names=params.project_names)
        if result.failure:
            return result
        report = result.value
        if params.apply and report.total_violations:
            all_violations = tuple(
                v for proj in report.projects for v in proj.violations
            )
            fixed_count = cls._apply_fixes(
                workspace_root=params.workspace_path,
                violations=all_violations,
            )
            cli.display_text(
                f"Applied {fixed_count} auto-fix(es) for ENFORCE-043. Re-running audit…"
            )
            return auditor.audit_workspace(project_names=params.project_names)
        cli.display_text(cls.render_text(report))
        if report.total_violations:
            return r[m.Infra.Census.WorkspaceReport].fail(
                f"{report.total_violations} enforcement violation(s) found",
            )
        return result


__all__: list[str] = ["FlextInfraEnforcementAuditor"]
