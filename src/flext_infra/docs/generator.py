"""Documentation generator service driven by code, exports, and docstrings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, m, r, u
from flext_infra.docs import FlextInfraDocServiceBase, FlextInfraDocsGeneratorBundle

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDocGenerator(
    FlextInfraDocServiceBase[m.Infra.DocsPhaseReports],
    FlextInfraDocsGeneratorBundle,
):
    """Generate managed docs artifacts from package exports and docstrings."""

    # Why (X-47): standalone `docs generate` renders the workspace root by
    # default; codegen conform overrides this per plan (DECLARED scope
    # excludes the root repository from the render entirely).
    include_root: Annotated[
        bool,
        m.Field(description="Render the workspace root as a docs output scope"),
    ] = True

    @classmethod
    def execute_request(
        cls, request: m.Infra.DocsGenerateRequest
    ) -> p.Result[m.Infra.DocsPhaseReports]:
        """Expose one fixed-effect CLI request without inherited mode controls.

        Returns:
            Published reports, or the original failure.

        """
        owner = cls(repository_root=request.repository_root)
        return owner.generate(request).map(m.Infra.DocsPhaseReports.model_validate)

    def generate(
        self,
        request: m.Infra.DocsGenerateRequest,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Render, plan and publish generated docs through the shared publisher.

        Returns:
            Published reports, or the original failure.

        """
        report_type = r[Sequence[m.Infra.DocsPhaseReport]]
        prepared = self._prepare_request(request)
        if prepared.failure:
            return report_type.from_failure(prepared)
        bundle = prepared.value
        plans = self.plan_files(bundle)
        if plans.failure:
            return report_type.from_failure(plans)
        published = u.Infra.publish_codegen_plans(bundle.repository_root, plans.value)
        if published.failure:
            return report_type.from_failure(published)
        return self._generation_reports(bundle, frozenset(published.value))

    def _generation_reports(
        self,
        bundle: m.Infra.DocsGenerationBundle,
        written: frozenset[Path],
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Report only destinations written by the shared publisher.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.DocsPhaseReport]]``.

        """
        reports: list[m.Infra.DocsPhaseReport] = []
        first_scope = bundle.scopes[0].scope
        root_scope = first_scope if first_scope.name == c.Infra.RK_ROOT else None
        for scoped in bundle.scopes:
            scope = scoped.scope
            paths = tuple(scope.path / item.relative_path for item in scoped.artifacts)
            changed = tuple(path for path in paths if path in written)
            collocated = self._is_collocated_workspace_project(
                scope,
                root_scope=root_scope,
            )
            metadata_paths = tuple(
                plan.path
                for plan in bundle.metadata_files
                if plan.project == scope.path and not collocated
            )
            all_paths = (*paths, *metadata_paths)
            report = m.Infra.DocsPhaseReport(
                phase="generate",
                scope=scope.name,
                changed_files=sum(path in written for path in all_paths),
                generated=len(changed),
                applied=True,
                source="code-docstring-ssot",
                items=tuple(
                    m.Infra.DocsPhaseItemModel(
                        phase="generate",
                        path=str(path),
                        written=path in written,
                    )
                    for path in all_paths
                ),
                result=c.Infra.ResultStatus.OK,
                reason=(
                    "aggregate-root-owner"
                    if collocated
                    else f"changes:{sum(path in written for path in all_paths)}"
                ),
                passed=True,
            )
            self.logger.info(
                "docs_generate_scope_planned",
                project=scope.name,
                phase="generate",
                result=report.result,
                reason=report.reason,
            )
            reports.append(report)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(tuple(reports))

    @staticmethod
    def plan_files(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Bind one prepared render bundle to exact live destination states.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.CodegenFilePlan, ...]]``.

        """
        return u.Infra.docs_file_plans(bundle)

    def prepare_bundle(
        self,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Render the configured docs inventory once.

        Returns:
            The resulting ``p.Result[m.Infra.DocsGenerationBundle]``.

        """
        return self._prepare_request(self._configured_request(), declared_files)

    @override
    def execute(
        self,
    ) -> p.Result[m.Infra.DocsPhaseReports]:
        """Execute the configured docs generation flow.

        Returns:
            The published reports in the canonical model-valued service result.

        """
        return self.generate(self._configured_request()).map(
            m.Infra.DocsPhaseReports.model_validate
        )

    def _configured_request(self) -> m.Infra.DocsGenerateRequest:
        """Return the pure render request of this configured generator.

        Returns:
            The pure render request of this configured generator.

        """
        return m.Infra.DocsGenerateRequest(
            repository_root=self.repository_root,
            projects=self.selected_projects,
            output_dir=self.output_dir,
            include_root=self.include_root,
        )


__all__: list[str] = ["FlextInfraDocGenerator"]
