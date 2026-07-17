"""Phase: Ensure canonical fail-closed pytest configuration.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, p, t
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsurePytestConfigPhase:
    """Ensure canonical pytest policy while preserving extension declarations."""

    def __init__(self, tool_config: p.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to compose canonical pytest defaults."""
        self._tool_config = tool_config

    def _phase(self) -> p.Cli.TomlPhaseConfig:
        """Build the canonical pytest phase definition."""
        pytest = self._tool_config.tools.pytest
        return (
            m.Cli.TomlPhaseConfig
            .Builder("pytest")
            .table(c.Infra.PYTEST, c.Infra.INI_OPTIONS)
            # mro-j47u (codex): no pytest policy literal survives outside config.
            .value(c.Infra.MINVERSION, pytest.min_version)
            .list(
                c.Infra.PYTHON_CLASSES,
                pytest.python_classes,
                strategy=c.Cli.TomlMergeMode.MERGE,
            )
            .list(
                c.Infra.PYTHON_FILES,
                pytest.python_files,
                strategy=c.Cli.TomlMergeMode.MERGE,
            )
            # mro-wkii.17 (codex): replace stale collection roots and warning bypasses.
            .list("testpaths", pytest.test_paths, strategy=c.Cli.TomlMergeMode.REPLACE)
            .list(
                c.Infra.ADDOPTS,
                pytest.standard_addopts,
                # mro-pulj (codex): replace stale coverage, collection, and bypass flags.
                strategy=c.Cli.TomlMergeMode.REPLACE,
            )
            .list(
                c.Infra.MARKERS,
                pytest.standard_markers,
                strategy=c.Cli.TomlMergeMode.MERGE,
            )
            .list(
                "filterwarnings",
                pytest.filter_warnings,
                strategy=c.Cli.TomlMergeMode.REPLACE,
            )
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply canonical pytest policy while preserving extension declarations."""
        return FlextInfraTomlPhaseService.apply_phases(doc, self._phase())

    def apply_payload(self, payload: t.MutableJsonMapping) -> t.StrSequence:
        """Apply pytest defaults directly to one normalized payload."""
        return FlextInfraTomlPhaseService.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsurePytestConfigPhase"]
