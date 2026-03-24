"""Phase: Ensure standard Pyright configuration for strict type checking."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import tomlkit
from tomlkit.items import Item, Table

from flext_infra import FlextInfraExtraPathsManager, c, m, t, u


class FlextInfraEnsurePyrightConfigPhase:
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    @staticmethod
    def _env_entry(
        *,
        root: str,
        report_private_usage: str,
        extra_paths: Sequence[str],
    ) -> t.Infra.ContainerDict:
        return {
            "root": root,
            "reportPrivateUsage": report_private_usage,
            "extraPaths": [*extra_paths],
        }

    def _path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        return self._tool_config.tools.pyright.path_rules

    def _report_private_usage_for_env(self, env_dir: str) -> str:
        rules = self._path_rules()
        if env_dir == rules.source_dir:
            return rules.source_report_private_usage
        if env_dir in set(rules.test_like_dirs):
            return rules.test_like_report_private_usage
        return rules.other_report_private_usage

    @staticmethod
    def _test_like_dirs_set(
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> set[str]:
        return set(rules.test_like_dirs)

    def _extra_paths_for_env(
        self,
        *,
        env_dir: str,
        source_path: str,
        project_root: str,
        test_like_dirs: set[str],
    ) -> t.StrSequence:
        if env_dir in test_like_dirs and source_path != project_root:
            return [project_root, source_path]
        if env_dir in test_like_dirs:
            return [project_root]
        return [source_path]

    def _fallback_envs(
        self,
        *,
        source_path: str,
        project_root: str,
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> Sequence[t.Infra.ContainerDict]:
        default_test_root = (
            rules.test_like_dirs[0]
            if rules.test_like_dirs
            else c.Infra.Directories.TESTS
        )
        test_like_extra = self._extra_paths_for_env(
            env_dir=default_test_root,
            source_path=source_path,
            project_root=project_root,
            test_like_dirs=self._test_like_dirs_set(rules),
        )
        return [
            self._env_entry(
                root=rules.source_dir,
                report_private_usage=self._report_private_usage_for_env(
                    rules.source_dir,
                ),
                extra_paths=[source_path],
            ),
            self._env_entry(
                root=default_test_root,
                report_private_usage=self._report_private_usage_for_env(
                    default_test_root,
                ),
                extra_paths=test_like_extra,
            ),
        ]

    def _project_source_path(
        self,
        project_dir: Path,
        *,
        prefix: str = "",
    ) -> str:
        rules = self._path_rules()
        src_dir = project_dir / rules.source_dir
        if src_dir.is_dir():
            if prefix:
                return f"{prefix}/{rules.source_dir}"
            return rules.source_dir
        return prefix or rules.project_root

    def _expected_envs(
        self,
        *,
        is_root: bool,
        workspace_root: Path | None,
        project_dir: Path | None = None,
    ) -> Sequence[t.Infra.ContainerDict]:
        if not is_root:
            return self._expected_envs_for_project(project_dir)
        if workspace_root is None:
            return self._expected_envs_for_project(project_dir)

        rules = self._path_rules()
        test_like_dirs = self._test_like_dirs_set(rules)
        expected_envs: MutableSequence[t.Infra.ContainerDict] = []
        root_source_path = self._project_source_path(workspace_root)
        for env_dir in rules.env_dirs:
            if not (workspace_root / env_dir).is_dir():
                continue
            report_private_usage = self._report_private_usage_for_env(env_dir)
            extra_paths = self._extra_paths_for_env(
                env_dir=env_dir,
                source_path=root_source_path,
                project_root=rules.project_root,
                test_like_dirs=test_like_dirs,
            )
            expected_envs.append(
                self._env_entry(
                    root=env_dir,
                    report_private_usage=report_private_usage,
                    extra_paths=extra_paths,
                ),
            )

        child_projects = sorted(
            child
            for child in workspace_root.iterdir()
            if child.is_dir() and (child / c.Infra.Files.PYPROJECT_FILENAME).exists()
        )
        for child_project in child_projects:
            relative_root = child_project.relative_to(workspace_root)
            relative_project_root = relative_root.as_posix()
            child_source_path = self._project_source_path(
                child_project,
                prefix=relative_project_root,
            )
            for env_dir in rules.env_dirs:
                if not (child_project / env_dir).is_dir():
                    continue
                report_private_usage = self._report_private_usage_for_env(env_dir)
                extra_paths = self._extra_paths_for_env(
                    env_dir=env_dir,
                    source_path=child_source_path,
                    project_root=relative_project_root,
                    test_like_dirs=test_like_dirs,
                )
                expected_envs.append(
                    self._env_entry(
                        root=(relative_root / env_dir).as_posix(),
                        report_private_usage=report_private_usage,
                        extra_paths=extra_paths,
                    ),
                )
        return expected_envs

    def _expected_envs_for_project(
        self,
        project_dir: Path | None,
    ) -> Sequence[t.Infra.ContainerDict]:
        """Build executionEnvironments from YAML-configured directories."""
        rules = self._path_rules()
        if project_dir is None:
            return self._fallback_envs(
                source_path=rules.source_dir,
                project_root=rules.project_root,
                rules=rules,
            )
        source_path = self._project_source_path(project_dir)
        test_like_dirs = self._test_like_dirs_set(rules)
        envs: MutableSequence[t.Infra.ContainerDict] = []
        for env_dir in rules.env_dirs:
            if not (project_dir / env_dir).is_dir():
                continue
            report_private_usage = self._report_private_usage_for_env(env_dir)
            envs.append(
                self._env_entry(
                    root=env_dir,
                    report_private_usage=report_private_usage,
                    extra_paths=self._extra_paths_for_env(
                        env_dir=env_dir,
                        source_path=source_path,
                        project_root=rules.project_root,
                        test_like_dirs=test_like_dirs,
                    ),
                ),
            )
        if not envs:
            return self._fallback_envs(
                source_path=source_path,
                project_root=rules.project_root,
                rules=rules,
            )
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
        existing: MutableSequence[str] = []
        for relative_path in configured_paths:
            if (base_dir / relative_path).is_dir():
                existing.append(relative_path)
        return existing

    def _expected_ignores(
        self,
        *,
        is_root: bool,
        workspace_root: Path | None,
        project_dir: Path | None,
    ) -> t.StrSequence:
        """Ignore typings diagnostics while still keeping typings available in extraPaths."""
        rules = self._path_rules()
        if is_root:
            root_dir = workspace_root or project_dir
            return sorted(self._existing_paths(root_dir, rules.root_typings_paths))
        return sorted(self._existing_paths(project_dir, rules.project_typings_paths))

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
        current_excludes = u.Infra.as_string_list(
            u.Infra.get(pyright, c.Infra.EXCLUDE),
        )
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
        current_ignores = u.Infra.as_string_list(
            u.Infra.get(pyright, c.Infra.IGNORE),
        )
        if expected_ignores:
            if current_ignores != expected_ignores:
                pyright[c.Infra.IGNORE] = u.Infra.array(expected_ignores)
                changes.append(
                    "tool.pyright.ignore synchronized for typings diagnostics",
                )
        elif c.Infra.IGNORE in pyright:
            del pyright[c.Infra.IGNORE]
            changes.append("tool.pyright.ignore removed (no discovered ignores)")
        if "stubPath" in pyright:
            del pyright["stubPath"]
            changes.append("tool.pyright.stubPath removed (managed by extraPaths)")
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
        merged_settings: MutableMapping[str, str] = {
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
