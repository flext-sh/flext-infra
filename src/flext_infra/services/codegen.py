"""Caller-bound codegen handlers inherited by the public API service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import p
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenConformExecute,
)


class FlextInfraCodegenHandlers:
    """Compose each codegen operation from the caller's actual capabilities."""

    def codegen_generate(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Generate projections using the caller-bound ports and runtime seeds.

        Exceptions from collaborator binding or generation propagate unchanged.

        Returns:
            The delegated generation Result, including any reported failure.

        """
        return FlextInfraCodegenConformExecute.execute_request(
            request,
            execution_context=self,
        )

    def codegen_conform(
        self: p.Infra.CodegenExecutionContext,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Observe or repair projections without retaining request state on the API.

        Exceptions from collaborator binding or conformance propagate unchanged.

        Returns:
            The delegated observation or repair Result, including reported failures.

        """
        return FlextInfraCodegenConform.execute_request(
            request,
            execution_context=self,
        )


__all__: list[str] = ["FlextInfraCodegenHandlers"]
