"""Semantic publication through the canonical recoverable file transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)
from flext_infra.codegen.staged_package import FlextInfraStagedPackage

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraSemanticPublication:
    """Publish semantic file plans through the recoverable codegen transaction."""

    @classmethod
    def publish_semantic_file_plans(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        repository_root: Path,
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
            projection_roots=projection_roots,
            validator=validator,
            source_guard=None,
            published_files=published_files,
            dependency_group=dependency_group,
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
            projection_roots=(),
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
            input_roots=candidate.roots,
            dependency_group=analysis.value.phase,
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
    def _publish_joint_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        repository_root: Path,
        projection_roots: t.VariadicTuple[Path],
        validator: Callable[[Path], p.Result[bool]] | None,
        source_guard: Callable[[], p.Result[bool]] | None,
        input_roots: t.VariadicTuple[Path] = (),
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
        dependency_group: str | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Keep semantic and generated phases in the same recoverable journal.

        Returns:
            Published paths after phase receipts and consumer acceptance.
        """
        projection_analyses: list[m.Infra.CodegenPhaseAnalysis] = []
        roots = cls._semantic_phase_roots(
            analysis.files, (*projection_roots, *input_roots)
        )
        producer = FlextInfraCodegenPreconditions.capture_producer()
        if producer.failure:
            return r[tuple[Path, ...]].from_failure(producer)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=repository_root),
            producer=producer.value,
        )
        if dependency_group is not None:

            def plan_exposure(
                view_root: Path,
                _candidate: m.Infra.StageSourcePlan,
            ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
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
                        before = u.Cli.atomic_read_binary_file_state(
                            path, required=False
                        )
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
                return r[tuple[Path, ...]].from_failure(planned)
            if planned.value.failure:
                return r[tuple[Path, ...]].from_failure(planned.value)
            analysis = planned.value.value

        if validator is not None:
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
                return r[tuple[Path, ...]].from_failure(accepted)
            if accepted.value.failure:
                return r[tuple[Path, ...]].from_failure(accepted.value)
            if not accepted.value.value:
                return r[tuple[Path, ...]].fail(
                    "semantic candidate acceptance rejected"
                )

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            guarded = cls._guard_source_inputs(source_guard)
            if guarded.failure:
                return r[tuple[Path, ...]].from_failure(guarded)
            started = transaction.begin_files_locked(scope_root, roots, analysis.inputs)
            if started.failure:
                return r[tuple[Path, ...]].from_failure(started)

            def apply(
                session: m.Infra.CodegenTransactionSession,
            ) -> p.Result[t.VariadicTuple[Path]]:
                guarded = cls._guard_source_inputs(source_guard)
                if guarded.failure:
                    return r[tuple[Path, ...]].from_failure(guarded)
                published = transaction.append_phase_locked(
                    session,
                    analysis.phase,
                    analysis.files,
                )
                if published.failure:
                    return r[tuple[Path, ...]].from_failure(published)
                if projection_roots and dependency_group is None:
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
                verified = cls._validate_phase_receipts(
                    (analysis, *projection_analyses),
                    transaction.validate_phase_analysis_locked,
                )
                if verified.failure:
                    return r[tuple[Path, ...]].from_failure(verified)
                return transaction.commit_locked(
                    published.value, published_files=published_files
                )

            return transaction.publish_prepared_locked(started.value, apply)

        return transaction.run_files_locked(roots, publish)

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
