"""Physical topology, source, destination, and real-consumer verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournalRelocation,
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
    def publication_current(
        cls,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate a completed publication without planning or rendering."""
        root = request.root.expanduser().resolve()
        report = root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        captured = FlextInfraMiseArtifactsFiles.read_state(report, required=False)
        result = r[m.Infra.CodegenPhaseOutcome]
        if captured.failure:
            return result.from_failure(captured)
        content = captured.value.content
        if content is None:
            return result.fail(
                f"generation publication receipt is missing: {report}; run make gen",
            )
        parsed = result.create_from_callable(
            lambda: m.Infra.CodegenPhaseOutcome.model_validate_json(content),
        )
        if parsed.failure:
            return result.from_failure(parsed)
        outcome = parsed.value
        if (
            not outcome.completed
            or outcome.issues
            or outcome.pending_files
            or not (outcome.outputs or outcome.batches)
            or not outcome.scope_roots
            or outcome.root != root
            or outcome.surface != c.Infra.CodegenConformSurface(request.what)
            or outcome.scope != c.Infra.CodegenConformScope(request.scope)
            or outcome.module != request.module
        ):
            return result.fail(
                f"generation publication does not cover this request: {report}; "
                "run make gen",
            )
        current = cls._publication_states_current(outcome)
        if current.failure:
            return result.from_failure(current)
        unchanged = cls.states_current((captured.value,))
        if unchanged.failure:
            return result.from_failure(unchanged)
        return result.ok(outcome)

    @classmethod
    def _publication_states_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Verify native file and ancestry witnesses of every completed batch."""
        from flext_infra.codegen.codegen_preconditions import (
            FlextInfraCodegenPreconditions,
        )

        if not outcome.completed or outcome.issues or outcome.pending_files:
            return r[bool].fail("generation batch is incomplete; run make gen")
        if not outcome.batches:
            if (
                not outcome.generator_sources
                or not outcome.generator_trees
                or any(source.role is None for source in outcome.generator_sources)
            ):
                return r[bool].fail(
                    "generation batch lacks pre-planning producer closure; run make gen"
                )
            producer = FlextInfraCodegenPreconditions.producer_trees_current(
                outcome.generator_trees, outcome.outputs
            )
            if producer.failure:
                return producer
        if outcome.phase == c.Infra.CodegenStagedFilePhase.DOCS:
            membership = u.Infra.docs_source_paths_for_roots(
                outcome.scope_roots,
                source_scope=outcome.source_scope,
            )
            if membership.failure:
                return r[bool].from_failure(membership)
            expected_paths = {
                source.path for source in outcome.sources if source.sha256 is not None
            }
            if set(membership.value) != expected_paths:
                return r[bool].fail(
                    "generation source membership changed; run make gen",
                )
        for witness in outcome.source_topology:
            observed = u.Cli.atomic_plan_directory_chain(witness.target)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != witness:
                return r[bool].fail(
                    f"generation source topology changed: {witness.target}; "
                    "run make gen",
                )
        for expected in (
            *outcome.sources,
            *outcome.outputs,
            *outcome.generator_sources,
        ):
            if expected.absent_parent is not None:
                ancestry = u.Cli.atomic_plan_directory_chain(expected.path.parent)
                if ancestry.failure:
                    return r[bool].from_failure(ancestry)
                if ancestry.value != expected.absent_parent:
                    return r[bool].fail(
                        f"generation source ancestry changed: {expected.path}; "
                        "run make gen",
                    )
            observed = FlextInfraMiseArtifactsFiles.read_state(
                expected.path,
                required=expected.sha256 is not None,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            recorded = FlextInfraMiseArtifactsJournalRelocation.source_record(
                expected.phase,
                observed.value,
                previous=expected,
            )
            if recorded.failure:
                return r[bool].from_failure(recorded)
            if recorded.value != expected:
                return r[bool].fail(
                    f"generation publication state changed: {expected.path}; "
                    "run make gen",
                )
        for batch in outcome.batches:
            verified = cls._publication_states_current(batch)
            if verified.failure:
                return verified
        return r[bool].ok(value=True)

    @classmethod
    def plans_current(
        cls,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[bool]:
        """Authenticate original destinations and only journal-owned parent gains."""
        for plan in plans:
            if not isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
                current = cls.states_current((plan.before,), journal=journal)
                if current.failure:
                    return current
                continue
            witness = plan.before
            observed = u.Cli.atomic_plan_directory_chain(witness.target)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value == witness:
                continue
            if journal is None:
                return r[bool].fail(
                    f"generation destination parent changed: {plan.path}",
                )
            ancestry = cls._verified_parent_ancestry(journal, witness)
            if ancestry.failure:
                return r[bool].from_failure(ancestry)
            if (
                observed.value.directories
                or observed.value.anchor_path != witness.target
                or observed.value.anchor_ancestry != ancestry.value
            ):
                return r[bool].fail(
                    f"generation destination parent identity changed: {plan.path}",
                )
            absent = FlextInfraMiseArtifactsFiles.read_state(plan.path, required=False)
            if absent.failure:
                return r[bool].from_failure(absent)
            if absent.value.content is not None:
                return r[bool].fail(
                    f"generation destination appeared after planning: {plan.path}",
                )
        return r[bool].ok(value=True)

    @classmethod
    def states_current(
        cls,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[bool]:
        """Prove every full file state still equals its authenticated snapshot.

        Compare content, mode, and physical identity within the caller's scope.
        Parent identities may change only through the supplied native journal's
        exact directory-creation receipts. Each destination still has its own
        guarded write; this check does not claim multi-file OS atomicity.

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
    def phase_analysis_live(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[bool]:
        """Prove one published phase from its authenticated analysis receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        u.Cli.info(
            f"phase={analysis.phase} verify destinations={len(analysis.files)}",
        )
        for plan in analysis.files:
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
                continue
            if (
                current.content,
                current.mode,
            ) != (
                plan.desired_content,
                plan.desired_mode,
            ):
                return r[bool].fail(
                    f"published {analysis.phase} destination differs from receipt: "
                    f"{plan.path}",
                )
        return r[bool].ok(value=True)

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
