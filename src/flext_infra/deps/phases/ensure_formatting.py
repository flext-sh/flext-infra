"""Phase: Ensure safe default settings for TOML/YAML formatting tools.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import config, m, p, t, u
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsureFormattingToolingPhase:
    """Ensure safe default settings for TOML/YAML formatting tools."""

    def _phases(
        self,
    ) -> tuple[
        p.Cli.TomlPhaseConfig,
        p.Cli.TomlPhaseConfig,
        p.Cli.TomlPhaseConfig,
        p.Cli.TomlPhaseConfig,
        p.Cli.TomlPhaseConfig,
    ]:
        """Build the canonical formatting phases."""
        tools = config.Infra.tooling.tools
        codespell_builder = (
            m.Cli.TomlPhaseConfig
            .Builder("codespell")
            .table("codespell")
            .value("check-filenames", tools.codespell.check_filenames)
        )
        if tools.codespell.ignore_words_list:
            codespell_builder = codespell_builder.value(
                "ignore-words-list", tools.codespell.ignore_words_list
            )
        codespell_phase = codespell_builder.build()
        deptry_phase = (
            m.Cli.TomlPhaseConfig
            .Builder("deptry")
            .table("deptry")
            .list("known_first_party", tools.deptry.known_first_party)
            .list(
                "pep621_dev_dependency_groups",
                tools.deptry.pep621_dev_dependency_groups,
            )
            .build()
        )
        hatch_phase = (
            m.Cli.TomlPhaseConfig
            .Builder("hatch")
            .table("hatch", "metadata")
            .value("allow-direct-references", tools.hatch.allow_direct_references)
            .build()
        )
        tomlsort_phase = (
            m.Cli.TomlPhaseConfig
            .Builder("tomlsort")
            .table("tomlsort")
            .value("all", tools.tomlsort.all)
            .value("in_place", tools.tomlsort.in_place)
            .list("sort_first", tools.tomlsort.sort_first)
            .build()
        )
        yamlfix_phase = (
            m.Cli.TomlPhaseConfig
            .Builder("yamlfix")
            .table("yamlfix")
            .value("line_length", tools.yamlfix.line_length)
            .value("preserve_quotes", tools.yamlfix.preserve_quotes)
            .value("whitelines", tools.yamlfix.whitelines)
            .value("section_whitelines", tools.yamlfix.section_whitelines)
            .value("explicit_start", tools.yamlfix.explicit_start)
            .build()
        )
        return (
            codespell_phase,
            deptry_phase,
            hatch_phase,
            tomlsort_phase,
            yamlfix_phase,
        )

    @staticmethod
    def _remove_codespell_skip_doc(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Remove the stale hardcoded codespell skip entry from one TOML document."""
        tool_table = u.Cli.toml_table_child(doc, "tool")
        if tool_table is None:
            return ()
        codespell_table = u.Cli.toml_table_child(tool_table, "codespell")
        if codespell_table is None or "skip" not in codespell_table:
            return ()
        del codespell_table["skip"]
        return ["removed codespell.skip hardcode"]

    @staticmethod
    def _remove_codespell_skip_payload(payload: t.MutableJsonMapping) -> t.StrSequence:
        """Remove the stale hardcoded codespell skip entry from one plain payload."""
        codespell_table = u.Cli.toml_mapping_path(payload, ("tool", "codespell"))
        if codespell_table is None:
            return ()
        if u.Cli.toml_mapping_remove_key_if_present(codespell_table, "skip"):
            return ["removed codespell.skip hardcode"]
        return ()

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply canonical codespell, tomlsort, and yamlfix configuration."""
        changes = list(FlextInfraTomlPhaseService.apply_phases(doc, *self._phases()))
        changes.extend(self._remove_codespell_skip_doc(doc))
        return changes

    def apply_payload(self, payload: t.MutableJsonMapping) -> t.StrSequence:
        """Apply formatting defaults directly to one normalized payload."""
        changes = list(
            FlextInfraTomlPhaseService.apply_payload_phases(payload, *self._phases())
        )
        changes.extend(self._remove_codespell_skip_payload(payload))
        return changes


__all__: list[str] = ["FlextInfraEnsureFormattingToolingPhase"]
