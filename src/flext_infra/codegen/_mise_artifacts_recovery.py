"""Retire authenticated generation staging without undoing published files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, r, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles as files,
    FlextInfraMiseArtifactsJournal as journal_io,
    FlextInfraMiseArtifactsState as state,
    FlextInfraMiseArtifactsVerification as verify,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseRecovery:
    """Preserve every live destination while retiring owned staging."""

    @staticmethod
    def execute(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Clean authenticated staging without restoring any destination.

        Returns:
            The cleanup outcome, preserving its original failure.
        """
        topology = verify.journal_topology(layout, journal)
        if topology.failure:
            return topology
        authorized = state.validate_transaction_roots(layout, journal)
        if authorized.failure:
            return authorized
        if journal.state == "prepared":
            grouped = tuple(
                entry for entry in journal.entries if entry.dependency_group is not None
            )
            selected = {
                entry.dependency_group for entry in grouped if entry.recover_group
            }
            recovering = tuple(
                entry
                for entry in grouped
                if not selected or entry.dependency_group in selected
            )
            if recovering:
                journal = journal.model_copy(
                    update={
                        "entries": tuple(
                            entry.model_copy(update={"recover_group": True})
                            if entry in recovering
                            else entry
                            for entry in journal.entries
                        ),
                    }
                )
                persisted = journal_io.write(layout, journal, expected=journal_state)
                if persisted.failure:
                    return r[bool].from_failure(persisted)
                journal_state = persisted.value
                recovered = FlextInfraMiseRecovery.restore_groups(layout, journal)
                if recovered.failure:
                    return recovered
        return journal_io.cleanup(layout, journal, journal_state)

    @staticmethod
    def restore_groups(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[bool]:
        """Consume only preimages selected by the durable group recovery decision."""
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
        """Compensate only an admitted effect or its exact staged inode identity."""
        path = files.resolve_transaction(
            layout, entry.path, purpose="dependent-group recovery"
        )
        if path.failure:
            return r[bool].from_failure(path)
        observed = files.read_state(path.value, required=False)
        if observed.failure:
            return r[bool].from_failure(observed)
        current = observed.value
        identity = (
            current.parent_device,
            current.parent_inode,
            files.digest(current.content) if current.content is not None else None,
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
        if identity == original:
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
            if current.content is None:
                return r[bool].ok(value=False)
            if identity != desired:
                return (
                    r[bool].fail(f"admitted group destination changed: {path.value}")
                    if entry.group_admitted
                    else r[bool].ok(value=False)
                )
            return files.delete_state(current)
        if entry.original_staging is None or entry.original_content_hex is None:
            return r[bool].fail(f"group preimage missing: {entry.path}")
        backup_path = files.resolve_transaction(
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
        if intent is None or intent.created is None:
            return r[bool].fail(f"group preimage has no physical receipt: {entry.path}")
        receipt = intent.created
        if (
            current.device,
            current.inode,
            current.mode,
            files.digest(current.content) if current.content is not None else None,
        ) == (receipt.device, receipt.inode, receipt.mode, receipt.sha256):
            return r[bool].ok(value=False)
        if identity != desired:
            return (
                r[bool].fail(f"admitted group destination changed: {path.value}")
                if entry.group_admitted
                else r[bool].ok(value=False)
            )
        if not entry.desired_exists and not entry.group_admitted:
            return r[bool].fail(f"group deletion has no admitted receipt: {entry.path}")
        backup = files.read_state(backup_path.value, required=True)
        if backup.failure:
            return r[bool].from_failure(backup)
        preimage = backup.value
        if (
            (
                preimage.parent_device,
                preimage.parent_inode,
                preimage.device,
                preimage.inode,
                preimage.mode,
                files.digest(preimage.content)
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
            return r[bool].fail(f"group preimage identity changed: {entry.path}")
        return u.Cli.atomic_publish_staged_binary_file_guarded(current, preimage).map(
            lambda _: True
        )


__all__: list[str] = ["FlextInfraMiseRecovery"]
