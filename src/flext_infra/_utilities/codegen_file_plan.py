"""Generated-file plan decisions exposed through ``u.Infra``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from flext_cli import m as cli_m, u
from flext_core import r
from flext_infra import m, p, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    def planned_file(
        project: Path,
        target: Path,
        *,
        required: bool,
        desired_content: bytes | None,
        desired_mode: int | None,
        source_states: t.SequenceOf[cli_m.Cli.AtomicFileState] = (),
        owner: str = "",
        policy: Literal["full", "merge", "create-only", "delegated", "manual"]
        | None = None,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Capture one destination's before state and bind it to its desired state.

        ``required`` says whether the destination must already exist: a removal
        plan reads an existing file, a publication plan tolerates its absence.
        """
        before = u.Cli.atomic_read_binary_file_state(target, required=required)
        if before.failure:
            return r[m.Infra.CodegenFilePlan].from_failure(before)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                project=project,
                path=target,
                before=before.value,
                desired_content=desired_content,
                desired_mode=desired_mode,
                source_states=tuple(source_states),
                owner=owner,
                policy=policy,
            )
        )

    @staticmethod
    def required_file_states(
        paths: t.IterableOf[Path],
    ) -> p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]:
        """Snapshot descriptor-authenticated states for an inventoried path set.

        Every path must exist: an absent input is a planning defect, not an empty
        snapshot.
        """
        states: list[cli_m.Cli.AtomicFileState] = []
        for path in sorted(set(paths)):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[cli_m.Cli.AtomicFileState, ...]].from_failure(state)
            states.append(state.value)
        return r[tuple[cli_m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def codegen_file_before_state(
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[cli_m.Cli.AtomicFileState]:
        """Return a publishable state only after its parent physically exists."""
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return r[cli_m.Cli.AtomicFileState].fail(
                f"codegen destination parent is absent: {plan.path.parent}"
            )
        return r[cli_m.Cli.AtomicFileState].ok(plan.before)

    @staticmethod
    def atomic_file_state_differs(
        before: cli_m.Cli.AtomicFileState,
        *,
        desired_content: bytes | None,
        desired_mode: int | None,
    ) -> bool:
        """Whether desired content or mode differs from an observed leaf state."""
        return before.content != desired_content or before.mode != desired_mode

    @staticmethod
    def codegen_file_requires_effect(plan: m.Infra.CodegenFilePlan) -> bool:
        """Whether publication must change a generated-file destination."""
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return plan.desired_content is not None
        return FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            plan.before,
            desired_content=plan.desired_content,
            desired_mode=plan.desired_mode,
        )


__all__: list[str] = ["FlextInfraUtilitiesCodegenFilePlan"]
