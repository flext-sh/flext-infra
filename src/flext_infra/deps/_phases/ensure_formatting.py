"""Phase: Ensure safe default config for TOML/YAML formatting tools."""

from __future__ import annotations

from flext_infra import FlextInfraToml, m, t


class FlextInfraEnsureFormattingToolingPhase:
    """Ensure safe default config for TOML/YAML formatting tools."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        tomlsort_phase = (
            m.Infra.TomlPhaseConfig
            .Builder("tomlsort")
            .table("tomlsort")
            .value("all", self._tool_config.tools.tomlsort.all)
            .value("in_place", self._tool_config.tools.tomlsort.in_place)
            .list("sort_first", self._tool_config.tools.tomlsort.sort_first)
            .build()
        )
        yamlfix_phase = (
            m.Infra.TomlPhaseConfig
            .Builder("yamlfix")
            .table("yamlfix")
            .value("line_length", self._tool_config.tools.yamlfix.line_length)
            .value(
                "preserve_quotes",
                self._tool_config.tools.yamlfix.preserve_quotes,
            )
            .value("whitelines", self._tool_config.tools.yamlfix.whitelines)
            .value(
                "section_whitelines",
                self._tool_config.tools.yamlfix.section_whitelines,
            )
            .value(
                "explicit_start",
                self._tool_config.tools.yamlfix.explicit_start,
            )
            .build()
        )
        return FlextInfraToml.apply_phases(doc, tomlsort_phase, yamlfix_phase)
