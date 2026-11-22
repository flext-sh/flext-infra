"""Testmon SQLite integrity contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flext_infra import config
from flext_infra.validate import FlextInfraTestmonDbInspector
from tests import p, tm, u


class TestsFlextInfraTestmonDbInspector:
    """Prove WAL checkpoint, integrity, and change decisions."""

    @staticmethod
    def test_missing_db_fails_loud(tmp_path: Path) -> None:
        """Test missing db fails loud."""
        filename = config.Infra.codegen.make.testmon_cache.database_filename
        repository_root = tmp_path / "checkout"
        repository_root.mkdir()
        inspector = FlextInfraTestmonDbInspector(
            repository_root=repository_root,
            db_path=tmp_path / "cache" / filename,
            pre_run_digest=None,
        )

        with u.Tests.raises(FileNotFoundError):
            inspector.execute()

    @staticmethod
    def test_native_checkout_database_is_accepted(tmp_path: Path) -> None:
        """Testmon's native checkout-root database is the inspected database."""
        repository_root = tmp_path / "checkout"
        repository_root.mkdir()
        database = (
            repository_root / config.Infra.codegen.make.testmon_cache.database_filename
        )

        inspector = FlextInfraTestmonDbInspector(
            repository_root=repository_root,
            db_path=database,
            pre_run_digest=None,
        )

        tm.that(inspector.db_path, eq=database)

    @staticmethod
    def test_corrupt_db_preserves_sqlite_failure(tmp_path: Path) -> None:
        """Test corrupt db preserves sqlite failure."""
        repository_root = tmp_path / "checkout"
        repository_root.mkdir()
        db = (
            tmp_path
            / "cache"
            / config.Infra.codegen.make.testmon_cache.database_filename
        )
        db.parent.mkdir()
        db.write_text("not a sqlite database", encoding="utf-8")

        with u.Tests.raises(sqlite3.DatabaseError):
            FlextInfraTestmonDbInspector(
                repository_root=repository_root,
                db_path=db,
                pre_run_digest=None,
            ).execute()

    @staticmethod
    def test_healthy_new_db_is_reported_created(tmp_path: Path) -> None:
        """A healthy database with no input digest is reported as created."""
        repository_root = tmp_path / "checkout"
        repository_root.mkdir()
        db = (
            tmp_path
            / "cache"
            / config.Infra.codegen.make.testmon_cache.database_filename
        )
        db.parent.mkdir()
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE meta (k TEXT, v TEXT)")
        connection.execute("INSERT INTO meta VALUES ('schema', '1')")
        connection.commit()
        connection.close()
        state: p.Infra.TestmonCacheState = tm.ok(
            FlextInfraTestmonDbInspector(
                repository_root=repository_root,
                db_path=db,
                pre_run_digest=None,
            ).execute(),
        )
        tm.fail(state.restored_accepted)
        tm.that(state.reason, eq="created")

    @staticmethod
    def test_unchanged_db_is_reported_unchanged(tmp_path: Path) -> None:
        """An unchanged restored database is accepted and reported unchanged."""
        repository_root = tmp_path / "checkout"
        repository_root.mkdir()
        db = (
            tmp_path
            / "cache"
            / config.Infra.codegen.make.testmon_cache.database_filename
        )
        db.parent.mkdir()
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE meta (k TEXT)")
        connection.commit()
        connection.close()
        digest = FlextInfraTestmonDbInspector.digest_file(db)
        state: p.Infra.TestmonCacheState = tm.ok(
            FlextInfraTestmonDbInspector(
                repository_root=repository_root,
                db_path=db,
                pre_run_digest=digest,
            ).execute(),
        )
        tm.ok(state.restored_accepted)
        tm.fail(state.changed)
        tm.that(state.reason, eq="unchanged")
