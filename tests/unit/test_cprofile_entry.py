"""Boundary tests for the source-live cProfile execution entrypoint."""

from __future__ import annotations

import runpy

import pytest


def test_cprofile_entry_rejects_report_rendering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report rendering remains owned by the canonical typed report service."""
    monkeypatch.setenv("FLEXT_CPROFILE_ACTION", "report")
    with pytest.raises(ValueError, match="invalid cProfile action: report"):
        _ = runpy.run_module("flext_infra._cprofile_entry", run_name="__main__")


__all__: list[str] = []
