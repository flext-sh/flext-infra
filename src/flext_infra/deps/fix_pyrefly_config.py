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

from flext_core import FlextLogger
from flext_infra import (
    FlextInfraExtraPathsManager,
    FlextInfraUtilitiesCliDispatch,
    c,
    m,
    r,
    s,
    t,
    u,
)

_logger = FlextLogger.create_module_logger(__name__)


class FlextInfraConfigFixer(s[bool]):
    """Fix pyrefly configuration across workspace projects."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        *,
        workspace: Path | None = None,
    ) -> None:
        """Initialize pyrefly config fixer."""
        self._workspace_root = u.Infra.resolve_workspace_root_or_cwd(
            workspace_root or workspace,
        )
        config_result = u.Infra.load_tool_config()
        if config_result.is_failure:
            msg = config_result.error or "failed to load deps tool config"
            raise ValueError(msg)
        self._tool_config: m.Infra.ToolConfigDocument = config_result.value

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() directly")

    def find_pyproject_files(
        self,
        project_paths: Sequence[Path] | None = None,
    ) -> r[Sequence[Path]]:
        """Find pyproject.toml files for selected projects."""
        return u.Infra.find_all_pyproject_files(
            self._workspace_root,
            project_paths=project_paths,
        )

    def process_file(self, path: Path, *, dry_run: bool = False) -> r[t.StrSequence]:
        """Process one pyproject.toml file and apply fixes."""
        document_result = u.Cli.toml_read_document(path)
        if document_result.is_failure:
            return r[t.StrSequence].fail(
                document_result.error or f"failed to read {path}",
            )
        doc = document_result.value
        doc_data = doc.unwrap()
        tool_data = doc_data.get(c.Infra.TOOL)
        if not u.is_mapping(tool_data):
            return r[t.StrSequence].ok([])
        typed_tool_data: MutableMapping[str, t.Infra.InfraValue] = (
            t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(tool_data)
        )
        pyrefly_data = typed_tool_data.get(c.Infra.PYREFLY)
        if not u.is_mapping(pyrefly_data):
            return r[t.StrSequence].ok([])
        try:
            pyrefly: MutableMapping[str, t.Infra.InfraValue] = (
                t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(pyrefly_data)
            )
        except ValidationError:
            return r[t.StrSequence].ok([])
        all_fixes: MutableSequence[str] = []
        fixes = self._fix_search_paths_tk(pyrefly, path.parent)
        all_fixes.extend(fixes)
        fixes = self._remove_ignore_sub_config_tk(pyrefly)
        all_fixes.extend(fixes)
        if (
            any("removed ignore" in item for item in all_fixes)
            or path.parent == self._workspace_root
        ):
            fixes = self._ensure_project_excludes_tk(pyrefly)
            all_fixes.extend(fixes)
        if all_fixes and (not dry_run):
            typed_tool_data[c.Infra.PYREFLY] = dict(pyrefly)
            doc_data[c.Infra.TOOL] = typed_tool_data
            new_doc = u.Cli.toml_document()
            for key, value in doc_data.items():
                new_doc[str(key)] = value
            write_result = u.Cli.toml_write_document(path, new_doc)
            if write_result.is_failure:
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
    ) -> r[t.StrSequence]:
        """Run pyrefly configuration fixes for selected projects."""
        project_paths = [self._resolve_project_path(project) for project in projects]
        files_result = self.find_pyproject_files(project_paths or None)
        if files_result.is_failure:
            return r[t.StrSequence].fail(
                files_result.error or "failed to find pyproject files",
            )
        messages: MutableSequence[str] = []
        total_fixes = 0
        pyproject_files: Sequence[Path] = files_result.value
        for path in pyproject_files:
            fixes_result = self.process_file(path, dry_run=dry_run)
            if fixes_result.is_failure:
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

    def _ensure_project_excludes_tk(
        self,
        pyrefly: MutableMapping[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        fixes: MutableSequence[str] = []
        excludes = pyrefly.get(c.Infra.PROJECT_EXCLUDES)
        current: t.StrSequence = []
        if isinstance(excludes, list):
            exclude_items: t.Cli.JsonList = []
            with contextlib.suppress(ValidationError):
                exclude_items = t.Cli.JSON_LIST_ADAPTER.validate_python([*excludes])
            current = [str(value) for value in exclude_items]
        expected = sorted(set(self._tool_config.tools.pyrefly.project_exclude_globs))
        if current != expected:
            pyrefly[c.Infra.PROJECT_EXCLUDES] = u.Cli.toml_array(expected)
            fixes.append("synchronized project-excludes from YAML rules")
        return fixes

    def _fix_search_paths_tk(
        self,
        pyrefly: MutableMapping[str, t.Infra.InfraValue],
        project_dir: Path,
    ) -> t.StrSequence:
        fixes: MutableSequence[str] = []
        search_path = pyrefly.get(c.Infra.SEARCH_PATH)
        if not isinstance(search_path, list):
            return []
        manager = FlextInfraExtraPathsManager(workspace_root=self._workspace_root)
        expected_search = manager.pyrefly_search_paths(
            project_dir=project_dir,
            is_root=project_dir == self._workspace_root,
        )
        search_raw = pyrefly.get(c.Infra.SEARCH_PATH)
        current_paths: t.Cli.JsonList = []
        if isinstance(search_raw, list):
            with contextlib.suppress(ValidationError):
                current_paths = t.Cli.JSON_LIST_ADAPTER.validate_python(
                    list(search_raw)
                )
        current_search = [
            str(path_item) for path_item in current_paths if isinstance(path_item, str)
        ]
        if current_search != expected_search:
            pyrefly[c.Infra.SEARCH_PATH] = u.Cli.toml_array(expected_search)
            fixes.append("synchronized search-path from YAML rules")
        return fixes

    def _remove_ignore_sub_config_tk(
        self,
        pyrefly: MutableMapping[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        fixes: MutableSequence[str] = []
        sub_configs = pyrefly.get(c.Infra.SUB_CONFIG)
        if not isinstance(sub_configs, list):
            return []
        new_configs: MutableSequence[t.Infra.InfraValue] = []
        configs: Sequence[t.Infra.InfraValue] = []
        with contextlib.suppress(ValidationError):
            configs = t.Infra.INFRA_SEQ_ADAPTER.validate_python(sub_configs)
        for conf in configs:
            conf_out: t.Infra.InfraValue = conf
            conf_map: Mapping[str, t.Infra.InfraValue] = {}
            if u.is_mapping(conf):
                try:
                    conf_map = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(conf)
                    conf_out = dict(conf_map)
                except ValidationError:
                    pass
            if conf_map.get(c.Infra.IGNORE) is True:
                matches = conf_map.get("matches", c.Infra.Defaults.UNKNOWN)
                fixes.append(f"removed ignore=true sub-config for '{matches}'")
                continue
            new_configs.append(conf_out)
        if len(new_configs) != len(configs):
            pyrefly[c.Infra.SUB_CONFIG] = new_configs
        return fixes

    def _resolve_project_path(self, raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = self._workspace_root / path
        return path.resolve()

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Legacy entrypoint routed through the canonical check CLI."""
        return FlextInfraUtilitiesCliDispatch.run_command(
            c.Infra.Verbs.CHECK,
            "fix-pyrefly-config",
            argv,
        )


if __name__ == "__main__":
    raise SystemExit(FlextInfraConfigFixer.main())


__all__ = ["FlextInfraConfigFixer"]
