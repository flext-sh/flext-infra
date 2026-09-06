"""Crash recovery for staging, prepared, recovering, or committed journals."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from flext_core import r
from flext_infra import m
from flext_infra.codegen import (
    _mise_artifacts_files as files,
    _mise_artifacts_journal as journal_io,
    _mise_artifacts_process as process,
    _mise_artifacts_state as state,
    _mise_artifacts_verification as verify,
)

if TYPE_CHECKING:
    from flext_infra import p

type _FileIdentity = tuple[
    int | None,
    int | None,
    str | None,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
]


class FlextInfraMiseRecovery:
    """Restore only full states attributable to one durable journal."""

    def execute(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Recover an authenticated journal without consulting source topology."""
        topology = verify.journal_topology(layout, journal)
        if topology.failure:
            return topology
        roots = state.validate_transaction_roots(layout, journal)
        if roots.failure:
            return roots
        if journal.state == "staging":
            return journal_io.cleanup(layout, journal, journal_state)
        classified = self._classify(layout, journal)
        if classified.failure:
            return r[bool].from_failure(classified)
        if journal.state == "committed":
            return journal_io.cleanup(layout, journal, journal_state)
        if journal.state == "prepared":
            prepared = self._prepare_restore_candidates(layout, classified.value)
            if prepared.failure:
                return r[bool].from_failure(prepared)
            recovering = journal_io.begin_recovery(journal, prepared.value)
            if recovering.failure:
                return r[bool].from_failure(recovering)
            manifests = verify.register_transaction_manifests(layout, recovering.value)
            if manifests.failure:
                return r[bool].from_failure(manifests)
            recorded = journal_io.record_directories(recovering.value, manifests.value)
            if recorded.failure:
                return r[bool].from_failure(recorded)
            persisted = journal_io.write(layout, recorded.value, expected=journal_state)
            if persisted.failure:
                return r[bool].from_failure(persisted)
            journal = recorded.value
            journal_state = persisted.value
            classified = self._classify(layout, journal)
            if classified.failure:
                return r[bool].from_failure(classified)
        candidates = self._load_restore_candidates(layout, classified.value)
        if candidates.failure:
            return r[bool].from_failure(candidates)
        restored = self._restore(classified.value, candidates.value)
        if restored.failure:
            return restored
        exact = self._verify_rollback(layout, journal, classified.value)
        if exact.failure:
            return exact
        return journal_io.cleanup(layout, journal, journal_state)

    def _classify(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[tuple[m.Infra.CodegenRecoveryAction, ...]]:
        """Classify every live target before preparing any recovery effect."""
        result_type = r[tuple[m.Infra.CodegenRecoveryAction, ...]]
        actions: list[m.Infra.CodegenRecoveryAction] = []
        for entry in journal.entries:
            target = files.resolve_relative(
                layout.scope_root, entry.path, purpose="generated destination"
            )
            if target.failure:
                return result_type.from_failure(target)
            current = files.read_state(target.value, required=False)
            if current.failure:
                return result_type.from_failure(current)
            identity = self._identity(current.value)
            original = self._entry_identity(entry, "original")
            desired = self._entry_identity(entry, "desired")
            rollback = self._entry_identity(entry, "rollback")
            if journal.state == "committed":
                if identity != desired:
                    return result_type.fail(
                        f"committed generated file changed: {entry.path}"
                    )
                operation = "noop"
            elif (
                journal.state == "recovering" and identity == rollback
            ) or identity == original:
                operation = "noop"
            elif identity != desired:
                operation = "noop"
            elif entry.original_exists:
                operation = "restore"
            else:
                operation = "delete"
            actions.append(
                m.Infra.CodegenRecoveryAction(
                    entry=entry, current=current.value, operation=operation
                )
            )
        return result_type.ok(tuple(actions))

    def _prepare_restore_candidates(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        actions: tuple[m.Infra.CodegenRecoveryAction, ...],
    ) -> p.Result[tuple[m.Infra.CodegenStagedFile | None, ...]]:
        result_type = r[tuple[m.Infra.CodegenStagedFile | None, ...]]
        candidates: list[m.Infra.CodegenStagedFile | None] = []
        for action in actions:
            if not action.entry.original_exists:
                candidates.append(None)
                continue
            prepared = self._prepare_restore_candidate(layout, action)
            if prepared.failure:
                return result_type.from_failure(prepared)
            candidates.append(prepared.value)
        return result_type.ok(tuple(candidates))

    @staticmethod
    def _prepare_restore_candidate(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        action: m.Infra.CodegenRecoveryAction,
    ) -> p.Result[m.Infra.CodegenStagedFile]:
        entry = action.entry
        if (
            entry.original_backup is None
            or entry.original_sha256 is None
            or entry.original_mode is None
        ):
            return r[m.Infra.CodegenStagedFile].fail(
                f"generation recovery tuple is incomplete: {entry.path}"
            )
        backup_path = files.resolve_relative(
            layout.scope_root,
            entry.original_backup,
            purpose="generation recovery backup",
        )
        if backup_path.failure:
            return r[m.Infra.CodegenStagedFile].from_failure(backup_path)
        backup = files.read_state(backup_path.value, required=True)
        if backup.failure or backup.value.content is None:
            return r[m.Infra.CodegenStagedFile].fail(
                backup.error or f"generation recovery backup is absent: {entry.path}"
            )
        if (
            backup.value.mode != files.JOURNAL_MODE
            or files.digest(backup.value.content) != entry.original_sha256
        ):
            return r[m.Infra.CodegenStagedFile].fail(
                f"generation recovery backup differs: {entry.path}"
            )
        candidate_path = backup_path.value.with_suffix(".restore")
        candidate = files.read_state(candidate_path, required=False)
        if candidate.failure:
            return r[m.Infra.CodegenStagedFile].from_failure(candidate)
        if candidate.value.content is None:
            created = process.write_new(
                candidate_path, backup.value.content, entry.original_mode
            )
            if created.failure:
                return r[m.Infra.CodegenStagedFile].from_failure(created)
            candidate = files.read_state(candidate_path, required=True)
            if candidate.failure:
                return r[m.Infra.CodegenStagedFile].from_failure(candidate)
        if (
            candidate.value.content != backup.value.content
            or candidate.value.mode != entry.original_mode
        ):
            return r[m.Infra.CodegenStagedFile].fail(
                f"generation restore candidate differs: {entry.path}"
            )
        project = next(
            item.root for item in layout.projects if item.selector == entry.project
        )
        return r[m.Infra.CodegenStagedFile].ok(
            m.Infra.CodegenStagedFile(
                phase="recovery",
                project=project,
                before=action.current,
                replacement=candidate.value,
            )
        )

    def _load_restore_candidates(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        actions: tuple[m.Infra.CodegenRecoveryAction, ...],
    ) -> p.Result[tuple[m.Infra.CodegenStagedFile | None, ...]]:
        result_type = r[tuple[m.Infra.CodegenStagedFile | None, ...]]
        candidates: list[m.Infra.CodegenStagedFile | None] = []
        for action in actions:
            entry = action.entry
            if action.operation != "restore":
                candidates.append(None)
                continue
            if entry.original_backup is None:
                return result_type.fail(
                    f"generation rollback backup is absent: {entry.path}"
                )
            backup = files.resolve_relative(
                layout.scope_root,
                entry.original_backup,
                purpose="generation recovery backup",
            )
            if backup.failure:
                return result_type.from_failure(backup)
            candidate = files.read_state(
                backup.value.with_suffix(".restore"), required=True
            )
            if candidate.failure:
                return result_type.from_failure(candidate)
            if (
                self._identity(candidate.value)[2:]
                != self._entry_identity(entry, "rollback")[2:]
            ):
                return result_type.fail(
                    f"generation rollback candidate changed: {entry.path}"
                )
            project = next(
                item.root for item in layout.projects if item.selector == entry.project
            )
            candidates.append(
                m.Infra.CodegenStagedFile(
                    phase="recovery",
                    project=project,
                    before=action.current,
                    replacement=candidate.value,
                )
            )
        return result_type.ok(tuple(candidates))

    @staticmethod
    def _restore(
        actions: tuple[m.Infra.CodegenRecoveryAction, ...],
        candidates: tuple[m.Infra.CodegenStagedFile | None, ...],
    ) -> p.Result[bool]:
        paired = tuple(zip(actions, candidates, strict=True))
        for action, candidate in reversed(paired):
            if action.operation == "restore":
                if candidate is None:
                    return r[bool].fail(
                        f"generation restore candidate is absent: {action.entry.path}"
                    )
                restored = files.write_publication(candidate)
                if restored.failure:
                    return r[bool].from_failure(restored)
            elif action.operation == "delete":
                removed = files.delete_state(action.current)
                if removed.failure:
                    return r[bool].from_failure(removed)
        return r[bool].ok(True)

    def _verify_rollback(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        actions: tuple[m.Infra.CodegenRecoveryAction, ...],
    ) -> p.Result[bool]:
        by_path = {action.entry.path: action for action in actions}
        for entry in journal.entries:
            target = files.resolve_relative(
                layout.scope_root, entry.path, purpose="generated destination"
            )
            if target.failure:
                return r[bool].from_failure(target)
            current = files.read_state(target.value, required=False)
            if current.failure:
                return r[bool].from_failure(current)
            identity = self._identity(current.value)
            expected = {
                self._entry_identity(entry, "original"),
                self._entry_identity(entry, "rollback"),
            }
            action = by_path.get(entry.path)
            if action is None:
                return r[bool].fail(
                    f"generation recovery action is absent: {entry.path}"
                )
            if action.operation == "noop":
                expected.add(self._identity(action.current))
            if identity not in expected:
                return r[bool].fail(f"generated file was not restored: {entry.path}")
        return r[bool].ok(True)

    @staticmethod
    def _identity(state: m.Cli.AtomicFileState) -> _FileIdentity:
        return (
            state.parent_device,
            state.parent_inode,
            None if state.content is None else files.digest(state.content),
            state.mode,
            state.device,
            state.inode,
            state.link_count,
            state.file_attributes,
            state.reparse_tag,
        )

    @staticmethod
    def _entry_identity(
        entry: m.Infra.CodegenJournalEntry,
        prefix: Literal["original", "desired", "rollback"],
    ) -> _FileIdentity:
        if prefix == "original":
            return FlextInfraMiseRecovery._stored_identity(
                exists=entry.original_exists,
                parent_device=entry.original_parent_device,
                parent_inode=entry.original_parent_inode,
                sha256=entry.original_sha256,
                mode=entry.original_mode,
                device=entry.original_device,
                inode=entry.original_inode,
                link_count=entry.original_link_count,
                file_attributes=entry.original_file_attributes,
                reparse_tag=entry.original_reparse_tag,
            )
        if prefix == "desired":
            return FlextInfraMiseRecovery._stored_identity(
                exists=entry.desired_exists,
                parent_device=entry.desired_parent_device,
                parent_inode=entry.desired_parent_inode,
                sha256=entry.desired_sha256,
                mode=entry.desired_mode,
                device=entry.desired_device,
                inode=entry.desired_inode,
                link_count=entry.desired_link_count,
                file_attributes=entry.desired_file_attributes,
                reparse_tag=entry.desired_reparse_tag,
            )
        return FlextInfraMiseRecovery._stored_identity(
            exists=entry.rollback_exists,
            parent_device=entry.rollback_parent_device,
            parent_inode=entry.rollback_parent_inode,
            sha256=entry.rollback_sha256,
            mode=entry.rollback_mode,
            device=entry.rollback_device,
            inode=entry.rollback_inode,
            link_count=entry.rollback_link_count,
            file_attributes=entry.rollback_file_attributes,
            reparse_tag=entry.rollback_reparse_tag,
        )

    @staticmethod
    def _stored_identity(
        *,
        exists: bool | None,
        parent_device: int | None,
        parent_inode: int | None,
        sha256: str | None,
        mode: int | None,
        device: int | None,
        inode: int | None,
        link_count: int | None,
        file_attributes: int | None,
        reparse_tag: int | None,
    ) -> _FileIdentity:
        """Build one journal identity without dynamically addressing model fields."""
        parent = (parent_device, parent_inode)
        if not exists:
            return (*parent, None, None, None, None, None, None, None)
        return (
            *parent,
            sha256,
            mode,
            device,
            inode,
            link_count,
            file_attributes,
            reparse_tag,
        )


__all__: list[str] = ["FlextInfraMiseRecovery"]
