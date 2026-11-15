"""Phase: Ensure standard Pyright configuration for strict type checking.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p
    from flext_infra.deps import FlextInfraExtraPathsManager


class FlextInfraEnsurePyrightConfigPhase:
    """Ensure standard Pyright configuration for strict type checking."""

    def __init__(
        self,
        tool_config: p.Infra.ToolConfigDocument,
        *,
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Initialize the phase with the canonical tool configuration."""
        self._tool_config = tool_config
        self._codegen = codegen

    def _report_private_usage_for_env(
        self,
        env_dir: str,
        *,
        rules: p.Infra.PyrightConfigPathRulesConfig | None = None,
    ) -> str:
        """Apply the configured privacy policy for each declared root category.

        Returns:
            The resulting ``str``.

        """
        effective_rules = rules or self._tool_config.tools.pyright.path_rules
        if env_dir == effective_rules.source_dir:
            source_report: str = effective_rules.source_report_private_usage
            return source_report
        if env_dir in effective_rules.test_like_dirs:
            test_report: str = effective_rules.test_like_report_private_usage
            return test_report
        other_report: str = effective_rules.other_report_private_usage
        return other_report

    def _env_entry(
        self,
        *,
        env_dir: str,
        root: str,
        extra_paths: Sequence[str],
        rules: p.Infra.PyrightConfigPathRulesConfig,
    ) -> p.Infra.PyrightConfigExecutionEnvironment:
        """Env entry.

        Returns:
            The resulting ``m.Infra.PyrightConfig.ExecutionEnvironment``.

        """
        return m.Infra.PyrightConfig.ExecutionEnvironment(
            root=root,
            report_private_usage=self._report_private_usage_for_env(
                env_dir,
                rules=rules,
            ),
            extra_paths=[*extra_paths],
        )

    @staticmethod
    def _extra_paths_for_env(
        *,
        env_dir: str,
        source_path: str,
        project_root: str,
        source_dir: str,
        member_src_paths: Sequence[str] = (),
    ) -> Sequence[str]:
        """Resolve owned source packages before installed distributions.

        Returns:
            The resulting ``Sequence[str]``.

        """
        if env_dir == source_dir:
            paths = list(dict.fromkeys((source_path, project_root)))
        elif source_path != project_root:
            paths = [project_root, source_path]
        else:
            paths = [project_root]
        return [*paths, *member_src_paths]

    def _envs_for_dirs(
        self,
        *,
        env_dirs: Sequence[str],
        source_path: str,
        project_root: str,
        rules: p.Infra.PyrightConfigPathRulesConfig,
    ) -> Sequence[p.Infra.PyrightConfigExecutionEnvironment]:
        """Envs for dirs.

        Returns:
            The resulting ``Sequence[p.Infra.PyrightConfigExecutionEnvironment]``.

        """
        environments = [
            self._env_entry(
                env_dir=env_dir,
                root=env_dir,
                extra_paths=self._extra_paths_for_env(
                    env_dir=env_dir,
                    source_path=source_path,
                    project_root=project_root,
                    source_dir=rules.source_dir,
                ),
                rules=rules,
            )
            for env_dir in env_dirs
            if env_dir not in rules.project_root_env_dirs
        ]
        if any(env_dir in rules.project_root_env_dirs for env_dir in env_dirs):
            environments.append(
                self._env_entry(
                    env_dir=rules.project_root,
                    root=project_root,
                    extra_paths=self._extra_paths_for_env(
                        env_dir=rules.project_root,
                        source_path=source_path,
                        project_root=project_root,
                        source_dir=rules.source_dir,
                    ),
                    rules=rules,
                ),
            )
        return environments

    def _diagnostic_exception_envs(
        self,
        *,
        project_dir: Path | None,
        source_path: str,
    ) -> Sequence[p.Infra.PyrightConfigExecutionEnvironment]:
        """Render each authorized exception root before the broad environments.

        Pyright elects the first environment containing a file, so each root
        repeats the policy of its category and adds only its authorized levels.

        Returns:
            One environment per exception that changes a Pyright rule.

        """
        rules = self._tool_config.tools.pyright.path_rules
        environments: MutableSequence[p.Infra.PyrightConfigExecutionEnvironment] = []
        for root, levels in u.Infra.diagnostic_exception_levels(
            self._tool_config, c.Infra.PYRIGHT, project_dir
        ):
            parts = PurePosixPath(root).parts
            env_dir = parts[0] if len(parts) > 1 else rules.project_root
            diagnostic_levels = dict(levels)
            report_private_usage = diagnostic_levels.pop(
                c.Infra.REPORT_PRIVATE_USAGE,
                self._report_private_usage_for_env(env_dir, rules=rules),
            )
            environments.append(
                m.Infra.PyrightConfig.ExecutionEnvironment(
                    root=root,
                    report_private_usage=report_private_usage,
                    extra_paths=self._extra_paths_for_env(
                        env_dir=env_dir,
                        source_path=source_path,
                        project_root=rules.project_root,
                        source_dir=rules.source_dir,
                    ),
                    diagnostic_levels=diagnostic_levels,
                ),
            )
        return tuple(environments)

    def _project_source_path(self, *, prefix: str = "") -> str:
        """Project source path.

        Returns:
            The resulting ``str``.

        """
        rules = self._tool_config.tools.pyright.path_rules
        return f"{prefix}/{rules.source_dir}" if prefix else rules.source_dir

    @staticmethod
    def _workspace_member_roots(
        repository_root: Path,
    ) -> Sequence[tuple[str, Sequence[str]]]:
        """Discover each declared member's owned Python roots independently.

        Returns:
            Member-relative paths paired with their owned Python targets.

        """
        return tuple(
            (
                member,
                u.Infra.analyzer_python_roots(
                    repository_root / member,
                    (),
                    workspace_excluded_top_dirs=(
                        FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                            repository_root / member
                        ).unwrap()
                    ),
                ),
            )
            for member in u.Infra.workspace_project_paths(repository_root)
        )

    def _workspace_member_envs(
        self, repository_root: Path
    ) -> Sequence[p.Infra.PyrightConfigExecutionEnvironment]:
        """Share one analyzer while keeping member package resolution local.

        Returns:
            Specific member environments followed by each member's root.

        """
        rules = self._tool_config.tools.pyright.path_rules
        environments: list[p.Infra.PyrightConfigExecutionEnvironment] = []
        for member, roots in self._workspace_member_roots(repository_root):
            source = self._project_source_path(prefix=member)
            environments.extend(
                self._env_entry(
                    env_dir=env_dir,
                    root=f"{member}/{env_dir}",
                    extra_paths=self._extra_paths_for_env(
                        env_dir=env_dir,
                        source_path=source,
                        project_root=member,
                        source_dir=rules.source_dir,
                    ),
                    rules=rules,
                )
                for env_dir in roots
                if (repository_root / member / env_dir).is_dir()
                and env_dir not in rules.project_root_env_dirs
            )
            # Top-level modules such as conftest.py still belong to this member.
            environments.append(
                self._env_entry(
                    env_dir=rules.project_root,
                    root=member,
                    extra_paths=(member, source),
                    rules=rules,
                )
            )
        return tuple(environments)

    def _expected_envs(
        self,
        *,
        is_root: bool,
        repository_root: Path | None,
        project_dir: Path | None,
        project_roots: Sequence[str],
    ) -> Sequence[p.Infra.PyrightConfigExecutionEnvironment]:
        """Return the expected execution environments.

        Returns:
            The expected execution environments.

        """
        if not is_root or repository_root is None:
            rules = self._tool_config.tools.pyright.path_rules
            return (
                *self._diagnostic_exception_envs(
                    project_dir=project_dir,
                    source_path=self._project_source_path(),
                ),
                *self._envs_for_dirs(
                    env_dirs=project_roots,
                    source_path=self._project_source_path(),
                    project_root=rules.project_root,
                    rules=rules,
                ),
            )
        rules = self._tool_config.tools.pyright.path_rules
        expected_envs = list(self._workspace_member_envs(repository_root))
        root_source_path = self._project_source_path()
        member_src_paths = tuple(
            f"{member}/src"
            for member in u.Infra.workspace_project_paths(repository_root)
        )
        # Specific roots precede the broad source environment.
        expected_envs.extend(
            self._diagnostic_exception_envs(
                project_dir=repository_root,
                source_path=root_source_path,
            ),
        )
        for env_dir in project_roots:
            if env_dir in rules.project_root_env_dirs:
                continue
            if (repository_root / env_dir / c.PYPROJECT_FILENAME).is_file():
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
                ),
            )
        if any(env_dir in rules.project_root_env_dirs for env_dir in project_roots):
            expected_envs.append(
                self._env_entry(
                    env_dir=rules.project_root,
                    root=rules.project_root,
                    extra_paths=(
                        rules.project_root,
                        root_source_path,
                        *member_src_paths,
                    ),
                    rules=rules,
                ),
            )
        return expected_envs

    def environment_payloads_for_dirs(
        self,
        env_dirs: Sequence[str],
    ) -> Sequence[t.JsonDict]:
        """Render configured environments for Python roots declared before writes.

        Returns:
            The resulting ``Sequence[t.JsonDict]``.

        """
        rules = self._tool_config.tools.pyright.path_rules
        environments = self._envs_for_dirs(
            env_dirs=self._declared_environment_dirs(env_dirs),
            source_path=self._project_source_path(),
            project_root=rules.project_root,
            rules=rules,
        )
        return tuple(self._environment_payload(item) for item in environments)

    def _declared_environment_dirs(self, env_dirs: Sequence[str]) -> Sequence[str]:
        """Apply canonical Python discovery exclusions to pre-write declarations.

        Returns:
            The resulting ``Sequence[str]``.

        """
        # Declared and on-disk roots must
        # select the same first-class analyzer environments in the first pass.
        return tuple(
            env_dir
            for env_dir in env_dirs
            if env_dir not in self._codegen.analysis_excluded_dirs
        )

    @staticmethod
    def _environment_payload(
        environment: p.Infra.PyrightConfigExecutionEnvironment,
    ) -> t.JsonDict:
        """Render one execution environment.

        Returns:
            The resulting ``t.JsonDict``.

        """
        payload: t.JsonDict = environment.model_dump(mode="json", by_alias=True)
        payload.update(environment.diagnostic_levels)
        return payload

    def _expected_excludes(
        self,
        project_root: Path | None,
        analysis_exclusions: Sequence[str] | None,
    ) -> Sequence[str]:
        """Return the complete config-owned Pyright exclude list.

        Returns:
            The complete config-owned Pyright exclude list.

        """
        rules = self._tool_config.tools.pyright.path_rules
        workspace_excludes: Sequence[str] = ()
        if analysis_exclusions is None and project_root is not None:
            workspace_excludes = tuple(
                path.as_posix()
                for path in FlextInfraWorkspaceDetector.analysis_exclusion_paths(
                    project_root,
                ).unwrap()
            )
        provided_exclusions = () if analysis_exclusions is None else analysis_exclusions
        return sorted({
            *rules.default_excludes,
            *self._codegen.analyzer_exclude_globs,
            *workspace_excludes,
            *provided_exclusions,
        })

    def _expected_ignores(self) -> Sequence[str]:
        """Ignore the configured diagnostic globs, each once.

        Returns:
            The configured ignore globs in declaration order.

        """
        return list(
            dict.fromkeys(
                self._tool_config.tools.pyright.path_rules.ignored_diagnostic_globs
            )
        )

    def _expected_project_roots(
        self,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None,
    ) -> Sequence[str]:
        """Resolve declared directories and discovered Python include targets.

        Returns:
            The resulting ``Sequence[str]``.

        """
        generated_roots = (
            paths_manager.generated_python_roots if paths_manager is not None else ()
        )
        declared = self._declared_environment_dirs(
            tuple(dict.fromkeys((*context.declared_python_dirs, *generated_roots))),
        )
        repository_root = context.repository_root
        if (
            context.is_root
            and repository_root is not None
            and (repository_root / c.Infra.GITMODULES).is_file()
        ):
            return u.Infra.analyzer_python_roots(
                repository_root,
                generated_roots,
                workspace_excluded_top_dirs=(
                    paths_manager.analysis_excluded_top_dirs
                    if paths_manager is not None
                    else FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                        repository_root,
                    ).unwrap()
                ),
            )
        if context.project_dir is not None:
            return u.Infra.analyzer_python_roots(
                context.project_dir,
                declared,
                workspace_excluded_top_dirs=(
                    paths_manager.analysis_excluded_top_dirs
                    if paths_manager is not None
                    else FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                        context.project_dir,
                    ).unwrap()
                ),
            )
        if declared or context.declared_python_dirs_are_complete:
            return declared
        return self._tool_config.tools.pyright.path_rules.env_dirs

    def _phase(
        self,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None,
        analysis_exclusions: Sequence[str] | None,
    ) -> p.Infra.PhaseConfig:
        """Build the managed pyright phase for one project context.

        Returns:
            The resulting ``m.Infra.DepsToml.PhaseConfig``.

        """
        is_root = context.is_root
        repository_root, project_dir = context.repository_root, context.project_dir
        project_root = repository_root if is_root else project_dir
        expected_excludes = self._expected_excludes(project_root, analysis_exclusions)
        expected_ignores = self._expected_ignores()
        expected_roots = self._expected_project_roots(
            context=context,
            paths_manager=paths_manager,
        )
        # Include every Python target owned by the selected project manifest.
        expected_includes = list(expected_roots)
        if (
            is_root
            and repository_root is not None
            and (repository_root / c.Infra.GITMODULES).is_file()
        ):
            expected_includes.extend(
                f"{member}/{root}"
                for member, roots in self._workspace_member_roots(repository_root)
                for root in roots
            )
        expected_envs = self._expected_envs(
            is_root=is_root,
            repository_root=repository_root,
            project_dir=project_dir,
            project_roots=tuple(
                root
                for root in expected_roots
                if project_root is None or not (project_root / root).is_file()
            ),
        )
        toml = m.Infra.DepsToml
        operations: MutableSequence[
            m.Infra.DepsToml.SetOp | m.Infra.DepsToml.ListOp | m.Infra.DepsToml.RemoveOp
        ] = [
            toml.ListOp(key=c.Infra.EXCLUDE, values=expected_excludes)
            if expected_excludes
            else toml.RemoveOp(key=c.Infra.EXCLUDE),
            toml.ListOp(key=c.Infra.IGNORE, values=expected_ignores)
            if expected_ignores
            else toml.RemoveOp(key=c.Infra.IGNORE),
            toml.ListOp(key="include", values=expected_includes)
            if expected_includes
            else toml.RemoveOp(key="include"),
        ]
        if project_root is not None and paths_manager is not None:
            operations.append(
                toml.ListOp(
                    key="extraPaths",
                    values=paths_manager.pyright_extra_paths(),
                    sort=False,
                ),
            )
        operations.append(toml.RemoveOp(key="stubPath"))
        # ADR-003 Decision 5: the existing topology owner elects the runtime.
        # A scaffold without an on-disk project owns its future environment.
        environment_parent = (
            u.Infra
            .runtime_owner_root(project_root)
            .unwrap()
            .relative_to(project_root.resolve(), walk_up=True)
            .as_posix()
            if project_root is not None
            else "."
        )
        operations.append(toml.SetOp(key="venv", value=c.Infra.ENVIRONMENT_DIRECTORY))
        operations.append(toml.SetOp(key="venvPath", value=environment_parent))
        operations.append(
            toml.SetOp(
                key="executionEnvironments",
                value=[
                    u.normalize_to_json_value(self._environment_payload(expected_env))
                    for expected_env in expected_envs
                ],
            ),
        )
        operations.append(
            toml.SetOp(
                key="pythonVersion", value=self._codegen.toolchain.python_version
            )
        )
        return toml.PhaseConfig(
            name="pyright",
            table_path=(c.Infra.PYRIGHT,),
            operations=tuple(operations),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None = None,
        analysis_exclusions: Sequence[str] | None = None,
    ) -> Sequence[str]:
        """Apply managed pyright settings directly to one normalized payload.

        Returns:
            The resulting ``Sequence[str]``.

        Raises:
            ValueError: When the pyright owner produces no native table.

        """
        native = u.Infra.native_tool_configuration(self._tool_config, c.Infra.PYRIGHT)
        # Operator-authorized global axioms render as level none in every
        # project; the declaration lives once, in tools.pyright.
        for rule in self._tool_config.tools.pyright.ruling_disabled_rules:
            native[rule] = "none"
        desired: t.MutableJsonMapping = {c.Infra.TOOL: {c.Infra.PYRIGHT: native}}
        u.Infra.apply_toml_phases(
            desired,
            self._phase(
                context=context,
                paths_manager=paths_manager,
                analysis_exclusions=analysis_exclusions,
            ),
        )
        table = u.Cli.toml_mapping_path(desired, (c.Infra.TOOL, c.Infra.PYRIGHT))
        if table is None:
            msg = "Pyright owner produced no native table"
            raise ValueError(msg)
        return u.Infra.apply_toml_phases(
            payload,
            m.Infra.DepsToml.PhaseConfig(
                name=c.Infra.PYRIGHT,
                table_path=(),
                operations=(
                    m.Infra.DepsToml.SetOp(
                        key=c.Infra.PYRIGHT,
                        value=u.normalize_to_json_value(table),
                    ),
                ),
            ),
        )

    def render_source(
        self,
        source: str,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None = None,
        analysis_exclusions: Sequence[str] | None = None,
    ) -> p.Result[str]:
        """Project only the analyzer table, preserving the rest of the document.

        The caller injects the analyzer inputs its full modernization owns.

        Returns:
            TOML with the same configuration emitted by full modernization.

        """
        parsed = u.Cli.toml_mapping_from_text_result(source)
        if parsed.failure:
            return r[str].from_failure(parsed)
        payload: t.MutableJsonMapping = dict(parsed.value)
        self.apply_payload(
            payload,
            context=context,
            paths_manager=paths_manager,
            analysis_exclusions=analysis_exclusions,
        )
        document = u.Cli.toml_parse_text(source)
        if document is None:
            return r[str].fail(
                "validated TOML could not be parsed for round-trip editing"
            )
        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        expected = u.Cli.toml_mapping_path(payload, (c.Infra.TOOL, c.Infra.PYRIGHT))
        if expected is None:
            return r[str].fail("Pyright projection produced no analyzer table")
        ordered = u.Cli.json_dumps(u.normalize_to_json_value(expected), sort_keys=True)
        if ordered.failure:
            return r[str].from_failure(ordered)
        # This table is generated in full. Replacing its value also normalizes
        # nested object keys while retaining semantic list order.
        tool[c.Infra.PYRIGHT] = u.json_mapping_adapter().validate_json(ordered.value)
        return r[str].ok(u.Cli.toml_dumps(document))


__all__: list[str] = ["FlextInfraEnsurePyrightConfigPhase"]
