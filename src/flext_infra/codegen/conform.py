"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_infra import m
from flext_infra.codegen._conform import FlextInfraCodegenConformExecute


class FlextInfraCodegenConform(FlextInfraCodegenConformExecute):
    """Plan every selected output, then atomically write only a clean plan."""

    # This is the only
    # orchestrator for Make/toolchain/source conformance. Rendering stays in
    # flext-cli; Git-source TOML policy and attached detection are composed from
    # their separately owned u.Infra/workspace services.
    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated scaffold specification included in the atomic plan",
        ),
    ] = None
    scaffolded_repository: Annotated[
        bool,
        m.Field(
            default=False,
            exclude=True,
            description="Whether this invocation initialized an unpublished Git root",
        ),
    ] = False


__all__: list[str] = ["FlextInfraCodegenConform"]
