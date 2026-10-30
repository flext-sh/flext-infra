"""Docs scope helpers for FLEXT-only discovery and project classification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScopeProjects


class FlextInfraUtilitiesDocsScope(FlextInfraUtilitiesDocsScopeProjects):
    """Utility helpers for docs scope policy and project classification."""


__all__: list[str] = ["FlextInfraUtilitiesDocsScope"]
