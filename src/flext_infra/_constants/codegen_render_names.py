"""Template name constants for the codegen package."""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsCodegenRenderNames:
    """Template filename constants consumed by codegen renderers."""

    TEMPLATE_PREAMBLE_STANDARD: Final[str] = "lazy_init_preamble_standard.py.j2"
    "Standard module preamble."
    TEMPLATE_PREAMBLE_L0: Final[str] = "lazy_init_preamble_l0.py.j2"
    "L0 typings preamble."
    TEMPLATE_BODY: Final[str] = "lazy_init_body.py.j2"
    "Middle section for generated lazy-init modules."
    TEMPLATE_GETATTR_STANDARD: Final[str] = "lazy_init_getattr_standard.py.j2"
    "Standard PEP 562 lazy export installer."
    TEMPLATE_GETATTR_L0: Final[str] = "lazy_init_getattr_l0.py.j2"
    "L0-typings lazy export installer."
    TEMPLATE_DIRECT_BOOTSTRAP: Final[str] = "lazy_init_direct_bootstrap.py.j2"
    "Direct-import bootstrap package initializer."
    TEMPLATE_FLEXT_CORE_ROOT: Final[str] = "lazy_init_flext_core_root.py.j2"
    "Canonical flext-core root package initializer."
    TEMPLATE_VERSION_FILE: Final[str] = "version_file.py.j2"
    "Per-project ``__version__.py`` template."
    TEMPLATE_MKDOCS_PROJECT: Final[str] = "mkdocs_project.yml.j2"
    "Per-project ``mkdocs.yml`` template."
    TEMPLATE_MKDOCS_ROOT: Final[str] = "mkdocs_root.yml.j2"
    "Workspace-root ``mkdocs.yml`` template."


__all__: list[str] = ["FlextInfraConstantsCodegenRenderNames"]
