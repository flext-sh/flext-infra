"""Centralized constants for the github subpackage."""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final


class FlextInfraConstantsGithub:
    """Github infrastructure constants."""

    @unique
    class PullRequestAction(StrEnum):
        """Supported pull-request publication actions."""

        CREATE = "create"
        STATUS = "status"

    @unique
    class WorkflowLintStatus(StrEnum):
        """GitHub workflow lint status enumeration (single source of truth).

        DRY Pattern:
            StrEnum is the single source of truth. Use WorkflowLintStatus.OK.value
            or WorkflowLintStatus.OK directly - no base strings needed.

        Represents all possible outcomes of GitHub workflow linting operations.
        """

        OK = "ok"
        SKIPPED = "skipped"
        FAIL = "fail"

    GH: Final[str] = "gh"
    PULL_REQUEST_JSON_FIELDS: Final[str] = (
        "number,title,state,baseRefName,headRefName,url,isDraft"
    )
    MANAGED_FILES: Final[frozenset[str]] = frozenset({"ci.yml"})


__all__: list[str] = ["FlextInfraConstantsGithub"]
