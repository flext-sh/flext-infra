"""Shared utilities for documentation services.

All methods moved to u.Infra MRO chain via FlextInfraUtilitiesDocs.
This module is kept for backwards compatibility of the class name.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import FlextInfraUtilitiesDocs


class FlextInfraDocsShared(FlextInfraUtilitiesDocs):
    """Backwards-compatible alias — use u.Infra.* instead."""


__all__ = ["FlextInfraDocsShared"]
