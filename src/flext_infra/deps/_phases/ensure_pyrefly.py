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
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, c.Infra.Toml.PYTHON_VERSION_HYPHEN),
            )
            != "3.13"
        ):
            pyrefly[c.Infra.Toml.PYTHON_VERSION_HYPHEN] = "3.13"
            changes.append("tool.pyrefly.python-version set to 3.13")
        if "python-interpreter-path" in pyrefly:
            del pyrefly["python-interpreter-path"]
            changes.append(
                "tool.pyrefly.python-interpreter-path removed (non-portable)",
            )
        if (
            u.Infra.unwrap_item(
                u.Infra.get(pyrefly, c.Infra.Toml.IGNORE_ERRORS_IN_GENERATED),
            )
            is not True
        ):
            pyrefly[c.Infra.Toml.IGNORE_ERRORS_IN_GENERATED] = True
            changes.append("tool.pyrefly.ignore-errors-in-generated-code enabled")
        if project_dir is not None:
            local_dirs = u.Infra.discover_python_dirs(project_dir)
            manager = FlextInfraExtraPathsManager()
            dep_paths = manager.get_dep_paths(doc, is_root=is_root)
            if is_root:
                expected_search = sorted(
                    {".", *local_dirs, "typings", *dep_paths},
                )
            else:
                expected_search = sorted(
                    {".", *local_dirs, *dep_paths},
                )
        else:
            expected_search = ["."]
        current_search = u.Infra.as_string_list(
            u.Infra.get(pyrefly, c.Infra.Toml.SEARCH_PATH),
        )
        if current_search != expected_search:
            pyrefly[c.Infra.Toml.SEARCH_PATH] = u.Infra.array(expected_search)
            changes.append(f"tool.pyrefly.search-path set to {expected_search}")
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
        pb2_globs = ["**/*_pb2*.py", "**/*_pb2_grpc*.py"]
        needed = set(pb2_globs) - set(current_excludes)
        if needed and (
            is_root or any(glob in current_excludes for glob in pb2_globs) or True
        ):
            pyrefly[c.Infra.Toml.PROJECT_EXCLUDES] = u.Infra.array(
                sorted(set(current_excludes) | set(pb2_globs)),
            )
            changes.append(f"tool.pyrefly.project-excludes added {', '.join(needed)}")
        return changes

EnsurePyreflyConfigPhase = FlextInfraEnsurePyreflyConfigPhase

__all__ = ["EnsurePyreflyConfigPhase", "FlextInfraEnsurePyreflyConfigPhase"]
