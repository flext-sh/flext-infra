"""Pyright execution environment computation helpers."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t


class FlextInfraEnsurePyrightEnvs:
    """Helpers for computing pyright executionEnvironments entries.

    Methods that depend on the main class (_path_rules, _report_private_usage_for_env,
    _suppressions_for_env) are resolved via MRO when the main class inherits this mixin.
    """

    def _path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        raise NotImplementedError

    def _report_private_usage_for_env(self, env_dir: str) -> str:
        raise NotImplementedError

    def _suppressions_for_env(self, env_dir: str) -> t.StrMapping:
        raise NotImplementedError

    @staticmethod
    def _env_entry(
        *,
        root: str,
        report_private_usage: str,
        extra_paths: t.StrSequence,
        suppressions: t.StrMapping | None = None,
    ) -> t.Infra.ContainerDict:
        entry: t.Infra.MutableInfraMapping = {
            "root": root,
            "reportPrivateUsage": report_private_usage,
            "extraPaths": [*extra_paths],
        }
        if suppressions:
            for key in sorted(suppressions):
                entry[key] = suppressions[key]
        return entry

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
                suppressions=self._suppressions_for_env(rules.source_dir),
            ),
            self._env_entry(
                root=default_test_root,
                report_private_usage=self._report_private_usage_for_env(
                    default_test_root,
                ),
                extra_paths=test_like_extra,
                suppressions=self._suppressions_for_env(default_test_root),
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
                    suppressions=self._suppressions_for_env(env_dir),
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
                        suppressions=self._suppressions_for_env(env_dir),
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
                    suppressions=self._suppressions_for_env(env_dir),
                ),
            )
        if not envs:
            return self._fallback_envs(
                source_path=source_path,
                project_root=rules.project_root,
                rules=rules,
            )
        return envs


__all__ = ["FlextInfraEnsurePyrightEnvs"]
