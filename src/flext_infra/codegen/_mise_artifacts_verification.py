"""Physical topology, source, destination, and real-consumer verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen._mise_artifacts_files import FlextInfraMiseArtifactsFiles
from flext_infra.codegen._mise_artifacts_verification_manifest import (
    FlextInfraMiseArtifactsVerificationManifest,
)
from flext_infra.codegen._mise_artifacts_verification_receipts import (
    FlextInfraMiseArtifactsVerificationReceipts,
)
from flext_infra.codegen._mise_artifacts_verification_topology import (
    FlextInfraMiseArtifactsVerificationTopology,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsVerification(
    FlextInfraMiseArtifactsVerificationReceipts,
    FlextInfraMiseArtifactsVerificationManifest,
    FlextInfraMiseArtifactsVerificationTopology,
):
    """Manifest, topology, and liveness verification for Mise transactions."""

    @classmethod
    def plans_current(
        cls,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[bool]:
        """Authenticate original destinations and only journal-owned parent gains.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for plan in plans:
            current = cls._plan_current(plan, journal)
            if current.failure:
                return current
        return r[bool].ok(value=True)

    @classmethod
    def _plan_current(
        cls,
        plan: m.Infra.CodegenFilePlan,
        journal: m.Infra.CodegenTransactionJournal | None,
    ) -> p.Result[bool]:
        """Authenticate one plan's existing destination or its planned absence.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        witness = plan.before
        if not isinstance(witness, m.Cli.AtomicDirectoryChainPlan):
            return cls.states_current((witness,), journal=journal)
        observed = u.Cli.atomic_plan_directory_chain(witness.target)
        if observed.failure:
            return r[bool].from_failure(observed)
        if observed.value == witness:
            return r[bool].ok(value=True)
        identity = cls._journal_parent_identity_current(
            plan,
            journal,
            witness,
            observed.value,
        )
        if identity.failure:
            return identity
        return cls._destination_still_absent(plan)

    @classmethod
    def _journal_parent_identity_current(
        cls,
        plan: m.Infra.CodegenFilePlan,
        journal: m.Infra.CodegenTransactionJournal | None,
        witness: m.Cli.AtomicDirectoryChainPlan,
        observed: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[bool]:
        """Prove the observed parent gain is owned by this journal's receipts.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if journal is None:
            return r[bool].fail(
                f"generation destination parent changed: {plan.path}",
            )
        ancestry = cls._verified_parent_ancestry(journal, witness)
        if ancestry.failure:
            return r[bool].from_failure(ancestry)
        if (
            observed.directories
            or observed.anchor_path != witness.target
            or observed.anchor_ancestry != ancestry.value
        ):
            return r[bool].fail(
                f"generation destination parent identity changed: {plan.path}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _destination_still_absent(plan: m.Infra.CodegenFilePlan) -> p.Result[bool]:
        """Prove a planned-absence destination has not appeared since planning.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        absent = FlextInfraMiseArtifactsFiles.read_state(plan.path, required=False)
        if absent.failure:
            return r[bool].from_failure(absent)
        if absent.value.content is not None:
            return r[bool].fail(
                f"generation destination appeared after planning: {plan.path}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def materialized_directory_chain(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
        witness: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[bool]:
        """Prove the declared parent chain was materialized by this journal.

        Returns:
            The first identity failure or the authenticated physical ancestry.

        """
        current = u.Cli.atomic_plan_directory_chain(witness.target)
        if current.failure:
            return r[bool].from_failure(current)
        ancestry = cls._verified_parent_ancestry(journal, witness)
        if ancestry.failure:
            return r[bool].from_failure(ancestry)
        if current.value.directories or current.value.anchor_ancestry != ancestry.value:
            return r[bool].fail(
                f"generation destination parent identity changed: {witness.target}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def phase_analysis_live(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        session: m.Infra.CodegenTransactionSession | None = None,
    ) -> p.Result[bool]:
        """Prove one published phase from its authenticated analysis receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        u.Cli.info(
            f"phase={analysis.phase} verify destinations={len(analysis.files)}",
        )
        if session is not None:
            owned = cls.journal_destinations_live(
                session.plan.layout,
                session.journal,
            )
            if owned.failure:
                return owned
        entries = (
            {
                FlextInfraMiseArtifactsFiles.resolve_transaction(
                    session.plan.layout,
                    entry.path,
                    purpose="phase receipt destination",
                ).unwrap(): entry
                for entry in session.journal.entries
            }
            if session is not None
            else {}
        )
        inputs = cls._phase_inputs_live(analysis, session, entries)
        if inputs.failure:
            return inputs
        for plan in analysis.files:
            entry = entries.get(plan.path)
            checked = (
                cls._journal_phase_destination(analysis.phase, plan, session, entry)
                if session is not None and entry is not None
                else cls._unjournaled_phase_destination(analysis.phase, plan, session)
            )
            if checked.failure:
                return checked
        return r[bool].ok(value=True)

    @classmethod
    def _phase_inputs_live(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        session: m.Infra.CodegenTransactionSession | None,
        entries: t.MappingKV[Path, m.Infra.CodegenJournalEntry],
    ) -> p.Result[bool]:
        """Prove non-destination inputs against live bytes or owned history.

        Returns:
            The first input failure in original analysis order.

        """
        destination_paths = frozenset(file.path for file in analysis.files)
        for source in analysis.inputs:
            if source.path in destination_paths:
                continue
            entry = entries.get(source.path)
            if entry is None or session is None:
                checked = cls.states_current((source,))
            else:
                if not cls._historical_state_recorded(source, session, entry):
                    return r[bool].fail(
                        "published phase input has no historical journal proof: "
                        f"{source.path}",
                    )
                continue
            if checked.failure:
                return checked
        return r[bool].ok(value=True)

    @classmethod
    def _journal_phase_destination(
        cls,
        phase: c.Infra.CodegenStagedFilePhase,
        plan: m.Infra.CodegenFilePlan,
        session: m.Infra.CodegenTransactionSession,
        entry: m.Infra.CodegenJournalEntry,
    ) -> p.Result[bool]:
        """Bind a phase's destination intent to this session's owned receipt.

        Returns:
            The matching intent and original-state proof.

        """
        if entry.phase != phase:
            if (
                u.Infra.codegen_file_requires_effect(plan)
                or not isinstance(plan.before, m.Cli.AtomicFileState)
                or not cls._historical_state_recorded(plan.before, session, entry)
            ):
                return r[bool].fail(
                    "published phase destination has no owned journal receipt: "
                    f"{plan.path}",
                )
            return r[bool].ok(value=True)
        desired_digest = (
            FlextInfraMiseArtifactsFiles.digest(plan.desired_content)
            if plan.desired_content is not None
            else None
        )
        if (entry.desired_sha256, entry.desired_mode) != (
            desired_digest,
            plan.desired_mode,
        ):
            return r[bool].fail(
                f"published phase destination intent differs from journal: {plan.path}",
            )
        return cls._journal_original_destination(plan, session, entry)

    @classmethod
    def _journal_original_destination(
        cls,
        plan: m.Infra.CodegenFilePlan,
        session: m.Infra.CodegenTransactionSession,
        entry: m.Infra.CodegenJournalEntry,
    ) -> p.Result[bool]:
        """Prove the journal's original identity or materialized absence chain.

        Returns:
            The original-state proof without rereading an overwritten preimage.

        """
        if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
            parent = cls.materialized_directory_chain(session.journal, plan.before)
            if parent.failure:
                return parent
            if entry.original_exists:
                return r[bool].fail(
                    f"published absent destination had an original file: {plan.path}",
                )
        elif cls._state_receipt_identity(plan.before) != (
            entry.original_parent_device,
            entry.original_parent_inode,
            entry.original_sha256,
            entry.original_mode,
            entry.original_device,
            entry.original_inode,
            entry.original_link_count,
            entry.original_file_attributes,
            entry.original_reparse_tag,
        ):
            return r[bool].fail(
                f"published destination original differs from plan: {plan.path}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _unjournaled_phase_destination(
        cls,
        phase: c.Infra.CodegenStagedFilePhase,
        plan: m.Infra.CodegenFilePlan,
        session: m.Infra.CodegenTransactionSession | None,
    ) -> p.Result[bool]:
        """Require a physical no-effect receipt when no journal entry owns a file.

        Returns:
            The unchanged preimage and current publication proof.

        """
        if session is not None and u.Infra.codegen_file_requires_effect(plan):
            return r[bool].fail(
                "published phase destination has no owned journal receipt: "
                f"{plan.path}",
            )
        before = u.Infra.codegen_file_before_state(plan)
        if before.failure:
            return r[bool].from_failure(before)
        if session is not None:
            unchanged = cls.states_current((before.value,))
            if unchanged.failure:
                return unchanged
        return cls._published_destination_bytes(phase, plan)

    @staticmethod
    def _published_destination_bytes(
        phase: c.Infra.CodegenStagedFilePhase,
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[bool]:
        """Read the destination and apply the existing authored-retention policy.

        Returns:
            The physical publication verdict with its original first cause.

        """
        observed = FlextInfraMiseArtifactsFiles.read_state(
            plan.path,
            required=plan.desired_content is not None,
        )
        if observed.failure:
            return r[bool].from_failure(observed)
        current = observed.value
        if (
            plan.path.name == c.Infra.INIT_PY
            and u.Infra.codegen_initializer_is_authored(current.content)
        ):
            u.Cli.info(
                f"ownership=authored disposition=retained target={plan.path}",
            )
            return r[bool].ok(value=True)
        if (current.content, current.mode) != (
            plan.desired_content,
            plan.desired_mode,
        ):
            return r[bool].fail(
                f"published {phase} destination differs from receipt: {plan.path}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _historical_state_recorded(
        cls,
        state: m.Cli.AtomicFileState,
        session: m.Infra.CodegenTransactionSession,
        entry: m.Infra.CodegenJournalEntry,
    ) -> bool:
        """Match an input only to historical or publisher-produced journal identity.

        Returns:
            Whether the complete input identity is owned by the durable journal.

        """
        historical = cls._state_receipt_identity(state)
        return any(
            recorded.path == state.path
            and (
                recorded.parent_device,
                recorded.parent_inode,
                recorded.sha256,
                recorded.mode,
                recorded.device,
                recorded.inode,
                recorded.link_count,
                recorded.file_attributes,
                recorded.reparse_tag,
            )
            == historical
            for recorded in session.journal.sources
        ) or historical in {
            (
                entry.original_parent_device,
                entry.original_parent_inode,
                entry.original_sha256,
                entry.original_mode,
                entry.original_device,
                entry.original_inode,
                entry.original_link_count,
                entry.original_file_attributes,
                entry.original_reparse_tag,
            ),
            (
                entry.desired_parent_device,
                entry.desired_parent_inode,
                entry.desired_sha256,
                entry.desired_mode,
                entry.desired_device,
                entry.desired_inode,
                entry.desired_link_count,
                entry.desired_file_attributes,
                entry.desired_reparse_tag,
            ),
        }

    @staticmethod
    def _state_receipt_identity(
        state: m.Cli.AtomicFileState,
    ) -> tuple[int | str | None, ...]:
        """Match all recorded physical and byte fields without observing live data.

        Returns:
            The exact identity represented by a durable journal file receipt.

        """
        return (
            state.parent_device,
            state.parent_inode,
            FlextInfraMiseArtifactsFiles.digest(state.content)
            if state.content is not None
            else None,
            state.mode,
            state.device,
            state.inode,
            state.link_count,
            state.file_attributes,
            state.reparse_tag,
        )

    @classmethod
    def destinations(cls, plan: m.Infra.MiseToolchainWorkspacePlan) -> p.Result[bool]:
        """Prove all Mise destinations still equal the captured preflight snapshot.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for project in plan.projects:
            current = cls.states_current((project.config.before,))
            if current.failure:
                return current
        return r[bool].ok(value=True)

    @classmethod
    def publications_live(
        cls,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[bool]:
        """Prove live destinations have the exact staged inode or planned absence.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for publication in publications:
            observed = FlextInfraMiseArtifactsFiles.read_state(
                publication.before.path,
                required=False,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            current = observed.value
            before = publication.before
            if (
                current.parent_device is None
                or current.parent_inode is None
                or before.parent_device is None
                or before.parent_inode is None
            ):
                return r[bool].fail(
                    (
                        f"generation destination parent "
                        f"identity is incomplete: {before.path}"
                    ),
                )
            replacement = publication.replacement
            if replacement is None:
                if (
                    observed.value.content is not None
                    or observed.value.parent_device != publication.before.parent_device
                    or observed.value.parent_inode != publication.before.parent_inode
                ):
                    return r[bool].fail(
                        "deleted generation destination or its parent changed: "
                        f"{publication.before.path}",
                    )
                continue
            if cls._file_identity(
                current,
                parent_device=current.parent_device,
                parent_inode=current.parent_inode,
            ) != cls._file_identity(
                replacement,
                parent_device=before.parent_device,
                parent_inode=before.parent_inode,
            ):
                return r[bool].fail(
                    (
                        f"live generation destination differs "
                        f"from staged identity: {current.path}"
                    ),
                )
        return r[bool].ok(value=True)

    @classmethod
    def live(
        cls,
        owner: p.Infra.MiseArtifactsOwner,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile] | None = None,
        *,
        published: t.VariadicTuple[m.Infra.CodegenStagedFile] = (),
    ) -> p.Result[bool]:
        """Exercise every real Mise consumer while guarding sources and live bytes.

        ``publications`` are the staged Mise artifacts the consumers read;
        ``published`` is everything this transaction published, whose config
        sources the source guard expects.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        source_before = cls.sources(plan, published)
        if source_before.failure:
            return source_before
        staged = cls._staged_replacements(publications or ())
        if staged.failure:
            return r[bool].from_failure(staged)
        stable = cls._stable_artifact_snapshot(plan, staged.value, owner)
        if stable.failure:
            return r[bool].from_failure(stable)
        source_after = cls.sources(plan, published)
        if source_after.failure:
            return source_after
        return r[bool].ok(value=True)

    @staticmethod
    def _staged_replacements(
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.MappingKV[Path, t.Pair[bytes, int | None]]]:
        """Collect every staged Mise replacement keyed by its live path.

        Returns:
            The resulting ``p.Result[t.MappingKV[Path, t.Pair[bytes,
                int | None]]]``.

        """
        result_type = r[t.MappingKV[Path, t.Pair[bytes, int | None]]]
        replacements: MutableMapping[Path, t.Pair[bytes, int | None]] = {}
        for publication in publications:
            replacement = publication.replacement
            if replacement is None or replacement.content is None:
                return result_type.fail(
                    f"Mise replacement is absent: {publication.before.path}",
                )
            replacements[publication.before.path] = (
                replacement.content,
                replacement.mode,
            )
        return result_type.ok(replacements)

    @classmethod
    def _stable_artifact_snapshot(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        replacements: t.MappingKV[Path, t.Pair[bytes, int | None]],
        owner: p.Infra.MiseArtifactsOwner,
    ) -> p.Result[bool]:
        """Exercise real consumers and prove the rendered artifacts unchanged.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        artifact_before = cls._artifact_snapshot(plan, replacements)
        if artifact_before.failure:
            return r[bool].from_failure(artifact_before)
        for project in plan.projects:
            validated = owner.validate_artifacts(
                project.layout.root,
                plan.layout.scope_root,
            )
            if validated.failure:
                return r[bool].from_failure(validated)
        artifact_after = cls._artifact_snapshot(plan, replacements)
        if artifact_after.failure:
            return r[bool].from_failure(artifact_after)
        if artifact_after.value != artifact_before.value:
            return r[bool].fail("published Mise artifacts changed during validation")
        return r[bool].ok(value=True)

    @classmethod
    def _artifact_snapshot(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        replacements: t.MappingKV[Path, t.Pair[bytes, int | None]],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        states: list[m.Cli.AtomicFileState] = []
        for project in plan.projects:
            artifacts = (project.config.before,)
            for expected, required_mode in zip(
                artifacts,
                (project.config.replacement_mode,),
                strict=True,
            ):
                current = FlextInfraMiseArtifactsFiles.read_state(
                    expected.path,
                    required=False,
                )
                if current.failure:
                    return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(current)
                if current.value.content is None:
                    return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                        f"published Mise artifact is absent: {expected.path}; "
                        "run make gen",
                    )
                if current.value.mode is None:
                    return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                        f"published Mise artifact mode is unreadable: {expected.path}",
                    )
                expected_state = replacements.get(
                    expected.path,
                    (expected.content, expected.mode),
                )
                if (current.value.content, current.value.mode) != expected_state:
                    return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                        f"published Mise artifact differs from plan: {expected.path}",
                    )
                if current.value.mode != required_mode:
                    return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                        "published Mise artifact mode is noncanonical:"
                        f" {expected.path}"
                        f" (observed {oct(current.value.mode)},"
                        f" canonical {oct(required_mode)})",
                    )
                states.append(current.value)
        return r[tuple[m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @classmethod
    def _file_identity(
        cls,
        value: m.Cli.AtomicFileState,
        *,
        parent_device: int,
        parent_inode: int,
    ) -> tuple[
        int,
        int,
        bytes | None,
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
    ]:
        """Return every physical and byte field except the intentionally moved path.

        Returns:
            Every physical and byte field except the intentionally moved path.

        """
        return (
            parent_device,
            parent_inode,
            value.content,
            value.mode,
            value.device,
            value.inode,
            value.link_count,
            value.file_attributes,
            value.reparse_tag,
        )


__all__: list[str] = ["FlextInfraMiseArtifactsVerification"]
