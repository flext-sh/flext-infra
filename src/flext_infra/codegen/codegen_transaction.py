"""Single extensible transaction coordinator for complete project generation."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
<<<<<<< HEAD
from flext_infra import c, m, u
=======
from flext_infra import m, u
>>>>>>> origin/0.12.0-dev
from flext_infra.codegen import (
    _codegen_staging as generic_staging,
    _mise_artifacts_journal as journal_io,
    _mise_artifacts_publication as publication,
    _mise_artifacts_state as state,
    _mise_artifacts_verification as verify,
)
<<<<<<< HEAD
from flext_infra.codegen._mise_artifacts_recovery import FlextInfraMiseRecovery
from flext_infra.codegen._mise_artifacts_staging import FlextInfraMiseStaging
=======
>>>>>>> origin/0.12.0-dev
from flext_infra.codegen.mise_artifacts_lock import FlextInfraMiseLock
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner

from ._mise_artifacts_recovery import FlextInfraMiseRecovery
from ._mise_artifacts_staging import FlextInfraMiseStaging

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransaction:
    """Keep every generation phase recoverable until one final fixed point."""

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        """Initialize the transaction with its configured Mise artifact owner."""
        self._owner = owner
        self._planner = FlextInfraMiseWorkspacePlanner(owner)
        self._lock = FlextInfraMiseLock()
        self._recovery = FlextInfraMiseRecovery()
        self._mise_staging = FlextInfraMiseStaging(owner)

    def validate(
        self, config_plans: tuple[m.Infra.CodegenFilePlan, ...] = ()
    ) -> p.Result[bool]:
        """Validate a coherent committed Mise snapshot under the generation lock."""
        return self.run_locked(
            prepare=False,
            operation=lambda scope_root: self.validate_locked(scope_root, config_plans),
        )

    def validate_locked(
        self, scope_root: Path, config_plans: tuple[m.Infra.CodegenFilePlan, ...] = ()
    ) -> p.Result[bool]:
        """Reject pending recovery/residue, then exercise real Mise consumers."""
        layout_result = (
            self._planner.layout_for_config_plans(scope_root, config_plans)
            if config_plans
            else self._planner.layout(scope_root)
        )
        if layout_result.failure:
            return r[bool].from_failure(layout_result)
        selected = self._planner.select_layout(layout_result.value, config_plans)
        if selected.failure:
            return r[bool].from_failure(selected)
        layout = selected.value
        journal = state.journal_state(layout)
        if journal.failure:
            return r[bool].from_failure(journal)
        journal_snapshot = state.journal_snapshot(journal.value)
        if journal_snapshot is not None and journal_snapshot.content is not None:
            return r[bool].fail(
                "pending generation transaction requires apply-mode recovery"
            )
        residue = state.transaction_residue(layout)
        if residue:
            return r[bool].fail(
                f"generation staging has no journal authority: {residue[0]}"
            )
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return r[bool].from_failure(plan)
        return verify.live(self._owner, plan.value)

    @staticmethod
    def validate_phase_analysis_locked(
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[bool]:
        """Validate a published phase from its immutable planning receipt."""
        return verify.phase_analysis_live(analysis)

    def run_locked[T](
        self, *, prepare: bool, operation: Callable[[Path], p.Result[T]]
    ) -> p.Result[T]:
        """Run one operation under the stable descriptor-bound workspace lock."""
        identity = self._planner.scope_identity()
        if identity.failure:
            return r[T].from_failure(identity)
        try:
            with self._lock.lease(identity.value):
                return self._run_locked_operation(
                    identity.value, prepare=prepare, operation=operation
                )
        except BlockingIOError:
            return r[T].fail(
                "another generation transaction owns the workspace: "
                f"{identity.value.git_dir / c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME}"
            )
        except OSError as exc:
            return r[T].fail_op("execute generation transaction", exc)

    def _run_locked_operation[T](
        self,
        identity: m.Infra.GitIdentityReport,
        *,
        prepare: bool,
        operation: Callable[[Path], p.Result[T]],
    ) -> p.Result[T]:
        """Reauthenticate and reconcile after the descriptor lock is held."""
        if prepare:
            reconciled = self._reconcile(identity)
            if reconciled.failure:
                return r[T].from_failure(reconciled)
        return operation(identity.repo_root)

    def begin_locked(
        self,
        scope_root: Path,
        config_plans: tuple[m.Infra.CodegenFilePlan, ...],
        file_plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Publish conform+Mise as the first fully journaled prepared phase."""
        result_type = r[m.Infra.CodegenTransactionSession]
        transaction_id = secrets.token_hex(16)
        layout_result = self._planner.layout_for_config_plans(
            scope_root, config_plans, transaction_id=transaction_id
        )
        if layout_result.failure:
            return result_type.from_failure(layout_result)
        layout = layout_result.value
        if state.transaction_residue(layout):
            return result_type.fail(
                f"generation residue has no journal authority: {state.transaction_residue(layout)[0]}"
            )
        transaction_directories = state.plan_transaction_directories(layout)
        if transaction_directories.failure:
            return result_type.from_failure(transaction_directories)
        conform_directories = state.plan_directories(
            layout,
            phase="conform",
            requested=u.Infra.codegen_required_directories(file_plans),
            disposition="generated",
        )
        if conform_directories.failure:
            return result_type.from_failure(conform_directories)
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return result_type.from_failure(plan)
        journal_before = state.journal_state(layout)
        if journal_before.failure:
            return result_type.from_failure(journal_before)
        journal_before_snapshot = state.journal_snapshot(journal_before.value)
        if journal_before_snapshot is None:
            return result_type.fail("generation journal state is unavailable")
        if journal_before_snapshot.content is not None:
            return result_type.fail("generation journal appeared after locked recovery")
        config_paths = {config_plan.path for config_plan in config_plans}
        ordinary = tuple(
            file_plan
            for file_plan in file_plans
            if file_plan.path not in config_paths
            and u.Infra.codegen_file_requires_effect(file_plan)
        )
        source_states = self._phase_sources("conform", file_plans)
        if source_states.failure:
            return result_type.from_failure(source_states)
        mise_sources = tuple(
            ("mise", source)
            for project in plan.value.projects
            for source in project.config.sources
        )
        all_sources = (*source_states.value, *mise_sources)
        source_barrier = verify.states_current(
            self._unique_states(tuple(source for _phase, source in all_sources))
        )
        if source_barrier.failure:
            return result_type.from_failure(source_barrier)
        staging_journal = journal_io.begin(
            plan.value,
            transaction_id=transaction_id,
            sources=all_sources,
            directories=transaction_directories.value,
        )
        if staging_journal.failure:
            return result_type.from_failure(staging_journal)
        staging_state = journal_io.write(
            layout, staging_journal.value, expected=journal_before_snapshot
        )
        if staging_state.failure:
            return result_type.from_failure(staging_state)
        with_conform_directories = journal_io.append_directories(
            staging_journal.value, conform_directories.value
        )
        if with_conform_directories.failure:
            return result_type.from_failure(with_conform_directories)
        if with_conform_directories.value != staging_journal.value:
            staging_state = journal_io.write(
                layout, with_conform_directories.value, expected=staging_state.value
            )
            if staging_state.failure:
                return result_type.from_failure(staging_state)
        active_staging_journal = with_conform_directories.value
        materialized = self._materialize_directories(
            layout, active_staging_journal, staging_state.value
        )
        if materialized.failure:
            return result_type.from_failure(materialized)
        active_journal, active_state = materialized.value
        ordinary_staged = generic_staging.stage_file_plans(layout, "conform", ordinary)
        if ordinary_staged.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, ordinary_staged.error or "cannot stage conform files"
                )
            )
        mise_staged = self._mise_staging.stage(plan.value)
        if mise_staged.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, mise_staged.error or "cannot stage Mise artifacts"
                )
            )
        publications = (*ordinary_staged.value, *mise_staged.value)
        barriers = self._prepublication_barriers(
            plan.value,
            tuple(source for _phase, source in all_sources),
            tuple(item.before for item in publications),
        )
        if barriers.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, barriers.error or "generation barrier failed"
                )
            )
        prepared_journal = journal_io.append_prepared(
            plan.value, active_journal, publications, sources=all_sources
        )
        if prepared_journal.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    prepared_journal.error or "cannot prepare generation journal",
                )
            )
        manifested = self._register_transaction_manifests(
            layout, prepared_journal.value
        )
        if manifested.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    manifested.error or "cannot register generation staging tree",
                )
            )
        prepared_state = journal_io.write(
            layout, manifested.value, expected=active_state
        )
        if prepared_state.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout,
                    prepared_state.error
                    or "cannot publish prepared generation journal",
                )
            )
        barriers = self._prepublication_barriers(
            plan.value,
            tuple(source for _phase, source in all_sources),
            tuple(item.before for item in publications),
        )
        if barriers.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, barriers.error or "generation barrier failed"
                )
            )
        published = publication.publish(publications)
        if published.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, published.error or "generation publication failed"
                )
            )
        publication_state = verify.publications_live(publications)
        if publication_state.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    publication_state.error
                    or "generation publication identity changed",
                )
            )
        live = verify.live(self._owner, plan.value, mise_staged.value)
        if live.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, live.error or "Mise real-consumer validation failed"
                )
            )
        return result_type.ok(
            m.Infra.CodegenTransactionSession(
                plan=plan.value,
                journal=manifested.value,
                journal_state=prepared_state.value,
                written_files=published.value,
            )
        )

    def append_phase_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Append, durably authorize, then publish one dependent generated phase."""
        result_type = r[m.Infra.CodegenTransactionSession]
        changed = tuple(
            plan for plan in plans if u.Infra.codegen_file_requires_effect(plan)
        )
        if not changed:
            return result_type.ok(session)
        layout = session.plan.layout
        observed_journal = state.journal_state(layout)
        observed_journal_snapshot = (
            None
            if observed_journal.failure
            else state.journal_snapshot(observed_journal.value)
        )
        if (
            observed_journal.failure
            or observed_journal_snapshot is None
            or observed_journal_snapshot != session.journal_state
        ):
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    observed_journal.error
                    or "generation journal changed between phases",
                )
            )
        sources = self._phase_sources(phase, plans)
        if sources.failure:
            return result_type.from_failure(
                self._recover_failure(layout, sources.error or "invalid phase sources")
            )
        source_states = tuple(source for _phase, source in sources.value)
        source_barrier = verify.states_current(self._unique_states(source_states))
        if source_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, source_barrier.error or f"{phase} sources changed"
                )
            )
        staged = generic_staging.stage_file_plans(layout, phase, changed)
        if staged.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, staged.error or f"cannot stage {phase} phase"
                )
            )
        destination_barrier = verify.states_current(
            tuple(item.before for item in staged.value)
        )
        if destination_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, destination_barrier.error or f"{phase} destinations changed"
                )
            )
        extended = journal_io.append_prepared(
            session.plan, session.journal, staged.value, sources=sources.value
        )
        if extended.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, extended.error or f"cannot append {phase} journal phase"
                )
            )
        manifested = self._register_transaction_manifests(layout, extended.value)
        if manifested.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, manifested.error or f"cannot register {phase} staging tree"
                )
            )
        persisted = journal_io.write(
            layout, manifested.value, expected=session.journal_state
        )
        if persisted.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout, persisted.error or f"cannot persist {phase} journal phase"
                )
            )
        source_barrier = verify.states_current(self._unique_states(source_states))
        destination_barrier = verify.states_current(
            tuple(item.before for item in staged.value)
        )
        if source_barrier.failure or destination_barrier.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    source_barrier.error
                    or destination_barrier.error
                    or f"{phase} prepublication barrier failed",
                )
            )
        published = publication.publish(staged.value)
        if published.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, published.error or f"cannot publish {phase} phase"
                )
            )
        live = verify.publications_live(staged.value)
        if live.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout, live.error or f"{phase} publication changed"
                )
            )
        return result_type.ok(
            m.Infra.CodegenTransactionSession(
                plan=session.plan,
                journal=manifested.value,
                journal_state=persisted.value,
                written_files=(*session.written_files, *published.value),
            )
        )

    def append_directories_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        phase: str,
        directories: tuple[Path, ...],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Authorize missing generated directories durably, then create them."""
        result_type = r[m.Infra.CodegenTransactionSession]
        planned = state.plan_directories(
            session.plan.layout,
            phase=phase,
            requested=directories,
            disposition="generated",
        )
        if planned.failure:
            return result_type.from_failure(
                self._recover_failure(
                    session.plan.layout,
                    planned.error or f"cannot plan {phase} directories",
                )
            )
        if not planned.value:
            return result_type.ok(session)
        observed = state.journal_state(session.plan.layout)
        observed_snapshot = (
            None if observed.failure else state.journal_snapshot(observed.value)
        )
        if (
            observed.failure
            or observed_snapshot is None
            or observed_snapshot != session.journal_state
        ):
            return result_type.from_failure(
                self._recover_failure(
                    session.plan.layout,
                    observed.error or "generation journal changed before directories",
                )
            )
        extended = journal_io.append_directories(session.journal, planned.value)
        if extended.failure:
            return result_type.from_failure(
                self._recover_failure(
                    session.plan.layout,
                    extended.error or f"cannot append {phase} directories",
                )
            )
        persisted = journal_io.write(
            session.plan.layout, extended.value, expected=session.journal_state
        )
        if persisted.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    session.plan.layout,
                    persisted.error or f"cannot persist {phase} directories",
                )
            )
        materialized = self._materialize_directories(
            session.plan.layout, extended.value, persisted.value
        )
        if materialized.failure:
            return result_type.from_failure(materialized)
        recorded, recorded_state = materialized.value
        return result_type.ok(
            m.Infra.CodegenTransactionSession(
                plan=session.plan,
                journal=recorded,
                journal_state=recorded_state,
                written_files=session.written_files,
            )
        )

    def commit_locked[T](
        self,
        session: m.Infra.CodegenTransactionSession,
        validator: Callable[[], p.Result[T]],
    ) -> p.Result[tuple[tuple[Path, ...], T]]:
        """Validate final reality and return its receipt after atomic commit."""
        validated = validator()
        if validated.failure:
            return r[tuple[tuple[Path, ...], T]].from_failure(
                self._recover_failure(
                    session.plan.layout,
                    validated.error or "generation fixed-point validation failed",
                )
            )
        observed = state.journal_state(session.plan.layout)
        observed_snapshot = (
            None if observed.failure else state.journal_snapshot(observed.value)
        )
        if (
            observed.failure
            or observed_snapshot is None
            or observed_snapshot != session.journal_state
        ):
            return r[tuple[tuple[Path, ...], T]].from_failure(
                self._recover_failure(
                    session.plan.layout,
                    observed.error or "generation journal changed before commit",
                )
            )
        committed = journal_io.commit(session.journal)
        if committed.failure:
            return r[tuple[tuple[Path, ...], T]].from_failure(
                self._recover_failure(
                    session.plan.layout,
                    committed.error or "cannot validate generation commit",
                )
            )
        committed_state = journal_io.write(
            session.plan.layout, committed.value, expected=session.journal_state
        )
        if committed_state.failure:
            return r[tuple[tuple[Path, ...], T]].from_failure(
                self._recover_failure(
                    session.plan.layout,
                    committed_state.error or "cannot persist generation commit",
                )
            )
        cleaned = journal_io.cleanup(
            session.plan.layout, committed.value, committed_state.value
        )
        if cleaned.failure:
            return r[tuple[tuple[Path, ...], T]].from_failure(cleaned)
        return r[tuple[tuple[Path, ...], T]].ok((
            session.written_files,
            validated.value,
        ))

    def _materialize_directories(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Create and durably bind one directory identity at a time."""
        result_type = r[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]
        current_journal = journal
        current_state = journal_state
        for intent in current_journal.directories:
            if intent.created is not None:
                continue
            created = state.create_journaled_directory(
                layout, current_journal.directories, intent
            )
            if created.failure:
                return result_type.from_failure(
                    self._recover_failure(
                        layout,
                        created.error or f"cannot create directory {intent.path}",
                    )
                )
            directories = tuple(
                created.value if entry.path == intent.path else entry
                for entry in current_journal.directories
            )
            recorded = journal_io.record_directories(current_journal, directories)
            if recorded.failure:
                failed = self._compensate_directory_persistence(
                    layout,
                    created.value,
                    recorded.error or f"cannot record directory {intent.path}",
                    journal_write=False,
                )
                return result_type.from_failure(failed)
            persisted = journal_io.write(layout, recorded.value, expected=current_state)
            if persisted.failure:
                failed = self._compensate_directory_persistence(
                    layout,
                    created.value,
                    persisted.error or f"cannot persist directory {intent.path}",
                    journal_write=True,
                )
                return result_type.from_failure(failed)
            current_journal = recorded.value
            current_state = persisted.value
        return result_type.ok((current_journal, current_state))

    def _compensate_directory_persistence(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        created: m.Infra.CodegenJournalDirectory,
        failure: str,
        *,
        journal_write: bool,
    ) -> p.Result[bool]:
        """Compensate only this invocation's exact empty-directory effect."""
        compensated = state.compensate_created_directory(created)
        if compensated.failure:
            return r[bool].fail(
                f"{failure}; created-directory compensation failed: {compensated.error}"
            )
        if journal_write:
            return self._handle_journal_write_failure(layout, failure)
        return self._recover_failure(layout, failure)

    @staticmethod
    def _register_transaction_manifests(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        registered = verify.register_transaction_manifests(layout, journal)
        if registered.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(registered)
        return journal_io.record_directories(journal, registered.value)

    def abort_locked(
        self, session: m.Infra.CodegenTransactionSession, failure: str
    ) -> p.Result[bool]:
        """Recover the complete prepared transaction and preserve the cause."""
        return self._recover_failure(session.plan.layout, failure)

    @staticmethod
    def _phase_sources(
        phase: str, plans: tuple[m.Infra.CodegenFilePlan, ...]
    ) -> p.Result[tuple[tuple[str, m.Cli.AtomicFileState], ...]]:
        result_type = r[tuple[tuple[str, m.Cli.AtomicFileState], ...]]
        sources: dict[Path, m.Cli.AtomicFileState] = {}
        for plan in plans:
            for source in plan.source_states:
                previous = sources.get(source.path)
                if previous is not None and previous != source:
                    return result_type.fail(
                        f"{phase} planner observed two states for {source.path}"
                    )
                sources[source.path] = source
        return result_type.ok(tuple((phase, source) for source in sources.values()))

    @staticmethod
    def _unique_states(
        states: tuple[m.Cli.AtomicFileState, ...],
    ) -> tuple[m.Cli.AtomicFileState, ...]:
        by_path: dict[Path, m.Cli.AtomicFileState] = {}
        for file_state in states:
            by_path[file_state.path] = file_state
        return tuple(by_path.values())

    @staticmethod
    def _prepublication_barriers(
        plan: m.Infra.MiseToolchainWorkspacePlan,
        sources: tuple[m.Cli.AtomicFileState, ...],
        destinations: tuple[m.Cli.AtomicFileState, ...],
    ) -> p.Result[bool]:
        source_barrier = verify.states_current(
            FlextInfraCodegenTransaction._unique_states(sources)
        )
        if source_barrier.failure:
            return source_barrier
        destination_barrier = verify.states_current(destinations)
        if destination_barrier.failure:
            return destination_barrier
        return verify.sources(plan)

    def _reconcile(self, identity: m.Infra.GitIdentityReport) -> p.Result[bool]:
        layout = self._planner.journal_layout(identity)
        if layout.failure:
            return r[bool].from_failure(layout)
        journal = state.journal_state(layout.value)
        if journal.failure:
            return r[bool].from_failure(journal)
        journal_snapshot = state.journal_snapshot(journal.value)
        if journal_snapshot is not None and journal_snapshot.content is not None:
            return self._recover(layout.value)
        return r[bool].ok(True)

    def _handle_journal_write_failure(
        self, layout: m.Infra.MiseToolchainWorkspaceLayout, failure: str
    ) -> p.Result[bool]:
        observed = state.journal_state(layout)
        if observed.failure:
            return r[bool].fail(
                f"{failure}; journal inspection failed: {observed.error}"
            )
        observed_snapshot = state.journal_snapshot(observed.value)
        if observed_snapshot is None or observed_snapshot.content is None:
            return r[bool].fail(f"{failure}; durable journal disappeared")
        return self._recover_failure(layout, failure)

    def _recover_failure(
        self, layout: m.Infra.MiseToolchainWorkspaceLayout, failure: str
    ) -> p.Result[bool]:
        recovered = self._recover(layout)
        if recovered.failure:
            return r[bool].fail(f"{failure}; recovery failed: {recovered.error}")
        return r[bool].fail(failure)

    def _recover(self, layout: m.Infra.MiseToolchainWorkspaceLayout) -> p.Result[bool]:
        loaded = journal_io.read(layout)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        journal, journal_state = loaded.value
        selectors = tuple(project.selector for project in journal.projects)
        recovery_layout = self._planner.layout_from_selectors(
            layout.scope_root, selectors, transaction_id=journal.transaction_id
        )
        if recovery_layout.failure:
            return r[bool].from_failure(recovery_layout)
        if recovery_layout.value.journal_path != layout.journal_path:
            return r[bool].fail("generation journal identity changed during recovery")
        return self._recovery.execute(recovery_layout.value, journal, journal_state)


__all__: list[str] = ["FlextInfraCodegenTransaction"]
