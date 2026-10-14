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
    FlextInfraMiseArtifactsFiles as files,
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
        dependencies = cls._source_prerequisites(plan.source_states, {})
        if dependencies.failure:
            return dependencies
        publication_before = u.Infra.codegen_file_before_state(plan)
        if publication_before.failure:
            return r[bool].from_failure(publication_before)
        if not u.Infra.codegen_file_requires_effect(plan):
            return FlextInfraMiseArtifactsVerification.states_current(
                (publication_before.value,),
            )
        before = files.read_state(plan.path, required=False)
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
        dependencies = cls._source_prerequisites(plan.source_states, {})
        if dependencies.failure:
            return dependencies
        published = files.write_publication(staged_publication.value)
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
        staged = files.read_state(staging_path, required=True)
        if staged.failure:
            return result_type.from_failure(staged)
        return result_type.ok(
            m.Infra.CodegenStagedFile(
                phase=c.Infra.CodegenStagedFilePhase(phase),
                project=plan.project,
                before=before,
                replacement=staged.value,
                source_states=plan.source_states,
                tracking=plan.tracking,
                index_before=plan.index_before,
                tracking_dependencies=plan.tracking_dependencies,
            ),
        )

    @staticmethod
    def admit_batch(
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate batch inputs and original destination states once.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        inputs = FlextInfraMisePublication._admission_inputs(analysis)
        if inputs.failure:
            return result_type.from_failure(inputs)
        current = FlextInfraMisePublication._source_prerequisites(inputs.value, {})
        if current.failure:
            return result_type.from_failure(current)
        gates = FlextInfraMisePublication._admission_gates(analysis, journal)
        if gates.failure:
            return result_type.from_failure(gates)
        outputs = FlextInfraMisePublication._admission_outputs(analysis)
        if outputs.failure:
            return result_type.from_failure(outputs)
        return result_type.ok(
            m.Infra.CodegenPhaseOutcome(
                analysis=analysis,
                admitted_states=inputs.value,
                phase=analysis.phase,
                outputs=outputs.value,
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
            return result_type.fail(
                "batch inputs differ from publication dependencies: "
                f"phase={analysis.phase}; "
                f"analysis_only={sorted(map(str, input_states.keys() - declared_states.keys()))}; "
                f"publication_only={sorted(map(str, declared_states.keys() - input_states.keys()))}; "
                f"differing_fields={differing}"
            )
        return result_type.ok(inputs.value)

    @staticmethod
    def _admission_gates(
        analysis: m.Infra.CodegenPhaseAnalysis,
        journal: m.Infra.CodegenTransactionJournal | None,
    ) -> p.Result[bool]:
        """Prove producer closure and planned destinations for the batch.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if analysis.generator_trees:
            producer = FlextInfraCodegenPreconditions.producer_trees_current(
                analysis.generator_trees,
                modules=analysis.generator_modules,
            )
            if producer.failure:
                return r[bool].from_failure(producer)
        return FlextInfraMiseArtifactsVerification.plans_current(
            analysis.files, journal=journal
        )

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
        for index, publication in enumerate(ordered, start=1):
            u.Cli.emit_raw(
                f"  publish [{index}/{len(publications)}] {publication.before.path}\n"
            )
            ready = FlextInfraMisePublication._tracking_prerequisites(
                publication,
                publications,
                written,
            )
            if ready.success:
                ready = FlextInfraMisePublication._generator_authority(
                    ordered,
                    published_states,
                    journal,
                )
            if ready.success:
                ready = FlextInfraMisePublication._source_prerequisites(
                    publication.source_states,
                    published_states,
                )
            if ready.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=ready.error or "tracking prerequisite failed",
                    ),
                )
                exception = exception or ready.exception
                continue
            observed = files.read_state(publication.before.path, required=False)
            if (
                observed.success
                and publication.phase != c.Infra.CodegenStagedFilePhase.SEMANTIC
                and publication.before.path.name == c.Infra.INIT_PY
                and u.Infra.codegen_initializer_is_authored(observed.value.content)
            ):
                retained.append(publication.before.path)
                u.Cli.info(
                    "ownership=authored disposition=retained "
                    f"target={publication.before.path}",
                )
                continue
            changed = (
                files.write_publication(publication)
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
                if exception is None:
                    exception = changed.exception
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
                exception = exception or published_receipt.exception
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
            retired = FlextInfraMisePublication._retire_index_file(publication)
            if retired.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=retired.error or "index retirement failed",
                    ),
                )
                exception = exception or retired.exception
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
        if FlextInfraMisePublication._batch_admission_mismatch(
            batch_admission,
            batch_analysis,
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
    def _batch_admission_mismatch(
        batch_admission: m.Infra.CodegenPhaseOutcome,
        batch_analysis: m.Infra.CodegenPhaseAnalysis | None,
    ) -> bool:
        """Report whether the admission outcome is not exactly this batch's.

        Returns:
            True when the admission does not match its own batch analysis.

        """
        if batch_analysis is None or batch_admission.error or batch_admission.issues:
            return True
        if batch_admission.exception is not None:
            return True
        return (
            batch_admission.phase != batch_analysis.phase
            or batch_admission.admitted_states != batch_analysis.inputs
        )

    @staticmethod
    def _generator_authority(
        ordered: t.VariadicTuple[m.Infra.CodegenStagedFile],
        published_states: t.MappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ],
        journal: m.Infra.CodegenTransactionJournal | None,
    ) -> p.Result[bool]:
        """Reauthenticate generator trees with staged and published authority.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if journal is None or not journal.generator_trees:
            return r[bool].ok(value=True)
        authority = {item.path: item for item in journal.outputs}
        for staged in ordered:
            if staged.replacement is None or staged.before.path in published_states:
                continue
            encoded = FlextInfraMiseArtifactsJournal.source_record(
                "staging", staged.replacement
            )
            if encoded.failure:
                return r[bool].from_failure(encoded)
            authority[encoded.value.path] = encoded.value
        for _before, after in published_states.values():
            encoded = FlextInfraMiseArtifactsJournal.source_record("output", after)
            if encoded.failure:
                return r[bool].from_failure(encoded)
            authority[encoded.value.path] = encoded.value
        return FlextInfraCodegenPreconditions.producer_trees_current(
            journal.generator_trees,
            tuple(authority.values()),
            modules=journal.generator_modules,
        )

    @staticmethod
    def _publication_receipt(
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Read back one published destination and prove its staged identity.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        receipt = files.read_state(
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
    def _retire_index_file(
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Retire one portable index binding after its publication.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        if publication.index_before is None:
            return r[m.Infra.GitBoolReport].ok(value=m.Infra.GitBoolReport())
        return u.Infra.git_retire_index_file(
            m.Infra.GitIndexRetirementRequest(
                repo_root=publication.project,
                entry=publication.index_before,
            ),
        )

    @staticmethod
    def _source_prerequisites(
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
        published: t.MappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ],
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
        return FlextInfraMiseArtifactsVerification.states_current(tuple(expected))

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
            observed = files.read_state(dependency, required=True)
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
