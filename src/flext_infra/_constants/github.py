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

    GH: Final[str] = "gh"
    ACTIONLINT: Final[str] = "actionlint"
    ACTIONLINT_JSON_FORMAT: Final[str] = "{{json .}}"
    GITHUB_WORKFLOWS_DIR: Final[str] = ".github/workflows"
    GITHUB_WORKFLOW_GLOBS: Final[tuple[str, str]] = ("*.yml", "*.yaml")
    PULL_REQUEST_JSON_FIELDS: Final[str] = (
        "number,title,state,baseRefName,headRefName,url,isDraft"
    )


__all__: list[str] = ["FlextInfraConstantsGithub"]
