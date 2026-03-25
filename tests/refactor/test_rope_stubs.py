"""Wave 0 stub tests confirming rope is importable."""

from __future__ import annotations

from rope.base.project import Project
from rope.contrib.findit import find_occurrences
from rope.refactor.rename import Rename


def test_rope_import() -> None:
    """Confirm rope.base.project.Project is importable."""
    assert Project is not None


def test_rope_rename_import() -> None:
    """Confirm rope.refactor.rename.Rename is importable."""
    assert Rename is not None


def test_rope_find_occurrences_import() -> None:
    """Confirm rope.contrib.findit.find_occurrences is importable."""
    assert find_occurrences is not None
