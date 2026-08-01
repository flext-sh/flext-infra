"""Unit-test boundary fixtures for FLEXT Infra."""

from __future__ import annotations

import pytest

from flext_infra import c


@pytest.fixture(autouse=True)
def execute_cli_routes_inside_governed_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise command behavior without repeating the integration transaction."""
    monkeypatch.setenv(c.Infra.WORKTREE_TRANSACTION_ENV, "1")
