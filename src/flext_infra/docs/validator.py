"""Documentation validator service."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra import c, m, r, u
from flext_infra.docs.base import FlextInfraDocServiceBase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraDocValidator(FlextInfraDocServiceBase):
    """Validate the governed docs contract for root and FLEXT projects."""

    def validate_workspace(
        self, request: m.Infra.DocsGenerateRequest
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Validate documentation across the workspace root and governed projects."""
        return self.run_scoped_docs(
            request.workspace_root,
            projects=request.projects,
            output_dir=request.output_dir,
            handler=lambda scope: self._validate_scope(scope, apply_mode=request.apply),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs validation flow."""
        result = self.validate_workspace(
            m.Infra.DocsGenerateRequest(
                workspace_root=self.workspace_root,
                projects=self.selected_projects,
                output_dir=self.output_dir,
                apply=self.apply_changes,
            )
        )
        return self._propagate_phase_outcome(
            "validate",
            result,
            failure_predicate=lambda report: report.result == c.Infra.ResultStatus.FAIL,
        )

    def _run_adr_skill_check(
        self, workspace_root: Path
    ) -> p.Result[t.StrSequence]:
        """Run the ADR skill validation check for the root docs scope."""
        required_result = u.Infra.docs_load_required_skills(workspace_root)
        if required_result.failure:
            error = required_result.error
            if error is None:
                msg = "ADR skill configuration failed without an error"
                raise RuntimeError(msg)
            return r[t.StrSequence].fail(error)
        required_skills = required_result.value
        skills_root = workspace_root / ".agents/skills"
        missing: list[str] = []
        for skill_name in required_skills:
            skill_path = skills_root / skill_name / "SKILL.md"
            if not skill_path.exists() or not (
                u.Infra.docs_has_adr_reference(skill_path)
            ):
                missing.append(skill_name)
        return r[t.StrSequence].ok(tuple(missing))

    def _validate_scope(
        self, scope: m.Infra.DocScope, *, apply_mode: bool
    ) -> m.Infra.DocsPhaseReport:
        """Validate one docs scope and persist the standard reports."""
        status = c.Infra.ResultStatus.OK
        messages: list[str] = []
        missing_adr_skills: t.StrSequence = ()
        if scope.name == c.Infra.RK_ROOT:
            adr_result = self._run_adr_skill_check(scope.path)
            if adr_result.failure:
                status = c.Infra.ResultStatus.FAIL
                error = adr_result.error
                if error is None:
                    msg = "ADR skill validation failed without an error"
                    raise RuntimeError(msg)
                messages.append(error)
            else:
                missing_adr_skills = adr_result.value
                if missing_adr_skills:
                    status = c.Infra.ResultStatus.FAIL
                    messages.append(
                        "missing adr references in skills: "
                        f"{', '.join(missing_adr_skills)}"
                    )
        missing_paths = u.Infra.docs_missing_required_paths(scope)
        if missing_paths:
            status = c.Infra.ResultStatus.FAIL
            messages.append(f"missing required docs files: {', '.join(missing_paths)}")
        contract_messages = u.Infra.docs_contract_messages(scope)
        if contract_messages:
            status = c.Infra.ResultStatus.FAIL
            messages.extend(contract_messages)
        todo_result = u.Infra.docs_write_todo(scope, apply_mode=apply_mode)
        if todo_result.failure:
            status = c.Infra.ResultStatus.FAIL
            error = todo_result.error
            if error is None:
                msg = "docs TODO write failed without an error"
                raise RuntimeError(msg)
            messages.append(error)
            wrote_todo = False
        else:
            wrote_todo = todo_result.value
        message = "; ".join(messages) if messages else "validation passed"
        report = m.Infra.DocsPhaseReport(
            phase="validate",
            scope=scope.name,
            result=status,
            message=message,
            missing_adr_skills=missing_adr_skills,
            todo_written=wrote_todo,
            passed=status == c.Infra.ResultStatus.OK,
        )
        write_result = u.Infra.docs_write_validate_reports(scope, report)
        if write_result.failure:
            report = u.Infra.docs_persistence_failure(
                phase="validate",
                scope=scope.name,
                error=write_result.error,
                report=report,
            )
        self.logger.info(
            "docs_validate_scope_completed",
            project=scope.name,
            phase=c.Infra.VERB_VALIDATE,
            result=report.result,
            reason=report.message,
        )
        return report


__all__: list[str] = ["FlextInfraDocValidator"]
