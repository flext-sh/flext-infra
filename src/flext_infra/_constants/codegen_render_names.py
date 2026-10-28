"""Template name constants for the codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import ClassVar


class FlextInfraConstantsCodegenRenderNames:
    """Template filename constants consumed by codegen renderers."""

    TEMPLATE_ROOT_INIT: ClassVar[str] = "lazy_init_root.py.j2"
    "Public project-root ``__init__.py`` consuming owned lazy metadata."
    TEMPLATE_VERSION_FILE: ClassVar[str] = "version_file.py.j2"
    "Per-project ``__version__.py`` template."
    TEMPLATE_MKDOCS_PROJECT: ClassVar[str] = "mkdocs_project.yml.j2"
    "Per-project ``mkdocs.yml`` template."
    TEMPLATE_MKDOCS_ROOT: ClassVar[str] = "mkdocs_root.yml.j2"
    "Workspace ``mkdocs.yml`` template."
    TEMPLATE_DOCS_DIRECTIVE_PAGE: ClassVar[str] = "docs/directive_page.md.j2"
    "Generated mkdocstrings directive page template."
    TEMPLATE_DOCS_PROJECT_INDEX: ClassVar[str] = "docs/project_index.md.j2"
    "Generated ``<project>/docs/index.md`` landing page template."
    TEMPLATE_DOCS_PROJECT_README: ClassVar[str] = "docs/project_readme.md.j2"
    "Generated ``<project>/README.md`` page template."
    TEMPLATE_DOCS_GUIDES_INDEX: ClassVar[str] = "docs/guides_index.md.j2"
    "Generated guides index page template."
    TEMPLATE_DOCS_API_README: ClassVar[str] = "docs/api_readme.md.j2"
    "Generated project API readme page template."
    TEMPLATE_DOCS_OVERVIEW_PAGE: ClassVar[str] = "docs/overview_page.md.j2"
    "Generated project API overview page template."
    TEMPLATE_DOCS_MODULES_INDEX: ClassVar[str] = "docs/modules_index.md.j2"
    "Generated module index page template."
    TEMPLATE_DOCS_ROOT_OVERVIEW_PAGE: ClassVar[str] = "docs/root_overview_page.md.j2"
    "Generated workspace API overview page template."
    TEMPLATE_DOCS_ROOT_PROJECTS_INDEX: ClassVar[str] = "docs/root_projects_index.md.j2"
    "Generated workspace module-page index page template."
    TEMPLATE_DOCS_PROJECT_CATALOG_PAGE: ClassVar[str] = (
        "docs/project_catalog_page.md.j2"
    )
    "Generated workspace project catalog page template."


__all__: list[str] = ["FlextInfraConstantsCodegenRenderNames"]
