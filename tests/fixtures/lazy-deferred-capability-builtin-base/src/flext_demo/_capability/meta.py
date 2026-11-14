"""Capability part whose base is a builtin type.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations


class FlextDemoCapabilityMeta(type):
    """A metaclass a stand-in cannot represent."""

    META_VALUE = 4


__all__: list[str] = ["FlextDemoCapabilityMeta"]
