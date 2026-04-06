"""Tooling phase tests for deps modernizer."""

from __future__ import annotations

from pathlib import Path

import tomlkit
from flext_tests import tm
from tests import m, t, u

from flext_infra import (
    FlextInfraEnsureFormattingToolingPhase,
    FlextInfraEnsureNamespaceToolingPhase,
    FlextInfraEnsureRuffConfigPhase,
)


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


def _doc_mapping(doc: t.Cli.TomlDocument) -> t.Cli.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
        u.Cli.normalize_json_value(doc.unwrap()),
    )


def _mapping(value: t.Cli.JsonValue) -> t.Cli.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.Cli.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


class TestEnsureFormattingToolingPhase:
    """Tests formatting tooling phase behavior."""

    def test_apply_sets_expected_tomlsort_and_yamlfix_state(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.document()

        _ = FlextInfraEnsureFormattingToolingPhase(tool_config).apply(doc)

        tool = _mapping(_doc_mapping(doc)["tool"])
        tomlsort = _mapping(tool["tomlsort"])
        yamlfix = _mapping(tool["yamlfix"])
        assert tomlsort["all"] == tool_config.tools.tomlsort.all
        assert tomlsort["in_place"] == tool_config.tools.tomlsort.in_place
        assert list(_strings(tomlsort["sort_first"])) == sorted(
            tool_config.tools.tomlsort.sort_first,
        )
        assert yamlfix["line_length"] == tool_config.tools.yamlfix.line_length
        assert yamlfix["preserve_quotes"] == tool_config.tools.yamlfix.preserve_quotes
        assert yamlfix["whitelines"] == tool_config.tools.yamlfix.whitelines
        assert (
            yamlfix["section_whitelines"]
            == tool_config.tools.yamlfix.section_whitelines
        )
        assert yamlfix["explicit_start"] == tool_config.tools.yamlfix.explicit_start

    def test_apply_is_idempotent(self) -> None:
        tool_config = _test_tool_config()
        phase = FlextInfraEnsureFormattingToolingPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])


class TestEnsureNamespaceToolingPhase:
    """Tests namespace tooling phase behavior."""

    def test_apply_sets_detected_known_first_party(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src" / "flext_sample").mkdir(parents=True, exist_ok=True)
        _ = (project_dir / "src" / "flext_sample" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        doc = tomlkit.document()

        _ = FlextInfraEnsureNamespaceToolingPhase().apply(
            doc,
            path=project_dir / "pyproject.toml",
        )

        deptry_mapping = _mapping(_mapping(_doc_mapping(doc)["tool"])["deptry"])
        assert list(_strings(deptry_mapping["known_first_party"])) == ["flext_sample"]


class TestEnsureRuffConfigPhase:
    """Tests Ruff config phase behavior."""

    def test_apply_sets_expected_ruff_state(self, tmp_path: Path) -> None:
        tool_config = _test_tool_config()
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src" / "flext_sample").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
        _ = (project_dir / "src" / "flext_sample" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        _ = (project_dir / "tests" / "test_dummy.py").write_text(
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

        _ = FlextInfraEnsureRuffConfigPhase(tool_config).apply(
            doc,
            path=project_dir / "pyproject.toml",
        )

        root = _doc_mapping(doc)
        assert "lint" not in root
        ruff = _mapping(_mapping(root["tool"])["ruff"])
        assert ruff["fix"] == tool_config.tools.ruff.fix
        assert ruff["line-length"] == tool_config.tools.ruff.line_length
        assert ruff["preview"] == tool_config.tools.ruff.preview
        assert ruff["respect-gitignore"] == tool_config.tools.ruff.respect_gitignore
        assert ruff["show-fixes"] == tool_config.tools.ruff.show_fixes
        assert ruff["target-version"] == tool_config.tools.ruff.target_version
        assert set(_strings(ruff["src"])) == {"src", "tests"}
        format_section = _mapping(ruff["format"])
        assert (
            format_section["docstring-code-format"]
            == tool_config.tools.ruff.format.docstring_code_format
        )
        lint_section = _mapping(ruff["lint"])
        assert set(_strings(lint_section["select"])) == set(
            tool_config.tools.ruff.lint.select
        )
        assert set(_strings(lint_section["ignore"])) == set(
            tool_config.tools.ruff.lint.ignore
        )
        isort = _mapping(lint_section["isort"])
        assert (
            isort["combine-as-imports"]
            == tool_config.tools.ruff.lint.isort.combine_as_imports
        )
        assert list(_strings(isort["known-first-party"])) == ["flext_sample"]
        assert _mapping(lint_section["per-file-ignores"]) == {
            pattern: sorted(rules)
            for pattern, rules in tool_config.tools.ruff.lint.per_file_ignores.items()
        }

    def test_apply_is_idempotent(self, tmp_path: Path) -> None:
        tool_config = _test_tool_config()
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src" / "flext_sample").mkdir(parents=True, exist_ok=True)
        _ = (project_dir / "src" / "flext_sample" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        phase = FlextInfraEnsureRuffConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc, path=project_dir / "pyproject.toml")
        second_changes = phase.apply(doc, path=project_dir / "pyproject.toml")

        tm.that(second_changes, eq=[])
