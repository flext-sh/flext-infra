"""Scope metadata derivation for docs generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra import c, m
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsGenerateSources:
    """Derive one docs scope's identity from its live or projected metadata."""

    @staticmethod
    def docs_scope_from_sources(
        scope: m.Infra.DocScope,
        *,
        metadata_projection: m.Infra.CodegenFilePlan | None = None,
        governance_source: m.Infra.CodegenBootstrapSource | None = None,
    ) -> m.Infra.DocScope:
        """Derive scope metadata, package identity and governance owner.

        Returns:
            The resulting ``m.Infra.DocScope``.

        Raises:
            ValueError: If docs scope is disabled in its metadata.

        """
        if scope.name == c.Infra.RK_ROOT:
            return scope.model_copy(update={"governance_source": governance_source})
        state = FlextInfraUtilitiesDocsScope.project_state(
            scope.path,
            metadata_projection=metadata_projection,
        )
        if not FlextInfraUtilitiesDocsScope.docs_scope_enabled(state.docs_meta):
            msg = f"docs scope is disabled in its metadata: {scope.path}"
            raise ValueError(msg)
        return scope.model_copy(
            update={
                "name": state.project_name,
                "package_name": state.package_name,
                "documentation_language": (
                    FlextInfraUtilitiesDocsScope.docs_documentation_language(
                        state.docs_meta
                    )
                ),
                "project_class": (
                    FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                        state.project_name,
                        state.docs_meta,
                    )
                ),
                "governance_source": governance_source,
            }
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateSources"]
