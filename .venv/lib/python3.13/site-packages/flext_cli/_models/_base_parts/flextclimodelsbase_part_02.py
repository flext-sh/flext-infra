"""CLI Pydantic domain models."""

from __future__ import annotations

from types import MappingProxyType
from typing import Annotated, ClassVar

from flext_cli import c, t
from flext_core import m, u


class FlextCliModelsBase:
    """Implementation part for FlextCliModelsBase."""

    class PromptRuntimeState(m.FlexibleInternalModel):
        """Centralized runtime state for CLI prompt behavior."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid", validate_assignment=True
        )

        interactive: Annotated[
            bool, m.Field(True, description="Whether prompt interaction is enabled")
        ] = True
        quiet: Annotated[
            bool, m.Field(False, description="Whether prompt output is suppressed")
        ] = False
        default_timeout: Annotated[
            int, m.Field(description="Default prompt timeout in seconds")
        ] = c.Cli.PROMPT_DEFAULT_TIMEOUT

    class AuthCredentialsPayload(m.BaseModel):
        """Validated auth payload for token or username/password flows."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid", validate_assignment=True
        )
        token: Annotated[
            str | None,
            m.Field(None, description="Direct authentication token", strict=True),
        ] = None
        username: Annotated[
            str, m.Field("", description="Authentication username", strict=True)
        ] = ""
        password: Annotated[
            str, m.Field("", description="Authentication password", strict=True)
        ] = ""

    class ProcessEnvironmentSpec(m.BaseModel):
        """Validated process environment contract for runtime command execution."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)
        base_env: Annotated[
            t.StrMapping,
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description="Base environment inherited from the current process",
            ),
        ]
        overrides: Annotated[
            t.StrMapping,
            m.Field(
                default_factory=lambda: MappingProxyType({}),
                description="Explicit environment overrides for the child process",
            ),
        ]
        remove_keys: Annotated[
            t.StrSequence,
            m.Field(
                default_factory=tuple,
                description="Environment keys removed before applying overrides",
            ),
        ]

        @u.computed_field()
        @property
        def resolved(self) -> dict[str, str]:
            """Resolved environment mapping after removals and overrides."""
            return self.resolve()

        def resolve(self) -> dict[str, str]:
            """Type-safe accessor for the computed environment mapping."""
            remove_keys = frozenset(self.remove_keys)
            resolved = {
                key: value
                for key, value in self.base_env.items()
                if key not in remove_keys
            }
            resolved.update(dict(self.overrides))
            return resolved


__all__: list[str] = ["FlextCliModelsBase"]
