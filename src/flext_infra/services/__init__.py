# AUTO-GENERATED FILE — Regenerate with: make gen
"""Services package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".basemk": ("FlextInfraServiceBasemkMixin",),
        ".check": ("FlextInfraServiceCheckMixin",),
        ".cli_base": ("FlextInfraServiceCliRunnerMixin",),
        ".codegen": ("FlextInfraServiceCodegenMixin",),
        ".consolidator": ("FlextInfraCodegenConsolidator",),
        ".deps": ("FlextInfraServiceDepsMixin",),
        ".github": ("FlextInfraServiceGithubMixin",),
        ".pipeline": ("FlextInfraCodegenPipeline",),
        ".refactor": ("FlextInfraServiceRefactorMixin",),
        ".release": ("FlextInfraServiceReleaseMixin",),
        ".toml_engine": ("FlextInfraToml",),
        ".validate": ("FlextInfraServiceValidateMixin",),
        ".workspace": ("FlextInfraServiceWorkspaceMixin",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
