"""Extracted facade class for config.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._config import FlextInfraConfigMakeContract


class FlextInfraFlextInfraConfig(
    FlextInfraConfigMakeContract,
):
    """Facade for config."""


__all__: list[str] = ["FlextInfraFlextInfraConfig"]
