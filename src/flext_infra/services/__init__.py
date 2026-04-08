# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Services package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.services.basemk as _flext_infra_services_basemk

    basemk = _flext_infra_services_basemk
    import flext_infra.services.check as _flext_infra_services_check
    from flext_infra.services.basemk import FlextInfraServiceBasemkMixin

    check = _flext_infra_services_check
    import flext_infra.services.codegen as _flext_infra_services_codegen
    from flext_infra.services.check import FlextInfraServiceCheckMixin

    codegen = _flext_infra_services_codegen
    import flext_infra.services.consolidator as _flext_infra_services_consolidator
    from flext_infra.services.codegen import FlextInfraServiceCodegenMixin

    consolidator = _flext_infra_services_consolidator
    import flext_infra.services.deduplicator as _flext_infra_services_deduplicator
    from flext_infra.services.consolidator import FlextInfraCodegenConsolidator

    deduplicator = _flext_infra_services_deduplicator
    import flext_infra.services.deps as _flext_infra_services_deps
    from flext_infra.services.deduplicator import FlextInfraCodegenDeduplicator

    deps = _flext_infra_services_deps
    import flext_infra.services.docs as _flext_infra_services_docs
    from flext_infra.services.deps import FlextInfraServiceDepsMixin

    docs = _flext_infra_services_docs
    import flext_infra.services.github as _flext_infra_services_github
    from flext_infra.services.docs import FlextInfraServiceDocsMixin

    github = _flext_infra_services_github
    import flext_infra.services.pipeline as _flext_infra_services_pipeline
    from flext_infra.services.github import FlextInfraServiceGithubMixin

    pipeline = _flext_infra_services_pipeline
    import flext_infra.services.refactor as _flext_infra_services_refactor
    from flext_infra.services.pipeline import FlextInfraCodegenPipeline

    refactor = _flext_infra_services_refactor
    import flext_infra.services.release as _flext_infra_services_release
    from flext_infra.services.refactor import FlextInfraServiceRefactorMixin

    release = _flext_infra_services_release
    import flext_infra.services.toml_engine as _flext_infra_services_toml_engine
    from flext_infra.services.release import FlextInfraServiceReleaseMixin

    toml_engine = _flext_infra_services_toml_engine
    import flext_infra.services.validate as _flext_infra_services_validate
    from flext_infra.services.toml_engine import FlextInfraToml

    validate = _flext_infra_services_validate
    import flext_infra.services.workspace as _flext_infra_services_workspace
    from flext_infra.services.validate import FlextInfraServiceValidateMixin

    workspace = _flext_infra_services_workspace
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.services.workspace import FlextInfraServiceWorkspaceMixin
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
    "d": ("flext_core.decorators", "FlextDecorators"),
    "deduplicator": "flext_infra.services.deduplicator",
    "deps": "flext_infra.services.deps",
    "docs": "flext_infra.services.docs",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "github": "flext_infra.services.github",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "pipeline": "flext_infra.services.pipeline",
    "r": ("flext_core.result", "FlextResult"),
    "refactor": "flext_infra.services.refactor",
    "release": "flext_infra.services.release",
    "s": ("flext_core.service", "FlextService"),
    "toml_engine": "flext_infra.services.toml_engine",
    "validate": "flext_infra.services.validate",
    "workspace": "flext_infra.services.workspace",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenDeduplicator",
    "FlextInfraCodegenPipeline",
    "FlextInfraServiceBasemkMixin",
    "FlextInfraServiceCheckMixin",
    "FlextInfraServiceCodegenMixin",
    "FlextInfraServiceDepsMixin",
    "FlextInfraServiceDocsMixin",
    "FlextInfraServiceGithubMixin",
    "FlextInfraServiceRefactorMixin",
    "FlextInfraServiceReleaseMixin",
    "FlextInfraServiceValidateMixin",
    "FlextInfraServiceWorkspaceMixin",
    "FlextInfraToml",
    "basemk",
    "check",
    "codegen",
    "consolidator",
    "d",
    "deduplicator",
    "deps",
    "docs",
    "e",
    "github",
    "h",
    "pipeline",
    "r",
    "refactor",
    "release",
    "s",
    "toml_engine",
    "validate",
    "workspace",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
