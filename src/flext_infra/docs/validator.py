"""Documentation validator service."""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, m, p, r, t, u


class FlextInfraDocValidator(FlextInfraProjectSelectionServiceBase[bool]):
    """Validate the governed docs contract for root and FLEXT projects."""

    output_dir: Annotated[
        Path | None,
        m.Field(description="Docs output dir"),
    ] = Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR)

    def validate_workspace(
        self,
        value: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: Path | str = Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR),
        apply: bool = False,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Validate documentation across the workspace root and governed projects."""
        return self.run_scoped_docs(
            value,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._validate_scope(
                scope,
                apply_mode=apply,
            ),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs validation flow."""
        result = self.validate_workspace(
            self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.output_dir or Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR),
            apply=self.apply_changes,
        )
        if result.failure:
            return r[bool].fail(result.error or "validate failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.ResultStatus.FAIL
        )
        if failures:
            return r[bool].fail(f"Validate found {failures} failure(s)")
        return r[bool].ok(True)

    def _run_adr_skill_check(
        self,
        workspace_root: Path,
    ) -> t.Infra.Pair[int, t.StrSequence]:
        """Run the ADR skill validation check for the root docs scope."""
        required_result = u.Infra.docs_load_required_skills(workspace_root)
        if required_result.failure:
            self.logger.warning(
                "adr_skill_check_failed",
                error=required_result.error,
            )
            return (1, [])
        required_skills = required_result.value or [
            "rules-docs",
            "scripts-maintenance",
            "readme-standardization",
        ]
        skills_root = workspace_root / ".agents/skills"
        missing: list[str] = []
        for skill_name in required_skills:
            skill_path = skills_root / skill_name / "SKILL.md"
            if not skill_path.exists() or not u.Infra.docs_has_adr_reference(
                skill_path
            ):
                missing.append(skill_name)
        return (0 if not missing else 1, missing)

    def _validate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        apply_mode: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Validate one docs scope and persist the standard reports."""
        status = c.Infra.ResultStatus.OK
        messages: list[str] = []
        missing_adr_skills: t.StrSequence = []
        config_exists = (
            scope.path / "docs/architecture/architecture_config.json"
        ).exists()
        if scope.name == c.Infra.RK_ROOT and config_exists:
            code, missing = self._run_adr_skill_check(scope.path)
            missing_adr_skills = missing
            if code != 0:
                status = c.Infra.ResultStatus.FAIL
                messages.append(
                    f"missing adr references in skills: {', '.join(missing)}"
                )
        missing_paths = u.Infra.docs_missing_required_paths(scope)
        if missing_paths:
            status = c.Infra.ResultStatus.FAIL
            messages.append(f"missing required docs files: {', '.join(missing_paths)}")
        contract_messages = u.Infra.docs_contract_messages(scope)
        if contract_messages:
            status = c.Infra.ResultStatus.FAIL
            messages.extend(contract_messages)
        message = "; ".join(messages) if messages else "validation passed"
        wrote_todo = u.Infra.docs_write_todo(scope, apply_mode=apply_mode)
        report = m.Infra.DocsPhaseReport(
            phase="validate",
            scope=scope.name,
            result=status,
            message=message,
            missing_adr_skills=missing_adr_skills,
            todo_written=wrote_todo,
            passed=status == c.Infra.ResultStatus.OK,
        )
        u.Infra.docs_write_validate_reports(scope, report)
        self.logger.info(
            "docs_validate_scope_completed",
            project=scope.name,
            phase=c.Infra.VERB_VALIDATE,
            result=status,
            reason=message,
        )
        return report


__all__: list[str] = ["FlextInfraDocValidator"]
