"""Phase: Ensure standard Pyrefly configuration for max-strict typing."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, t, u
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsurePyreflyConfigPhase:
    """Ensure standard Pyrefly configuration for max-strict typing."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used when enforcing pyrefly project settings."""
        self._tool_config = tool_config

    def _phase(
        self,
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
        stale_error_keys: t.StrSequence = (),
        declared_python_dirs: t.StrSequence = (),
    ) -> m.Infra.Deps.Toml.PhaseConfig:
        """Build the canonical pyrefly phase definition."""
        pyrefly_rules = self._tool_config.tools.pyrefly
        venv_rules = self._tool_config.tools.pyright.path_rules
        venv_path = (
            venv_rules.root_venv_path if is_root else venv_rules.project_venv_path
        )
        interpreter_path = f"{venv_path}/{venv_rules.venv_name}/bin/python"
        if project_dir is not None and paths_manager is not None:
            expected_search = paths_manager.pyrefly_search_paths(
                project_dir=project_dir, is_root=is_root
            )
            expected_includes = paths_manager.pyrefly_project_includes(
                project_dir=project_dir, is_root=is_root
            )
        else:
            expected_search = [c.Infra.DEFAULT_SRC_DIR]
            expected_includes = [f"{c.Infra.DEFAULT_SRC_DIR}/**/*.py*"]
        # mro-j47u (codex): keep pre-write Pyrefly scope identical to the first
        # post-write discovery without fabricating directories on disk.
        if declared_python_dirs:
            expected_search = sorted({
                *expected_search,
                *pyrefly_rules.path_rules.project_shared_search_paths,
            })
            # NOTE (multi-agent, mro-wkii.17.9.2.1): analysis roots belong in
            # project-includes; only import roots belong in search-path.
            expected_includes = tuple(
                f"{directory}/**/*.py*" for directory in declared_python_dirs
            )
        error_values: t.SequenceOf[tuple[str, t.JsonValue]] = (
            *(
                (error_rule, "error")
                for error_rule in self._tool_config.tools.pyrefly.strict_errors
            ),
            *(
                (error_rule, False)
                for error_rule in self._tool_config.tools.pyrefly.disabled_errors
            ),
        )
        return (
            m.Infra.Deps.Toml.PhaseConfig
            .Builder("pyrefly")
            .table(c.Infra.PYREFLY)
            .value(c.Infra.PYTHON_VERSION_HYPHEN, pyrefly_rules.python_version)
            .value("python-interpreter-path", interpreter_path)
            .deprecated("disable-search-path-heuristics")
            .deprecated("fallback-python-interpreter-name")
            # Interpreter discovery resolves PEP 660 editable sibling packages.
            .deprecated("site-package-path")
            .deprecated("skip-interpreter-query")
            .value(
                c.Infra.IGNORE_ERRORS_IN_GENERATED,
                pyrefly_rules.ignore_errors_in_generated_code,
            )
            .list(c.Infra.SEARCH_PATH, expected_search)
            .list(c.Infra.PROJECT_INCLUDES, expected_includes)
            .value(
                "disable-project-excludes-heuristics",
                pyrefly_rules.disable_project_excludes_heuristics,
            )
            .value("use-ignore-files", pyrefly_rules.use_ignore_files)
            .list(
                c.Infra.PROJECT_EXCLUDES,
                sorted(set(pyrefly_rules.project_exclude_globs)),
            )
            .nested("errors", values=error_values, deprecated_keys=stale_error_keys)
            .build()
        )

    def _configured_error_keys(self) -> frozenset[str]:
        """Return pyrefly error keys governed by the canonical tool config."""
        pyrefly_rules = self._tool_config.tools.pyrefly
        return frozenset((*pyrefly_rules.strict_errors, *pyrefly_rules.disabled_errors))

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
        declared_python_dirs: t.StrSequence = (),
    ) -> t.StrSequence:
        """Apply canonical pyrefly table values, paths, and strict error toggles."""
        configured_error_keys = self._configured_error_keys()
        errors_table = u.Cli.toml_table_path(
            doc, (c.Infra.TOOL, c.Infra.PYREFLY, "errors")
        )
        stale_error_keys = (
            tuple(key for key in errors_table if key not in configured_error_keys)
            if errors_table is not None
            else ()
        )
        return FlextInfraTomlPhaseService.apply_phases(
            doc,
            self._phase(
                is_root=is_root,
                project_dir=project_dir,
                paths_manager=paths_manager,
                stale_error_keys=stale_error_keys,
                declared_python_dirs=declared_python_dirs,
            ),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
        declared_python_dirs: t.StrSequence = (),
    ) -> t.StrSequence:
        """Apply canonical pyrefly settings to one normalized payload."""
        configured_error_keys = self._configured_error_keys()
        errors_table = u.Cli.toml_mapping_path(
            payload, (c.Infra.TOOL, c.Infra.PYREFLY, "errors")
        )
        stale_error_keys = (
            tuple(key for key in errors_table if key not in configured_error_keys)
            if errors_table is not None
            else ()
        )
        return FlextInfraTomlPhaseService.apply_payload_phases(
            payload,
            self._phase(
                is_root=is_root,
                project_dir=project_dir,
                paths_manager=paths_manager,
                stale_error_keys=stale_error_keys,
                declared_python_dirs=declared_python_dirs,
            ),
        )


__all__: list[str] = ["FlextInfraEnsurePyreflyConfigPhase"]
