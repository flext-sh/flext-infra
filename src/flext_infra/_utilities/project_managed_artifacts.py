"""Load and compose project-owned managed-artifact configuration."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from flext_core import r
from flext_infra import c, config, m, p, t, u


class FlextInfraUtilitiesProjectManagedArtifacts:
    """Single owner for ``ManagedArtifacts`` across ``config/*.yaml`` files."""

    @classmethod
    def snapshot_config_sources(
        cls, project_dir: Path
    ) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
        """Capture one stable, physical, direct ``config/*.yaml`` file set.

        A project root that does not exist yet declares no managed artifacts, so
        it snapshots empty — the same answer ``_config_directory_identity``
        already gives for an absent ``config/`` directory. ``codegen conform``
        plans a brand-new project before materializing its tree, and that plan
        must not fail on the absence it is about to fix. Every other inspection
        failure (permission, non-directory, reparse point) still fails loud.
        """
        if not project_dir.exists():
            return r[tuple[m.Cli.AtomicFileState, ...]].ok(())
        project_identity = cls._required_directory_identity(
            project_dir, purpose="project root"
        )
        if project_identity.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(project_identity)
        config_dir = project_dir / c.CONFIG_DIR_NAME
        identity = cls._config_directory_identity(config_dir)
        if identity.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(identity)
        if not identity.value:
            return r[tuple[m.Cli.AtomicFileState, ...]].ok(())
        paths = cls._config_yaml_paths(config_dir, identity.value)
        if paths.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(paths)
        sources: list[m.Cli.AtomicFileState] = []
        for path in paths.value:
            source = u.Cli.atomic_read_binary_file_state(path, required=True)
            if source.failure:
                return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(source)
            sources.append(source.value)
        stable_paths = cls._config_yaml_paths(config_dir, identity.value)
        if stable_paths.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(stable_paths)
        if stable_paths.value != paths.value:
            return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                f"project config source topology changed: {config_dir}"
            )
        stable_project = cls._required_directory_identity(
            project_dir, purpose="project root"
        )
        if stable_project.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(stable_project)
        if stable_project.value != project_identity.value:
            return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                f"project root changed during config snapshot: {project_dir}"
            )
        return r[tuple[m.Cli.AtomicFileState, ...]].ok(tuple(sources))

    @classmethod
    def _required_directory_identity(
        cls, path: Path, *, purpose: str
    ) -> p.Result[tuple[int, ...]]:
        try:
            state = path.lstat()
        except OSError as exc:
            return r[tuple[int, ...]].fail_op(f"inspect {purpose}", exc)
        attributes = getattr(state, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not stat.S_ISDIR(state.st_mode) or attributes & reparse:
            return r[tuple[int, ...]].fail(
                f"{purpose} is not a physical directory: {path}"
            )
        return r[tuple[int, ...]].ok(cls._directory_state_key(state))

    @classmethod
    def _config_directory_identity(cls, config_dir: Path) -> p.Result[tuple[int, ...]]:
        try:
            state = config_dir.lstat()
        except FileNotFoundError:
            return r[tuple[int, ...]].ok(())
        except OSError as exc:
            return r[tuple[int, ...]].fail_op("inspect project config directory", exc)
        attributes = getattr(state, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not stat.S_ISDIR(state.st_mode) or attributes & reparse:
            return r[tuple[int, ...]].fail(
                f"project config path is not a physical directory: {config_dir}"
            )
        return r[tuple[int, ...]].ok(cls._directory_state_key(state))

    @staticmethod
    def empty_snapshot() -> m.Infra.ProjectManagedArtifactsSnapshot:
        """Return the explicit managed-artifact state for a future scaffold."""
        return m.Infra.ProjectManagedArtifactsSnapshot(
            sources=(),
            resolution=m.Infra.ProjectManagedArtifactsResolution(
                artifacts=m.Infra.ProjectManagedArtifactsConfig(), mise_tool_sources={}
            ),
        )

    @classmethod
    def _config_yaml_paths(
        cls, config_dir: Path, expected_identity: tuple[int, ...]
    ) -> p.Result[tuple[Path, ...]]:
        try:
            paths = tuple(
                sorted(path for path in config_dir.iterdir() if path.suffix == ".yaml")
            )
        except OSError as exc:
            return r[tuple[Path, ...]].fail_op("enumerate project config sources", exc)
        current = cls._config_directory_identity(config_dir)
        if current.failure:
            return r[tuple[Path, ...]].from_failure(current)
        if current.value != expected_identity:
            return r[tuple[Path, ...]].fail(
                f"project config directory changed during snapshot: {config_dir}"
            )
        return r[tuple[Path, ...]].ok(paths)

    @staticmethod
    def _directory_state_key(state: os.stat_result) -> tuple[int, ...]:
        return (
            state.st_dev,
            state.st_ino,
            state.st_mode,
            state.st_uid,
            state.st_gid,
            state.st_size,
            state.st_mtime_ns,
            state.st_ctime_ns,
        )

    @staticmethod
    def validate_mise_tool_selectors(
        selectors: t.StrSequence, *, source: Path
    ) -> p.Result[bool]:
        """Reject selectors belonging to suspended auxiliary capabilities."""
        patterns = config.Infra.codegen.toolchain.suspended_mise_selector_patterns
        for selector in selectors:
            for pattern in patterns:
                if not fnmatchcase(selector, pattern):
                    continue
                return r[bool].fail(
                    "project Mise selector belongs to a suspended toolchain: "
                    f"{selector!r} in {source}"
                )
        return r[bool].ok(True)

    @staticmethod
    def load(project_dir: Path) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Load the neutral tooling owner without probing auxiliary configs."""
        config_dir = project_dir / c.CONFIG_DIR_NAME
        empty = m.Infra.ProjectManagedArtifactsResolution(
            artifacts=m.Infra.ProjectManagedArtifactsConfig(), mise_tool_sources={}
        )
        tooling_path = config_dir / "tooling.yaml"
        if not tooling_path.is_file():
            return r[m.Infra.ProjectManagedArtifactsResolution].ok(empty)
        loaded = u.Cli.config_load(tooling_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                loaded.error or f"project tooling config load failed: {tooling_path}"
            )
        ruff_ignores: dict[str, set[str]] = {}
        mise_tools: dict[str, str] = {}
        mise_sources: dict[str, Path] = {}
        managed = loaded.value.data.get("ManagedArtifacts")
        if managed:
            project_config = m.Infra.ProjectConfigDocument.model_validate({
                "ManagedArtifacts": managed
            })
            artifacts = project_config.ManagedArtifacts
            for pattern, rules in artifacts.Ruff.per_file_ignores.items():
                ruff_ignores.setdefault(pattern, set()).update(rules)
            source = tooling_path
            for selector, version in artifacts.Mise.tools.items():
                mise_tools[selector] = version
                mise_sources[selector] = source
        artifacts = m.Infra.ProjectManagedArtifactsConfig(
            Ruff=m.Infra.ProjectRuffConfig(
                per_file_ignores={
                    pattern: tuple(sorted(rules))
                    for pattern, rules in sorted(ruff_ignores.items())
                }
            ),
            Mise=m.Infra.ProjectMiseConfig(tools=dict(sorted(mise_tools.items()))),
        )
        return r[m.Infra.ProjectManagedArtifactsResolution].ok(
            m.Infra.ProjectManagedArtifactsResolution(
                artifacts=artifacts,
                mise_tool_sources=dict(sorted(mise_sources.items())),
            )
        )

    @classmethod
    def compose_mise_toml(cls, project_dir: Path, rendered: str) -> p.Result[str]:
        """Add local tools through TOML types and reject global collisions."""
        resolved = cls.load(project_dir)
        if resolved.failure:
            return r[str].fail(resolved.error or "project artifact load failed")
        local_tools = resolved.value.artifacts.Mise.tools
        if not local_tools:
            return r[str].ok(rendered)
        for selector in local_tools:
            selector_validation = cls.validate_mise_tool_selectors(
                (selector,), source=resolved.value.mise_tool_sources[selector]
            )
            if selector_validation.failure:
                return r[str].fail(
                    selector_validation.error
                    or "project Mise identity validation failed"
                )
        doc = u.Cli.toml_parse_text(rendered)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_ensure_table(doc, "tools")
        for selector, version in local_tools.items():
            if selector in tools:
                source = resolved.value.mise_tool_sources[selector]
                return r[str].fail(
                    "project Mise selector collides with fleet tool "
                    f"{selector!r}: global .mise.toml template and {source}"
                )
            tools[selector] = version
        return r[str].ok(u.Cli.toml_dumps(doc))


__all__: tuple[str, ...] = ("FlextInfraUtilitiesProjectManagedArtifacts",)
