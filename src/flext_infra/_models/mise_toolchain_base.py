"""Declarative base for schema-loaded Mise toolchain records.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m


class FlextInfraModelsMiseToolchainBase(m.ContractModel):
    """Immutable coercing preset shared by schema-loaded configuration records."""

    # Rendered payloads are byte contracts; preserve their final newline.
    model_config = m.ConfigDict(
        strict=False,
        frozen=True,
        extra="forbid",
        str_strip_whitespace=False,
    )


__all__: list[str] = ["FlextInfraModelsMiseToolchainBase"]
