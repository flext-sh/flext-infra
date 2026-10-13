"""The committed uv.lock carries every distribution it references.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from flext_infra.workspace import FlextInfraWorkspaceLockCompleteness
from tests import tm


class TestsFlextInfraWorkspaceLockCompleteness:
    """An interrupted resolution must never pass as a complete lock."""

    @staticmethod
    def _write_lock(repository_root: Path, text: str) -> Path:
        lock = repository_root / "uv.lock"
        lock.write_text(dedent(text), encoding="utf-8")
        return lock

    def test_a_complete_lock_passes_with_the_entry_count(self, tmp_path: Path) -> None:
        """Every referenced distribution resolved into a [[package]] block."""
        lock = self._write_lock(
            tmp_path,
            """\
            [[package]]
            name = "cosmos-main"
            version = "0.4.0"

            [package.metadata]
            requires-dist = [
                { name = "flext-core" },
                { name = "pytest-markdown-docs" },
            ]

            [[package]]
            name = "flext-core"
            version = "0.12.0"

            [[package]]
            name = "pytest-markdown-docs"
            version = "1.2.3"
            """,
        )
        tm.that(
            tm.ok(FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock)),
            eq=3,
        )

    def test_a_partial_lock_fails_loud_with_the_missing_names(
        self, tmp_path: Path
    ) -> None:
        """Requires-dist entries without a package block fail with remediation."""
        lock = self._write_lock(
            tmp_path,
            """\
            [[package]]
            name = "cosmos-main"
            version = "0.4.0"

            [package.metadata]
            requires-dist = [
                { name = "flext-core" },
                { name = "pytest-markdown-docs" },
                { name = "ruff" },
            ]

            [[package]]
            name = "flext-core"
            version = "0.12.0"
            """,
        )
        tm.fail(
            FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock),
            has="pytest-markdown-docs",
        )
        tm.fail(
            FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock),
            has="run make upg",
        )

    def test_an_invalid_lock_fails_loud(self, tmp_path: Path) -> None:
        """A lock that is not TOML never passes as complete."""
        lock = self._write_lock(tmp_path, "not [valid toml {{{")
        tm.fail(FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock))

    def test_a_missing_lock_fails_loud(self, tmp_path: Path) -> None:
        """No committed lock is a loud absence, never an empty pass."""
        tm.fail(
            FlextInfraWorkspaceLockCompleteness.validate_lock_file(
                tmp_path / "uv.lock",
            ),
        )

    def test_the_infra_checkout_lock_is_complete(self) -> None:
        """The repository's own committed lock always passes its own gate."""
        lock = Path(__file__).parents[3] / "uv.lock"
        if not lock.is_file():
            pytest.skip("checkout carries no committed uv.lock")
        tm.ok(FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock))
