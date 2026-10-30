"""Scope metadata derivation for docs generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsGenerateSources:
    """Derive one docs scope's identity from its live or projected metadata."""

    @staticmethod
    def scope_from_sources(
        scope: m.Infra.DocScope,
        *,
        metadata_projection: m.Infra.CodegenFilePlan | None = None,
        governance_source: m.Infra.CodegenBootstrapSource | None = None,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> m.Infra.DocScope:
        """Derive scope metadata, package identity and governance owner.

        Returns:
            The resulting ``m.Infra.DocScope``.

        Raises:
            ValueError: If docs scope is disabled in its metadata.

        """
        name = scope.name
        package_name = scope.package_name
        language = scope.documentation_language
        project_class = scope.project_class
        if scope.name != c.Infra.RK_ROOT:
            state = FlextInfraUtilitiesDocsScope.project_state(
                scope.path, metadata_projection=metadata_projection
            )
            if not FlextInfraUtilitiesDocsScope.scope_enabled(state.docs_meta):
                msg = f"docs scope is disabled in its metadata: {scope.path}"
                raise ValueError(msg)
            name = state.project_name
            package_name = state.package_name
            language = FlextInfraUtilitiesDocsScope.docs_documentation_language(
                state.docs_meta
            )
            project_class = FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                state.project_name, state.docs_meta
            )
        return m.Infra.DocScope(
            name=name,
            path=scope.path,
            report_dir=scope.report_dir,
            package_name=package_name,
            project_class=project_class,
            documentation_language=language,
            governance_source=governance_source,
            repository_root_override=scope.repository_root_override,
            declared_files=declared_files,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateSources"]
