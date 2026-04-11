"""Phase: Ensure standard pydantic-mypy configuration for strict model typing."""

from __future__ import annotations

from flext_infra import FlextInfraToml, m, t


class FlextInfraEnsurePydanticMypyConfigPhase:
    """Ensure standard pydantic-mypy configuration for strict model typing."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to populate pydantic-mypy settings."""
        self._tool_config = tool_config

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply canonical ``[tool.pydantic-mypy]`` defaults into TOML document."""
        phase = (
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
        return FlextInfraToml.apply_phases(doc, phase)


__all__ = ["FlextInfraEnsurePydanticMypyConfigPhase"]
