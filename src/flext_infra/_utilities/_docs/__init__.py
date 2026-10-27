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
    from flext_infra._utilities._docs._docs_audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectorsMixin,
    )
    from flext_infra._utilities._docs._docs_command_contract import (
        FlextInfraUtilitiesDocsCommandContractMixin,
    )
    from flext_infra._utilities._docs._docs_generate_plan import (
        FlextInfraUtilitiesDocsGeneratePlanMixin,
    )
    from flext_infra._utilities._docs._docs_generate_project import (
        FlextInfraUtilitiesDocsGenerateProjectMixin,
    )
    from flext_infra._utilities._docs._docs_generate_root import (
        FlextInfraUtilitiesDocsGenerateRootMixin,
    )
    from flext_infra._utilities._docs._docs_generate_sources import (
        FlextInfraUtilitiesDocsGenerateSourcesMixin,
    )
    from flext_infra._utilities._docs._docs_github_links import (
        FlextInfraUtilitiesDocsGithubLinks,
    )
    from flext_infra._utilities._docs._docs_guides import (
        FlextInfraUtilitiesDocsGuidesMixin,
    )
    from flext_infra._utilities._docs._docs_scope_build import (
        FlextInfraUtilitiesDocsScopeBuildMixin,
    )
    from flext_infra._utilities._docs._docs_scope_paths import (
        FlextInfraUtilitiesDocsScopePathsMixin,
    )
    from flext_infra._utilities._docs._docs_scope_policy import (
        FlextInfraUtilitiesDocsScopePolicyMixin,
    )
    from flext_infra._utilities._docs._docs_scope_selection import (
        FlextInfraUtilitiesDocsScopeSelectionMixin,
    )
    from flext_infra._utilities._docs._docs_scope_state import (
        FlextInfraUtilitiesDocsScopeStateMixin,
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


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectorsMixin",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsCollection",
    "FlextInfraUtilitiesDocsCollectionSources",
    "FlextInfraUtilitiesDocsCommandContractMixin",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsGeneratePlanMixin",
    "FlextInfraUtilitiesDocsGenerateProjectMixin",
    "FlextInfraUtilitiesDocsGenerateRootMixin",
    "FlextInfraUtilitiesDocsGenerateSourcesMixin",
    "FlextInfraUtilitiesDocsGithubLinks",
    "FlextInfraUtilitiesDocsGuidesMixin",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsScopeBuildMixin",
    "FlextInfraUtilitiesDocsScopePathsMixin",
    "FlextInfraUtilitiesDocsScopePolicyMixin",
    "FlextInfraUtilitiesDocsScopeProjectsMixin",
    "FlextInfraUtilitiesDocsScopeSelectionMixin",
    "FlextInfraUtilitiesDocsScopeStateMixin",
    "FlextInfraUtilitiesDocsValidate",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesDocsApi": ".docs_api",
        "FlextInfraUtilitiesDocsAudit": ".docs_audit",
        "FlextInfraUtilitiesDocsAuditDetectorsMixin": "._docs_audit_detectors",
        "FlextInfraUtilitiesDocsBuild": ".docs_build",
        "FlextInfraUtilitiesDocsCollection": ".docs_collection",
        "FlextInfraUtilitiesDocsCollectionSources": ".docs_collection_sources",
        "FlextInfraUtilitiesDocsCommandContractMixin": "._docs_command_contract",
        "FlextInfraUtilitiesDocsContract": ".docs_contract",
        "FlextInfraUtilitiesDocsFix": ".docs_fix",
        "FlextInfraUtilitiesDocsGenerate": ".docs_generate",
        "FlextInfraUtilitiesDocsGeneratePlanMixin": "._docs_generate_plan",
        "FlextInfraUtilitiesDocsGenerateProjectMixin": "._docs_generate_project",
        "FlextInfraUtilitiesDocsGenerateRootMixin": "._docs_generate_root",
        "FlextInfraUtilitiesDocsGenerateSourcesMixin": "._docs_generate_sources",
        "FlextInfraUtilitiesDocsGithubLinks": "._docs_github_links",
        "FlextInfraUtilitiesDocsGuidesMixin": "._docs_guides",
        "FlextInfraUtilitiesDocsRender": ".docs_render",
        "FlextInfraUtilitiesDocsScope": ".docs_scope",
        "FlextInfraUtilitiesDocsScopeBuildMixin": "._docs_scope_build",
        "FlextInfraUtilitiesDocsScopePathsMixin": "._docs_scope_paths",
        "FlextInfraUtilitiesDocsScopePolicyMixin": "._docs_scope_policy",
        "FlextInfraUtilitiesDocsScopeProjectsMixin": ".docs_scope_projects",
        "FlextInfraUtilitiesDocsScopeSelectionMixin": "._docs_scope_selection",
        "FlextInfraUtilitiesDocsScopeStateMixin": "._docs_scope_state",
        "FlextInfraUtilitiesDocsValidate": ".docs_validate",
    }),
    public_exports=__all__,
)
