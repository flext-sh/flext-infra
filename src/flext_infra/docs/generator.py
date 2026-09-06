"""Documentation generator service driven by code, exports, and docstrings."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, m, t, u

from ._generator_bundle import FlextInfraDocGeneratorBundleMixin
from .base import FlextInfraDocServiceBase

if TYPE_CHECKING:
    from flext_infra import p

type _DocsScopePlan = tuple[m.Infra.DocScope, tuple[m.Infra.CodegenFilePlan, ...]]


class FlextInfraDocGenerator(
    FlextInfraDocServiceBase, FlextInfraDocGeneratorBundleMixin
):
    """Generate managed docs artifacts from package exports and docstrings."""

    def generate(
        self, request: m.Infra.DocsGenerateRequest
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Check docs plans; publication belongs to the conform transaction."""
        prepared = self._prepare_request(request)
        if prepared.failure:
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].from_failure(prepared)
        planned = self._plan_bundle(prepared.value)
        if planned.failure:
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].from_failure(planned)
        reports: list[m.Infra.DocsPhaseReport] = []
        repository_root = prepared.value.scopes[0].scope.path
        for scope, plans in planned.value:
            changed = tuple(
                plan for plan in plans if u.Infra.codegen_file_requires_effect(plan)
            )
            collocated = self._is_collocated_workspace_project(
                scope, workspace_root=repository_root
            )
            report = m.Infra.DocsPhaseReport(
                phase="generate",
                scope=scope.name,
                changed_files=len(changed),
                generated=0,
                applied=False,
                source="code-docstring-ssot",
                items=tuple(
                    m.Infra.DocsPhaseItemModel(
                        phase="generate", path=str(plan.path), written=False
                    )
                    for plan in plans
                ),
                result=(
                    c.Infra.ResultStatus.OK
                    if not changed
                    else c.Infra.ResultStatus.FAIL
                ),
                reason=(
                    "aggregate-root-owner" if collocated else f"changes:{len(changed)}"
                ),
                passed=not changed,
            )
            self.logger.info(
                "docs_generate_scope_planned",
                project=scope.name,
                phase="generate",
                result=report.result,
                reason=report.reason,
            )
            reports.append(report)
        return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok(tuple(reports))

    def plan_files(
        self, bundle: m.Infra.DocsGenerationBundle
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Bind one prepared render bundle to exact live destination states."""
        return u.Infra.docs_file_plans(bundle)

    def required_directories(
        self, bundle: m.Infra.DocsGenerationBundle
    ) -> p.Result[tuple[Path, ...]]:
        """Derive target parent chains from the exact prepared render bundle."""
        repository_root = bundle.scopes[0].scope.path
        stable = u.Infra.docs_verify_sources(
            repository_root,
            bundle.source_states,
            extra_roots=tuple(scoped.scope.path for scoped in bundle.scopes),
        )
        if stable.failure:
            return r[tuple[Path, ...]].from_failure(stable)
        return u.Infra.docs_required_directories(bundle)

    def prepare_bundle(self) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Freeze the configured render and all of its authenticated inputs."""
        return self._prepare_request(self._configured_request())

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs generation flow."""
        return self._propagate_phase_outcome(
            "generate",
            self.generate(
                m.Infra.DocsGenerateRequest(
                    workspace_root=self.repository_root,
                    projects=self.selected_projects,
                    output_dir=self.output_dir,
                    apply=self.apply_changes,
                )
            ),
            failure_predicate=lambda report: not report.passed,
        )

    def _configured_request(self) -> m.Infra.DocsGenerateRequest:
        """Return the check-only request shared by both planner entry points."""
        return m.Infra.DocsGenerateRequest(
            workspace_root=self.repository_root,
            projects=self.selected_projects,
            output_dir=self.output_dir,
            apply=False,
        )

    @staticmethod
    def _plan_bundle(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[_DocsScopePlan, ...]]:
        """Build every scope plan from one already prepared docs bundle."""
        planned = u.Infra.docs_file_plans(bundle)
        if planned.failure:
            return r[tuple[_DocsScopePlan, ...]].from_failure(planned)
        scope_plans: list[_DocsScopePlan] = []
        offset = 0
        for scoped in bundle.scopes:
            size = len(scoped.artifacts)
            scope_plans.append((scoped.scope, planned.value[offset : offset + size]))
            offset += size
        return r[tuple[_DocsScopePlan, ...]].ok(tuple(scope_plans))


__all__: list[str] = ["FlextInfraDocGenerator"]
