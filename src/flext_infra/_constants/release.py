"""Centralized constants for the release subpackage."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsRelease:
    """Release infrastructure constants."""

    RELEASE_PHASE_ALL: Final[str] = "all"
    VERSION_RELEASE_SEGMENTS: Final[int] = 3

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
    VERSION_RE: Final[t.RegexPattern] = re.compile(
        r"^version\s*=\s*['\"](.+?)['\"]", re.MULTILINE
    )


__all__: list[str] = ["FlextInfraConstantsRelease"]
