"""Phase: Ensure standard Pyrefly configuration for max-strict typing."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import tomlkit
from flext_core import FlextTypes as t
from tomlkit.items import Item, Table

from flext_infra import FlextInfraExtraPathsManager, c, m, u


class FlextInfraEnsurePyreflyConfigPhase:
    """Ensure standard Pyrefly configuration for max-strict typing."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def _expected_project_includes(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        pyrefly_rules = self._tool_config.tools.pyrefly.path_rules
        env_dirs = set(pyrefly_rules.env_dirs)
        includes: MutableSequence[str] = []
        if is_root:
            root_dirs = set(u.Infra.discover_python_dirs(project_dir))
            for directory in sorted(root_dirs & env_dirs):
                includes.append(f"{directory}/**/*.py*")
            for child in sorted(project_dir.iterdir()):
                if not child.is_dir():
                    continue
                if not (child / c.Infra.Files.PYPROJECT_FILENAME).exists():
                    continue
                child_dirs = set(u.Infra.discover_python_dirs(child))
                for directory in sorted(child_dirs & env_dirs):
                    includes.append(f"{child.name}/{directory}/**/*.py*")
        else:
            project_dirs = set(u.Infra.discover_python_dirs(project_dir))
            for directory in sorted(project_dirs & env_dirs):
                includes.append(f"{directory}/**/*.py*")
        return sorted(set(includes))

    def apply(
        self,
        doc: tomlkit.TOMLDocument,
        *,
        is_root: bool,
        project_dir: Path | None = None,
    ) -> t.StrSequence:
        changes: MutableSequence[str] = []
        tool: Item | None = None
        if c.Infra.Toml.TOOL in doc:
            raw_tool = doc[c.Infra.Toml.TOOL]
            if isinstance(raw_tool, Item):
                tool = raw_tool
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.Toml.TOOL] = tool
        pyrefly = u.Infra.ensure_table(tool, c.Infra.Toml.PYREFLY)
        pyrefly_rules = self._tool_config.tools.pyrefly
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, c.Infra.Toml.PYTHON_VERSION_HYPHEN),
            )
            != pyrefly_rules.python_version
        ):
            pyrefly[c.Infra.Toml.PYTHON_VERSION_HYPHEN] = pyrefly_rules.python_version
            changes.append(
                f"tool.pyrefly.python-version set to {pyrefly_rules.python_version}",
            )
        if "python-interpreter-path" in pyrefly:
            del pyrefly["python-interpreter-path"]
            changes.append(
                "tool.pyrefly.python-interpreter-path removed (non-portable)",
            )
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, c.Infra.Toml.IGNORE_ERRORS_IN_GENERATED),
            )
            is not pyrefly_rules.ignore_errors_in_generated_code
        ):
            pyrefly[c.Infra.Toml.IGNORE_ERRORS_IN_GENERATED] = (
                pyrefly_rules.ignore_errors_in_generated_code
            )
            changes.append(
                "tool.pyrefly.ignore-errors-in-generated-code synchronized from YAML rules",
            )
        if project_dir is not None:
            manager = FlextInfraExtraPathsManager()
            expected_search = manager.pyrefly_search_paths(
                project_dir=project_dir,
                is_root=is_root,
            )
            expected_includes = self._expected_project_includes(
                project_dir=project_dir,
                is_root=is_root,
            )
        else:
            expected_search = [c.Infra.Paths.DEFAULT_SRC_DIR]
            expected_includes = [f"{c.Infra.Paths.DEFAULT_SRC_DIR}/**/*.py*"]
        current_search = u.Infra.as_string_list(
            u.Infra.get(pyrefly, c.Infra.Toml.SEARCH_PATH),
        )
        if current_search != expected_search:
            pyrefly[c.Infra.Toml.SEARCH_PATH] = u.Infra.array(expected_search)
            changes.append(f"tool.pyrefly.search-path set to {expected_search}")
        current_includes = u.Infra.as_string_list(u.Infra.get(pyrefly, "project-includes"))
        if current_includes != expected_includes:
            pyrefly["project-includes"] = u.Infra.array(expected_includes)
            changes.append("tool.pyrefly.project-includes synchronized from YAML rules")
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, "disable-project-excludes-heuristics"),
            )
            is not pyrefly_rules.disable_project_excludes_heuristics
        ):
            pyrefly["disable-project-excludes-heuristics"] = (
                pyrefly_rules.disable_project_excludes_heuristics
            )
            changes.append(
                "tool.pyrefly.disable-project-excludes-heuristics synchronized from YAML rules",
            )
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, "use-ignore-files"),
            )
            is not pyrefly_rules.use_ignore_files
        ):
            pyrefly["use-ignore-files"] = pyrefly_rules.use_ignore_files
            changes.append("tool.pyrefly.use-ignore-files synchronized from YAML rules")
        errors = u.Infra.ensure_table(pyrefly, "errors")
        for error_rule in self._tool_config.tools.pyrefly.strict_errors:
            if u.Infra.unwrap_item(u.Infra.get(errors, error_rule)) is not True:
                errors[error_rule] = True
                changes.append(f"tool.pyrefly.errors.{error_rule} enabled")
        for error_rule in self._tool_config.tools.pyrefly.disabled_errors:
            if u.Infra.unwrap_item(u.Infra.get(errors, error_rule)) is not False:
                errors[error_rule] = False
                changes.append(f"tool.pyrefly.errors.{error_rule} disabled")
        current_excludes = u.Infra.as_string_list(
            u.Infra.get(pyrefly, c.Infra.Toml.PROJECT_EXCLUDES),
        )
        configured_excludes = self._tool_config.tools.pyrefly.project_exclude_globs
        expected_excludes = sorted(set(configured_excludes))
        if current_excludes != expected_excludes:
            pyrefly[c.Infra.Toml.PROJECT_EXCLUDES] = u.Infra.array(
                expected_excludes,
            )
            changes.append(
                "tool.pyrefly.project-excludes synchronized from YAML rules",
            )
        return changes


__all__ = ["FlextInfraEnsurePyreflyConfigPhase"]
