"""Phase: Ensure standard Pyright configuration for strict type checking."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import FlextInfraToml, c, m, t, u

if TYPE_CHECKING:
    from flext_infra import FlextInfraExtraPathsManager

from .ensure_pyright_envs import FlextInfraEnsurePyrightEnvs


class FlextInfraEnsurePyrightConfigPhase(FlextInfraEnsurePyrightEnvs):
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    @override
    def _path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        return self._tool_config.tools.pyright.path_rules

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
            c.Infra.VENV_PATH: venv_path,
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

    def _expected_includes(
        self,
        *,
        is_root: bool,
        workspace_root: Path | None,
        project_dir: Path | None,
    ) -> t.StrSequence:
        """Return the concrete source/test roots that pyright should analyze."""
        rules = self._path_rules()
        if not is_root:
            if project_dir is None:
                return list(rules.env_dirs)
            return [
                env_dir
                for env_dir in rules.env_dirs
                if (project_dir / env_dir).is_dir()
            ]
        if workspace_root is None:
            return list(rules.env_dirs)
        includes: MutableSequence[str] = [
            env_dir for env_dir in rules.env_dirs if (workspace_root / env_dir).is_dir()
        ]
        discovered = u.Infra.discover_projects(workspace_root)
        if discovered.is_failure:
            return includes
        child_projects = sorted(
            (
                project.path
                for project in discovered.value
                if (
                    project.workspace_role
                    == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
                )
            ),
            key=lambda project_path: project_path.name,
        )
        for child_project in child_projects:
            relative_root = child_project.relative_to(workspace_root)
            for env_dir in rules.env_dirs:
                if (child_project / env_dir).is_dir():
                    includes.append((relative_root / env_dir).as_posix())
        return includes

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        workspace_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> t.StrSequence:
        project_root = workspace_root if is_root else project_dir
        expected_excludes = self._expected_excludes(project_root)
        expected_ignores = self._expected_ignores(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
        expected_includes = self._expected_includes(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
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
        expected_envs = self._expected_envs(
            is_root=is_root,
            workspace_root=workspace_root,
            project_dir=project_dir,
        )
        phase_builder = m.Infra.TomlPhaseConfig.Builder("pyright").table(
            c.Infra.PYRIGHT
        )
        if expected_excludes:
            phase_builder = phase_builder.list(c.Infra.EXCLUDE, expected_excludes)
        else:
            phase_builder = phase_builder.deprecated(c.Infra.EXCLUDE)
        if expected_ignores:
            phase_builder = phase_builder.list(c.Infra.IGNORE, expected_ignores)
        else:
            phase_builder = phase_builder.deprecated(c.Infra.IGNORE)
        if expected_includes:
            phase_builder = phase_builder.list("include", expected_includes)
        else:
            phase_builder = phase_builder.deprecated("include")
        if project_root is not None and paths_manager is not None:
            phase_builder = phase_builder.list(
                "extraPaths",
                paths_manager.pyright_extra_paths(
                    project_dir=project_root,
                    is_root=is_root,
                ),
            )
        if expected_stub_path is not None:
            existing = project_root / expected_stub_path if project_root else None
            if existing is not None and existing.is_dir():
                phase_builder = phase_builder.value("stubPath", expected_stub_path)
            else:
                phase_builder = phase_builder.deprecated("stubPath")
        else:
            phase_builder = phase_builder.deprecated("stubPath")
        for key, value in self._venv_settings(is_root=is_root).items():
            phase_builder = phase_builder.value(key, value)
        phase_builder = phase_builder.value(
            "executionEnvironments",
            [
                u.Cli.normalize_json_value(
                    expected_env.model_dump(mode="json", by_alias=True),
                )
                for expected_env in expected_envs
            ],
        )
        if is_root:
            for key, value in self._tool_config.tools.pyright.strict_settings.items():
                phase_builder = phase_builder.value(key, value)
            for key, value in self._tool_config.tools.pyright.extended_settings.items():
                phase_builder = phase_builder.value(key, value)
            return FlextInfraToml.apply_phases(doc, phase_builder.build())
        for key, value in self._tool_config.tools.pyright.strict_settings.items():
            phase_builder = phase_builder.value(key, value)
        merged_settings: t.MutableStrMapping = {
            **self._tool_config.tools.pyright.extended_settings,
        }
        override = self._override_for_kind(project_kind)
        if override is not None:
            merged_settings.update(override.pyright)
        for key, value in merged_settings.items():
            phase_builder = phase_builder.value(key, value)
        return FlextInfraToml.apply_phases(doc, phase_builder.build())


__all__ = ["FlextInfraEnsurePyrightConfigPhase"]
