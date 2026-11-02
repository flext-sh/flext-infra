# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/settings
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_cli import c, t


class FlextInfraProtocolsSettings:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class InfraSettings(Protocol):
        """Structural data contract projected from the owning model."""

        standalone: bool
        repository_root: Path | None
        github_actions: (
            Literal[c.ParserBooleanToken.TRUE, c.ParserBooleanToken.FALSE] | None
        )
        profile: bool
        profile_output: Path | None
        profile_children: bool
        use_https: bool
        github_head_ref: str | None
        github_ref_name: str | None
        uv_executable: str | None
        toolchain_repair_tool: t.NonEmptyStr | None
        runtime_root: Path | None
        virtual_env: str | None
        dispatch_what: str | None
        flext_command_dispatched: str | None
        flext_command_path: str | None
        system_path: str | None
        sonar_token: t.SecretStr | None


__all__: list[str] = [
    "FlextInfraProtocolsSettings",
]
