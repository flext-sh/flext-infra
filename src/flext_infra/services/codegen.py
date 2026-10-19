"""Caller-bound codegen handlers inherited by the public API service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import p
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenProtocolModels,
)


class FlextInfraCodegenHandlers:
    """Compose fresh conform invocations from the caller's actual capabilities."""

    def codegen_generate(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Generate projections using the caller-bound ports and runtime seeds.

        Exceptions from collaborator binding or generation propagate unchanged.

        Returns:
            The delegated generation Result, including any reported failure.

        """
        return FlextInfraCodegenConform.generate_request(
            request,
            execution_context=self,
        )

    def codegen_conform(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenConformRequest,
        initial_workspace: p.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Observe or repair projections without retaining request state on the API.

        Exceptions from collaborator binding or conformance propagate unchanged.

        Returns:
            The delegated observation or repair Result, including reported failures.

        """
        return FlextInfraCodegenConform.execute_request(
            request,
            initial_workspace,
            execution_context=self,
        )

    def codegen_protocol_models(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CommandPayloadContext,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Bind protocol projection to this API's native conformance handler.

        Returns:
            The unchanged service result, including any publication failure.

        """
        return FlextInfraCodegenProtocolModels(
            repository_root=request.repository_root,
            apply_changes=request.apply_changes,
            check_only=request.check_only,
            dry_run=request.dry_run,
            conform=self.codegen_conform,
        ).execute()


__all__: list[str] = ["FlextInfraCodegenHandlers"]
