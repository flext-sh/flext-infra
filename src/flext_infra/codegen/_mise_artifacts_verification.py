"""Physical topology, source, destination, and real-consumer verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsVerificationManifest,
    FlextInfraMiseArtifactsVerificationTopology,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsVerification(
    FlextInfraMiseArtifactsVerificationManifest,
    FlextInfraMiseArtifactsVerificationTopology,
):
    """Manifest, topology, and liveness verification for Mise transactions."""

    @classmethod
    def states_current(
        cls,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[bool]:
        """Prove every full file state still equals its authenticated snapshot.

        This barrier is what makes the transaction atomic: it proves nothing
        moved between planning and publication. It compares the FULL state --
        content, mode and physical identity -- because a snapshot whose inode or
        device changed underneath the transaction is exactly the race the
        barrier exists to catch.

        It must never be softened to make a run pass. It briefly was: content
        was compared whitespace-normalised, mode drift was downgraded to a
        warning "logged but does not block the pipeline", and a literal
        `_models/config.py` was skipped as "expected to drift". That file
        carries no generation marker -- it is authored source and is not
        expected to drift at all; the drift being masked was the truncation
        churn of that same afternoon. A verifier that cannot fail is not a
        verifier, and a hardcoded path exemption in a fleet-wide generator hides
        the next real corruption just as effectively as it hid that one.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for original_expected in states:
            expected = original_expected
            if expected.parent_device is None and journal is not None:
                rebound = cls._bind_source_parent(expected, journal)
                if rebound.failure:
                    return r[bool].from_failure(rebound)
                rebound_expected = rebound.value
            else:
                rebound_expected = expected
            observed = FlextInfraMiseArtifactsFiles.read_state(
                rebound_expected.path,
                required=rebound_expected.content is not None,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != rebound_expected:
                content_changed = observed.value.content != rebound_expected.content
                return r[bool].fail(
                    f"generation authenticated state changed: {rebound_expected.path}; "
                    f"content_changed={content_changed}; "
                    "expected="
                    f"{rebound_expected.model_dump_json(exclude={'content'})}; "
                    f"observed={observed.value.model_dump_json(exclude={'content'})}",
                )
        return r[bool].ok(value=True)

    @classmethod
    def _bind_source_parent(
        cls,
        expected: m.Cli.AtomicFileState,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Recognize only parent identities created under the durable absence witness.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        result = r[m.Cli.AtomicFileState]
        source = next(
            (item for item in journal.sources if item.path == expected.path),
            None,
        )
        if (
            source is None
            or source.absent_parent is None
            or expected.content is not None
        ):
            return result.fail(
                f"generation source has no absence witness: {expected.path}",
            )
        witness = source.absent_parent
        current = u.Cli.atomic_plan_directory_chain(witness.target)
        if current.failure:
            return result.from_failure(current)
        if current.value == witness:
            return result.ok(expected)
        ancestry = cls._verified_parent_ancestry(journal, witness)
        if ancestry.failure:
            return result.from_failure(ancestry)
        observed = current.value
        if observed.directories or observed.anchor_ancestry != ancestry.value:
            return result.fail(
                f"generation source parent identity changed: {expected.path}",
            )
        return result.ok(
            expected.model_copy(
                update={
                    "parent_device": ancestry.value[-1][0],
                    "parent_inode": ancestry.value[-1][1],
                },
            ),
        )

    @classmethod
    def _verified_parent_ancestry(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
        witness: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[t.VariadicTuple[t.Pair[int, int]]]:
        """Rebuild the parent ancestry chain from journal-created directories.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[int, int]]]``.

        """
        result_type = r[t.VariadicTuple[t.Pair[int, int]]]
        created = {
            item.created.path: item.created
            for item in journal.directories
            if item.created is not None and item.disposition == "generated"
        }
        ancestry = list(witness.anchor_ancestry)
        for path in witness.directories:
            identity = created.get(path)
            if identity is None or identity.device is None or identity.inode is None:
                return result_type.fail(
                    f"generation source parent was not created by this journal: {path}",
                )
            if (identity.parent_device, identity.parent_inode) != ancestry[-1]:
                return result_type.fail(
                    (
                        f"generation source parent ancestry "
                        f"differs from its journal: {path}"
                    ),
                )
            ancestry.append((identity.device, identity.inode))
        return result_type.ok(tuple(ancestry))

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
        destination_paths = frozenset(file.path for file in analysis.files)
        u.Cli.info(
            f"phase={analysis.phase} verify inputs={len(analysis.inputs)} "
            f"destinations={len(analysis.files)}",
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
        for source in analysis.inputs:
            if source.path in destination_paths:
                continue
            entry = entries.get(source.path)
            if entry is None or session is None:
                checked = cls.states_current((source,))
            else:
                if not cls._historical_state_recorded(source, session, entry):
                    return r[bool].fail(
                        f"published phase input has no historical journal proof: {source.path}",
                    )
                continue
            if checked.failure:
                return checked
        for plan in analysis.files:
            entry = entries.get(plan.path)
            if session is not None and entry is not None:
                if entry.phase != analysis.phase:
                    if (
                        u.Infra.codegen_file_requires_effect(plan)
                        or not isinstance(plan.before, m.Cli.AtomicFileState)
                        or not cls._historical_state_recorded(
                            plan.before, session, entry,
                        )
                    ):
                        return r[bool].fail(
                            f"published phase destination has no owned journal receipt: {plan.path}",
                        )
                    continue
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
                if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
                    parent = cls.materialized_directory_chain(
                        session.journal, plan.before,
                    )
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
                continue
            if session is not None and u.Infra.codegen_file_requires_effect(plan):
                return r[bool].fail(
                    f"published phase destination has no owned journal receipt: {plan.path}",
                )
            before = u.Infra.codegen_file_before_state(plan)
            if before.failure:
                return r[bool].from_failure(before)
            if session is not None:
                unchanged = cls.states_current((before.value,))
                if unchanged.failure:
                    return unchanged
            observed = FlextInfraMiseArtifactsFiles.read_state(
                plan.path,
                required=plan.desired_content is not None,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            current = observed.value
            if (
                current.content,
                current.mode,
                current.parent_device,
                current.parent_inode,
            ) != (
                plan.desired_content,
                plan.desired_mode,
                before.value.parent_device,
                before.value.parent_inode,
            ):
                return r[bool].fail(
                    f"published {analysis.phase} destination differs from receipt: "
                    f"{plan.path}",
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
            ) == historical
            for recorded in session.journal.sources
        ) or historical in (
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
        )

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
    def sources(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        published: t.VariadicTuple[m.Infra.CodegenStagedFile] = (),
    ) -> p.Result[bool]:
        """Prove every Mise config source equals its expected full snapshot.

        Before publication the expectation is the plan-time snapshot. After
        it, every config source this transaction published itself replaces or
        joins that snapshot with its staged identity (``publications_live``
        already proved that identity live); any other change is foreign.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for project in plan.projects:
            current = u.Infra.snapshot_config_sources(project.layout.root)
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != cls._expected_sources(project, published):
                return r[bool].fail(f"Mise sources changed: {project.layout.selector}")
        return r[bool].ok(value=True)

    @staticmethod
    def _expected_sources(
        project: m.Infra.MiseToolchainProjectState,
        published: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> t.VariadicTuple[m.Cli.AtomicFileState]:
        """Return the plan-time sources with this transaction's own config writes.

        Returns:
            The expected sources, ordered by path like the snapshot.

        """
        own = {
            item.before.path: item
            for item in published
            if u.Infra.direct_config_source(project.layout.root, item.before.path)
        }
        kept = (item for item in project.config.sources if item.path not in own)
        landed = (
            item.replacement.model_copy(
                update={
                    "path": item.before.path,
                    "parent_device": item.before.parent_device,
                    "parent_inode": item.before.parent_inode,
                },
            )
            for item in own.values()
            if item.replacement is not None
        )
        return tuple(sorted((*kept, *landed), key=lambda item: item.path))

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
