"""Phase: Ensure standard Pyright configuration for strict type checking."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import override

import tomlkit
from tomlkit.items import Item, Table

from flext_infra import FlextInfraExtraPathsManager, c, m, t, u

from .ensure_pyright_envs import FlextInfraEnsurePyrightEnvs


class FlextInfraEnsurePyrightConfigPhase(FlextInfraEnsurePyrightEnvs):
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    @override
    def _path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        return self._tool_config.tools.pyright.path_rules

    @override
    def _suppressions_for_env(self, env_dir: str) -> t.StrMapping:
        """Return merged pyright suppressions for the given env directory."""
        pyright_cfg = self._tool_config.tools.pyright
        merged: t.MutableStrMapping = {**pyright_cfg.lazy_import_suppressions}
        rules = self._path_rules()
        if env_dir == rules.source_dir:
            merged.update(pyright_cfg.source_env_suppressions)
        elif env_dir in set(rules.test_like_dirs):
            merged.update(pyright_cfg.test_like_env_suppressions)
        return merged

    @override
    def _report_private_usage_for_env(self, env_dir: str) -> str:
        rules = self._path_rules()
        if env_dir == rules.source_dir:
            return rules.source_report_private_usage
        if env_dir in set(rules.test_like_dirs):
            return rules.test_like_report_private_usage
        return rules.other_report_private_usage

    def _override_for_kind(
        self,
        project_kind: str,
    ) -> m.Infra.ProjectTypeOverrideConfig | None:
        """Return the project-type override config for the given kind."""
        overrides = self._tool_config.project_type_overrides
        kind_map: Mapping[str, m.Infra.ProjectTypeOverrideConfig] = {
            "core": overrides.core,
            "domain": overrides.domain,
            "platform": overrides.platform,
            "integration": overrides.integration,
            "app": overrides.app,
        }
        return kind_map.get(project_kind)

    def _venv_settings(
        self,
        *,
        is_root: bool,
    ) -> t.StrMapping:
        rules = self._path_rules()
        venv_path = rules.root_venv_path if is_root else rules.project_venv_path
        return {
            "venvPath": venv_path,
            "venv": rules.venv_name,
        }

    def _expected_excludes(self, project_root: Path | None) -> t.StrSequence:
        """Build pyright exclude list from discovered workspace/project dirs."""
        rules = self._path_rules()
        default_excludes = set(rules.default_excludes)
        if project_root is None or not project_root.is_dir():
            return sorted(default_excludes)
        dynamic_excludes = {
            directory
            for directory in sorted(rules.dynamic_exclude_dirs)
            if (project_root / directory).is_dir()
        }
        return sorted(default_excludes | dynamic_excludes)

    def _existing_paths(
        self,
        base_dir: Path | None,
        configured_paths: t.StrSequence,
    ) -> t.StrSequence:
        if base_dir is None:
            return []
        existing: t.StrSequence = [
            relative_path
            for relative_path in configured_paths
            if (base_dir / relative_path).is_dir()
        ]
        return existing

    def _expected_ignores(
        self,
        *,
        is_root: bool,
        workspace_root: Path | None,
        project_dir: Path | None,
    ) -> t.StrSequence:
        """Ignore typings and stub diagnostics."""
        rules = self._path_rules()
        ignores: MutableSequence[str] = []
        if is_root:
            root_dir = workspace_root or project_dir
            ignores.extend(self._existing_paths(root_dir, rules.root_typings_paths))
        else:
            ignores.extend(
                self._existing_paths(project_dir, rules.project_typings_paths)
            )
        for pattern in rules.ignored_diagnostic_globs:
            if pattern not in ignores:
                ignores.append(pattern)
        return list(ignores)

    def apply(
        self,
        doc: tomlkit.TOMLDocument,
        *,
        is_root: bool,
        workspace_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
    ) -> t.StrSequence:
        changes: MutableSequence[str] = []
        tool: Item | None = None
        if c.Infra.TOOL in doc:
            raw_tool = doc[c.Infra.TOOL]
            if isinstance(raw_tool, Item):
                tool = raw_tool
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        pyright = u.Infra.ensure_table(tool, c.Infra.PYRIGHT)
        project_root = workspace_root if is_root else project_dir
        expected_excludes = self._expected_excludes(project_root)
        current_excludes = u.Infra.as_string_list(u.Infra.get(pyright, c.Infra.EXCLUDE))
        if expected_excludes:
            if current_excludes != expected_excludes:
                pyright[c.Infra.EXCLUDE] = u.Infra.array(expected_excludes)
                changes.append("tool.pyright.exclude synchronized from discovered dirs")
        elif c.Infra.EXCLUDE in pyright:
            del pyright[c.Infra.EXCLUDE]
            changes.append("tool.pyright.exclude removed (no discovered excludes)")
        expected_ignores = self._expected_ignores(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
        current_ignores = u.Infra.as_string_list(u.Infra.get(pyright, c.Infra.IGNORE))
        if expected_ignores:
            if current_ignores != expected_ignores:
                pyright[c.Infra.IGNORE] = u.Infra.array(expected_ignores)
                changes.append(
                    "tool.pyright.ignore synchronized for typings diagnostics",
                )
        elif c.Infra.IGNORE in pyright:
            del pyright[c.Infra.IGNORE]
            changes.append("tool.pyright.ignore removed (no discovered ignores)")
        stub_rules = self._path_rules()
        expected_stub_path: str | None = (
            stub_rules.root_typings_paths[0]
            if is_root and stub_rules.root_typings_paths
            else (
                stub_rules.project_typings_paths[0]
                if stub_rules.project_typings_paths
                else None
            )
        )
        if expected_stub_path is not None:
            existing = project_root / expected_stub_path if project_root else None
            if existing is not None and existing.is_dir():
                current_stub = u.Infra.unwrap_item(u.Infra.get(pyright, "stubPath"))
                if current_stub != expected_stub_path:
                    pyright["stubPath"] = expected_stub_path
                    changes.append(
                        f"tool.pyright.stubPath set to {expected_stub_path}",
                    )
            elif "stubPath" in pyright:
                del pyright["stubPath"]
                changes.append("tool.pyright.stubPath removed (typings dir missing)")
        elif "stubPath" in pyright:
            del pyright["stubPath"]
            changes.append("tool.pyright.stubPath removed (no typings configured)")
        if project_root is not None:
            expected_extra = FlextInfraExtraPathsManager().pyright_extra_paths(
                project_dir=project_root,
                is_root=is_root,
            )
            current_extra = u.Infra.as_string_list(u.Infra.get(pyright, "extraPaths"))
            if current_extra != expected_extra:
                pyright["extraPaths"] = u.Infra.array(expected_extra)
                changes.append("tool.pyright.extraPaths synchronized")
        expected_envs = self._expected_envs(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
        for key, value in self._venv_settings(is_root=is_root).items():
            if u.Infra.unwrap_item(u.Infra.get(pyright, key)) != value:
                pyright[key] = value
                changes.append(f"tool.pyright.{key} set to {value}")
        if is_root:
            for key, value in self._tool_config.tools.pyright.strict_settings.items():
                if u.Infra.unwrap_item(u.Infra.get(pyright, key)) != value:
                    pyright[key] = value
                    changes.append(f"tool.pyright.{key} set to {value}")
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
        merged_settings: t.MutableStrMapping = {
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


__all__ = ["FlextInfraEnsurePyrightConfigPhase"]
