"""Authenticate the real semantic publisher without invoking publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import m, p
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.validate import FlextInfraValidateFreshImport


class FlextInfraValidateProducer:
    """Expose the existing native producer authentication through a typed request."""

    @staticmethod
    def execute_request(
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Authenticate the bound publisher against its cold source authority.

        Returns:
            The original producer analysis or its unchanged authentication failure.

        """
        return FlextInfraValidateFreshImport.capture_producer(
            request.repository_root,
            entrypoint=FlextInfraSemanticPublication.publish_semantic_analyses,
        )


__all__: list[str] = ["FlextInfraValidateProducer"]
