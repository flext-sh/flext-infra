"""Publication receipt and effect-lineage verification for Mise transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
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

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsVerificationReceipts(FlextInfraMiseArtifactsComparison):
    """Authenticate publication receipts and the frontier of their effects."""

    @classmethod
    def publication_current(
        cls,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Verify a completed publication's physical inputs and effects.

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

        Recorded data proves physical inputs and effects, never executable code.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.root is None:
            return r[bool].fail("publication receipt lacks its actual root")
        history = cls._publication_history_current((outcome,))
        if history.failure:
            return r[bool].from_failure(history)
        outputs, batches = history.value
        states = {source.path: source for batch in batches for source in batch.sources}
        states.update((output.path, output) for output in outputs)
        return cls._recorded_states_current(tuple(states.values()))

    @classmethod
    def publication_outputs_current(
        cls,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        reference: m.Infra.NativeImportReference | None = None,
        destinations: t.SequenceOf[Path] | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]:
        """Authenticate actual prior effects before using them as producer authority.

        Returns:
            Terminal outputs relevant to the original producer, or the first failure.

        """
        pending = list(publications)
        while pending:
            publication = pending.pop()
            if publication.batches:
                pending.extend(publication.batches)
            else:
                born = cls.publication_birth_current(publication)
                if born.failure:
                    return r[
                        t.VariadicTuple[m.Infra.CodegenJournalSource]
                    ].from_failure(
                        born,
                    )
        history = cls._publication_history_current(
            publications, reference=reference, destinations=destinations
        )
        result_type = r[t.VariadicTuple[m.Infra.CodegenJournalSource]]
        if history.failure:
            return result_type.from_failure(history)
        outputs, _outcomes = history.value
        return result_type.ok(outputs)

    @staticmethod
    def publication_birth_current(
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Require the exact receipt emitted by its live publication owner.

        Returns:
            Success for the original receipt, never a JSON or copied model.

        """
        storage = outcome.__pydantic_private__
        if storage is None or storage.get("_publication_birth") != (
            id(outcome),
            u.Cli.sha256_content(outcome.model_dump_json()),
        ):
            return r[bool].fail(
                "publication receipt was not emitted by this live operation",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _publication_history_current(
        cls,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        reference: m.Infra.NativeImportReference | None = None,
        destinations: t.SequenceOf[Path] | None = None,
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
        if reference is not None or destinations is not None:
            files = frozenset((
                *(
                    (state.path for state in reference.source_authority.inputs)
                    if reference is not None
                    else ()
                ),
                *(destinations if destinations is not None else ()),
            ))
            directories = (
                {tree.root.path for tree in reference.source_authority.generator_trees}
                if reference is not None
                else set()
            )
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
                publication,
                frontier,
                terminal,
                outcomes,
                None,
            )
            if history.failure:
                return result_type.from_failure(history)
        outputs = tuple(
            record
            for path, record in terminal.items()
            if selection is None or selection(path)
        )
        physical = cls._recorded_states_current(
            tuple(
                record
                for path, record in frontier.items()
                if selection is None or selection(path)
            )
        )
        if physical.failure:
            return result_type.from_failure(physical)
        topology = {
            witness.target: witness
            for batch in outcomes
            for witness in batch.source_topology
        }
        for batch in outcomes:
            if selection is not None and not any(
                selection(output.path) for output in batch.outputs
            ):
                continue
            prerequisites = cls._frontier_prerequisites_current(
                batch, outputs, topology
            )
            if prerequisites.failure:
                return result_type.from_failure(prerequisites)
        return result_type.ok((outputs, tuple(outcomes)))

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
        """Prove each terminal output still matches its recorded physical identity.

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
                batch,
                frontier,
                terminal,
                outcomes,
                selection,
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
                or outcome.source_directories
                or outcome.source_query_topology
                or outcome.source_scope is not None
                or outcome.analysis is not None
                or outcome.admitted_states
                or outcome.published_files
                or outcome.retained_files
                or outcome.effect_targets
                or outcome.attempted_files
            )
        return not outcome.outputs

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
        """Prove consumed snapshots agree with prior outputs and each other.

        Read-only inputs remain evidence of their completed batch. Only actual
        output snapshots advance the frontier re-proven by later publications.

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
            else:
                previous = frontier.get(path)
                preimages = (
                    *inputs.get(path, ()),
                    *((previous,) if previous is not None else ()),
                )
                if any(
                    preimage.model_dump(exclude={"phase", "role"})
                    != output.model_dump(exclude={"phase", "role"})
                    for preimage in preimages
                ):
                    return r[bool].fail(
                        f"generation output changed without an owned write: {path}",
                    )
            frontier[path] = output
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraMiseArtifactsVerificationReceipts"]
