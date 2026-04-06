"""Phase: Ensure standard Pyrefly configuration for max-strict typing."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraToml, c, m, t

if TYPE_CHECKING:
    from flext_infra import FlextInfraExtraPathsManager


class FlextInfraEnsurePyreflyConfigPhase:
    """Ensure standard Pyrefly configuration for max-strict typing."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        project_dir: Path | None = None,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> t.StrSequence:
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
            expected_search = [c.Infra.Paths.DEFAULT_SRC_DIR]
            expected_includes = [f"{c.Infra.Paths.DEFAULT_SRC_DIR}/**/*.py*"]
        error_values: Sequence[tuple[str, t.Cli.JsonValue]] = (
            *(
                (error_rule, True)
                for error_rule in self._tool_config.tools.pyrefly.strict_errors
            ),
            *(
                (error_rule, False)
                for error_rule in self._tool_config.tools.pyrefly.disabled_errors
            ),
        )
        phase = (
            m.Infra.TomlPhaseConfig
            .Builder("pyrefly")
            .table(c.Infra.PYREFLY)
            .value(c.Infra.PYTHON_VERSION_HYPHEN, pyrefly_rules.python_version)
            .deprecated("python-interpreter-path")
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
        return FlextInfraToml.apply_phases(doc, phase)


__all__ = ["FlextInfraEnsurePyreflyConfigPhase"]
