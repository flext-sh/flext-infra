"""One campaign for declared candidate recovery projections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, p, r, t, u


class FlextInfraCandidateBootstrapService:
    """Plan every declared target before one shared publication."""

    def __init__(self, planner: p.Infra.CandidateBootstrapPlanner) -> None:
        """Wire the declared-target planner."""
        self._planner = planner

    def execute(
        self,
        source_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        command: m.Infra.CandidateBootstrapCommand,
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
        if command.apply_changes and not (command.dry_run or command.check_only):
            planned = self.plan_candidates(roots.value, targets)
            if planned.failure:
                return r[bool].from_failure(planned)
            published = u.Infra.publish_codegen_plans(source_root, planned.value)
            if published.failure:
                return r[bool].from_failure(published)
        return self._verify(roots.value, targets)

    @staticmethod
    def _resolved_roots(
        source_root: Path,
        targets: m.Infra.CandidateBootstrapTargets,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Resolve each declared target to its exact elected worktree root.

        Args:
            source_root: The repository root anchoring declared target paths.
            targets: The declared candidate bootstrap targets.

        Returns:
            The elected worktree roots in target order, or the first
            resolution failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        elected: list[Path] = []
        for target in targets:
            identity = u.Infra.exact_worktree_root(
                (source_root / target.path).resolve(strict=True),
            )
            if identity.failure:
                return result_type.from_failure(identity)
            elected.append(identity.value.repo_root)
        if len(set(elected)) != len(elected):
            return result_type.fail(
                "candidate bootstrap targets resolve to duplicate worktrees",
            )
        return result_type.ok(tuple(elected))

    def plan_candidates(
        self,
        roots: t.SequenceOf[Path],
        targets: m.Infra.CandidateBootstrapTargets,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Compose the file plans of every declared target.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        files: list[m.Infra.CodegenFilePlan] = []
        for root, target in zip(roots, targets, strict=True):
            planned = self._planned_target(root, target)
            if planned.failure:
                return result_type.from_failure(planned)
            files.extend(planned.value)
        return result_type.ok(tuple(files))

    def _planned_target(
        self,
        root: Path,
        target: m.Infra.CandidateBootstrapTargetSpec,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan one target under its surface contract and prove destinations.

        Args:
            root: The elected worktree root of the target.
            target: The declared candidate bootstrap target being planned.

        Returns:
            The planned files of the target, or the first contract violation.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        captured = u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return result_type.from_failure(captured)
        contract = self._planner.surface_contract(
            target.what, codegen=captured.value.spec
        )
        if contract.complete_governed:
            return result_type.fail(
                f"candidate bootstrap requires one declared surface: {root}",
            )
        planned = self._planner.plan_repositories(
            m.Infra.CodegenGenerateRequest(root=root, what=target.what),
            captured.value,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        if planned.value.exception is not None:
            raise planned.value.exception
        if planned.value.issues:
            return result_type.fail(planned.value.issues[0].formatted)
        files = planned.value.files
        if contract.destinations is not None and not contract.destinations and not files:
            return result_type.fail(
                f"candidate bootstrap has no declared destinations: {root}",
            )
        for file in files:
            if file.project != root or not file.path.is_relative_to(root):
                return result_type.fail(
                    f"candidate bootstrap destination has a foreign owner: {file.path}"
                )
            if (
                contract.destinations is not None
                and file.path.relative_to(root).as_posix() not in contract.destinations
            ):
                return result_type.fail(
                    f"candidate bootstrap destination is outside its surface: "
                    f"{file.path}"
                )
        return result_type.ok(tuple(files))

    def _verify(
        self,
        roots: t.SequenceOf[Path],
        targets: m.Infra.CandidateBootstrapTargets,
    ) -> p.Result[bool]:
        """Require a complete fixed point for every declared target.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        planned = self.plan_candidates(roots, targets)
        if planned.failure:
            return r[bool].from_failure(planned)
        return u.Infra.codegen_fixed_point(
            planned.value,
            subject="candidate bootstrap",
        )


__all__: list[str] = ["FlextInfraCandidateBootstrapService"]
