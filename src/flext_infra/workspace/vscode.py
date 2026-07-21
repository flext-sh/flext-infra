"""Canonical VS Code settings synchronization for FLEXT workspaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraWorkspaceVscode:
    """Synchronize generated VS Code settings without replacing custom keys."""

    @classmethod
    def sync_settings(
        cls, workspace_root: Path, *, apply: bool = True
    ) -> p.Result[bool]:
        """Ensure ``.vscode/settings.json`` carries the canonical FLEXT defaults."""
        if not (workspace_root / c.Infra.PYPROJECT_FILENAME).is_file():
            return r[bool].ok(False)
        settings_path = (
            workspace_root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        )
        merged_result = cls.render_merged_settings(workspace_root)
        if merged_result.failure:
            return r[bool].fail(merged_result.error or "VS Code settings merge failed")
        current = ""
        if settings_path.is_file():
            read_current = u.Cli.files_read_text(settings_path)
            if read_current.failure:
                return r[bool].fail(
                    read_current.error or "VS Code settings read failed"
                )
            current = read_current.value
        if current == merged_result.value:
            return r[bool].ok(False)
        if not apply:
            return r[bool].ok(True)
        write_result = u.Cli.atomic_write_text_file(settings_path, merged_result.value)
        if write_result.failure:
            return r[bool].fail(write_result.error or "VS Code settings write failed")
        return r[bool].ok(True)

    @classmethod
    def render_merged_settings(cls, workspace_root: Path) -> p.Result[str]:
        """Return the canonical-merged ``settings.json`` document for one root."""
        settings_path = (
            workspace_root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        )
        read_result = cls.read_settings(settings_path)
        if read_result.failure:
            return r[str].fail(read_result.error or "VS Code settings read failed")
        settings: t.MutableJsonMapping = {
            key: u.normalize_to_json_value(value)
            for key, value in read_result.value.items()
        }
        _ = cls.apply_canonical_settings(settings, workspace_root)
        serialized = u.Cli.json_dumps(dict(settings), indent=2)
        if serialized.failure:
            return r[str].fail(serialized.error or "VS Code settings serialize failed")
        return r[str].ok(serialized.value + "\n")

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
    def apply_canonical_settings(
        cls, settings: t.MutableJsonMapping, workspace_root: Path
    ) -> bool:
        """Merge canonical codegen VS Code settings into one settings mapping."""
        spec = config.Infra.codegen.vscode
        changed = cls.apply_enforced_settings(
            settings,
            scalar_settings=spec.scalar_settings,
            list_settings=spec.list_settings,
            workspace_root=workspace_root,
        )
        return cls.apply_union_settings(settings, spec.map_union_settings) or changed

    @classmethod
    def apply_enforced_settings(
        cls,
        settings: t.MutableJsonMapping,
        *,
        scalar_settings: Mapping[str, str | bool],
        list_settings: Mapping[str, tuple[str, ...]],
        workspace_root: Path,
    ) -> bool:
        """Enforce exact scalar and list VS Code keys from the codegen config."""
        changed = False
        for key, value in scalar_settings.items():
            normalized = u.normalize_to_json_value(value)
            if settings.get(key) == normalized:
                continue
            settings[key] = normalized
            changed = True
        for key, value in list_settings.items():
            entries = cls.resolve_list_setting(
                key, value, workspace_root=workspace_root
            )
            canonical: list[t.JsonValue] = [
                u.normalize_to_json_value(entry) for entry in entries
            ]
            if settings.get(key) == canonical:
                continue
            settings[key] = canonical
            changed = True
        return changed

    @staticmethod
    def apply_union_settings(
        settings: t.MutableJsonMapping,
        map_union_settings: Mapping[str, Mapping[str, str | bool]],
    ) -> bool:
        """Union-merge canonical map keys over existing project entries."""
        changed = False
        for key, canonical_map in map_union_settings.items():
            current = settings.get(key)
            existing: dict[str, t.JsonValue] = (
                {
                    name: u.normalize_to_json_value(value)
                    for name, value in current.items()
                }
                if isinstance(current, Mapping)
                else {}
            )
            merged: dict[str, t.JsonValue] = existing | {
                name: u.normalize_to_json_value(value)
                for name, value in canonical_map.items()
            }
            if settings.get(key) == merged:
                continue
            settings[key] = merged
            changed = True
        return changed

    @classmethod
    def resolve_list_setting(
        cls, key: str, base_entries: tuple[str, ...], *, workspace_root: Path
    ) -> tuple[str, ...]:
        """Resolve one canonical list, deriving extra globs from the topology."""
        if key != c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY:
            return base_entries
        derived = list(base_entries)
        manifest = (
            workspace_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        if manifest.is_file():
            loaded = u.Cli.yaml_safe_load(manifest)
            if loaded.success:
                members = loaded.value.get("members")
                if isinstance(members, list):
                    for member in members:
                        if not isinstance(member, Mapping):
                            continue
                        path = member.get("path")
                        if not isinstance(path, str) or path in {"", "."}:
                            continue
                        derived.append(f"./{path}/.venv")
        return tuple(dict.fromkeys(derived))

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
