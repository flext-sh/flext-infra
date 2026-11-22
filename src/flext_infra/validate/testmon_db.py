"""Typed integrity inspection for the native pytest-testmon SQLite DB.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Annotated, Self, override

from flext_infra import m, p, r, s, u


class FlextInfraTestmonDbInspector(s[p.Infra.TestmonCacheState]):
    """Checkpoint WAL, verify integrity, and report the change since the run."""

    db_path: Annotated[Path, m.Field(description="Absolute .testmondata path.")]
    pre_run_digest: Annotated[
        str | None,
        m.Field(default=None, description="Hex digest of DB bytes before pytest."),
    ] = None

    @m.model_validator(mode="after")
    def _validate_absolute_db(self) -> Self:
        """Reject a relative database path.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If testmon db_path is not absolute.

        """
        if not self.db_path.is_absolute():
            msg = "testmon db_path must be absolute"
            raise ValueError(msg)
        return self

    @staticmethod
    def digest_file(path: Path) -> str | None:
        """Return a stable digest; absence alone denotes a cold cache.

        Returns:
            A stable digest; absence alone denotes a cold cache.

        Raises:
            ValueError: If testmon db must not be a symlink; or if testmon db must be a
                regular file; or if testmon db must not be empty.

        """
        if path.is_symlink():
            msg = f"testmon db must not be a symlink: {path}"
            raise ValueError(msg)
        if not path.exists():
            return None
        if not path.is_file():
            msg = f"testmon db must be a regular file: {path}"
            raise ValueError(msg)
        if path.stat().st_size == 0:
            msg = f"testmon db must not be empty: {path}"
            raise ValueError(msg)
        return u.Cli.sha256_file(path)

    @staticmethod
    def _validate_open_db(connection: sqlite3.Connection) -> None:
        """Raise on the first invalid SQLite cache property.

        Raises:
            RuntimeError: If testmon wal_checkpoint busy=; or if testmon
                integrity_check=; or if testmon schema empty.

        """
        checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if checkpoint is None or int(checkpoint[0]) != 0:
            msg = f"testmon wal_checkpoint busy={checkpoint!r}"
            raise RuntimeError(msg)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            msg = f"testmon integrity_check={integrity!r}"
            raise RuntimeError(msg)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
            ).fetchall()
        }
        if not tables:
            msg = "testmon schema empty"
            raise RuntimeError(msg)

    def _inspect_existing(self) -> p.Result[p.Infra.TestmonCacheState]:
        """Validate one on-disk DB after pytest has closed it.

        Returns:
            The resulting ``p.Result[p.Infra.TestmonCacheState]``.

        Raises:
            FileNotFoundError: If ``not path.exists()``.
            ValueError: If testmon db must not be a symlink; or if testmon db must be a
                regular file; or if testmon db must not be empty.

        """
        path = self.db_path
        if path.is_symlink():
            msg = f"testmon db must not be a symlink: {path}"
            raise ValueError(msg)
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_file():
            msg = f"testmon db must be a regular file: {path}"
            raise ValueError(msg)
        if path.stat().st_size == 0:
            msg = f"testmon db must not be empty: {path}"
            raise ValueError(msg)
        database_uri = f"{path.as_uri()}?mode=rw"
        with closing(sqlite3.connect(database_uri, uri=True)) as connection:
            self._validate_open_db(connection)
        post_digest = self.digest_file(path)
        changed = post_digest is not None and post_digest != self.pre_run_digest
        restored = self.pre_run_digest is not None
        if not restored:
            reason = "created"
        elif changed:
            reason = "changed"
        else:
            reason = "unchanged"
        return r[p.Infra.TestmonCacheState].ok(
            m.Infra.TestmonCacheState(
                restored_accepted=restored,
                changed=changed,
                reason=reason,
            ),
        )

    @override
    def execute(self) -> p.Result[p.Infra.TestmonCacheState]:
        """Return typed cache state after a successful testmon-backed pytest run.

        Returns:
            Typed cache state after a successful testmon-backed pytest run.

        """
        return self._inspect_existing()


__all__: list[str] = ["FlextInfraTestmonDbInspector"]
