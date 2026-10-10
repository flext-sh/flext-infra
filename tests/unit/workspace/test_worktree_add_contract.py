"""Private worktree ADD owner behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraWorktreeService
from tests import c, u


class TestsFlextInfraWorktreeAddContract(u.Tests.WorktreeFixture):
    """Group cohesive worktree behavior."""

    @pytest.mark.parametrize(
        ("case", "filename", "content", "committed"),
        [
            (
                "clean-setup-failure",
                "Makefile",
                (
                    ".PHONY: setup\nsetup:\n"
                    "\t@printf 'visible setup progress\\n'\n\t@exit 17\n"
                ),
                True,
            ),
            (
                "dirty-setup-failure",
                "Makefile",
                (
                    ".PHONY: setup\nsetup:\n"
                    "\t@printf 'preserve me\\n' > setup-wip.txt\n\t@exit 19\n"
                ),
                True,
            ),
            (
                "invalid-metadata",
                "pyproject.toml",
                (
                    '[project]\nname = "fixture"\nversion = "0.1.0"\n'
                    'description = ["not", "a", "string"]\n'
                ),
                True,
            ),
            (
                "dirty-primary-metadata",
                "pyproject.toml",
                '[dependency-groups]\ndescription = "dirty primary WIP"\n',
                False,
            ),
        ],
    )
    def test_add_is_refused_before_any_lane_setup_or_metadata_effect(
        self,
        tmp_path: Path,
        *,
        case: str,
        filename: str,
        content: str,
        committed: bool,
    ) -> None:
        """Lane admission refuses ADD before checkout, metadata reads, or setup.

        ``git_verify_lane`` refuses every ``create`` request until authoritative
        Beads ownership reaches the native admission contract (bead
        flext-itpd1.3.26), and ``_add`` runs that admission before it resolves
        the base, reserves the path, reads lane metadata, or could run setup.
        Whatever the primary checkout holds — a failing or dirtying setup
        recipe, invalid committed PEP 621 metadata, or uncommitted metadata
        WIP — no lane, branch, setup artifact, or primary rewrite results.
        """
        repository = self._repository(tmp_path)
        (repository / filename).write_text(content, encoding="utf-8")
        if committed:
            self._commit_fixture(repository, f"test: {case}")

        _ = self.refused_lane(repository, f"feature/{case}")

        tm.that((repository / filename).read_text(encoding="utf-8"), eq=content)
        tm.that((repository / "setup-wip.txt").exists(), eq=False)

    def test_mutation_without_apply_fails_closed(self, tmp_path: Path) -> None:
        """A branch alone never authorizes repository mutation."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/no-apply",
            base="HEAD",
        ).execute()

        tm.fail(result, has="requires --apply")

    def test_add_without_base_fails_loud(self, tmp_path: Path) -> None:
        """A mutating caller must explicitly select its integration base."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/no-base",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="requires --base")
