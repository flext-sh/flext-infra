"""Behavior tests for managed mkdocs.yml rendering (exclude_docs / nav404).

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

import re
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import mkdocs.config
import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


@runtime_checkable
class MkDocsProjectLoader(Protocol):
    """Native MkDocs loader port for one project configuration file."""

    def __call__(
        self,
        config_file: str,
        *,
        plugins: list[object],
    ) -> MkDocsConfig:
        """Load one project configuration, overriding declared plugins."""
        ...


@runtime_checkable
class MkDocsConfigModulePort(Protocol):
    """Native ``mkdocs.config`` module port exposing its loader."""

    @property
    def load_config(self) -> MkDocsProjectLoader:
        """The native loader bound to this configuration module."""
        ...


def mkdocs_project_config(
    module: object,
    config_file: str,
) -> MkDocsConfig:
    """Load one project ``mkdocs.yml`` with plugin overrides disabled.

    Returns:
        The loaded native MkDocs configuration.

    Raises:
        TypeError: If the native module does not satisfy its loader port.

    """
    if not isinstance(module, MkDocsConfigModulePort):
        msg = "mkdocs.config does not satisfy its loader port"
        raise TypeError(msg)
    return module.load_config(config_file, plugins=[])


class TestsFlextInfraDocsRender:
    """nav404 regression: exclude_docs must keep nested section READMEs (flext-3o9s).

    MkDocs evaluates ``exclude_docs`` as gitignore-style patterns
    (``pathspec.GitIgnoreSpec``). A bare ``README.md`` drops every section
    README that generated index pages link to, producing 404s in the built
    site nav; the rooted ``/README.md`` excludes only the docs-dir root README.
    """

    @staticmethod
    def test_project_navigation_discovers_maintained_pages(
        tmp_path: Path,
    ) -> None:
        """The real MkDocs navigation has manual guides beyond generated indexes."""
        scope = m.Infra.DocScope(
            name="flext-demo",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )
        for relative in ("index.md", "security/triage.md", "decisions/ADR-001.md"):
            page = tmp_path / "docs" / relative
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("# Maintained page\n", encoding="utf-8")
        config_file = tmp_path / "mkdocs.yml"
        config_file.write_text(
            u.Infra.docs_project_mkdocs(scope, {}),
            encoding="utf-8",
        )
        configuration = mkdocs_project_config(mkdocs.config, str(config_file))
        files = get_files(configuration)
        navigation = get_navigation(files, configuration)
        tm.that(
            {page.file.src_uri for page in navigation.pages},
            eq={"index.md", "security/triage.md", "decisions/ADR-001.md"},
        )

    @staticmethod
    def test_project_mkdocs_excludes_root_readme_only(tmp_path: Path) -> None:
        """Keep nested README pages while excluding only the docs root README."""
        scope = m.Infra.DocScope(
            name="flext-demo",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )

        rendered = u.Infra.docs_project_mkdocs(scope, {})

        # flext-i6nq.10: Validate the rendered public artifact through pathspec's
        # documented text-stream boundary, without an ad-hoc extraction helper.
        match = re.search(r"exclude_docs: \|\n((?: {2}\S.*\n)+)", rendered)
        tm.ok(match is not None)
        if match is None:
            pytest.fail("rendered exclude_docs block was not found")
        patterns = tuple(
            line.strip() for line in match.group(1).splitlines() if line.strip()
        )
        # The rooted pattern excludes only the docs-dir root README; a bare
        # README.md would also hide every nested section README from MkDocs.
        tm.that(patterns, has="/README.md")
        tm.that(patterns, lacks="README.md")

    @staticmethod
    def test_root_navigation_discovers_maintained_pages(tmp_path: Path) -> None:
        """The root portal exposes maintained sections without a fixed nav list."""
        for relative in (
            "index.md",
            "architecture/adr/001-decision.md",
            "guides/development.md",
            "standards/testing.md",
        ):
            page = tmp_path / "docs" / relative
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("# Maintained page\n", encoding="utf-8")
        config_file = tmp_path / "mkdocs.yml"
        config_file.write_text(
            u.Infra.docs_root_mkdocs(
                {"site_title": "Workspace"}, repository_root=tmp_path
            ),
            encoding="utf-8",
        )
        configuration = mkdocs_project_config(mkdocs.config, str(config_file))
        files = get_files(configuration)
        navigation = get_navigation(files, configuration)

        tm.that(
            {page.file.src_uri for page in navigation.pages},
            eq={
                "index.md",
                "architecture/adr/001-decision.md",
                "guides/development.md",
                "standards/testing.md",
            },
        )

    @staticmethod
    def test_mkdocs_repository_name_comes_from_project_metadata(
        tmp_path: Path,
    ) -> None:
        """Render the repository label from the same URL owner as the link."""
        scope = m.Infra.DocScope(
            name="consumer",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )
        contract = {
            "repo_url": "https://github.com/example/consumer.git",
            "site_title": "Consumer",
        }

        project = u.Infra.docs_project_mkdocs(scope, contract)
        root = u.Infra.docs_root_mkdocs(contract, repository_root=tmp_path)

        tm.that(project, has="repo_name: example/consumer")
        tm.that(root, has="repo_name: example/consumer")

    @staticmethod
    def test_project_mkdocs_excludes_generated_api_from_revision_dates(
        tmp_path: Path,
    ) -> None:
        """Do not derive Git revision dates for generated API pages."""
        scope = m.Infra.DocScope(
            name="flext-demo",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )

        rendered = u.Infra.docs_project_mkdocs(scope, {})

        parsed = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.yaml_roundtrip_load_map_text(rendered))
        )
        plugins = parsed["plugins"]
        if not isinstance(plugins, list):
            pytest.fail("the rendered plugins must be a list")
        revision = [
            entry["git-revision-date-localized"]
            for entry in plugins
            if isinstance(entry, dict) and "git-revision-date-localized" in entry
        ]
        tm.that(len(revision), eq=1)
        options = revision[0]
        if not isinstance(options, dict):
            pytest.fail("the revision plugin must declare its options")
        tm.that(options["exclude"], eq=["api-reference/generated/**"])
        tm.that(options["enable_creation_date"], eq=False)
        tm.that(options["enable_git_follow"], eq=False)

    @staticmethod
    def test_declared_exclusions_reach_docs_and_plugin_without_duplicates(
        tmp_path: Path,
    ) -> None:
        """Repository policy reaches page and physical-copy consumers exactly once."""
        scope = m.Infra.DocScope(
            name="flext-demo",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )
        defaults = tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec.exclusions
        directory = tmp_path / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir()
        page_pattern = f"{c.Infra.DIR_DOCS}/drafts/**"
        copy_pattern = f"{c.Infra.DIR_DOCS}/private/**"
        tm.ok(
            u.Cli.yaml_dump(
                directory / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "exclusions": {
                                "docs_publish": [
                                    *defaults.docs_publish,
                                    page_pattern,
                                    page_pattern,
                                ],
                                "docs_copy": [
                                    *defaults.docs_copy,
                                    copy_pattern,
                                    copy_pattern,
                                ],
                            },
                        },
                    },
                },
            )
        )
        parsed = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
            tm.ok(
                u.Cli.yaml_roundtrip_load_map_text(
                    u.Infra.docs_project_mkdocs(scope, {})
                )
            )
        )

        published = str(parsed["exclude_docs"]).split()
        tm.that(published.count("/drafts/**"), eq=1)
        tm.that(published.count("/private/**"), eq=1)
        plugins = parsed["plugins"]
        if not isinstance(plugins, list):
            pytest.fail("the rendered plugins must be a list")
        exclusion = [
            entry["exclude"]
            for entry in plugins
            if isinstance(entry, dict) and "exclude" in entry
        ]
        tm.that(len(exclusion), eq=1)
        options = u.Tests.toml_mapping(exclusion[0])
        patterns = u.Tests.toml_strings(options["regex"])
        tm.that(len(patterns), eq=len(set(patterns)))
        tm.that(
            any(re.fullmatch(pattern, "private/secret.md") for pattern in patterns),
            eq=True,
        )
        tm.that(
            any(re.fullmatch(pattern, "drafts/proposal.md") for pattern in patterns),
            eq=False,
        )
