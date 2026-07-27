"""Public package version behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

import flext_infra as infra_pkg
from flext_infra import u

if TYPE_CHECKING:
    from flext_infra import p


class TestsFlextInfraInfraVersionCore:
    """Validate public package metadata against canonical public utilities."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def _metadata(self) -> p.ProjectMetadata:
        metadata_result = u.read_project_metadata(self._project_root())
        tm.ok(metadata_result)
        return metadata_result.value

    def test_package_version_matches_project_metadata(self) -> None:
        metadata = self._metadata()

        tm.that(infra_pkg.__version__, eq=metadata.project.version)

    def test_package_version_info_matches_current_workspace_semver_prefix(self) -> None:
        version_result = u.Infra.current_workspace_version(self._project_root())

        tm.ok(version_result)
        parse_result = u.Infra.parse_semver(version_result.value)
        tm.ok(parse_result)
        tm.that(infra_pkg.__version_info__[:3], eq=parse_result.value)

    def test_package_version_fields_have_public_runtime_types(self) -> None:
        tm.that(infra_pkg.__version__, is_=str)
        tm.that(infra_pkg.__version_info__, is_=tuple)
