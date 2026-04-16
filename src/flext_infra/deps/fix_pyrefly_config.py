"""CLI tool to fix Pyrefly configurations across projects.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import (
    FlextInfraExtraPathsManager,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)

_logger = u.fetch_logger(__name__)


class FlextInfraConfigFixer(s[bool]):
    """Fix pyrefly configuration across workspace projects."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        *,
        workspace: Path | None = None,
    ) -> None:
        """Initialize pyrefly settings fixer."""
        self._workspace_root = u.Infra.resolve_workspace_root_or_cwd(
            workspace_root or workspace,
        )
        config_result = u.Infra.load_tool_config()
        if config_result.failure:
            msg = config_result.error or "failed to load deps tool settings"
            raise ValueError(msg)
        self._tool_config: m.Infra.ToolConfigDocument = config_result.value

    @override
    def execute(self) -> p.Result[bool]:
        return r[bool].fail("Use run() directly")

    def process_file(
        self, path: Path, *, dry_run: bool = False
    ) -> p.Result[t.StrSequence]:
        """Process one pyproject.toml file and apply fixes."""
        document_result = u.Cli.toml_read_document(path)
        if document_result.failure:
            return r[t.StrSequence].fail(
                document_result.error or f"failed to read {path}",
            )
        doc = document_result.value
        doc_data = doc.unwrap()
        tool_data = doc_data.get(c.Infra.TOOL)
        if not isinstance(tool_data, Mapping):
            return r[t.StrSequence].ok([])
        typed_tool_data: MutableMapping[str, t.Infra.InfraValue] = (
            t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(tool_data)
        )
        pyrefly_data = typed_tool_data.get(c.Infra.PYREFLY)
        if not isinstance(pyrefly_data, Mapping):
            return r[t.StrSequence].ok([])
        try:
            pyrefly: MutableMapping[str, t.Infra.InfraValue] = (
                t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(pyrefly_data)
            )
        except c.ValidationError:
            return r[t.StrSequence].ok([])
        all_fixes: MutableSequence[str] = []
        project_dir = path.parent
        is_root = project_dir == self._workspace_root
        search_raw = pyrefly.get(c.Infra.SEARCH_PATH)
        if isinstance(search_raw, list):
            current_paths: t.Cli.JsonList = []
            with contextlib.suppress(ValidationError):
                current_paths = t.Cli.JSON_LIST_ADAPTER.validate_python(
                    list(search_raw)
                )
            current_search = [
                str(path_item)
                for path_item in current_paths
                if isinstance(path_item, str)
            ]
            expected_search = FlextInfraExtraPathsManager(
                workspace_root=self._workspace_root
            ).pyrefly_search_paths(
                project_dir=project_dir,
                is_root=is_root,
            )
            if current_search != expected_search:
                pyrefly[c.Infra.SEARCH_PATH] = u.Cli.toml_array(expected_search)
                all_fixes.append("synchronized search-path from YAML rules")
        removed_ignore = False
        sub_configs = pyrefly.get(c.Infra.SUB_CONFIG)
        if isinstance(sub_configs, list):
            new_configs: MutableSequence[t.Infra.InfraValue] = []
            configs: Sequence[t.Infra.InfraValue] = []
            with contextlib.suppress(ValidationError):
                configs = t.Infra.INFRA_SEQ_ADAPTER.validate_python(sub_configs)
            for conf in configs:
                conf_out: t.Infra.InfraValue = conf
                conf_map: t.Infra.ContainerDict = {}
                if isinstance(conf, Mapping):
                    try:
                        conf_map = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(conf)
                        conf_out = dict(conf_map)
                    except c.ValidationError:
                        conf_map = {}
                if conf_map.get(c.Infra.IGNORE) is True:
                    removed_ignore = True
                    matches = conf_map.get("matches", c.Infra.DEFAULT_UNKNOWN)
                    all_fixes.append(
                        f"removed ignore=true sub-settings for '{matches}'"
                    )
                    continue
                new_configs.append(conf_out)
            if len(new_configs) != len(configs):
                pyrefly[c.Infra.SUB_CONFIG] = new_configs
        if removed_ignore or is_root:
            current_excludes: t.StrSequence = []
            excludes = pyrefly.get(c.Infra.PROJECT_EXCLUDES)
            if isinstance(excludes, list):
                exclude_items: t.Cli.JsonList = []
                with contextlib.suppress(ValidationError):
                    exclude_items = t.Cli.JSON_LIST_ADAPTER.validate_python([*excludes])
                current_excludes = [str(value) for value in exclude_items]
            expected_excludes = sorted(
                set(self._tool_config.tools.pyrefly.project_exclude_globs)
            )
            if current_excludes != expected_excludes:
                pyrefly[c.Infra.PROJECT_EXCLUDES] = u.Cli.toml_array(expected_excludes)
                all_fixes.append("synchronized project-excludes from YAML rules")
        if all_fixes and (not dry_run):
            typed_tool_data[c.Infra.PYREFLY] = dict(pyrefly)
            doc_data[c.Infra.TOOL] = typed_tool_data
            new_doc = u.Cli.toml_document()
            for key, value in doc_data.items():
                new_doc[str(key)] = value
            write_result = u.Cli.toml_write_document(path, new_doc)
            if write_result.failure:
                return r[t.StrSequence].fail(
                    write_result.error or f"failed to write {path}",
                )
        return r[t.StrSequence].ok(all_fixes)

    def run(
        self,
        projects: t.StrSequence,
        *,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> p.Result[t.StrSequence]:
        """Run pyrefly configuration fixes for selected projects."""
        project_paths = [
            (
                project_path
                if project_path.is_absolute()
                else (self._workspace_root / project_path)
            ).resolve()
            for project in projects
            for project_path in [Path(project)]
        ]
        files_result = u.Infra.find_all_pyproject_files(
            self._workspace_root,
            project_paths=project_paths or None,
        )
        if files_result.failure:
            return r[t.StrSequence].fail(
                files_result.error or "failed to find pyproject files",
            )
        messages: MutableSequence[str] = []
        total_fixes = 0
        pyproject_files: Sequence[Path] = files_result.value
        for path in pyproject_files:
            fixes_result = self.process_file(path, dry_run=dry_run)
            if fixes_result.failure:
                return r[t.StrSequence].fail(
                    fixes_result.error or f"failed to process {path}",
                )
            fixes: t.StrSequence = fixes_result.value
            if not fixes:
                continue
            total_fixes += len(fixes)
            if verbose:
                try:
                    rel = path.relative_to(self._workspace_root)
                except ValueError:
                    rel = path
                for fix in fixes:
                    line = f"  {('(dry)' if dry_run else '✓')} {rel}: {fix}"
                    _logger.info("pyrefly_config_fix", detail=line)
                    messages.append(line)
        if verbose and total_fixes == 0:
            _logger.info("pyrefly_configs_clean")
        return r[t.StrSequence].ok(messages)


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = ["FlextInfraConfigFixer"]
