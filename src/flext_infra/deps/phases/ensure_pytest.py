"""Phase: Ensure standard pytest configuration without removing project-specific entries."""

from __future__ import annotations

from flext_infra import c, m, t
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsurePytestConfigPhase:
    """Ensure standard pytest configuration without removing project-specific entries."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to compose canonical pytest defaults."""
        self._tool_config = tool_config

    def _phase(self) -> m.Infra.Deps.Toml.PhaseConfig:
        """Build the canonical pytest phase definition."""
        pytest = self._tool_config.tools.pytest
        return (
            m.Infra.Deps.Toml.PhaseConfig
            .Builder("pytest")
            .table(c.Infra.PYTEST, c.Infra.INI_OPTIONS)
            # mro-j47u (codex): no pytest policy literal survives outside config.
            .value(c.Infra.MINVERSION, pytest.min_version)
            .list(
                c.Infra.PYTHON_CLASSES,
                pytest.python_classes,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.PYTHON_FILES,
                pytest.python_files,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.ADDOPTS,
                pytest.standard_addopts,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.MARKERS,
                pytest.standard_markers,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .list(
                "filterwarnings",
                pytest.filter_warnings,
                strategy=c.Infra.TomlMergeMode.MERGE,
            )
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply pytest defaults while preserving project-specific ini options."""
        return FlextInfraTomlPhaseService.apply_phases(doc, self._phase())

    def apply_payload(self, payload: t.MutableJsonMapping) -> t.StrSequence:
        """Apply pytest defaults directly to one normalized payload."""
        return FlextInfraTomlPhaseService.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsurePytestConfigPhase"]
