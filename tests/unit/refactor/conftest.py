from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from tests import t, u


@pytest.fixture
def rope_project(tmp_path: Path) -> Iterator[t.Infra.RopeProject]:
    """Shared minimal rope project for refactor unit tests."""
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    yield project
    project.close()
