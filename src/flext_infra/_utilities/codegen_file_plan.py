"""Generated-file plan decisions exposed through ``u.Infra``."""

from __future__ import annotations

from flext_cli import m as cli_m, u as cli_u
from flext_core import r
from flext_infra import m, p


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    def codegen_file_before_state(
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[cli_m.Cli.AtomicFileState]:
        """Return a publishable state only after its parent physically exists.

        Read-only planning records the absent parent chain when there is no
        leaf to snapshot. Once the transaction has materialized that chain the
        leaf becomes readable, and its state — an absent file under a physical
        parent — is exactly what publication guards against.
        """
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            if not plan.path.parent.is_dir():
                return r[cli_m.Cli.AtomicFileState].fail(
                    f"codegen destination parent is absent: {plan.path.parent}"
                )
            return cli_u.Cli.atomic_read_binary_file_state(plan.path, required=False)
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
