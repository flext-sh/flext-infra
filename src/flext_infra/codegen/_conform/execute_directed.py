"""Transactional publication of exactly selected conformance files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenFileLeases,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
    FlextInfraStagedPackage,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformExecuteScaffold
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions


class FlextInfraCodegenConformExecuteDirected(FlextInfraCodegenConformExecuteScaffold):
    """Publish file-only surfaces through the existing locked transaction."""

    @staticmethod
    def _observe_publication(
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Observe physical publication evidence without a general code audit.

        Returns:
            The verified publication result, or the verification failure.

        """
        with FlextInfraCodegenFileLeases.mutation_lease(request.root):
            observed = FlextInfraMiseArtifactsVerification.publication_current(
                request,
            )
            if observed.failure:
                return r[m.Infra.CodegenResult].from_failure(observed)
            return r[m.Infra.CodegenResult].ok(
                m.Infra.CodegenResult(verified_publication=observed.value),
            )

    @staticmethod
    def _run_publication(
        request: m.Infra.CodegenConformRequest,
        transaction: FlextInfraCodegenTransaction,
        roots: t.MappingKV[str, Path],
        publisher: Callable[
            [Path, t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]],
            p.Result[m.Infra.CodegenResult],
        ],
    ) -> p.Result[m.Infra.CodegenResult]:
        """Bind the request to its actual completed batch outside the batch lease.

        Returns:
            The published result, or the receipt, publication, or batch failure.

        """
        scope_roots = tuple(
            path for name, path in roots.items() if not name.startswith("@stage-inputs")
        )
        operation = transaction.publish_operation_receipt(
            request,
            (),
            scope_roots=scope_roots,
        )
        if operation.failure:
            return r[m.Infra.CodegenResult].from_failure(operation)

        def publish(
            scope_root: Path,
        ) -> p.Result[t.Pair[m.Infra.CodegenResult, m.Infra.CodegenPhaseOutcome]]:
            result_type = r[t.Pair[m.Infra.CodegenResult, m.Infra.CodegenPhaseOutcome]]
            receipts: list[m.Infra.CodegenPhaseOutcome] = []
            result = publisher(scope_root, receipts)
            if result.failure:
                return result_type.from_failure(result)
            if not receipts:
                return result_type.fail("completed batch publication receipt is absent")
            return result_type.ok((result.value, receipts[-1]))

        published = transaction.run_files_locked(roots, publish)
        if published.failure:
            return r[m.Infra.CodegenResult].from_failure(published)
        result, batch = published.value
        completed = transaction.publish_operation_receipt(
            request,
            (batch,),
            scope_roots=scope_roots,
            operation=operation.value,
            completed=True,
        )
        if completed.failure:
            return r[m.Infra.CodegenResult].from_failure(completed)
        return r[m.Infra.CodegenResult].ok(result)

    def _execute_lazy_init(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Run the initializer-only surface under the existing file transaction.

        Returns:
            The checked or atomically published initializer plan.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
        )
        root = request.root.expanduser().resolve()
        engine = FlextInfraCodegenPreconditions.rendering_engine(root)
        if engine.failure:
            return r[m.Infra.CodegenResult].from_failure(engine)
        inputs = u.Infra.load_codegen_inputs(root)
        if inputs.failure:
            return r[m.Infra.CodegenResult].from_failure(inputs)
        topology = self._planning_workspace(request, root, inputs=inputs.value)
        if topology.failure:
            return r[m.Infra.CodegenResult].from_failure(topology)
        workspace, _target, repository = topology.value
        roots = self._lazy_init_roots(request, root, workspace, repository)
        if roots.failure:
            return r[m.Infra.CodegenResult].from_failure(roots)
        return self._run_publication(
            request,
            transaction,
            roots.value,
            lambda scope_root, receipts: self._execute_lazy_init_locked(
                request,
                transaction,
                (roots.value, scope_root),
                receipts,
            ),
        )

    def _lazy_init_roots(
        self,
        request: m.Infra.CodegenConformRequest,
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[t.MappingKV[str, Path]]:
        """Namespace the selected initializer participants under pseudo-roots.

        Args:
            request: Conform request selecting the participant scope.
            root: Resolved repository root of the request.
            workspace: Loaded planning workspace specification.
            repository: Current repository reference of the checkout.

        Returns:
            The pseudo-root mapping of the initializer publication, or the
            first selection or staging failure.

        """
        selected = self._select_repositories(request, workspace, repository)
        if selected.failure:
            return r[t.MappingKV[str, Path]].from_failure(selected)
        roots = FlextInfraCodegenTransaction.capability_roots(
            request.what,
            tuple(
                (root / participant.path).resolve()
                for participant in selected.value
                if participant.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
            ),
        )
        if request.what == c.Infra.CodegenConformSurface.FACADES:
            stage_workspace = FlextInfraStagedPackage.workspace_root(request.root)
            if stage_workspace.failure:
                return r[t.MappingKV[str, Path]].from_failure(stage_workspace)
            if stage_workspace.value != request.root.expanduser().resolve():
                roots = {
                    **roots,
                    **FlextInfraCodegenTransaction.capability_roots(
                        "stage-inputs", (stage_workspace.value,)
                    ),
                }
        return r[t.MappingKV[str, Path]].ok(roots)

    def _execute_lazy_init_locked(
        self,
        request: m.Infra.CodegenConformRequest,
        transaction: FlextInfraCodegenTransaction,
        scope: t.Pair[t.MappingKV[str, Path], Path],
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[m.Infra.CodegenResult]:
        """Plan after lease acquisition and collect the exact batch receipt.

        Returns:
            The initializer result, retaining any planner or transaction failure.

        """
        roots, scope_root = scope
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        planned = self._plan_single_surface(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].from_failure(planned)
        plan, analysis = planned.value
        if request.what == c.Infra.CodegenConformSurface.FACADES:
            u.Cli.info(f"stage=facades-plan files={len(plan.files)} environments=0")
            for file in plan.files:
                u.Cli.info(f"  destination={file.path}")
        changed = tuple(
            file
            for file in analysis.files
            if u.Infra.codegen_file_requires_effect(file)
        )
        return self._publish_directed_phase(
            request,
            transaction,
            (roots, scope_root),
            (plan, analysis, changed),
            receipts,
        )

    def _publish_directed_phase(
        self,
        request: m.Infra.CodegenConformRequest,
        transaction: FlextInfraCodegenTransaction,
        scope: t.Pair[t.MappingKV[str, Path], Path],
        candidate: t.Triple[
            m.Infra.CodegenPlan,
            m.Infra.CodegenPhaseAnalysis,
            t.VariadicTuple[m.Infra.CodegenFilePlan],
        ],
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[m.Infra.CodegenResult]:
        """Authenticate staged inputs and publish the selected phase under its lease.

        Returns:
            The original plan and published paths, or the first phase failure.

        """
        roots, scope_root = scope
        plan, analysis, changed = candidate
        staged = self._directed_stage_inputs(request, analysis)
        if staged.failure:
            return r[m.Infra.CodegenResult].from_failure(staged)
        analysis, stage_plan = staged.value

        def validate_stage(
            session: m.Infra.CodegenTransactionSession,
            publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            return self._validate_directed_stage(
                request.root,
                transaction,
                stage_plan,
                session,
                publications,
            )

        published = transaction.publish_file_phase_locked(
            scope_root,
            roots,
            analysis,
            m.Infra.CodegenPhasePublicationPolicy(
                directories=tuple(
                    sorted({
                        file.path.parent
                        for file in changed
                        if not file.path.parent.is_dir()
                    }),
                ),
                staged_validator=validate_stage if stage_plan is not None else None,
            ),
            publication_receipts=receipts,
        )
        if published.failure:
            return r[m.Infra.CodegenResult].from_failure(published)
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=plan, written_files=published.value),
        )

    @staticmethod
    def _directed_stage_inputs(
        request: m.Infra.CodegenConformRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[
        t.Pair[m.Infra.CodegenPhaseAnalysis, m.Infra.StagePackagePlan | None]
    ]:
        """Pin the type facade's staged contract and merge its authenticated inputs.

        Returns:
            The phase analysis and optional staged plan, or a planning failure.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenPhaseAnalysis, m.Infra.StagePackagePlan | None]
        ]
        if request.what != c.Infra.CodegenConformSurface.FACADES:
            return result_type.ok((analysis, None))
        selected_file = analysis.files[0]
        if selected_file.desired_content is None:
            return result_type.ok((analysis, None))
        source = selected_file.desired_content.decode(c.DEFAULT_ENCODING)
        if "t" not in u.Infra.facade_letter_names_source(
            source, filename=str(selected_file.path)
        ):
            return result_type.ok((analysis, None))
        candidate = FlextInfraStagedPackage.plan(request.root, selected_file)
        if candidate.failure:
            return result_type.from_failure(candidate)
        stage_plan = candidate.value
        source_states = FlextInfraCodegenPreconditions.unique_states((
            *analysis.inputs,
            *stage_plan.inputs,
        ))
        if source_states.failure:
            return result_type.from_failure(source_states)
        authenticated = analysis.model_copy(
            update={
                "inputs": source_states.value,
                "files": (
                    selected_file.model_copy(
                        update={"source_states": source_states.value}
                    ),
                ),
            },
        )
        return result_type.ok((
            authenticated,
            stage_plan.model_copy(update={"inputs": source_states.value}),
        ))

    @staticmethod
    def _validate_directed_stage(
        root: Path,
        transaction: FlextInfraCodegenTransaction,
        stage_plan: m.Infra.StagePackagePlan | None,
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Materialize and validate the exact journal-owned candidate package view.

        Returns:
            The materialized session after consumer validation, or its first failure.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if stage_plan is None or len(publications) != 1:
            return result_type.fail(
                "staged facade requires one exact candidate contract",
            )
        materialized = transaction.materialize_package_view_locked(
            session,
            stage_plan,
            publications[0],
        )
        if materialized.failure:
            return result_type.from_failure(materialized)
        current, view = materialized.value
        checked = FlextInfraValidateFreshImport(
            repository_root=root,
            runtime_root=None,
        ).validate_stage_view(view, current)
        if checked.failure:
            return result_type.from_failure(checked)
        return result_type.ok(current)

    @staticmethod
    def _drift_message(
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
        label: str,
    ) -> str | None:
        """Render the drift failure message for a changed file set, if any.

        Returns:
            The drift message, or None when the set is empty.

        """
        if not changed:
            return None
        paths = ", ".join(str(file.path) for file in changed)
        report = u.Infra.codegen_file_drift_report(changed)
        return f"{label} drift detected: {paths}\n{report}"


__all__: list[str] = ["FlextInfraCodegenConformExecuteDirected"]
