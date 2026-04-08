# AUTO-GENERATED FILE — Regenerate with: make gen
"""Services package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCodegenConsolidator": ".consolidator",
    "FlextInfraCodegenDeduplicator": ".deduplicator",
    "FlextInfraCodegenPipeline": ".pipeline",
    "FlextInfraServiceBasemkMixin": ".basemk",
    "FlextInfraServiceCheckMixin": ".check",
    "FlextInfraServiceCodegenMixin": ".codegen",
    "FlextInfraServiceDepsMixin": ".deps",
    "FlextInfraServiceDocsMixin": ".docs",
    "FlextInfraServiceGithubMixin": ".github",
    "FlextInfraServiceRefactorMixin": ".refactor",
    "FlextInfraServiceReleaseMixin": ".release",
    "FlextInfraServiceValidateMixin": ".validate",
    "FlextInfraServiceWorkspaceMixin": ".workspace",
    "FlextInfraToml": ".toml_engine",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
