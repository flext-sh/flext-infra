"""Phase: Ensure standard pydantic-mypy configuration for strict model typing."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
)

from flext_infra import FlextInfraPhaseEngine, m, t


class FlextInfraEnsurePydanticMypyConfigPhase:
    """Ensure standard pydantic-mypy configuration for strict model typing."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to populate pydantic-mypy settings."""
        self._tool_config = tool_config

    def _phase(self) -> m.Infra.TomlPhaseConfig:
        """Build the canonical pydantic-mypy phase definition."""
        return (
            m.Infra.TomlPhaseConfig
            .Builder("pydantic-mypy")
            .table("pydantic-mypy")
            .value(
                "init_forbid_extra",
                self._tool_config.tools.pydantic_mypy.init_forbid_extra,
            )
            .value("init_typed", self._tool_config.tools.pydantic_mypy.init_typed)
            .value(
                "warn_required_dynamic_aliases",
                self._tool_config.tools.pydantic_mypy.warn_required_dynamic_aliases,
            )
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply canonical ``[tool.pydantic-mypy]`` defaults into TOML document."""
        return FlextInfraPhaseEngine.apply_phases(doc, self._phase())

    def apply_payload(
        self,
        payload: MutableMapping[str, t.JsonValue],
    ) -> t.StrSequence:
        """Apply canonical pydantic-mypy settings to one normalized payload."""
        return FlextInfraPhaseEngine.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsurePydanticMypyConfigPhase"]
