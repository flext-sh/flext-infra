"""Guarded live publication for one fully journaled generation phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenPreconditions,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMisePublication:
    """Publish staged generated files through full-state guarded primitives."""

    @staticmethod
    def _invalidate_project_document(path: Path) -> None:
        """Drop the process-wide parsed pyproject after this writer replaces it.

        Why: flext-core caches the parsed pyproject per process keyed by root; a
        plan built right after publication must read the published document.
        """
        if path.name == c.PYPROJECT_FILENAME:
            u.read_project_document_cached.cache_clear()

    @classmethod
    def publish_file_plan(
        cls,
        plan: m.Infra.CodegenFilePlan,
        *,
        phase: str,
    ) -> p.Result[bool]:
        """Publish one FilePlan through write_publication without a journal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        dependencies = cls._source_prerequisites(
            plan.source_states,
            {},
            directories=plan.source_directories,
            topology=plan.source_query_topology,
        )
        if dependencies.failure:
            return dependencies
        publication_before = u.Infra.codegen_file_before_state(plan)
        if publication_before.failure:
            return r[bool].from_failure(publication_before)
        if not u.Infra.codegen_file_requires_effect(plan):
            return FlextInfraMiseArtifactsVerification.states_current(
                (publication_before.value,),
            )
        before = FlextInfraMiseArtifactsFiles.read_state(plan.path, required=False)
        if before.failure:
            return r[bool].from_failure(before)
        return cls._publish_required_plan(
            plan,
            phase=phase,
            before=before.value,
            publication_before=publication_before.value,
        )

    @classmethod
    def _publish_required_plan(
        cls,
        plan: m.Infra.CodegenFilePlan,
        *,
        phase: str,
        before: m.Cli.AtomicFileState,
        publication_before: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Publish one plan that requires a guarded publication effect.

        Args:
            plan: File plan to publish.
            phase: Staged file phase name for the staged publication.
            before: Freshly observed destination state gating authored retention.
            publication_before: Plan-time destination state bound to the staging.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if (
            phase != c.Infra.CodegenStagedFilePhase.SEMANTIC
            and plan.path.name == c.Infra.INIT_PY
            and u.Infra.codegen_initializer_is_authored(before.content)
        ):
            u.Cli.info(
                f"ownership=authored disposition=retained target={plan.path}",
            )
            return r[bool].ok(value=False)
        staged_publication = cls._staged_publication(
            plan,
            phase=phase,
            before=publication_before,
        )
        if staged_publication.failure:
            return r[bool].from_failure(staged_publication)
        dependencies = cls._source_prerequisites(
            plan.source_states,
            {},
            directories=plan.source_directories,
            topology=plan.source_query_topology,
        )
        if dependencies.failure:
            return dependencies
        published = FlextInfraMiseArtifactsFiles.write_publication(
            staged_publication.value
        )
        FlextInfraMisePublication._invalidate_project_document(plan.path)
        return published

    @classmethod
    def _staged_publication(
        cls,
        plan: m.Infra.CodegenFilePlan,
        *,
        phase: str,
        before: m.Cli.AtomicFileState,
    ) -> p.Result[m.Infra.CodegenStagedFile]:
        """Stage one plan's desired content beside its destination.

        A deletion-only plan stages the journal entry whose replacement is
        None; the model owns that contract.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenStagedFile]``.

        """
        result_type = r[m.Infra.CodegenStagedFile]
        if plan.desired_content is None:
            return result_type.ok(
                m.Infra.CodegenStagedFile(
                    phase=c.Infra.CodegenStagedFilePhase(phase),
                    project=plan.project,
                    before=before,
                    replacement=None,
                    source_states=plan.source_states,
                    source_directories=plan.source_directories,
                    source_query_topology=plan.source_query_topology,
                    tracking=plan.tracking,
                    index_before=plan.index_before,
                    tracking_dependencies=plan.tracking_dependencies,
                ),
            )
        mode = plan.desired_mode
        if mode is None:
            return result_type.fail(f"codegen desired mode is absent: {plan.path}")
        staging_path = plan.path.with_name(f".{plan.path.name}.codegen-staging")
        staged_before = u.Cli.atomic_read_binary_file_state(
            staging_path,
            required=False,
        )
        if staged_before.failure:
            return result_type.from_failure(staged_before)
        written = u.Cli.atomic_write_binary_file_guarded(
            staged_before.value,
            plan.desired_content,
            permission_mode=mode,
        )
        if written.failure:
            return result_type.from_failure(written)
        staged = FlextInfraMiseArtifactsFiles.read_state(staging_path, required=True)
        if staged.failure:
            return result_type.from_failure(staged)
        return result_type.ok(
            m.Infra.CodegenStagedFile(
                phase=c.Infra.CodegenStagedFilePhase(phase),
                project=plan.project,
                before=before,
                replacement=staged.value,
                source_states=plan.source_states,
                source_directories=plan.source_directories,
                source_query_topology=plan.source_query_topology,
                tracking=plan.tracking,
                index_before=plan.index_before,
                tracking_dependencies=plan.tracking_dependencies,
            ),
        )

    @staticmethod
    def admit_batch(
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        producer: m.Infra.CodegenPhaseAnalysis | None = None,
        journal: m.Infra.CodegenTransactionJournal | None = None,
        admission: m.Infra.CodegenPhaseOutcome | None = None,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome] = (),
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate a batch or require its exact previously admitted context.

        An injected producer is the original complete producer observation;
        its inputs and native closure are proven once before binding metadata.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        if producer is not None:
            bound = FlextInfraMisePublication._admission_gates(
                analysis, prior_publications, producer=producer
            )
            if bound.failure:
                return result_type.from_failure(bound)
            analysis = bound.value
        if admission is not None:
            if (
                admission.analysis != analysis
                or FlextInfraMisePublication._batch_admission_is_inconsistent(admission)
            ):
                return result_type.fail(
                    admission.error
                    or (
                        "external batch admission differs from captured "
                        "producer context"
                    ),
                    exception=admission.exception,
                )
            return result_type.ok(admission)
        return FlextInfraMisePublication._admit_fresh_batch(
            analysis,
            producer=producer,
            journal=journal,
            prior_publications=prior_publications,
        )

    @staticmethod
    def _admit_fresh_batch(
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        producer: m.Infra.CodegenPhaseAnalysis | None,
        journal: m.Infra.CodegenTransactionJournal | None,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Prove fresh inputs and destinations before recording admitted outputs.

        Returns:
            The exact fresh admission or its first input or destination failure.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        inputs = FlextInfraMisePublication._admission_inputs(analysis)
        if inputs.failure:
            return result_type.from_failure(inputs)
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            analysis.source_directories, analysis.source_query_topology
        )
        analysis = analysis.model_copy(
            update={
                "source_directories": directories,
                "source_query_topology": topology,
            }
        )
        current = FlextInfraMisePublication._source_prerequisites(
            inputs.value,
            {},
            directories=analysis.source_directories,
            topology=analysis.source_query_topology,
        )
        if current.failure:
            return result_type.from_failure(current)
        if producer is None:
            current_producer = FlextInfraMisePublication._admission_gates(
                analysis, prior_publications
            )
            if current_producer.failure:
                return result_type.from_failure(current_producer)
        destinations = FlextInfraMiseArtifactsVerification.plans_current(
            analysis.files, journal=journal
        )
        if destinations.failure:
            return result_type.from_failure(destinations)
        outputs = FlextInfraMisePublication._admission_outputs(analysis)
        if outputs.failure:
            return result_type.from_failure(outputs)
        return result_type.ok(
            m.Infra.CodegenPhaseOutcome(
                analysis=analysis,
                admitted_states=inputs.value,
                phase=analysis.phase,
                outputs=outputs.value,
                source_directories=analysis.source_directories,
                source_query_topology=analysis.source_query_topology,
            )
        )

    @staticmethod
    def _admission_inputs(
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Authenticate batch inputs against declared publication dependencies.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]``.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        inputs = FlextInfraCodegenPreconditions.unique_states(analysis.inputs)
        declared = FlextInfraCodegenPreconditions.unique_states(
            tuple(source for plan in analysis.files for source in plan.source_states)
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        if declared.failure:
            return result_type.from_failure(declared)
        if u.Cli.atomic_merge_directory_query_receipts(
            analysis.source_directories, analysis.source_query_topology
        ) != u.Cli.atomic_merge_directory_query_receipts(
            tuple(
                receipt
                for file in analysis.files
                for receipt in file.source_directories
            ),
            tuple(
                receipt
                for file in analysis.files
                for receipt in file.source_query_topology
            ),
        ):
            return result_type.fail(
                "batch native source queries differ from publication dependencies"
            )
        input_states = {item.path: item for item in inputs.value}
        declared_states = {item.path: item for item in declared.value}
        if input_states != declared_states:
            differing = tuple(
                (
                    str(path),
                    tuple(
                        field
                        for field in m.Cli.AtomicFileState.model_fields
                        if getattr(input_states[path], field)
                        != getattr(declared_states[path], field)
                    ),
                )
                for path in sorted(input_states.keys() & declared_states.keys())
                if input_states[path] != declared_states[path]
            )
            analysis_only = sorted(
                map(str, input_states.keys() - declared_states.keys()),
            )
            publication_only = sorted(
                map(str, declared_states.keys() - input_states.keys()),
            )
            return result_type.fail(
                "batch inputs differ from publication dependencies: "
                f"phase={analysis.phase}; "
                f"analysis_only={analysis_only}; "
                f"publication_only={publication_only}; "
                f"differing_fields={differing}"
            )
        return result_type.ok(inputs.value)

    @staticmethod
    def _admission_gates(
        analysis: m.Infra.CodegenPhaseAnalysis,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        producer: m.Infra.CodegenPhaseAnalysis | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Prove the complete producer once and compose the batch's metadata.

        Returns:
            The bound batch analysis, or the first producer authority failure.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        outputs = FlextInfraMiseArtifactsVerification.publication_outputs_current(
            prior_publications,
            reference=(
                producer.generator_reference
                if producer is not None
                else analysis.generator_reference
            ),
            destinations=tuple(
                dict.fromkeys((
                    *(state.path for state in analysis.inputs),
                    *(file.path for file in analysis.files),
                ))
            ),
        )
        if outputs.failure:
            return result_type.from_failure(outputs)
        if producer is not None:
            current = FlextInfraCodegenPreconditions.producer_current(
                producer, outputs=outputs.value
            )
            if current.failure:
                return result_type.from_failure(current)
            return FlextInfraCodegenPreconditions.compose_producer_analysis(
                analysis, producer, outputs=outputs.value
            )
        if analysis.generator_reference is not None or analysis.generator_trees:
            current = FlextInfraCodegenPreconditions.producer_trees_current(
                analysis.generator_trees,
                outputs.value,
                modules=analysis.generator_modules,
                reference=analysis.generator_reference,
            )
            if current.failure:
                return result_type.from_failure(current)
        return result_type.ok(analysis)

    @staticmethod
    def _admission_outputs(
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]:
        """Capture one output journal record per planned destination.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]``.

        """
        outputs: list[m.Infra.CodegenJournalSource] = []
        for plan in analysis.files:
            captured = FlextInfraMiseArtifactsJournal.source_record(
                "output", plan.before, path=plan.path
            )
            if captured.failure:
                return r[tuple[m.Infra.CodegenJournalSource, ...]].from_failure(
                    captured
                )
            outputs.append(captured.value)
        return r[tuple[m.Infra.CodegenJournalSource, ...]].ok(tuple(outputs))

    @staticmethod
    def publish(
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        batch_admission: m.Infra.CodegenPhaseOutcome | None = None,
        journal: m.Infra.CodegenTransactionJournal | None = None,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome] = (),
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Publish every target independently and retain all native failures.

        Returns:
            The complete written paths and target issues.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        if batch_admission is not None:
            validated = FlextInfraMisePublication._validated_batch_admission(
                publications,
                batch_admission,
                journal,
            )
            if validated.failure:
                return result_type.from_failure(validated)
        written: list[Path] = []
        admitted: list[m.Infra.CodegenStagedFile] = []
        retained: list[Path] = []
        issues: list[m.Infra.Issue] = []
        published_states: t.MutableMappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ] = {}
        exception: BaseException | None = None
        ordered = tuple(
            sorted(publications, key=lambda item: item.index_before is not None)
        )
        prior = FlextInfraMiseArtifactsVerification.publication_outputs_current(
            prior_publications,
            destinations=tuple(
                dict.fromkeys(
                    path
                    for item in publications
                    for path in (
                        item.before.path,
                        *(state.path for state in item.source_states),
                    )
                )
            ),
        )
        if prior.failure:
            return result_type.from_failure(prior)
        for index, publication in enumerate(ordered, start=1):
            u.Cli.emit_raw(
                f"  publish [{index}/{len(publications)}] {publication.before.path}\n"
            )
            blocking, blocked_by = FlextInfraMisePublication._prerequisite_issue(
                publication,
                publications,
                written,
                published_states,
                directory_publications=tuple(
                    item.created
                    for item in journal.directories
                    if item.created is not None
                )
                if journal is not None
                else (),
            )
            if blocking is not None:
                issues.append(blocking)
                exception = blocked_by if exception is None else exception
                continue
            observed = FlextInfraMiseArtifactsFiles.read_state(
                publication.before.path, required=False
            )
            if FlextInfraMisePublication._authored_retention(publication, observed):
                retained.append(publication.before.path)
                u.Cli.info(
                    "ownership=authored disposition=retained "
                    f"target={publication.before.path}",
                )
                continue
            changed = (
                FlextInfraMiseArtifactsFiles.write_publication(publication)
                if observed.success
                else r[bool].from_failure(observed)
            )
            if changed.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=changed.error or "publication failed",
                    ),
                )
                exception = changed.exception if exception is None else exception
                continue
            FlextInfraMisePublication._invalidate_project_document(
                publication.before.path,
            )
            written.append(publication.before.path)
            published_receipt = FlextInfraMisePublication._publication_receipt(
                publication,
            )
            if published_receipt.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=str(published_receipt.error),
                    ),
                )
                exception = (
                    published_receipt.exception if exception is None else exception
                )
                continue
            published_states[publication.before.path] = (
                publication.before,
                published_receipt.value,
            )
            admitted.append(
                publication.model_copy(
                    update={
                        "replacement": published_receipt.value
                        if publication.replacement is not None
                        else None
                    }
                )
            )
            blocking = FlextInfraMisePublication._retired_index_issue(publication)
            if blocking[0] is not None:
                issues.append(blocking[0])
                exception = blocking[1] if exception is None else exception
        return result_type.ok(
            m.Infra.CodegenPhaseOutcome(
                written_files=tuple(written),
                published_files=tuple(admitted),
                retained_files=tuple(retained),
                issues=tuple(issues),
                exception=exception,
            ),
        )

    @staticmethod
    def _retired_index_issue(
        publication: m.Infra.CodegenStagedFile,
    ) -> t.Pair[m.Infra.Issue | None, BaseException | None]:
        """Retire the publication's captured index entry after publication.

        Args:
            publication: The staged publication whose index entry is retired.

        Returns:
            The retirement failure issue with its causal exception, or
            ``(None, None)`` when no entry is captured or retirement holds.


        """
        if publication.index_before is None:
            return None, None
        retired = u.Infra.git_retire_index_file(
            m.Infra.GitIndexRetirementRequest(
                repo_root=publication.project,
                entry=publication.index_before,
            ),
        )
        if retired.success:
            return None, None
        return (
            m.Infra.Issue(
                file=str(publication.before.path),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=retired.error or "index retirement failed",
            ),
            retired.exception,
        )

    @staticmethod
    def _prerequisite_issue(
        publication: m.Infra.CodegenStagedFile,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        written: list[Path],
        published_states: t.MutableMappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ],
        *,
        directory_publications: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> t.Pair[m.Infra.Issue | None, BaseException | None]:
        """Name the first failed publication prerequisite of one target.

        Args:
            publication: The staged publication being attempted.
            publications: Every staged publication of the batch.
            written: Destination paths already written by earlier targets.
            published_states: Before and after states of published targets.
            directory_publications: Directory states published by this batch.

        Returns:
            The blocking prerequisite issue with its causal exception, or
            ``(None, None)`` when the target is ready to publish.

        """
        ready = FlextInfraMisePublication._tracking_prerequisites(
            publication,
            publications,
            written,
        )
        if ready.success:
            ready = FlextInfraMisePublication._source_prerequisites(
                publication.source_states,
                published_states,
                directories=publication.source_directories,
                topology=publication.source_query_topology,
                directory_publications=directory_publications,
            )
        if ready.success:
            return None, None
        return (
            m.Infra.Issue(
                file=str(publication.before.path),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=ready.error or "tracking prerequisite failed",
            ),
            ready.exception,
        )

    @staticmethod
    def _authored_retention(
        publication: m.Infra.CodegenStagedFile,
        observed: p.Result[m.Cli.AtomicFileState],
    ) -> bool:
        """Report whether an authored initializer destination stays untouched.

        Returns:
            True when the observed destination is an authored initializer
            outside the semantic phase.

        """
        return (
            observed.success
            and publication.phase != c.Infra.CodegenStagedFilePhase.SEMANTIC
            and publication.before.path.name == c.Infra.INIT_PY
            and u.Infra.codegen_initializer_is_authored(observed.value.content)
        )

    @staticmethod
    def _batch_admission_is_inconsistent(
        batch_admission: m.Infra.CodegenPhaseOutcome,
    ) -> bool:
        """Report whether the batch admission disagrees with its analysis.

        Returns:
            True when the admission carries an error, issues, an exception,
            or its phase, admitted states or output membership differ from the analysis.

        """
        analysis = batch_admission.analysis
        if analysis is None or batch_admission.error or batch_admission.issues:
            return True
        return (
            batch_admission.exception is not None
            or batch_admission.phase != analysis.phase
            or batch_admission.admitted_states != analysis.inputs
            or batch_admission.source_directories != analysis.source_directories
            or batch_admission.source_query_topology != analysis.source_query_topology
            or tuple(output.path for output in batch_admission.outputs)
            != tuple(plan.path for plan in analysis.files)
        )

    @staticmethod
    def _validated_batch_admission(
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        batch_admission: m.Infra.CodegenPhaseOutcome,
        journal: m.Infra.CodegenTransactionJournal | None,
    ) -> p.Result[bool]:
        """Prove the staged publications exactly match the admitted batch.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        batch_analysis = batch_admission.analysis
        if batch_analysis is None or (
            FlextInfraMisePublication._batch_admission_is_inconsistent(
                batch_admission,
            )
        ):
            return r[bool].fail(
                "publication requires its exact native batch admission",
            )
        expected = {
            plan.path
            for plan in batch_analysis.files
            if u.Infra.codegen_file_requires_effect(plan)
        }
        if expected != {item.before.path for item in publications} or any(
            item.phase != batch_analysis.phase
            and not (
                batch_analysis.phase == c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP
                and item.phase == c.Infra.CodegenStagedFilePhase.MISE
            )
            for item in publications
        ):
            return r[bool].fail(
                "staged publications differ from admitted batch",
            )
        plans = {item.path: item for item in batch_analysis.files}
        if any(
            item.project != plans[item.before.path].project
            or item.source_states != plans[item.before.path].source_states
            or item.source_directories != plans[item.before.path].source_directories
            or item.source_query_topology
            != plans[item.before.path].source_query_topology
            or (None if item.replacement is None else item.replacement.content)
            != plans[item.before.path].desired_content
            or (None if item.replacement is None else item.replacement.mode)
            != plans[item.before.path].desired_mode
            for item in publications
        ):
            return r[bool].fail(
                "staged candidates differ from admitted desired outputs",
            )
        destinations = FlextInfraMiseArtifactsVerification.plans_current(
            batch_analysis.files, journal=journal
        )
        if destinations.failure:
            return r[bool].from_failure(destinations)
        return r[bool].ok(value=True)

    @staticmethod
    def _publication_receipt(
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Read back one published destination and prove its staged identity.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        receipt = FlextInfraMiseArtifactsFiles.read_state(
            publication.before.path,
            required=publication.replacement is not None,
        )
        expected_content = (
            publication.replacement.content
            if publication.replacement is not None
            else None
        )
        expected_mode = (
            publication.replacement.mode
            if publication.replacement is not None
            else None
        )
        if receipt.failure or (
            receipt.value.content != expected_content
            or receipt.value.mode != expected_mode
        ):
            cause = (
                receipt.exception or ValueError(receipt.error)
                if receipt.failure
                else ValueError(
                    f"generated destination changed after publication: "
                    f"{publication.before.path}",
                )
            )
            return r[m.Cli.AtomicFileState].fail(str(cause), exception=cause)
        return r[m.Cli.AtomicFileState].ok(receipt.value)

    @staticmethod
    def _source_prerequisites(
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
        published: t.MappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ],
        *,
        directories: t.VariadicTuple[m.Cli.AtomicDirectoryInventory] = (),
        topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = (),
        directory_publications: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[bool]:
        """Verify this target's inputs, rebinding only this phase's own writes.

        Returns:
            Exact dependency verification or its first native cause.

        """
        expected: list[m.Cli.AtomicFileState] = []
        for source in sources:
            receipt = published.get(source.path)
            if receipt is None:
                expected.append(source)
                continue
            before, after = receipt
            if source != before:
                cause = ValueError(
                    f"generated dependency preimage differs: {source.path}",
                )
                return r[bool].fail(str(cause), exception=cause)
            expected.append(after)
        current = FlextInfraMiseArtifactsVerification.states_current(tuple(expected))
        if current.failure:
            return current
        candidates = tuple(
            inventory.root.path / name
            for inventory in directories
            for name, _predicate in inventory.queries
        ) + tuple(
            witness.target / name
            for witness in topology
            for name, _predicate in witness.queries
        )
        relevant = tuple(
            (before, after)
            for before, after in published.values()
            if any(
                after.path == path or after.path.is_relative_to(path)
                for path in candidates
            )
            or any(
                inventory.membership_queried
                and after.path.is_relative_to(inventory.root.path)
                for inventory in directories
            )
            or any(
                witness.membership_queried and after.path.is_relative_to(witness.target)
                for witness in topology
            )
        )
        effects = FlextInfraMiseArtifactsVerification.states_current(
            tuple(after for _before, after in relevant)
        )
        if effects.failure:
            return effects
        return u.Cli.atomic_verify_directory_queries(
            directories,
            topology,
            publications=relevant,
            directory_publications=directory_publications,
        )

    @staticmethod
    def _tracking_prerequisites(
        publication: m.Infra.CodegenStagedFile,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        written: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Require portable declarations from this phase before retiring their binding.

        Returns:
            Verified publication evidence for every required declaration.

        """
        for dependency in publication.tracking_dependencies:
            planned = next(
                (item for item in publications if item.before.path == dependency),
                None,
            )
            if (
                planned is None
                or dependency not in written
                or planned.replacement is None
            ):
                error = ValueError(
                    f"portable declaration was not published: {dependency}",
                )
                return r[bool].fail(str(error), exception=error)
            observed = FlextInfraMiseArtifactsFiles.read_state(
                dependency, required=True
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if (
                observed.value.content != planned.replacement.content
                or observed.value.mode != planned.replacement.mode
            ):
                error = ValueError(
                    f"portable declaration changed after publication: {dependency}",
                )
                return r[bool].fail(str(error), exception=error)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraMisePublication"]
