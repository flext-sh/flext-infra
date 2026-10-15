"""One atomic campaign for declared candidate recovery projections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenPreconditions


class FlextInfraCandidateBootstrapService:
    """Plan every declared target before one journaled publication."""

    def __init__(
        self,
        planner: p.Infra.CandidateBootstrapPlanner,
        transaction: p.Infra.CandidateBootstrapTransaction,
    ) -> None:
        """Wire the declared-target planner to its atomic publisher."""
        self._planner = planner
        self._transaction = transaction

    def execute(
        self,
        source_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        command: m.Infra.CandidateBootstrapCommand,
        declaration_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Publish a fixed point for the entire typed target declaration.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        targets = workspace.candidate_bootstrap_targets
        if not targets:
            return r[bool].fail("candidate bootstrap targets are not declared")
        roots = self._resolved_roots(source_root, targets)
        if roots.failure:
            return r[bool].from_failure(roots)
        if command.dry_run or command.check_only or not command.apply_changes:
            return self._verify(roots.value, targets, declaration_states)

        def publish(scope_root: Path) -> p.Result[bool]:
            planned = self._plan(roots.value, targets, declaration_states)
            if planned.failure:
                return r[bool].from_failure(planned)
            analysis = planned.value
            changed = tuple(
                plan
                for plan in analysis.files
                if u.Infra.codegen_file_requires_effect(plan)
            )
            if not changed:
                return self._verify(roots.value, targets, declaration_states)
            receipts: list[m.Infra.CodegenPhaseOutcome] = []
            committed = self._transaction.publish_file_phase_locked(
                scope_root,
                roots.value,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=tuple(
                        sorted({
                            file.path.parent
                            for file in changed
                            if not file.path.parent.is_dir()
                        }),
                    ),
                ),
                publication_receipts=receipts,
            )
            if committed.failure:
                return r[bool].from_failure(committed)
            continued = self._planner.continue_after_publication(tuple(receipts))
            if continued.failure:
                return r[bool].from_failure(continued)
            return self._verify(
                roots.value,
                targets,
                declaration_states,
                publications=tuple(
                    publication
                    for receipt in receipts
                    for publication in receipt.published_files
                ),
            )

        return self._transaction.run_files_locked(roots.value, publish)

    @staticmethod
    def _resolved_roots(
        source_root: Path,
        targets: m.Infra.CandidateBootstrapTargets,
    ) -> p.Result[t.MutableMappingKV[str, Path]]:
        """Resolve each declared target to its exact elected worktree root.

        Args:
            source_root: The repository root anchoring declared target paths.
            targets: The declared candidate bootstrap targets.

        Returns:
            The elected worktree root keyed by candidate identity, or the
            first resolution failure.

        """
        roots: t.MutableMappingKV[str, Path] = {}
        for index, target in enumerate(targets):
            identity = u.Infra.exact_worktree_root(
                (source_root / target.path).resolve(strict=True),
            )
            if identity.failure:
                return r[t.MutableMappingKV[str, Path]].from_failure(identity)
            roots[f"@candidate-{index}"] = identity.value.repo_root
        if len(set(roots.values())) != len(roots):
            return r[t.MutableMappingKV[str, Path]].fail(
                "candidate bootstrap targets resolve to duplicate worktrees",
            )
        return r[t.MutableMappingKV[str, Path]].ok(roots)

    def _plan(
        self,
        roots: t.MappingKV[str, Path],
        targets: m.Infra.CandidateBootstrapTargets,
        declaration_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Compose one immutable receipt from all conform planners.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        files: list[m.Infra.CodegenFilePlan] = []
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {
            state.path: state for state in declaration_states
        }
        for root, target in zip(roots.values(), targets, strict=True):
            planned = self._planned_target(root, target, inputs)
            if planned.failure:
                return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
            for file in planned.value:
                sources = FlextInfraCodegenPreconditions.unique_states((
                    *file.source_states,
                    *declaration_states,
                ))
                if sources.failure:
                    return r[m.Infra.CodegenPhaseAnalysis].from_failure(sources)
                files.append(file.model_copy(update={"source_states": sources.value}))
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CANDIDATE_BOOTSTRAP,
                files=tuple(files),
                inputs=tuple(inputs.values()),
            ),
        )

    def _planned_target(
        self,
        root: Path,
        target: m.Infra.CandidateBootstrapTargetSpec,
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan one candidate target and admit its states into the inventory.

        Args:
            root: The elected worktree root of the target.
            target: The declared candidate bootstrap targets being planned.
            inputs: The mutable input state inventory, updated in place.

        Returns:
            The planned files of the target, or the first bootstrap failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        captured = self._captured_target_states(root, inputs)
        if captured.failure:
            return result_type.from_failure(captured)
        admitted = self._admitted_target_plan(root, target, captured.value)
        if admitted.failure:
            return result_type.from_failure(admitted)
        contract, planned_files = admitted.value
        files: list[m.Infra.CodegenFilePlan] = []
        for file in planned_files:
            diagnostic = self._planned_file_failure(root, file, contract, inputs)
            if diagnostic is not None:
                return result_type.fail(diagnostic)
            files.append(file)
            for state in file.source_states:
                inputs[state.path] = state
        return result_type.ok(tuple(files))

    @staticmethod
    def _captured_target_states(
        root: Path,
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenInputs]:
        """Load one target's codegen inputs and admit its source states.

        Args:
            root: The elected worktree root of the target.
            inputs: The mutable input state inventory, updated in place.

        Returns:
            The target's captured codegen inputs, or the first admission
            failure.

        """
        captured = u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return r[m.Infra.CodegenInputs].from_failure(captured)
        for state in captured.value.sources:
            previous = inputs.setdefault(state.path, state)
            if previous != state:
                return r[m.Infra.CodegenInputs].fail(
                    f"candidate bootstrap observed two states for {state.path}",
                )
        return r[m.Infra.CodegenInputs].ok(captured.value)

    def _admitted_target_plan(
        self,
        root: Path,
        target: m.Infra.CandidateBootstrapTargetSpec,
        captured: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Pair[
            m.Infra.CodegenConformSurfaceContract,
            t.VariadicTuple[m.Infra.CodegenFilePlan],
        ]
    ]:
        """Plan one target under its surface contract and prove destinations.

        Args:
            root: The elected worktree root of the target.
            target: The declared candidate bootstrap targets being planned.
            captured: The target's captured codegen inputs.

        Returns:
            The target's surface contract with its planned files, or the
            first contract violation.

        """
        result_type = r[
            t.Pair[
                m.Infra.CodegenConformSurfaceContract,
                t.VariadicTuple[m.Infra.CodegenFilePlan],
            ]
        ]
        contract = self._planner.surface_contract(target.what, codegen=captured.spec)
        if contract.complete_governed:
            return result_type.fail(
                f"candidate bootstrap requires one declared surface: {root}",
            )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=target.what,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = self._planner.plan_repositories(request, captured)
        if planned.failure:
            return result_type.from_failure(planned)
        if planned.value.exception is not None:
            raise planned.value.exception
        if planned.value.issues:
            return result_type.fail(planned.value.issues[0].formatted)
        if (
            contract.destinations is not None
            and not contract.destinations
            and not planned.value.files
        ):
            return result_type.fail(
                f"candidate bootstrap has no declared destinations: {root}",
            )
        return result_type.ok((contract, planned.value.files))

    @staticmethod
    def _planned_file_failure(
        root: Path,
        file: m.Infra.CodegenFilePlan,
        contract: m.Infra.CodegenConformSurfaceContract,
        inputs: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> str | None:
        """Name the first bootstrap violation of one planned file.

        Returns:
            The failure message, or ``None`` when the file is planable.

        """
        if file.project != root or not file.path.is_relative_to(root):
            return f"candidate bootstrap destination has a foreign owner: {file.path}"
        if (
            contract.destinations is not None
            and file.path.relative_to(root).as_posix() not in contract.destinations
        ):
            return (
                f"candidate bootstrap destination is outside its surface: {file.path}"
            )
        for state in file.source_states:
            previous = inputs.get(state.path)
            if previous is not None and previous != state:
                return f"candidate bootstrap observed two states for {state.path}"
        return None

    def _verify(
        self,
        roots: t.MappingKV[str, Path],
        targets: m.Infra.CandidateBootstrapTargets,
        declaration_states: t.VariadicTuple[m.Cli.AtomicFileState],
        *,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile] = (),
    ) -> p.Result[bool]:
        """Require unchanged declarations and a complete post-publication fixed point.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        published = {item.before.path: item for item in publications}
        expected_states: list[m.Cli.AtomicFileState] = []
        for state in declaration_states:
            publication = published.get(state.path)
            expected = state
            if publication is not None:
                if publication.before != state or publication.replacement is None:
                    return r[bool].fail(
                        "candidate bootstrap declaration lacks its "
                        "captured publication",
                    )
                expected = publication.replacement
            observed = u.Cli.atomic_read_binary_file_state(
                state.path,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != expected:
                return r[bool].fail(
                    "candidate bootstrap declaration changed during publication",
                )
            expected_states.append(expected)
        planned = self._plan(roots, targets, tuple(expected_states))
        if planned.failure:
            return r[bool].from_failure(planned)
        return u.Infra.codegen_fixed_point(
            planned.value.files,
            subject="candidate bootstrap",
        )


__all__: list[str] = ["FlextInfraCandidateBootstrapService"]
