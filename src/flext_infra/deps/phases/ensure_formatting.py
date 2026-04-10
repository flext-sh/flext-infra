"""Phase: Ensure safe default config for TOML/YAML formatting tools."""

from __future__ import annotations

from flext_infra import FlextInfraToml, m, t, u


class FlextInfraEnsureFormattingToolingPhase:
    """Ensure safe default config for TOML/YAML formatting tools."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        codespell_builder = (
            m.Infra.TomlPhaseConfig
            .Builder("codespell")
            .table("codespell")
            .value(
                "check-filenames",
                self._tool_config.tools.codespell.check_filenames,
            )
        )
        if self._tool_config.tools.codespell.ignore_words_list:
            codespell_builder = codespell_builder.value(
                "ignore-words-list",
                self._tool_config.tools.codespell.ignore_words_list,
            )
        codespell_phase = codespell_builder.build()
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
        changes = [
            *FlextInfraToml.apply_phases(
                doc,
                codespell_phase,
                tomlsort_phase,
                yamlfix_phase,
            ),
        ]
        tool_table = u.Cli.toml_get_table(doc, "tool")
        if tool_table is None:
            return changes
        codespell_table = u.Cli.toml_get_table(tool_table, "codespell")
        if codespell_table is None or "skip" not in codespell_table:
            return changes
        del codespell_table["skip"]
        changes.append("removed codespell.skip hardcode")
        return changes
