"""Caller-bound codegen handlers inherited by the public API service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCli

from flext_infra import codegen, h, m, p, t


class FlextInfraCodegenHandlers:
    """Compose each codegen operation from the caller's actual capabilities."""

    @classmethod
    def codegen_routes(
        cls: type[p.Infra.CodegenService],
        *,
        provide: t.Cli.NullaryOperation[p.Infra.CodegenService],
    ) -> t.VariadicTuple[p.Cli.ResultCommandRoute]:
        """Declare codegen request contracts and caller-bound handlers once.

        Returns:
            The existing result routes bound to this public API instance.

        """
        return FlextCli.service_routes(
            cls,
            provide=provide,
            owner=FlextInfraCodegenHandlers,
            operation_prefix="codegen_",
            success_formatter=FlextInfraCodegenHandlers._codegen_message,
        )

    @staticmethod
    def _codegen_message(operation: str, value: t.Cli.ResultValue) -> str:
        """Render a public codegen receipt at the CLI's output boundary.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If Codegen operation.

        """
        if not isinstance(value, p.Infra.CodegenResult):
            message = f"Codegen operation {operation} returned no generation receipt"
            raise TypeError(message)
        if operation == "codegen_conform":
            return "project conformance complete"
        return (
            "generation receipt: "
            f"repositories={len(value.plan.repositories)} "
            f"planned_files={len(value.plan.files)} "
            f"written_files={len(value.written_files)} "
            f"errors={len(value.errors)}\n"
            "managed projection generation complete"
        )

    @h.handler(command=m.Infra.CodegenGenerateRequest)
    def codegen_generate(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Generate projections using the caller-bound ports and runtime seeds.

        Exceptions from collaborator binding or generation propagate unchanged.

        Returns:
            The delegated generation Result, including any reported failure.

        """
        return codegen.FlextInfraCodegenConform.Generate.execute_request(
            request,
            execution_context=self,
        )

    @h.handler(command=m.Infra.CodegenConformRequest)
    def codegen_conform(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Observe or repair projections without retaining request state on the API.

        Exceptions from collaborator binding or conformance propagate unchanged.

        Returns:
            The delegated observation or repair Result, including reported failures.

        """
        return codegen.FlextInfraCodegenConform.execute_request(
            request,
            execution_context=self,
        )


__all__: list[str] = ["FlextInfraCodegenHandlers"]
