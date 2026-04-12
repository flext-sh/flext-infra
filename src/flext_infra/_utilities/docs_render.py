"""Reusable docs rendering helpers exposed through ``u.Infra``."""

from __future__ import annotations

from typing import TypeIs

from flext_infra import c, m, t


class FlextInfraUtilitiesDocsRender:
    """Rendering helpers for generated docs content."""

    @staticmethod
    def _is_object_list(
        value: t.Infra.InfraValue | None,
    ) -> TypeIs[t.MutableSequenceOf[t.Infra.InfraValue]]:
        """Type guard: narrow one infra value to a mutable sequence."""
        return isinstance(value, list)

    @staticmethod
    def _string_list(
        data: t.Infra.ContainerDict,
        key: str,
    ) -> t.SequenceOf[str]:
        """Return one contract field as a normalized string sequence."""
        value = data.get(key)
        if not FlextInfraUtilitiesDocsRender._is_object_list(value):
            return []
        return [str(entry) for entry in value]

    @staticmethod
    def _preview(values: t.SequenceOf[str], *, limit: int = 6) -> str:
        """Render one compact preview list with overflow summary."""
        normalized = [value for value in values if value]
        if not normalized:
            return "_none_"
        preview = ", ".join(f"`{value}`" for value in normalized[:limit])
        remaining = len(normalized) - limit
        return f"{preview} (+{remaining} more)" if remaining > 0 else preview

    @staticmethod
    def _escape_table_cell(value: str) -> str:
        """Escape Markdown table separators in one cell."""
        return value.replace("|", "\\|").strip()

    @staticmethod
    def _module_relative_doc_path(
        package_name: str,
        module_name: str,
    ) -> str:
        """Return the generated relative path for one module page."""
        relative = module_name.removeprefix(f"{package_name}.").replace(".", "/")
        return f"{relative}.md"

    @staticmethod
    def _exclude_plugin_lines(data: t.Infra.ContainerDict) -> t.SequenceOf[str]:
        """Render optional ``mkdocs-exclude`` plugin lines."""
        patterns = FlextInfraUtilitiesDocsRender._string_list(data, "exclude_docs")
        if not patterns:
            return []
        return [
            "  - exclude:",
            "      glob:",
            *[f"        - {pattern}" for pattern in patterns],
        ]

    @staticmethod
    def _exclude_docs_lines(data: t.Infra.ContainerDict) -> t.SequenceOf[str]:
        """Render optional native ``exclude_docs`` lines for early MkDocs filtering."""
        patterns = FlextInfraUtilitiesDocsRender._string_list(data, "exclude_docs")
        if not patterns:
            return []
        return [
            "exclude_docs: |",
            *[f"  {pattern}" for pattern in patterns],
            "",
        ]

    @staticmethod
    def docs_directive_page(title: str, dotted_path: str) -> str:
        """Return a mkdocstrings page for a module path."""
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {title}",
            "",
            f"::: {dotted_path}",
            "    options:",
            "      show_root_heading: true",
            "      show_root_full_path: false",
            "      show_source: false",
            "",
        ])

    @staticmethod
    def docs_project_index(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
    ) -> str:
        """Return the standard project docs landing page."""
        data = contract
        aliases = FlextInfraUtilitiesDocsRender._string_list(data, "aliases")
        facades = FlextInfraUtilitiesDocsRender._string_list(data, "facades")
        module_exports = FlextInfraUtilitiesDocsRender._string_list(
            data,
            "module_exports",
        )
        public_symbols = FlextInfraUtilitiesDocsRender._string_list(
            data,
            "public_symbols",
        )
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name} Documentation",
            "",
            f"- Version: `{str(data.get('version', '')).strip() or 'unknown'}`",
            f"- Project class: `{scope.project_class}`",
            f"- Package: `{scope.package_name}`",
            f"- Description: {str(data.get('description', '')).strip() or '_not declared_'}",
            "",
            "This project portal is generated from `pyproject.toml`, package exports, and real docstrings.",
            "",
            "## Start Here",
            "",
            "- [Guides](guides/README.md)",
            "- [API Reference](api-reference/README.md)",
            "- [Generated API Overview](api-reference/generated/overview.md)",
            "- [Generated Module Index](api-reference/generated/modules/index.md)",
            "",
            "## Public Surface Summary",
            "",
            f"- Primary facades: {FlextInfraUtilitiesDocsRender._preview(facades)}",
            f"- Alias namespaces: {FlextInfraUtilitiesDocsRender._preview(aliases, limit=11)}",
            f"- Public symbol exports: `{len(public_symbols)}`",
            f"- Exported module shortcuts: {FlextInfraUtilitiesDocsRender._preview(module_exports)}",
            "",
        ])

    @staticmethod
    def docs_guides_index(scope: m.Infra.DocScope) -> str:
        """Return a minimal guides index for projects missing one."""
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name} Guides",
            "",
            "Curated operational guides live here. Keep API behavior in generated reference pages sourced from code and docstrings.",
            "",
            "- [Back to project docs](../index.md)",
            "- [API Reference](../api-reference/README.md)",
            "",
        ])

    @staticmethod
    def docs_api_readme(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
    ) -> str:
        """Return the standard API readme for a project."""
        data = contract
        facades = FlextInfraUtilitiesDocsRender._string_list(data, "facades")
        modules = FlextInfraUtilitiesDocsRender._string_list(data, "modules")
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name} API Reference",
            "",
            "This section is generated from public exports and real docstrings.",
            "",
            "## Source of Truth",
            "",
            "1. `pyproject.toml` metadata",
            f"2. `src/{scope.package_name}/__init__.py` exports",
            "3. Module docstrings",
            "4. Class and function docstrings",
            "",
            "## Generated Pages",
            "",
            "- [Overview](generated/overview.md)",
            "- [Public API](generated/public-api.md)",
            "- [Module Index](generated/modules/index.md)",
            "",
            "## Surface Summary",
            "",
            f"- Primary facades: {FlextInfraUtilitiesDocsRender._preview(facades)}",
            f"- Generated module pages: `{len(modules)}`",
            "",
            "- [Back to project docs](../index.md)",
            "",
        ])

    @staticmethod
    def docs_project_mkdocs(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
        modules: t.SequenceOf[str],
    ) -> str:
        """Return the managed mkdocs.yml for a project scope."""
        _ = modules
        data = contract
        site_title = str(data.get("site_title", "")).strip() or scope.name
        site_url = str(data.get("site_url", "")).strip() or c.Infra.GITHUB_REPO_URL
        repo_url = str(data.get("repo_url", "")).strip() or c.Infra.GITHUB_REPO_URL
        return "\n".join([
            "# AUTO-GENERATED — DO NOT EDIT MANUALLY",
            f"site_name: {site_title} Documentation",
            f"site_description: Generated documentation for {site_title}",
            f"site_url: {site_url}",
            f"repo_name: {c.Infra.GITHUB_REPO_NAME}",
            f"repo_url: {repo_url}",
            f"edit_uri: edit/main/{scope.name}/",
            "docs_dir: docs",
            "site_dir: .reports/docs/site",
            "",
            *FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            "theme:",
            "  name: material",
            "",
            "plugins:",
            "  - search",
            *FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            "  - autorefs",
            "  - section-index",
            "  - mkdocstrings:",
            "      handlers:",
            "        python:",
            "          paths:",
            "            - src",
            "          docstring_style: auto",
            "          docstring_options:",
            "            warnings: false",
            "            warn_unknown_params: false",
            "            warn_missing_types: false",
            "          options:",
            "            show_root_heading: true",
            "            show_root_full_path: false",
            "            show_source: false",
            "",
            "nav:",
            "  - Home: index.md",
            "  - Guides: guides/README.md",
            "  - API Reference: api-reference/README.md",
            "",
            "validation:",
            "  omitted_files: ignore",
            "  absolute_links: ignore",
            "  unrecognized_links: ignore",
            "",
        ])

    @staticmethod
    def docs_overview_page(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
    ) -> str:
        """Return the generated overview page for a project API."""
        data = contract
        aliases = FlextInfraUtilitiesDocsRender._preview(
            FlextInfraUtilitiesDocsRender._string_list(data, "aliases"),
            limit=11,
        )
        exports = FlextInfraUtilitiesDocsRender._preview(
            FlextInfraUtilitiesDocsRender._string_list(data, "public_symbols"),
            limit=10,
        )
        facades = FlextInfraUtilitiesDocsRender._preview(
            FlextInfraUtilitiesDocsRender._string_list(data, "facades"),
            limit=8,
        )
        module_exports = FlextInfraUtilitiesDocsRender._preview(
            FlextInfraUtilitiesDocsRender._string_list(data, "module_exports"),
            limit=8,
        )
        modules = FlextInfraUtilitiesDocsRender._string_list(data, "modules")
        keywords = FlextInfraUtilitiesDocsRender._preview(
            FlextInfraUtilitiesDocsRender._string_list(data, "keywords"),
            limit=8,
        )
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {(data.get('site_title', '') or scope.name)} API Overview",
            "",
            f"- Package: `{scope.package_name}`",
            f"- Version: `{data.get('version', '')}`",
            f"- Description: {data.get('description', '') or '_not declared_'}",
            f"- Project class: `{scope.project_class}`",
            f"- Keywords: {keywords}",
            f"- Main facades: {facades}",
            f"- Alias exports: {aliases}",
            f"- Public symbol exports: {exports}",
            f"- Exported module shortcuts: {module_exports}",
            f"- Generated module pages: `{len(modules)}`",
            "",
            "## Next Pages",
            "",
            "- [Public API](public-api.md)",
            "- [Module Index](modules/index.md)",
            "",
        ])

    @staticmethod
    def docs_modules_index(
        scope: m.Infra.DocScope,
        modules: t.SequenceOf[str],
    ) -> str:
        """Return the generated module index page for one project."""
        lines: t.MutableSequenceOf[str] = [
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name} Module Index",
            "",
            "These pages are generated from public modules and their docstrings.",
            "",
        ]
        if not modules:
            lines.extend(["_No public modules discovered._", ""])
            return "\n".join(lines)
        for module_name in modules:
            relative_path = FlextInfraUtilitiesDocsRender._module_relative_doc_path(
                scope.package_name,
                module_name,
            )
            lines.append(f"- [{module_name}]({relative_path})")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def docs_root_mkdocs(contract: t.Infra.ContainerDict) -> str:
        """Return the managed mkdocs.yml for the workspace root."""
        data = contract
        site_title = str(data.get("site_title", "")).strip() or "FLEXT Workspace"
        site_url = str(data.get("site_url", "")).strip() or c.Infra.GITHUB_REPO_URL
        repo_url = str(data.get("repo_url", "")).strip() or c.Infra.GITHUB_REPO_URL
        return "\n".join([
            "# AUTO-GENERATED — DO NOT EDIT MANUALLY",
            f"site_name: {site_title}",
            "site_description: Workspace documentation generated from code and curated root docs",
            f"site_url: {site_url}",
            f"repo_name: {c.Infra.GITHUB_REPO_NAME}",
            f"repo_url: {repo_url}",
            "docs_dir: docs",
            "site_dir: .reports/docs/site",
            "",
            *FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            "theme:",
            "  name: material",
            "",
            "plugins:",
            "  - search",
            *FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            "  - autorefs",
            "  - section-index",
            "  - mkdocstrings:",
            "      handlers:",
            "        python:",
            "          docstring_style: auto",
            "          docstring_options:",
            "            warnings: false",
            "            warn_unknown_params: false",
            "            warn_missing_types: false",
            "          options:",
            "            show_root_heading: true",
            "            show_root_full_path: false",
            "            show_source: false",
            "",
            "nav:",
            "  - Home: index.md",
            "  - Architecture: architecture/README.md",
            "  - Guides: guides/README.md",
            "  - Projects: projects/README.md",
            "  - API Reference: api-reference/README.md",
            "  - API Overview: api-reference/generated/overview.md",
            "  - Project Catalog: projects/generated/catalog.md",
            "",
            "validation:",
            "  omitted_files: ignore",
            "  absolute_links: ignore",
            "  unrecognized_links: ignore",
            "",
        ])

    @staticmethod
    def docs_root_overview_page(
        contract: t.Infra.ContainerDict,
        *,
        project_count: int,
        class_counts: t.MappingKV[str, int],
    ) -> str:
        """Return the generated root API overview page."""
        data = contract
        classes = (
            ", ".join(
                f"`{name}`={count}" for name, count in sorted(class_counts.items())
            )
            or "_none_"
        )
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {str(data.get('site_title', '')).strip() or 'FLEXT Workspace'} API Overview",
            "",
            f"- Version: `{str(data.get('version', '')).strip() or 'unknown'}`",
            f"- Description: {str(data.get('description', '')).strip() or '_not declared_'}",
            f"- Governed projects: `{project_count}`",
            f"- Project classes: {classes}",
            "",
            "Generated from workspace discovery, `pyproject.toml`, public exports, and docstrings.",
            "",
        ])

    @staticmethod
    def docs_project_catalog_page(entries: t.SequenceOf[t.StrMapping]) -> str:
        """Return the generated workspace project catalog page."""
        rows = [
            "| "
            + " | ".join([
                f"[{entry['name']}]({entry['api_page']})",
                FlextInfraUtilitiesDocsRender._escape_table_cell(
                    entry["project_class"]
                ),
                f"`{entry['package_name']}`",
                FlextInfraUtilitiesDocsRender._escape_table_cell(
                    entry["description"] or "_not declared_"
                ),
            ])
            + " |"
            for entry in entries
        ]
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            "# FLEXT Project Catalog",
            "",
            "Project links resolve to the generated root API reference for each governed FLEXT package.",
            "",
            "| project | class | package | description |",
            "|---|---|---|---|",
            *rows,
            "",
        ])


__all__: list[str] = ["FlextInfraUtilitiesDocsRender"]
