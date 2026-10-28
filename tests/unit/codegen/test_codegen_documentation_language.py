"""Authorial documentation-language projection through the public conform owner.

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

from pathlib import Path

from tests import c, m, t, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenDocumentationLanguage:
    """Validate the sole authorial key before activating any real repository."""

    @staticmethod
    def _plan(root: Path, language: t.Infra.DocumentationLanguage | None) -> str:
        """Plan the pyproject from one project-owned language declaration.

        Returns:
            The serialized public conform plan for the pyproject.

        """
        repository = u.Tests.repository_ref("language-project").model_copy(
            update={"role": c.Infra.MakeProfile.STANDALONE}
        )
        root.mkdir(parents=True, exist_ok=True)
        u.Tests.initialize_git_repo(root, origin_url=repository.url)
        payload = u.Tests.project_spec("language-project").model_dump()
        payload.pop("documentation_language")
        if language is not None:
            payload["documentation_language"] = language
        workspace = u.Tests.workspace_spec(
            repository, project=m.Infra.ProjectSpec.model_validate(payload)
        )
        u.Tests.copy_tracked_mise_seeds(root.parent)
        service, request = TestsFlextInfraConformSupport.check_conform_service(
            root, workspace, what=c.Infra.CodegenConformSurface.PYPROJECT
        )
        plan = tm.ok(service.plan(request))
        tm.that(plan.issues, empty=True)
        tm.that(plan.exception is None, eq=True)
        file = next(
            item for item in plan.files if item.path.name == c.PYPROJECT_FILENAME
        )
        return u.Tests.codegen_file_text(file)

    def test_nondefault_projection_roundtrips_to_strict_docs_scope(
        self, tmp_path: Path
    ) -> None:
        """The local authorial value reaches docs through its generated projection."""
        root = tmp_path / "project"
        rendered = self._plan(root, "pt-BR")
        metadata = u.Tests.toml_table_at(rendered, "tool", "flext", "docs")
        tm.that(metadata["documentation_language"], eq="pt-BR")
        root.mkdir(parents=True, exist_ok=True)
        pyproject = root / c.PYPROJECT_FILENAME
        pyproject.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        scope = u.Infra.docs_scope_from_sources(
            m.Infra.DocScope(name="project", path=root, report_dir=root / "reports"),
        )
        tm.that(scope.documentation_language, eq="pt-BR")

    def test_absent_and_explicit_english_have_identical_projection_bytes(
        self, tmp_path: Path
    ) -> None:
        """Default English does not add a field to existing pyproject consumers."""
        root = tmp_path / "project"
        absent = self._plan(root, None)
        explicit = self._plan(root, "en")
        tm.that(explicit, eq=absent)
        tm.that(absent, lacks="documentation_language")
        portuguese = self._plan(root, "pt-BR")
        tm.that(
            {
                key: value
                for key, value in u.Tests.toml_table_at(
                    portuguese, "tool", "flext", "docs"
                ).items()
                if key != "documentation_language"
            },
            eq=u.Tests.toml_table_at(absent, "tool", "flext", "docs"),
        )

    def test_existing_custom_docs_survive_language_projection_and_reset(
        self, tmp_path: Path
    ) -> None:
        """An existing CUSTOM table cannot override or retain the owned locale leaf."""
        root = tmp_path / "project"
        english = self._plan(root, None)
        document = tm.not_none(u.Cli.toml_parse_text(english))
        custom_docs = u.Cli.toml_ensure_path(document, ("tool", "flext", "docs"))
        custom_docs["site_title"] = "Título autoral"
        custom_docs["exclude_docs"] = ["private/**"]
        vendor = u.Cli.toml_ensure_path(document, ("tool", "bandit"))
        vendor["exclude_dirs"] = ["private"]
        managed = u.Cli.toml_ensure_path(document, ("tool", "ruff"))
        managed["obsolete_owned_key"] = True
        managed["obsolete_owned_child"] = {"obsolete_owned_key": True}
        custom = u.Cli.toml_dumps(document)
        root.mkdir(parents=True, exist_ok=True)
        path = root / c.PYPROJECT_FILENAME
        path.write_text(custom, encoding=c.DEFAULT_ENCODING)
        canonical_english = self._plan(root, "en")
        tm.that(canonical_english, lacks="obsolete_owned_")
        tm.that(
            u.Tests.toml_table_at(canonical_english, "tool", "flext", "docs")[
                "site_title"
            ],
            eq="Título autoral",
        )
        path.write_text(canonical_english, encoding=c.DEFAULT_ENCODING)
        portuguese = self._plan(root, "pt-BR")
        docs = u.Tests.toml_table_at(portuguese, "tool", "flext", "docs")
        tm.that(docs["documentation_language"], eq="pt-BR")
        tm.that(docs["site_title"], eq="Título autoral")
        tm.that(docs["exclude_docs"], eq=["private/**"])
        tm.that(
            u.Tests.toml_table_at(portuguese, "tool", "bandit"),
            eq={"exclude_dirs": ["private"]},
        )
        path.write_text(portuguese, encoding=c.DEFAULT_ENCODING)
        tm.that(self._plan(root, "pt-BR"), eq=portuguese)
        reset = self._plan(root, "en")
        tm.that(reset, lacks="documentation_language")
        tm.that(reset, eq=canonical_english)
        tm.that(
            u.Tests.toml_table_at(reset, "tool", "flext", "docs")["site_title"],
            eq="Título autoral",
        )
        path.write_text(reset, encoding=c.DEFAULT_ENCODING)
        tm.that(self._plan(root, None), eq=reset)

    def test_invalid_core_namespace_remains_a_causal_ingress_failure(
        self, tmp_path: Path
    ) -> None:
        """Do not turn strict Core validation into a repair or a locale fallback."""
        root = tmp_path / "project"
        document = tm.not_none(u.Cli.toml_parse_text(self._plan(root, None)))
        namespace = u.Cli.toml_ensure_path(document, c.Infra.CONFORM_NAMESPACE_TABLE)
        namespace["obsolete_owned_key"] = True
        invalid = u.Cli.toml_dumps(document)
        path = root / c.PYPROJECT_FILENAME
        path.write_text(invalid, encoding=c.DEFAULT_ENCODING)
        result = u.Infra.read_project_metadata_result(root)
        tm.fail(result, has="tool.flext.namespace.obsolete_owned_key")
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=invalid)
