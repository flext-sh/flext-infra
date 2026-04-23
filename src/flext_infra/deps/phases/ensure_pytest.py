"""Phase: Ensure standard pytest configuration without removing project-specific entries."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
)

from flext_infra import FlextInfraPhaseEngine, c, m, t


class FlextInfraEnsurePytestConfigPhase:
    """Ensure standard pytest configuration without removing project-specific entries."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to compose canonical pytest defaults."""
        self._tool_config = tool_config

    def _phase(self) -> m.Infra.TomlPhaseConfig:
        """Build the canonical pytest phase definition."""
        return (
            m.Infra.TomlPhaseConfig
            .Builder("pytest")
            .table(c.Infra.PYTEST, c.Infra.INI_OPTIONS)
            .value(c.Infra.MINVERSION, "8.0")
            .list(
                c.Infra.PYTHON_CLASSES,
                ("Test*",),
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.PYTHON_FILES,
                ("*_test.py", "*_tests.py", "test_*.py"),
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.ADDOPTS,
                self._tool_config.tools.pytest.standard_addopts,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.MARKERS,
                self._tool_config.tools.pytest.standard_markers,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply pytest defaults while preserving project-specific ini options."""
        return FlextInfraPhaseEngine.apply_phases(doc, self._phase())

    def apply_payload(
        self,
        payload: MutableMapping[str, t.JsonValue],
    ) -> t.StrSequence:
        """Apply pytest defaults directly to one normalized payload."""
        return FlextInfraPhaseEngine.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsurePytestConfigPhase"]
