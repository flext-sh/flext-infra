"""Test extra paths uv sources behavior."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from tests.unit.deps._extra_paths_support import ExtraPathsTestSupport


class TestsFlextInfraExtraPathsUvSources:
    """Test flext infra extra paths uv sources behavior."""

    def test_pyrefly_search_paths_include_uv_source_path_dependencies_at_root(
        self, tmp_path: Path
    ) -> None:
        """Verify pyrefly search paths include uv source path dependencies at root."""
        consumer = tmp_path / "ai-hub"
        consumer.mkdir()
        (consumer / ".git").mkdir()
        (consumer / "ai_hub").mkdir()
        (consumer / "ai_hub" / "__init__.py").write_text("", encoding="utf-8")
        (consumer / "pyproject.toml").write_text(
            (
                "[project]\n"
                "name = 'ai-hub'\n"
                "dependencies = ['flext-core', 'flext-cli', 'skillopt']\n"
                "[tool.uv.sources]\n"
                "flext-core = { path = '../flext/flext-core', editable = true }\n"
                "flext-cli = { path = '../flext/flext-cli', editable = true }\n"
                "flext-infra = { path = '../flext/flext-infra', editable = true }\n"
                "skillopt = { path = '../SkillOpt', editable = true }\n"
            ),
            encoding="utf-8",
        )
        for dep_name, package_name in (
            ("flext-core", "flext_core"),
            ("flext-cli", "flext_cli"),
            ("flext-infra", "flext_infra"),
        ):
            dep_root = tmp_path / "flext" / dep_name
            dep_root.mkdir(parents=True)
            (dep_root / ".git").mkdir()
            (dep_root / "Makefile").write_text("", encoding="utf-8")
            (dep_root / "pyproject.toml").write_text(
                f"[project]\nname = '{dep_name}'\n", encoding="utf-8"
            )
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_src / "__init__.py").write_text("", encoding="utf-8")
            dep_examples = dep_root / "examples"
            dep_examples.mkdir()
            (dep_examples / "sample.py").write_text("", encoding="utf-8")
        skillopt_root = tmp_path / "SkillOpt"
        skillopt_root.mkdir()
        (skillopt_root / "skillopt").mkdir()
        (skillopt_root / "skillopt" / "__init__.py").write_text("", encoding="utf-8")
        (skillopt_root / "scripts").mkdir()
        (skillopt_root / "scripts" / "tool.py").write_text("", encoding="utf-8")

        manager = ExtraPathsTestSupport.manager(consumer)
        result = manager.pyrefly_search_paths(project_dir=consumer, is_root=True)

        tm.that(
            result,
            eq=[
                ".",
                "../SkillOpt",
                "../flext/flext-cli/src",
                "../flext/flext-core/src",
            ],
        )
