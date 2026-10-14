"""Generation-phase staging, journal preparation, and publication mixin.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenStaging,
    FlextInfraMiseArtifactsJournal as journal_io,
    FlextInfraMiseArtifactsState as state,
    FlextInfraMisePublication,
    FlextInfraMiseStaging,
)
from flext_infra.codegen._codegen_transaction_phases import (
    FlextInfraCodegenTransactionPhases,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransactionGeneration(FlextInfraCodegenTransactionPhases):
    """Stage, prepare, and publish the first conform+Mise generation phase."""

    def __init__(
        self,
        owner: p.Infra.MiseArtifactsOwner,
        *,
        participant_policy: m.Infra.CodegenParticipantPolicy | None = None,
        producer: m.Infra.CodegenPhaseAnalysis | None = None,
    ) -> None:
        """Initialize the transaction with its configured Mise artifact owner."""
        super().__init__(
            owner, participant_policy=participant_policy, producer=producer
        )
        self._owner = owner
        self._mise_staging = FlextInfraMiseStaging()

    def _materialize_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        expected: m.Cli.AtomicFileState,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Persist one journal revision, then materialize its planned directories.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        persisted = self._write_journal(layout, journal, expected=expected)
        if persisted.failure:
            return result_type.from_failure(persisted)
        materialized = self._materialize_directories(layout, journal, persisted.value)
        if materialized.failure:
            return result_type.from_failure(materialized)
        recorded, recorded_state = materialized.value
        return result_type.ok((recorded, recorded_state))

    def begin_locked(
        self,
        scope_root: Path,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        file_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Publish conform+Mise as the first fully journaled prepared phase.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if self._producer.failure:
            return result_type.from_failure(self._producer)
        by_path = {item.path: item for item in file_plans}
        if any(by_path.get(item.path) != item for item in config_plans):
            return result_type.fail(
                "generation configurations differ from the complete file plan",
            )
        sources = FlextInfraCodegenPreconditions.unique_states(
            tuple(source for item in file_plans for source in item.source_states)
        )
        if sources.failure:
            return result_type.from_failure(sources)
        bound = FlextInfraCodegenPreconditions.bind_producer_analysis(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                inputs=sources.value,
                files=file_plans,
            ),
            self._producer.value,
        )
        if bound.failure:
            return result_type.from_failure(bound)
        file_plans = bound.value.files
        by_path = {item.path: item for item in file_plans}
        config_plans = tuple(by_path[item.path] for item in config_plans)
        destinations = FlextInfraMisePublication.admit_batch(bound.value)
        if destinations.failure:
            return result_type.from_failure(destinations)
        settled = self._stage_generation_transaction(
            scope_root,
            config_plans,
            file_plans,
        )
        if settled.failure:
            return result_type.from_failure(settled)
        published = self._publish_generation_transaction(
            settled.value, file_plans, destinations.value
        )
        if published.failure:
            return result_type.from_failure(published)
        return result_type.ok(published.value)

    def _validated_generation_topology(
        self,
        scope_root: Path,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        file_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        transaction_id: str,
    ) -> p.Result[
        t.Triple[
            m.Infra.MiseToolchainWorkspaceLayout,
            t.VariadicTuple[m.Infra.CodegenJournalDirectory],
            m.Infra.MiseToolchainWorkspacePlan,
        ]
    ]:
        """Derive transaction topology, reject residue, and plan its directories.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.MiseToolchainWorkspaceLayout,
                t.VariadicTuple[m.Infra.CodegenJournalDirectory],
                m.Infra.MiseToolchainWorkspacePlan]]``.

        """
        result_type = r[
            t.Triple[
                m.Infra.MiseToolchainWorkspaceLayout,
                t.VariadicTuple[m.Infra.CodegenJournalDirectory],
                m.Infra.MiseToolchainWorkspacePlan,
            ]
        ]
        layout_result = self._planner.layout_for_config_plans(
            scope_root,
            config_plans,
            transaction_id=transaction_id,
        )
        if layout_result.failure:
            return result_type.from_failure(layout_result)
        layout = layout_result.value
        residue = state.transaction_residue(layout)
        if residue:
            return result_type.fail(
                f"generation residue has no journal authority: {residue[0]}",
            )
        transaction_directories = state.plan_transaction_directories(
            layout,
            destinations=tuple(
                item.path
                for item in file_plans
                if item.desired_content is not None
                and u.Infra.codegen_file_requires_effect(item)
            ),
        )
        if transaction_directories.failure:
            return result_type.from_failure(transaction_directories)
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return result_type.from_failure(plan)
        return result_type.ok((layout, transaction_directories.value, plan.value))

    @staticmethod
    def _generation_sources(
        file_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        plan: m.Infra.MiseToolchainWorkspacePlan,
    ) -> p.Result[t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]]]:
        """Tag conform and Mise source receipts without a workspace drift guard.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[str,
                m.Cli.AtomicFileState]]]``.

        """
        source_states = FlextInfraCodegenPreconditions.phase_sources(
            c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            file_plans,
        )
        if source_states.failure:
            return source_states
        all_sources = (
            *source_states.value,
            *(("mise", source) for source in plan.sources),
        )
        return r[t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]]].ok(all_sources)

    def _open_generation_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        all_sources: t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
        transaction_id: str,
        transaction_directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Open the generation journal on an absent baseline and materialize it.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        journal_before = state.journal_state(layout)
        if journal_before.failure:
            return result_type.from_failure(journal_before)
        journal_before_snapshot = state.journal_snapshot(journal_before.value)
        if journal_before_snapshot is None:
            return result_type.fail("generation journal state is unavailable")
        if journal_before_snapshot.content is not None:
            return result_type.fail("generation journal appeared after locked recovery")
        staging_journal = journal_io.begin(
            plan,
            transaction_id=transaction_id,
            sources=all_sources,
            directories=transaction_directories,
            producer=self._producer.value,
        )
        if staging_journal.failure:
            return result_type.from_failure(staging_journal)
        return self._materialize_journal(
            layout,
            staging_journal.value,
            expected=journal_before_snapshot,
        )

    def _register_mise_staging(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[
        t.Triple[
            m.Infra.CodegenTransactionJournal,
            m.Cli.AtomicFileState,
            t.VariadicTuple[m.Infra.CodegenStagedFile],
        ]
    ]:
        """Stage Mise artifacts and record their manifests into the journal.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState, t.VariadicTuple[
                m.Infra.CodegenStagedFile]]]``.

        """
        result_type = r[
            t.Triple[
                m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState,
                t.VariadicTuple[m.Infra.CodegenStagedFile],
            ]
        ]
        mise_staged = self._mise_staging.stage(plan)
        if mise_staged.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    mise_staged.error or "cannot stage Mise artifacts",
                ),
            )
        mise_files, mise_directories = mise_staged.value
        recorded = journal_io.record_transaction_manifests(
            layout,
            journal,
            created=(
                *mise_directories,
                *(
                    item.replacement
                    for item in mise_files
                    if item.replacement is not None
                ),
            ),
        )
        if recorded.failure:
            return result_type.from_failure(recorded)
        persisted = self._write_journal(layout, recorded.value, expected=journal_state)
        if persisted.failure:
            return result_type.from_failure(persisted)
        return result_type.ok((recorded.value, persisted.value, mise_files))

    def _stage_generation_transaction(
        self,
        scope_root: Path,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        file_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[
        tuple[
            m.Infra.MiseToolchainWorkspaceLayout,
            m.Infra.MiseToolchainWorkspacePlan,
            t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
            t.VariadicTuple[m.Infra.CodegenStagedFile],
            t.VariadicTuple[m.Infra.CodegenFilePlan],
        ]
    ]:
        """Validate topology, open the journal, and register Mise staging.

        Returns:
            The resulting staged tuple carrying the layout, plan, tagged
            sources, journal pair, staged Mise files, and the ordinary
            (non-config) conform plans.

        """
        result_type = r[
            tuple[
                m.Infra.MiseToolchainWorkspaceLayout,
                m.Infra.MiseToolchainWorkspacePlan,
                t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
                t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
                t.VariadicTuple[m.Infra.CodegenStagedFile],
                t.VariadicTuple[m.Infra.CodegenFilePlan],
            ]
        ]
        transaction_id = secrets.token_hex(16)
        topology = self._validated_generation_topology(
            scope_root,
            config_plans,
            file_plans,
            transaction_id,
        )
        if topology.failure:
            return result_type.from_failure(topology)
        layout, transaction_directories, plan = topology.value
        sources = self._generation_sources(file_plans, plan)
        if sources.failure:
            return result_type.from_failure(sources)
        opened = self._open_generation_journal(
            layout,
            plan,
            sources.value,
            transaction_id,
            transaction_directories,
        )
        if opened.failure:
            return result_type.from_failure(opened)
        registered = self._register_mise_staging(layout, plan, *opened.value)
        if registered.failure:
            return result_type.from_failure(registered)
        active_journal, active_state, mise_files = registered.value
        config_paths = {config_plan.path for config_plan in config_plans}
        ordinary = tuple(
            file_plan
            for file_plan in file_plans
            if file_plan.path not in config_paths
            and u.Infra.codegen_file_requires_effect(file_plan)
        )
        return result_type.ok((
            layout,
            plan,
            sources.value,
            (active_journal, active_state),
            mise_files,
            ordinary,
        ))

    def _validate_staged_configs(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        mise_files: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[bool]:
        """Re-validate every staged Mise configuration on its staged root.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for project in plan.projects:
            staged_config = next(
                item.replacement
                for item in mise_files
                if item.before.path == project.config.before.path
            )
            if staged_config is None:
                return r[bool].fail("Mise staging receipt has no configuration")
            # The staged set is complete and self-contained; its projection of
            # the runtime root is proven again on the published destinations.
            staged_root = staged_config.path.parent
            validated = self._owner.validate_artifacts(staged_root, staged_root)
            if validated.failure:
                return self._recover_failure(
                    layout,
                    validated.error or "Mise staged validation failed",
                )
        return r[bool].ok(value=True)

    def _bind_conform_publications(
        self,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        journal_state: t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
        ordinary: t.VariadicTuple[m.Infra.CodegenFilePlan],
        mise_publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[
        t.Pair[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
            t.VariadicTuple[m.Infra.CodegenStagedFile],
        ]
    ]:
        """Authorize ordinary staging before creating any phase artifact.

        Returns:
            The durable journal receipt and complete conform plus Mise publication set.

        """
        result_type = r[
            t.Pair[
                t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
                t.VariadicTuple[m.Infra.CodegenStagedFile],
            ]
        ]
        phase = c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP
        prepared = self.prepare_phase_staging_journal_locked(
            plan.layout,
            journal_state[0],
            journal_state[1],
            phase,
            ordinary,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        journal, _journal_state = prepared.value
        layout = plan.layout
        ordinary_staged = FlextInfraCodegenStaging.stage_file_plans(
            layout,
            phase,
            ordinary,
            directories=tuple(
                directory.created
                for directory in journal.directories
                if directory.created is not None
            ),
            intents=journal.staging_intents,
        )
        if ordinary_staged.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    ordinary_staged.error or "cannot stage conform files",
                    exception=ordinary_staged.exception,
                    error_code=ordinary_staged.error_code,
                    error_data=ordinary_staged.error_data,
                ),
            )
        bound = state.bind_created_parents(
            journal.directories,
            (*ordinary_staged.value, *mise_publications),
        )
        if bound.failure:
            return result_type.from_failure(bound)
        return result_type.ok((prepared.value, bound.value))

    def _prepare_generation_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        all_sources: t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
        journal_state: t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Durably prepare the generation journal, then re-verify the barriers.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        active_journal, active_state = journal_state
        prepared_journal = journal_io.append_prepared(
            plan,
            active_journal,
            publications,
            sources=all_sources,
        )
        if prepared_journal.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    prepared_journal.error or "cannot prepare generation journal",
                ),
            )
        manifested = journal_io.record_transaction_manifests(
            layout,
            prepared_journal.value,
        )
        if manifested.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    manifested.error or "cannot register generation staging tree",
                ),
            )
        prepared_state = self._write_journal(
            layout,
            manifested.value,
            expected=active_state,
        )
        if prepared_state.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout,
                    prepared_state.error
                    or "cannot publish prepared generation journal",
                ),
            )
        return result_type.ok((manifested.value, prepared_state.value))

    def _publish_prepared_generation(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        admission: m.Infra.CodegenPhaseOutcome,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Publish the staged set and prove publication and real-consumer liveness.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]`` with the written
            files.

        """
        published = FlextInfraMisePublication.publish(
            publications, batch_admission=admission, journal=journal
        )
        if published.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(
                self._recover_failure(
                    layout,
                    published.error or "generation publication failed",
                ),
            )
        return published

    def _publish_generation_transaction(
        self,
        settled: tuple[
            m.Infra.MiseToolchainWorkspaceLayout,
            m.Infra.MiseToolchainWorkspacePlan,
            t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState],
            t.VariadicTuple[m.Infra.CodegenStagedFile],
            t.VariadicTuple[m.Infra.CodegenFilePlan],
        ],
        all_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        admission: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Validate staged configs, prepare the journal, and publish.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        layout, plan, all_sources, journal_state, mise_files, ordinary = settled
        validated = self._validate_staged_configs(layout, plan, mise_files)
        if validated.failure:
            return result_type.from_failure(validated)
        mise_publications = tuple(
            item
            for item in mise_files
            if item.replacement is not None
            and u.Infra.atomic_file_state_differs(
                item.before,
                desired_content=item.replacement.content,
                desired_mode=item.replacement.mode,
            )
        )
        publications = self._bind_conform_publications(
            plan,
            journal_state,
            ordinary,
            mise_publications,
        )
        if publications.failure:
            return result_type.from_failure(publications)
        current, staged = publications.value
        prepared = self._prepare_generation_journal(
            layout,
            plan,
            all_sources,
            current,
            staged,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        manifested, prepared_state = prepared.value
        session = m.Infra.CodegenTransactionSession(
            plan=plan, journal=manifested, journal_state=prepared_state
        )
        bound = self.bind_publication_proof(
            session,
            all_plans,
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            batch_admission=admission,
        )
        if bound.failure:
            return result_type.from_failure(bound)
        incomplete = self.record_publication(bound.value)
        if incomplete.failure:
            return result_type.from_failure(incomplete)
        finalized = self._publish_prepared_generation(
            layout,
            staged,
            admission,
            bound.value.journal,
        )
        if finalized.failure:
            return result_type.from_failure(finalized)
        observed = bound.value.model_copy(
            update={
                "written_files": finalized.value.written_files,
                "published_files": finalized.value.published_files,
                "retained_files": finalized.value.retained_files,
                "issues": finalized.value.issues,
                "exception": finalized.value.exception,
            },
        )
        proven = self.bind_publication_proof(observed, all_plans)
        if proven.failure:
            return result_type.from_failure(proven)
        return self.record_publication(
            proven.value,
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
        )


__all__: list[str] = ["FlextInfraCodegenTransactionGeneration"]
