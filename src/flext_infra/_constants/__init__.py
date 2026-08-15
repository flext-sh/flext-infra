# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .adapters import FlextInfraConstantsAdapters
    from .base import FlextInfraConstantsBase
    from .basemk import FlextInfraConstantsBasemk
    from .census import FlextInfraConstantsCensus
    from .check import FlextInfraConstantsCheck
    from .cli import FlextInfraConstantsCli
    from .codegen import FlextInfraConstantsCodegen
    from .codegen_detection import FlextInfraConstantsCodegenDetection
    from .codegen_lazy import FlextInfraConstantsCodegenLazy
    from .codegen_project import FlextInfraConstantsCodegenProject
    from .codegen_render_names import FlextInfraConstantsCodegenRenderNames
    from .deps import FlextInfraConstantsDeps
    from .detectors import FlextInfraConstantsDetectors
    from .docs import FlextInfraConstantsDocs
    from .git import FlextInfraConstantsGit
    from .github import FlextInfraConstantsGithub
    from .make import FlextInfraConstantsMake
    from .namespace import FlextInfraConstantsNamespace
    from .refactor import FlextInfraConstantsRefactor
    from .release import FlextInfraConstantsRelease
    from .rope import FlextInfraConstantsRope
    from .source_code import FlextInfraConstantsSourceCode
    from .validate import FlextInfraConstantsSharedInfra
    from .workspace import FlextInfraConstantsWorkspace

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".adapters": ("FlextInfraConstantsAdapters",),
    ".base": ("FlextInfraConstantsBase",),
    ".basemk": ("FlextInfraConstantsBasemk",),
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
    ".git": ("FlextInfraConstantsGit",),
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

__all__: tuple[str, ...] = (
    "FlextInfraConstantsAdapters",
    "FlextInfraConstantsBase",
    "FlextInfraConstantsBasemk",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCheck",
    "FlextInfraConstantsCli",
    "FlextInfraConstantsCodegen",
    "FlextInfraConstantsCodegenDetection",
    "FlextInfraConstantsCodegenLazy",
    "FlextInfraConstantsCodegenProject",
    "FlextInfraConstantsCodegenRenderNames",
    "FlextInfraConstantsDeps",
    "FlextInfraConstantsDetectors",
    "FlextInfraConstantsDocs",
    "FlextInfraConstantsGit",
    "FlextInfraConstantsGithub",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsNamespace",
    "FlextInfraConstantsRefactor",
    "FlextInfraConstantsRelease",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSharedInfra",
    "FlextInfraConstantsSourceCode",
    "FlextInfraConstantsWorkspace",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
