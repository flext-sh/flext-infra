"""Canonical VS Code settings synchronization for FLEXT workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_core import r
from flext_infra import c, config, p, t, u


class FlextInfraWorkspaceVscode:
    """Synchronize generated VS Code settings without replacing custom keys."""

    @classmethod
    def sync_settings(
        cls, workspace_root: Path, *, apply: bool = True
    ) -> p.Result[bool]:
        """Ensure ``.vscode/settings.json`` carries the canonical FLEXT defaults."""
        if not (workspace_root / c.PYPROJECT_FILENAME).is_file():
            return r[bool].ok(False)
        settings_path = (
            workspace_root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        )
        read_result = cls.read_settings(settings_path)
        if read_result.failure:
            return r[bool].fail(read_result.error or "VS Code settings read failed")
        settings: t.MutableJsonMapping = {
            key: u.normalize_to_json_value(value)
            for key, value in read_result.value.items()
        }
        if not cls.apply_required_settings(settings):
            return r[bool].ok(False)
        if not apply:
            return r[bool].ok(True)
        write_result = u.Cli.json_write(settings_path, settings)
        if write_result.failure:
            return r[bool].fail(write_result.error or "VS Code settings write failed")
        return r[bool].ok(True)

    @classmethod
    def read_settings(cls, settings_path: Path) -> p.Result[t.JsonMapping]:
        """Read VS Code JSONC settings as a validated JSON mapping."""
        if not settings_path.exists():
            empty_settings: t.JsonMapping = {}
            return r[t.JsonMapping].ok(empty_settings)
        read_result = u.Cli.files_read_text(settings_path)
        if read_result.failure:
            return r[t.JsonMapping].fail(
                read_result.error or "VS Code settings read failed"
            )
        parsed = u.Cli.json_loads(read_result.value)
        if parsed.failure:
            parsed = u.Cli.json_loads(cls.normalize_jsonc(read_result.value))
        if parsed.failure:
            return r[t.JsonMapping].fail(
                parsed.error or "VS Code settings JSONC parse failed"
            )
        if not isinstance(parsed.value, Mapping):
            return r[t.JsonMapping].fail("VS Code settings root must be an object")
        return r[t.JsonMapping].ok(
            t.Cli.JSON_MAPPING_ADAPTER.validate_python(parsed.value)
        )

    @classmethod
    def apply_required_settings(cls, settings: t.MutableJsonMapping) -> bool:
        """Mutate one settings mapping with the canonical FLEXT VS Code keys."""
        changed = cls.apply_scalar_settings(settings)
        return cls.apply_watcher_excludes(settings) or changed

    @staticmethod
    def apply_scalar_settings(settings: t.MutableJsonMapping) -> bool:
        """Apply top-level scalar VS Code settings."""
        changed = False
        for key, value in c.Infra.VSCODE_REQUIRED_SCALAR_SETTINGS.items():
            if settings.get(key) == value:
                continue
            settings[key] = value
            changed = True
        return changed

    @staticmethod
    def apply_watcher_excludes(settings: t.MutableJsonMapping) -> bool:
        """Exclude nested worktrees from the parent VS Code file watcher."""
        key = c.Infra.VSCODE_FILES_WATCHER_EXCLUDE_KEY
        current = settings.get(key)
        excludes: t.JsonDict = (
            {name: u.normalize_to_json_value(value) for name, value in current.items()}
            if isinstance(current, Mapping)
            else {}
        )
        required_excludes: t.JsonDict = {
            f"**/{config.Infra.worktree_transaction.root}/**": True,
            **c.Infra.VSCODE_REQUIRED_WATCHER_EXCLUDES,
        }
        changed = False
        for pattern, expected in required_excludes.items():
            if excludes.get(pattern) == expected:
                continue
            excludes[pattern] = expected
            changed = True
        if not changed and settings.get(key) == excludes:
            return False
        settings[key] = excludes
        return True

    @classmethod
    def normalize_jsonc(cls, content: str) -> str:
        """Return JSON text from VS Code JSONC settings content."""
        return cls.remove_trailing_commas(cls.remove_jsonc_comments(content))

    @staticmethod
    def remove_jsonc_comments(content: str) -> str:
        """Remove JSONC comments while preserving string content."""
        output: list[str] = []
        in_string = False
        escaped = False
        in_line_comment = False
        in_block_comment = False
        index = 0
        while index < len(content):
            char = content[index]
            next_char = content[index + 1] if index + 1 < len(content) else ""
            if in_line_comment:
                if char in "\r\n":
                    in_line_comment = False
                    output.append(char)
                index += 1
                continue
            if in_block_comment:
                if char == "*" and next_char == "/":
                    in_block_comment = False
                    index += 2
                    continue
                index += 1
                continue
            if in_string:
                output.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue
            if char == '"':
                in_string = True
                output.append(char)
                index += 1
                continue
            if char == "/" and next_char == "/":
                in_line_comment = True
                index += 2
                continue
            if char == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue
            output.append(char)
            index += 1
        return "".join(output)

    @staticmethod
    def remove_trailing_commas(content: str) -> str:
        """Remove commas before JSON object or array closers outside strings."""
        output: list[str] = []
        in_string = False
        escaped = False
        index = 0
        while index < len(content):
            char = content[index]
            if in_string:
                output.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue
            if char == '"':
                in_string = True
                output.append(char)
                index += 1
                continue
            if char == ",":
                next_index = index + 1
                while next_index < len(content) and content[next_index].isspace():
                    next_index += 1
                if next_index < len(content) and content[next_index] in "}]":
                    index += 1
                    continue
            output.append(char)
            index += 1
        return "".join(output)


__all__: list[str] = ["FlextInfraWorkspaceVscode"]
