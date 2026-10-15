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
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
    FlextInfraStagedPackage,
)


class _PublicationOptions(m.FrozenModel):
    """Caller-controlled gates and scope roots for one joint publication."""

    validator: Callable[[Path], p.Result[bool]] | None = m.Field(
        default=None,
        description="Consumer acceptance gate over the previewed view root",
    )
    source_guard: Callable[[], p.Result[bool]] | None = m.Field(
        default=None,
        description="Pre-publication guard over the governed source inputs",
    )
    published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = m.Field(
        default=None,
        description="Caller-owned sink receiving every staged publication",
    )
    dependency_group: str | None = m.Field(
        default=None,
        description="Dependency group owning composed projection exposure",
    )
    projection_roots: t.VariadicTuple[Path] = m.Field(
        default=(),
        description="Generated projection roots composed into the publication",
    )
    input_roots: t.VariadicTuple[Path] = m.Field(
        default=(),
        description="Additional read-only driver roots namespaced as pseudo-roots",
    )


class FlextInfraSemanticPublication:
    """Publish semantic file plans through the recoverable codegen transaction."""

    @classmethod
    def publish_semantic_artifact_plans(
        cls,
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        repository_root: Path,
        validator: Callable[[], p.Result[bool]] | None = None,
        projection_roots: t.VariadicTuple[Path] = (),
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish exact create/rewrite/remove effects through the shared journal."""
        inputs = cls._semantic_input_snapshots(plans)
        if inputs.failure:
            return r[tuple[Path, ...]].from_failure(inputs)
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            files=tuple(plans),
            inputs=inputs.value,
        )
        return cls._publish_joint_analysis(
            analysis,
            cls._semantic_phase_roots(plans, projection_roots),
            repository_root=repository_root,
            projection_roots=projection_roots,
            preflight=None,
            validator=validator,
        )

    @classmethod
    def publish_semantic_file_plans(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        repository_root: Path,
        preflight: Callable[[], p.Result[bool]] | None = None,
        validator: Callable[[Path], p.Result[bool]] | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
        projection_roots: t.VariadicTuple[Path] = (),
        dependency_group: str | None = None,
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
        if not analysis.value.files and not projection_roots:
            if preflight is not None:
                checked = preflight()
                if checked.failure:
                    return r[tuple[Path, ...]].from_failure(checked)
                if not checked.value:
                    return r[tuple[Path, ...]].fail("semantic input preflight rejected")
            if validator is not None:
                checked = validator(repository_root)
                if checked.failure:
                    return r[tuple[Path, ...]].from_failure(checked)
                if not checked.value:
                    return r[tuple[Path, ...]].fail("semantic acceptance rejected")
            return r[tuple[Path, ...]].ok(())
        return cls._publish_joint_analysis(
            analysis.value,
            repository_root=repository_root,
            options=_PublicationOptions(
                validator=validator,
                published_files=published_files,
                dependency_group=dependency_group,
                projection_roots=projection_roots,
                preflight=preflight,
            ),
        )

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
        if {
            plan.path: plan.desired_content
            for plan in plans
            if plan.desired_content is not None
        } != {
            path: source.encode(c.DEFAULT_ENCODING)
            for path, source in candidate.updates.items()
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
            options=_PublicationOptions(
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
        options: _PublicationOptions,
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
        producer = FlextInfraCodegenPreconditions.capture_producer(
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
        transaction: FlextInfraCodegenTransaction,
        repository_root: Path,
        options: _PublicationOptions,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Expose generated projections inside one dependency-group publication.

        Args:
            analysis: Semantic phase analysis planned for publication.
            transaction: Open recoverable file transaction.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            The dependency-group-planned analysis, or the first planning
            failure.

        """
        dependency_group = options.dependency_group
        if dependency_group is None:
            return r[m.Infra.CodegenPhaseAnalysis].ok(analysis)
        projection_roots = options.projection_roots

        def plan_exposure(
            view_root: Path,
            _candidate: t.MappingKV[Path, Path],
        ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
            """Compose the semantic plans with the generated projection phase.

            Args:
                view_root: Elected view root of the previewed transaction.
                _candidate: Previewed staged path mapping, unused here.

            Returns:
                The composed phase analysis, or its first planning failure.

            """
            combined = {
                item.path: item.model_copy(
                    update={"dependency_group": dependency_group}
                )
                for item in analysis.files
            }
            inputs = list(analysis.inputs)
            if projection_roots:
                generated = FlextInfraCodegenLazyInit(
                    repository_root=view_root,
                    project_scope_roots=tuple(
                        view_root / path.relative_to(repository_root)
                        for path in projection_roots
                    ),
                ).plan_files(evidence_root=repository_root)
                if generated.failure:
                    return r[m.Infra.CodegenPhaseAnalysis].from_failure(generated)
                for item in generated.value.files:
                    path = repository_root / item.path.relative_to(view_root)
                    before = u.Cli.atomic_read_binary_file_state(path, required=False)
                    if before.failure:
                        return r[m.Infra.CodegenPhaseAnalysis].from_failure(before)
                    inputs.append(before.value)
                    combined[path] = item.model_copy(
                        update={
                            "project": repository_root
                            / item.project.relative_to(view_root),
                            "path": path,
                            "before": before.value,
                            "source_states": analysis.inputs,
                            "dependency_group": dependency_group,
                        }
                    )
            unique = FlextInfraCodegenPreconditions.unique_states(tuple(inputs))
            if unique.failure:
                return r[m.Infra.CodegenPhaseAnalysis].from_failure(unique)
            return r[m.Infra.CodegenPhaseAnalysis].ok(
                m.Infra.CodegenPhaseAnalysis(
                    phase=analysis.phase,
                    files=tuple(combined.values()),
                    inputs=unique.value,
                ),
            )

        planned = transaction.preview_sources(
            repository_root,
            {
                item.path: item.desired_content.decode(c.DEFAULT_ENCODING)
                for item in analysis.files
                if item.desired_content is not None
            },
            plan_exposure,
            inputs=analysis.inputs,
        )
        if planned.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
        if planned.value.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned.value)
        return r[m.Infra.CodegenPhaseAnalysis].ok(planned.value.value)

    @classmethod
    def _accepted_candidate(
        cls,
        transaction: FlextInfraCodegenTransaction,
        repository_root: Path,
        analysis: m.Infra.CodegenPhaseAnalysis,
        validator: Callable[[Path], p.Result[bool]] | None,
    ) -> p.Result[bool]:
        """Preview the planned candidate through the consumer validator.

        Args:
            transaction: Open recoverable file transaction.
            repository_root: Governed workspace root of the publication.
            analysis: Planned phase analysis to preview.
            validator: Consumer acceptance gate, or ``None`` to accept.

        Returns:
            Whether the consumer accepted the previewed candidate, or the
            first preview or acceptance failure.

        """
        if validator is None:
            return r[bool].ok(value=True)
        accepted = transaction.preview_sources(
            repository_root,
            {
                item.path: item.desired_content.decode(c.DEFAULT_ENCODING)
                for item in analysis.files
                if item.desired_content is not None
            },
            lambda view_root, _candidate: validator(view_root),
            inputs=analysis.inputs,
        )
        if accepted.failure:
            return r[bool].from_failure(accepted)
        if accepted.value.failure:
            return r[bool].from_failure(accepted.value)
        if not accepted.value.value:
            return r[bool].fail("semantic candidate acceptance rejected")
        return r[bool].ok(value=True)

    @classmethod
    def _appended_projection_phase(
        cls,
        transaction: FlextInfraCodegenTransaction,
        session: m.Infra.CodegenTransactionSession,
        repository_root: Path,
        projection_roots: t.VariadicTuple[Path],
        preflight: Callable[[], p.Result[bool]] | None,
        projection_analyses: list[m.Infra.CodegenPhaseAnalysis],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Plan and append the generated projection phase once per publication.

        Args:
            transaction: Open recoverable file transaction.
            session: Locked session holding the appended semantic phase.
            repository_root: Governed workspace root of the publication.
            projection_roots: Generated projection roots to compose.
            projection_analyses: Receipt analyses accumulated for validation.

        Returns:
            The session extended by the projection phase, or its planning or
            append failure.

        """
        planned = FlextInfraCodegenLazyInit(
            repository_root=repository_root,
            project_scope_roots=projection_roots,
        ).plan_files()
        if planned.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(planned)
        projection_analyses.append(planned.value)
        return transaction.append_phase_locked(
            session,
            planned.value.phase,
            planned.value.files,
        )

    @classmethod
    def _published_paths(
        cls,
        transaction: FlextInfraCodegenTransaction,
        roots: t.MappingKV[str, Path],
        analysis: m.Infra.CodegenPhaseAnalysis,
        repository_root: Path,
        options: _PublicationOptions,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Stage, validate and commit every phase inside the locked transaction.

        Args:
            transaction: Open recoverable file transaction.
            roots: Stable pseudo-root mapping of the publication.
            analysis: Planned semantic phase analysis to publish.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            Published paths after phase receipts and consumer acceptance.

        """
        projection_analyses: list[m.Infra.CodegenPhaseAnalysis] = []
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=repository_root),
        )

        def validate_published(
            session: m.Infra.CodegenTransactionSession,
        ) -> p.Result[bool]:
            checked = cls._validate_phase_receipts(
                (analysis, *projection_analyses),
                lambda phase_analysis: transaction.validate_phase_analysis_locked(
                    phase_analysis,
                    session=session,
                ),
            )
            if checked.failure or not checked.value or validator is None:
                return checked
            return validator()

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            if preflight is not None:
                checked = preflight()
                if checked.failure:
                    return r[tuple[Path, ...]].from_failure(checked)
                if not checked.value:
                    return r[tuple[Path, ...]].fail("semantic input preflight rejected")
            started = transaction.begin_files_locked(scope_root, roots, analysis.inputs)
            if started.failure:
                return r[tuple[Path, ...]].from_failure(started)

            def apply(
                session: m.Infra.CodegenTransactionSession,
            ) -> p.Result[t.VariadicTuple[Path]]:
                witnesses = tuple(
                    plan.before
                    for plan in analysis.files
                    if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                )
                for witness in witnesses:
                    observed = u.Cli.atomic_plan_directory_chain(witness.target)
                    if observed.failure:
                        return r[tuple[Path, ...]].from_failure(observed)
                    if observed.value != witness:
                        return r[tuple[Path, ...]].fail(
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
                        return r[tuple[Path, ...]].from_failure(materialized)
                    session = materialized.value
                    for witness in witnesses:
                        verified = FlextInfraMiseArtifactsVerification.materialized_directory_chain(
                            session.journal,
                            witness,
                        )
                        if verified.failure:
                            return r[tuple[Path, ...]].from_failure(verified)
                published = transaction.append_phase_locked(
                    session,
                    analysis.phase,
                    analysis.files,
                )
                if published.failure:
                    return r[tuple[Path, ...]].from_failure(published)
                if projection_roots:
                    planned = FlextInfraCodegenLazyInit(
                        repository_root=repository_root,
                        project_scope_roots=projection_roots,
                    ).plan_files()
                    if planned.failure:
                        return r[tuple[Path, ...]].from_failure(planned)
                    projection_analyses.append(planned.value)
                    published = transaction.append_phase_locked(
                        published.value,
                        planned.value.phase,
                        planned.value.files,
                    )
                    if published.failure:
                        return r[tuple[Path, ...]].from_failure(published)
                return transaction.commit_locked(
                    published.value,
                    lambda: validate_published(published.value),
                )

            return transaction.publish_prepared_locked(started.value, apply)

        return transaction.run_files_locked(roots, publish)

    @classmethod
    def _publish_joint_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        repository_root: Path,
        options: _PublicationOptions,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Keep semantic and generated phases in the same recoverable journal.

        Args:
            analysis: Semantic phase analysis planned for publication.
            repository_root: Governed workspace root of the publication.
            options: Caller-controlled gates and scope roots.

        Returns:
            Published paths after phase receipts and consumer acceptance.

        """
        prepared = cls._prepared_transaction(analysis, repository_root, options)
        if prepared.failure:
            return r[tuple[Path, ...]].from_failure(prepared)
        transaction, roots = prepared.value
        planned = cls._group_planned_analysis(
            analysis,
            transaction,
            repository_root,
            options,
        )
        if planned.failure:
            return r[tuple[Path, ...]].from_failure(planned)
        analysis = planned.value
        accepted = cls._accepted_candidate(
            transaction,
            repository_root,
            analysis,
            options.validator,
        )
        if accepted.failure:
            return r[tuple[Path, ...]].from_failure(accepted)
        return cls._published_paths(
            transaction, roots, analysis, repository_root, options
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
        return {
            f"@semantic-{index}": project
            for index, project in enumerate(
                sorted({plan.project for plan in files} | set(projection_roots)),
            )
        }

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
