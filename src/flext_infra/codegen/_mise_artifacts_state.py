"""Persistent coordination-state lifecycle for Mise transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import stat
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsComparison,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsVerificationManifest,
    FlextInfraMiseArtifactsVerificationTopology,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsState:
    """Journaled directory state for Mise artifact transactions."""

    @classmethod
    def unchanged_journal(
        cls,
        session: m.Infra.CodegenTransactionSession,
        changed_error: str,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Authenticate the full session receipt through the journal state owner.

        Returns:
            The session only when its complete native journal snapshot is current.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        observed = cls.journal_state(session.plan.layout)
        if observed.failure:
            return result_type.from_failure(observed)
        if cls.journal_snapshot(observed.value) != session.journal_state:
            return result_type.fail(
                changed_error,
                error_data={
                    "cleanup_error": "journal authority mismatch vs session receipt"
                },
            )
        return result_type.ok(session)

    @classmethod
    def _hosting_device(cls, path: Path) -> int:
        """Return the filesystem device that will host ``path``.

        The check below proves every destination shares one device with the
        project root, because the transaction publishes by rename and a rename
        cannot cross filesystems. A destination directory need not exist yet --
        a freshly scaffolded project has no ``external/bin`` until this
        transaction creates it -- and `lstat` on the absent directory raised
        `FileNotFoundError`, failing generation for every new project. What will
        host it is its nearest existing ancestor, which is what the rename
        actually has to satisfy.

        Returns:
            The filesystem device that will host ``path``.

        Raises:
            FileNotFoundError: If no existing ancestor hosts the destination.

        """
        for candidate in (path, *path.parents):
            if candidate.exists():
                return candidate.lstat().st_dev
        msg = f"no existing ancestor hosts the destination: {path}"
        raise FileNotFoundError(msg)

    @classmethod
    def _project_depth(
        cls,
        item: m.Infra.MiseToolchainProjectLayout | m.Infra.CodegenFileParticipant,
    ) -> int:
        """Order the narrowest project owner before its ancestors.

        Returns:
            The resulting ``int``.

        """
        return -len(item.root.parts)

    @classmethod
    def _directory_cleanup_order(
        cls,
        item: m.Infra.CodegenJournalDirectory,
    ) -> t.Pair[int, str]:
        """Order journaled directory cleanup from descendants to ancestors.

        Returns:
            The resulting ``t.Pair[int, str]``.

        """
        return cls._relative_order(item.path)

    @classmethod
    def plan_transaction_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        *,
        destinations: t.VariadicTuple[Path] = (),
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalDirectory]]:
        """Prove every transaction path absent before journal publication.

        Returns:
            The resulting
                ``p.Result[t.VariadicTuple[m.Infra.CodegenJournalDirectory]]``.

        """
        roots: list[Path] = []
        for project in layout.projects:
            transaction_root = project.transaction_root
            if transaction_root is None:
                return r[tuple[m.Infra.CodegenJournalDirectory, ...]].fail(
                    "Mise mutating layout has no transaction root",
                )
            try:
                destination_devices = {cls._hosting_device(project.config.parent)}
                project_device = cls._hosting_device(project.root)
            except OSError as exc:
                return r[tuple[m.Infra.CodegenJournalDirectory, ...]].fail_op(
                    "inspect Mise staging filesystem",
                    exc,
                )
            if destination_devices != {project_device}:
                return r[tuple[m.Infra.CodegenJournalDirectory, ...]].fail(
                    f"Mise state is not on destination filesystem: {project.selector}",
                )
            roots.append(transaction_root)
        roots.extend(
            participant.transaction_root for participant in layout.file_participants
        )
        temporary = cls.plan_directories(
            layout,
            phase=c.Infra.CodegenStagedFilePhase.TRANSACTION,
            requested=tuple(roots),
            disposition="temporary",
        )
        if temporary.failure:
            return temporary
        parents = tuple(
            dict.fromkeys(
                project.config.parent
                for project in layout.projects
                if project.config.parent != project.root
            ),
        )
        project_roots = {
            item.root
            for item in FlextInfraMiseArtifactsFiles.transaction_participants(layout)
        }
        parents = tuple(
            dict.fromkeys((
                *parents,
                *(
                    path.parent
                    for path in destinations
                    if path.parent not in project_roots
                ),
            )),
        )
        generated = cls.plan_directories(
            layout,
            phase=c.Infra.CodegenStagedFilePhase.MISE,
            requested=parents,
            disposition="generated",
        )
        if generated.failure:
            return generated
        return r[tuple[m.Infra.CodegenJournalDirectory, ...]].ok((
            *temporary.value,
            *generated.value,
        ))

    @classmethod
    def bind_created_parents(
        cls,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
        """Bind absent destinations only to parents created by this journal.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]``.

        """
        result_type = r[tuple[m.Infra.CodegenStagedFile, ...]]
        bound: list[m.Infra.CodegenStagedFile] = []
        for publication in publications:
            before = publication.before
            parent = next(
                (
                    entry.created
                    for entry in directories
                    if entry.created is not None
                    and entry.created.path == before.path.parent
                    and entry.disposition == "generated"
                ),
                None,
            )
            if before.parent_device is not None and before.parent_inode is not None:
                if parent is not None and (
                    before.parent_device,
                    before.parent_inode,
                ) != (parent.device, parent.inode):
                    return result_type.fail(
                        (
                            f"generation destination parent differs "
                            f"from journal: {before.path}"
                        ),
                    )
                bound.append(publication)
                continue
            if (
                before.content is not None
                or parent is None
                or parent.device is None
                or parent.inode is None
            ):
                return result_type.fail(
                    (
                        f"generation destination has no created "
                        f"parent authority: {before.path}"
                    ),
                )
            expected = m.Cli.AtomicFileState.model_validate({
                **before.model_dump(),
                "parent_device": parent.device,
                "parent_inode": parent.inode,
            })
            observed = FlextInfraMiseArtifactsFiles.read_state(
                before.path, required=False
            )
            if observed.failure:
                return result_type.from_failure(observed)
            if observed.value != expected:
                return result_type.fail(
                    (
                        f"generation destination changed "
                        f"after parent creation: {before.path}"
                    ),
                )
            bound.append(
                m.Infra.CodegenStagedFile.model_validate({
                    **publication.model_dump(),
                    "before": expected,
                }),
            )
        return result_type.ok(tuple(bound))

    @classmethod
    def plan_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        *,
        phase: str,
        requested: t.VariadicTuple[Path],
        disposition: Literal["temporary", "generated"],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalDirectory]]:
        """Return unique missing paths after descriptor-authenticated preflight.

        Returns:
            Unique missing paths after descriptor-authenticated preflight.

        """
        result_type = r[tuple[m.Infra.CodegenJournalDirectory, ...]]
        if len(set(requested)) != len(requested):
            return result_type.fail(f"duplicate {phase} directory request")
        projects = tuple(
            sorted(
                FlextInfraMiseArtifactsFiles.transaction_participants(layout),
                key=cls._project_depth,
            ),
        )
        planned: MutableMapping[Path, m.Infra.CodegenJournalDirectory] = {}
        for target in requested:
            path = target.expanduser().absolute()
            project = next(
                (item for item in projects if path.is_relative_to(item.root)),
                None,
            )
            if project is None or path == project.root:
                return result_type.fail(
                    f"{phase} directory escapes its project: {path}",
                )
            chain = u.Cli.atomic_plan_directory_chain(path)
            if chain.failure:
                return result_type.from_failure(chain)
            planned_chain = cls._planned_chain_directories(
                layout,
                planned,
                phase,
                disposition,
                chain.value,
            )
            if planned_chain.failure:
                return result_type.from_failure(planned_chain)
        ordered = tuple(planned[path] for path in sorted(planned, key=cls._path_order))
        return result_type.ok(ordered)

    @classmethod
    def _planned_chain_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        planned: MutableMapping[Path, m.Infra.CodegenJournalDirectory],
        phase: str,
        disposition: Literal["temporary", "generated"],
        chain: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[bool]:
        """Plan every directory of one chain into the shared planned map.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        projects = tuple(
            sorted(
                FlextInfraMiseArtifactsFiles.transaction_participants(layout),
                key=cls._project_depth,
            ),
        )
        for directory in chain.directories:
            owner = next(
                (item for item in projects if directory.is_relative_to(item.root)),
                None,
            )
            if owner is None or directory == owner.root:
                return result_type.fail(
                    f"{phase} directory has no project owner: {directory}",
                )
            relative = FlextInfraMiseArtifactsFiles.transaction_relative(
                layout, directory
            )
            if relative.failure:
                return result_type.from_failure(relative)
            before = cls._anchor_witness(directory, chain)
            if before.failure:
                return result_type.from_failure(before)
            before_value, before_present = before.value
            entry = m.Infra.CodegenJournalDirectory(
                phase=c.Infra.CodegenStagedFilePhase(phase),
                project=owner.selector,
                path=relative.value,
                disposition=disposition,
                before=(
                    before_value
                    if before_present and before_value is not None
                    else None
                ),
            )
            previous = planned.get(directory)
            if previous is not None and (
                previous.phase,
                previous.project,
                previous.disposition,
            ) != (entry.phase, entry.project, entry.disposition):
                return result_type.fail(
                    f"generation directory has conflicting owners: {directory}",
                )
            fresher = previous is None or (previous.before is None and before_present)
            if fresher:
                planned[directory] = entry
        return result_type.ok(value=True)

    @staticmethod
    def _anchor_witness(
        directory: Path,
        chain: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[t.Pair[m.Cli.AtomicDirectoryState | None, bool]]:
        """Observe the anchor-bound parent state when a directory sits on it.

        Returns:
            The resulting ``p.Result[t.Pair[m.Cli.AtomicDirectoryState |
            None, bool]]`` where the boolean marks witness presence.

        """
        result_type = r[t.Pair[m.Cli.AtomicDirectoryState | None, bool]]
        if directory.parent != chain.anchor_path:
            return result_type.ok((None, False))
        observed = u.Cli.atomic_read_empty_directory_state(directory, required=False)
        if observed.failure:
            return result_type.from_failure(observed)
        if observed.value.exists or (
            observed.value.parent_device,
            observed.value.parent_inode,
        ) != (chain.anchor_device, chain.anchor_inode):
            return result_type.fail(
                f"{directory} anchor changed during planning",
            )
        return result_type.ok((observed.value, True))

    @classmethod
    def create_journaled_directory(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
        entry: m.Infra.CodegenJournalDirectory,
    ) -> p.Result[m.Infra.CodegenJournalDirectory]:
        """Create one durable intent and return its exact physical identity.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenJournalDirectory]``.

        """
        result_type = r[m.Infra.CodegenJournalDirectory]
        if entry.created is not None or entry not in directories:
            return result_type.fail(f"invalid directory creation cursor: {entry.path}")
        target = FlextInfraMiseArtifactsFiles.resolve_transaction(
            layout,
            entry.path,
            purpose="journaled generation directory",
        )
        if target.failure:
            return result_type.from_failure(target)
        project = next(
            (
                item
                for item in FlextInfraMiseArtifactsFiles.transaction_participants(
                    layout
                )
                if item.selector == entry.project
            ),
            None,
        )
        if project is None or not target.value.is_relative_to(project.root):
            return result_type.fail(
                f"journaled directory differs from its project: {entry.path}",
            )
        before = cls._creation_before_state(
            directories,
            entry,
            target.value,
        )
        if before.failure:
            return result_type.from_failure(before)
        created = u.Cli.atomic_create_empty_directory_guarded(
            before.value,
            permission_mode=0o700 if entry.disposition == "temporary" else 0o755,
        )
        if created.failure:
            return result_type.from_failure(created)
        return cls._validated_created_entry(entry, before.value, created.value)

    @classmethod
    def _creation_before_state(
        cls,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
        entry: m.Infra.CodegenJournalDirectory,
        target: Path,
    ) -> p.Result[m.Cli.AtomicDirectoryState]:
        """Derive the exact pre-creation state a directory must be created in.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicDirectoryState]``.

        """
        result_type = r[m.Cli.AtomicDirectoryState]
        before = entry.before
        if before is not None:
            if before.path != target:
                return result_type.fail(
                    f"journaled absent state belongs to another path: {entry.path}",
                )
            return result_type.ok(before)
        parent_entry = next(
            (
                candidate
                for candidate in directories
                if candidate.created is not None
                and candidate.created.path == target.parent
            ),
            None,
        )
        if (
            parent_entry is None
            or parent_entry.created is None
            or parent_entry.created.device is None
            or parent_entry.created.inode is None
        ):
            return result_type.fail(
                f"journaled directory parent has no durable identity: {entry.path}",
            )
        observed = u.Cli.atomic_read_empty_directory_state(target, required=False)
        if observed.failure:
            return result_type.from_failure(observed)
        if observed.value.exists or (
            observed.value.parent_device,
            observed.value.parent_inode,
        ) != (
            parent_entry.created.device,
            parent_entry.created.inode,
        ):
            return result_type.fail(
                f"journaled directory parent changed before creation: {entry.path}",
            )
        return result_type.ok(observed.value)

    @staticmethod
    def _validated_created_entry(
        entry: m.Infra.CodegenJournalDirectory,
        before: m.Cli.AtomicDirectoryState,
        created: m.Cli.AtomicDirectoryState,
    ) -> p.Result[m.Infra.CodegenJournalDirectory]:
        """Validate the created identity, compensating the effect on failure.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenJournalDirectory]``.

        """
        result_type = r[m.Infra.CodegenJournalDirectory]
        validated: p.Result[m.Infra.CodegenJournalDirectory] = u.validate_value(
            m.Infra.CodegenJournalDirectory,
            {**entry.model_dump(), "before": before, "created": created},
        )
        if not validated.failure:
            return validated
        rolled_back = u.Cli.atomic_delete_empty_directory_guarded(created)
        if rolled_back.failure:
            return result_type.fail(
                f"validate created directory identity failed: {validated.error}; "
                f"compensation failed: {rolled_back.error}",
            )
        return result_type.fail_op(
            "validate created directory identity",
            validated.error,
        )

    @classmethod
    def compensate_created_directory(
        cls,
        entry: m.Infra.CodegenJournalDirectory,
    ) -> p.Result[bool]:
        """Remove only the exact empty directory returned by this invocation.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if entry.created is None:
            return r[bool].fail(f"directory has no created identity: {entry.path}")
        return u.Cli.atomic_delete_empty_directory_guarded(entry.created)

    @classmethod
    def journal_state(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read the typed Git-owned journal without creating filesystem state.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]``.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        snapshot = FlextInfraMiseArtifactsFiles.read_state(
            layout.journal_path, required=False
        )
        if snapshot.failure:
            return result_type.from_failure(snapshot)
        return result_type.ok((snapshot.value,))

    @classmethod
    def journal_snapshot(
        cls,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> m.Cli.AtomicFileState | None:
        """Return the optional journal snapshot from its non-null result payload.

        Returns:
            The optional journal snapshot from its non-null result payload.

        """
        return states[0] if states else None

    @classmethod
    def transaction_residue(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> t.VariadicTuple[Path]:
        """Return every transaction-prefixed child or unsafe state-root alias.

        An unreadable state root is a read failure, never classified as
        residue; the read error escapes.

        Returns:
            Every transaction-prefixed child or unsafe state-root alias.

        """
        residue: list[Path] = []
        for project in FlextInfraMiseArtifactsFiles.transaction_participants(layout):
            state_root = project.root / c.Infra.MISE_ARTIFACTS_STATE_DIRECTORY
            if not state_root.exists() and not state_root.is_symlink():
                continue
            if state_root.is_symlink():
                residue.append(state_root)
                continue
            root_state = state_root.lstat()
            if not stat.S_ISDIR(root_state.st_mode) or cls._is_reparse(root_state):
                residue.append(state_root)
                continue
            children = tuple(state_root.iterdir())
            residue.extend(
                child
                for child in children
                if child.name.startswith(c.Infra.TRANSACTION_DIR_PREFIX)
            )
        return tuple(sorted(set(residue)))

    @classmethod
    def cleanup_journaled_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        include_generated: bool,
    ) -> p.Result[bool]:
        """Remove authenticated temporary trees and authorized empty directories.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        bound = FlextInfraMiseArtifactsVerificationTopology.journal_retirement_topology(
            layout, journal
        )
        if bound.failure:
            return bound
        validated = cls.validate_transaction_roots(layout, journal)
        if validated.failure:
            return validated
        removed_roots = cls._removed_transaction_roots(layout, journal)
        if removed_roots.failure:
            return r[bool].from_failure(removed_roots)
        return cls._removed_removable_directories(
            layout,
            journal,
            include_generated=include_generated,
            removed_temporary_roots=removed_roots.value,
        )

    @classmethod
    def _removed_transaction_roots(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[frozenset[str]]:
        """Delete every project's journaled transaction root.

        Returns:
            The resulting ``p.Result[frozenset[str]]`` with the removed
            journal paths.

        """
        result_type = r[frozenset[str]]
        removed_temporary_roots: set[str] = set()
        for project in FlextInfraMiseArtifactsFiles.transaction_participants(layout):
            transaction_root = project.transaction_root
            if transaction_root is None:
                return result_type.fail("Mise recovery layout has no transaction root")
            if not transaction_root.exists() and not transaction_root.is_symlink():
                continue
            relative = FlextInfraMiseArtifactsFiles.transaction_relative(
                layout, transaction_root
            )
            if relative.failure:
                return result_type.from_failure(relative)
            entry = next(
                (item for item in journal.directories if item.path == relative.value),
                None,
            )
            if entry is None or entry.created is None:
                return result_type.fail(
                    (
                        f"transaction root has no durable "
                        f"physical identity: {relative.value}"
                    ),
                )
            if entry.manifest is None:
                # A created directory receipt owns only that empty directory,
                # never descendants discovered after an interrupted stage.
                if cls._hosts_lease_lock(layout, transaction_root):
                    removed_temporary_roots.add(entry.path)
                    continue
                removed = cls._retirement_directory_input(entry.created).flat_map(
                    u.Cli.atomic_delete_empty_directory_guarded
                )
            else:
                manifest_owner = FlextInfraMiseArtifactsVerificationManifest
                observed = manifest_owner.authorized_cleanup_manifest(
                    layout, journal, entry
                )
                if observed.failure:
                    return result_type.from_failure(observed)
                removed = u.Cli.atomic_cleanup_physical_tree_guarded(observed.value)
            if removed.failure:
                return result_type.from_failure(removed)
            removed_temporary_roots.add(entry.path)
        return result_type.ok(frozenset(removed_temporary_roots))

    @classmethod
    def _removed_removable_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        include_generated: bool,
        removed_temporary_roots: frozenset[str],
    ) -> p.Result[bool]:
        """Delete remaining empty journaled directories, deepest first.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        removable = tuple(
            directory
            for directory in journal.directories
            if (
                directory.path not in removed_temporary_roots
                and (directory.disposition == "temporary" or include_generated)
            )
        )
        for entry in sorted(removable, key=cls._directory_cleanup_order, reverse=True):
            target = FlextInfraMiseArtifactsFiles.resolve_transaction(
                layout,
                entry.path,
                purpose="journaled cleanup directory",
            )
            if target.failure:
                return r[bool].from_failure(target)
            if not target.value.exists() and not target.value.is_symlink():
                continue
            if entry.created is None:
                return r[bool].fail(
                    (
                        f"journaled directory exists "
                        f"without durable identity: {entry.path}"
                    ),
                )
            if cls._hosts_lease_lock(layout, target.value):
                # The journal lease lock file persists by identity across
                # transactions, so its home directory is durable state the
                # cleanup must leave in place rather than delete empty.
                continue
            removed = cls._retirement_directory_input(entry.created).flat_map(
                u.Cli.atomic_delete_empty_directory_guarded
            )
            if removed.failure:
                journaled = {j.path for j in journal.entries}
                preserved = set(removed_temporary_roots) | {
                    d.path for d in removable if d.path != entry.path
                }
                preserved_residents = cls._authenticated_residents(
                    layout,
                    target.value,
                    journaled=journaled,
                    preserved=preserved,
                )
                if preserved_residents.failure:
                    return r[bool].from_failure(preserved_residents)
                if preserved_residents.value:
                    continue
                return r[bool].from_failure(removed)
        return r[bool].ok(value=True)

    @classmethod
    def _authenticated_residents(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        target: Path,
        *,
        journaled: set[str],
        preserved: set[str],
    ) -> p.Result[bool]:
        """Prove every resident of an undeletable directory is journal-owned.

        A journaled generated directory may keep journaled residents whose
        recovery classified noop (unrecognized state the generation owns and
        rewrites). Only residents the journal itself authenticated preserve
        the directory; anything else inside is foreign state and the cleanup
        still fails closed.

        Returns:
            The resulting ``p.Result[bool]``: True when the directory keeps
            authenticated residents.

        """
        residents = tuple(target.iterdir()) if target.is_dir() else ()
        if not residents:
            return r[bool].ok(value=False)
        for resident in residents:
            selector = FlextInfraMiseArtifactsFiles.transaction_relative(
                layout, resident
            )
            if selector.failure:
                return r[bool].from_failure(selector)
            relative = selector.value
            if relative in journaled or relative in preserved:
                continue
            # An ancestor is preservable when everything between it and a
            # preserved descendant is itself journaled: the descendant's own
            # guard already authenticated its subtree.
            prefix = relative + "/"
            if not any(candidate.startswith(prefix) for candidate in preserved):
                return r[bool].ok(value=False)
        return r[bool].ok(value=True)

    @staticmethod
    def _hosts_lease_lock(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directory: Path,
    ) -> bool:
        """Keep journal and participant lease identities across transactions.

        Returns:
            The resulting ``bool``.

        """
        lease_paths = (
            layout.journal_path,
            *(
                participant.root
                / c.Infra.TRANSACTION_STATE_DIRNAME
                / c.Infra.JOURNAL_NAME
                for participant in layout.file_participants
            ),
        )
        return any(
            lease.with_name(f"{lease.name}.lock").is_relative_to(directory)
            for lease in lease_paths
        )

    @classmethod
    def reconcile_pending_directories(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[bool]:
        """Remove only current empty inputs of interrupted temporary intentions.

        Original creation receipts and manifests remain unchanged. Every root
        passes its original proof before any captured empty input is removed.

        Returns:
            The original manifests' currency after guarded empty-only cleanup.

        """
        for intent in journal.staging_intents:
            observed = FlextInfraMiseArtifactsFiles.read_state(
                intent.before.path, required=False
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            current = observed.value
            if (current.link_count or 0) > 1:
                digest = (
                    FlextInfraMiseArtifactsFiles.digest(current.content)
                    if current.content is not None
                    else None
                )
                u.Cli.emit_raw(
                    f"{c.Cli.OUTPUT_LOG_LEVEL_INFO}: recovery=staging-intention "
                    f"path={current.path} device={current.device} "
                    f"inode={current.inode} links={current.link_count} "
                    f"mode={current.mode} intended-mode={intent.mode} "
                    f"sha256={digest} "
                    f"intended-sha256={intent.sha256}\n",
                    error=True,
                )
        inputs: list[m.Cli.AtomicDirectoryState] = []
        for intent in (
            directory
            for directory in journal.directories
            if directory.disposition == "temporary" and directory.created is None
        ):
            captured = cls._pending_directory_input(layout, journal, intent)
            if captured.failure:
                return r[bool].from_failure(captured)
            inputs.append(captured.value)
        inputs = [current for current in inputs if current.exists]
        if not inputs:
            return cls.validate_transaction_roots(layout, journal)
        proven = cls.validate_transaction_roots(
            layout, journal, reconciliation_inputs=tuple(inputs)
        )
        if proven.failure:
            return proven
        for current in inputs:
            removed = u.Cli.atomic_delete_empty_directory_guarded(current)
            if removed.failure:
                return removed
        return cls.validate_transaction_roots(layout, journal)

    @staticmethod
    def _pending_directory_input(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        intent: m.Infra.CodegenJournalDirectory,
    ) -> p.Result[m.Cli.AtomicDirectoryState]:
        """Capture one empty reconciliation input under its original parent proof.

        Returns:
            Current input identity, absence, or the first refusal.

        """
        target = FlextInfraMiseArtifactsFiles.resolve_transaction(
            layout, intent.path, purpose="pending temporary directory"
        ).unwrap()
        captured = u.Cli.atomic_read_empty_directory_state(target, required=False)
        if captured.failure:
            return captured
        current = captured.value
        if not current.exists:
            return captured
        return FlextInfraMiseArtifactsVerificationManifest.reconciliation_input_current(
            layout, journal, intent, current
        ).map(lambda _: current)

    @classmethod
    def validate_transaction_roots(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        reconciliation_inputs: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[bool]:
        """Authenticate the sole journal-derived staging root in every project.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected = {
            project.transaction_root
            for project in FlextInfraMiseArtifactsFiles.transaction_participants(layout)
            if project.transaction_root is not None
        }
        unexpected = sorted(set(cls.transaction_residue(layout)) - expected)
        if unexpected:
            return r[bool].fail(
                f"foreign generation transaction residue exists: {unexpected[0]}",
            )
        for project in FlextInfraMiseArtifactsFiles.transaction_participants(layout):
            authenticated = cls._validated_project_transaction_root(
                layout,
                journal,
                project,
                reconciliation_inputs=reconciliation_inputs,
            )
            if authenticated.failure:
                return authenticated
        # The receipt authenticates publication destinations independently of
        # staging cleanup. Guarded deletion refuses foreign or unmanifested
        # residents and retains their bytes and journal for owner correction.
        # Recovery preserves files already published.
        return r[bool].ok(value=True)

    @classmethod
    def _validated_project_transaction_root(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        project: (m.Infra.MiseToolchainProjectLayout | m.Infra.CodegenFileParticipant),
        *,
        reconciliation_inputs: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[bool]:
        """Authenticate one project's staging root against its journal receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        transaction_root = project.transaction_root
        if transaction_root is None:
            return r[bool].fail("Mise recovery layout has no transaction root")
        transaction = cls._validate_transaction_root(transaction_root)
        if transaction.failure:
            return r[bool].from_failure(transaction)
        if transaction.value is False:
            return r[bool].ok(value=True)
        relative = FlextInfraMiseArtifactsFiles.transaction_relative(
            layout, transaction_root
        )
        if relative.failure:
            return r[bool].from_failure(relative)
        recorded = next(
            (item for item in journal.directories if item.path == relative.value),
            None,
        )
        if recorded is None or recorded.created is None:
            reason = "missing entry" if recorded is None else "created absent"
            return r[bool].fail(
                f"Mise transaction root identity is not journaled: {relative.value}; "
                f"journal_path={layout.journal_path}; reason={reason}; "
                f"observed_device_inode={transaction.value}",
            )
        return cls._validated_root_evidence(
            layout,
            journal,
            recorded,
            reconciliation_inputs=reconciliation_inputs,
        )

    @classmethod
    def _validated_root_evidence(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        recorded: m.Infra.CodegenJournalDirectory,
        *,
        reconciliation_inputs: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[bool]:
        """Prove an unmanifested root is intact or authorize its manifest.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if recorded.manifest is not None:
            authorized = (
                FlextInfraMiseArtifactsVerificationManifest.authorized_cleanup_manifest(
                    layout,
                    journal,
                    recorded,
                    reconciliation_inputs=reconciliation_inputs,
                )
            )
            if authorized.failure:
                return r[bool].from_failure(authorized)
            return r[bool].ok(value=True)
        if recorded.created is None:
            return r[bool].fail(
                f"temporary tree has no original created receipt: {recorded.path}",
            )
        empty = cls._retirement_directory_input(recorded.created)
        if empty.failure:
            return r[bool].from_failure(empty)
        return r[bool].ok(value=True)

    @staticmethod
    def _retirement_directory_input(
        expected: m.Cli.AtomicDirectoryState,
    ) -> p.Result[m.Cli.AtomicDirectoryState]:
        """Authorize a declared empty directory and retain its fresh native state.

        Returns:
            The current receipt for exact native removal, never a rewritten record.

        """
        observed = u.Cli.atomic_read_empty_directory_state(expected.path, required=True)
        if observed.failure:
            return observed
        if not FlextInfraMiseArtifactsComparison.same_retirement_directory(
            observed.value, expected
        ):
            return r[m.Cli.AtomicDirectoryState].fail(
                f"journaled empty directory metadata changed: {expected.path}",
            )
        return observed

    @classmethod
    def _validate_transaction_root(
        cls,
        target: Path,
    ) -> p.Result[t.Pair[int, int] | bool]:
        if not target.exists() and not target.is_symlink():
            return r[tuple[int, int] | bool].ok(value=False)
        identifier = target.name.removeprefix(c.Infra.TRANSACTION_DIR_PREFIX)
        if (
            not target.name.startswith(c.Infra.TRANSACTION_DIR_PREFIX)
            or len(identifier) != c.Infra.TRANSACTION_ID_LENGTH
            or any(character not in "0123456789abcdef" for character in identifier)
            or target.is_symlink()
        ):
            return r[tuple[int, int] | bool].fail(
                f"refusing invalid Mise transaction target: {target}",
            )
        try:
            state = target.lstat()
        except OSError as exc:
            return r[tuple[int, int] | bool].fail_op(
                "inspect Mise transaction target",
                exc,
            )
        if not stat.S_ISDIR(state.st_mode) or cls._is_reparse(state):
            return r[tuple[int, int] | bool].fail(
                f"Mise transaction target is not physical: {target}",
            )
        return r[tuple[int, int] | bool].ok((state.st_dev, state.st_ino))

    @classmethod
    def _path_order(cls, path: Path) -> t.Pair[int, str]:
        return len(path.parts), path.as_posix()

    @classmethod
    def _relative_order(cls, path: str) -> t.Pair[int, str]:
        relative = Path(path)
        return len(relative.parts), path

    @classmethod
    def _is_reparse(cls, state: os.stat_result) -> bool:
        attributes = getattr(state, "st_file_attributes", 0)
        marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        return bool(attributes & marker)


__all__: list[str] = ["FlextInfraMiseArtifactsState"]
