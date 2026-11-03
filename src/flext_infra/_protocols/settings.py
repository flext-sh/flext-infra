# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/settings
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import c, t


class FlextInfraProtocolsSettings:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class InfraSettings(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def standalone(self) -> bool:
            """Force standalone mode and skip workspace auto-detection."""
            ...

        @property
        def repository_root(self) -> Path | None:
            """Explicit repository root for dependency orchestration."""
            ...

        @property
        def github_actions(
            self,
        ) -> Literal[c.ParserBooleanToken.TRUE, c.ParserBooleanToken.FALSE] | None:
            """Actual hosted-runner signal used before host-path election."""
            ...

        @property
        def profile(self) -> bool:
            """Structural member projected from the owning model.

            Measure generation, modification, captured checks and tests through the
            shared profilers without changing operation, status or deadline.
            """
            ...

        @property
        def profile_output(self) -> Path | None:
            """Structural member projected from the owning model.

            Destination of the CLI command profile; the invoking verb declares it
            (required when profiling is enabled).
            """
            ...

        @property
        def profile_children(self) -> bool:
            """Structural member projected from the owning model.

            Profile child consumers independently of parent profiling, using the
            invoking verb's declared profile destination.
            """
            ...

        @property
        def use_https(self) -> bool:
            """Prefer HTTPS repository URLs during dependency sync."""
            ...

        @property
        def github_head_ref(self) -> str | None:
            """GitHub Actions head ref for dependency sync."""
            ...

        @property
        def github_ref_name(self) -> str | None:
            """GitHub Actions ref name for dependency sync."""
            ...

        @property
        def uv_executable(self) -> str | None:
            """Uv launcher path resolved for dependency orchestration."""
            ...

        @property
        def toolchain_repair_tool(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Explicit declared tool selected by fix-toolchain; unset refuses
            installation repair before effects.
            """
            ...

        @property
        def runtime_root(self) -> Path | None:
            """Structural member projected from the owning model.

            Declared runtime root whose environment executes the target checkout's
            code; the generated Makefile exports its RUNTIME_ROOT. Undeclared, the
            owner derives the checkout's Git root.
            """
            ...

        @property
        def virtual_env(self) -> str | None:
            """Active virtualenv root for promoted Python commands."""
            ...

        @property
        def dispatch_what(self) -> str | None:
            """Make-dispatch WHAT verb for promoted commands."""
            ...

        @property
        def flext_command_dispatched(self) -> str | None:
            """Dispatcher marker exported to a promoted command."""
            ...

        @property
        def flext_command_path(self) -> str | None:
            """Resolved path of the promoted command being dispatched."""
            ...

        @property
        def system_path(self) -> str | None:
            """Process PATH captured for isolated subprocess builds."""
            ...

        @property
        def sonar_token(self) -> t.SecretStr | None:
            """Structural member projected from the owning model.

            SonarCloud web API token; required only by the explicit sonarcloud-sync
            verb, never read from any other source.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsSettings",
]
