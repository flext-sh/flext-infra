"""Release notes and changelog helpers.

All methods moved to u.Infra MRO chain via FlextInfraUtilitiesRelease.
This module is kept for backwards compatibility of the class name.
"""

from __future__ import annotations

from flext_infra._utilities.release import FlextInfraUtilitiesRelease


class FlextInfraReleaseReporting(FlextInfraUtilitiesRelease):
    """Backwards-compatible alias — use u.Infra.* instead."""


__all__ = ["FlextInfraReleaseReporting"]
