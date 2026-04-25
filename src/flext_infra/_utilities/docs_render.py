"""Reusable docs rendering helpers exposed through ``u.Infra``."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, m, t


class FlextInfraUtilitiesDocsRender:
    """Rendering helpers for generated docs content."""

    @staticmethod
    def _is_object_list(
        value: t.Infra.InfraValue | None,
    ) -> bool:
        """Type guard: narrow one infra value to a mutable sequence."""
        return isinstance(value, list)

    @staticmethod
    def _string_list(
        data: t.Infra.ContainerDict,
        key: str,
    ) -> t.SequenceOf[str]:
        """Return one contract field as a normalized string sequence."""
        value = data.get(key)
        if not isinstance(value, list):
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

    _LINK_PREFIX_DOCS_INDEX: ClassVar[str] = "../../.."
    """Relative path from ``<project>/docs/index.md`` to workspace root."""

    _LINK_PREFIX_README: ClassVar[str] = ".."
    """Relative path from ``<project>/README.md`` to workspace root."""

    @staticmethod
    def _public_surface_lines(data: t.Infra.ContainerDict) -> t.SequenceOf[str]:
        """Return the four-bullet public-surface summary used on every project page."""
        aliases = FlextInfraUtilitiesDocsRender._string_list(data, "aliases")
        facades = FlextInfraUtilitiesDocsRender._string_list(data, "facades")
        module_exports = FlextInfraUtilitiesDocsRender._string_list(
            data, "module_exports"
        )
        public_symbols = FlextInfraUtilitiesDocsRender._string_list(
            data, "public_symbols"
        )
        return [
            f"- Primary facades: {FlextInfraUtilitiesDocsRender._preview(facades)}",
            f"- Alias namespaces: {FlextInfraUtilitiesDocsRender._preview(aliases, limit=11)}",
            f"- Public symbol exports: `{len(public_symbols)}`",
            f"- Exported module shortcuts: {FlextInfraUtilitiesDocsRender._preview(module_exports)}",
        ]

    @staticmethod
    def _collection_rules_lines(
        scope: m.Infra.DocScope,
        *,
        link_prefix: str,
    ) -> t.SequenceOf[str]:
        """Return the canonical Collection Rules section (used by index + readme)."""
        return [
            "## Collection Rules (regras de coletas)",
            "",
            "Required pre-work before changing this project (per AGENTS.md §9):",
            "",
            f"1. Read [`/flext/AGENTS.md`]({link_prefix}/AGENTS.md) (governance) and this project's `pyproject.toml`.",
            f"2. Confirm parent MRO chain via `pyproject.toml` `dependencies` filtered by `flext-*` (excluding `{scope.name}` self).",
            "3. Verify Scope: `cd <project> && scope status` (re-bootstrap per `flext-scope-bootstrap` if absent).",
            f"4. Load skills relevant to the change scope from [`/flext/.agents/skills/`]({link_prefix}/.agents/skills/) (start with `flext-mro-namespace-rules`, `flext-import-rules`, `flext-patterns`).",
            "5. Confirm the canonical zero-debt baseline:",
            "    - `make check` exits 0",
            "    - `make val VALIDATE_SCOPE=project` exits 0",
            "    - `make docs DOCS_PHASE=audit` reports zero issues",
            f"6. Cross-check the c/p/t/m/u slot registry in [`flext-mro-namespace-rules`]({link_prefix}/.agents/skills/flext-mro-namespace-rules/SKILL.md) to confirm this project's owned slots before adding/renaming any symbol.",
        ]

    @staticmethod
    def _quality_gates_lines() -> t.SequenceOf[str]:
        """Return the canonical Quality Gates section (identical for every page)."""
        return [
            "## Quality Gates",
            "",
            "- `make check` — Lint suite (ruff, pyrefly, mypy, pyright per project).",
            "- `make test` — Pytest with project coverage threshold from `pyproject.toml`.",
            "- `make val VALIDATE_SCOPE=project` — Validation gates (complexity, docstring, namespace).",
            "- `make docs DOCS_PHASE=audit` — Docs audit (broken links, stale symbols, missing docstrings).",
            "- `make docs DOCS_PHASE=build` — Build mkdocs HTML output to `.reports/docs/site/`.",
        ]

    @staticmethod
    def _governance_pointer_lines(*, link_prefix: str) -> t.SequenceOf[str]:
        """Return the canonical Governance Pointer section."""
        return [
            "## Governance Pointer",
            "",
            f"- Canonical engineering law: [`/flext/AGENTS.md`]({link_prefix}/AGENTS.md).",
            f"- Project skills index: [`/flext/.agents/skills/`]({link_prefix}/.agents/skills/).",
            f"- Workspace onboarding: [`/flext/docs/guides/onboarding.md`]({link_prefix}/docs/guides/onboarding.md).",
        ]

    @staticmethod
    def docs_project_index(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
    ) -> str:
        """Return the standard ``<project>/docs/index.md`` landing page."""
        data = contract
        version = str(data.get("version", "")).strip() or "unknown"
        description = str(data.get("description", "")).strip() or "_not declared_"
        link_prefix = FlextInfraUtilitiesDocsRender._LINK_PREFIX_DOCS_INDEX
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name} Documentation",
            "",
            f"- Version: `{version}`",
            f"- Project class: `{scope.project_class}`",
            f"- Package: `{scope.package_name}`",
            f"- Description: {description}",
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
            *FlextInfraUtilitiesDocsRender._public_surface_lines(data),
            "",
            *FlextInfraUtilitiesDocsRender._collection_rules_lines(
                scope, link_prefix=link_prefix
            ),
            "",
            *FlextInfraUtilitiesDocsRender._quality_gates_lines(),
            "",
            *FlextInfraUtilitiesDocsRender._governance_pointer_lines(
                link_prefix=link_prefix
            ),
            "",
        ])

    @staticmethod
    def docs_project_readme(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
    ) -> str:
        """Return the canonical ``<project>/README.md`` (8-section structure).

        Auto-generated from ``pyproject.toml`` + package exports + the canonical
        FLEXT readme template (see ``readme-standardization`` skill). Output is
        fully deterministic — running the generator twice produces byte-identical
        content. Shares Collection Rules, Quality Gates, and Governance Pointer
        sections with ``docs_project_index`` via private helpers (no duplication).
        """
        data = contract
        version = str(data.get("version", "")).strip() or "unknown"
        description = str(data.get("description", "")).strip() or "_not declared_"
        facades = FlextInfraUtilitiesDocsRender._string_list(data, "facades")
        link_prefix = FlextInfraUtilitiesDocsRender._LINK_PREFIX_README
        return "\n".join([
            c.Infra.GENERATED_HEADER,
            "",
            f"# {scope.name}",
            "",
            f"**Version**: `{version}` | **Python**: 3.13+ | **Project class**: `{scope.project_class}`",
            "",
            "## Purpose",
            "",
            description,
            "",
            "## Module Map",
            "",
            *FlextInfraUtilitiesDocsRender._public_surface_lines(data),
            "",
            *FlextInfraUtilitiesDocsRender._collection_rules_lines(
                scope, link_prefix=link_prefix
            ),
            "",
            "## Operation Flow",
            "",
            "- Public surface: see [`docs/index.md`](docs/index.md) and [`docs/api-reference/README.md`](docs/api-reference/README.md).",
            "- Generated module overview: [`docs/api-reference/generated/overview.md`](docs/api-reference/generated/overview.md).",
            "- Settings env prefix: see project `pyproject.toml` `[tool.flext]` and `FlextSettings` ConfigDict.",
            "",
            "## Integration Points",
            "",
            "- Parent MRO chain: read this project's `pyproject.toml` `dependencies` array filtered by `flext-*`. The MRO cascade is encoded in the inheritance lists of the facade classes listed under Module Map above.",
            f"- Public extensions exposed by this project: {FlextInfraUtilitiesDocsRender._preview(facades)}.",
            "- Library abstraction boundaries: see AGENTS.md §2.7.",
            "",
            *FlextInfraUtilitiesDocsRender._quality_gates_lines(),
            "",
            *FlextInfraUtilitiesDocsRender._governance_pointer_lines(
                link_prefix=link_prefix
            ),
            "- Full project portal: [`docs/index.md`](docs/index.md).",
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
    def _render_block(lines: t.SequenceOf[str]) -> str:
        """Pre-format a line sequence into a newline-terminated j2-safe block.

        Returns ``""`` when ``lines`` is empty so the template's substitution
        leaves no trailing artifacts. Otherwise joins with newlines and adds
        one trailing newline so the next macro sits on a fresh line.
        """
        return "\n".join([*lines, ""]) if lines else ""

    @staticmethod
    def _mkdocstrings_paths_block(paths: t.SequenceOf[str]) -> str:
        """Pre-format the optional mkdocstrings ``paths`` sub-block."""
        if not paths:
            return ""
        body = ["          paths:", *(f"            - {path}" for path in paths)]
        return "\n".join([*body, ""])

    @staticmethod
    def docs_project_mkdocs(
        scope: m.Infra.DocScope,
        contract: t.Infra.ContainerDict,
        modules: t.SequenceOf[str],
    ) -> str:
        """Return the managed mkdocs.yml for a project scope.

        Renders the canonical ``mkdocs_project.yml.j2`` template via
        ``FlextInfraCodegenGeneration.get_template`` — single SSOT j2 path
        shared with the workspace-root variant; theme + plugins + validation
        macros live in the template, not Python.
        """
        _ = modules
        data = contract
        from flext_infra import FlextInfraCodegenGeneration  # noqa: PLC0415

        template = FlextInfraCodegenGeneration.get_template(
            c.Infra.TEMPLATE_MKDOCS_PROJECT,
        )
        return template.render(
            site_title=str(data.get("site_title", "")).strip() or scope.name,
            site_url=str(data.get("site_url", "")).strip() or c.Infra.GITHUB_REPO_URL,
            repo_url=str(data.get("repo_url", "")).strip() or c.Infra.GITHUB_REPO_URL,
            repo_name=c.Infra.GITHUB_REPO_NAME,
            scope_name=scope.name,
            exclude_docs_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            ),
            exclude_plugin_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            ),
            mkdocstrings_paths_block=FlextInfraUtilitiesDocsRender._mkdocstrings_paths_block(
                ("src",),
            ),
        )

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
        """Return the managed mkdocs.yml for the workspace root.

        Renders the canonical ``mkdocs_root.yml.j2`` template via
        ``FlextInfraCodegenGeneration.get_template`` — single SSOT j2 path
        shared with the per-project variant.
        """
        data = contract
        from flext_infra import FlextInfraCodegenGeneration  # noqa: PLC0415

        template = FlextInfraCodegenGeneration.get_template(
            c.Infra.TEMPLATE_MKDOCS_ROOT,
        )
        return template.render(
            site_title=(str(data.get("site_title", "")).strip() or "FLEXT Workspace"),
            site_url=str(data.get("site_url", "")).strip() or c.Infra.GITHUB_REPO_URL,
            repo_url=str(data.get("repo_url", "")).strip() or c.Infra.GITHUB_REPO_URL,
            repo_name=c.Infra.GITHUB_REPO_NAME,
            exclude_docs_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            ),
            exclude_plugin_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            ),
            mkdocstrings_paths_block=FlextInfraUtilitiesDocsRender._mkdocstrings_paths_block(
                (),
            ),
        )

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
