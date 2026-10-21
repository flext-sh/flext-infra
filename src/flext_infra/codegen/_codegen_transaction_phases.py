"""Dependent-phase append, directory authorization, and commit mixin.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenStaging,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsProcess,
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMisePublication,
)
from flext_infra.codegen._codegen_transaction_recovery import (
    FlextInfraCodegenTransactionRecovery,
)


class FlextInfraCodegenTransactionPhases(FlextInfraCodegenTransactionRecovery):
    """Append dependent phases and directories, then commit the journal."""

    def append_phase_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        issues: t.VariadicTuple[m.Infra.Issue] = (),
        publication_policy: m.Infra.CodegenPhasePublicationPolicy | None = None,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Append, durably authorize, then publish one dependent generated phase.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        batch_admission = (
            None if publication_policy is None else publication_policy.admission
        )
        staged_validator = (
            None if publication_policy is None else publication_policy.staged_validator
        )
        if batch_admission is not None and (
            batch_admission.analysis is None
            or batch_admission.analysis.phase != phase
            or batch_admission.analysis.files != plans
            or batch_admission.admitted_states != batch_admission.analysis.inputs
        ):
            return result_type.fail("batch analysis differs from requested phase")
        bound = self.bind_publication_proof(
            session, plans, batch_admission=batch_admission
        )
        if bound.failure:
            return result_type.from_failure(bound)
        session = bound.value
        recorded = self.record_publication(session, phase=phase)
        if recorded.failure:
            return result_type.from_failure(recorded)
        if issues:
            session = session.model_copy(
                update={"issues": (*session.issues, *issues)},
            )
        changed = tuple(
            plan for plan in plans if u.Infra.codegen_file_requires_effect(plan)
        )
        if not changed:
            unchanged = self._unchanged_phase_session(
                session,
                plans,
                batch_admission=batch_admission,
            )
            if unchanged.failure or staged_validator is None:
                return unchanged
            return self._validate_staged_consumer(
                unchanged.value,
                (),
                staged_validator,
            )
        authorized = self._authorize_phase_destinations(session, phase, changed, plans)
        return self._append_authorized_phase(
            session,
            authorized,
            self._PendingPhase(
                phase=phase,
                changed=changed,
                all_plans=plans,
                staged_validator=staged_validator,
                batch_admission=batch_admission,
            ),
        )

    class _PendingPhase(m.Infra.FrozenArbitrary):
        """Dependent-phase append request bound by the phase entry point."""

        phase: str = m.Field(
            description="Dependent phase awaiting transaction admission"
        )
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan] = m.Field(
            default=(), description="Plans changing files in this dependent phase"
        )
        all_plans: t.VariadicTuple[m.Infra.CodegenFilePlan] = m.Field(
            default=(), description="Complete plan inventory for this dependent phase"
        )
        staged_validator: (
            Callable[
                [
                    m.Infra.CodegenTransactionSession,
                    t.VariadicTuple[m.Infra.CodegenStagedFile],
                ],
                p.Result[m.Infra.CodegenTransactionSession],
            ]
            | None
        ) = m.Field(
            default=None, description="Public validator for the staged dependent phase"
        )
        batch_admission: m.Infra.CodegenPhaseOutcome | None = m.Field(
            default=None,
            description="Producer admission result for the dependent batch",
        )

    @staticmethod
    def _unchanged_phase_session(
        session: m.Infra.CodegenTransactionSession,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        batch_admission: m.Infra.CodegenPhaseOutcome | None,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Return the recorded session when no plan requires an effect.

        Args:
            session: The session recorded for the declared phase.
            plans: Every declared plan of the phase.
            batch_admission: Existing batch admission requiring re-proof.

        Returns:
            The unchanged session, or the re-proof failure.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if batch_admission is None:
            return result_type.ok(session)
        admitted = FlextInfraMiseArtifactsVerification.plans_current(
            plans, journal=session.journal
        )
        if admitted.failure:
            return result_type.from_failure(admitted)
        return result_type.ok(session)

    def _append_authorized_phase(
        self,
        session: m.Infra.CodegenTransactionSession,
        authorized: p.Result[
            t.Triple[
                m.Infra.CodegenTransactionSession,
                t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ],
        pending: p.Infra.CodegenPendingPhase,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Stage and publish a phase only after its source authority is proven.

        Args:
            session: The session recorded before this phase's authorization.
            authorized: The phase authorization outcome.
            pending: The dependent-phase append request.

        Returns:
            The session advanced to the durably published phase.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if authorized.failure:
            return result_type.from_failure(authorized)
        phase, changed = pending.phase, pending.changed
        aligned, tagged_sources, source_states = authorized.value
        prepared = self.prepare_phase_staging_locked(
            aligned,
            phase,
            changed,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        authorized_phase = (prepared.value, tagged_sources, source_states)
        staged = self._stage_authorized_phase(authorized_phase, phase, changed)
        if staged.failure:
            return result_type.from_failure(staged)
        persisted = self._persist_phase_journal(authorized_phase, phase, staged.value)
        if persisted.failure:
            return result_type.from_failure(persisted)
        current = m.Infra.CodegenTransactionSession(
            plan=prepared.value.plan,
            journal=persisted.value[0],
            journal_state=persisted.value[1],
            written_files=prepared.value.written_files,
            published_files=prepared.value.published_files,
            retained_files=prepared.value.retained_files,
            issues=prepared.value.issues,
            exception=prepared.value.exception,
        )
        if pending.staged_validator is not None:
            checked = self._validate_staged_consumer(
                current,
                staged.value,
                pending.staged_validator,
            )
            if checked.failure:
                return result_type.from_failure(checked)
            current = checked.value
        return self._publish_bound_phase(
            session, prepared.value, staged.value, current, pending
        )

    def _publish_bound_phase(
        self,
        session: m.Infra.CodegenTransactionSession,
        prepared: m.Infra.CodegenTransactionSession,
        staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        current: m.Infra.CodegenTransactionSession,
        pending: p.Infra.CodegenPendingPhase,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Publish the verified phase and bind its proof into the session.

        Args:
            session: The session recorded before this phase's authorization.
            prepared: The session prepared for staging.
            staged: The staged files of the phase.
            current: The durably staged session, consumer-validated if given.
            pending: The dependent-phase append request.

        Returns:
            The session advanced to the durably published phase.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        published = self._publish_verified_phase(
            prepared.plan.layout,
            pending.phase,
            staged,
            batch_admission=pending.batch_admission,
            journal=current.journal,
        )
        if not published.success:
            return result_type.from_failure(published)
        if published.value.issues:
            return result_type.fail(
                "\n".join(issue.formatted for issue in published.value.issues),
                exception=session.exception or published.value.exception,
                error_code=c.Infra.ToolOutcome.ERROR.value,
                error_data={
                    "written_files": tuple(
                        str(path) for path in published.value.written_files
                    ),
                    "issues": tuple(
                        issue.model_dump(mode="json")
                        for issue in published.value.issues
                    ),
                },
            )
        journal, journal_state = current.journal, current.journal_state
        if any(item.dependency_group is not None for item in staged):
            recorded = FlextInfraMiseArtifactsJournal.read(prepared.plan.layout)
            if recorded.failure:
                return result_type.from_failure(recorded)
            journal, journal_state = recorded.value
            original = self._live_producer_journal(journal)
            if original.failure:
                return result_type.from_failure(original)
            journal = original.value
        bound = self.bind_publication_proof(
            m.Infra.CodegenTransactionSession(
                plan=prepared.plan,
                journal=journal,
                journal_state=journal_state,
                written_files=(*session.written_files, *published.value.written_files),
                published_files=(
                    *session.published_files,
                    *published.value.published_files,
                ),
                retained_files=(
                    *session.retained_files,
                    *published.value.retained_files,
                ),
                issues=(*session.issues, *published.value.issues),
                exception=session.exception or published.value.exception,
            ),
            pending.all_plans,
        )
        if bound.failure:
            return result_type.from_failure(bound)
        return self.record_publication(bound.value, phase=pending.phase)

    def _validate_staged_consumer(
        self,
        current: m.Infra.CodegenTransactionSession,
        staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        validator: Callable[
            [
                m.Infra.CodegenTransactionSession,
                t.VariadicTuple[m.Infra.CodegenStagedFile],
            ],
            p.Result[m.Infra.CodegenTransactionSession],
        ],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Consume the staged phase and reauthenticate its journal and inputs.

        Returns:
            The consumer's session after both authority barriers succeed.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        checked = validator(current, staged)
        if checked.failure:
            return result_type.from_failure(
                self._recover_failure(
                    current.plan.layout,
                    r[bool].fail(
                        checked.error or "staged consumer failed",
                        exception=checked.exception,
                        error_code=checked.error_code,
                        error_data=checked.error_data,
                    ),
                )
            )
        current = checked.value
        journal_barrier = FlextInfraMiseArtifactsState.unchanged_journal(
            current,
            "journal changed during staged consumer",
        )
        if journal_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(
                    current.plan.layout,
                    r[bool].fail(
                        journal_barrier.error or "staged consumer authority changed",
                        exception=journal_barrier.exception,
                        error_code=journal_barrier.error_code,
                        error_data=journal_barrier.error_data,
                    ),
                )
            )
        return result_type.ok(current)

    def materialize_package_view_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.StagePackagePlan,
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionSession, m.Infra.StagePackageView]]:
        """Materialize only journal-declared runtime bytes before live publication.

        Returns:
            The durable session and its descriptor-authenticated package view.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionSession, m.Infra.StagePackageView]
        ]
        authorized = self._package_sources_authorized(session, plan)
        if authorized.failure:
            return result_type.from_failure(authorized)
        prepared = self._package_view_inputs(session, plan, publication)
        if prepared.failure:
            return result_type.from_failure(prepared)
        root, layouts, writes, desired = prepared.value
        materialized = self._materialize_package_writes(session, writes)
        if materialized.failure:
            return result_type.from_failure(materialized)
        view = self._package_view_snapshot(plan, publication, root, layouts, desired)
        if view.failure:
            return result_type.from_failure(view)
        return result_type.ok((materialized.value, view.value))

    @staticmethod
    def _package_sources_authorized(
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.StagePackagePlan,
    ) -> p.Result[bool]:
        """Bind each pinned source to its existing immutable journal authority.

        Returns:
            Whether every source matches its recorded journal identity.

        """
        result_type = r[bool]
        for source in plan.inputs:
            previous = next(
                (item for item in session.journal.sources if item.path == source.path),
                None,
            )
            if previous is None:
                return result_type.fail(
                    f"candidate source has no journal authority: {source.path}"
                )
            record = FlextInfraMiseArtifactsJournal.source_record(
                previous.phase, source, previous
            )
            if record.failure:
                return result_type.from_failure(record)
            if record.value != previous:
                return result_type.fail(
                    f"candidate source differs from journal authority: {source.path}"
                )
        return result_type.ok(value=True)

    @staticmethod
    def _package_view_inputs(
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.StagePackagePlan,
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[
        tuple[
            Path,
            t.VariadicTuple[m.Infra.RopeProjectLayout],
            t.VariadicTuple[tuple[Path, bytes, int]],
            bytes,
        ]
    ]:
        """Bind package paths and ordered bytes to the authenticated replacement.

        Returns:
            The transaction root, relocated layouts, writes, and desired bytes.

        """
        result_type = r[
            tuple[
                Path,
                t.VariadicTuple[m.Infra.RopeProjectLayout],
                t.VariadicTuple[tuple[Path, bytes, int]],
                bytes,
            ]
        ]
        participant = next(
            (
                item
                for item in session.plan.layout.file_participants
                if item.root == publication.project
            ),
            None,
        )
        replacement = publication.replacement
        if participant is None or replacement is None or replacement.content is None:
            return result_type.fail(
                "candidate package has no authenticated replacement participant"
            )
        root = participant.transaction_root / "package-view"
        layouts = tuple(
            layout.model_copy(
                update={
                    "project_root": root / layout.package_name,
                    "src_dir": root
                    / layout.package_name
                    / layout.src_dir.relative_to(layout.project_root),
                    "package_dir": root
                    / layout.package_name
                    / layout.package_dir.relative_to(layout.project_root),
                    "init_path": root
                    / layout.package_name
                    / layout.init_path.relative_to(layout.project_root),
                }
            )
            for layout in plan.layouts
        )
        writes: list[tuple[Path, bytes, int]] = []
        for before in plan.inputs:
            if before.content is None:
                continue
            if before.mode is None:
                return result_type.fail(
                    f"candidate source mode is unauthenticated: {before.path}"
                )
            original = next(
                (
                    layout
                    for layout in plan.layouts
                    if before.path.is_relative_to(layout.project_root)
                ),
                None,
            )
            if original is None:
                continue
            path = (
                root
                / original.package_name
                / before.path.relative_to(original.project_root)
            )
            content = (
                replacement.content
                if before.path == publication.before.path
                else before.content
            )
            writes.append((path, content, before.mode))
        return result_type.ok((root, layouts, tuple(writes), replacement.content))

    def _materialize_package_writes(
        self,
        session: m.Infra.CodegenTransactionSession,
        writes: t.VariadicTuple[tuple[Path, bytes, int]],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Journal directories and absent intentions before guarded package writes.

        Returns:
            The package session with its physical manifest durably recorded.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        directories = FlextInfraMiseArtifactsState.plan_directories(
            session.plan.layout,
            phase=c.Infra.CodegenStagedFilePhase.TRANSACTION,
            requested=tuple(sorted({path.parent for path, _content, _mode in writes})),
            disposition="temporary",
        )
        if directories.failure:
            return result_type.from_failure(directories)
        materialized = self._persist_directories(
            session, "transaction", directories.value
        )
        if materialized.failure:
            return result_type.from_failure(materialized)
        session = m.Infra.CodegenTransactionSession(
            plan=session.plan,
            journal=materialized.value[0],
            journal_state=materialized.value[1],
            written_files=session.written_files,
            published_files=session.published_files,
            retained_files=session.retained_files,
            issues=session.issues,
            exception=session.exception,
        )
        intended = self._persist_staging_intents(session, "package-view", writes)
        if intended.failure:
            return result_type.from_failure(intended)
        session = intended.value
        intents = {item.before.path: item for item in session.journal.staging_intents}
        for path, content, mode in writes:
            written = FlextInfraMiseArtifactsProcess.write_new(
                path, content, mode, intent=intents[path]
            )
            if written.failure:
                return result_type.from_failure(written)
        return self._persist_package_manifest(session)

    def _persist_package_manifest(
        self,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Finalize physical receipts and CAS-persist the resulting manifest.

        Returns:
            The session carrying the exact durable package manifest journal.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        recorded = FlextInfraMiseArtifactsJournal.record_transaction_manifests(
            session.plan.layout, session.journal
        )
        if recorded.failure:
            return result_type.from_failure(recorded)
        durable = self._write_journal(
            session.plan.layout, recorded.value, expected=session.journal_state
        )
        if durable.failure:
            return result_type.from_failure(durable)
        session = m.Infra.CodegenTransactionSession(
            plan=session.plan,
            journal=recorded.value,
            journal_state=durable.value,
            written_files=session.written_files,
            published_files=session.published_files,
            retained_files=session.retained_files,
            issues=session.issues,
            exception=session.exception,
        )
        return result_type.ok(session)

    @staticmethod
    def _package_view_snapshot(
        plan: m.Infra.StagePackagePlan,
        publication: m.Infra.CodegenStagedFile,
        root: Path,
        layouts: t.VariadicTuple[m.Infra.RopeProjectLayout],
        desired: bytes,
    ) -> p.Result[m.Infra.StagePackageView]:
        """Inventory the materialized tree and require the exact desired target.

        Returns:
            The physical package view with its authenticated target receipt.

        """
        result_type = r[m.Infra.StagePackageView]
        inventory = u.Cli.atomic_inventory_physical_tree(root)
        if inventory.failure:
            return result_type.from_failure(inventory)
        local = next(
            layout for layout in layouts if layout.package_name == plan.package
        )
        target_path = local.package_dir / publication.before.path.name
        target = next(
            (entry for entry in inventory.value.entries if entry.path == target_path),
            None,
        )
        if target is None or target.sha256 != FlextInfraMiseArtifactsFiles.digest(
            desired
        ):
            return result_type.fail(
                "candidate target differs from desired staged replacement"
            )
        return result_type.ok(
            m.Infra.StagePackageView(
                plan=plan,
                root=root,
                layouts=layouts,
                manifest=inventory.value,
                target=target,
            )
        )

    def prepare_phase_staging_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Persist absent-leaf intentions before any replacement or backup write.

        Returns:
            The session with its staging intentions durably recorded.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        aligned = FlextInfraMiseArtifactsState.unchanged_journal(
            session,
            "generation journal changed before staging intentions",
        )
        if aligned.failure:
            return result_type.from_failure(aligned)
        session = aligned.value
        prepared = self.prepare_phase_staging_journal_locked(
            session.plan.layout,
            session.journal,
            session.journal_state,
            phase,
            changed,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        journal, journal_state = prepared.value
        return result_type.ok(
            session.model_copy(
                update={"journal": journal, "journal_state": journal_state},
            ),
        )

    def prepare_phase_staging_journal_locked(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Authorize staging for the actual staging or prepared journal lifecycle.

        Returns:
            The persisted journal and its exact physical receipt.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        current = FlextInfraMiseArtifactsJournal.read(layout)
        if current.failure:
            return result_type.from_failure(current)
        if (
            current.value[0].model_dump() != journal.model_dump()
            or current.value[1] != journal_state
        ):
            return result_type.fail(
                "generation journal changed before staging intentions",
            )
        writes = self._phase_staging_writes(layout, phase, changed)
        if writes.failure:
            return result_type.from_failure(writes)
        planned = FlextInfraMiseArtifactsState.plan_directories(
            layout,
            phase=c.Infra.CodegenStagedFilePhase.TRANSACTION,
            requested=writes.value[1],
            disposition="temporary",
        )
        if planned.failure:
            return result_type.from_failure(planned)
        if planned.value:
            recorded = self._persist_directory_journal(
                layout,
                journal,
                journal_state,
                "transaction",
                planned.value,
            )
            if recorded.failure:
                return result_type.from_failure(recorded)
            journal, journal_state = recorded.value
        return self._persist_staging_journal(
            layout,
            journal,
            journal_state,
            phase,
            writes.value[0],
        )

    @staticmethod
    def _phase_staging_writes(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[
        t.Pair[t.VariadicTuple[tuple[Path, bytes, int]], t.VariadicTuple[Path]]
    ]:
        """Plan ordered writes, including authenticated dependent-group preimages.

        Returns:
            The ordered writes and sorted transaction directories they require.

        """
        result_type = r[
            t.Pair[t.VariadicTuple[tuple[Path, bytes, int]], t.VariadicTuple[Path]]
        ]
        checked = FlextInfraCodegenStaging.plan_file_staging(layout, phase, changed)
        if checked.failure:
            return result_type.from_failure(checked)
        prepared, phase_roots = checked.value
        writes: list[tuple[Path, bytes, int]] = []
        directories = set(phase_roots)
        for index, (plan, before, replacement, present) in enumerate(prepared):
            if plan.dependency_group is not None and before.content is not None:
                if before.mode is None:
                    return result_type.fail(
                        f"group preimage has no authenticated mode: {before.path}"
                    )
                writes.append((
                    replacement[0] / f"{index:06d}.original",
                    before.content,
                    before.mode,
                ))
            if present:
                root, content, mode = replacement
                writes.append((root / f"{index:06d}.replacement", content, mode))
        return result_type.ok((tuple(writes), tuple(sorted(directories))))

    def _persist_staging_intents(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        writes: t.VariadicTuple[tuple[Path, bytes, int]],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Capture absent leaves and CAS-persist their authority before writes.

        Returns:
            The session carrying the exact persisted intention journal.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        persisted = self._persist_staging_journal(
            session.plan.layout,
            session.journal,
            session.journal_state,
            phase,
            writes,
        )
        if persisted.failure:
            return result_type.from_failure(persisted)
        journal, journal_state = persisted.value
        return result_type.ok(
            session.model_copy(
                update={"journal": journal, "journal_state": journal_state},
            ),
        )

    def _persist_staging_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        current: m.Infra.CodegenTransactionJournal,
        expected: m.Cli.AtomicFileState,
        phase: str,
        writes: t.VariadicTuple[tuple[Path, bytes, int]],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Persist absent leaf authority without inventing a prepared session.

        Returns:
            The journal with its durable staging intentions and physical receipt.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        intents = list(current.staging_intents)
        for path, content, mode in writes:
            absent = FlextInfraMiseArtifactsFiles.read_state(path, required=False)
            if absent.failure:
                return result_type.from_failure(absent)
            if absent.value.content is not None:
                return result_type.fail(
                    f"staging intention leaf already exists: {path}",
                )
            intents.append(
                m.Infra.CodegenStagingIntent(
                    before=absent.value,
                    sha256=FlextInfraMiseArtifactsFiles.digest(content),
                    mode=mode,
                ),
            )
        extended = FlextInfraMiseArtifactsJournal.validated_extension(
            current,
            current.model_copy(update={"staging_intents": tuple(intents)}),
        )
        if extended.failure:
            return result_type.from_failure(extended)
        persisted = self._write_journal(layout, extended.value, expected=expected)
        if persisted.failure:
            return result_type.from_failure(persisted)
        u.Cli.emit_raw(
            f"{c.Cli.OUTPUT_LOG_LEVEL_INFO}: phase={phase} "
            f"staging-intentions={len(writes)} durable-before-write\n",
            error=True,
        )
        return result_type.ok((extended.value, persisted.value))

    def _authorize_phase_destinations(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[
        t.Triple[
            m.Infra.CodegenTransactionSession,
            t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Authorize the journal and prove the phase's sources unchanged.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.CodegenTransactionSession,
                t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
                t.VariadicTuple[m.Cli.AtomicFileState]]]`` carrying the aligned
            session, the tagged sources, and their bare states.

        """
        result_type = r[
            t.Triple[
                m.Infra.CodegenTransactionSession,
                t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        aligned = FlextInfraMiseArtifactsState.unchanged_journal(
            session,
            "generation journal changed between phases",
        )
        if aligned.failure:
            return result_type.from_failure(aligned)
        session = aligned.value
        layout = session.plan.layout
        destinations = self._unique_phase_destinations(session, changed)
        if destinations.failure:
            return result_type.from_failure(destinations)
        sources = FlextInfraCodegenPreconditions.phase_sources(phase, plans)
        if sources.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        sources.error or "invalid phase sources",
                        exception=sources.exception,
                        error_code=sources.error_code,
                        error_data=sources.error_data,
                    ),
                ),
            )
        # Reuse the original witnesses: requested directory effects may already
        # have materialized parents under this journal before file authorization.
        recorded = FlextInfraMiseArtifactsJournal.append_prepared(
            session.plan, session.journal, (), sources=sources.value
        )
        if recorded.failure:
            return result_type.from_failure(recorded)
        persisted = self._write_journal(
            layout, recorded.value, expected=session.journal_state
        )
        if persisted.failure:
            return result_type.from_failure(persisted)
        session = session.model_copy(
            update={"journal": recorded.value, "journal_state": persisted.value},
        )
        source_states = tuple(source for _phase, source in sources.value)
        return result_type.ok((session, sources.value, source_states))

    def _unique_phase_destinations(
        self,
        session: m.Infra.CodegenTransactionSession,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[bool]:
        """Authenticate paths and reject destinations owned by an earlier phase.

        Returns:
            Success, or the original path or recovered ownership failure.

        """
        layout = session.plan.layout
        existing_paths = {entry.path for entry in session.journal.entries}
        for plan in changed:
            relative = FlextInfraMiseArtifactsFiles.transaction_relative(
                layout, plan.path
            )
            if relative.failure:
                return r[bool].from_failure(relative)
            if relative.value in existing_paths:
                return self._recover_failure(
                    layout,
                    r[bool].fail(
                        "multiple generation phases own one destination: "
                        f"{relative.value}",
                    ),
                )
        return r[bool].ok(value=True)

    def _stage_authorized_phase(
        self,
        authorized: t.Triple[
            m.Infra.CodegenTransactionSession,
            t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
        """Stage the phase's files, bind parents, and prove destinations stable.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]``.

        """
        session = authorized[0]
        layout = session.plan.layout
        staged = FlextInfraCodegenStaging.stage_file_plans(
            layout,
            phase,
            changed,
            intents=session.journal.staging_intents,
            directories=tuple(
                directory.created
                for directory in session.journal.directories
                if directory.created is not None
            ),
        )
        if staged.failure:
            return r[t.VariadicTuple[m.Infra.CodegenStagedFile]].from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        staged.error or f"cannot stage {phase} phase",
                        exception=staged.exception,
                        error_code=staged.error_code,
                        error_data=staged.error_data,
                    ),
                ),
            )
        bound = FlextInfraMiseArtifactsState.bind_created_parents(
            session.journal.directories, staged.value
        )
        if bound.failure:
            return r[t.VariadicTuple[m.Infra.CodegenStagedFile]].from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        bound.error or f"cannot bind {phase} destination parents",
                        exception=bound.exception,
                        error_code=bound.error_code,
                        error_data=bound.error_data,
                    ),
                ),
            )
        return bound

    def _persist_phase_journal(
        self,
        authorized: t.Triple[
            m.Infra.CodegenTransactionSession,
            t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
        phase: str,
        staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Append, manifest, and durably persist the phase, then re-verify barriers.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        session, tagged_sources, _source_states = authorized
        layout = session.plan.layout
        extended = FlextInfraMiseArtifactsJournal.append_prepared(
            session.plan,
            session.journal,
            staged,
            sources=tagged_sources,
        )
        if extended.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        extended.error or f"cannot append {phase} journal phase",
                        exception=extended.exception,
                        error_code=extended.error_code,
                        error_data=extended.error_data,
                    ),
                ),
            )
        manifested = FlextInfraMiseArtifactsJournal.record_transaction_manifests(
            layout, extended.value
        )
        if manifested.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        manifested.error or f"cannot register {phase} staging tree",
                        exception=manifested.exception,
                        error_code=manifested.error_code,
                        error_data=manifested.error_data,
                    ),
                ),
            )
        persisted = self._write_journal(
            layout,
            manifested.value,
            expected=session.journal_state,
        )
        if persisted.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout,
                    r[bool].from_failure(persisted),
                ),
            )
        return result_type.ok((manifested.value, persisted.value))

    def _publish_verified_phase(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        phase: str,
        staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        batch_admission: m.Infra.CodegenPhaseOutcome | None = None,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Publish the verified staged set and prove it live.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]`` with the written
            files.

        """
        published = FlextInfraMisePublication.publish(
            staged,
            batch_admission=batch_admission,
            journal=journal,
            prior_publications=self._prior_publications,
        )
        if published.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        published.error or f"cannot publish {phase} phase",
                        exception=published.exception,
                        error_code=published.error_code,
                        error_data=published.error_data,
                    ),
                ),
            )
        grouped = tuple(item for item in staged if item.dependency_group is not None)
        if grouped:
            failed_paths = {Path(issue.file) for issue in published.value.issues}
            failed_groups = {
                item.dependency_group
                for item in grouped
                if item.before.path in failed_paths
            }
            admitted_paths = {
                item.before.path for item in published.value.published_files
            }
            observed = FlextInfraMiseArtifactsJournal.read(layout)
            if observed.failure:
                return r[m.Infra.CodegenPhaseOutcome].from_failure(observed)
            journal, snapshot = observed.value
            entries: t.MutableSequenceOf[m.Infra.CodegenJournalEntry] = []
            for entry in journal.entries:
                destination = FlextInfraMiseArtifactsFiles.resolve_transaction(
                    layout, entry.path, purpose="group admission"
                )
                if destination.failure:
                    return r[m.Infra.CodegenPhaseOutcome].from_failure(destination)
                entries.append(
                    entry.model_copy(
                        update={
                            "group_admitted": entry.group_admitted
                            or (
                                entry.dependency_group is not None
                                and destination.value in admitted_paths
                            ),
                            "recover_group": entry.recover_group
                            or entry.dependency_group in failed_groups,
                        }
                    )
                )
            recorded = self._write_journal(
                layout,
                journal.model_copy(update={"entries": tuple(entries)}),
                expected=snapshot,
            )
            if recorded.failure:
                return r[m.Infra.CodegenPhaseOutcome].from_failure(recorded)
            if failed_groups:
                recovered = self._recovery.restore_groups(
                    layout,
                    journal.model_copy(update={"entries": tuple(entries)}),
                )
                if recovered.failure:
                    return r[m.Infra.CodegenPhaseOutcome].fail(
                        published.value.issues[0].formatted,
                        exception=published.value.exception,
                        error_data={"cleanup_error": recovered.error},
                    )
                live = tuple(
                    item
                    for item in published.value.published_files
                    if FlextInfraMiseArtifactsVerification.publications_live((
                        item,
                    )).success
                )
                published = r[m.Infra.CodegenPhaseOutcome].ok(
                    published.value.model_copy(
                        update={
                            "published_files": live,
                            "written_files": tuple(item.before.path for item in live),
                        }
                    ),
                )
        return published

    def append_directories_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        directories: t.VariadicTuple[Path],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Authorize missing generated directories durably, then create them.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        planned = FlextInfraMiseArtifactsState.plan_directories(
            session.plan.layout,
            phase=phase,
            requested=directories,
            disposition="generated",
        )
        if planned.failure:
            return result_type.from_failure(
                self._recover_failure(
                    session.plan.layout,
                    r[bool].fail(
                        planned.error or f"cannot plan {phase} directories",
                        exception=planned.exception,
                        error_code=planned.error_code,
                        error_data=planned.error_data,
                    ),
                ),
            )
        if not planned.value:
            return result_type.ok(session)
        materialized = self._persist_directories(session, phase, planned.value)
        if materialized.failure:
            return result_type.from_failure(materialized)
        recorded, recorded_state = materialized.value
        return result_type.ok(
            m.Infra.CodegenTransactionSession(
                plan=session.plan,
                journal=recorded,
                journal_state=recorded_state,
                written_files=session.written_files,
                published_files=session.published_files,
                retained_files=session.retained_files,
                issues=session.issues,
                exception=session.exception,
            ),
        )

    def _persist_directories(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        planned: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Authorize the journal, append the directories, and materialize them.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        unchanged = FlextInfraMiseArtifactsState.unchanged_journal(
            session,
            "generation journal changed before directories",
        )
        if unchanged.failure:
            return r[
                t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
            ].from_failure(unchanged)
        return self._persist_directory_journal(
            session.plan.layout,
            unchanged.value.journal,
            unchanged.value.journal_state,
            phase,
            planned,
        )

    def _persist_directory_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
        phase: str,
        planned: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Materialize directory intentions after their journal CAS succeeds.

        Returns:
            The journal carrying every created directory's physical receipt.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        extended = FlextInfraMiseArtifactsJournal.append_directories(journal, planned)
        if extended.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        extended.error or f"cannot append {phase} directories",
                        exception=extended.exception,
                        error_code=extended.error_code,
                        error_data=extended.error_data,
                    ),
                ),
            )
        persisted = self._write_journal(
            layout,
            extended.value,
            expected=journal_state,
        )
        if persisted.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout,
                    r[bool].from_failure(persisted),
                ),
            )
        return self._materialize_directories(layout, extended.value, persisted.value)

    def commit_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        *,
        published_files: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Report every target, preserve gains, and settle the publication cursor.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        endpoints = tuple(
            {
                receipt.before.path: receipt for receipt in session.published_files
            }.values()
        )
        try:
            settled = self.record_publication(session).flat_map(
                lambda _recorded: self._settle_publication(session, endpoints)
            )
            if settled.failure and session.exception is not None:
                session.exception.add_note(
                    f"generation settlement failed: {settled.error}"
                )
                return r[t.VariadicTuple[Path]].fail(
                    "\n".join(issue.formatted for issue in session.issues)
                    or str(session.exception),
                    exception=session.exception,
                    error_code=c.Infra.ToolOutcome.ERROR.value,
                    error_data={
                        **(settled.error_data or {}),
                        "written_files": tuple(
                            str(path) for path in session.written_files
                        ),
                        "issues": tuple(
                            issue.model_dump(mode="json") for issue in session.issues
                        ),
                        "settlement_error": settled.error,
                    },
                )
            if settled.failure or publication_receipts is None:
                return settled
            receipt = self.publication_outcome(session, completed=True)
            if receipt.failure:
                return r[t.VariadicTuple[Path]].from_failure(receipt)
            publication_receipts.append(receipt.value)
            return settled
        finally:
            if published_files is not None:
                live_paths = {
                    receipt.before.path
                    for receipt in endpoints
                    if FlextInfraMiseArtifactsVerification.publications_live(
                        (receipt,),
                    ).success
                }
                published_files.extend(
                    receipt
                    for receipt in session.published_files
                    if receipt.before.path in live_paths
                )

    def _settle_publication(
        self,
        session: m.Infra.CodegenTransactionSession,
        endpoints: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Verify the commit, settle the cursor, and report residual issues.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        result_type = r[t.VariadicTuple[Path]]
        committed = FlextInfraMiseArtifactsVerification.publications_live(
            endpoints,
        ).flat_map(lambda _current: self._verified_commit(session))
        if committed.failure:
            return result_type.from_failure(committed)
        authorized = self._authorize_journal(session.plan.layout, committed.value[0])
        if authorized.failure:
            return result_type.from_failure(authorized)
        cleaned = FlextInfraMiseArtifactsVerification.publications_live(
            endpoints,
        ).flat_map(
            lambda _current: FlextInfraMiseArtifactsJournal.cleanup(
                session.plan.layout,
                committed.value[0],
                committed.value[1],
            )
        )
        if cleaned.failure:
            return result_type.from_failure(cleaned)
        completed = FlextInfraMiseArtifactsVerification.publications_live(
            endpoints,
        ).flat_map(lambda _current: self.record_publication(session, completed=True))
        if completed.failure:
            return result_type.from_failure(completed)
        if not session.issues:
            return result_type.ok(session.written_files)
        return result_type.fail(
            "\n".join(issue.formatted for issue in session.issues),
            error_code=c.Infra.ToolOutcome.ERROR.value,
            exception=session.exception,
            error_data={
                "written_files": tuple(str(path) for path in session.written_files),
                "issues": tuple(
                    issue.model_dump(mode="json") for issue in session.issues
                ),
            },
        )

    def _verified_commit(
        self,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Re-prove the journal, commit it, and durably persist the commit.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        layout = session.plan.layout
        unchanged = FlextInfraMiseArtifactsState.unchanged_journal(
            session,
            "generation journal changed before commit",
        )
        if unchanged.failure:
            return result_type.from_failure(unchanged)
        session = unchanged.value
        committed = FlextInfraMiseArtifactsJournal.commit(session.journal)
        if committed.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        committed.error or "cannot validate generation commit",
                        exception=committed.exception,
                        error_code=committed.error_code,
                        error_data=committed.error_data,
                    ),
                ),
            )
        committed_state = self._write_journal(
            layout,
            committed.value,
            expected=session.journal_state,
        )
        if committed_state.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].fail(
                        committed_state.error or "cannot persist generation commit",
                        exception=committed_state.exception,
                        error_code=committed_state.error_code,
                        error_data=committed_state.error_data,
                    ),
                ),
            )
        return result_type.ok((committed.value, committed_state.value))


__all__: list[str] = ["FlextInfraCodegenTransactionPhases"]
