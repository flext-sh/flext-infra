"""Journal-declared package-view materialization mixin for dependent phases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsProcess,
    FlextInfraMiseArtifactsState,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransactionPhasesPackageViewMixin:
    """Materialize a descriptor-authenticated package view inside the journal."""

    if TYPE_CHECKING:

        def _write_journal(
            self,
            layout: m.Infra.MiseToolchainWorkspaceLayout,
            journal: m.Infra.CodegenTransactionJournal,
            *,
            expected: m.Cli.AtomicFileState,
        ) -> p.Result[m.Cli.AtomicFileState]: ...

        def _persist_directories(
            self,
            session: m.Infra.CodegenTransactionSession,
            phase: str,
            planned: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
        ) -> p.Result[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]: ...

        def _persist_staging_intents(
            self,
            session: m.Infra.CodegenTransactionSession,
            phase: str,
            writes: t.VariadicTuple[tuple[Path, bytes, int]],
        ) -> p.Result[m.Infra.CodegenTransactionSession]: ...

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


__all__: list[str] = ["FlextInfraCodegenTransactionPhasesPackageViewMixin"]
