"""Project-owned Mise tools: declaration, composition, and lock platform scope."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import config, m, u
from flext_tests import tm

_RENDERED = '[settings]\nlockfile = true\n\n[tools]\npython = "3.13"\n'


def _project(root: Path, tools_yaml: str) -> Path:
    root.mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config" / "managed-artifacts.yaml").write_text(
        tools_yaml, encoding="utf-8"
    )
    return root


def _fleet_platforms() -> tuple[str, ...]:
    return tuple(config.Infra.codegen.toolchain.mise_lock_platforms)


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

        document = tomllib.loads(tm.ok(composed))
        assert document["tools"]["github:example/tool"] == "1.2.3"
        assert document["tools"]["python"] == "3.13"

    def test_platform_subset_becomes_lock_exclusion(self, tmp_path: Path) -> None:
        fleet = _fleet_platforms()
        kept = fleet[:2]
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool":\n'
            '        version: "1.2.3"\n'
            f"        platforms: [{', '.join(kept)}]\n",
        )

        exclusions = u.Infra.lock_platform_exclusions(root)

        assert tm.ok(exclusions) == {
            "github:example/tool": frozenset(fleet) - frozenset(kept)
        }

    def test_full_platform_coverage_declares_no_exclusion(self, tmp_path: Path) -> None:
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool":\n'
            '        version: "1.2.3"\n',
        )

        exclusions = u.Infra.lock_platform_exclusions(root)

        assert tm.ok(exclusions) == {}

    def test_empty_platform_list_declares_no_lock_platforms(
        self, tmp_path: Path
    ) -> None:
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "npm:example-tool":\n'
            '        version: "1.2.3"\n'
            "        platforms: []\n",
        )

        exclusions = u.Infra.lock_platform_exclusions(root)

        assert tm.ok(exclusions) == {"npm:example-tool": frozenset(_fleet_platforms())}

    def test_platform_outside_fleet_is_rejected(self, tmp_path: Path) -> None:
        root = _project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool":\n'
            '        version: "1.2.3"\n'
            "        platforms: [plan9-mips]\n",
        )

        loaded = u.Infra.load_project_managed_artifacts(root)

        tm.fail(loaded, has=["outside the fleet lock platforms", "plan9-mips"])

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
