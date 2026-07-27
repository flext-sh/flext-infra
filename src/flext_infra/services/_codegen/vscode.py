"""VS Code settings codegen owner — the single canonical merge instrumentation.

This is the only place that knows how ``.vscode/settings.json`` is produced.
It reads any existing document through the thin canonical JSON wrapper
(``u.Cli.json_read`` — strict JSON, no bespoke parser), merges the config-driven
canonical keys from ``config.Infra.codegen.vscode`` plus the artifact-derived
exclude maps, derives shallow member ``.venv`` globs from the workspace manifest,
and serializes the result with ``u.Cli.json_dumps``. Rendering, planning, atomic
writes, and fixed-point verification stay owned by ``FlextInfraCodegenConform``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraCodegenVscodeMixin:
    """Produce the canonical ``.vscode/settings.json`` document for one root."""

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

    @staticmethod
    def _read_existing_settings(settings_path: Path) -> p.Result[t.JsonMapping]:
        """Read an existing settings document via the thin canonical JSON reader."""
        if not settings_path.exists():
            empty_settings: t.JsonMapping = {}
            return r[t.JsonMapping].ok(empty_settings)
        return u.Cli.json_read(settings_path)

    @classmethod
    def _apply_canonical_settings(
        cls, settings: t.MutableJsonMapping, workspace_root: Path
    ) -> bool:
        """Merge canonical codegen VS Code settings into one settings mapping."""
        spec = config.Infra.codegen.vscode
        changed = cls._apply_enforced_settings(
            settings,
            scalar_settings=spec.scalar_settings,
            list_settings=spec.list_settings,
            workspace_root=workspace_root,
        )
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
        for key, list_value in list_settings.items():
            entries = cls._resolve_list_setting(
                key, list_value, workspace_root=workspace_root
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


__all__: list[str] = ["FlextInfraCodegenVscodeMixin"]
