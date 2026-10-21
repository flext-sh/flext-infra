"""Project-local documentation presentation contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests import c, m, t, tm, u


class TestsFlextInfraDocumentationLanguage:
    """Keep localization at the presentation boundary and isolated per project."""

    @staticmethod
    def _scope(
        root: Path, language: t.Infra.DocumentationLanguage = "en"
    ) -> m.Infra.DocScope:
        """Build one scope with captured governance identity.

        Returns:
            The isolated, typed project scope.

        """
        return m.Infra.DocScope(
            name="sample",
            path=root,
            report_dir=root / ".reports/docs",
            package_name="sample",
            project_class="library",
            documentation_language=language,
            governance_source=m.Infra.CodegenBootstrapSource(
                url=c.Infra.GITHUB_REPO_URL, ref="0.12.0-dev"
            ),
        )

    @staticmethod
    def _pages(scope: m.Infra.DocScope) -> tuple[str, ...]:
        """Exercise project presentation renderers with unchanged source prose.

        Returns:
            The rendered project pages in their canonical order.

        """
        contract: t.JsonMapping = {
            "version": "1.2.3",
            "description": "Version is a domain term; do not translate `--check`.",
            "facades": ["sample.Service"],
        }
        return (
            u.Infra.docs_project_readme(scope, contract, width=88),
            u.Infra.docs_project_index(scope, contract, width=88),
            u.Infra.docs_guides_index(scope, guide_paths=(), width=88),
            u.Infra.docs_api_readme(scope, contract, ["sample.api"], width=88),
            u.Infra.docs_overview_page(scope, contract, ["sample.api"], width=88),
            u.Infra.docs_modules_index(scope, ["sample.api"], width=88),
        )

    def test_portuguese_labels_preserve_links_directives_and_domain_text(
        self, tmp_path: Path
    ) -> None:
        """Translate human presentation, not paths, directives or project metadata."""
        english = self._pages(self._scope(tmp_path))
        portuguese = self._pages(self._scope(tmp_path, "pt-BR"))
        labels = (
            "## Finalidade",
            "## Comece aqui",
            "# sample Guias",
            "## Fonte de verdade",
            "Visão geral da API",
            "Índice de módulos",
        )
        for original, localized, label in zip(english, portuguese, labels, strict=True):
            tm.that(localized, has=label)
            tm.that(
                re.findall(r"\]\(([^)]+)\)", localized),
                eq=re.findall(r"\]\(([^)]+)\)", original),
            )
            tm.that(c.Infra.GENERATED_HEADER in localized, eq=True)
        for page in (portuguese[0], portuguese[1], portuguese[4]):
            tm.that(page, has="Version is a domain term; do not translate `--check`.")
        for page in portuguese[:2]:
            tm.that(page, has="::: sample\n\n    options:")
            tm.that(page, has="      show_source: false")
            tm.that(page, has="Verificações de qualidade")
        tm.that(portuguese[0], has="**Alfa (0.12.0).**")
        tm.that(portuguese[3], has="Docstrings das classes e funções")

    def test_default_english_is_byte_identical_and_project_isolated(
        self, tmp_path: Path
    ) -> None:
        """Explicit and absent English retain identical bytes after Portuguese use."""
        scope = self._scope(tmp_path)
        payload = scope.model_dump(
            exclude={"repository_root", "documentation_language"}
        )
        default = m.Infra.DocScope.model_validate(payload)
        before = self._pages(default)
        self._pages(self._scope(tmp_path / "pt", "pt-BR"))
        tm.that(self._pages(scope), eq=before)
        tm.that(self._pages(default), eq=before)
        tm.that(before[0], has="## Purpose")
        tm.that(before[1], has="# sample Documentation")
        tm.that(before[2], has="- [Back to project docs](../index.md)")
        tm.that(before[3], has="## Source of Truth")

    def test_material_language_and_palette_are_project_local(
        self, tmp_path: Path
    ) -> None:
        """Both standalone and member sites retain the selected Brazilian dialect."""
        portuguese = self._scope(tmp_path, "pt-BR")
        english = u.Infra.docs_project_mkdocs(self._scope(tmp_path), {}, [])
        member = u.Infra.docs_project_mkdocs(portuguese, {}, [])
        root = u.Infra.docs_root_mkdocs({}, documentation_language="pt-BR")
        for rendered in (member, root):
            tm.that(rendered, has="  language: pt-BR\n")
            tm.that(rendered, has="name: Alternar para o modo escuro")
            tm.that(rendered, has="name: Alternar para o modo claro")
            parsed = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                tm.ok(u.Cli.yaml_roundtrip_load_map_text(rendered))
            )
            theme = parsed["theme"]
            if not isinstance(theme, dict):
                pytest.fail("the rendered theme must be a mapping")
            tm.that(theme["language"], eq="pt-BR")
        tm.that(english, lacks="  language:")
        tm.that(english, has="name: Switch to dark mode")
        tm.that(u.Infra.docs_project_mkdocs(self._scope(tmp_path), {}, []), eq=english)

    @staticmethod
    @pytest.mark.parametrize("language", ["pt", "PT-BR", "fr", "", None, 1])
    def test_unsupported_locale_fails_before_effects(
        tmp_path: Path, language: t.JsonValue
    ) -> None:
        """Strict authorial and projected ingress refuse unknown language values."""
        project = u.Tests.project_spec("locale-project").model_dump()
        project["documentation_language"] = language
        with pytest.raises(c.ValidationError, match="documentation_language"):
            m.Infra.ProjectSpec.model_validate(project)
        with pytest.raises(ValueError, match="unsupported documentation_language"):
            u.Infra.docs_documentation_language({"documentation_language": language})
        with pytest.raises(c.ValidationError, match="documentation_language"):
            m.Infra.DocScope.model_validate({
                "name": "invalid",
                "path": tmp_path,
                "report_dir": tmp_path / "reports",
                "documentation_language": language,
            })
        tm.that(list(tmp_path.iterdir()), eq=[])

    @staticmethod
    def test_guide_labels_use_rendered_h1_not_filename_or_fenced_examples(
        tmp_path: Path,
    ) -> None:
        """Preserve a real Portuguese title and existing guide target path."""
        content = (
            "---\ntitle: not the heading\n---\n\n"
            "```markdown\n# Fake title\n```\n\n"
            "Operação e recuperação\n======================\n\n## Details\n"
        )
        title = tm.not_none(u.Infra.docs_contract_title(content))
        tm.that(title, eq="Operação e recuperação")
        path = tmp_path / "disaster-recovery.md"
        scope = TestsFlextInfraDocumentationLanguage._scope(tmp_path, "pt-BR")
        rendered = u.Infra.docs_guides_index(
            scope, guide_paths=(path,), guide_titles={path: title}, width=88
        )
        tm.that(rendered, has="[Operação e recuperação](disaster-recovery.md)")
        tm.that(rendered, lacks="Fake title")
        tm.that(path.exists(), eq=False)

    @staticmethod
    def test_captured_project_projection_controls_only_its_scope(
        tmp_path: Path,
    ) -> None:
        """Refresh each scope from its own authenticated metadata, not a singleton."""
        scopes: list[m.Infra.DocScope] = []
        for name, declaration in (
            ("pt", 'documentation_language = "pt-BR"\n'),
            ("en", ""),
        ):
            root = tmp_path / name
            root.mkdir()
            path = root / "pyproject.toml"
            path.write_text(
                f'[project]\nname = "{name}"\nversion = "1.0"\n'
                '[tool.flext.docs]\npackage_name = "sample"\n' + declaration,
                encoding=c.DEFAULT_ENCODING,
            )
            state = tm.ok(u.Cli.atomic_read_binary_file_state(path))
            scopes.append(
                u.Infra.docs_scope_from_sources(
                    TestsFlextInfraDocumentationLanguage._scope(root), (state,)
                )
            )
        tm.that(scopes[0].documentation_language, eq="pt-BR")
        tm.that(scopes[1].documentation_language, eq="en")
        tm.that(u.Infra.docs_project_index(scopes[0], {}, width=88), has="Comece aqui")
        tm.that(u.Infra.docs_project_index(scopes[1], {}, width=88), has="Start Here")

    @staticmethod
    def test_real_bundle_localizes_one_member_and_keeps_sibling_bytes(
        tmp_path: Path,
    ) -> None:
        """Plan real project artifacts without publishing into any checkout."""
        workspace, generator = u.Tests.docs_workspace_generator(
            tmp_path,
            project_names=("flext-a", "flext-b"),
            selected_projects=["flext-a", "flext-b"],
        )
        before = {
            plan.path: plan.desired_content
            for plan in u.Tests.plan_docs_bundle(generator)
        }
        project = workspace / "flext-a"
        declaration = u.Tests.project_spec("flext-a").model_dump(mode="json")
        declaration["documentation_language"] = "pt-BR"
        config_dir = project / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "codegen.yaml").write_text(
            json.dumps({
                "Infra": {"codegen": {"repository": {"project": declaration}}}
            }),
            encoding=c.DEFAULT_ENCODING,
        )
        guide = project / "docs/guides/disaster-recovery.md"
        guide.parent.mkdir(parents=True, exist_ok=True)
        guide.write_text("# Operação e recuperação\n", encoding=c.DEFAULT_ENCODING)
        after = {
            plan.path: plan.desired_content
            for plan in u.Tests.plan_docs_bundle(generator)
        }
        for path, content in before.items():
            if path.is_relative_to(workspace / "flext-b"):
                tm.that(after[path], eq=content)
        labels = {
            "README.md": "## Finalidade",
            "docs/index.md": "Comece aqui",
            "docs/guides/README.md": "[Operação e recuperação](disaster-recovery.md)",
            "docs/api-reference/README.md": "Fonte de verdade",
            "mkdocs.yml": "language: pt-BR",
        }
        for relative, label in labels.items():
            tm.that(
                tm.not_none(after[project / relative]).decode(c.DEFAULT_ENCODING),
                has=label,
            )
        tm.that((project / "README.md").read_bytes(), eq=b"# flext-a\n")
