"""Semantic publication through the canonical recoverable file transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenStaging,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
    FlextInfraStagedPackage,
)
from flext_infra.validate import FlextInfraValidateFreshImport


class FlextInfraSemanticPublication:
    """Publish semantic file plans through the recoverable codegen transaction."""

    @classmethod
    def publish_semantic_artifact_plans(
        cls,
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions | None = None,
        publish: bool = True,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish exact create/rewrite/remove effects through the shared journal.

        Returns:
            Published paths or the original input or publication failure.

        """
        inputs = FlextInfraCodegenPreconditions.unique_states((
            *(state for plan in plans for state in plan.source_states),
            *(
                plan.before
                for plan in plans
                if isinstance(plan.before, m.Cli.AtomicFileState)
            ),
        ))
        if inputs.failure:
            return r[tuple[Path, ...]].from_failure(inputs)
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            files=tuple(plans),
            inputs=inputs.value,
        )
        return cls._publish_joint_analysis(
            analysis,
            repository_root=repository_root,
            options=m.Infra.SemanticPublicationOptions()
            if options is None
            else options,
            publish=publish,
        )

    @classmethod
    def publish_semantic_file_plans(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish each guarded file and report byte and caller acceptance.

        ``None`` content means no semantic change, never deletion. The existing
        transaction owns identity checks, staging and durable recovery. Consumer
        rejection preserves successful writes for correction at their owner.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        analysis = cls._semantic_phase_analysis(plans, codegen)
        if analysis.failure:
            return r[tuple[Path, ...]].from_failure(analysis)
        selected = m.Infra.SemanticPublicationOptions() if options is None else options
        if not analysis.value.files and not selected.projection_roots:
            return cls._accepted_empty_publication(repository_root, selected)
        return cls._publish_joint_analysis(
            analysis.value,
            repository_root=repository_root,
            options=selected,
            published_files=published_files,
        )

    @staticmethod
    def _accepted_empty_publication(
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Run the real source and consumer gates even without publication effects.

        Returns:
            Empty actual effects, or the original guard/consumer failure.

        """
        if options.source_guard is not None:
            checked = options.source_guard()
            if checked.failure:
                return r[tuple[Path, ...]].from_failure(checked)
            if not checked.value:
                return r[tuple[Path, ...]].fail("semantic input preflight rejected")
        if options.validator is not None:
            checked = options.validator(repository_root)
            if checked.failure:
                return r[tuple[Path, ...]].from_failure(checked)
            if not checked.value:
                return r[tuple[Path, ...]].fail("semantic acceptance rejected")
        return r[tuple[Path, ...]].ok(())

    @classmethod
    def publish_source_candidate(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        candidate: m.Infra.StageSourcePlan,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish an accepted candidate under its complete original input guard.

        Additional read-only driver snapshots belong to the transaction, not the
        candidate's governed source inventory. Preserve every caller snapshot.

        Returns:
            Published paths, or the original pre-CAS identity failure.

        """
        if any(source is None for source in candidate.updates.values()) or {
            plan.path: plan.desired_content
            for plan in plans
            if plan.desired_content is not None
        } != {
            path: source.encode(c.DEFAULT_ENCODING)
            for path, source in candidate.updates.items()
            if source is not None
        }:
            return r[tuple[Path, ...]].fail(
                "semantic plans differ from accepted candidate"
            )
        analysis = cls._semantic_phase_analysis(
            plans,
            None,
            inputs=(*candidate.inputs, *inputs),
        )
        if analysis.failure:
            return r[tuple[Path, ...]].from_failure(analysis)
        originals = {state.path: state for state in candidate.inputs}
        if any(originals.get(plan.path) != plan.before for plan in plans):
            return r[tuple[Path, ...]].fail(
                "semantic originals differ from accepted candidate"
            )
        return cls._publish_joint_analysis(
            analysis.value,
            repository_root=candidate.workspace,
            options=m.Infra.SemanticPublicationOptions(
                validator=lambda _view_root: u.Cli.atomic_verify_binary_file_states(
                    tuple(
                        state
                        for state in analysis.value.inputs
                        if state.path not in candidate.updates
                    )
                ),
                source_guard=lambda: u.Cli.atomic_verify_binary_file_states(
                    analysis.value.inputs
                ).flat_map(
                    lambda _: FlextInfraStagedPackage.source_inputs_current(candidate)
                ),
                dependency_group=analysis.value.phase,
                input_roots=candidate.roots,
            ),
        )

    @classmethod
    def _semantic_phase_analysis(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        codegen: m.Infra.CodegenConfigSpec | None,
        *,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Build the same authenticated analysis for both publication inputs.

        Returns:
            The complete analysis or its first planning failure.

        """
        snapshots = FlextInfraCodegenPreconditions.unique_states((
            *inputs,
            *(state for plan in plans for state in (plan.before, *plan.source_states)),
        ))
        if snapshots.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(snapshots)
        files = cls._concrete_file_plans(plans, codegen, source_states=snapshots.value)
        if files.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(files)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(files.value),
                inputs=snapshots.value,
            )
        )

    @staticmethod
    def _guard_source_inputs(
        source_guard: Callable[[], p.Result[bool]] | None,
    ) -> p.Result[bool]:
        """Preserve native pre-publication refusal and reject a false verdict.

        Returns:
            The original failure or a successful applicable source guard.

        """
        if source_guard is None:
            return r[bool].ok(value=True)
        guarded = source_guard()
        if guarded.failure:
            return guarded
        return (
            guarded if guarded.value else r[bool].fail("semantic source guard rejected")
        )

    @classmethod
    def _prepared_transaction(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[t.Pair[FlextInfraCodegenTransaction, t.MappingKV[str, Path]]]:
        """Capture the producer and open the transaction over stable pseudo-roots.

        Args:
            analysis: Semantic phase analysis whose projects are namespaced.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            The open transaction with its pseudo-root mapping, or the first
            producer failure.

        """
        roots = cls._semantic_phase_roots(
            analysis.files,
            (*options.projection_roots, *options.input_roots),
        )
        producer = FlextInfraValidateFreshImport.capture_producer(
            repository_root,
            entrypoint=cls.publish_source_candidate,
        )
        if producer.failure:
            return r[
                t.Pair[FlextInfraCodegenTransaction, t.MappingKV[str, Path]]
            ].from_failure(producer)
        return r[t.Pair[FlextInfraCodegenTransaction, t.MappingKV[str, Path]]].ok(
            (
                FlextInfraCodegenTransaction(
                    FlextInfraCodegenMiseArtifacts(repository_root=repository_root),
                    producer=producer.value,
                ),
                roots,
            ),
        )

    @classmethod
    def _group_planned_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Expose generated projections inside one dependency-group publication.

        Args:
            analysis: Semantic phase analysis planned for publication.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            The dependency-group-planned analysis, or the first planning
            failure.

        """
        dependency_group = options.dependency_group
        if dependency_group is None:
            if not options.projection_roots:
                return r[m.Infra.CodegenPhaseAnalysis].ok(analysis)
            dependency_group = analysis.phase
        combined = {
            item.path: item.model_copy(update={"dependency_group": dependency_group})
            for item in analysis.files
        }
        if not options.projection_roots:
            return r[m.Infra.CodegenPhaseAnalysis].ok(
                analysis.model_copy(update={"files": tuple(combined.values())}),
            )
        return cls._combined_projection_analysis(
            analysis,
            repository_root,
            options,
            dependency_group,
            combined,
        )

    @classmethod
    def _combined_projection_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
        dependency_group: str,
        combined: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Join generated projection files into one dependency-group analysis.

        Args:
            analysis: Semantic phase analysis planned for publication.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.
            dependency_group: Elected group of every joined effect.
            combined: Group-labeled plans keyed by destination path.

        Returns:
            The dependency-group-planned analysis, or the first planning
            failure.

        """
        # Resolve the proposed graph with the original native read authority.
        # A physical runtime can only consume the fully composed candidate below.
        with u.Infra.facade_source_project(
            repository_root,
            source_states=analysis.inputs,
            declared_files=analysis.files,
            project_roots=tuple(
                dict.fromkeys((
                    *options.projection_roots,
                    *(plan.project for plan in analysis.files),
                ))
            ),
        ) as binding:
            generated = FlextInfraCodegenLazyInit(
                repository_root=repository_root,
                project_scope_roots=options.projection_roots,
            ).plan_files(source_project=binding[0])
        if generated.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(generated)
        projection = generated.value
        if projection.exception is not None or projection.issues:
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                "semantic dependency group has incomplete generated projections: "
                + "; ".join(issue.message for issue in projection.issues),
                exception=projection.exception,
            )
        for item in projection.files:
            previous = combined.get(item.path)
            if previous is not None and previous.before != item.before:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"semantic projection changed "
                    f"its original destination: {item.path}",
                )
            combined[item.path] = item.model_copy(
                update={"dependency_group": dependency_group},
            )
        inputs = FlextInfraCodegenPreconditions.unique_states((
            *analysis.inputs,
            *projection.inputs,
            *(state for item in combined.values() for state in item.source_states),
        ))
        if inputs.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(inputs)
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            (*analysis.source_directories, *projection.source_directories),
            (*analysis.source_query_topology, *projection.source_query_topology),
        )
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            projection.model_copy(
                update={
                    "phase": analysis.phase,
                    "files": tuple(combined.values()),
                    "inputs": inputs.value,
                    "source_directories": directories,
                    "source_query_topology": topology,
                    "publications": (*analysis.publications, *projection.publications),
                }
            ),
        )

    @classmethod
    def _accepted_candidate(
        cls,
        transaction: FlextInfraCodegenTransaction,
        repository_root: Path,
        analysis: m.Infra.CodegenPhaseAnalysis,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[bool]:
        """Preview the planned candidate through the consumer validator.

        Args:
            transaction: Open recoverable file transaction.
            repository_root: Governed workspace root of the publication.
            analysis: Planned phase analysis to preview.
            options: Declared native consumers and additional acceptance gate.

        Returns:
            Whether the consumer accepted the previewed candidate, or the
            first preview or acceptance failure.

        """
        validator = options.validator
        if validator is None and not options.projection_roots:
            return r[bool].ok(value=True)
        workspaces = tuple(
            dict.fromkeys(
                u.Infra.import_project_roots(root)[0]
                for root in options.projection_roots
            )
        )
        accepted = transaction.preview_sources(
            repository_root,
            {
                item.path: (
                    None
                    if item.desired_content is None
                    else item.desired_content.decode(c.DEFAULT_ENCODING)
                )
                for item in analysis.files
            },
            lambda view_root, _candidate: (
                r[bool].ok(value=True) if validator is None else validator(view_root)
            ),
            options=m.Infra.CodegenSourcePreviewOptions(
                inputs=analysis.inputs,
                workspaces=workspaces,
                modes={
                    item.path: item.desired_mode
                    for item in analysis.files
                    if item.desired_mode is not None
                },
            ),
        )
        if accepted.failure:
            return r[bool].from_failure(accepted)
        if accepted.value.failure:
            return r[bool].from_failure(accepted.value)
        if not accepted.value.value:
            return r[bool].fail("semantic candidate acceptance rejected")
        return r[bool].ok(value=True)

    @staticmethod
    def _materialized_semantic_parents(
        transaction: FlextInfraCodegenTransaction,
        session: m.Infra.CodegenTransactionSession,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Authenticate and materialize actual planned parent chains under the lease.

        Returns:
            The real updated session or its first planning/materialization failure.

        """
        witnesses = tuple(
            plan.before
            for plan in analysis.files
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
        )
        for witness in witnesses:
            observed = u.Cli.atomic_plan_directory_chain(witness.target)
            if observed.failure:
                return r[m.Infra.CodegenTransactionSession].from_failure(observed)
            if observed.value != witness:
                return r[m.Infra.CodegenTransactionSession].fail(
                    "semantic destination parent chain changed after planning: "
                    f"{witness.target}",
                )
        if witnesses:
            materialized = transaction.append_directories_locked(
                session,
                analysis.phase,
                tuple(dict.fromkeys(witness.target for witness in witnesses)),
            )
            if materialized.failure:
                return r[m.Infra.CodegenTransactionSession].from_failure(materialized)
            session = materialized.value
            for witness in witnesses:
                verified = (
                    FlextInfraMiseArtifactsVerification.materialized_directory_chain(
                        session.journal,
                        witness,
                    )
                )
                if verified.failure:
                    return r[m.Infra.CodegenTransactionSession].from_failure(verified)
        return r[m.Infra.CodegenTransactionSession].ok(session)

    @classmethod
    def _validate_published(
        cls,
        transaction: FlextInfraCodegenTransaction,
        session: m.Infra.CodegenTransactionSession,
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
        publication: t.Pair[Path, m.Infra.SemanticPublicationOptions],
    ) -> p.Result[bool]:
        """Require actual phase receipts before the final consumer acceptance gate.

        Returns:
            The original receipt or consumer verdict with its first failure intact.

        """
        repository_root, options = publication
        checked = cls._validate_phase_receipts(
            analyses,
            lambda phase_analysis: transaction.validate_phase_analysis_locked(
                phase_analysis, session=session
            ),
        )
        if checked.failure or not checked.value or options.validator is None:
            return checked
        return options.validator(repository_root)

    @classmethod
    def _apply_semantic_session(
        cls,
        transaction: FlextInfraCodegenTransaction,
        session: m.Infra.CodegenTransactionSession,
        analysis: m.Infra.CodegenPhaseAnalysis,
        publication: t.Pair[Path, m.Infra.SemanticPublicationOptions],
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Apply actual semantic/projection effects inside prepared recovery ownership.

        Returns:
            Committed actual paths or the original pre-commit failure.

        """
        repository_root = publication[0]
        materialized = cls._materialized_semantic_parents(
            transaction, session, analysis
        )
        if materialized.failure:
            return r[tuple[Path, ...]].from_failure(materialized)
        session = materialized.value
        published = transaction.append_phase_locked(
            session,
            analysis.phase,
            analysis.files,
            publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                directories=(),
                staged_validator=lambda current, staged: (
                    FlextInfraCodegenStaging.validate_python_plans(
                        current,
                        staged,
                        plans=analysis.files,
                        workspace=repository_root,
                    )
                ),
            ),
        )
        if published.failure:
            return r[tuple[Path, ...]].from_failure(published)
        checked = cls._validate_published(
            transaction, published.value, (analysis,), publication
        )
        if checked.failure:
            return r[tuple[Path, ...]].from_failure(checked)
        if not checked.value:
            return r[tuple[Path, ...]].fail("semantic acceptance rejected")
        return transaction.commit_locked(
            published.value,
            published_files=published_files,
        )

    @classmethod
    def _published_paths(
        cls,
        transaction: FlextInfraCodegenTransaction,
        roots: t.MappingKV[str, Path],
        analysis: m.Infra.CodegenPhaseAnalysis,
        publication: t.Pair[Path, m.Infra.SemanticPublicationOptions],
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Stage, validate and commit actual phases inside the locked transaction.

        Returns:
            Published paths after actual receipts and consumer acceptance.

        """
        options = publication[1]

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            guarded = cls._guard_source_inputs(options.source_guard)
            if guarded.failure:
                return r[tuple[Path, ...]].from_failure(guarded)
            started = transaction.begin_files_locked(scope_root, roots, analysis.inputs)
            if started.failure:
                return r[tuple[Path, ...]].from_failure(started)

            def apply(
                session: m.Infra.CodegenTransactionSession,
            ) -> p.Result[t.VariadicTuple[Path]]:
                return cls._apply_semantic_session(
                    transaction,
                    session,
                    analysis,
                    publication,
                    published_files,
                )

            return transaction.publish_prepared_locked(started.value, apply)

        return transaction.run_files_locked(roots, publish)

    @classmethod
    def _publish_joint_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
        publish: bool = True,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Keep semantic and generated phases in the same recoverable journal.

        Args:
            analysis: Semantic phase analysis planned for publication.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.
            published_files: Original caller-owned sink receiving committed effects.
            publish: Whether the staged plan is committed through the locked
                transaction journal.

        Returns:
            Published paths after phase receipts and consumer acceptance.

        """
        guarded = cls._guard_source_inputs(options.source_guard)
        if guarded.failure:
            return r[tuple[Path, ...]].from_failure(guarded)
        prepared = cls._prepared_publication(analysis, repository_root, options)
        if prepared.failure:
            return r[tuple[Path, ...]].from_failure(prepared)
        (transaction, roots), analysis = prepared.value
        accepted = cls._accepted_candidate(
            transaction,
            repository_root,
            analysis,
            options,
        )
        if accepted.failure:
            return r[tuple[Path, ...]].from_failure(accepted)
        if not publish:
            return r[tuple[Path, ...]].ok(())
        return cls._published_paths(
            transaction,
            roots,
            analysis,
            (repository_root, options),
            published_files,
        )

    @classmethod
    def _prepared_publication(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[
        t.Pair[
            t.Pair[FlextInfraCodegenTransaction, t.MappingKV[str, Path]],
            m.Infra.CodegenPhaseAnalysis,
        ]
    ]:
        """Open the transaction and prepare the complete publication context.

        Args:
            analysis: Semantic phase analysis planned for publication.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            The open transaction with its roots and the prepared analysis.

        """
        result_type = r[
            t.Pair[
                t.Pair[FlextInfraCodegenTransaction, t.MappingKV[str, Path]],
                m.Infra.CodegenPhaseAnalysis,
            ]
        ]
        prepared = cls._prepared_transaction(analysis, repository_root, options)
        if prepared.failure:
            return result_type.from_failure(prepared)
        transaction, roots = prepared.value
        planned = cls._group_planned_analysis(
            analysis,
            repository_root,
            options,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        prepared_analysis = cls._python_prepared_analysis(
            planned.value,
            repository_root,
        )
        if prepared_analysis.failure:
            return result_type.from_failure(prepared_analysis)
        return result_type.ok(((transaction, roots), prepared_analysis.value))

    @classmethod
    def _python_prepared_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Prepare the analysis's Python plans and merge their receipts.

        Args:
            analysis: Dependency-group-planned analysis of the publication.
            repository_root: Governed workspace root of the publication.

        Returns:
            The analysis bound to its prepared Python plans.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        prepared_files = FlextInfraCodegenStaging.prepare_python_plans(
            repository_root,
            analysis.files,
        )
        if prepared_files.failure:
            return result_type.from_failure(prepared_files)
        inputs = FlextInfraCodegenPreconditions.unique_states((
            *analysis.inputs,
            *(state for plan in prepared_files.value for state in plan.source_states),
        ))
        if inputs.failure:
            return result_type.from_failure(inputs)
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            (
                *analysis.source_directories,
                *(
                    receipt
                    for plan in prepared_files.value
                    for receipt in plan.source_directories
                ),
            ),
            (
                *analysis.source_query_topology,
                *(
                    receipt
                    for plan in prepared_files.value
                    for receipt in plan.source_query_topology
                ),
            ),
        )
        return result_type.ok(
            analysis.model_copy(
                update={
                    "files": prepared_files.value,
                    "inputs": inputs.value,
                    "source_directories": directories,
                    "source_query_topology": topology,
                }
            )
        )

    @staticmethod
    def _validate_phase_receipts(
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
        verify: Callable[[m.Infra.CodegenPhaseAnalysis], p.Result[bool]],
    ) -> p.Result[bool]:
        """Require every phase receipt before consumer acceptance.

        Returns:
            The first rejected receipt, or successful receipt validation.

        """
        for analysis in analyses:
            checked = verify(analysis)
            if checked.failure or not checked.value:
                return checked
        return r[bool].ok(value=True)

    @staticmethod
    def _semantic_phase_roots(
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        projection_roots: t.VariadicTuple[Path] = (),
    ) -> t.MappingKV[str, Path]:
        """Namespace the touched projects under stable semantic pseudo-roots.

        Returns:
            The deterministic pseudo-root mapping of the publication.

        """
        return FlextInfraCodegenTransaction.capability_roots(
            "semantic",
            sorted({plan.project for plan in files} | set(projection_roots)),
        )

    @staticmethod
    def _concrete_file_plans(
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        codegen: m.Infra.CodegenConfigSpec | None,
        *,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Convert every changed semantic plan into one owned codegen file plan.

        ``None`` content means no semantic change, never deletion. A generated
        source outside the declared template inventory requires canonical
        generator repair and is rejected here.

        Returns:
            The resulting concrete codegen file plans.

        """
        files: list[m.Infra.CodegenFilePlan] = []
        template_sources = u.Infra.codegen_template_sources(
            config.Infra.codegen if codegen is None else codegen,
        )
        for plan in plans:
            if plan.desired_content is None:
                continue
            if plan.desired_mode is None:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"semantic desired mode is absent: {plan.path}",
                )
            if (
                plan.path.resolve() not in template_sources
                and plan.before.content is not None
                and plan.before.content.decode(c.DEFAULT_ENCODING).startswith(
                    c.Infra.AUTOGEN_HEADERS,
                )
            ):
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    "generated findings require canonical generator repair: "
                    f"{plan.path}",
                )
            files.append(
                m.Infra.CodegenFilePlan(
                    project=plan.project,
                    path=plan.path,
                    before=plan.before,
                    desired_content=plan.desired_content,
                    desired_mode=plan.desired_mode,
                    source_states=source_states,
                    owner="semantic",
                ),
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(files)


__all__: list[str] = ["FlextInfraSemanticPublication"]
