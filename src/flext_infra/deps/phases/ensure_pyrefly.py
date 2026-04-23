"""Phase: Ensure standard Pyrefly configuration for max-strict typing."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    Sequence,
)
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraPhaseEngine, c, m, t

if TYPE_CHECKING:
    from flext_infra import FlextInfraExtraPathsManager


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
    ) -> m.Infra.TomlPhaseConfig:
        """Build the canonical pyrefly phase definition."""
        pyrefly_rules = self._tool_config.tools.pyrefly
        if project_dir is not None and paths_manager is not None:
            expected_search = paths_manager.pyrefly_search_paths(
                project_dir=project_dir,
                is_root=is_root,
            )
            expected_includes = paths_manager.pyrefly_project_includes(
                project_dir=project_dir,
                is_root=is_root,
            )
        else:
            expected_search = [c.Infra.DEFAULT_SRC_DIR]
            expected_includes = [f"{c.Infra.DEFAULT_SRC_DIR}/**/*.py*"]
        error_values: Sequence[tuple[str, t.JsonValue]] = (
            *(
                (error_rule, True)
                for error_rule in self._tool_config.tools.pyrefly.strict_errors
            ),
            *(
                (error_rule, False)
                for error_rule in self._tool_config.tools.pyrefly.disabled_errors
            ),
        )
        return (
            m.Infra.TomlPhaseConfig
            .Builder("pyrefly")
            .table(c.Infra.PYREFLY)
            .value(c.Infra.PYTHON_VERSION_HYPHEN, pyrefly_rules.python_version)
            .deprecated("python-interpreter-path")
            .deprecated("disable-search-path-heuristics")
            .value(
                c.Infra.IGNORE_ERRORS_IN_GENERATED,
                pyrefly_rules.ignore_errors_in_generated_code,
            )
            .list(c.Infra.SEARCH_PATH, expected_search)
            .list("project-includes", expected_includes)
            .value(
                "disable-project-excludes-heuristics",
                pyrefly_rules.disable_project_excludes_heuristics,
            )
            .value("use-ignore-files", pyrefly_rules.use_ignore_files)
            .list(
                c.Infra.PROJECT_EXCLUDES,
                sorted(set(pyrefly_rules.project_exclude_globs)),
            )
            .nested("errors", values=error_values)
            .build()
        )

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> t.StrSequence:
        """Apply canonical pyrefly table values, paths, and strict error toggles."""
        return FlextInfraPhaseEngine.apply_phases(
            doc,
            self._phase(
                is_root=is_root,
                project_dir=project_dir,
                paths_manager=paths_manager,
            ),
        )

    def apply_payload(
        self,
        payload: MutableMapping[str, t.JsonValue],
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> t.StrSequence:
        """Apply canonical pyrefly settings to one normalized payload."""
        return FlextInfraPhaseEngine.apply_payload_phases(
            payload,
            self._phase(
                is_root=is_root,
                project_dir=project_dir,
                paths_manager=paths_manager,
            ),
        )


__all__: list[str] = ["FlextInfraEnsurePyreflyConfigPhase"]
