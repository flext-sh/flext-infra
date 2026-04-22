"""Tooling phase tests for deps modernizer."""

from __future__ import annotations

from pathlib import Path

import tomlkit

from flext_infra import (
    FlextInfraEnsureFormattingToolingPhase,
    FlextInfraEnsureNamespaceToolingPhase,
    FlextInfraEnsureRuffConfigPhase,
)
from tests import m, tm, u


class TestDepsModernizerTooling:
    """Declarative tests for formatting, namespace, and Ruff phases."""

    def test_formatting_phase_sets_expected_state(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.document()

        _ = FlextInfraEnsureFormattingToolingPhase(tool_config_document).apply(doc)

        tool = u.Infra.Tests.toml_mapping(u.Infra.Tests.toml_doc_mapping(doc)["tool"])
        codespell = u.Infra.Tests.toml_mapping(tool["codespell"])
        tomlsort = u.Infra.Tests.toml_mapping(tool["tomlsort"])
        yamlfix = u.Infra.Tests.toml_mapping(tool["yamlfix"])
        assert (
            codespell["check-filenames"]
            == tool_config_document.tools.codespell.check_filenames
        )
        assert (
            codespell["ignore-words-list"]
            == tool_config_document.tools.codespell.ignore_words_list
        )
        assert tomlsort["all"] == tool_config_document.tools.tomlsort.all
        assert tomlsort["in_place"] == tool_config_document.tools.tomlsort.in_place
        assert list(u.Infra.Tests.toml_strings(tomlsort["sort_first"])) == sorted(
            tool_config_document.tools.tomlsort.sort_first,
        )
        assert yamlfix["line_length"] == tool_config_document.tools.yamlfix.line_length
        assert (
            yamlfix["preserve_quotes"]
            == tool_config_document.tools.yamlfix.preserve_quotes
        )
        assert yamlfix["whitelines"] == tool_config_document.tools.yamlfix.whitelines
        assert (
            yamlfix["section_whitelines"]
            == tool_config_document.tools.yamlfix.section_whitelines
        )
        assert (
            yamlfix["explicit_start"]
            == tool_config_document.tools.yamlfix.explicit_start
        )

    def test_formatting_phase_is_idempotent(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        phase = FlextInfraEnsureFormattingToolingPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        assert second_changes == []

    def test_formatting_phase_removes_codespell_skip(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        phase = FlextInfraEnsureFormattingToolingPhase(tool_config_document)
        doc = tomlkit.parse(
            """
[tool.codespell]
check-filenames = true
ignore-words-list = "crate,nd"
skip = ".git,poetry.lock"
""",
        )

        changes = phase.apply(doc)

        tool = u.Infra.Tests.toml_mapping(u.Infra.Tests.toml_doc_mapping(doc)["tool"])
        codespell = u.Infra.Tests.toml_mapping(tool["codespell"])
        assert "skip" not in codespell
        tm.that(changes, has="removed codespell.skip hardcode")

    def test_namespace_phase_sets_detected_first_party(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        doc = tomlkit.document()

        _ = FlextInfraEnsureNamespaceToolingPhase().apply(
            doc,
            path=project_dir / "pyproject.toml",
        )

        deptry = u.Infra.Tests.toml_mapping(
            u.Infra.Tests.toml_mapping(u.Infra.Tests.toml_doc_mapping(doc)["tool"])[
                "deptry"
            ],
        )
        assert list(u.Infra.Tests.toml_strings(deptry["known_first_party"])) == [
            "flext_sample",
        ]

    def test_ruff_phase_sets_expected_state(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        test_dir = project_dir / "tests"
        fixture_dir = test_dir / "fixtures"
        package_dir.mkdir(parents=True, exist_ok=True)
        fixture_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        _ = (fixture_dir / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        _ = (test_dir / "test_dummy.py").write_text(
            "def test_dummy() -> None:\n    assert True\n",
            encoding="utf-8",
        )
        doc = tomlkit.parse(
            """
[lint]
select = ["E501"]

[tool.ruff.lint.per-file-ignores]
"old.py" = ["E402"]
""",
        )

        _ = FlextInfraEnsureRuffConfigPhase(tool_config_document).apply(
            doc,
            path=project_dir / "pyproject.toml",
        )

        root = u.Infra.Tests.toml_doc_mapping(doc)
        assert "lint" not in root
        ruff = u.Infra.Tests.toml_mapping(
            u.Infra.Tests.toml_mapping(root["tool"])["ruff"],
        )
        assert set(u.Infra.Tests.toml_strings(ruff["exclude"])) == set(
            tool_config_document.tools.ruff.exclude,
        )
        assert ruff["fix"] == tool_config_document.tools.ruff.fix
        assert ruff["line-length"] == tool_config_document.tools.ruff.line_length
        assert ruff["preview"] == tool_config_document.tools.ruff.preview
        assert (
            ruff["respect-gitignore"]
            == tool_config_document.tools.ruff.respect_gitignore
        )
        assert ruff["show-fixes"] == tool_config_document.tools.ruff.show_fixes
        assert ruff["target-version"] == tool_config_document.tools.ruff.target_version
        assert set(u.Infra.Tests.toml_strings(ruff["src"])) == {"src", "tests"}
        format_section = u.Infra.Tests.toml_mapping(ruff["format"])
        assert (
            format_section["docstring-code-format"]
            == tool_config_document.tools.ruff.format.docstring_code_format
        )
        lint_section = u.Infra.Tests.toml_mapping(ruff["lint"])
        assert set(u.Infra.Tests.toml_strings(lint_section["select"])) == set(
            tool_config_document.tools.ruff.lint.select,
        )
        assert set(u.Infra.Tests.toml_strings(lint_section["ignore"])) == set(
            tool_config_document.tools.ruff.lint.ignore,
        )
        isort = u.Infra.Tests.toml_mapping(lint_section["isort"])
        assert (
            isort["combine-as-imports"]
            == tool_config_document.tools.ruff.lint.isort.combine_as_imports
        )
        assert list(u.Infra.Tests.toml_strings(isort["known-first-party"])) == [
            "flext_sample",
        ]
        assert u.Infra.Tests.toml_mapping(lint_section["per-file-ignores"]) == {
            pattern: sorted(rules)
            for pattern, rules in tool_config_document.tools.ruff.lint.per_file_ignores.items()
        }

    def test_ruff_phase_is_idempotent(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        phase = FlextInfraEnsureRuffConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc, path=project_dir / "pyproject.toml")
        second_changes = phase.apply(doc, path=project_dir / "pyproject.toml")

        assert second_changes == []

    def test_ruff_phase_skips_attached_workspace_namespaces(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        workspace_root = tmp_path / "workspace"
        project_dir = workspace_root / "algar-oud-mig"
        internal_project = workspace_root / "flext-core"
        project_dir.joinpath("src", "algar_oud_mig").mkdir(parents=True, exist_ok=True)
        internal_project.joinpath("src", "flext_core").mkdir(
            parents=True,
            exist_ok=True,
        )
        _ = project_dir.joinpath("src", "algar_oud_mig", "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        _ = internal_project.joinpath("src", "flext_core", "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        _ = project_dir.joinpath("pyproject.toml").write_text(
            '[project]\nname = "algar-oud-mig"\nversion = "0.1.0"\ndependencies = ["flext-core>=0.1.0"]\n',
            encoding="utf-8",
        )
        _ = workspace_root.joinpath("pyproject.toml").write_text(
            "[project]\nname = 'workspace'\n\n"
            "[tool.uv.workspace]\n"
            "members = ['flext-core']\n",
            encoding="utf-8",
        )
        _ = internal_project.joinpath("pyproject.toml").write_text(
            '[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        doc = tomlkit.document()

        _ = FlextInfraEnsureRuffConfigPhase(tool_config_document).apply(
            doc,
            path=workspace_root / "pyproject.toml",
        )

        ruff = u.Infra.Tests.toml_mapping(
            u.Infra.Tests.toml_mapping(u.Infra.Tests.toml_doc_mapping(doc)["tool"])[
                "ruff"
            ],
        )
        lint_section = u.Infra.Tests.toml_mapping(ruff["lint"])
        isort = u.Infra.Tests.toml_mapping(lint_section["isort"])
        known_first_party = list(u.Infra.Tests.toml_strings(isort["known-first-party"]))
        tm.that(known_first_party, has="flext_core")
        tm.that("algar_oud_mig" in known_first_party, eq=False)
