"""Git-specific fixtures for FLEXT infra tests.

Provides fixtures for creating real git repositories with commits.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import u


@pytest.fixture
def real_git_repo(tmp_path: Path) -> Path:
    """Create a real git repository with initial commit.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to git repository root

    """
    repo_root = tmp_path / "git_repo"
    repo_root.mkdir()

    # Initialize git repo
    init_result = u.Cli.run_raw(["git", "init"], cwd=repo_root)
    assert init_result.success
    assert init_result.value.exit_code == 0

    # Configure git user for commits
    email_result = u.Cli.run_raw(
        ["git", "settings", "user.email", "test@example.com"],
        cwd=repo_root,
    )
    assert email_result.success
    assert email_result.value.exit_code == 0
    name_result = u.Cli.run_raw(
        ["git", "settings", "user.name", "Test User"],
        cwd=repo_root,
    )
    assert name_result.success
    assert name_result.value.exit_code == 0

    # Create initial file and commit
    (repo_root / "README.md").write_text("# Test Repository\n")
    add_result = u.Cli.run_raw(["git", "add", "README.md"], cwd=repo_root)
    assert add_result.success
    assert add_result.value.exit_code == 0
    commit_result = u.Cli.run_raw(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_root,
    )
    assert commit_result.success
    assert commit_result.value.exit_code == 0

    return repo_root


__all__ = ["real_git_repo"]
