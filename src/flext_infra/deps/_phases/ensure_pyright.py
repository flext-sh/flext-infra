"""Phase: Ensure standard Pyright configuration for strict type checking."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import tomlkit
from tomlkit.items import Item, Table

from flext_infra import c, m, u


class EnsurePyrightConfigPhase:
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def _expected_envs(
        self,
        *,
        is_root: bool,
        workspace_root: Path | None,
        project_dir: Path | None = None,
    ) -> Sequence[Mapping[str, str]]:
        if not is_root:
            return self._expected_envs_for_project(project_dir)
        if workspace_root is None:
            return self._expected_envs_for_project(project_dir)

        expected_envs: Sequence[Mapping[str, str]] = []
        root_src = workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR
        root_tests = workspace_root / c.Infra.Directories.TESTS
        root_examples = workspace_root / c.Infra.Directories.EXAMPLES
        root_scripts = workspace_root / c.Infra.Directories.SCRIPTS
        if root_src.exists():
            expected_envs.append({
                "root": c.Infra.Paths.DEFAULT_SRC_DIR,
                "reportPrivateUsage": "error",
            })
        if root_tests.exists():
            expected_envs.append({
                "root": c.Infra.Directories.TESTS,
                "reportPrivateUsage": "none",
            })
        if root_examples.exists():
            expected_envs.append({
                "root": c.Infra.Directories.EXAMPLES,
                "reportPrivateUsage": "none",
            })
        if root_scripts.exists():
            expected_envs.append({
                "root": c.Infra.Directories.SCRIPTS,
                "reportPrivateUsage": "none",
            })

        child_projects = sorted(
            child
            for child in workspace_root.iterdir()
            if child.is_dir() and (child / c.Infra.Files.PYPROJECT_FILENAME).exists()
        )
        for child_project in child_projects:
            relative_root = child_project.relative_to(workspace_root)
            child_src = child_project / c.Infra.Paths.DEFAULT_SRC_DIR
            child_tests = child_project / c.Infra.Directories.TESTS
            child_examples = child_project / c.Infra.Directories.EXAMPLES
            child_scripts = child_project / c.Infra.Directories.SCRIPTS
            if child_src.exists():
                expected_envs.append({
                    "root": (relative_root / c.Infra.Paths.DEFAULT_SRC_DIR).as_posix(),
                    "reportPrivateUsage": "error",
                })
            if child_tests.exists():
                expected_envs.append({
                    "root": (relative_root / c.Infra.Directories.TESTS).as_posix(),
                    "reportPrivateUsage": "none",
                })
            if child_examples.exists():
                expected_envs.append({
                    "root": (relative_root / c.Infra.Directories.EXAMPLES).as_posix(),
                    "reportPrivateUsage": "none",
                })
            if child_scripts.exists():
                expected_envs.append({
                    "root": (relative_root / c.Infra.Directories.SCRIPTS).as_posix(),
                    "reportPrivateUsage": "none",
                })
        return expected_envs

    @staticmethod
    def _expected_envs_for_project(
        project_dir: Path | None,
    ) -> Sequence[Mapping[str, str]]:
        """Build executionEnvironments dynamically from discovered dirs."""
        if project_dir is None:
            return [
                {"root": c.Infra.Paths.DEFAULT_SRC_DIR, "reportPrivateUsage": "error"},
                {"root": c.Infra.Directories.TESTS, "reportPrivateUsage": "none"},
            ]
        discovered = u.Infra.discover_python_dirs(project_dir)
        envs: Sequence[Mapping[str, str]] = []
        for dir_name in discovered:
            if dir_name == c.Infra.Paths.DEFAULT_SRC_DIR:
                envs.append({"root": dir_name, "reportPrivateUsage": "error"})
            else:
                envs.append({"root": dir_name, "reportPrivateUsage": "none"})
        if not envs:
            return [
                {"root": c.Infra.Paths.DEFAULT_SRC_DIR, "reportPrivateUsage": "error"},
                {"root": c.Infra.Directories.TESTS, "reportPrivateUsage": "none"},
            ]
        return envs

    def _override_for_kind(
        self,
        project_kind: str,
    ) -> m.Infra.ProjectTypeOverrideConfig | None:
        """Return the project-type override config for the given kind, if any."""
        overrides = self._tool_config.project_type_overrides
        kind_map: Mapping[str, m.Infra.ProjectTypeOverrideConfig] = {
            "core": overrides.core,
            "domain": overrides.domain,
            "platform": overrides.platform,
            "integration": overrides.integration,
            "app": overrides.app,
        }
        return kind_map.get(project_kind)

    def apply(
        self,
        doc: tomlkit.TOMLDocument,
        *,
        is_root: bool,
        workspace_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
    ) -> Sequence[str]:
        changes: Sequence[str] = []
        tool: Item | None = None
        if c.Infra.Toml.TOOL in doc:
            raw_tool = doc[c.Infra.Toml.TOOL]
            if isinstance(raw_tool, Item):
                tool = raw_tool
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.Toml.TOOL] = tool
        pyright = u.Infra.ensure_table(tool, c.Infra.Toml.PYRIGHT)
        expected_envs = self._expected_envs(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
        if is_root:
            if (
                u.Infra.unwrap_item(u.Infra.get(pyright, "typeCheckingMode"))
                != c.Infra.Modes.STRICT
            ):
                pyright["typeCheckingMode"] = c.Infra.Modes.STRICT
                changes.append("tool.pyright.typeCheckingMode set to strict")
            for key, value in self._tool_config.tools.pyright.extended_settings.items():
                if u.Infra.unwrap_item(u.Infra.get(pyright, key)) != value:
                    pyright[key] = value
                    changes.append(f"tool.pyright.{key} set to {value}")
            u.Infra.ensure_pyright_execution_envs(pyright, expected_envs, changes)
            return changes
        for key, value in self._tool_config.tools.pyright.strict_settings.items():
            if u.Infra.unwrap_item(u.Infra.get(pyright, key)) != value:
                pyright[key] = value
                changes.append(f"tool.pyright.{key} set to {value}")
        # Merge extended_settings with project_kind overrides BEFORE applying
        # to avoid double-change noise (set to X then immediately override to Y)
        merged_settings: Mapping[str, str] = {
            **self._tool_config.tools.pyright.extended_settings,
        }
        override = self._override_for_kind(project_kind)
        if override is not None:
            merged_settings.update(override.pyright)
        for key, value in merged_settings.items():
            if u.Infra.unwrap_item(u.Infra.get(pyright, key)) != value:
                pyright[key] = value
                changes.append(f"tool.pyright.{key} set to {value}")
        u.Infra.ensure_pyright_execution_envs(pyright, expected_envs, changes)
        return changes
