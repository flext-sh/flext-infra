"""Pure Pydantic settings declarations for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from flext_cli import c, m, t


class FlextInfraModelsSettings:
    """Private namespace for validated settings payloads."""

    class InfraSettings(m.BaseSettings):
        """Validated process-start settings owned by flext-infra."""

        # Validate every external alias before singleton export.
        model_config = m.SettingsConfigDict(
            env_prefix="",
            env_ignore_empty=True,
            enable_decoding=False,
            case_sensitive=True,
            populate_by_name=True,
            frozen=True,
            extra="forbid",
        )

        standalone: bool = m.Field(
            default=False,
            validation_alias="FLEXT_STANDALONE",
            description="Force standalone mode and skip workspace auto-detection.",
        )
        repository_root: Path | None = m.Field(
            default=None,
            validation_alias="FLEXT_REPOSITORY_ROOT",
            description="Explicit repository root for dependency orchestration.",
        )
        github_actions: (
            Literal[c.ParserBooleanToken.TRUE, c.ParserBooleanToken.FALSE] | None
        ) = m.Field(
            default=None,
            validation_alias="GITHUB_ACTIONS",
            description="Actual hosted-runner signal used before host-path election.",
        )
        upgrade_packages: Annotated[tuple[t.NonEmptyStr, ...], m.ForceDecode] = m.Field(
            default=(),
            validation_alias="FLEXT_INFRA_UPGRADE_PACKAGES",
            description="Explicit Python package upgrade scope; empty upgrades all.",
        )
        profile: bool = m.Field(
            default=False,
            validation_alias="FLEXT_INFRA_PROFILE",
            description=(
                "Measure generation, modification, captured checks and tests through "
                "the shared profilers without changing operation, status or deadline."
            ),
        )
        profile_output: Path | None = m.Field(
            default=None,
            validation_alias="FLEXT_INFRA_PROFILE_OUTPUT",
            description=(
                "Destination of the CLI command profile; the invoking verb declares "
                "it (required when profiling is enabled)."
            ),
        )

        use_https: bool = m.Field(
            default=False,
            validation_alias="FLEXT_USE_HTTPS",
            description="Prefer HTTPS repository URLs during dependency sync.",
        )
        github_head_ref: str | None = m.Field(
            default=None,
            validation_alias="GITHUB_HEAD_REF",
            description="GitHub Actions head ref for dependency sync.",
        )
        github_ref_name: str | None = m.Field(
            default=None,
            validation_alias="GITHUB_REF_NAME",
            description="GitHub Actions ref name for dependency sync.",
        )
        uv_executable: str | None = m.Field(
            default=None,
            validation_alias="UV",
            description="uv launcher path resolved for dependency orchestration.",
        )
        toolchain_repair_tool: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                validation_alias="FLEXT_INFRA_TOOLCHAIN_REPAIR_TOOL",
                description=(
                    "Explicit declared tool selected by fix-toolchain; unset "
                    "refuses installation repair before effects."
                ),
            ),
        ] = None
        runtime_root: Path | None = m.Field(
            default=None,
            validation_alias="RUNTIME_ROOT",
            description=(
                "Declared runtime root whose environment executes the target "
                "checkout's code; the generated Makefile exports its "
                "RUNTIME_ROOT. Undeclared, the owner derives the checkout's "
                "Git root."
            ),
        )
        virtual_env: str | None = m.Field(
            default=None,
            validation_alias="VIRTUAL_ENV",
            description="Active virtualenv root for promoted Python commands.",
        )
        dispatch_what: str | None = m.Field(
            default=None,
            validation_alias="WHAT",
            description="Make-dispatch WHAT verb for promoted commands.",
        )
        flext_command_dispatched: str | None = m.Field(
            default=None,
            validation_alias="FLEXT_COMMAND_DISPATCHED",
            description="Dispatcher marker exported to a promoted command.",
        )
        flext_command_path: str | None = m.Field(
            default=None,
            validation_alias="FLEXT_COMMAND_PATH",
            description="Resolved path of the promoted command being dispatched.",
        )
        system_path: str | None = m.Field(
            default=None,
            validation_alias="PATH",
            description="Process PATH captured for isolated subprocess builds.",
        )
        sonar_token: t.SecretStr | None = m.Field(
            default=None,
            validation_alias="SONAR_TOKEN",
            description=(
                "SonarCloud web API token; required only by the explicit "
                "sonarcloud-sync verb, never read from any other source."
            ),
        )


__all__: list[str] = ["FlextInfraModelsSettings"]
