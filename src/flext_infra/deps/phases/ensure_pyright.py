"""Phase: Ensure standard Pyright configuration for strict type checking."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager


class FlextInfraEnsurePyrightConfigPhase:
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Initialize the phase with the canonical tool configuration."""
        self._tool_config = tool_config

    def _report_private_usage_for_env(
        self,
        env_dir: str,
        *,
        rules: m.Infra.PyrightConfig.PathRulesConfig | None = None,
    ) -> str:
        """Only ``source_dir`` (src/) is strict; all auto-discovered dirs relax."""
        effective_rules = rules or self._tool_config.tools.pyright.path_rules
        if env_dir == effective_rules.source_dir:
            source_report: str = effective_rules.source_report_private_usage
            return source_report
        test_report: str = effective_rules.test_like_report_private_usage
        return test_report

    def _env_entry(
        self,
        *,
        env_dir: str,
        root: str,
        extra_paths: t.StrSequence,
        rules: m.Infra.PyrightConfig.PathRulesConfig,
    ) -> m.Infra.PyrightConfig.ExecutionEnvironment:
        """Env entry."""
        return m.Infra.PyrightConfig.ExecutionEnvironment(
            root=root,
            report_private_usage=self._report_private_usage_for_env(
                env_dir, rules=rules
            ),
            extra_paths=[*extra_paths],
        )

    def _extra_paths_for_env(
        self,
        *,
        env_dir: str,
        source_path: str,
        project_root: str,
        source_dir: str,
        member_src_paths: t.StrSequence = (),
    ) -> t.StrSequence:
        """``src/`` owns only its own path; every other discovered dir also imports from src + root."""
        if env_dir == source_dir:
            paths = [source_path]
        elif source_path != project_root:
            paths = [project_root, source_path]
        else:
            paths = [project_root]
        return [*paths, *member_src_paths]

    def _envs_for_dirs(
        self, env_dirs: t.StrSequence
    ) -> t.SequenceOf[m.Infra.PyrightConfig.ExecutionEnvironment]:
        """Only ``source_dir`` is strict and self-contained; other roots import src + root."""
        rules = self._tool_config.tools.pyright.path_rules
        shared_paths = (
            (rules.project_root, rules.source_dir)
            if rules.source_dir != rules.project_root
            else (rules.project_root,)
        )
        return tuple(
            m.Infra.PyrightConfig.ExecutionEnvironment(
                root=env_dir,
                report_private_usage=(
                    rules.source_report_private_usage
                    if env_dir == rules.source_dir
                    else rules.test_like_report_private_usage
                ),
                extra_paths=(
                    [rules.source_dir]
                    if env_dir == rules.source_dir
                    else [*shared_paths]
                ),
            )
            for env_dir in env_dirs
        )

    def _expected_envs(
        self,
        *,
        is_root: bool,
        repository_root: Path | None,
        project_dir: Path | None,
        project_roots: t.StrSequence,
    ) -> t.SequenceOf[m.Infra.PyrightConfig.ExecutionEnvironment]:
        """Return diagnostic overrides first, then one environment per owned root."""
        rules = self._tool_config.tools.pyright.path_rules
        expected_envs: t.MutableSequenceOf[
            m.Infra.PyrightConfig.ExecutionEnvironment
        ] = []
        root_source_path = self._project_source_path()
        member_src_paths = tuple(
            f"{member}/src"
            for member in u.Infra.workspace_project_paths(repository_root)
        )
        # Specific roots precede the broad source environment.
        expected_envs.extend(
            self._diagnostic_override_envs(
                project_dir=repository_root,
                root_prefix=None,
                source_path=root_source_path,
            )
        )
        for env_dir in project_roots:
            if (repository_root / env_dir / c.Infra.PYPROJECT_FILENAME).is_file():
                continue
            expected_envs.append(
                self._env_entry(
                    env_dir=env_dir,
                    root=env_dir,
                    extra_paths=self._extra_paths_for_env(
                        env_dir=env_dir,
                        source_path=root_source_path,
                        project_root=rules.project_root,
                        source_dir=rules.source_dir,
                        member_src_paths=member_src_paths,
                    ),
                    rules=rules,
                )
            )
        return expected_envs

    def environment_payloads_for_dirs(
        self, env_dirs: t.StrSequence
    ) -> t.SequenceOf[t.JsonDict]:
        """Render configured environments for Python roots declared before writes."""
        return tuple(
            self._environment_payload(item)
            for item in self._envs_for_dirs(self._declared_environment_dirs(env_dirs))
        )

    @staticmethod
    def _declared_environment_dirs(env_dirs: t.StrSequence) -> t.StrSequence:
        """Apply canonical Python discovery exclusions to pre-write declarations."""
        # Declared and on-disk roots must
        # select the same first-class analyzer environments in the first pass.
        return tuple(
            env_dir
            for env_dir in env_dirs
            if env_dir not in c.Infra.PYTHON_DISCOVERY_SKIP_DIRS
        )

    def _environment_payload(
        self, environment: m.Infra.PyrightConfig.ExecutionEnvironment
    ) -> t.JsonDict:
        """Render one environment with its closed, scope-specific diagnostics."""
        pyright = self._tool_config.tools.pyright
        env_dir = Path(environment.root).name
        payload: t.JsonDict = environment.model_dump(mode="json", by_alias=True)
        payload.update(pyright.lazy_import_suppressions)
        if env_dir == pyright.path_rules.source_dir:
            payload.update(pyright.source_env_suppressions)
        elif env_dir in pyright.path_rules.test_like_dirs:
            payload.update(pyright.test_like_env_suppressions)
        return payload

    def _expected_excludes(
        self, project_root: Path | None, analysis_exclusions: t.StrSequence | None
    ) -> t.StrSequence:
        """Return the complete config-owned Pyright exclude list."""
        excludes = analysis_exclusions or ()
        if analysis_exclusions is None and project_root is not None:
            excluded = FlextInfraWorkspaceDetector.analysis_exclusion_paths(
                project_root
            )
            if excluded.failure:
                raise ValueError(
                    excluded.error or "workspace analysis scope is unavailable"
                )
            excludes = tuple(path.as_posix() for path in excluded.value)
        return sorted({
            *self._tool_config.tools.pyright.path_rules.default_excludes,
            *excludes,
        })

    def _expected_project_roots(
        self,
        *,
        is_root: bool,
        repository_root: Path | None,
        project_dir: Path | None,
        declared_python_dirs: t.StrSequence,
        declared_python_dirs_are_complete: bool,
        generated_roots: t.StrSequence = (),
        workspace_excluded_top_dirs: frozenset[str] | None = None,
    ) -> t.StrSequence:
        """Resolve the one analyzer-root set consumed by includes and environments."""
        generated_roots = (
            paths_manager.generated_python_roots if paths_manager is not None else ()
        )
        excluded_top_dirs = (
            paths_manager.analysis_excluded_top_dirs
            if paths_manager is not None
            else None
        )
        declared = self._declared_environment_dirs(
            tuple(dict.fromkeys((*declared_python_dirs, *generated_roots)))
        )
        if (
            is_root
            and repository_root is not None
            and (repository_root / c.Infra.GITMODULES).is_file()
        ):
            return u.Infra.analyzer_python_roots(
                repository_root,
                generated_roots,
                workspace_excluded_top_dirs=excluded_top_dirs,
            )
        if declared_python_dirs_are_complete:
            return declared
        if project_dir is not None:
            return u.Infra.analyzer_python_roots(
                project_dir, declared, workspace_excluded_top_dirs=excluded_top_dirs
            )
        return declared or self._tool_config.tools.pyright.path_rules.env_dirs

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        is_root: bool,
        repository_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
        paths_manager: FlextInfraExtraPathsManager | None = None,
        declared_python_dirs: t.StrSequence = (),
        declared_python_dirs_are_complete: bool = False,
        analysis_exclusions: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Apply managed pyright settings directly to one normalized payload."""
        pyright = self._tool_config.tools.pyright
        rules = pyright.path_rules
        project_root = repository_root if is_root else project_dir
        typings_paths = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_base = (repository_root or project_dir) if is_root else project_dir
        expected_ignores = list(
            dict.fromkeys((
                *(
                    path
                    for path in typings_paths
                    if typings_base is not None and (typings_base / path).is_dir()
                ),
                *rules.ignored_diagnostic_globs,
            ))
        )
        expected_roots = self._expected_project_roots(
            is_root=is_root,
            repository_root=repository_root,
            project_dir=project_dir,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=declared_python_dirs_are_complete,
            paths_manager=paths_manager,
        )
        (
            rules.root_typings_paths[0]
            if is_root and rules.root_typings_paths
            else next(iter(rules.project_typings_paths), None)
        )
        builder = m.Infra.Deps.Toml.PhaseConfig.Builder("pyright").table(
            c.Infra.PYRIGHT
        )
        for key, values in (
            (
                c.Infra.EXCLUDE,
                self._expected_excludes(project_root, analysis_exclusions),
            ),
            (c.Infra.IGNORE, expected_ignores),
            ("include", expected_roots),
        ):
            builder = builder.list(key, values) if values else builder.deprecated(key)
        if project_root is not None and paths_manager is not None:
            builder = builder.list(
                "extraPaths",
                paths_manager.pyright_extra_paths(
                    project_dir=project_root, is_root=is_root
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
        phase_builder = phase_builder.deprecated("venv").deprecated(c.Infra.VENV_PATH)
        phase_builder = phase_builder.value(
            "executionEnvironments",
            [
                u.normalize_to_json_value(self._environment_payload(expected_env))
                for expected_env in expected_envs
            ],
        )
        if is_root:
            for key, value in self._tool_config.tools.pyright.strict_settings.items():
                phase_builder = phase_builder.value(key, value)
            for key, value in self._tool_config.tools.pyright.extended_settings.items():
                phase_builder = phase_builder.value(key, value)
            return phase_builder.build()
        for key, value in self._tool_config.tools.pyright.strict_settings.items():
            phase_builder = phase_builder.value(key, value)
        merged_settings: t.MutableStrMapping = {
            **self._tool_config.tools.pyright.extended_settings
        }
        override = self._override_for_kind(project_kind)
        if override is not None:
            merged_settings.update(override.pyright)
        for key, value in merged_settings.items():
            phase_builder = phase_builder.value(key, value)
        return phase_builder.build()

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        repository_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
        paths_manager: FlextInfraExtraPathsManager | None = None,
        declared_python_dirs: t.StrSequence = (),
        declared_python_dirs_are_complete: bool = False,
        analysis_exclusions: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Apply the managed pyright configuration for one TOML document."""
        return u.Infra.apply_toml_phases(
            doc,
            self._phase(
                is_root=is_root,
                repository_root=repository_root,
                project_dir=project_dir,
                project_kind=project_kind,
                paths_manager=paths_manager,
                declared_python_dirs=declared_python_dirs,
                declared_python_dirs_are_complete=declared_python_dirs_are_complete,
                analysis_exclusions=analysis_exclusions,
            ),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        is_root: bool,
        repository_root: Path | None = None,
        project_dir: Path | None = None,
        project_kind: str = "core",
        paths_manager: FlextInfraExtraPathsManager | None = None,
        declared_python_dirs: t.StrSequence = (),
        declared_python_dirs_are_complete: bool = False,
        analysis_exclusions: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Apply managed pyright settings directly to one normalized payload."""
        return u.Infra.apply_toml_phases(
            payload,
            self._phase(
                is_root=is_root,
                repository_root=repository_root,
                project_dir=project_dir,
                project_kind=project_kind,
                paths_manager=paths_manager,
                declared_python_dirs=declared_python_dirs,
                declared_python_dirs_are_complete=declared_python_dirs_are_complete,
                analysis_exclusions=analysis_exclusions,
            ),
        )


__all__: list[str] = ["FlextInfraEnsurePyrightConfigPhase"]
