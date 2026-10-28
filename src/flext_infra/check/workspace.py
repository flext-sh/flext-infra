"""Extracted facade class for workspace.

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

from flext_infra.check._workspace import FlextInfraCheckWorkspaceCheckReports


class FlextInfraCheckWorkspace(
    FlextInfraCheckWorkspaceCheckReports,
):
    """Facade for workspace."""


__all__: list[str] = ["FlextInfraCheckWorkspace"]
