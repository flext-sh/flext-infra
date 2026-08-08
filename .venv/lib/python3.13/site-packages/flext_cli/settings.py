"""FLEXT CLI Configuration Module.

CLI-specific settings extending FlextSettings. All Pydantic v2; no compatibility layers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from flext_cli import c
from flext_core import FlextSettings, m, u

if TYPE_CHECKING:
    from flext_cli import p


class FlextCliSettings(FlextSettings):
    """CLI-specific configuration; extends FlextSettings with profile and CLI fields."""

    model_config = m.SettingsConfigDict(env_prefix="FLEXT_CLI_", extra="ignore")

    class CliSettings(m.SettingsValue):
        """Namespaced CLI runtime settings."""

        verbose: Annotated[bool, m.Field(description="Verbose output")] = (
            c.Cli.CLI_DEFAULT_VERBOSE
        )
        quiet: Annotated[bool, m.Field(description="Quiet output")] = (
            c.Cli.CLI_DEFAULT_QUIET
        )
        app_name: Annotated[str, m.Field(description="CLI application name")] = (
            c.Cli.FLEXT_CLI
        )
        log_verbosity: Annotated[
            str, m.Field(description="Log format (compact, detailed, full)")
        ] = c.Cli.LogVerbosity.COMPACT
        cli_log_level: Annotated[
            c.LogLevel | str, m.Field(description="CLI log level")
        ] = c.LogLevel.INFO
        no_color: Annotated[bool, m.Field(description="Disable colored output")] = (
            c.Cli.CLI_DEFAULT_NO_COLOR
        )
        output_format: Annotated[
            str, m.Field(description="Output format (table, json, yaml, csv, plain)")
        ] = c.Cli.OUTPUT_DEFAULT_FORMAT_TYPE
        config_file: Annotated[
            str | None, m.Field(description="Path to settings file")
        ] = None
        token_file: Annotated[
            str | None, m.Field(description="Path to auth token file")
        ] = None
        ci: Annotated[
            bool,
            m.Field(description="Whether the current runtime is a CI environment."),
        ] = c.Cli.ENV_DEFAULT_CI
        pytest_current_test: Annotated[
            str | None, m.Field(description="Current pytest test identifier.")
        ] = None
        shell_command: Annotated[
            str | None,
            m.Field(description="Current shell command propagated by the runtime."),
        ] = None

        @u.computed_field()
        @property
        def test_env(self) -> bool:
            """Whether prompts should treat the current runtime as test/CI mode."""
            normalized_shell = (self.shell_command or "").strip().lower()
            return (
                self.pytest_current_test is not None
                or "pytest" in normalized_shell
                or self.ci
            )

    if TYPE_CHECKING:
        Cli: p.Cli.CliSettings
    else:
        Cli: CliSettings = m.Field(
            default_factory=CliSettings, description="Namespaced CLI settings branch."
        )
