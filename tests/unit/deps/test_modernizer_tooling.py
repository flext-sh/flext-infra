"""Tooling phase tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit
from flext_tests import tm

from flext_infra.deps.phases.ensure_formatting import (
    FlextInfraEnsureFormattingToolingPhase,
)
from flext_infra.deps.phases.ensure_namespace import (
    FlextInfraEnsureNamespaceToolingPhase,
)
from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


class TestsFlextInfraDepsModernizerTooling:
    """Declarative tests for formatting, namespace, and Ruff phases."""

    def test_typecheck_policy_keeps_tracked_surfaces_visible(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Keep every tracked Python surface visible to all four analyzers."""
        tools = tool_config_document.tools
        tracked_surfaces = {"examples", "scripts", "src", "tests"}
        hidden_globs = {"**/examples", "**/examples/**", "**/tests", "**/tests/**"}

        tm.that(set(tools.ruff.src), eq=tracked_surfaces)
        tm.that(tracked_surfaces.isdisjoint(tools.ruff.exclude), eq=True)
        tm.that(tools.mypy.exclude, eq=r"^legado(?:/|$)")
        tm.that(set(tools.pyright.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(
            hidden_globs.isdisjoint(tools.pyright.path_rules.default_excludes), eq=True
        )
        tm.that(set(tools.pyrefly.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(hidden_globs.isdisjoint(tools.pyrefly.project_exclude_globs), eq=True)

    def test_formatting_phase_sets_expected_state(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render every managed formatting tool from typed policy."""
        doc = tomlkit.document()

        _ = FlextInfraEnsureFormattingToolingPhase(tool_config_document).apply(doc)

        tool = u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])
        codespell = u.Tests.toml_mapping(tool["codespell"])
        tomlsort = u.Tests.toml_mapping(tool["tomlsort"])
        yamlfix = u.Tests.toml_mapping(tool["yamlfix"])
        tm.that(
            codespell["check-filenames"],
            eq=tool_config_document.tools.codespell.check_filenames,
        )
        tm.that(
            codespell["ignore-words-list"],
            eq=tool_config_document.tools.codespell.ignore_words_list,
        )
        tm.that(tomlsort["all"], eq=tool_config_document.tools.tomlsort.all)
        tm.that(tomlsort["in_place"], eq=tool_config_document.tools.tomlsort.in_place)
        tm.that(
            list(u.Tests.toml_strings(tomlsort["sort_first"])),
            eq=sorted(tool_config_document.tools.tomlsort.sort_first),
        )
        tm.that(
            yamlfix["line_length"], eq=tool_config_document.tools.yamlfix.line_length
        )
        tm.that(
            yamlfix["preserve_quotes"],
            eq=tool_config_document.tools.yamlfix.preserve_quotes,
        )
        tm.that(yamlfix["whitelines"], eq=tool_config_document.tools.yamlfix.whitelines)
        tm.that(
            yamlfix["section_whitelines"],
            eq=tool_config_document.tools.yamlfix.section_whitelines,
        )
        tm.that(
            yamlfix["explicit_start"],
            eq=tool_config_document.tools.yamlfix.explicit_start,
        )

    def test_formatting_phase_is_idempotent(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Keep formatting output stable after the first application."""
        phase = FlextInfraEnsureFormattingToolingPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])

    def test_formatting_phase_removes_codespell_skip(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Remove the obsolete codespell skip setting."""
        phase = FlextInfraEnsureFormattingToolingPhase(tool_config_document)
        doc = tomlkit.parse(
            """
[tool.codespell]
check-filenames = true
ignore-words-list = "crate,nd"
skip = ".git,poetry.lock"
"""
        )

        changes = phase.apply(doc)

        tool = u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])
        codespell = u.Tests.toml_mapping(tool["codespell"])
        tm.that(codespell, lacks="skip")
        tm.that(changes, has="removed codespell.skip hardcode")

    def test_namespace_phase_sets_detected_first_party(self, tmp_path: Path) -> None:
        """Detect the project package as first-party code."""
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        doc = tomlkit.document()

        _ = FlextInfraEnsureNamespaceToolingPhase().apply(
            doc, path=project_dir / "pyproject.toml"
        )

        deptry = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["deptry"]
        )
        tm.that(
            list(u.Tests.toml_strings(deptry["known_first_party"])),
            eq=["flext_core", "flext_sample"],
        )

    def test_namespace_phase_includes_workspace_source_packages(
        self, tmp_path: Path
    ) -> None:
        """Include declared workspace dependencies in first-party packages."""
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        doc = tomlkit.parse(
            """
[project]
dependencies = ["flext-core>=0.1.0"]

[tool.uv.sources.flext-core]
workspace = true
"""
        )

        _ = FlextInfraEnsureNamespaceToolingPhase().apply(
            doc, path=project_dir / "pyproject.toml"
        )

        deptry = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["deptry"]
        )
        tm.that(
            list(u.Tests.toml_strings(deptry["known_first_party"])),
            eq=["flext_core", "flext_sample"],
        )

    def test_ruff_phase_sets_expected_state(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render Ruff policy while retaining tracked test roots."""
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        test_dir = project_dir / "tests"
        fixture_dir = test_dir / "fixtures"
        package_dir.mkdir(parents=True, exist_ok=True)
        fixture_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        _ = (fixture_dir / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        _ = (test_dir / "test_dummy.py").write_text(
            "def test_dummy() -> None:\n    assert True\n", encoding="utf-8"
        )
        doc = tomlkit.parse(
            """
[lint]
select = ["E501"]

[tool.ruff.lint.per-file-ignores]
"old.py" = ["E402"]
"""
        )

        _ = FlextInfraEnsureRuffConfigPhase(tool_config_document).apply(
            doc, path=project_dir / "pyproject.toml"
        )

        root = u.Tests.toml_doc_mapping(doc)
        tm.that(root, lacks="lint")
        ruff = u.Tests.toml_mapping(u.Tests.toml_mapping(root["tool"])["ruff"])
        tm.that(
            set(u.Tests.toml_strings(ruff["exclude"])),
            eq=set(tool_config_document.tools.ruff.exclude),
        )
        tm.that(ruff["fix"], eq=tool_config_document.tools.ruff.fix)
        tm.that(ruff["line-length"], eq=tool_config_document.tools.ruff.line_length)
        tm.that(ruff["preview"], eq=tool_config_document.tools.ruff.preview)
        tm.that(
            ruff["respect-gitignore"],
            eq=tool_config_document.tools.ruff.respect_gitignore,
        )
        tm.that(ruff["show-fixes"], eq=tool_config_document.tools.ruff.show_fixes)
        tm.that(
            ruff["target-version"], eq=tool_config_document.tools.ruff.target_version
        )
        tm.that(set(u.Tests.toml_strings(ruff["src"])), eq={"src", "tests"})
        format_section = u.Tests.toml_mapping(ruff["format"])
        tm.that(
            format_section["docstring-code-format"],
            eq=tool_config_document.tools.ruff.format.docstring_code_format,
        )
        lint_section = u.Tests.toml_mapping(ruff["lint"])
        tm.that(
            set(u.Tests.toml_strings(lint_section["select"])),
            eq=set(tool_config_document.tools.ruff.lint.select),
        )
        tm.that(
            set(u.Tests.toml_strings(lint_section["ignore"])),
            eq=set(tool_config_document.tools.ruff.lint.ignore),
        )
        isort = u.Tests.toml_mapping(lint_section["isort"])
        tm.that(
            isort["combine-as-imports"],
            eq=tool_config_document.tools.ruff.lint.isort.combine_as_imports,
        )
        tm.that(
            list(u.Tests.toml_strings(isort["known-first-party"])),
            eq=["flext_core", "flext_sample"],
        )
        tm.that(
            u.Tests.toml_mapping(lint_section["per-file-ignores"]),
            eq={
                pattern: sorted(rules)
                for pattern, rules in tool_config_document.tools.ruff.lint.per_file_ignores.items()
            },
        )

    def test_ruff_phase_is_idempotent(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Keep the Ruff phase stable after the first application."""
        project_dir = tmp_path / "flext-sample"
        package_dir = project_dir / "src" / "flext_sample"
        package_dir.mkdir(parents=True, exist_ok=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        phase = FlextInfraEnsureRuffConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc, path=project_dir / "pyproject.toml")
        second_changes = phase.apply(doc, path=project_dir / "pyproject.toml")

        tm.that(second_changes, eq=[])

    def test_ruff_phase_skips_attached_workspace_namespaces(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Exclude attached consumer namespaces from FLEXT first-party names."""
        workspace_root = tmp_path / "workspace"
        project_dir = workspace_root / "demo-migration-tool"
        internal_project = workspace_root / "flext-core"
        project_dir.joinpath("src", "demo_migration_tool").mkdir(
            parents=True, exist_ok=True
        )
        internal_project.joinpath("src", "flext_core").mkdir(
            parents=True, exist_ok=True
        )
        _ = project_dir.joinpath(
            "src", "demo_migration_tool", "__init__.py"
        ).write_text("", encoding="utf-8")
        _ = internal_project.joinpath("src", "flext_core", "__init__.py").write_text(
            "", encoding="utf-8"
        )
        _ = project_dir.joinpath("pyproject.toml").write_text(
            '[project]\nname = "demo-migration-tool"\nversion = "0.1.0"\ndependencies = ["flext-core>=0.1.0"]\n',
            encoding="utf-8",
        )
        _ = workspace_root.joinpath("pyproject.toml").write_text(
            "[project]\nname = 'workspace'\n\n"
            "[tool.uv.workspace]\n"
            "members = ['flext-core']\n",
            encoding="utf-8",
        )
        _ = internal_project.joinpath("pyproject.toml").write_text(
            '[project]\nname = "flext-core"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        doc = tomlkit.document()

        _ = FlextInfraEnsureRuffConfigPhase(tool_config_document).apply(
            doc, path=workspace_root / "pyproject.toml"
        )

        ruff = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["ruff"]
        )
        lint_section = u.Tests.toml_mapping(ruff["lint"])
        isort = u.Tests.toml_mapping(lint_section["isort"])
        known_first_party = list(u.Tests.toml_strings(isort["known-first-party"]))
        tm.that(known_first_party, has="flext_core")
        tm.that("demo_migration_tool" in known_first_party, eq=False)
