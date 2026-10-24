"""Recover failed journaled dependency groups and retain independent effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseRecovery:
    """Recover failed dependent groups while preserving independent published gains."""

    @staticmethod
    def execute(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Retire interrupted proposals or compensate explicitly rejected groups.

        Unselected prepared proposals preserve current destinations as new cleanup
        inputs. Retirement neither approves the interrupted group nor authorizes its
        pending publications.

        Returns:
            The cleanup outcome, preserving its original failure.

        """
        topology_verifier = (
            FlextInfraMiseArtifactsVerification.journal_topology
            if any(entry.recover_group for entry in journal.entries)
            else FlextInfraMiseArtifactsVerification.journal_retirement_topology
        )
        topology = topology_verifier(layout, journal)
        if topology.failure:
            return topology
        current = FlextInfraMiseArtifactsVerification.states_current((journal_state,))
        if current.failure:
            return current
        preserved: t.VariadicTuple[m.Cli.AtomicFileState] = ()
        if journal.state == "prepared" and not any(
            entry.recover_group for entry in journal.entries
        ):
            observed = FlextInfraMiseRecovery.retirement_inputs(layout, journal)
            if observed.failure:
                return r[bool].from_failure(observed)
            preserved = observed.value
        retained = FlextInfraMiseArtifactsVerification.states_current((
            *preserved,
            journal_state,
        ))
        if retained.failure:
            return retained
        authorized = FlextInfraMiseArtifactsState.reconcile_pending_directories(
            layout, journal
        )
        if authorized.failure:
            return authorized
        settled = FlextInfraMiseRecovery._recover_selected_groups(
            layout, journal, journal_state
        )
        return settled.flat_map(
            lambda current: FlextInfraMiseArtifactsJournal.cleanup(
                layout, *current, preserved_states=preserved
            )
        )

    @staticmethod
    def _recover_selected_groups(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Preserve the durable compensation decision for explicitly failed groups.

        Returns:
            The settled journal and its exact current receipt.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        selected = {
            entry.dependency_group for entry in journal.entries if entry.recover_group
        }
        if journal.state != "prepared" or not selected:
            return result_type.ok((journal, journal_state))
        journal = journal.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(update={"recover_group": True})
                    if entry.dependency_group in selected
                    else entry
                    for entry in journal.entries
                ),
            }
        )
        persisted = FlextInfraMiseArtifactsJournal.write(
            layout, journal, expected=journal_state
        )
        if persisted.failure:
            return result_type.from_failure(persisted)
        return FlextInfraMiseRecovery.restore_groups(layout, journal).map(
            lambda _: (journal, persisted.value)
        )

    @staticmethod
    def retirement_inputs(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Capture current physical destinations before retiring a proposal.

        These are current cleanup inputs, never publication or completion receipts.
        Earlier authored changes are preserved; every captured state is revalidated
        before cleanup and before the journal is retired.

        Returns:
            The complete observed destination states, or the first unsafe input.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileState]]
        captured: list[m.Cli.AtomicFileState] = []
        for entry in journal.entries:
            path = FlextInfraMiseArtifactsFiles.resolve_transaction(
                layout, entry.path, purpose="interrupted proposal retirement"
            )
            if path.failure:
                return result_type.from_failure(path)
            observed = FlextInfraMiseArtifactsFiles.read_state(
                path.value, required=False
            )
            if observed.failure:
                return result_type.from_failure(observed)
            captured.append(observed.value)
        return result_type.ok(tuple(captured))

    @staticmethod
    def restore_groups(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[bool]:
        """Consume only preimages selected by the durable group recovery decision.

        Returns:
            Whether every selected effect was safely recovered.

        """
        for entry in reversed(journal.entries):
            if entry.dependency_group is None or not entry.recover_group:
                continue
            recovered = FlextInfraMiseRecovery._recover_group_entry(
                layout, journal, entry
            )
            if recovered.failure:
                return recovered
        return r[bool].ok(value=True)

    @staticmethod
    def _recover_group_entry(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        entry: m.Infra.CodegenJournalEntry,
    ) -> p.Result[bool]:
        """Compensate only an admitted effect or its exact staged inode identity.

        Returns:
            Whether this authenticated destination required compensation.

        """
        path = FlextInfraMiseArtifactsFiles.resolve_transaction(
            layout, entry.path, purpose="dependent-group recovery"
        )
        if path.failure:
            return r[bool].from_failure(path)
        observed = FlextInfraMiseArtifactsFiles.read_state(path.value, required=False)
        if observed.failure:
            return r[bool].from_failure(observed)
        current = observed.value
        identity = (
            current.parent_device,
            current.parent_inode,
            FlextInfraMiseArtifactsFiles.digest(current.content)
            if current.content is not None
            else None,
            current.mode,
            current.device,
            current.inode,
            current.link_count,
            current.file_attributes,
            current.reparse_tag,
        )
        original = (
            entry.original_parent_device,
            entry.original_parent_inode,
            entry.original_sha256,
            entry.original_mode,
            entry.original_device,
            entry.original_inode,
            entry.original_link_count,
            entry.original_file_attributes,
            entry.original_reparse_tag,
        )
        if identity == original or (
            not entry.original_exists and current.content is None
        ):
            return r[bool].ok(value=False)
        desired = (
            entry.desired_parent_device,
            entry.desired_parent_inode,
            entry.desired_sha256,
            entry.desired_mode,
            entry.desired_device,
            entry.desired_inode,
            entry.desired_link_count,
            entry.desired_file_attributes,
            entry.desired_reparse_tag,
        )
        if not entry.original_exists:
            if identity != desired:
                return (
                    r[bool].fail(f"admitted group destination changed: {path.value}")
                    if entry.group_admitted
                    else r[bool].ok(value=False)
                )
            return FlextInfraMiseArtifactsFiles.delete_state(current)
        return FlextInfraMiseRecovery._restore_original(
            layout,
            journal,
            entry,
            current,
            matches_desired=identity == desired,
        )

    @staticmethod
    def _restore_original(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        entry: m.Infra.CodegenJournalEntry,
        current: m.Cli.AtomicFileState,
        *,
        matches_desired: bool,
    ) -> p.Result[bool]:
        """Bind compensation to its persisted preimage and target receipt.

        Returns:
            Whether the journal-owned preimage was consumed.

        """
        if entry.original_staging is None or entry.original_content_hex is None:
            return r[bool].fail(f"group preimage missing: {entry.path}")
        backup_path = FlextInfraMiseArtifactsFiles.resolve_transaction(
            layout, entry.original_staging, purpose="group preimage"
        )
        if backup_path.failure:
            return r[bool].from_failure(backup_path)
        intent = next(
            (
                item
                for item in journal.staging_intents
                if item.before.path == backup_path.value
            ),
            None,
        )
        if (
            intent is None
            or intent.created is None
            or intent.created.sha256 != entry.original_sha256
        ):
            return r[bool].fail(f"group preimage has no physical receipt: {entry.path}")
        receipt = intent.created
        if (
            current.parent_device,
            current.parent_inode,
            current.device,
            current.inode,
            current.mode,
            FlextInfraMiseArtifactsFiles.digest(current.content)
            if current.content is not None
            else None,
            current.link_count,
            current.file_attributes,
            current.reparse_tag,
        ) == (
            entry.original_parent_device,
            entry.original_parent_inode,
            receipt.device,
            receipt.inode,
            receipt.mode,
            receipt.sha256,
            receipt.link_count,
            receipt.file_attributes,
            receipt.reparse_tag,
        ):
            return r[bool].ok(value=False)
        if not matches_desired or (
            not entry.desired_exists and not entry.group_admitted
        ):
            return (
                r[bool].fail(
                    "admitted group destination changed or lacks deletion "
                    f"receipt: {entry.path}"
                )
                if entry.group_admitted or matches_desired
                else r[bool].ok(value=False)
            )
        return FlextInfraMiseRecovery._authenticated_preimage(
            backup_path.value,
            entry,
            receipt,
        ).flat_map(
            lambda preimage: u.Cli.atomic_publish_staged_binary_file_guarded(
                current, preimage
            ).map(lambda _: True)
        )

    @staticmethod
    def _authenticated_preimage(
        path: Path,
        entry: m.Infra.CodegenJournalEntry,
        receipt: m.Cli.AtomicPhysicalTreeEntry,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Read the exact preimage authorized by the journal's staging intention.

        Returns:
            The authenticated physical preimage snapshot.

        """
        backup = FlextInfraMiseArtifactsFiles.read_state(path, required=True)
        if backup.failure:
            return r[m.Cli.AtomicFileState].from_failure(backup)
        preimage = backup.value
        if entry.original_content_hex is None:
            return r[m.Cli.AtomicFileState].fail(
                f"group preimage bytes missing: {entry.path}"
            )
        if (
            (
                preimage.parent_device,
                preimage.parent_inode,
                preimage.device,
                preimage.inode,
                preimage.mode,
                FlextInfraMiseArtifactsFiles.digest(preimage.content)
                if preimage.content is not None
                else None,
                preimage.link_count,
                preimage.file_attributes,
                preimage.reparse_tag,
            )
            != (
                receipt.parent_device,
                receipt.parent_inode,
                receipt.device,
                receipt.inode,
                receipt.mode,
                receipt.sha256,
                receipt.link_count,
                receipt.file_attributes,
                receipt.reparse_tag,
            )
            or preimage.content != bytes.fromhex(entry.original_content_hex)
            or receipt.sha256 != entry.original_sha256
        ):
            return r[m.Cli.AtomicFileState].fail(
                f"group preimage identity changed: {entry.path}"
            )
        return r[m.Cli.AtomicFileState].ok(preimage)


__all__: list[str] = ["FlextInfraMiseRecovery"]
