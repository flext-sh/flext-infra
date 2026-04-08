# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Services package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCodegenConsolidator": (
        "flext_infra.services.consolidator",
        "FlextInfraCodegenConsolidator",
    ),
    "FlextInfraCodegenDeduplicator": (
        "flext_infra.services.deduplicator",
        "FlextInfraCodegenDeduplicator",
    ),
    "FlextInfraCodegenPipeline": (
        "flext_infra.services.pipeline",
        "FlextInfraCodegenPipeline",
    ),
    "FlextInfraServiceBasemkMixin": (
        "flext_infra.services.basemk",
        "FlextInfraServiceBasemkMixin",
    ),
    "FlextInfraServiceCheckMixin": (
        "flext_infra.services.check",
        "FlextInfraServiceCheckMixin",
    ),
    "FlextInfraServiceCodegenMixin": (
        "flext_infra.services.codegen",
        "FlextInfraServiceCodegenMixin",
    ),
    "FlextInfraServiceDepsMixin": (
        "flext_infra.services.deps",
        "FlextInfraServiceDepsMixin",
    ),
    "FlextInfraServiceDocsMixin": (
        "flext_infra.services.docs",
        "FlextInfraServiceDocsMixin",
    ),
    "FlextInfraServiceGithubMixin": (
        "flext_infra.services.github",
        "FlextInfraServiceGithubMixin",
    ),
    "FlextInfraServiceRefactorMixin": (
        "flext_infra.services.refactor",
        "FlextInfraServiceRefactorMixin",
    ),
    "FlextInfraServiceReleaseMixin": (
        "flext_infra.services.release",
        "FlextInfraServiceReleaseMixin",
    ),
    "FlextInfraServiceValidateMixin": (
        "flext_infra.services.validate",
        "FlextInfraServiceValidateMixin",
    ),
    "FlextInfraServiceWorkspaceMixin": (
        "flext_infra.services.workspace",
        "FlextInfraServiceWorkspaceMixin",
    ),
    "FlextInfraToml": ("flext_infra.services.toml_engine", "FlextInfraToml"),
    "basemk": "flext_infra.services.basemk",
    "check": "flext_infra.services.check",
    "codegen": "flext_infra.services.codegen",
    "consolidator": "flext_infra.services.consolidator",
    "deduplicator": "flext_infra.services.deduplicator",
    "deps": "flext_infra.services.deps",
    "docs": "flext_infra.services.docs",
    "github": "flext_infra.services.github",
    "pipeline": "flext_infra.services.pipeline",
    "refactor": "flext_infra.services.refactor",
    "release": "flext_infra.services.release",
    "toml_engine": "flext_infra.services.toml_engine",
    "validate": "flext_infra.services.validate",
    "workspace": "flext_infra.services.workspace",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
