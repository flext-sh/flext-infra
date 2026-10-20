"""Reusable docs rendering helpers exposed through ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
import textwrap
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

from flext_cli import u

from flext_infra import c, config, m, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository


class FlextInfraUtilitiesDocsRender:
    """Rendering helpers for generated docs content."""

    _MIN_REPO_PARTS: ClassVar[int] = 2

    @staticmethod
    def docs_markdown_line_length(tool_config: m.Infra.ToolConfigDocument) -> int:
        """Read the same prose width used by the formatter and Markdown gate.

        Returns:
            The resulting ``int``.

        Raises:
            TypeError: If MD013 must declare the generated prose line length.
            ValueError: If MD013 line_length must be a positive integer.

        """
        rule = FlextInfraUtilitiesProjectManagedArtifacts.configuration_pairs(
            tool_config.tools.markdown.rules
        )["MD013"]
        if not isinstance(rule, dict):
            msg = "MD013 must declare the generated prose line length"
            raise TypeError(msg)
        width = rule["line_length"]
        if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
            msg = "MD013 line_length must be a positive integer"
            raise ValueError(msg)
        return width

    @staticmethod
    def _repository_name(repo_url: str) -> str:
        """Return the ``owner/repository`` identity declared by one URL.

        Returns:
            The ``owner/repository`` identity declared by one URL.

        Raises:
            ValueError: If repository URL does not identify owner/repository.

        """
        normalized = repo_url.strip().rstrip("/").removesuffix(".git")
        if not normalized:
            return c.Infra.GITHUB_REPO_NAME
        if "://" in normalized:
            path = urlsplit(normalized).path
        elif ":" in normalized and "@" in normalized.partition(":")[0]:
            path = normalized.partition(":")[2]
        else:
            path = normalized
        parts = tuple(part for part in path.split("/") if part)
        if len(parts) < FlextInfraUtilitiesDocsRender._MIN_REPO_PARTS:
            msg = f"repository URL does not identify owner/repository: {repo_url}"
            raise ValueError(msg)
        return "/".join(parts[-FlextInfraUtilitiesDocsRender._MIN_REPO_PARTS :])

    @staticmethod
    def _wrap_markdown_line(line: str, *, width: int) -> t.SequenceOf[str]:
        """Wrap one generated prose line without changing Markdown structure.

        Returns:
            The resulting ``t.SequenceOf[str]``.

        """
        if len(line) <= width:
            return (line,)
        stripped = line.lstrip()
        if (
            not stripped
            or stripped != line
            or stripped.startswith(("#", "|", ":::", "```", "<"))
        ):
            return (line,)
        prefix = ""
        body = line
        subsequent_indent = ""
        if line.startswith(("- ", "* ", "+ ")):
            prefix, body = line[:2], line[2:]
            subsequent_indent = "  "
        elif line.startswith("> "):
            prefix, body = line[:2], line[2:]
            subsequent_indent = prefix
        else:
            marker, separator, remainder = line.partition(" ")
            if separator and marker.endswith(".") and marker[:-1].isdigit():
                prefix, body = f"{marker} ", remainder
                subsequent_indent = " " * len(prefix)
        wrapper = textwrap.TextWrapper(
            width=width,
            initial_indent=prefix,
            subsequent_indent=subsequent_indent,
            break_long_words=False,
            break_on_hyphens=False,
        )
        return tuple(wrapper.wrap(body)) or (line,)

    @staticmethod
    def _render_markdown(lines: t.SequenceOf[str], *, width: int) -> str:
        """Render generated Markdown with bounded prose and verbatim code blocks.

        Returns:
            The resulting ``str``.

        """
        rendered: t.MutableSequenceOf[str] = []
        in_fence = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                rendered.append(line)
            elif in_fence:
                rendered.append(line)
            else:
                rendered.extend(
                    FlextInfraUtilitiesDocsRender._wrap_markdown_line(line, width=width)
                )
        return "\n".join(rendered)

    @staticmethod
    def _is_object_list(value: t.JsonValue | None) -> bool:
        """Type guard: narrow one infra value to a mutable sequence.

        Returns:
            The resulting ``bool``.

        """
        return isinstance(value, list)

    @staticmethod
    def as_string_sequence(data: t.JsonMapping, key: str) -> t.SequenceOf[str]:
        """Return one contract field as a normalized string sequence.

        Returns:
            One contract field as a normalized string sequence.

        """
        value = data.get(key)
        if not isinstance(value, list):
            return []
        return [str(entry) for entry in value]

    @staticmethod
    def _preview(values: t.SequenceOf[str], *, limit: int = 6) -> str:
        """Render one compact preview list with overflow summary.

        Returns:
            The resulting ``str``.

        """
        normalized = [value for value in values if value]
        if not normalized:
            return "_none_"
        preview = ", ".join(f"`{value}`" for value in normalized[:limit])
        remaining = len(normalized) - limit
        return f"{preview} (+{remaining} more)" if remaining > 0 else preview

    @staticmethod
    def _escape_table_cell(value: str) -> str:
        """Escape Markdown table separators in one cell.

        Returns:
            The resulting ``str``.

        """
        return value.replace("|", "\\|").strip()

    @staticmethod
    def _module_relative_doc_path(package_name: str, module_name: str) -> str:
        """Return the generated relative path for one module page.

        Returns:
            The generated relative path for one module page.

        """
        relative = module_name.removeprefix(f"{package_name}.").replace(".", "/")
        return f"{relative}.md"

    @staticmethod
    def _resolve_governance_link(
        prefix: str,
        path: str,
        *,
        is_dir: bool = False,
        governance_source: m.Infra.CodegenBootstrapSource | None,
    ) -> str:
        """Return a resolvable governance link for README or project docs.

        READMEs render on GitHub and can use relative paths; generated
        ``docs/index.md`` pages are built by MkDocs with ``docs_dir`` isolation,
        so governance pointers must be absolute GitHub URLs.

        Returns:
            A resolvable governance link for README or project docs.

        Raises:
            ValueError: If documentation repository owner must resolve exactly once.

        """
        if FlextInfraUtilitiesDocs.docs_is_secure_web_url(prefix):
            kind = "tree" if is_dir else "blob"
            if governance_source is None:
                msg = "governance link has no captured source and ref"
                raise ValueError(msg)
            normalized = (
                FlextInfraUtilitiesRepository
                .validate_git_remote_url(governance_source.url)
                .unwrap()
                .rstrip("/")
                .removesuffix(".git")
            )
            if normalized != prefix.rstrip("/"):
                msg = "governance link differs from its captured owner"
                raise ValueError(msg)
            return f"{prefix}/{kind}/{governance_source.ref}/{path}"
        return f"{prefix}/{path}"

    @staticmethod
    def _exclude_plugin_lines(data: t.JsonMapping) -> t.SequenceOf[str]:
        """Render optional ``mkdocs-exclude`` plugin lines.

        Returns:
            The resulting ``t.SequenceOf[str]``.

        """
        patterns = FlextInfraUtilitiesDocsRender.as_string_sequence(
            data,
            "exclude_docs",
        )
        if not patterns:
            return []
        return [
            "  - exclude:",
            "      glob:",
            *[f"        - {pattern}" for pattern in patterns],
        ]

    @staticmethod
    def _exclude_docs_lines(data: t.JsonMapping) -> t.SequenceOf[str]:
        """Render native ``exclude_docs`` lines for early MkDocs filtering.

        ``exclude_docs`` is gitignore-style (``pathspec.GitIgnoreSpec``): a bare
        ``README.md`` matches at every depth and silently drops legitimate
        ``docs/<section>/README.md`` pages that generated index pages link to
        (producing nav 404s). The rooted ``/README.md`` excludes only the
        docs-dir root README (the project README mirror), preserving nested
        section READMEs.

        Curated ``API/**`` mirrors duplicate the generated public-API page and
        register the same flat symbol anchors (for example ``<package>.s``),
        producing ``Multiple primary URLs`` autorefs conflicts. The generated
        page is canonical; the curated mirror is excluded.

        Returns:
            The resulting ``t.SequenceOf[str]``.

        """
        patterns = list(
            dict.fromkeys([
                *FlextInfraUtilitiesDocsRender.as_string_sequence(data, "exclude_docs"),
                "/README.md",
                "/API/**",
            ]),
        )
        return ["exclude_docs: |", *[f"  {pattern}" for pattern in patterns], ""]

    @staticmethod
    def docs_directive_page(title: str, dotted_path: str, *, width: int) -> str:
        """Return a mkdocstrings page for a module path.

        Returns:
            A mkdocstrings page for a module path.

        """
        return FlextInfraUtilitiesDocsRender._generated_page(
            title,
            [
                f"::: {dotted_path}",
                "",
                "    options:",
                "      show_root_heading: true",
                "      show_root_full_path: false",
                "      show_source: false",
            ],
            width=width,
        )

    _LINK_PREFIX_DOCS_INDEX: ClassVar[str] = c.Infra.GITHUB_REPO_URL
    """Link prefix for ``<project>/docs/index.md`` governance pointers.

    Uses the canonical GitHub URL so MkDocs can resolve the pointers during
    per-project builds; files under ``docs_dir`` cannot point outside the
    project docs tree with relative paths.
    """

    _LINK_PREFIX_README: ClassVar[str] = c.Infra.GITHUB_REPO_URL
    """Canonical governance URL shared by workspace and standalone READMEs."""

    @staticmethod
    def _public_surface_lines(scope: m.Infra.DocScope) -> t.SequenceOf[str]:
        """Return the canonical public-surface block — mkdocstrings autodoc.

        Replaces the prior hardcoded four-bullet summary (frozen snapshot of
        ``aliases`` / ``facades`` / ``public_symbols`` from contract data) with
        a live mkdocstrings directive that renders the package-level docstring
        + ``__all__`` exports at mkdocs build time. Real content from real
        code, never frozen — the user's "fake markdown" complaint.

        Returns:
            The canonical public-surface block — mkdocstrings autodoc.

        """
        return [
            f"::: {scope.package_name}",
            "",
            "    options:",
            "      members: false",
            "      show_root_heading: false",
            "      show_root_toc_entry: false",
            "      show_source: false",
        ]

    @staticmethod
    def _collection_rules_lines(
        scope: m.Infra.DocScope,
        *,
        link_prefix: str,
    ) -> t.SequenceOf[str]:
        """Return a thin pointer to the canonical Collection Rules.

        SSOT: the actual content lives in ``flext/AGENTS.md`` §9 — duplicating
        it 33x per project (once for ``docs/index.md`` and once for
        ``README.md``) is the "fake markdown" the user flagged. Each project
        page now points back to the canonical source instead of carrying a
        copy. ``scope`` is preserved on the signature for symmetry with the
        other boilerplate helpers but is intentionally unused.

        Returns:
            A thin pointer to the canonical Collection Rules.

        """
        agents_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            "AGENTS.md",
            governance_source=scope.governance_source,
        )
        return [
            "## Collection Rules",
            "",
            (
                f"Read [`/flext/AGENTS.md`]({agents_link}) and this project's "
                "`AGENTS.md` for the current authority chain, execution "
                "boundaries and required validation."
            ),
        ]

    @staticmethod
    def _quality_gates_lines(
        scope: m.Infra.DocScope, *, link_prefix: str
    ) -> t.SequenceOf[str]:
        """Return a thin pointer to the canonical Quality Gates surface.

        Why: the flext-quality-gates skill path does not exist; route to
        make-check and AGENTS.md Make contract instead.

        Returns:
            A thin pointer to the canonical Quality Gates surface.

        """
        agents_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            "AGENTS.md",
            governance_source=scope.governance_source,
        )
        return [
            "## Quality Gates",
            "",
            (
                "Canonical `make` verbs (`gen`, `check`, `test`, `fmt`, "
                "`docs`) execute their declared operations directly."
            ),
            "",
            (
                f"See [`/flext/AGENTS.md`]({agents_link}) for the build, test, "
                "and Python quality gates."
            ),
        ]

    @staticmethod
    def _governance_pointer_lines(
        scope: m.Infra.DocScope, *, link_prefix: str
    ) -> t.SequenceOf[str]:
        """Return a thin pointer to the canonical governance surface.

        Returns:
            A thin pointer to the canonical governance surface.

        """
        agents_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            "AGENTS.md",
            governance_source=scope.governance_source,
        )
        skills_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            ".agents/skills/",
            governance_source=scope.governance_source,
            is_dir=True,
        )
        onboarding_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            "docs/guides/onboarding.md",
            governance_source=scope.governance_source,
        )
        governance_link = FlextInfraUtilitiesDocsRender._resolve_governance_link(
            link_prefix,
            "docs/GOVERNANCE.md",
            governance_source=scope.governance_source,
        )
        return [
            "## Governance Pointer",
            "",
            f"- Engineering law: [`/flext/AGENTS.md`]({agents_link})",
            f"- Governance + ADRs: [`/flext/docs/GOVERNANCE.md`]({governance_link})",
            f"- Skills index: [`/flext/.agents/skills/`]({skills_link})",
            f"- Onboarding: [`/flext/docs/guides/onboarding.md`]({onboarding_link})",
        ]

    @staticmethod
    def _declared_or(data: t.JsonMapping, key: str, default: str) -> str:
        """Return one declared contract string or its explicit default.

        Empty and whitespace-only declarations resolve to the default exactly
        once, at this boundary; per-call-site ``or`` masks are forbidden so the
        declared defaults cannot drift between renderers.
        """
        declared = str(data.get(key, "")).strip()
        return declared or default

    @staticmethod
    def docs_project_index(
        scope: m.Infra.DocScope, contract: t.JsonMapping, *, width: int
    ) -> str:
        """Return the standard ``<project>/docs/index.md`` landing page.

        Returns:
            The standard ``<project>/docs/index.md`` landing page.

        """
        data = contract
        version = FlextInfraUtilitiesDocsRender._declared_or(data, "version", "unknown")
        description = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "description",
            "_not declared_",
        )
        link_prefix = FlextInfraUtilitiesDocsRender._LINK_PREFIX_DOCS_INDEX
        return FlextInfraUtilitiesDocsRender._generated_page(
            f"{scope.name} Documentation",
            [
                f"- Version: `{version}`",
                f"- Project class: `{scope.project_class}`",
                f"- Package: `{scope.package_name}`",
                f"- Description: {description}",
                "",
                (
                    "This project portal is generated from `pyproject.toml`, "
                    "package exports, and real docstrings."
                ),
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
                *FlextInfraUtilitiesDocsRender._public_surface_lines(scope),
                "",
                *FlextInfraUtilitiesDocsRender._collection_rules_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
                "",
                *FlextInfraUtilitiesDocsRender._quality_gates_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
                "",
                *FlextInfraUtilitiesDocsRender._governance_pointer_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
            ],
            width=width,
        )

    @staticmethod
    def docs_project_readme(
        scope: m.Infra.DocScope, contract: t.JsonMapping, *, width: int
    ) -> str:
        """Return the canonical ``<project>/README.md`` (8-section structure).

        Auto-generated from ``pyproject.toml`` + package exports + the canonical
        FLEXT readme template (see ``readme-standardization`` skill). Output is
        fully deterministic — running the generator twice produces byte-identical
        content. Shares Collection Rules, Quality Gates, and Governance Pointer
        sections with ``docs_project_index`` via private helpers (no duplication).

        Returns:
            The canonical ``<project>/README.md`` (8-section structure).

        """
        data = contract
        version = FlextInfraUtilitiesDocsRender._declared_or(data, "version", "unknown")
        description = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "description",
            "_not declared_",
        )
        facades = FlextInfraUtilitiesDocsRender.as_string_sequence(data, "facades")
        link_prefix = FlextInfraUtilitiesDocsRender._LINK_PREFIX_README
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {scope.name}",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                (
                    f"**Version**: `{version}` | **Python**: see `pyproject.toml` "
                    "`requires-python` | "
                    f"**Project class**: `{scope.project_class}`"
                ),
                "",
                (
                    "> **Alpha (0.12.0).** This package is alpha quality. Every "
                    "package in the workspace must be re-checked and re-validated "
                    "at 0.12.0 before any promotion beyond alpha; treat interfaces "
                    "as unstable."
                ),
                "",
                "## Purpose",
                "",
                description,
                "",
                "## Module Map",
                "",
                *FlextInfraUtilitiesDocsRender._public_surface_lines(scope),
                "",
                *FlextInfraUtilitiesDocsRender._collection_rules_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
                "",
                "## Operation Flow",
                "",
                (
                    "- Public surface: see [`docs/index.md`](docs/index.md) and "
                    "[`docs/api-reference/README.md`](docs/api-reference/README.md)."
                ),
                (
                    "- Generated module overview: "
                    "[`docs/api-reference/generated/overview.md`](docs/api-reference/generated/overview.md)."
                ),
                (
                    "- Settings env prefix: see project `pyproject.toml` "
                    "`[tool.flext]` and `FlextSettings` ConfigDict."
                ),
                "",
                "## Integration Points",
                "",
                (
                    "- Parent FLEXT chain: read this project's `pyproject.toml` "
                    "`dependencies` array filtered by `flext-*`. The FLEXT cascade "
                    "is encoded in the inheritance lists of the facade classes "
                    "listed under Module Map above."
                ),
                (
                    "- Public extensions exposed by this project: "
                    f"{FlextInfraUtilitiesDocsRender._preview(facades)}."
                ),
                (
                    "- Library abstraction boundaries: see the project `AGENTS.md` "
                    "and the referenced parent architecture rules."
                ),
                "",
                *FlextInfraUtilitiesDocsRender._quality_gates_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
                "",
                *FlextInfraUtilitiesDocsRender._governance_pointer_lines(
                    scope,
                    link_prefix=link_prefix,
                ),
                "- Full project portal: [`docs/index.md`](docs/index.md).",
                "",
            ],
            width=width,
        )

    @staticmethod
    def docs_guides_index(
        scope: m.Infra.DocScope, *, guide_paths: t.SequenceOf[Path], width: int
    ) -> str:
        """Index the planned guide inventory, including retained custom guides.

        Returns:
            The resulting ``str``.

        """
        entries = [
            f"- [{path.stem.replace('-', ' ').capitalize()}]({path.name})"
            for path in sorted(guide_paths)
        ]
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {scope.name} Guides",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                (
                    "Curated operational guides live here. Keep API behavior in "
                    "generated reference pages sourced from code and docstrings."
                ),
                "",
                *entries,
                "- [Back to project docs](../index.md)",
                "- [API Reference](../api-reference/README.md)",
                "",
            ],
            width=width,
        )

    @staticmethod
    def docs_api_readme(
        scope: m.Infra.DocScope,
        contract: t.JsonMapping,
        modules: t.SequenceOf[str],
        *,
        width: int,
    ) -> str:
        """Return the standard API readme for a project.

        ``modules`` is the configured module-page list actually rendered, not
        the analysed contract's public modules, so the count matches the pages.

        Returns:
            The standard API readme for a project.

        """
        data = contract
        facades = FlextInfraUtilitiesDocsRender.as_string_sequence(data, "facades")
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {scope.name} API Reference",
                "",
                c.Infra.GENERATED_HEADER,
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
                "Back to [project docs](../index.md).",
                "",
            ],
            width=width,
        )

    @staticmethod
    def _generated_page(title: str, body: t.SequenceOf[str], *, width: int) -> str:
        """Compose a generated markdown page with the canonical header + title.

        SSOT for the ``["# title", "", GENERATED_HEADER, "", ...body, ""]``
        layout shared by every ``docs_*_page``/``docs_*_index``/``docs_*_readme``
        renderer. Structural lines remain verbatim while prose is wrapped by
        the canonical renderer.

        Returns:
            The resulting ``str``.

        """
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {title}",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                *body,
                "",
            ],
            width=width,
        )

    @staticmethod
    def _render_block(lines: t.SequenceOf[str]) -> str:
        """Pre-format a line sequence into a newline-terminated j2-safe block.

        Returns ``""`` when ``lines`` is empty so the template's substitution
        leaves no trailing artifacts. Otherwise joins with newlines and adds
        one trailing newline so the next macro sits on a fresh line.

        Returns:
            The resulting ``str``.

        """
        return "\n".join([*lines, ""]) if lines else ""

    @staticmethod
    def _mkdocstrings_paths_block(paths: t.SequenceOf[str]) -> str:
        """Pre-format the optional mkdocstrings ``paths`` sub-block.

        Returns:
            The resulting ``str``.

        """
        if not paths:
            return ""
        body = ["          paths:", *(f"            - {path}" for path in paths)]
        return "\n".join([*body, ""])

    @staticmethod
    def docs_project_mkdocs(
        scope: m.Infra.DocScope,
        contract: t.JsonMapping,
        modules: t.SequenceOf[str],
        *,
        source_states: t.SequenceOf[m.Cli.AtomicFileState] | None = None,
    ) -> str:
        """Return the managed mkdocs.yml for a project scope.

        Renders the canonical ``mkdocs_project.yml.j2`` template through the
        flext-cli facade shared with the workspace variant; theme, plugins,
        and validation macros live in the template, not Python.

        Returns:
            The managed mkdocs.yml for a project scope.

        """
        del modules
        data = contract
        repo_url = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "repo_url",
            c.Infra.GITHUB_REPO_URL,
        )

        # Preserve one typed context across the sole public template-rendering boundary.
        context = m.Infra.MkdocsProjectRenderContext(
            site_title=FlextInfraUtilitiesDocsRender._declared_or(
                data,
                "site_title",
                scope.name,
            ),
            site_url=FlextInfraUtilitiesDocsRender._declared_or(
                data,
                "site_url",
                c.Infra.GITHUB_REPO_URL,
            ),
            repo_url=repo_url,
            repo_name=FlextInfraUtilitiesDocsRender._repository_name(repo_url),
            scope_name=scope.name,
            exclude_docs_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            ),
            exclude_plugin_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            ),
            mkdocstrings_paths_block=FlextInfraUtilitiesDocsRender._mkdocstrings_paths_block((
                "src",
            )),
        )
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_MKDOCS_PROJECT
        )
        rendered: str = t.Infra.STR_ADAPTER.validate_python(
            u.Cli
            .template_render_authenticated(
                template_path,
                context,
                source_states=source_states,
            )
            .unwrap()
            .rendered,
        )
        return rendered

    @staticmethod
    def docs_overview_page(
        scope: m.Infra.DocScope,
        contract: t.JsonMapping,
        modules: t.SequenceOf[str],
        *,
        width: int,
    ) -> str:
        """Return the generated overview page for a project API.

        ``modules`` is the configured module-page list actually rendered, not
        the analysed contract's public modules, so the count matches the pages.

        Returns:
            The generated overview page for a project API.

        """
        data = contract
        limits = config.Infra.codegen.make.docs.overview_preview_limits.model_dump()
        aliases, exports, facades, module_exports, keywords = (
            FlextInfraUtilitiesDocsRender._preview(
                FlextInfraUtilitiesDocsRender.as_string_sequence(data, field),
                limit=limits[field],
            )
            for field in (
                "aliases",
                "public_symbols",
                "facades",
                "module_exports",
                "keywords",
            )
        )
        classifiers = (
            ", ".join(
                FlextInfraUtilitiesDocsRender.as_string_sequence(data, "classifiers"),
            )
            or "_none_"
        )
        site_title = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "site_title",
            scope.name,
        )
        description = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "description",
            "_not declared_",
        )
        doc_summary = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "doc_summary",
            "_not declared_",
        )
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {site_title} API Overview",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                f"- Package: `{scope.package_name}`",
                f"- Version: `{data.get('version', '')}`",
                f"- Description: {description}",
                f"- Doc summary: {doc_summary}",
                f"- Classifiers: {classifiers}",
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
            ],
            width=width,
        )

    @staticmethod
    def docs_modules_index(
        scope: m.Infra.DocScope, modules: t.SequenceOf[str], *, width: int
    ) -> str:
        """Return the generated module index page for one project.

        Returns:
            The generated module index page for one project.

        """
        lines: t.MutableSequenceOf[str] = [
            f"# {scope.name} Module Index",
            "",
            c.Infra.GENERATED_HEADER,
            "",
            "These pages are generated from public modules and their docstrings.",
            "",
        ]
        if not modules:
            lines.extend(["_No public modules discovered._", ""])
            return FlextInfraUtilitiesDocsRender._render_markdown(lines, width=width)
        for module_name in modules:
            relative_path = FlextInfraUtilitiesDocsRender._module_relative_doc_path(
                scope.package_name,
                module_name,
            )
            lines.append(f"- [{module_name}]({relative_path})")
        lines.append("")
        return FlextInfraUtilitiesDocsRender._render_markdown(lines, width=width)

    @staticmethod
    def _site_title(data: t.JsonMapping) -> str:
        """Resolve the docs title: declared override, then project name.

        The last-resort literal is deliberately brand-free: a repository that
        declares neither a site title nor a project name must not describe
        itself with someone else's name.

        Returns:
            The resulting ``str``.

        """
        return (
            str(data.get("site_title", "")).strip()
            or str(data.get("name", "")).strip()
            or "Workspace docs"
        )

    @staticmethod
    def docs_root_mkdocs(
        contract: t.JsonMapping,
        src_paths: t.SequenceOf[str] = (),
        *,
        source_states: t.SequenceOf[m.Cli.AtomicFileState] | None = None,
    ) -> str:
        """Return the managed mkdocs.yml for the repository root.

        Renders the canonical ``mkdocs_root.yml.j2`` template through the
        flext-cli facade shared with the per-project variant.

        Returns:
            The managed mkdocs.yml for the repository root.

        """
        data = contract
        repo_url = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "repo_url",
            c.Infra.GITHUB_REPO_URL,
        )

        # Preserve one typed context across the sole public template-rendering boundary.
        # The title falls back to the governed project name — never a fleet
        # brand — so a standalone repository describes itself (ag-q6uo).
        context = m.Infra.MkdocsRenderContext(
            site_title=FlextInfraUtilitiesDocsRender._site_title(data),
            site_url=FlextInfraUtilitiesDocsRender._declared_or(
                data,
                "site_url",
                c.Infra.GITHUB_REPO_URL,
            ),
            repo_url=repo_url,
            repo_name=FlextInfraUtilitiesDocsRender._repository_name(repo_url),
            exclude_docs_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_docs_lines(data),
            ),
            exclude_plugin_block=FlextInfraUtilitiesDocsRender._render_block(
                FlextInfraUtilitiesDocsRender._exclude_plugin_lines(data),
            ),
            mkdocstrings_paths_block=FlextInfraUtilitiesDocsRender._mkdocstrings_paths_block(
                src_paths,
            ),
        )
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_MKDOCS_ROOT
        )
        rendered: str = t.Infra.STR_ADAPTER.validate_python(
            u.Cli
            .template_render_authenticated(
                template_path,
                context,
                source_states=source_states,
            )
            .unwrap()
            .rendered,
        )
        return rendered

    @staticmethod
    def docs_root_overview_page(
        contract: t.JsonMapping,
        *,
        project_count: int,
        class_counts: t.SequenceOf[m.Infra.DocsClassCount],
        width: int,
    ) -> str:
        """Return the generated root API overview page.

        Returns:
            The generated root API overview page.

        """
        data = contract
        classes = (
            ", ".join(
                f"`{entry.project_class}`={entry.count}" for entry in class_counts
            )
            or "_none_"
        )
        version = FlextInfraUtilitiesDocsRender._declared_or(data, "version", "unknown")
        description = FlextInfraUtilitiesDocsRender._declared_or(
            data,
            "description",
            "_not declared_",
        )
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                f"# {FlextInfraUtilitiesDocsRender._site_title(data)} API Overview",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                f"- Version: `{version}`",
                f"- Description: {description}",
                f"- Governed projects: `{project_count}`",
                f"- Project classes: {classes}",
                "",
                (
                    "Generated from workspace discovery, `pyproject.toml`, "
                    "public exports, and docstrings."
                ),
                "",
                "## Next Pages",
                "",
                "- [Workspace Module Pages](projects/index.md)",
                "- [Project Catalog](../../projects/generated/catalog.md)",
                "",
            ],
            width=width,
        )

    @staticmethod
    def docs_root_projects_index(
        entries: t.SequenceOf[m.Infra.DocsProjectIndexEntry], *, width: int
    ) -> str:
        """Return the generated root index of per-project module pages.

        Returns:
            The generated root index of per-project module pages.

        """
        lines: t.MutableSequenceOf[str] = [
            "# Workspace Module Pages",
            "",
            c.Infra.GENERATED_HEADER,
            "",
            "Each project renders one page per public module, driven by docstrings.",
            "",
        ]
        if not entries:
            lines.extend(["_No projects discovered._", ""])
            return FlextInfraUtilitiesDocsRender._render_markdown(lines, width=width)
        for entry in entries:
            lines.append(
                f"- [{entry.name}]({entry.name}/modules/index.md)"
                f" — `{entry.module_count}` modules",
            )
        lines.append("")
        return FlextInfraUtilitiesDocsRender._render_markdown(lines, width=width)

    @staticmethod
    def docs_project_catalog_page(
        entries: t.SequenceOf[m.Infra.DocsCatalogEntry],
        *,
        exclude_docs: t.SequenceOf[str] | None = None,
        width: int,
    ) -> str:
        """Return the generated workspace project catalog page.

        Returns:
            The generated workspace project catalog page.

        """
        exclude_patterns: t.StrSequence = tuple(exclude_docs or ())
        rows = [
            "| "
            + " | ".join([
                f"[{entry.name}]({entry.api_page})",
                FlextInfraUtilitiesDocsRender._escape_table_cell(entry.project_class),
                f"`{entry.package_name}`",
                FlextInfraUtilitiesDocsRender._escape_table_cell(
                    entry.description or "_not declared_",
                ),
            ])
            + " |"
            for entry in entries
            if not any(
                fnmatch.fnmatch(entry.api_page.removeprefix("../../"), pattern)
                for pattern in exclude_patterns
            )
        ]
        return FlextInfraUtilitiesDocsRender._render_markdown(
            [
                "# FLEXT Project Catalog",
                "",
                c.Infra.GENERATED_HEADER,
                "",
                (
                    "Project links resolve to the generated root API reference "
                    "for each governed FLEXT package."
                ),
                "",
                "| project | class | package | description |",
                "|---|---|---|---|",
                *rows,
                "",
            ],
            width=width,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsRender"]
