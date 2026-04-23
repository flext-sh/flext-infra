"""Phase: Ensure safe default settings for TOML/YAML formatting tools."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
)

from flext_infra import FlextInfraPhaseEngine, m, t, u


class FlextInfraEnsureFormattingToolingPhase:
    """Ensure safe default settings for TOML/YAML formatting tools."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool settings used when enforcing formatting-related tables."""
        self._tool_config = tool_config

    def _phases(
        self,
    ) -> tuple[
        m.Infra.TomlPhaseConfig,
        m.Infra.TomlPhaseConfig,
        m.Infra.TomlPhaseConfig,
    ]:
        """Build the canonical formatting phases."""
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
        return (codespell_phase, tomlsort_phase, yamlfix_phase)

    @staticmethod
    def _remove_codespell_skip_doc(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Remove the stale hardcoded codespell skip entry from one TOML document."""
        tool_table = u.Cli.toml_table_child(doc, "tool")
        if tool_table is None:
            return []
        codespell_table = u.Cli.toml_table_child(tool_table, "codespell")
        if codespell_table is None or "skip" not in codespell_table:
            return []
        del codespell_table["skip"]
        return ["removed codespell.skip hardcode"]

    @staticmethod
    def _remove_codespell_skip_payload(
        payload: MutableMapping[str, t.JsonValue],
    ) -> t.StrSequence:
        """Remove the stale hardcoded codespell skip entry from one plain payload."""
        codespell_table = u.Cli.toml_mapping_path(payload, ("tool", "codespell"))
        if codespell_table is None:
            return []
        changes: list[str] = []
        _ = u.Cli.toml_mapping_remove_key_if_present(
            codespell_table,
            "skip",
            changes,
            "removed codespell.skip hardcode",
        )
        return changes

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply canonical codespell, tomlsort, and yamlfix configuration."""
        changes = list(FlextInfraPhaseEngine.apply_phases(doc, *self._phases()))
        changes.extend(self._remove_codespell_skip_doc(doc))
        return changes

    def apply_payload(
        self,
        payload: MutableMapping[str, t.JsonValue],
    ) -> t.StrSequence:
        """Apply formatting defaults directly to one normalized payload."""
        changes = list(
            FlextInfraPhaseEngine.apply_payload_phases(payload, *self._phases())
        )
        changes.extend(self._remove_codespell_skip_payload(payload))
        return changes


__all__: list[str] = ["FlextInfraEnsureFormattingToolingPhase"]
