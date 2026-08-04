"""Testmon SQLite integrity and saveability contracts."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flext_infra.validate.testmon_db import (
    FlextInfraTestmonCacheState,
    FlextInfraTestmonDbInspector,
)
from flext_tests import tm


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
