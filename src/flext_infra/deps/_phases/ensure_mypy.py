"""Phase: Ensure standard mypy configuration with pydantic plugin across all projects."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraToml, c, m, t, u


class FlextInfraEnsureMypyConfigPhase:
    """Ensure standard mypy configuration with pydantic plugin across all projects."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        configured = self._tool_config.tools.mypy.overrides
        expected_overrides: Sequence[dict[str, t.Cli.JsonValue]] = [
            {
                "module": u.Cli.normalize_json_value(list(entry.modules)),
                "disable_error_code": u.Cli.normalize_json_value(
                    list(entry.disable_error_codes),
                ),
            }
            for entry in configured
        ]
        phase_builder = (
            m.Infra.TomlPhaseConfig
            .Builder("mypy")
            .table(c.Infra.MYPY)
            .value(c.Infra.PYTHON_VERSION_UNDERSCORE, "3.13")
            .list(
                c.Infra.PLUGINS,
                self._tool_config.tools.mypy.plugins,
                strategy=c.Infra.TomlMerge.REPLACE,
            )
            .list(
                c.Infra.DISABLE_ERROR_CODE,
                self._tool_config.tools.mypy.disabled_error_codes,
                strategy=c.Infra.TomlMerge.REPLACE,
            )
            .value("overrides", list(expected_overrides))
        )
        for key, value in self._tool_config.tools.mypy.boolean_settings.items():
            phase_builder = phase_builder.value(key, value)
        return FlextInfraToml.apply_phases(doc, phase_builder.build())


__all__ = ["FlextInfraEnsureMypyConfigPhase"]
