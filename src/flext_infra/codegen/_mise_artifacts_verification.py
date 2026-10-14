"""Physical topology, source, destination, and real-consumer verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen._mise_artifacts_comparison import (
    FlextInfraMiseArtifactsComparison,
)
from flext_infra.codegen._mise_artifacts_files import FlextInfraMiseArtifactsFiles
from flext_infra.codegen._mise_artifacts_journal_relocation import (
    FlextInfraMiseArtifactsJournalRelocation,
)
from flext_infra.codegen._mise_artifacts_verification_manifest import (
    FlextInfraMiseArtifactsVerificationManifest,
)
from flext_infra.codegen._mise_artifacts_verification_topology import (
    FlextInfraMiseArtifactsVerificationTopology,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsVerification(
    FlextInfraMiseArtifactsComparison,
    FlextInfraMiseArtifactsVerificationManifest,
    FlextInfraMiseArtifactsVerificationTopology,
):
    """Manifest, topology, and liveness verification for Mise transactions."""

    @classmethod
    def publication_current(
        cls,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate a completed publication without planning or rendering.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        root = request.root.expanduser().resolve()
        observed = cls._read_publication(root)
        result = r[m.Infra.CodegenPhaseOutcome]
        if observed.failure:
            return result.from_failure(observed)
        outcome = observed.value
        if not cls._publication_covers_request(outcome, request, root):
            return result.fail(
                "generation publication does not cover this request: "
                f"{root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH}; "
                "run make gen",
            )
        return result.ok(outcome)

    @classmethod
    def _publication_covers_request(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        request: m.Infra.CodegenConformRequest,
        root: Path,
    ) -> bool:
        """Report whether the authenticated receipt covers this exact request.

        Returns:
            True when the receipt's surface, scope, module, and scope roots
            cover this request exactly.

        """
        surface = c.Infra.CodegenConformSurface(request.what)
        scope = c.Infra.CodegenConformScope(request.scope)
        covers_surface = outcome.surface == surface or (
            outcome.surface is c.Infra.CodegenConformSurface.ALL
            and surface is not c.Infra.CodegenConformSurface.ALL
        )
        covers_scope = outcome.scope == scope or (
            outcome.scope is c.Infra.CodegenConformScope.ALL
            and scope is c.Infra.CodegenConformScope.SELF
            and root in outcome.scope_roots
        )
        if not covers_surface or not covers_scope or outcome.module != request.module:
            return False
        if not outcome.scope_roots:
            return False
        if scope not in {
            c.Infra.CodegenConformScope.SELF,
            c.Infra.CodegenConformScope.ALL,
        }:
            return True
        return root in outcome.scope_roots

    @classmethod
    def _read_publication(
        cls,
        root: Path,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate the stored native receipt before testing request coverage.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        root = root.expanduser().resolve()
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
        if cls._receipt_incomplete(outcome, root):
            return result.fail(
                f"generation publication does not cover this request: {report}; "
                "run make gen",
            )
        current = cls.publication_states_current(outcome)
        if current.failure:
            return result.from_failure(current)
        return cls.states_current((captured.value,)).map(lambda _: outcome)

    @staticmethod
    def _receipt_incomplete(
        outcome: m.Infra.CodegenPhaseOutcome,
        root: Path,
    ) -> bool:
        """Report whether the stored receipt lacks a complete publication.

        Returns:
            True when the receipt is incomplete or belongs to another root.

        """
        if not outcome.completed or outcome.error or outcome.issues:
            return True
        if outcome.pending_files or not (outcome.outputs or outcome.batches):
            return True
        return outcome.root != root or outcome.transaction_id is None

    @classmethod
    def publication_states_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Verify the terminal frontier of the actual ordered journal batches.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not outcome.completed or outcome.issues or outcome.pending_files:
            return r[bool].fail("generation batch is incomplete; run make gen")
        closure = cls._producer_closure_current(
            outcome, producer_verifier=producer_verifier
        )
        if closure.failure:
            return closure
        membership = cls._docs_membership_current(outcome)
        if membership.failure:
            return membership
        topology = cls._source_topology_current(outcome)
        if topology.failure:
            return topology
        return cls._recorded_sources_current(outcome)

    @classmethod
    def _producer_closure_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        *,
        producer_verifier: p.Infra.CodegenProducerVerifier,
    ) -> p.Result[bool]:
        """Prove pre-planning producer closure for a batchless outcome.

        Args:
            outcome: Published phase outcome to authenticate.
            producer_verifier: Composed authority authenticating the complete epoch.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.batches:
            return r[bool].ok(value=True)
        if (
            not outcome.generator_sources
            or outcome.generator_reference is None
            or not outcome.generator_reference.source_authority.inputs
            or any(source.role is None for source in outcome.generator_sources)
        ):
            return r[bool].fail(
                "generation batch lacks pre-planning producer closure; run make gen",
            )
        producer = FlextInfraCodegenPreconditions.producer_trees_current(
            outcome.generator_trees,
            outcome.outputs,
            modules=outcome.generator_modules,
            reference=outcome.generator_reference,
        )
        if producer.failure:
            return producer
        return r[bool].ok(value=True)

    @classmethod
    def _docs_membership_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Prove DOCS-phase source membership matches the live documentation tree.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.phase != c.Infra.CodegenStagedFilePhase.DOCS:
            return r[bool].ok(value=True)
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
        return r[bool].ok(value=True)

    @classmethod
    def _source_topology_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Prove every planned source topology witness is still exact.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for witness in outcome.source_topology:
            observed = u.Cli.atomic_plan_directory_chain(witness.target)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != witness:
                return r[bool].fail(
                    f"generation source topology changed: {witness.target}; "
                    "run make gen",
                )
        return r[bool].ok(value=True)

    @classmethod
    def _recorded_sources_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Prove every recorded source and output still matches its live state.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for expected in (
            *outcome.sources,
            *outcome.outputs,
            *outcome.generator_sources,
        ):
            ancestry = cls._absent_parent_ancestry_current(expected)
            if ancestry.failure:
                return ancestry
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
        return r[bool].ok(value=True)

    @staticmethod
    def _absent_parent_ancestry_current(
        expected: m.Infra.CodegenJournalSource,
    ) -> p.Result[bool]:
        """Prove a planned absent-parent ancestry is still exact.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if expected.absent_parent is None:
            return r[bool].ok(value=True)
        ancestry = u.Cli.atomic_plan_directory_chain(expected.path.parent)
        if ancestry.failure:
            return r[bool].from_failure(ancestry)
        if ancestry.value != expected.absent_parent:
            return r[bool].fail(
                f"generation source ancestry changed: {expected.path}; run make gen",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _publication_frontier(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        frontier: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Advance only through outputs authorized by their native effect journal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if cls._frontier_incomplete(outcome):
            return r[bool].fail("generation batch is incomplete; run make gen")
        prerequisites = cls._frontier_prerequisites_current(outcome)
        if prerequisites.failure:
            return prerequisites
        journal = cls._frontier_journal_current(outcome, frontier)
        if journal.failure:
            return journal
        for batch in outcome.batches:
            advanced = cls._publication_frontier(batch, frontier)
            if advanced.failure:
                return advanced
        return r[bool].ok(value=True)

    @staticmethod
    def _frontier_incomplete(outcome: m.Infra.CodegenPhaseOutcome) -> bool:
        """Report whether the frontier outcome lacks a complete publication.

        Returns:
            True when the outcome is incomplete or lacks its journal identity.

        """
        if not outcome.completed or outcome.error or outcome.issues:
            return True
        if outcome.pending_files or outcome.root is None:
            return True
        if outcome.transaction_id is None:
            return True
        return not (outcome.outputs or outcome.batches)

    @classmethod
    def _frontier_prerequisites_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Prove producer closure, DOCS membership, and source topology.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        closure = cls._producer_closure_current(
            outcome, producer_verifier=producer_verifier
        )
        if closure.failure:
            return closure
        membership = cls._docs_frontier_membership_current(outcome)
        if membership.failure:
            return membership
        return cls._source_topology_current(outcome)

    @classmethod
    def _docs_frontier_membership_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Prove DOCS source membership for the frontier, including outputs.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.phase != c.Infra.CodegenStagedFilePhase.DOCS:
            return r[bool].ok(value=True)
        membership = u.Infra.docs_source_paths_for_roots(
            outcome.scope_roots,
            source_scope=outcome.source_scope,
        )
        if membership.failure:
            return r[bool].from_failure(membership)
        sources = {source.path: source for source in outcome.sources}
        destinations = {output.path for output in outcome.outputs}
        sources.update(
            {
                output.path: output
                for output in outcome.outputs
                if u.Infra.docs_source_path_is_input(
                    output.path,
                    outcome.scope_roots,
                    source_scope=outcome.source_scope,
                )
            },
        )
        expected_paths = {
            source.path
            for source in sources.values()
            if source.sha256 is not None
            and (
                source.path not in destinations
                or u.Infra.docs_source_path_is_input(
                    source.path,
                    outcome.scope_roots,
                    source_scope=outcome.source_scope,
                )
            )
        }
        if set(membership.value) != expected_paths:
            return r[bool].fail(
                "generation source membership changed; "
                f"added={sorted(set(membership.value) - expected_paths)}; "
                f"removed={sorted(expected_paths - set(membership.value))}; "
                "run make gen",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _frontier_journal_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        frontier: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Prove written files and inputs against the advancing frontier.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        outputs = {item.path: item for item in outcome.outputs}
        written = set(outcome.written_files)
        authority = cls._written_files_authority(outcome, written, outputs)
        if authority.failure:
            return authority
        inputs = cls._frontier_inputs_current(outcome, written, frontier)
        if inputs.failure:
            return r[bool].from_failure(inputs)
        return cls._frontier_outputs_current(outputs, written, inputs.value, frontier)

    @staticmethod
    def _written_files_authority(
        outcome: m.Infra.CodegenPhaseOutcome,
        written: set[Path],
        outputs: t.MappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Prove every written path carries its native batch or effect authority.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.batches:
            if written != {
                path for batch in outcome.batches for path in batch.written_files
            }:
                return r[bool].fail(
                    "generation operation differs from its actual batches",
                )
            return r[bool].ok(value=True)
        if not written.issubset(
            set(outcome.effect_targets) & set(outcome.attempted_files) & outputs.keys(),
        ):
            return r[bool].fail("generation writes have no journal effect authority")
        return r[bool].ok(value=True)

    @classmethod
    def _frontier_inputs_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        written: set[Path],
        frontier: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]]]:
        """Prove batch inputs agree with the frontier and each other.

        Returns:
            The resulting ``p.Result[t.MutableMappingKV[Path,
                list[m.Infra.CodegenJournalSource]]]``.

        """
        inputs: dict[Path, list[m.Infra.CodegenJournalSource]] = {}
        for source in (*outcome.sources, *outcome.generator_sources):
            inputs.setdefault(source.path, []).append(source)
        for path, records in inputs.items():
            previous = frontier.get(path)
            if previous is not None and not any(
                record.model_dump(exclude={"phase", "role"})
                == previous.model_dump(exclude={"phase", "role"})
                for record in records
            ):
                return r[
                    t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]]
                ].fail(
                    f"generation batch input differs from preceding output: {path}",
                )
            if path not in written and any(
                record.model_dump(exclude={"phase", "role"})
                != records[0].model_dump(exclude={"phase", "role"})
                for record in records[1:]
            ):
                return r[
                    t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]]
                ].fail(
                    f"generation inputs disagree without an owned write: {path}",
                )
            frontier[path] = records[0]
        return r[t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]]].ok(
            inputs
        )

    @staticmethod
    def _frontier_outputs_current(
        outputs: t.MappingKV[Path, m.Infra.CodegenJournalSource],
        written: set[Path],
        inputs: t.MappingKV[Path, list[m.Infra.CodegenJournalSource]],
        frontier: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Prove written outputs have preimages and unwritten ones are unchanged.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for path, output in outputs.items():
            if path in written:
                if path not in inputs:
                    return r[bool].fail(
                        f"generation output has no authenticated preimage: {path}",
                    )
            elif path in frontier and (
                frontier[path].model_dump(exclude={"phase", "role"})
                != output.model_dump(exclude={"phase", "role"})
            ):
                return r[bool].fail(
                    f"generation output changed without an owned write: {path}",
                )
            frontier[path] = output
        return r[bool].ok(value=True)

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
