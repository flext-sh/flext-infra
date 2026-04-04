"""Phase: Ensure safe default config for TOML/YAML formatting tools."""

from __future__ import annotations

from collections.abc import MutableSequence

import tomlkit
from pydantic import ValidationError
from tomlkit.items import Item, Table

from flext_infra import c, m, t, u


class FlextInfraEnsureFormattingToolingPhase:
    """Ensure safe default config for TOML/YAML formatting tools."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(self, doc: tomlkit.TOMLDocument) -> t.StrSequence:
        changes: MutableSequence[str] = []
        tool: Item | None = None
        if c.Infra.TOOL in doc:
            raw_tool = doc[c.Infra.TOOL]
            if isinstance(raw_tool, Item):
                tool = raw_tool
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        tomlsort = u.Infra.ensure_table(tool, "tomlsort")
        for key, value in {
            "all": self._tool_config.tools.tomlsort.all,
            "in_place": self._tool_config.tools.tomlsort.in_place,
            "sort_first": self._tool_config.tools.tomlsort.sort_first,
        }.items():
            current = u.Infra.unwrap_item(u.Infra.get(tomlsort, key))
            if isinstance(value, list) and isinstance(current, list):
                try:
                    current_values: t.StrSequence = (
                        t.Infra.STR_SEQ_ADAPTER.validate_python(
                            [str(x) for x in current],
                        )
                    )
                except ValidationError:
                    current_values = []
                if sorted(str(i) for i in current_values) != sorted(
                    str(i) for i in value
                ):
                    tomlsort[key] = u.Infra.array(sorted(str(item) for item in value))
                    changes.append(f"tool.tomlsort.{key} set")
            elif current != value:
                if isinstance(value, list):
                    tomlsort[key] = u.Infra.array(sorted(str(item) for item in value))
                else:
                    tomlsort[key] = value
                changes.append(f"tool.tomlsort.{key} set")
        yamlfix = u.Infra.ensure_table(tool, "yamlfix")
        for key, value in {
            "line_length": self._tool_config.tools.yamlfix.line_length,
            "preserve_quotes": self._tool_config.tools.yamlfix.preserve_quotes,
            "whitelines": self._tool_config.tools.yamlfix.whitelines,
            "section_whitelines": self._tool_config.tools.yamlfix.section_whitelines,
            "explicit_start": self._tool_config.tools.yamlfix.explicit_start,
        }.items():
            _ = u.Cli.toml_sync_value(
                yamlfix,
                key,
                value,
                changes,
                f"tool.yamlfix.{key} set to {value}",
            )
        return changes
