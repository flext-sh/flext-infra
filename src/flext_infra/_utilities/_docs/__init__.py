# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for docs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._docs.audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectors,
    )
    from flext_infra._utilities._docs.command_contract import (
        FlextInfraUtilitiesDocsCommandContract,
    )
    from flext_infra._utilities._docs.docs_api import FlextInfraUtilitiesDocsApi
    from flext_infra._utilities._docs.docs_audit import FlextInfraUtilitiesDocsAudit
    from flext_infra._utilities._docs.docs_build import FlextInfraUtilitiesDocsBuild
    from flext_infra._utilities._docs.docs_collection import (
        FlextInfraUtilitiesDocsCollection,
    )
    from flext_infra._utilities._docs.docs_collection_sources import (
        FlextInfraUtilitiesDocsCollectionSources,
    )
    from flext_infra._utilities._docs.docs_contract import (
        FlextInfraUtilitiesDocsContract,
    )
    from flext_infra._utilities._docs.docs_fix import FlextInfraUtilitiesDocsFix
    from flext_infra._utilities._docs.docs_generate import (
        FlextInfraUtilitiesDocsGenerate,
    )
    from flext_infra._utilities._docs.docs_render import FlextInfraUtilitiesDocsRender
    from flext_infra._utilities._docs.docs_scope import FlextInfraUtilitiesDocsScope
    from flext_infra._utilities._docs.docs_scope_projects import (
        FlextInfraUtilitiesDocsScopeProjectsMixin,
    )
    from flext_infra._utilities._docs.docs_validate import (
        FlextInfraUtilitiesDocsValidate,
    )
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
    from flext_infra._utilities._docs.scope_build import (
        FlextInfraUtilitiesDocsScopeBuild,
    )
    from flext_infra._utilities._docs.scope_paths import (
        FlextInfraUtilitiesDocsScopePaths,
    )
    from flext_infra._utilities._docs.scope_policy import (
        FlextInfraUtilitiesDocsScopePolicy,
    )
    from flext_infra._utilities._docs.scope_selection import (
        FlextInfraUtilitiesDocsScopeSelection,
    )
    from flext_infra._utilities._docs.scope_state import (
        FlextInfraUtilitiesDocsScopeState,
    )

__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectors",
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
    "FlextInfraUtilitiesDocsScopeProjectsMixin",
    "FlextInfraUtilitiesDocsScopeSelection",
    "FlextInfraUtilitiesDocsScopeState",
    "FlextInfraUtilitiesDocsValidate",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesDocsApi": ".docs_api",
        "FlextInfraUtilitiesDocsAudit": ".docs_audit",
        "FlextInfraUtilitiesDocsAuditDetectors": ".audit_detectors",
        "FlextInfraUtilitiesDocsBuild": ".docs_build",
        "FlextInfraUtilitiesDocsCollection": ".docs_collection",
        "FlextInfraUtilitiesDocsCollectionSources": ".docs_collection_sources",
        "FlextInfraUtilitiesDocsCommandContract": ".command_contract",
        "FlextInfraUtilitiesDocsContract": ".docs_contract",
        "FlextInfraUtilitiesDocsFix": ".docs_fix",
        "FlextInfraUtilitiesDocsGenerate": ".docs_generate",
        "FlextInfraUtilitiesDocsGeneratePlan": ".generate_plan",
        "FlextInfraUtilitiesDocsGenerateProject": ".generate_project",
        "FlextInfraUtilitiesDocsGenerateRoot": ".generate_root",
        "FlextInfraUtilitiesDocsGenerateSources": ".generate_sources",
        "FlextInfraUtilitiesDocsGithubLinks": ".github_links",
        "FlextInfraUtilitiesDocsGuides": ".guides",
        "FlextInfraUtilitiesDocsRender": ".docs_render",
        "FlextInfraUtilitiesDocsScope": ".docs_scope",
        "FlextInfraUtilitiesDocsScopeBuild": ".scope_build",
        "FlextInfraUtilitiesDocsScopePaths": ".scope_paths",
        "FlextInfraUtilitiesDocsScopePolicy": ".scope_policy",
        "FlextInfraUtilitiesDocsScopeProjectsMixin": ".docs_scope_projects",
        "FlextInfraUtilitiesDocsScopeSelection": ".scope_selection",
        "FlextInfraUtilitiesDocsScopeState": ".scope_state",
        "FlextInfraUtilitiesDocsValidate": ".docs_validate",
    }),
    public_exports=__all__,
)
