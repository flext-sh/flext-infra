"""Phase: Ensure standard mypy configuration with pydantic plugin across all projects."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence

import tomlkit
from pydantic import ValidationError
from tomlkit.container import Container
from tomlkit.items import AoT, Item, Table
from tomlkit.toml_document import TOMLDocument

from flext_infra import c, m, t, u


class FlextInfraEnsureMypyConfigPhase:
    """Ensure standard mypy configuration with pydantic plugin across all projects."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    @staticmethod
    def _normalize_override_entry(item: object) -> t.StrSequenceMapping | None:
        """Normalize one ``[[tool.mypy.overrides]]`` entry into the shared schema."""
        normalized_value = (
            item.unwrap() if isinstance(item, (Item, TOMLDocument)) else item
        )
        if not isinstance(normalized_value, Mapping):
            return None
        try:
            normalized_item = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                normalized_value,
            )
        except ValidationError:
            return None
        return {
            "module": u.Infra.as_string_list(normalized_item.get("module")),
            "disable_error_code": u.Infra.as_string_list(
                normalized_item.get("disable_error_code")
            ),
        }

    def apply(self, doc: tomlkit.TOMLDocument) -> t.StrSequence:
        changes: list[str] = []
        tool: Item | Container | None = None
        if c.Infra.TOOL in doc:
            tool = doc[c.Infra.TOOL]
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        mypy = u.Infra.ensure_table(tool, c.Infra.MYPY)
        if (
            u.Infra.unwrap_item(u.Infra.get(mypy, c.Infra.PYTHON_VERSION_UNDERSCORE))
            != "3.13"
        ):
            mypy[c.Infra.PYTHON_VERSION_UNDERSCORE] = "3.13"
            changes.append("tool.mypy.python_version set to 3.13")
        current_plugins = u.Infra.as_string_list(u.Infra.get(mypy, c.Infra.PLUGINS))
        needed_plugins = [
            plugin
            for plugin in self._tool_config.tools.mypy.plugins
            if plugin not in current_plugins
        ]
        if needed_plugins:
            mypy[c.Infra.PLUGINS] = u.Infra.array(
                sorted(
                    set(current_plugins) | set(self._tool_config.tools.mypy.plugins),
                ),
            )
            changes.append(f"tool.mypy.plugins added {', '.join(needed_plugins)}")
        current_disabled = u.Infra.as_string_list(
            u.Infra.get(mypy, c.Infra.DISABLE_ERROR_CODE)
        )
        needed_disabled = [
            ec
            for ec in self._tool_config.tools.mypy.disabled_error_codes
            if ec not in current_disabled
        ]
        if needed_disabled:
            mypy[c.Infra.DISABLE_ERROR_CODE] = u.Infra.array(
                sorted(
                    set(current_disabled)
                    | set(self._tool_config.tools.mypy.disabled_error_codes),
                ),
            )
            changes.append(
                f"tool.mypy.disable_error_code added {', '.join(needed_disabled)}",
            )
        for key, value in self._tool_config.tools.mypy.boolean_settings.items():
            if u.Infra.unwrap_item(u.Infra.get(mypy, key)) is not value:
                mypy[key] = value
                changes.append(f"tool.mypy.{key} set to {value}")
        self._ensure_overrides(tool, changes)
        return changes

    def _ensure_overrides(
        self,
        tool: Table,
        changes: MutableSequence[str],
    ) -> None:
        """Ensure [[tool.mypy.overrides]] matches configured overrides."""
        configured = self._tool_config.tools.mypy.overrides
        if not configured:
            return
        expected: Sequence[t.StrSequenceMapping] = [
            {
                "module": list(entry.modules),
                "disable_error_code": list(entry.disable_error_codes),
            }
            for entry in configured
        ]
        mypy_table = u.Infra.get(tool, c.Infra.MYPY)
        raw = (
            u.Infra.get(mypy_table, "overrides")
            if isinstance(mypy_table, Table)
            else None
        )
        current: Sequence[t.StrSequenceMapping] = []
        if isinstance(raw, (list, AoT)):
            normalized_current: MutableSequence[t.StrSequenceMapping] = []
            raw_items: Sequence[object] = list(raw)
            for item in raw_items:
                normalized_item = self._normalize_override_entry(item)
                if normalized_item is None:
                    continue
                normalized_current.append(normalized_item)
            current = normalized_current
        if list(current) == list(expected):
            return
        mypy_section = u.Infra.ensure_table(tool, c.Infra.MYPY)
        mypy_section["overrides"] = [
            {
                "module": list(entry["module"]),
                "disable_error_code": list(entry["disable_error_code"]),
            }
            for entry in expected
        ]
        changes.append(
            "tool.mypy.overrides synchronized for auto-generated files and PEP 695 generics",
        )


__all__ = ["FlextInfraEnsureMypyConfigPhase"]
