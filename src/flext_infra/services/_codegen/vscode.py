"""VS Code settings codegen owner — the single canonical merge instrumentation.

This is the only place that knows how ``.vscode/settings.json`` is produced.
It parses that explicitly JSONC document through the canonical string-aware
normalizer, validates the resulting mapping, merges the config-driven canonical
keys from ``config.Infra.codegen.vscode`` plus the artifact-derived exclude maps,
derives shallow member ``.venv`` globs from the workspace manifest, and serializes
the result with ``u.Cli.json_dumps``. Rendering, planning, atomic writes, and
fixed-point verification stay owned by ``FlextInfraCodegenConform``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, ClassVar

from flext_core import r
from flext_infra import c, config, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p


class FlextInfraCodegenVscodeMixin:
    """Produce the canonical ``.vscode/settings.json`` document for one root."""

    _JSON_STRING_PATTERN: ClassVar[str] = r'"(?:\\.|[^"\\])*"'
    _JSONC_COMMENT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"({_JSON_STRING_PATTERN})|//[^\r\n]*|/\*.*?\*/", re.DOTALL
    )
    _TRAILING_COMMA_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"({_JSON_STRING_PATTERN})|,(?=\s*[}}\]])"
    )

    @classmethod
    def render_vscode_settings(cls, workspace_root: Path) -> p.Result[str]:
        """Return the canonical-merged ``settings.json`` document for one root."""
        settings_path = (
            workspace_root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        )
        read_result = cls._read_existing_settings(settings_path)
        if read_result.failure:
            return r[str].fail(read_result.error or "VS Code settings read failed")
        settings: t.MutableJsonMapping = {
            key: u.normalize_to_json_value(value)
            for key, value in read_result.value.items()
        }
        _ = cls._apply_canonical_settings(settings, workspace_root)
        serialized = u.Cli.json_dumps(dict(settings), indent=2)
        if serialized.failure:
            return r[str].fail(serialized.error or "VS Code settings serialize failed")
        return r[str].ok(serialized.value + "\n")

    @classmethod
    def _read_existing_settings(cls, settings_path: Path) -> p.Result[t.JsonMapping]:
        """Read one VS Code JSONC document into a validated JSON mapping."""
        if not settings_path.exists():
            empty_settings: t.JsonMapping = {}
            return r[t.JsonMapping].ok(empty_settings)
        read_result = u.Cli.files_read_text(settings_path)
        if read_result.failure:
            return r[t.JsonMapping].fail(
                read_result.error or "VS Code settings read failed"
            )
        parsed = u.Cli.json_parse(cls._normalize_jsonc(read_result.value))
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
    def _normalize_jsonc(cls, content: str) -> str:
        """Return strict JSON text from VS Code JSONC content."""
        return cls._remove_trailing_commas(cls._remove_jsonc_comments(content))

    @staticmethod
    def _preserve_json_string(match: re.Match[str]) -> str:
        """Preserve JSON strings and erase the alternate lexical token."""
        return match.group(1) or ""

    @classmethod
    def _remove_jsonc_comments(cls, content: str) -> str:
        """Remove JSONC comments while preserving comment markers in strings."""
        return cls._JSONC_COMMENT_PATTERN.sub(cls._preserve_json_string, content)

    @classmethod
    def _remove_trailing_commas(cls, content: str) -> str:
        """Remove commas before object or array closers outside strings."""
        return cls._TRAILING_COMMA_PATTERN.sub(cls._preserve_json_string, content)

    @classmethod
    def _apply_canonical_settings(
        cls, settings: t.MutableJsonMapping, workspace_root: Path
    ) -> bool:
        """Merge canonical codegen VS Code settings into one settings mapping."""
        spec = config.Infra.codegen.vscode
        changed = cls._apply_enforced_settings(settings, spec, workspace_root)
        # The three exclude maps derive from the codegen artifact SSOT;
        # map_union_settings keeps only the remaining non-artifact keys.
        codegen = config.Infra.codegen
        map_union_settings: dict[str, Mapping[str, str | bool]] = {
            "files.exclude": dict(codegen.vscode_files_exclude_map),
            "files.watcherExclude": dict(codegen.vscode_watcher_exclude_map),
            "search.exclude": dict(codegen.vscode_search_exclude_map),
            **spec.map_union_settings,
        }
        return cls._apply_union_settings(settings, map_union_settings) or changed

    @classmethod
    def _apply_enforced_settings(
        cls,
        settings: t.MutableJsonMapping,
        spec: m.Infra.CodegenVscodeSpec,
        workspace_root: Path,
    ) -> bool:
        """Enforce exact scalar and list VS Code keys from the codegen config."""
        enforced: t.MutableJsonMapping = {
            key: u.normalize_to_json_value(value)
            for key, value in spec.scalar_settings.items()
        }
        enforced.update({
            key: [
                u.normalize_to_json_value(entry)
                for entry in cls._resolve_list_setting(
                    key, entries, workspace_root=workspace_root
                )
            ]
            for key, entries in spec.list_settings.items()
        })
        return cls._apply_exact_settings(settings, enforced)

    @staticmethod
    def _apply_exact_settings(
        settings: t.MutableJsonMapping, enforced: t.JsonMapping
    ) -> bool:
        """Apply fully resolved exact values to the settings document."""
        changed = False
        for key, value in enforced.items():
            if settings.get(key) == value:
                continue
            settings[key] = value
            changed = True
        return changed

    @staticmethod
    def _apply_union_settings(
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

    @staticmethod
    def _resolve_list_setting(
        key: str, base_entries: tuple[str, ...], *, workspace_root: Path
    ) -> tuple[str, ...]:
        """Resolve one canonical list, deriving extra globs from the topology."""
        if key != c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY:
            return base_entries
        manifest = (
            workspace_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        loaded = u.Cli.yaml_safe_load(manifest)
        members: t.SequenceOf[t.JsonMapping] = loaded.map_or(
            (), lambda document: u.Cli.json_as_mapping_list(document.get("members"))
        )
        member_paths = (
            path
            for member in members
            if isinstance(path := member.get("path"), str) and path not in {"", "."}
        )
        derived = (f"./{path}/.venv" for path in member_paths)
        return tuple(dict.fromkeys((*base_entries, *derived)))


__all__: list[str] = ["FlextInfraCodegenVscodeMixin"]
