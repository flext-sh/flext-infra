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
    MANAGED_GIT_TOOL_ARTIFACT_PLACEHOLDER: Final[str] = "{artifact}"
    MANAGED_GIT_TOOL_OUTPUT_PLACEHOLDER: Final[str] = "{output}"
    MANAGED_GIT_TOOL_SOURCE_PLACEHOLDER: Final[str] = "{source}"
    MANAGED_GIT_TOOL_RECEIPT_FILENAME: Final[str] = "receipt.json"
    MANAGED_GIT_TOOL_SOURCE_ARCHIVE_FILENAME: Final[str] = "source.tar"
    MANAGED_GIT_TOOL_ALLOWED_URL_SCHEME: Final[str] = "https"
    MANAGED_GIT_TOOL_GIT_ENV_KEYS: Final[t.StrSequence] = (
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    )
    MANAGED_GIT_TOOL_RESERVED_BUILD_ENV_KEYS: Final[frozenset[str]] = frozenset({
        "SOURCE_DATE_EPOCH"
    })

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
