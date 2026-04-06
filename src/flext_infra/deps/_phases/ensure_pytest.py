"""Phase: Ensure standard pytest configuration without removing project-specific entries."""

from __future__ import annotations

from flext_infra import FlextInfraToml, c, m, t


class FlextInfraEnsurePytestConfigPhase:
    """Ensure standard pytest configuration without removing project-specific entries."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        phase = (
            m.Infra.TomlPhaseConfig
            .Builder("pytest")
            .table(c.Infra.PYTEST, c.Infra.INI_OPTIONS)
            .value(c.Infra.MINVERSION, "8.0")
            .list(
                c.Infra.PYTHON_CLASSES,
                ("Test*",),
                strategy=c.Infra.TomlMerge.MERGE,
            )
            .list(
                c.Infra.PYTHON_FILES,
                ("*_test.py", "*_tests.py", "test_*.py"),
                strategy=c.Infra.TomlMerge.MERGE,
            )
            .list(
                c.Infra.ADDOPTS,
                self._tool_config.tools.pytest.standard_addopts,
                strategy=c.Infra.TomlMerge.MERGE,
            )
            .list(
                c.Infra.MARKERS,
                self._tool_config.tools.pytest.standard_markers,
                strategy=c.Infra.TomlMerge.MERGE,
            )
            .build()
        )
        return FlextInfraToml.apply_phases(doc, phase)


__all__ = ["FlextInfraEnsurePytestConfigPhase"]
