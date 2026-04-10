"""Pyright execution environment computation helpers."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraEnsurePyrightEnvs:
    """Helpers for computing pyright executionEnvironments entries.

    Methods that depend on the main class (_path_rules, _report_private_usage_for_env)
    are resolved via MRO when the main class inherits this mixin.
    """

    def _path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        raise NotImplementedError

    def _report_private_usage_for_env(
        self,
        env_dir: str,
        *,
        rules: m.Infra.PyrightConfig.PathRulesConfig | None = None,
    ) -> str:
        effective_rules = rules or self._path_rules()
        if env_dir == effective_rules.source_dir:
            return effective_rules.source_report_private_usage
        if env_dir in self._test_like_dirs_set(effective_rules):
            return effective_rules.test_like_report_private_usage
        return effective_rules.other_report_private_usage

    def _env_entry(
        self,
        *,
        env_dir: str,
        root: str,
        extra_paths: t.StrSequence,
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> m.Infra.PyrightConfig.ExecutionEnvironment:
        return m.Infra.PyrightConfig.ExecutionEnvironment(
            root=root,
            report_private_usage=self._report_private_usage_for_env(
                env_dir,
                rules=rules,
            ),
            extra_paths=[*extra_paths],
        )

    @staticmethod
    def _test_like_dirs_set(
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> t.Infra.StrSet:
        return set(rules.test_like_dirs)

    def _extra_paths_for_env(
        self,
        *,
        env_dir: str,
        source_path: str,
        project_root: str,
        test_like_dirs: t.Infra.StrSet,
    ) -> t.StrSequence:
        if env_dir in test_like_dirs and source_path != project_root:
            return [project_root, source_path]
        if env_dir in test_like_dirs:
            return [project_root]
        return [source_path]

    def _envs_for_dirs(
        self,
        *,
        env_dirs: t.StrSequence,
        source_path: str,
        project_root: str,
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> Sequence[m.Infra.PyrightConfig.ExecutionEnvironment]:
        test_like_dirs = self._test_like_dirs_set(rules)
        return [
            self._env_entry(
                env_dir=env_dir,
                root=env_dir,
                extra_paths=self._extra_paths_for_env(
                    env_dir=env_dir,
                    source_path=source_path,
                    project_root=project_root,
                    test_like_dirs=test_like_dirs,
                ),
                rules=rules,
            )
            for env_dir in env_dirs
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
    ) -> Sequence[m.Infra.PyrightConfig.ExecutionEnvironment]:
        if not is_root:
            return self._expected_envs_for_project(project_dir)
        if workspace_root is None:
            return self._expected_envs_for_project(project_dir)

        rules = self._path_rules()
        test_like_dirs = self._test_like_dirs_set(rules)
        expected_envs: MutableSequence[m.Infra.PyrightConfig.ExecutionEnvironment] = []
        root_source_path = self._project_source_path(workspace_root)
        for env_dir in rules.env_dirs:
            if not (workspace_root / env_dir).is_dir():
                continue
            extra_paths = self._extra_paths_for_env(
                env_dir=env_dir,
                source_path=root_source_path,
                project_root=rules.project_root,
                test_like_dirs=test_like_dirs,
            )
            expected_envs.append(
                self._env_entry(
                    env_dir=env_dir,
                    root=env_dir,
                    extra_paths=extra_paths,
                    rules=rules,
                ),
            )

        discovered = u.Infra.discover_projects(workspace_root)
        child_projects = (
            sorted(
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
            if discovered.is_success
            else []
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
                extra_paths = self._extra_paths_for_env(
                    env_dir=env_dir,
                    source_path=child_source_path,
                    project_root=relative_project_root,
                    test_like_dirs=test_like_dirs,
                )
                expected_envs.append(
                    self._env_entry(
                        env_dir=env_dir,
                        root=(relative_root / env_dir).as_posix(),
                        extra_paths=extra_paths,
                        rules=rules,
                    ),
                )
        return expected_envs

    def _expected_envs_for_project(
        self,
        project_dir: Path | None,
    ) -> Sequence[m.Infra.PyrightConfig.ExecutionEnvironment]:
        """Build executionEnvironments from YAML-configured directories."""
        rules = self._path_rules()
        if project_dir is None:
            return self._envs_for_dirs(
                env_dirs=rules.env_dirs,
                source_path=rules.source_dir,
                project_root=rules.project_root,
                rules=rules,
            )
        source_path = self._project_source_path(project_dir)
        existing_env_dirs = [
            env_dir for env_dir in rules.env_dirs if (project_dir / env_dir).is_dir()
        ]
        return self._envs_for_dirs(
            env_dirs=existing_env_dirs,
            source_path=source_path,
            project_root=rules.project_root,
            rules=rules,
        )


__all__ = ["FlextInfraEnsurePyrightEnvs"]
