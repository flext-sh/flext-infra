# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Docs package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._docs.api import FlextInfraUtilitiesDocsApi
    from flext_infra._utilities._docs.audit import FlextInfraUtilitiesDocsAudit
    from flext_infra._utilities._docs.audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectors,
    )
    from flext_infra._utilities._docs.base import FlextInfraUtilitiesDocsBase
    from flext_infra._utilities._docs.build import FlextInfraUtilitiesDocsBuild
    from flext_infra._utilities._docs.collection import (
        FlextInfraUtilitiesDocsCollection,
    )
    from flext_infra._utilities._docs.collection_sources import (
        FlextInfraUtilitiesDocsCollectionSources,
    )
    from flext_infra._utilities._docs.command_contract import (
        FlextInfraUtilitiesDocsCommandContract,
    )
    from flext_infra._utilities._docs.contract import FlextInfraUtilitiesDocsContract
    from flext_infra._utilities._docs.fix import FlextInfraUtilitiesDocsFix
    from flext_infra._utilities._docs.generate import FlextInfraUtilitiesDocsGenerate
    from flext_infra._utilities._docs.generate_plan import (
        FlextInfraUtilitiesDocsGeneratePlan,
    )
    from flext_infra._utilities._docs.generate_project import (
        FlextInfraUtilitiesDocsGenerateProject,
    )
    from flext_infra._utilities._docs.generate_root import (
        FlextInfraUtilitiesDocsGenerateRoot,
    )
    from flext_infra._utilities._docs.generate_sources import (
        FlextInfraUtilitiesDocsGenerateSources,
    )
    from flext_infra._utilities._docs.github_links import (
        FlextInfraUtilitiesDocsGithubLinks,
    )
    from flext_infra._utilities._docs.guides import FlextInfraUtilitiesDocsGuides
    from flext_infra._utilities._docs.render import FlextInfraUtilitiesDocsRender
    from flext_infra._utilities._docs.scope import FlextInfraUtilitiesDocsScope
    from flext_infra._utilities._docs.scope_build import (
        FlextInfraUtilitiesDocsScopeBuild,
    )
    from flext_infra._utilities._docs.scope_paths import (
        FlextInfraUtilitiesDocsScopePaths,
    )
    from flext_infra._utilities._docs.scope_policy import (
        FlextInfraUtilitiesDocsScopePolicy,
    )
    from flext_infra._utilities._docs.scope_projects import (
        FlextInfraUtilitiesDocsScopeProjects,
    )
    from flext_infra._utilities._docs.scope_selection import (
        FlextInfraUtilitiesDocsScopeSelection,
    )
    from flext_infra._utilities._docs.scope_state import (
        FlextInfraUtilitiesDocsScopeState,
    )
    from flext_infra._utilities._docs.validate import FlextInfraUtilitiesDocsValidate


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectors",
    "FlextInfraUtilitiesDocsBase",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsCollection",
    "FlextInfraUtilitiesDocsCollectionSources",
    "FlextInfraUtilitiesDocsCommandContract",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsGeneratePlan",
    "FlextInfraUtilitiesDocsGenerateProject",
    "FlextInfraUtilitiesDocsGenerateRoot",
    "FlextInfraUtilitiesDocsGenerateSources",
    "FlextInfraUtilitiesDocsGithubLinks",
    "FlextInfraUtilitiesDocsGuides",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsScopeBuild",
    "FlextInfraUtilitiesDocsScopePaths",
    "FlextInfraUtilitiesDocsScopePolicy",
    "FlextInfraUtilitiesDocsScopeProjects",
    "FlextInfraUtilitiesDocsScopeSelection",
    "FlextInfraUtilitiesDocsScopeState",
    "FlextInfraUtilitiesDocsValidate",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesDocsApi": ".api",
        "FlextInfraUtilitiesDocsAudit": ".audit",
        "FlextInfraUtilitiesDocsAuditDetectors": ".audit_detectors",
        "FlextInfraUtilitiesDocsBase": ".base",
        "FlextInfraUtilitiesDocsBuild": ".build",
        "FlextInfraUtilitiesDocsCollection": ".collection",
        "FlextInfraUtilitiesDocsCollectionSources": ".collection_sources",
        "FlextInfraUtilitiesDocsCommandContract": ".command_contract",
        "FlextInfraUtilitiesDocsContract": ".contract",
        "FlextInfraUtilitiesDocsFix": ".fix",
        "FlextInfraUtilitiesDocsGenerate": ".generate",
        "FlextInfraUtilitiesDocsGeneratePlan": ".generate_plan",
        "FlextInfraUtilitiesDocsGenerateProject": ".generate_project",
        "FlextInfraUtilitiesDocsGenerateRoot": ".generate_root",
        "FlextInfraUtilitiesDocsGenerateSources": ".generate_sources",
        "FlextInfraUtilitiesDocsGithubLinks": ".github_links",
        "FlextInfraUtilitiesDocsGuides": ".guides",
        "FlextInfraUtilitiesDocsRender": ".render",
        "FlextInfraUtilitiesDocsScope": ".scope",
        "FlextInfraUtilitiesDocsScopeBuild": ".scope_build",
        "FlextInfraUtilitiesDocsScopePaths": ".scope_paths",
        "FlextInfraUtilitiesDocsScopePolicy": ".scope_policy",
        "FlextInfraUtilitiesDocsScopeProjects": ".scope_projects",
        "FlextInfraUtilitiesDocsScopeSelection": ".scope_selection",
        "FlextInfraUtilitiesDocsScopeState": ".scope_state",
        "FlextInfraUtilitiesDocsValidate": ".validate",
    }),
    public_exports=__all__,
)
