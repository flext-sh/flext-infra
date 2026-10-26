"""Reusable docs rendering helpers exposed through ``u.Infra``.

Page layout lives in ``templates/docs/*.md.j2``; every builder here only shapes
one typed context and hands it to the flext-cli template owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from glob import translate
from pathlib import Path, PurePosixPath
from posixpath import normpath
from typing import ClassVar
from urllib.parse import urlsplit

from flext_cli import u

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository


class FlextInfraUtilitiesDocsRender:
    """Rendering helpers for generated docs content."""

    _MIN_REPO_PARTS: ClassVar[int] = 2

    @staticmethod
    def docs_rebase_patterns(
        patterns: t.StrSequence, *, repository_root: Path, docs_root: Path
    ) -> t.StrSequence:
        """Rebase repository globs to a docs root using native path matching.

        Returns:
            Deduplicated documentation-root-relative exclusion globs.

        """
        relative = PurePosixPath(docs_root.relative_to(repository_root).as_posix())
        rebased: list[str] = []
        for pattern in patterns:
            parts = PurePosixPath(pattern).parts
            if parts and parts[0] == "/":
                parts = parts[1:]
            if relative == PurePosixPath():
                rebased.append("/".join(parts))
                continue
            if any(
                ancestor.full_match("/".join(parts))
                for ancestor in (relative, *relative.parents)
                if ancestor != PurePosixPath()
            ):
                rebased.append("**")
                continue
            for boundary in range(1, len(parts)):
                if relative.full_match("/".join(parts[:boundary])):
                    # A recursive segment can also consume descendants of docs_root.
                    start = boundary - (parts[boundary - 1] == "**")
                    rebased.append("/".join(parts[start:]))
        return tuple(dict.fromkeys(rebased))

    @staticmethod
    def _mkdocs_exclusions(
        repository_root: Path,
    ) -> t.Pair[t.StrSequence, t.StrSequence]:
        """Project one repository's effective policy into both native consumers.

        Returns:
            Rooted page exclusions and translated physical-copy regular expressions.

        """
        codegen = (
            FlextInfraUtilitiesProjectManagedArtifacts
            .load_codegen_inputs(repository_root)
            .unwrap()
            .spec
        )
        publish, copy = (
            FlextInfraUtilitiesDocsRender.docs_rebase_patterns(
                patterns,
                repository_root=repository_root,
                docs_root=repository_root / c.Infra.DIR_DOCS,
            )
            for patterns in (
                codegen.exclusions.docs_publish,
                codegen.exclusions.docs_copy,
            )
        )
        return (
            tuple(f"/{pattern}" for pattern in publish),
            tuple(
                translate(pattern, recursive=True, include_hidden=True)
                for pattern in copy
            ),
        )

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
        normalized = repo_url.strip().rstrip("/").removesuffix(c.GIT_DIR_NAME)
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
    def _render_template(template: str, context: p.Model) -> str:
        """Render one packaged template through the flext-cli template owner.

        Returns:
            The rendered document.

        """
        return (
            u.Cli
            .template_render_authenticated(
                Path(__file__).resolve().parent.parent / "templates" / template,
                context,
            )
            .unwrap()
            .rendered
        )

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
                .removesuffix(c.GIT_DIR_NAME)
            )
            if normalized != prefix.rstrip("/"):
                msg = "governance link differs from its captured owner"
                raise ValueError(msg)
            return f"{prefix}/{kind}/{governance_source.ref}/{path}"
        return f"{prefix}/{path}"

    @staticmethod
    def _governance_links(scope: m.Infra.DocScope) -> m.Infra.DocsGovernanceLinks:
        """Return the canonical governance pointers of one project scope.

        Returns:
            The four resolvable governance pointers.

        """
        resolve = FlextInfraUtilitiesDocsRender._resolve_governance_link
        prefix = c.Infra.GITHUB_REPO_URL
        source = scope.governance_source
        return m.Infra.DocsGovernanceLinks(
            agents=resolve(prefix, "AGENTS.md", governance_source=source),
            governance=resolve(prefix, "docs/GOVERNANCE.md", governance_source=source),
            skills=resolve(
                prefix, ".agents/skills/", is_dir=True, governance_source=source
            ),
            onboarding=resolve(
                prefix, "docs/guides/onboarding.md", governance_source=source
            ),
        )

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
    def docs_directive_page(title: str, dotted_path: str, *, width: int) -> str:
        """Return a mkdocstrings page for a module path.

        Returns:
            A mkdocstrings page for a module path.

        """
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_DIRECTIVE_PAGE,
            m.Infra.DocsDirectivePageContext(
                line_width=width, title=title, dotted_path=dotted_path
            ),
        )

    @staticmethod
    def docs_project_index(
        scope: m.Infra.DocScope, contract: t.JsonMapping, *, width: int
    ) -> str:
        """Return the standard ``<project>/docs/index.md`` landing page.

        Returns:
            The standard ``<project>/docs/index.md`` landing page.

        """
        text = scope.documentation_text
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_PROJECT_INDEX,
            m.Infra.DocsProjectIndexContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                name=scope.name,
                project_class=scope.project_class,
                package_name=scope.package_name,
                version=FlextInfraUtilitiesDocsRender._declared_or(
                    contract, "version", text(c.Infra.DocumentationText.UNKNOWN)
                ),
                description=FlextInfraUtilitiesDocsRender._declared_or(
                    contract,
                    "description",
                    text(c.Infra.DocumentationText.NOT_DECLARED),
                ),
                links=FlextInfraUtilitiesDocsRender._governance_links(scope),
            ),
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
        sections with ``docs_project_index`` through the template macros.

        Returns:
            The canonical ``<project>/README.md`` (8-section structure).

        """
        text = scope.documentation_text
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_PROJECT_README,
            m.Infra.DocsProjectReadmeContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                name=scope.name,
                project_class=scope.project_class,
                package_name=scope.package_name,
                version=FlextInfraUtilitiesDocsRender._declared_or(
                    contract, "version", text(c.Infra.DocumentationText.UNKNOWN)
                ),
                description=FlextInfraUtilitiesDocsRender._declared_or(
                    contract,
                    "description",
                    text(c.Infra.DocumentationText.NOT_DECLARED),
                ),
                links=FlextInfraUtilitiesDocsRender._governance_links(scope),
                facades=FlextInfraUtilitiesDocsRender.as_string_sequence(
                    contract, "facades"
                ),
            ),
        )

    @staticmethod
    def docs_guides_index(
        scope: m.Infra.DocScope,
        *,
        guide_paths: t.SequenceOf[Path],
        width: int,
        guide_titles: t.MappingKV[Path, str] | None = None,
    ) -> str:
        """Index the planned guide inventory, including retained custom guides.

        Returns:
            The resulting ``str``.

        """
        titles: t.MappingKV[Path, str] = (
            guide_titles or {} if scope.documentation_language == "pt-BR" else {}
        )
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_GUIDES_INDEX,
            m.Infra.DocsGuidesIndexContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                name=scope.name,
                guides=tuple(
                    m.Infra.DocsGuideEntry(
                        file_name=path.name,
                        title=titles.get(
                            path, path.stem.replace("-", " ").capitalize()
                        ),
                    )
                    for path in sorted(guide_paths)
                ),
            ),
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
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_API_README,
            m.Infra.DocsApiReadmeContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                name=scope.name,
                package_name=scope.package_name,
                facades=FlextInfraUtilitiesDocsRender.as_string_sequence(
                    contract, "facades"
                ),
                module_count=len(modules),
            ),
        )

    @staticmethod
    def docs_project_mkdocs(
        scope: m.Infra.DocScope,
        contract: t.JsonMapping,
    ) -> str:
        """Return the managed mkdocs.yml for a project scope.

        Renders the canonical ``mkdocs_project.yml.j2`` template through the
        flext-cli facade shared with the workspace variant; theme, plugins,
        and validation macros live in the template, not Python.

        Returns:
            The managed mkdocs.yml for a project scope.

        """
        repo_url = FlextInfraUtilitiesDocsRender._declared_or(
            contract,
            "repo_url",
            c.Infra.GITHUB_REPO_URL,
        )
        publish, copy = FlextInfraUtilitiesDocsRender._mkdocs_exclusions(scope.path)
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_MKDOCS_PROJECT,
            m.Infra.MkdocsProjectRenderContext(
                documentation_language=scope.documentation_language,
                site_title=FlextInfraUtilitiesDocsRender._declared_or(
                    contract,
                    "site_title",
                    scope.name,
                ),
                site_url=FlextInfraUtilitiesDocsRender._declared_or(
                    contract,
                    "site_url",
                    c.Infra.GITHUB_REPO_URL,
                ),
                repo_url=repo_url,
                repo_name=FlextInfraUtilitiesDocsRender._repository_name(repo_url),
                scope_name=scope.name,
                exclude_docs=publish,
                exclude_plugin_patterns=copy,
                mkdocstrings_paths=(c.Infra.DEFAULT_SRC_DIR,),
            ),
        )

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
        text = scope.documentation_text
        declared = FlextInfraUtilitiesDocsRender._declared_or
        sequence = FlextInfraUtilitiesDocsRender.as_string_sequence
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_OVERVIEW_PAGE,
            m.Infra.DocsOverviewContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                site_title=declared(contract, "site_title", scope.name),
                package_name=scope.package_name,
                version=str(contract.get("version", "")),
                description=declared(
                    contract,
                    "description",
                    text(c.Infra.DocumentationText.NOT_DECLARED),
                ),
                doc_summary=declared(
                    contract,
                    "doc_summary",
                    text(c.Infra.DocumentationText.NOT_DECLARED),
                ),
                classifiers=sequence(contract, "classifiers"),
                project_class=scope.project_class,
                keywords=sequence(contract, "keywords"),
                facades=sequence(contract, "facades"),
                aliases=sequence(contract, "aliases"),
                public_symbols=sequence(contract, "public_symbols"),
                module_exports=sequence(contract, "module_exports"),
                preview_limits=(
                    config.Infra.codegen.make.docs.overview_preview_limits.model_dump()
                ),
                module_count=len(modules),
            ),
        )

    @staticmethod
    def docs_modules_index(
        scope: m.Infra.DocScope, modules: t.SequenceOf[str], *, width: int
    ) -> str:
        """Return the generated module index page for one project.

        Returns:
            The generated module index page for one project.

        """
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_MODULES_INDEX,
            m.Infra.DocsModulesIndexContext(
                documentation_language=scope.documentation_language,
                line_width=width,
                name=scope.name,
                modules=tuple(
                    m.Infra.DocsModuleEntry(
                        name=module_name,
                        path=FlextInfraUtilitiesDocsRender._module_relative_doc_path(
                            scope.package_name, module_name
                        ),
                    )
                    for module_name in modules
                ),
            ),
        )

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
        repository_root: Path,
        documentation_language: t.Infra.DocumentationLanguage = "en",
    ) -> str:
        """Return the managed mkdocs.yml for the repository root.

        Renders the canonical ``mkdocs_root.yml.j2`` template through the
        flext-cli facade shared with the per-project variant. The title falls
        back to the governed project name, never a fleet brand, so a standalone
        repository describes itself (ag-q6uo).

        Returns:
            The managed mkdocs.yml for the repository root.

        """
        repo_url = FlextInfraUtilitiesDocsRender._declared_or(
            contract,
            "repo_url",
            c.Infra.GITHUB_REPO_URL,
        )
        publish, copy = FlextInfraUtilitiesDocsRender._mkdocs_exclusions(
            repository_root
        )
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_MKDOCS_ROOT,
            m.Infra.MkdocsRenderContext(
                documentation_language=documentation_language,
                site_title=FlextInfraUtilitiesDocsRender._site_title(contract),
                site_url=FlextInfraUtilitiesDocsRender._declared_or(
                    contract,
                    "site_url",
                    c.Infra.GITHUB_REPO_URL,
                ),
                repo_url=repo_url,
                repo_name=FlextInfraUtilitiesDocsRender._repository_name(repo_url),
                exclude_docs=publish,
                exclude_plugin_patterns=copy,
                mkdocstrings_paths=src_paths,
            ),
        )

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
        english = c.Infra.DocumentationText
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_ROOT_OVERVIEW_PAGE,
            m.Infra.DocsRootOverviewContext(
                line_width=width,
                site_title=FlextInfraUtilitiesDocsRender._site_title(contract),
                version=FlextInfraUtilitiesDocsRender._declared_or(
                    contract, "version", english.UNKNOWN.localized("en")
                ),
                description=FlextInfraUtilitiesDocsRender._declared_or(
                    contract, "description", english.NOT_DECLARED.localized("en")
                ),
                project_count=project_count,
                class_counts=class_counts,
            ),
        )

    @staticmethod
    def docs_root_projects_index(
        entries: t.SequenceOf[m.Infra.DocsProjectIndexEntry], *, width: int
    ) -> str:
        """Return the generated root index of per-project module pages.

        Returns:
            The generated root index of per-project module pages.

        """
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_ROOT_PROJECTS_INDEX,
            m.Infra.DocsRootProjectsIndexContext(line_width=width, entries=entries),
        )

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
        return FlextInfraUtilitiesDocsRender._render_template(
            c.Infra.TEMPLATE_DOCS_PROJECT_CATALOG_PAGE,
            m.Infra.DocsProjectCatalogContext(
                line_width=width,
                entries=tuple(
                    entry
                    for entry in entries
                    if not any(
                        PurePosixPath(
                            normpath(f"docs/projects/generated/{entry.api_page}")
                        ).full_match(pattern)
                        for pattern in exclude_patterns
                    )
                ),
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsRender"]
