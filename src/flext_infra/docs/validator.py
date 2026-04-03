"""Documentation validator service.

Validates documentation for ADR skill references and generates
validation reports, returning structured r reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import JsonValue, ValidationError

from flext_core import FlextLogger
from flext_infra import c, m, r, t, u

logger = FlextLogger.create_module_logger(__name__)


class FlextInfraDocValidator:
    """Infrastructure service for documentation validation.

    Checks ADR skill references and generates validation reports,
    returning structured r reports.
    """

    @staticmethod
    def _has_adr_reference(skill_path: Path) -> bool:
        """Check whether a skill file contains an ADR reference."""
        text = skill_path.read_text(
            encoding=c.Infra.Encoding.DEFAULT,
            errors=c.Infra.IGNORE,
        ).lower()
        return "adr" in text

    @staticmethod
    def _maybe_write_todo(
        scope: m.Infra.DocScope,
        *,
        apply_mode: bool,
    ) -> bool:
        """Write a TODOS.md file for the scope if apply mode is enabled."""
        if scope.name == c.Infra.ReportKeys.ROOT or not apply_mode:
            return False
        path = scope.path / "TODOS.md"
        content = "# TODOS\n\n- [ ] Resolve documentation validation findings from `.reports/docs/validate-report.md`.\n"
        _ = path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
        return True

    def validate(
        self,
        workspace_root: Path,
        *,
        project: str | None = None,
        projects: str | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        check: str = "all",
        apply: bool = False,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation validation across project scopes.

        Args:
            workspace_root: Workspace root directory.
            project: Single project name filter.
            projects: Comma-separated project names.
            output_dir: Report output directory.
            check: Validation checks to run.
            apply: Write TODOS.md if needed.

        Returns:
            r with list of ValidateReport objects.

        """
        return u.Infra.run_scoped(
            workspace_root,
            project=project,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._validate_scope(
                scope,
                check=check,
                apply_mode=apply,
            ),
        )

    def execute_command(self, params: m.Infra.DocsValidateInput) -> r[bool]:
        """CLI handler — accepts input model, delegates to validate."""
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        result = self.validate(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            check="all" if params.check else "",
            apply=params.apply,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "validate failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.Status.FAIL
        )
        if failures:
            return r[bool].fail(f"Validate found {failures} failure(s)")
        return r[bool].ok(True)

    @staticmethod
    def _load_required_skills(workspace_root: Path) -> t.StrSequence | None:
        """Load required skill names from architecture config. Returns None on error."""
        config = workspace_root / "docs/architecture/architecture_config.json"
        if not config.exists():
            return []
        payload_result = u.Infra.read_json(config)
        if payload_result.is_failure:
            return None
        configured = FlextInfraDocValidator._extract_required_skills_list(
            payload_result.value,
        )
        if configured is None:
            return []
        try:
            required_items: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(
                configured,
                strict=True,
            )
            return [str(item) for item in required_items if item]
        except ValidationError:
            return []

    @staticmethod
    def _extract_required_skills_list(
        payload: Mapping[str, JsonValue],
    ) -> list[JsonValue] | None:
        """Extract the required_skills list from config payload. None if absent/invalid."""
        docs_validation = payload.get("docs_validation")
        if not isinstance(docs_validation, Mapping):
            return None
        configured = docs_validation.get("required_skills")
        if not isinstance(configured, list):
            return None
        return configured

    def _run_adr_skill_check(
        self, workspace_root: Path
    ) -> t.Infra.Pair[int, t.StrSequence]:
        """Run ADR skill check and return exit code with missing skill names."""
        loaded = self._load_required_skills(workspace_root)
        if loaded is None:
            return (1, [])
        required = loaded or [
            "rules-docs",
            "scripts-maintenance",
            "readme-standardization",
        ]
        skills_root = workspace_root / ".claude/skills"
        missing: MutableSequence[str] = []
        for name in required:
            skill = skills_root / name / "SKILL.md"
            if not skill.exists() or not self._has_adr_reference(skill):
                missing.append(name)
        return (0 if not missing else 1, missing)

    def _validate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        check: str,
        apply_mode: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Run validation for a single project scope."""
        status = c.Infra.Status.OK
        message = "validation passed"
        missing_adr_skills: t.StrSequence = []
        config_exists = (
            scope.path / "docs/architecture/architecture_config.json"
        ).exists()
        if (
            scope.name == c.Infra.ReportKeys.ROOT
            and config_exists
            and (check in {"adr-skill", "all"})
        ):
            code, missing = self._run_adr_skill_check(scope.path)
            missing_adr_skills = missing
            if code != 0:
                status = c.Infra.Status.FAIL
                message = f"missing adr references in skills: {', '.join(missing)}"
        wrote_todo = self._maybe_write_todo(scope, apply_mode=apply_mode)
        adr_skills_json: list[JsonValue] = list(missing_adr_skills)
        payload: Mapping[str, JsonValue] = {
            c.Infra.ReportKeys.SUMMARY: {
                c.Infra.ReportKeys.SCOPE: scope.name,
                "result": status,
                c.Infra.ReportKeys.MESSAGE: message,
                "apply": apply_mode,
            },
            "details": {
                "missing_adr_skills": adr_skills_json,
                "todo_written": wrote_todo,
            },
        }
        _ = u.Infra.write_json(
            scope.report_dir / "validate-summary.json",
            payload,
        )
        _ = u.Infra.write_markdown(
            scope.report_dir / "validate-report.md",
            [
                "# Docs Validate Report",
                "",
                f"Scope: {scope.name}",
                f"Result: {status}",
                f"Message: {message}",
                f"TODO written: {int(wrote_todo)}",
            ],
        )
        logger.info(
            "docs_validate_scope_completed",
            project=scope.name,
            phase=c.Infra.Verbs.VALIDATE,
            result=status,
            reason=message,
        )
        return m.Infra.DocsPhaseReport(
            phase="validate",
            scope=scope.name,
            result=status,
            message=message,
            missing_adr_skills=missing_adr_skills,
            todo_written=wrote_todo,
            passed=status == c.Infra.Status.OK,
        )


__all__ = ["FlextInfraDocValidator"]
