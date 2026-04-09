"""Tests for FlextInfraGitService using real git repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraUtilitiesGit
from tests import u


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a real git repository for testing."""
    init_result = u.Cli.run_raw(["git", "init", str(tmp_path)])
    tm.ok(init_result)
    tm.that(init_result.value.exit_code, eq=0)
    email_result = u.Cli.run_raw(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
    )
    tm.ok(email_result)
    tm.that(email_result.value.exit_code, eq=0)
    name_result = u.Cli.run_raw(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
    )
    tm.ok(name_result)
    tm.that(name_result.value.exit_code, eq=0)
    (tmp_path / "README.md").write_text("# Test\n")
    add_result = u.Cli.run_raw(["git", "add", "."], cwd=tmp_path)
    tm.ok(add_result)
    tm.that(add_result.value.exit_code, eq=0)
    commit_result = u.Cli.run_raw(["git", "commit", "-m", "init"], cwd=tmp_path)
    tm.ok(commit_result)
    tm.that(commit_result.value.exit_code, eq=0)
    return tmp_path


class TestFlextInfraGitService:
    """Test suite for FlextInfraGitService with real repos."""

    def test_current_branch_success(self, git_repo: Path) -> None:
        result = FlextInfraUtilitiesGit.git_current_branch(git_repo)
        tm.ok(result, is_=str)

    def test_current_branch_failure(self, tmp_path: Path) -> None:
        result = FlextInfraUtilitiesGit.git_current_branch(tmp_path)
        tm.fail(result)

    def test_tag_exists_true(self, git_repo: Path) -> None:
        tag_result = u.Cli.run_raw(
            ["git", "tag", "-a", "v1.0.0", "-m", "release"],
            cwd=git_repo,
        )
        tm.ok(tag_result)
        tm.that(tag_result.value.exit_code, eq=0)
        result = FlextInfraUtilitiesGit.git_tag_exists(git_repo, "v1.0.0")
        tm.ok(result, eq=True)

    def test_tag_exists_false(self, git_repo: Path) -> None:
        result = FlextInfraUtilitiesGit.git_tag_exists(git_repo, "v9.9.9")
        tm.ok(result, eq=False)

    def test_tag_exists_failure(self, tmp_path: Path) -> None:
        result = FlextInfraUtilitiesGit.git_tag_exists(tmp_path, "v1.0.0")
        tm.fail(result)

    def test_run_arbitrary_command(self, git_repo: Path) -> None:
        result = FlextInfraUtilitiesGit.git_run(["log", "--oneline"], cwd=git_repo)
        tm.ok(result, is_=str)

    def test_run_command_failure(self, tmp_path: Path) -> None:
        result = FlextInfraUtilitiesGit.git_run(["log"], cwd=tmp_path)
        tm.fail(result)


class TestRemovedCompatibilityMethods:
    """Removed compatibility methods are not callable anymore."""

    def test_removed_methods_raise_attribute_error(self) -> None:
        with pytest.raises(AttributeError):
            _ = getattr(FlextInfraUtilitiesGit, "smart_checkout")
        with pytest.raises(AttributeError):
            _ = getattr(FlextInfraUtilitiesGit, "checkpoint")
        with pytest.raises(AttributeError):
            _ = getattr(FlextInfraUtilitiesGit, "create_tag_if_missing")
        with pytest.raises(AttributeError):
            _ = getattr(FlextInfraUtilitiesGit, "collect_changes")


class TestGitTagOperations:
    """Tests for tag listing and creation."""

    def test_create_tag(self, git_repo: Path) -> None:
        result = FlextInfraUtilitiesGit.git_create_tag(git_repo, "v3.0.0")
        tm.ok(result, eq=True)
        verify = FlextInfraUtilitiesGit.git_tag_exists(git_repo, "v3.0.0")
        tm.ok(verify, eq=True)


class TestGitPush:
    """Tests for git push operations."""

    def test_push_to_nonexistent_remote_fails(self, git_repo: Path) -> None:
        result = FlextInfraUtilitiesGit.git_push(
            git_repo,
            remote="origin",
            branch="main",
            upstream=True,
        )
        tm.fail(result)
