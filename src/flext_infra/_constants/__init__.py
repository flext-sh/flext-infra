# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra. Constants package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".adapters": ("FlextInfraConstantsAdapters",),
    ".base": ("FlextInfraConstantsBase",),
    ".census": ("FlextInfraConstantsCensus",),
    ".check": ("FlextInfraConstantsCheck",),
    ".cli": ("FlextInfraConstantsCli",),
    ".codegen": ("FlextInfraConstantsCodegen",),
    ".codegen_detection": ("FlextInfraConstantsCodegenDetection",),
    ".codegen_lazy": ("FlextInfraConstantsCodegenLazy",),
    ".codegen_project": ("FlextInfraConstantsCodegenProject",),
    ".codegen_render_names": ("FlextInfraConstantsCodegenRenderNames",),
    ".deps": ("FlextInfraConstantsDeps",),
    ".detectors": ("FlextInfraConstantsDetectors",),
    ".docs": ("FlextInfraConstantsDocs",),
    ".github": ("FlextInfraConstantsGithub",),
    ".make": ("FlextInfraConstantsMake",),
    ".namespace": ("FlextInfraConstantsNamespace",),
    ".refactor": ("FlextInfraConstantsRefactor",),
    ".release": ("FlextInfraConstantsRelease",),
    ".rope": ("FlextInfraConstantsRope",),
    ".source_code": ("FlextInfraConstantsSourceCode",),
    ".validate": ("FlextInfraConstantsSharedInfra",),
    ".workspace": ("FlextInfraConstantsWorkspace",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
