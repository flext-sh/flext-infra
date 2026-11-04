"""Real formatter effects share one Git-scoped mutation lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flext_infra.gates import FlextInfraGatesRuffFormat
from tests import c, m, tm, u


class TestsFlextInfraMutationLeases:
    """Public formatter behavior respects exact shared writer ownership."""

    @staticmethod
    @c.Tests.MARK.parametrize("git_owned", [False, True])
    def test_mutation_lock_lives_outside_the_worktree(
        tmp_path: Path,
        *,
        git_owned: bool,
    ) -> None:
        """Every writer of one scope shares a lock that never dirties the tree."""
        root = u.Tests.git_repository(tmp_path) if git_owned else tmp_path
        lock = tm.ok(u.Infra.mutation_lock_path(root))
        nested = root / "nested"
        nested.mkdir()
        if git_owned:
            identity = tm.ok(
                u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root))
            )
            tm.that(lock.parent, eq=Path(identity.git_dir).resolve())
            tm.that(tm.ok(u.Infra.mutation_lock_path(nested)), eq=lock)
        else:
            tm.that(lock.parent, eq=root.resolve() / c.Infra.TRANSACTION_STATE_DIRNAME)
        with u.Cli.file_changes_lock(lock):
            tm.that(lock.parent.is_dir(), eq=True)

    @staticmethod
    @c.Tests.MARK.parametrize("git_owned", [False, True])
    def test_format_waits_for_scope_writer_and_does_not_apply_lint(
        tmp_path: Path,
        *,
        git_owned: bool,
    ) -> None:
        """Test format waits for scope writer and does not apply lint."""
        root = u.Tests.git_repository(tmp_path) if git_owned else tmp_path / "files"
        root.mkdir(exist_ok=True)
        (root / c.PYPROJECT_FILENAME).write_text("[tool.ruff]\n", encoding="utf-8")
        source = root / "src"
        source.mkdir()
        target = source / "sample.py"
        before = "import os\n\nvalue=[1,2,3]\n"
        target.write_text(before, encoding="utf-8")
        gate = FlextInfraGatesRuffFormat(root)
        context = m.Infra.GateContext(
            repository_root=root,
            reports_dir=root / "reports",
            apply_fixes=True,
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(root).unwrap()):
                applied = pool.submit(gate.fix, root, context)
                with u.Tests.raises(TimeoutError):
                    applied.result(timeout=0.2)
                tm.that(target.read_text(encoding="utf-8"), eq=before)
            tm.ok(applied.result().result.passed)
        tm.that(target.read_text(encoding="utf-8"), ne=before)
        tm.that(target.read_text(encoding="utf-8"), has="import os")
        tm.ok(gate.check(root, context).result.passed)

    @staticmethod
    def test_held_scope_records_its_holder_and_nests(tmp_path: Path) -> None:
        """The outermost holder records itself; a nested hold keeps that record."""
        root = u.Tests.git_repository(tmp_path)
        lock = tm.ok(u.Infra.mutation_lock_path(root))
        tm.that(u.Infra.mutation_lock_holder(lock), eq=None)
        with u.Infra.hold_mutation_scope(root, "outer") as held:
            tm.that(held, eq=lock)
            holder = u.Infra.mutation_lock_holder(lock)
            tm.that(holder, ne=None)
            tm.that(getattr(holder, "operation", None), eq="outer")
            tm.that(getattr(holder, "root", None), eq=root.resolve())
            tm.that(getattr(holder, "released_at", ""), eq=None)
            with u.Infra.hold_mutation_scope(root, "inner"):
                tm.that(u.Infra.mutation_lock_holder(lock), eq=holder)
            tm.that(u.Infra.mutation_lock_holder(lock), eq=holder)
        closed = u.Infra.mutation_lock_holder(lock)
        tm.that(getattr(closed, "operation", None), eq="outer")
        tm.that(getattr(closed, "released_at", None), ne=None)

    @staticmethod
    def test_failed_holder_closes_its_record_and_keeps_the_failure(
        tmp_path: Path,
    ) -> None:
        """A failing operation re-raises its own error and still closes the record."""
        root = u.Tests.git_repository(tmp_path)
        lock = tm.ok(u.Infra.mutation_lock_path(root))
        with (
            u.Tests.raises(m.ValidationError),
            u.Infra.hold_mutation_scope(root, "failing"),
        ):
            # A real validation failure inside the held operation.
            m.Infra.MutationLockHolder.model_validate({})
        closed = u.Infra.mutation_lock_holder(lock)
        tm.that(getattr(closed, "operation", None), eq="failing")
        tm.that(getattr(closed, "released_at", None), ne=None)

    @staticmethod
    def test_concurrent_writer_waits_for_held_scope(tmp_path: Path) -> None:
        """A second writer waits for the holder instead of failing at once."""
        root = u.Tests.git_repository(tmp_path)
        lock = tm.ok(u.Infra.mutation_lock_path(root))

        def second_writer() -> str:
            with u.Infra.hold_mutation_scope(root, "second"):
                return getattr(u.Infra.mutation_lock_holder(lock), "operation", "")

        with ThreadPoolExecutor(max_workers=1) as pool:
            with u.Infra.hold_mutation_scope(root, "first"):
                waiting = pool.submit(second_writer)
                with u.Tests.raises(TimeoutError):
                    waiting.result(timeout=0.2)
                observed = u.Infra.mutation_lock_holder(lock)
                tm.that(getattr(observed, "operation", None), eq="first")
            tm.that(waiting.result(), eq="second")

    @staticmethod
    def test_malformed_git_marker_is_not_a_file_scope(tmp_path: Path) -> None:
        """Test malformed git marker is not a file scope."""
        marker = tmp_path / c.Infra.GIT_DIR
        marker.mkdir()
        request = m.Infra.GitRepoRequest(repo_root=tmp_path)

        tm.ok(u.Infra.git_mutation_scope(request).failure)
        tm.fail((tmp_path / c.Infra.TRANSACTION_STATE_DIRNAME).exists())

    @staticmethod
    def test_nested_git_scope_uses_original_worktree_git_dir(
        tmp_path: Path,
    ) -> None:
        """Test nested git scope uses original worktree git dir."""
        root = u.Tests.git_repository(tmp_path)
        nested = root / "nested"
        nested.mkdir()
        scope = tm.ok(
            u.Infra.git_mutation_scope(m.Infra.GitRepoRequest(repo_root=nested)),
        )
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))

        tm.that(scope.git_dir, eq=identity.git_dir)
        tm.that(scope.root, eq=nested.resolve())


__all__: list[str] = ["TestsFlextInfraMutationLeases"]
