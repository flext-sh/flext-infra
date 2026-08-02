"""Centralized constants for the workspace subpackage."""

from __future__ import annotations

from enum import StrEnum, unique
from typing import TYPE_CHECKING, Final


if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsWorkspace:
    """Workspace infrastructure constants."""

    @unique
    class WorktreeOperation(StrEnum):
        """Supported repository-local development-lane operations."""

        LIST = "list"
        ADD = "add"
        UPDATE = "update"
        REMOVE = "remove"

    @unique
    class WorkspaceMode(StrEnum):
        """Workspace execution mode enumeration."""

        WORKSPACE = "workspace"
        WORKSPACE_MEMBER = "workspace-member"
        STANDALONE = "standalone"

    @unique
    class WorkspaceProjectRole(StrEnum):
        """Role of one discovered project relative to the uv workspace root."""

        WORKSPACE_MEMBER = "member"
        ATTACHED = "attached"

    EXTERNAL_WORKSPACE_SIBLING_PATTERNS: Final[t.StrSequence] = (
        ".ai-hub",
        "algar-*",
        "gruponos-*",
    )
    "Sibling directory patterns for FLEXT-managed external workspaces."

    PERSISTENT_STATE_ARTIFACT_NAMES: Final[frozenset[str]] = frozenset({
        ".beads",
        ".code-review-graph",
        ".codegraph",
        ".serena",
    })
    "Persistent-state artifact basenames owned only by the workspace root."

    # NOTE (mro-jnm1.2): the .gitignore body is derived from the artifact SSOT
    # (config/codegen.yaml artifacts -> CodegenConfigSpec.gitignore_sections)
    # and written only by codegen conform; the old REQUIRED_GITIGNORE_ENTRIES,
    # GITIGNORE_REMOVE_EXACT and GITIGNORE_MANAGED_HEADER append-paths were
    # removed with the migrator/sync parallel writers.
    WORKTREES_DIRNAME: Final[str] = ".worktrees"
    WORKTREE_NAMESPACE_DIGEST_LENGTH: Final[int] = 12
    VSCODE_DIRNAME: Final[str] = ".vscode"
    VSCODE_SETTINGS_FILENAME: Final[str] = "settings.json"
    VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY: Final[str] = "python-envs.workspaceSearchPaths"
    # Canonical VS Code settings content lives in config/codegen.yaml (vscode:).
    # Recursive "**" venv search globs are forbidden: they make the Python
    # Environments locator (pet) walk entire trees and hang discovery.
    # Tools that must never appear under mise: linters/type-checkers come from
    # the locked pyproject dependency groups into .venv (gates invoke them via
    # python -m), and go is not a workspace runtime. Sync prunes any drift.
    WORKSPACE_MISE_REMOVED_TOOLS: Final[t.StrSequence] = (
        "mypy",
        "pyright",
        "pyrefly",
        "ruff",
        "go",
    )


__all__: list[str] = ["FlextInfraConstantsWorkspace"]
