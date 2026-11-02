# Copyright (c) 2026 FLEXT Team. All rights reserved.
# SPDX-License-Identifier: MIT
"""Structural contracts mirrored from ``_models._config.workspace``.

This bootstrap contract lets the protocol projector construct the workspace
before it can publish the remaining model-module projections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra._constants.config import FlextInfraConstantsConfig


class FlextInfraProtocolsConfigWorkspace:
    """Runtime-checkable contracts declared by the workspace model module."""

    @runtime_checkable
    class GitSubmoduleDeclaration(Protocol):
        """One declared Git submodule section."""

        @property
        def path(self) -> Path:
            """Path relative to the superproject root."""
            ...

        @property
        def url(self) -> str:
            """Declared upstream URL."""
            ...

        @property
        def branch(self) -> str:
            """Declared branch, when present."""
            ...

        @property
        def managed(self) -> bool | None:
            """Native participation flag."""
            ...

        @property
        def layer(self) -> FlextInfraConstantsConfig.MemberArchitectureLayer | None:
            """Optional architecture layer."""
            ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsConfigWorkspace",)
