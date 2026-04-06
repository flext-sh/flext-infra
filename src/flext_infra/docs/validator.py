"""Documentation validator service."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.base import s


class FlextInfraDocValidator(s[bool]):
    """Validate the governed docs contract for root and FLEXT projects."""

    selected_projects: Annotated[
        t.StrSequence | None,
        Field(default=None, description="Selected projects", exclude=True),
    ] = None
    docs_output_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            description="Docs output dir",
            exclude=True,
        ),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR

    def validate(
        self,
        value: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        check: str = "all",
        apply: bool = False,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Validate documentation across the workspace root and governed projects."""
        return u.Infra.run_scoped(
            value,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._validate_scope(
                scope,
                check=check,
                apply_mode=apply,
            ),
        )

    def validate_docs(
        self,
        value: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        check: str = "all",
        apply: bool = False,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Backward-compatible alias for the canonical validate entrypoint."""
        return self.validate(
            value,
            projects=projects,
            output_dir=output_dir,
            check=check,
            apply=apply,
        )

    @override
    def execute(self) -> r[bool]:
        """Execute the configured docs validation flow."""
        result = self.validate(
            self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
            check="all" if self.check_only else "",
            apply=self.apply_changes,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "validate failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.Status.FAIL
        )
        if failures:
            return r[bool].fail(f"Validate found {failures} failure(s)")
        return r[bool].ok(True)

    @classmethod
    @override
    def execute_command(
        cls,
        params: s[bool] | m.Infra.DocsValidateInput,
    ) -> r[bool]:
        """Normalize docs CLI input into the canonical validator service model."""
        if isinstance(params, m.Infra.DocsValidateInput):
            service = cls.model_validate({
                "workspace_root": params.workspace_path,
                "apply_changes": params.apply,
                "check_only": params.check,
                "selected_projects": params.project_names,
                "docs_output_dir": params.output_dir,
            })
            return service.execute()
        return params.execute()

    def _run_adr_skill_check(
        self,
        workspace_root: Path,
    ) -> t.Infra.Pair[int, t.StrSequence]:
        """Run the ADR skill validation check for the root docs scope."""
        required = u.Infra.docs_load_required_skills(workspace_root)
        if required is None:
            return (1, [])
        required_skills = required or [
            "rules-docs",
            "scripts-maintenance",
            "readme-standardization",
        ]
        skills_root = workspace_root / ".claude/skills"
        missing: list[str] = []
        for skill_name in required_skills:
            skill_path = skills_root / skill_name / "SKILL.md"
            if not skill_path.exists() or not u.Infra.docs_has_adr_reference(
                skill_path
            ):
                missing.append(skill_name)
        return (0 if not missing else 1, missing)

    def _has_adr_reference(self, skill_path: Path) -> bool:
        """Delegate ADR reference detection to ``u.Infra``."""
        return u.Infra.docs_has_adr_reference(skill_path)

    def _maybe_write_todo(
        self,
        scope: m.Infra.DocScope,
        *,
        apply_mode: bool,
    ) -> bool:
        """Delegate optional TODO creation to ``u.Infra``."""
        return u.Infra.docs_write_todo(scope, apply_mode=apply_mode)

    def _validate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        check: str,
        apply_mode: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Validate one docs scope and persist the standard reports."""
        _ = check
        status = c.Infra.Status.OK
        messages: list[str] = []
        missing_adr_skills: t.StrSequence = []
        config_exists = (
            scope.path / "docs/architecture/architecture_config.json"
        ).exists()
        if scope.name == c.Infra.ReportKeys.ROOT and config_exists:
            code, missing = self._run_adr_skill_check(scope.path)
            missing_adr_skills = missing
            if code != 0:
                status = c.Infra.Status.FAIL
                messages.append(
                    f"missing adr references in skills: {', '.join(missing)}"
                )
        missing_paths = u.Infra.docs_missing_required_paths(scope)
        if missing_paths:
            status = c.Infra.Status.FAIL
            messages.append(f"missing required docs files: {', '.join(missing_paths)}")
        contract_messages = u.Infra.docs_contract_messages(scope)
        if contract_messages:
            status = c.Infra.Status.FAIL
            messages.extend(contract_messages)
        message = "; ".join(messages) if messages else "validation passed"
        wrote_todo = self._maybe_write_todo(scope, apply_mode=apply_mode)
        report = m.Infra.DocsPhaseReport(
            phase="validate",
            scope=scope.name,
            result=status,
            message=message,
            missing_adr_skills=missing_adr_skills,
            todo_written=wrote_todo,
            passed=status == c.Infra.Status.OK,
        )
        u.Infra.docs_write_validate_reports(scope, report)
        self.logger.info(
            "docs_validate_scope_completed",
            project=scope.name,
            phase=c.Infra.Verbs.VALIDATE,
            result=status,
            reason=message,
        )
        return report


__all__ = ["FlextInfraDocValidator"]
