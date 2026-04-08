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
    "c": ("flext_core.constants", "FlextConstants"),
    "check": "flext_infra.services.check",
    "codegen": "flext_infra.services.codegen",
    "consolidator": "flext_infra.services.consolidator",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "deduplicator": "flext_infra.services.deduplicator",
    "deps": "flext_infra.services.deps",
    "docs": "flext_infra.services.docs",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "github": "flext_infra.services.github",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pipeline": "flext_infra.services.pipeline",
    "r": ("flext_core.result", "FlextResult"),
    "refactor": "flext_infra.services.refactor",
    "release": "flext_infra.services.release",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "toml_engine": "flext_infra.services.toml_engine",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "validate": "flext_infra.services.validate",
    "workspace": "flext_infra.services.workspace",
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
