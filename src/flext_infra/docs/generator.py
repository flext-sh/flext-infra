"""Documentation generator service driven by code, exports, and docstrings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, m, r, t, u
from flext_infra.codegen import FlextInfraMisePublication
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.docs import FlextInfraDocGeneratorBundleMixin
from flext_infra.docs.base import FlextInfraDocServiceBase

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import p

type _DocsScopePlan = t.Pair[m.Infra.DocScope, t.VariadicTuple[m.Infra.CodegenFilePlan]]
type _DocsAdmission = t.Triple[
    m.Infra.CodegenPhaseAnalysis,
    m.Infra.CodegenPhaseOutcome,
    t.VariadicTuple[m.Infra.CodegenFilePlan],
]


class FlextInfraDocGenerator(
    FlextInfraDocServiceBase,
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
    def execute_request(cls, request: m.Infra.DocsGenerateRequest) -> p.Result[bool]:
        """Expose one fixed-effect CLI request without inherited mode controls.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        owner = cls(repository_root=request.repository_root)
        return owner._propagate_phase_outcome(
            "generate",
            owner.generate(request),
            failure_predicate=lambda report: not report.passed,
        )

    def generate(
        self,
        request: m.Infra.DocsGenerateRequest,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Publish generated docs through the existing durable file lifecycle.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        reports: list[m.Infra.DocsPhaseReport] = []
        for prepared in self._prepare_batches(request):
            if prepared.failure:
                return r[t.SequenceOf[m.Infra.DocsPhaseReport]].from_failure(prepared)
            published = self.publish_batch(prepared.value)
            if published.failure:
                return published
            reports.extend(published.value)
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
        roots = {
            f"@docs-{index}": path
            for index, path in enumerate(
                sorted({item.scope.path for item in bundle.scopes}),
            )
        }
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=bundle.repository_root),
            producer=bundle.producer,
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

    @classmethod
    def _admitted_docs_batch(
        cls,
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[_DocsAdmission]:
        """Verify topology, plan the files, and admit one docs batch.

        Returns:
            The resulting ``(analysis, admission, plans)`` triple.

        """
        result_type = r[_DocsAdmission]
        topology = u.Infra.docs_verify_source_topology(
            bundle.repository_root,
            bundle.source_states,
            source_roots=bundle.source_roots,
            source_scope=bundle.source_scope,
            source_directories=bundle.source_directories,
        )
        if topology.failure:
            return result_type.from_failure(topology)
        plans = cls.plan_files(bundle)
        if plans.failure:
            return result_type.from_failure(plans)
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.DOCS,
            files=plans.value,
            inputs=bundle.source_states,
        )
        bound_analysis = FlextInfraCodegenPreconditions.bind_producer_analysis(
            analysis, bundle.producer
        )
        if bound_analysis.failure:
            return result_type.from_failure(bound_analysis)
        analysis = bound_analysis.value
        admitted = FlextInfraMisePublication.admit_batch(analysis)
        if admitted.failure:
            return result_type.from_failure(admitted)
        return result_type.ok((analysis, admitted.value, plans.value))

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
        """Admit, begin, stage, and commit one scope inside the shared locks.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        report_type = r[t.SequenceOf[m.Infra.DocsPhaseReport]]
        prepared = self._admitted_docs_batch(bundle)
        if prepared.failure:
            return report_type.from_failure(prepared)
        started = transaction.begin_files_locked(
            scope_root,
            roots,
                analysis.inputs,
        )
        if started.failure:
            return report_type.from_failure(started)

        def staged_operation(
            session: m.Infra.CodegenTransactionSession,
        ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
            """Record, stage, commit, and report the admitted batch.

            Returns:
                The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

            """
            bound = self._recorded_publication_session(transaction, bundle, session)
            if bound.failure:
                return report_type.from_failure(bound)
            staged = self._staged_session(transaction, bundle, roots, bound.value)
            if staged.failure:
                return report_type.from_failure(staged)
            return self._committed_reports(
                transaction,
                bundle,
                prepared.value,
                staged.value,
                publication_receipts=publication_receipts,
            )

        return transaction.publish_prepared_locked(started.value, staged_operation)

    def _staged_session(
        self,
        transaction: FlextInfraCodegenTransaction,
        bundle: m.Infra.DocsGenerationBundle,
        roots: t.MappingKV[str, Path],
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Append the required directories outside the leased destinations.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        directories = self.required_directories(bundle)
        if directories.failure:
            return result_type.from_failure(directories)
        staged = transaction.append_directories_locked(
            session,
            c.Infra.CodegenStagedFilePhase.DOCS,
            tuple(path for path in directories.value if path not in roots.values()),
        )
        if staged.failure:
            return result_type.from_failure(staged)
        return result_type.ok(staged.value)

    def _committed_reports(
        self,
        transaction: FlextInfraCodegenTransaction,
        bundle: m.Infra.DocsGenerationBundle,
        preparation: _DocsAdmission,
        staged: m.Infra.CodegenTransactionSession,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Append the admitted phase, commit it, and report written files.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        analysis, admitted, plans = preparation
        written = transaction.append_phase_locked(
            staged,
            analysis.phase,
            analysis.files,
            batch_admission=admitted,
        )
        if written.failure:
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].from_failure(written)
        committed = transaction.commit_locked(
            written.value,
            publication_receipts=publication_receipts,
        )
        if committed.failure:
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].from_failure(committed)
        return self._generation_reports(
            bundle,
            plans,
            frozenset(committed.value),
        )

    @staticmethod
    def _recorded_publication_session(
        transaction: FlextInfraCodegenTransaction,
        bundle: m.Infra.DocsGenerationBundle,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Bind the empty proof and record the docs publication phase.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        bound = transaction.bind_publication_proof(
            session,
            (),
            source_topology=bundle.source_directories,
            scope_roots=bundle.source_roots,
            source_scope=bundle.source_scope,
            phase=c.Infra.CodegenStagedFilePhase.DOCS,
        )
        if bound.failure:
            return result_type.from_failure(bound)
        incomplete = transaction.record_publication(
            bound.value,
            phase=c.Infra.CodegenStagedFilePhase.DOCS,
        )
        if incomplete.failure:
            return result_type.from_failure(incomplete)
        return result_type.ok(incomplete.value)

    def _generation_reports(
        self,
        bundle: m.Infra.DocsGenerationBundle,
        committed_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        written: frozenset[Path],
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Report only destinations committed by the shared transaction.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]``.

        """
        reports: list[m.Infra.DocsPhaseReport] = []
        first_scope = bundle.scopes[0].scope
        root_scope = first_scope if first_scope.name == c.Infra.RK_ROOT else None
        offset = 0
        for scoped in bundle.scopes:
            scope = scoped.scope
            plans = committed_plans[offset : offset + len(scoped.artifacts)]
            offset += len(scoped.artifacts)
            changed = tuple(plan for plan in plans if plan.path in written)
            collocated = self._is_collocated_workspace_project(
                scope,
                root_scope=root_scope,
            )
            report = m.Infra.DocsPhaseReport(
                phase="generate",
                scope=scope.name,
                changed_files=len(changed),
                generated=len(changed),
                applied=True,
                source="code-docstring-ssot",
                items=tuple(
                    m.Infra.DocsPhaseItemModel(
                        phase="generate",
                        path=str(plan.path),
                        written=plan.path in written,
                    )
                    for plan in plans
                ),
                result=c.Infra.ResultStatus.OK,
                reason=(
                    "aggregate-root-owner" if collocated else f"changes:{len(changed)}"
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

        Source-state race verification is owned by ``docs_file_plans``.

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
        return self._prepare_request(self._configured_request())

    def prepare_batches(
        self,
    ) -> Iterator[p.Result[m.Infra.DocsGenerationBundle]]:
        """Yield the next captured scope only after the caller settles its batch.

        Returns:
            An iterator over ``p.Result[m.Infra.DocsGenerationBundle]`` for
            each prepared batch.

        """
        return self._prepare_batches(self._configured_request())

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs generation flow.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return self._propagate_phase_outcome(
            "generate",
            self.generate(
                m.Infra.DocsGenerateRequest(
                    repository_root=self.repository_root,
                    projects=self.selected_projects,
                    output_dir=self.output_dir,
                    include_root=self.include_root,
                ),
            ),
            failure_predicate=lambda report: not report.passed,
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
        offset = 0
        for scoped in bundle.scopes:
            size = len(scoped.artifacts)
            scope_plans.append((scoped.scope, planned.value[offset : offset + size]))
            offset += size
        return r[tuple[_DocsScopePlan, ...]].ok(tuple(scope_plans))


__all__: list[str] = ["FlextInfraDocGenerator"]
