"""Pytest's selected project owns its test package and fixture registration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

import tests
from tests import conftest


class TestsPytestProjectContext:
    """Native pytest imports retain project-local package and fixture identities."""

    @staticmethod
    def test_selected_project_owns_test_package_and_fixtures(
        pytestconfig: pytest.Config,
        infra_git_repo: Path,
    ) -> None:
        """Resolve the selected root without replacing cached module identities."""
        package_file = Path(tm.not_none(tests.__file__)).resolve()
        tm.that(
            package_file,
            eq=pytestconfig.rootpath / tests.__name__ / "__init__.py",
        )
        tm.that((infra_git_repo / ".git").is_dir(), eq=True)
        tm.that(pytestconfig.pluginmanager.is_registered(conftest), eq=True)
