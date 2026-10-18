"""Caller-bound codegen handlers inherited by the public API service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, p
from flext_infra.codegen import FlextInfraCodegenConform


class FlextInfraCodegenHandlers:
    """Compose fresh conform invocations from the caller's actual capabilities."""

    def codegen_generate(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Generate projections using the caller-bound ports and runtime seeds."""
        return FlextInfraCodegenConform.generate_request(
            request,
            ports=self.codegen_conform_collaborators(),
            runtime_settings=self.settings,
            initial_context=self.context,
        )

    def codegen_conform(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenConformRequest,
        initial_workspace: p.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Observe or repair projections without retaining request state on the API."""
        return FlextInfraCodegenConform.execute_request(
            request,
            initial_workspace,
            ports=(
                None
                if request.mode is c.Infra.CodegenConformMode.CHECK
                else self.codegen_conform_collaborators()
            ),
            runtime_settings=self.settings,
            initial_context=self.context,
        )


__all__: list[str] = ["FlextInfraCodegenHandlers"]
