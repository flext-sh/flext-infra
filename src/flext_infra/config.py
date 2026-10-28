"""Extracted facade class for config.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra.make_contract import FlextInfraConfigMakeContract


class FlextInfraFlextInfraConfig(
    FlextInfraConfigMakeContract,
):
    """Facade for config."""


__all__: list[str] = ["FlextInfraFlextInfraConfig"]
