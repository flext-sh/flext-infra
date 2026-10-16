"""Physical topology, source, destination, and real-consumer verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, codegen, m, r, t, u
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
        surface = c.Infra.CodegenConformSurface(request.what)
        observed = cls._read_publication(root, surface)
        result = r[m.Infra.CodegenPhaseOutcome]
        if observed.failure:
            return result.from_failure(observed)
        outcome = observed.value
        if not cls._publication_covers_request(outcome, request, root):
            return result.fail(
                "generation publication does not cover this request: "
                f"{root / cls.publication_receipt(surface)}; run make gen",
            )
        return result.ok(outcome)

    @staticmethod
    def publication_receipt(surface: c.Infra.CodegenConformSurface) -> Path:
        """Derive the repository-relative slot of one surface's latest receipt.

        The complete ``all`` surface owns the generation receipt; every
        partial surface owns its own slot inside the publication archive, so
        a partial publication never evicts the generation receipt.

        Returns:
            The slot path relative to the repository root.

        """
        latest = c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        if surface is c.Infra.CodegenConformSurface.ALL:
            return latest
        return c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH / (
            f"{surface.value}{latest.suffix}"
        )

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
        surface: c.Infra.CodegenConformSurface,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Authenticate the stored native receipt before testing request coverage.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        root = root.expanduser().resolve()
        captured = cls._governing_receipt(root, surface)
        result = r[m.Infra.CodegenPhaseOutcome]
        if captured.failure:
            return result.from_failure(captured)
        report = captured.value.path
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

    @classmethod
    def _governing_receipt(
        cls,
        root: Path,
        surface: c.Infra.CodegenConformSurface,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Elect the receipt slot that governs one surface's publication.

        A partial surface without its own publication is governed by the
        generation receipt, which covers every surface; the ``all``
        publication retires the partial slots it supersedes.

        Returns:
            The captured state of the governing slot, present or absent.

        """
        captured = FlextInfraMiseArtifactsFiles.read_state(
            root / cls.publication_receipt(surface),
            required=False,
        )
        if (
            captured.failure
            or captured.value.content is not None
            or surface is c.Infra.CodegenConformSurface.ALL
        ):
            return captured
        return FlextInfraMiseArtifactsFiles.read_state(
            root / cls.publication_receipt(c.Infra.CodegenConformSurface.ALL),
            required=False,
        )

    @classmethod
    def _receipt_incomplete(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        root: Path,
    ) -> bool:
        """Report whether the stored receipt lacks a complete publication.

        Returns:
            True when the receipt is incomplete or belongs to another root.

        """
        return cls._frontier_incomplete(outcome) or outcome.root != root

    @classmethod
    def publication_states_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Verify the terminal frontier of the actual ordered journal batches.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        history = cls._publication_history_current((outcome,))
        if history.failure:
            return r[bool].from_failure(history)
        outputs, outcomes = history.value
        for batch in outcomes:
            producer = cls._producer_closure_current(batch, outputs)
            if producer.failure:
                return producer
        return r[bool].ok(value=True)

    @classmethod
    def publication_outputs_current(
        cls,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        reference: m.Infra.NativeImportReference | None = None,
        destinations: t.SequenceOf[Path] = (),
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]:
        """Authenticate actual prior effects before using them as producer authority.

        Returns:
            Terminal outputs relevant to the original producer, or the first failure.

        """
        return cls._publication_history_current(
            publications, reference=reference, destinations=destinations
        ).map(operator.itemgetter(0))

    @classmethod
    def _publication_history_current(
        cls,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        reference: m.Infra.NativeImportReference | None = None,
        destinations: t.SequenceOf[Path] = (),
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Infra.CodegenJournalSource],
            t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        ]
    ]:
        """Prove actual effect lineage without executing historical producers again.

        Returns:
            The terminal outputs and their ordered batch receipts, or the
            first lineage failure.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[m.Infra.CodegenJournalSource],
                t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
            ]
        ]
        if not publications:
            return result_type.ok(((), ()))
        selection: Callable[[Path], bool] | None = None
        if reference is not None:
            files = frozenset((
                *(state.path for state in reference.source_authority.inputs),
                *destinations,
            ))
            directories = {
                tree.root.path for tree in reference.source_authority.generator_trees
            }
            roots = tuple(
                root
                for root in sorted(directories)
                if directories.isdisjoint(root.parents)
            )

            def relevant(path: Path) -> bool:
                return path in files or any(path.is_relative_to(root) for root in roots)

            selection = relevant
        terminal: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource] = {}
        outcomes: list[m.Infra.CodegenPhaseOutcome] = []
        frontier: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource] = {}
        for publication in publications:
            history = cls._publication_frontier(
                publication, frontier, terminal, outcomes, selection
            )
            if history.failure:
                return result_type.from_failure(history)
        outputs = tuple(terminal.values())
        physical = cls._recorded_states_current(tuple(frontier.values()))
        if physical.failure:
            return result_type.from_failure(physical)
        topology = {
            witness.target: witness
            for batch in outcomes
            for witness in batch.source_topology
        }
        for batch in outcomes:
            prerequisites = cls._frontier_prerequisites_current(
                batch, outputs, topology
            )
            if prerequisites.failure:
                return result_type.from_failure(prerequisites)
        return result_type.ok((outputs, tuple(outcomes)))

    @classmethod
    def _producer_closure_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Prove pre-planning producer closure for a batchless outcome.

        Args:
            outcome: Published phase outcome to authenticate.
            outputs: Physically authenticated terminal effects of the whole operation.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.batches:
            return r[bool].ok(value=True)
        return codegen.FlextInfraCodegenPreconditions.producer_trees_current(
            outcome.generator_trees,
            outputs,
            modules=outcome.generator_modules,
            reference=outcome.generator_reference,
        )

    @classmethod
    def _source_topology_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
        topology: t.MappingKV[Path, m.Cli.AtomicDirectoryChainPlan],
    ) -> p.Result[bool]:
        """Prove every planned source topology witness is still exact.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for witness in outcome.source_topology:
            terminal = topology[witness.target]
            if terminal != witness:
                gained = witness.directories[
                    : len(witness.directories) - len(terminal.directories)
                ]
                extension = (
                    bool(gained)
                    and terminal.anchor_path == gained[-1]
                    and terminal.directories == witness.directories[len(gained) :]
                    and terminal.anchor_ancestry[: len(witness.anchor_ancestry)]
                    == witness.anchor_ancestry
                    and all(
                        any(
                            output.sha256 is not None
                            and output.path.is_relative_to(path)
                            for output in outputs
                        )
                        for path in gained
                    )
                )
                if not extension:
                    return r[bool].fail(
                        f"generation source topology has no owned extension: "
                        f"{witness.target}; run make gen",
                    )
            observed = u.Cli.atomic_plan_directory_chain(witness.target)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != terminal:
                return r[bool].fail(
                    f"generation source topology changed: {witness.target}; "
                    "run make gen",
                )
        return r[bool].ok(value=True)

    @classmethod
    def _recorded_states_current(
        cls,
        states: t.VariadicTuple[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Prove each terminal input or output state still matches its live identity.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for expected in states:
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
        terminal: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource],
        outcomes: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
        selection: Callable[[Path], bool] | None,
    ) -> p.Result[bool]:
        """Advance only through outputs authorized by their native effect journal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if cls._frontier_incomplete(outcome):
            return r[bool].fail(
                outcome.error or "generation batch is incomplete; run make gen",
                exception=outcome.exception,
            )
        journal = cls._frontier_journal_current(outcome, frontier, selection)
        if journal.failure:
            return r[bool].from_failure(journal)
        terminal.update(journal.value)
        if selection is None or journal.value:
            outcomes.append(outcome)
        for batch in outcome.batches:
            advanced = cls._publication_frontier(
                batch, frontier, terminal, outcomes, selection
            )
            if advanced.failure:
                return advanced
        return r[bool].ok(value=True)

    @staticmethod
    def _frontier_incomplete(outcome: m.Infra.CodegenPhaseOutcome) -> bool:
        """Report whether the frontier outcome lacks a complete publication.

        Returns:
            True when the outcome is incomplete or lacks its journal identity.

        """
        if (
            not outcome.completed
            or outcome.error
            or outcome.issues
            or outcome.exception is not None
        ):
            return True
        if outcome.pending_files or outcome.root is None:
            return True
        if outcome.transaction_id is None:
            return True
        if outcome.batches:
            return bool(
                outcome.outputs
                or outcome.sources
                or outcome.generator_sources
                or outcome.generator_trees
                or outcome.generator_modules
                or outcome.generator_reference is not None
                or outcome.source_topology
                or outcome.source_scope is not None
                or outcome.analysis is not None
                or outcome.admitted_states
                or outcome.published_files
                or outcome.retained_files
                or outcome.effect_targets
                or outcome.attempted_files
            )
        reference = outcome.generator_reference
        return (
            not outcome.outputs
            or not outcome.generator_sources
            or reference is None
            or not reference.source_authority.inputs
            or any(source.role is None for source in outcome.generator_sources)
            or outcome.generator_trees != reference.source_authority.generator_trees
            or outcome.generator_modules != reference.source_authority.generator_modules
        )

    @classmethod
    def _frontier_prerequisites_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
        topology: t.MappingKV[Path, m.Cli.AtomicDirectoryChainPlan],
    ) -> p.Result[bool]:
        """Prove completed effects retain DOCS membership and source topology.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        membership = cls._docs_frontier_membership_current(outcome, outputs)
        if membership.failure:
            return membership
        return cls._source_topology_current(outcome, outputs, topology)

    @classmethod
    def _docs_frontier_membership_current(
        cls,
        outcome: m.Infra.CodegenPhaseOutcome,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
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
        destinations = {output.path for output in outputs}
        sources.update(
            {
                output.path: output
                for output in outputs
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
        selection: Callable[[Path], bool] | None,
    ) -> p.Result[t.MappingKV[Path, m.Infra.CodegenJournalSource]]:
        """Prove written files and inputs against the advancing frontier.

        Returns:
            Relevant outputs after their historical preimages have been proven.

        """
        result_type = r[t.MappingKV[Path, m.Infra.CodegenJournalSource]]
        outputs = {item.path: item for item in outcome.outputs}
        if len(outputs) != len(outcome.outputs):
            return result_type.fail("generation batch carries duplicate output paths")
        written = set(outcome.written_files)
        authority = cls._written_files_authority(outcome, written, outputs)
        if authority.failure:
            return result_type.from_failure(authority)
        selected = {
            path: output
            for path, output in outputs.items()
            if selection is None or selection(path)
        }
        inputs = cls._frontier_inputs_current(outcome, written, frontier, selection)
        if inputs.failure:
            return result_type.from_failure(inputs)
        return cls._frontier_outputs_current(
            selected, written, inputs.value, frontier
        ).map(lambda _current: selected)

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
        selection: Callable[[Path], bool] | None,
    ) -> p.Result[t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]]]:
        """Prove consumed data snapshots agree with the frontier and each other.

        Native producer inputs belong to the original code epoch and are
        authenticated separately against its physically proven terminal effects.

        Returns:
            The resulting ``p.Result[t.MutableMappingKV[Path,
                list[m.Infra.CodegenJournalSource]]]``.

        """
        inputs: t.MutableMappingKV[Path, list[m.Infra.CodegenJournalSource]] = {}
        for source in outcome.sources:
            if selection is None or selection(source.path):
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
