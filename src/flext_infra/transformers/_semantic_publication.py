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
    FlextInfraCodegenStaging,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMisePublication,
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
        inputs = u.Infra.unique_states((
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
        analysis = cls.plan_semantic_file_plans(plans, codegen)
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
        analysis = cls.plan_semantic_file_plans(
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
    def plan_semantic_file_plans(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        codegen: m.Infra.CodegenConfigSpec | None = None,
        *,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan authored sources through the shared guarded source ingress.

        Returns:
            The complete analysis or its first planning failure.

        """
        snapshots = u.Infra.unique_states((
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

    @classmethod
    def publish_semantic_analyses(
        cls,
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
        *,
        source_plans: t.SequenceOf[m.Infra.SemanticFilePlan] = (),
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions | None = None,
        publish: bool = True,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Admit complete native analyses and publish them with authored sources.

        Each original analysis is admitted before composition so another source
        cannot repair missing or conflicting producer metadata by aggregation.

        Returns:
            Actual cohort effects, or the first original admission failure.

        """
        if options is not None and options.projection_roots:
            return r[tuple[Path, ...]].fail(
                "complete native analyses already own their dependent projections"
            )
        authored = cls.plan_semantic_file_plans(source_plans)
        if authored.failure:
            return r[tuple[Path, ...]].from_failure(authored)
        for analysis in analyses:
            if (
                analysis.exception is not None
                or analysis.issues
                or analysis.failed_targets
            ):
                return r[tuple[Path, ...]].fail(
                    "; ".join(issue.message for issue in analysis.issues)
                    or "native semantic projection planning failed",
                    exception=analysis.exception,
                )
            if (
                analysis.phase == c.Infra.CodegenStagedFilePhase.LAZY_INIT
                and not analysis.publications
                and any(
                    file.path.name == c.Infra.INIT_PY
                    and file.desired_content is not None
                    for file in analysis.files
                )
            ):
                return r[tuple[Path, ...]].fail(
                    "native lazy-init analysis lacks original publication dependencies"
                )
            admitted = FlextInfraMisePublication.admit_batch(analysis)
            if admitted.failure:
                return r[tuple[Path, ...]].from_failure(admitted)
        combined = cls._combined_native_analysis((authored.value, *analyses))
        return combined.flat_map(
            lambda complete: cls._publish_joint_analysis(
                complete,
                repository_root=repository_root,
                options=m.Infra.SemanticPublicationOptions()
                if options is None
                else options,
                publish=publish,
            )
        )

    @staticmethod
    def _combined_native_analysis(
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Retain complete native publication and generator observations.

        Returns:
            The complete joint phase, or conflicting original producer metadata.

        """
        references = tuple(
            analysis.generator_reference
            for analysis in analyses
            if analysis.generator_reference is not None
        )
        if references and any(
            reference is not references[0] for reference in references
        ):
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                "native semantic analyses have different original producer references"
            )
        inputs = u.Infra.unique_states(
            tuple(state for analysis in analyses for state in analysis.inputs)
        )
        if inputs.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(inputs)
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            tuple(
                receipt
                for analysis in analyses
                for receipt in analysis.source_directories
            ),
            tuple(
                receipt
                for analysis in analyses
                for receipt in analysis.source_query_topology
            ),
        )
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(file for analysis in analyses for file in analysis.files),
                inputs=inputs.value,
                source_directories=directories,
                source_query_topology=topology,
                generator_trees=tuple(
                    tree for analysis in analyses for tree in analysis.generator_trees
                ),
                generator_modules=tuple(
                    module
                    for analysis in analyses
                    for module in analysis.generator_modules
                ),
                generator_reference=references[0] if references else None,
                publications=tuple(
                    publication
                    for analysis in analyses
                    for publication in analysis.publications
                ),
                issues=tuple(
                    issue for analysis in analyses for issue in analysis.issues
                ),
                failed_targets=tuple(
                    target
                    for analysis in analyses
                    for target in analysis.failed_targets
                ),
                exception=next(
                    (
                        analysis.exception
                        for analysis in analyses
                        if analysis.exception is not None
                    ),
                    None,
                ),
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
            entrypoint=cls.publish_semantic_analyses,
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
            source_options=m.Infra.StageSourceOptions(
                inputs=analysis.inputs, declared_files=analysis.files
            ),
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
        inputs = u.Infra.unique_states((
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
        repository_root, options = publication
        staged_files: list[m.Infra.CodegenStagedFile] = []

        def validate_stage(
            session: m.Infra.CodegenTransactionSession,
            staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            """Retain original parent witnesses and the actual staged-file objects.

            Returns:
                The native staged validation result, or its first failure.

            """
            materialized = cls._materialized_semantic_parents(
                transaction, session, analysis
            )
            if materialized.failure:
                return r[m.Infra.CodegenTransactionSession].from_failure(materialized)
            checked = FlextInfraCodegenStaging.validate_python_plans(
                materialized.value,
                staged,
                plans=analysis.files,
                runtime=m.Infra.CodegenSourceRuntime(workspace=repository_root),
            )
            staged_files.extend(staged)
            return checked

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            """Guard the sources, begin the locked files scope and apply.

            Args:
                scope_root: Elected scope root of the locked publication.

            Returns:
                The committed published paths, or the first phase failure.

            """
            guarded = cls._guard_source_inputs(options.source_guard)
            if guarded.failure:
                return r[tuple[Path, ...]].from_failure(guarded)
            committed = transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(), staged_validator=validate_stage
                ),
            )
            if committed.failure:
                return committed
            if published_files is not None:
                published_files.extend(
                    file for file in staged_files if file.before.path in committed.value
                )
            if options.validator is not None:
                accepted = options.validator(repository_root)
                if accepted.failure:
                    return r[tuple[Path, ...]].from_failure(accepted)
                if not accepted.value:
                    return r[tuple[Path, ...]].fail("semantic acceptance rejected")
            return committed

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
        guarded = cls._guard_source_inputs(options.source_guard)
        if guarded.failure:
            return result_type.from_failure(guarded)
        prepared = cls._prepared_transaction(
            prepared_analysis.value, repository_root, options
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        return result_type.ok((prepared.value, prepared_analysis.value))

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
            prepare=u.Infra.normalize_source_plan,
        )
        if prepared_files.failure:
            return result_type.from_failure(prepared_files)
        inputs = u.Infra.unique_states((
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
        codegen: m.Infra.CodegenConfigSpec | None = None,
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
