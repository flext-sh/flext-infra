"""Testmon SQLite integrity and saveability contracts."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flext_infra.validate.testmon_db import (
    FlextInfraTestmonCacheState,
    FlextInfraTestmonDbInspector,
    FlextInfraTestmonDbInvalidator,
)
from flext_tests import tm


def _create_testmon_db(db: Path, names: tuple[str, ...]) -> None:
    """Create only the official pytest-testmon tables used by invalidation."""
    connection = sqlite3.connect(db)
    connection.executescript(
        """
        CREATE TABLE test_execution (
            id INTEGER PRIMARY KEY,
            environment_id INTEGER,
            test_name TEXT,
            duration FLOAT,
            failed BIT,
            forced BIT
        );
        CREATE TABLE test_execution_file_fp (
            test_execution_id INTEGER,
            fingerprint_id INTEGER
        );
        """
    )
    for row_id, name in enumerate(names, start=1):
        connection.execute(
            "INSERT INTO test_execution VALUES (?, 1, ?, 0.1, 0, 0)", (row_id, name)
        )
        connection.execute(
            "INSERT INTO test_execution_file_fp VALUES (?, ?)", (row_id, row_id)
        )
    connection.commit()
    connection.close()


def _cached_names(db: Path) -> tuple[str, ...]:
    """Read cached nodeids for postcondition assertions."""
    connection = sqlite3.connect(db)
    names = tuple(
        str(row[0])
        for row in connection.execute(
            "SELECT test_name FROM test_execution ORDER BY id"
        ).fetchall()
    )
    connection.close()
    return names


def _failed_names(db: Path) -> tuple[str, ...]:
    """Read the exact cached cases Testmon will force into the next run."""
    connection = sqlite3.connect(db)
    names = tuple(
        str(row[0])
        for row in connection.execute(
            "SELECT test_name FROM test_execution WHERE failed = 1 ORDER BY test_name"
        ).fetchall()
    )
    connection.close()
    return names


class TestsFlextInfraTestmonDbInvalidator:
    """Prove Testmon invalidation is exact, bounded, and in-place."""

    def test_unfiltered_request_deletes_only_fastest_existing_test(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / ".testmondata"
        fastest = "tests/unit/test_fast.py::test_fast"
        slower = "tests/unit/test_slow.py::test_slow"
        for relative_path in ("tests/unit/test_fast.py", "tests/unit/test_slow.py"):
            path = tmp_path / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        _create_testmon_db(db, (slower, fastest))
        connection = sqlite3.connect(db)
        connection.execute(
            "UPDATE test_execution SET duration = 0.2 WHERE test_name = ?", (slower,)
        )
        connection.execute(
            "UPDATE test_execution SET duration = 0.01 WHERE test_name = ?", (fastest,)
        )
        connection.commit()
        connection.close()

        invalidated = tm.ok(
            FlextInfraTestmonDbInvalidator(
                workspace_root=tmp_path, db_path=db, max_tests=1
            ).execute()
        )

        tm.that(invalidated, eq=(fastest,))
        tm.that(_cached_names(db), eq=(slower, fastest))
        tm.that(_failed_names(db), eq=(fastest,))

    def test_exact_file_deletes_only_matching_rows_without_replacing_db(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / ".testmondata"
        target = "tests/unit/test_target.py::test_exact"
        other = "tests/unit/test_other.py::test_other"
        _create_testmon_db(db, (target, target, other))
        inode = db.stat().st_ino

        invalidated = tm.ok(
            FlextInfraTestmonDbInvalidator(
                workspace_root=tmp_path, db_path=db, file=target, max_tests=3
            ).execute()
        )

        tm.that(invalidated, eq=(target,))
        tm.that(db.stat().st_ino, eq=inode)
        tm.that(_cached_names(db), eq=(other,))
        connection = sqlite3.connect(db)
        linked_rows = connection.execute(
            "SELECT test_execution_id FROM test_execution_file_fp ORDER BY 1"
        ).fetchall()
        connection.close()
        tm.that(linked_rows, eq=[(3,)])

    def test_selector_over_limit_fails_without_mutating_db(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / ".testmondata"
        names = tuple(
            f"tests/unit/test_bounded_{index}.py::test_bounded" for index in range(33)
        )
        _create_testmon_db(db, names)
        digest = FlextInfraTestmonDbInspector.digest_file(db)

        result = FlextInfraTestmonDbInvalidator(
            workspace_root=tmp_path, db_path=db, match="bounded", max_tests=32
        ).execute()

        tm.fail(result, has="exceeds testmon invalidation limit")
        tm.that(FlextInfraTestmonDbInspector.digest_file(db), eq=digest)
        tm.that(_cached_names(db), eq=names)

    def test_zero_cached_matches_is_noop_without_mutating_db(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / ".testmondata"
        names = ("tests/unit/test_other.py::test_other",)
        _create_testmon_db(db, names)
        digest = FlextInfraTestmonDbInspector.digest_file(db)

        invalidated = tm.ok(
            FlextInfraTestmonDbInvalidator(
                workspace_root=tmp_path, db_path=db, match="absent", max_tests=32
            ).execute()
        )

        tm.that(invalidated, eq=())
        tm.that(FlextInfraTestmonDbInspector.digest_file(db), eq=digest)
        tm.that(_cached_names(db), eq=names)


class TestsFlextInfraTestmonDbInspector:
    """Prove WAL checkpoint, integrity, and saveability decisions."""

    def test_missing_db_is_not_saveable(self, tmp_path: Path) -> None:
        state: FlextInfraTestmonCacheState = tm.ok(
            FlextInfraTestmonDbInspector(
                workspace_root=tmp_path,
                db_path=tmp_path / ".testmondata",
                pre_run_digest=None,
                run_succeeded=True,
                mode="test",
            ).execute()
        )
        tm.that(state.seed_needed, eq=True)
        tm.that(state.saveable, eq=False)

    def test_healthy_new_db_is_saveable_seed(self, tmp_path: Path) -> None:
        db = tmp_path / ".testmondata"
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE meta (k TEXT, v TEXT)")
        connection.execute("INSERT INTO meta VALUES ('schema', '1')")
        connection.commit()
        connection.close()
        state: FlextInfraTestmonCacheState = tm.ok(
            FlextInfraTestmonDbInspector(
                workspace_root=tmp_path,
                db_path=db,
                pre_run_digest=None,
                run_succeeded=True,
                mode="test",
            ).execute()
        )
        tm.that(state.seed_needed, eq=True)
        tm.that(state.saveable, eq=True)
        tm.that(state.reason, eq="seed_ready")

    def test_unchanged_db_is_not_saveable(self, tmp_path: Path) -> None:
        db = tmp_path / ".testmondata"
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE meta (k TEXT)")
        connection.commit()
        connection.close()
        digest = FlextInfraTestmonDbInspector.digest_file(db)
        state: FlextInfraTestmonCacheState = tm.ok(
            FlextInfraTestmonDbInspector(
                workspace_root=tmp_path,
                db_path=db,
                pre_run_digest=digest,
                run_succeeded=True,
                mode="test",
            ).execute()
        )
        tm.that(state.changed, eq=False)
        tm.that(state.saveable, eq=False)
        tm.that(state.reason, eq="unchanged")
