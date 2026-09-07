"""Generated-file plan decisions exposed through ``u.Infra``."""

from __future__ import annotations

from pathlib import Path

from flext_cli import m as cli_m
from flext_core import r
from flext_infra import m, p
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

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
    def codegen_required_directories(
        plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> tuple[Path, ...]:
        """Return missing destination parents directly from authenticated plans."""
        required = {
            directory
            for plan in plans
            if plan.desired_content is not None
            and isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan)
            for directory in plan.before.directories
        }
        return tuple(sorted(required, key=FlextInfraUtilitiesBase.path_depth_then_text))

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
