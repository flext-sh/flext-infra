"""Centralized constants for the release subpackage."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Final


class FlextInfraConstantsRelease:
    """Release infrastructure constants."""

    RELEASE_PHASE_ALL: Final[str] = "all"

    class ReleasePhase(StrEnum):
        """Canonical release phases for workspace orchestration."""

        VALIDATE = "validate"
        VERSION = "version"
        BUILD = "build"
        PUBLISH = "publish"

    class VersionBump(StrEnum):
        """Canonical semantic-version bump kinds."""

        MAJOR = "major"
        MINOR = "minor"
        PATCH = "patch"

    VALID_PHASES: Final[frozenset[ReleasePhase]] = frozenset({
        ReleasePhase.VALIDATE,
        ReleasePhase.VERSION,
        ReleasePhase.BUILD,
        ReleasePhase.PUBLISH,
    })
    VALID_BUMP_TYPES: Final[frozenset[VersionBump]] = frozenset({
        VersionBump.MAJOR,
        VersionBump.MINOR,
        VersionBump.PATCH,
    })
    VERSION_RE: Final[re.Pattern[str]] = re.compile(
        r"^version\s*=\s*['\"](.+?)['\"]",
        re.MULTILINE,
    )


__all__: list[str] = ["FlextInfraConstantsRelease"]
