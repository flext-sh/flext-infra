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
        validator: Callable[[], p.Result[bool]] | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
        projection_roots: t.VariadicTuple[Path] = (),
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
                checked = validator()
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
        )

    @classmethod
    def publish_source_candidate(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        candidate: m.Infra.StageSourcePlan,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish an accepted candidate under its complete original input guard.

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
        originals = {state.path: state for state in candidate.inputs}
        if any(originals.get(plan.path) != plan.before for plan in plans):
            return r[tuple[Path, ...]].fail(
                "semantic originals differ from accepted candidate"
            )
        analysis = cls._semantic_phase_analysis(
            tuple(
                m.Infra.SemanticFilePlan(
                    project=plan.project,
                    path=plan.path,
                    before=plan.before,
                    desired_content=plan.desired_content,
                    desired_mode=plan.desired_mode,
                    changes=plan.changes,
                    source_states=candidate.inputs,
                )
                for plan in plans
            ),
            None,
        )
        if analysis.failure:
            return r[tuple[Path, ...]].from_failure(analysis)
        return cls._publish_joint_analysis(
            analysis.value,
            repository_root=candidate.workspace,
            projection_roots=(),
            validator=None,
            source_guard=lambda: FlextInfraStagedPackage.source_inputs_current(
                candidate
            ),
        )

    @classmethod
    def _semantic_phase_analysis(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        codegen: m.Infra.CodegenConfigSpec | None,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Build the same authenticated analysis for both publication inputs.

        Returns:
            The complete analysis or its first planning failure.
        """
        files = cls._concrete_file_plans(plans, codegen)
        if files.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(files)
        inputs = cls._semantic_input_snapshots(plans)
        if inputs.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(inputs)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(files.value),
                inputs=inputs.value,
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
        validator: Callable[[], p.Result[bool]] | None,
        source_guard: Callable[[], p.Result[bool]] | None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Keep semantic and generated phases in the same recoverable journal.

        Returns:
            Published paths after phase receipts and consumer acceptance.
        """
        projection_analyses: list[m.Infra.CodegenPhaseAnalysis] = []
        roots = cls._semantic_phase_roots(analysis.files, projection_roots)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=repository_root),
        )

        def validate_published() -> p.Result[bool]:
            checked = cls._validate_phase_receipts(
                (analysis, *projection_analyses),
                transaction.validate_phase_analysis_locked,
            )
            return (
                validator()
                if checked.success and checked.value and validator is not None
                else checked
            )

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
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
                return transaction.commit_locked(published.value, validate_published)

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

    @classmethod
    def _semantic_input_snapshots(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Authenticate one snapshot per semantic input path.

        Returns:
            The ordered first snapshots of every semantic input.

        """
        snapshots: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        for plan in plans:
            for state in (plan.before, *plan.source_states):
                if snapshots.setdefault(state.path, state) != state:
                    return r[t.VariadicTuple[m.Cli.AtomicFileState]].fail(
                        f"semantic input snapshots disagree: {state.path}",
                    )
        return r[t.VariadicTuple[m.Cli.AtomicFileState]].ok(
            tuple(snapshots.values()),
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
                    source_states=(plan.before, *plan.source_states),
                    owner="semantic",
                ),
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(files)


__all__: list[str] = ["FlextInfraSemanticPublication"]
