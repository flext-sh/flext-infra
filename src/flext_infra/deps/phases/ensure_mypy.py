"""Phase: Ensure standard mypy configuration with pydantic plugin across all projects."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    Sequence,
)

from flext_infra import FlextInfraPhaseEngine, c, m, t, u


class FlextInfraEnsureMypyConfigPhase:
    """Ensure standard mypy configuration with pydantic plugin across all projects."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to generate the canonical mypy section."""
        self._tool_config = tool_config

    def _phase(self) -> m.Infra.TomlPhaseConfig:
        """Build the canonical mypy phase definition."""
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
                strategy=c.Infra.TOML_MERGE_REPLACE,
            )
            .list(
                c.Infra.DISABLE_ERROR_CODE,
                self._tool_config.tools.mypy.disabled_error_codes,
                strategy=c.Infra.TOML_MERGE_REPLACE,
            )
        )
        if self._tool_config.tools.mypy.exclude:
            phase_builder = phase_builder.value(
                c.Infra.EXCLUDE,
                self._tool_config.tools.mypy.exclude,
            )
        else:
            phase_builder = phase_builder.deprecated(c.Infra.EXCLUDE)
        phase_builder = phase_builder.value("overrides", list(expected_overrides))
        for key, value in self._tool_config.tools.mypy.boolean_settings.items():
            phase_builder = phase_builder.value(key, value)
        return phase_builder.build()

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply mypy defaults, overrides, and toggles from tool configuration."""
        return FlextInfraPhaseEngine.apply_phases(doc, self._phase())

    def apply_payload(
        self,
        payload: MutableMapping[str, t.Cli.JsonValue],
    ) -> t.StrSequence:
        """Apply canonical mypy settings directly to one normalized payload."""
        return FlextInfraPhaseEngine.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsureMypyConfigPhase"]
