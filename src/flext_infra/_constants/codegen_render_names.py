"""Template name constants for the codegen package."""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsCodegenRenderNames:
    """Template filename constants consumed by codegen renderers."""

    TEMPLATE_UNIT_MANIFEST: Final[str] = "lazy_init_unit_manifest.py.j2"
    "Per-project-root ``__unit__.py`` lazy-import manifest (root SSOT)."
    TEMPLATE_ROOT_THIN: Final[str] = "lazy_init_root_thin.py.j2"
    "Thin project-root ``__init__.py`` consuming only ``__unit__.py``."
    TEMPLATE_VERSION_FILE: Final[str] = "version_file.py.j2"
    "Per-project ``__version__.py`` template."
    TEMPLATE_MKDOCS_PROJECT: Final[str] = "mkdocs_project.yml.j2"
    "Per-project ``mkdocs.yml`` template."
    TEMPLATE_MKDOCS_ROOT: Final[str] = "mkdocs_root.yml.j2"
    "Workspace-root ``mkdocs.yml`` template."


__all__: list[str] = ["FlextInfraConstantsCodegenRenderNames"]
