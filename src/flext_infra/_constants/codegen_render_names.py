"""Template name constants for the codegen package."""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsCodegenRenderNames:
    """Template filename constants consumed by codegen renderers."""

    # NOTE (multi-agent, mro-wkii.17.26 / agent: codex): one inline public-root
    # template plus its PEP 561 stub and one static subpackage template replace
    # __unit__ sidecars while preserving analyzable lazy public exports.
    TEMPLATE_ROOT_INIT: Final[str] = "lazy_init_root.py.j2"
    "Public project-root ``__init__.py`` with an inline lazy export map."
    TEMPLATE_ROOT_INIT_STUB: Final[str] = "lazy_init_root.pyi.j2"
    "PEP 561 declarations matching the public root lazy export map."
    TEMPLATE_STATIC_INIT: Final[str] = "static_package_init.py.j2"
    "Non-root package ``__init__.py`` with explicit static reexports."
    TEMPLATE_VERSION_FILE: Final[str] = "version_file.py.j2"
    "Per-project ``__version__.py`` template."
    TEMPLATE_MKDOCS_PROJECT: Final[str] = "mkdocs_project.yml.j2"
    "Per-project ``mkdocs.yml`` template."
    TEMPLATE_MKDOCS_ROOT: Final[str] = "mkdocs_root.yml.j2"
    "Workspace-root ``mkdocs.yml`` template."


__all__: list[str] = ["FlextInfraConstantsCodegenRenderNames"]
