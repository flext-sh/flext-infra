"""Project-owned Mise tools: declaration, composition, and lock platform scope."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_tests import tm
from tests import u

_RENDERED = '[settings]\nlockfile = true\n\n[tools]\npython = "3.13"\n'


def _project(root: Path, tools_yaml: str) -> Path:
    root.mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config" / "managed-artifacts.yaml").write_text(
        tools_yaml, encoding="utf-8"
    )
    return root


class TestsProjectMiseTools:
    """A project declares its own tools without touching the fleet catalog."""

    def test_declared_tool_reaches_generated_mise_toml(self, tmp_path: Path) -> None:
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool":\n'
            '        version: "1.2.3"\n',
        )

        composed = u.Infra.compose_mise_toml(root, _RENDERED)

        tools = u.Tests.toml_table_at(tm.ok(composed), "tools")
        assert tools["github:example/tool"] == "1.2.3"
        assert tools["python"] == "3.13"

    def test_version_string_shorthand_is_not_a_declaration(
        self, tmp_path: Path
    ) -> None:
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool": "1.2.3"\n',
        )

        try:
            u.Infra.load_project_managed_artifacts(root)
        except m.ValidationError:
            return
        msg = "a bare version string must not validate as a project tool"
        raise AssertionError(msg)
