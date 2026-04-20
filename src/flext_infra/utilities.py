"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods exposed directly via u.Infra.[method](...)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import u

from flext_infra import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegen,
    FlextInfraUtilitiesCompatibility,
    FlextInfraUtilitiesDependencyPathSync,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsAudit,
    FlextInfraUtilitiesDocsBuild,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsFix,
    FlextInfraUtilitiesDocsGenerate,
    FlextInfraUtilitiesDocsRender,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsValidate,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesLogParser,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRelease,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesSafety,
    FlextInfraUtilitiesVersioning,
)


class FlextInfraUtilities(u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import u

        u.Cli.run_checked(["git", "status"])
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCompatibility,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesGithub,
        FlextInfraUtilitiesImportNormalizer,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesDocsApi,
        FlextInfraUtilitiesDocsAudit,
        FlextInfraUtilitiesDocsBuild,
        FlextInfraUtilitiesDocsContract,
        FlextInfraUtilitiesDocsFix,
        FlextInfraUtilitiesDocsGenerate,
        FlextInfraUtilitiesDocsRender,
        FlextInfraUtilitiesDocsScope,
        FlextInfraUtilitiesDocsValidate,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesDependencyPathSync,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesParsing,
        FlextInfraUtilitiesPatterns,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRope,
        FlextInfraUtilitiesSafety,
        FlextInfraUtilitiesVersioning,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""

        @staticmethod
        @override
        def package_name(path: Path, /) -> str:
            """Resolve the canonical package name for a file-system path."""
            return FlextInfraUtilitiesDiscovery.package_name(path)


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
