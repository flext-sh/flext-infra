"""Public package metadata export tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra as infra_pkg
from flext_infra import m, u
from flext_tests import tm


class TestsFlextInfraInfraVersionExtra:
    """Validate public package metadata exports against project SSOT."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def _runtime_constants(self) -> m.ProjectConstants:
        return u.read_project_constants(infra_pkg.__title__, root=self._project_root())

    def test_public_package_metadata_matches_project_metadata(self) -> None:
        metadata = u.read_project_metadata(self._project_root())
        constants = self._runtime_constants()

        tm.that(infra_pkg.__title__, eq=metadata.name)
        tm.that(infra_pkg.__version__, eq=constants.PACKAGE_VERSION)
        tm.that(infra_pkg.__description__, eq=metadata.description)
        tm.that(infra_pkg.__license__, eq=constants.PACKAGE_LICENSE)
        tm.that(infra_pkg.__url__, eq=constants.PACKAGE_URL)

    def test_public_package_author_matches_project_authors(self) -> None:
        constants = self._runtime_constants()

        assert constants.PACKAGE_AUTHORS
        tm.that(infra_pkg.__author__, eq=constants.PACKAGE_AUTHORS[0])

    def test_public_package_exports_have_expected_runtime_types(self) -> None:
        tm.that(infra_pkg.__version__, is_=str)
        tm.that(infra_pkg.__version_info__, is_=tuple)
        tm.that(infra_pkg.__title__, is_=str)
        tm.that(infra_pkg.__description__, is_=str)
        tm.that(infra_pkg.__author__, is_=str)
        tm.that(infra_pkg.__author_email__, is_=str)
        tm.that(infra_pkg.__license__, is_=str)
        tm.that(infra_pkg.__url__, is_=str)

    def test_public_package_version_info_is_tuple(self) -> None:
        """Test that module-level __version_info__ is a tuple."""
        tm.that(infra_pkg.__version_info__, is_=tuple)
