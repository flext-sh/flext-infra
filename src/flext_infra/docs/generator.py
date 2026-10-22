"""Documentation generator service driven by code, exports, and docstrings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.docs import FlextInfraDocGeneratorBundleMixin, FlextInfraDocServiceBase

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import p

type _DocsScopePlan = t.Pair[m.Infra.DocScope, t.VariadicTuple[m.Infra.CodegenFilePlan]]


class FlextInfraDocGenerator(
    FlextInfraDocServiceBase[m.Infra.DocsPhaseReports],
    FlextInfraDocGeneratorBundleMixin,
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
            Committed reports, or the original failure with prior committed effects.

        """
        owner = cls(repository_root=request.repository_root)
        return owner.generate(request).map(m.Infra.DocsPhaseReports.model_validate)

    def generate(
        self,
        request: m.Infra.DocsGenerateRequest,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Publish generated docs through the existing durable file lifecycle.

        Returns:
            Committed reports on success. Failure preserves its original cause and
            ``error_data.committed_reports`` for preceding successful batches only.

        """
        reports: list[m.Infra.DocsPhaseReport] = []
        receipts: list[m.Infra.CodegenPhaseOutcome] = []
        for prepared in self._prepare_batches(
            request,
            publication_receipts=receipts,
        ):
            if prepared.failure:
                terminal: p.FailureLike = prepared
            else:
                published = self.publish_batch(
                    prepared.value, publication_receipts=receipts
                )
                if published.success:
                    reports.extend(published.value)
                    continue
                terminal = published
            data: t.JsonDict = dict(terminal.error_data or {})
            data["committed_reports"] = [
                dict(
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                        report.model_dump(
                            mode="json",
                            include={
                                "phase": True,
                                "scope": True,
                                "passed": True,
                                "applied": True,
                                "generated": True,
                                "changed_files": True,
                                "items": {"__all__": {"phase", "path", "written"}},
                            },
                        )
                    )
                )
                for report in reports
            ]
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].fail(
                r.require_error(terminal),
                error_code=terminal.error_code,
                error_data=data,
                exception=terminal.exception,
            )
        return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok(tuple(reports))

    def publish_batch(
        self,
        bundle: m.Infra.DocsGenerationBundle,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Admit and settle one captured batch before another batch is prepared.

        Args:
            bundle: The batch of docs generation artifacts to publish.
            publication_receipts: Mutable sequence collecting each committed
                publication phase outcome; ``None`` skips receipt collection.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        roots = FlextInfraCodegenTransaction.capability_roots(
            "docs",
            sorted({item.scope.path for item in bundle.scopes}),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=bundle.repository_root),
            prior_publications=tuple(publication_receipts or ()),
        )
        return transaction.run_files_locked(
            roots,
            lambda scope_root: self._published_scope(
                transaction,
                bundle,
                roots,
                scope_root,
                publication_receipts=publication_receipts,
            ),
        )

    def _published_scope(
        self,
        transaction: FlextInfraCodegenTransaction,
        bundle: m.Infra.DocsGenerationBundle,
        roots: t.MappingKV[str, Path],
        scope_root: Path,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Publish one planned docs scope through the shared file lifecycle.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        report_type = r[t.SequenceOf[m.Infra.DocsPhaseReport]]
        topology = u.Infra.docs_verify_source_topology(bundle)
        if topology.failure:
            return report_type.from_failure(topology)
        plans = self.plan_files(bundle)
        if plans.failure:
            return report_type.from_failure(plans)
        directories = self.required_directories(bundle)
        if directories.failure:
            return report_type.from_failure(directories)
        missing: list[Path] = []
        for path in directories.value:
            if path in roots.values():
                continue
            chain = u.Cli.atomic_plan_directory_chain(path)
            if chain.failure:
                return report_type.from_failure(chain)
            if chain.value.directories:
                missing.append(path)
        written = transaction.publish_file_phase_locked(
            scope_root,
            roots,
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.DOCS,
                files=plans.value,
                inputs=bundle.source_states,
            ),
            m.Infra.CodegenPhasePublicationPolicy(
                directories=tuple(missing),
                source_topology=bundle.source_directories,
                scope_roots=bundle.source_roots,
                source_scope=bundle.source_scope,
            ),
            publication_receipts=publication_receipts,
        )
        if written.failure:
            return report_type.from_failure(written)
        return self._generation_reports(
            bundle,
            frozenset(written.value),
        )

    def _generation_reports(
        self,
        bundle: m.Infra.DocsGenerationBundle,
        written: frozenset[Path],
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Report only destinations committed by the shared transaction.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

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
        return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok(tuple(reports))

    @staticmethod
    def plan_files(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind one prepared render bundle to exact live destination states.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        return u.Infra.docs_file_plans(bundle)

    @staticmethod
    def required_directories(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Derive target parent chains from the exact prepared render bundle.

        Publication owns source and destination guards for the current batch.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        # Why (X-47): the physical workspace root is not necessarily
        # `bundle.scopes[0]` once the root is excluded as an output scope
        # (DECLARED conform scope); use the bundle's own authenticated root.
        return u.Infra.docs_required_directories(bundle)

    def prepare_bundle(self) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Freeze the configured render and all of its authenticated inputs.

        Returns:
            The resulting ``p.Result[m.Infra.DocsGenerationBundle]``.

        """
        return self._prepare_request(
            self._configured_request(),
        )

    def prepare_batches(
        self,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> Iterator[p.Result[m.Infra.DocsGenerationBundle]]:
        """Capture each scope after the previous publication settles.

        Args:
            publication_receipts: Actual preceding outcomes shared with publication.

        Returns:
            An iterator over ``p.Result[m.Infra.DocsGenerationBundle]`` for
            each prepared batch.

        """
        return self._prepare_batches(
            self._configured_request(),
            publication_receipts=publication_receipts,
        )

    @override
    def execute(
        self,
    ) -> p.Result[m.Infra.DocsPhaseReports]:
        """Execute the configured docs generation flow.

        Returns:
            The committed reports in the canonical model-valued service result.

        """
        return self.generate(self._configured_request()).map(
            m.Infra.DocsPhaseReports.model_validate
        )

    def _configured_request(self) -> m.Infra.DocsGenerateRequest:
        """Return the pure render request shared by both planner entry points.

        Returns:
            The pure render request shared by both planner entry points.

        """
        return m.Infra.DocsGenerateRequest(
            repository_root=self.repository_root,
            projects=self.selected_projects,
            output_dir=self.output_dir,
            include_root=self.include_root,
        )

    @staticmethod
    def _plan_bundle(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[t.VariadicTuple[_DocsScopePlan]]:
        """Build every scope plan from one already prepared docs bundle.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[_DocsScopePlan]]``.

        """
        planned = u.Infra.docs_file_plans(bundle)
        if planned.failure:
            return r[tuple[_DocsScopePlan, ...]].from_failure(planned)
        scope_plans: list[_DocsScopePlan] = []
        metadata = {plan.project: plan for plan in bundle.metadata_files}
        offset = 0
        for scoped in bundle.scopes:
            size = len(scoped.artifacts)
            files = planned.value[offset : offset + size]
            projection = metadata.pop(scoped.scope.path, None)
            if projection is not None:
                files = (*files, projection)
            scope_plans.append((scoped.scope, files))
            offset += size
        return r[tuple[_DocsScopePlan, ...]].ok(tuple(scope_plans))


__all__: list[str] = ["FlextInfraDocGenerator"]
