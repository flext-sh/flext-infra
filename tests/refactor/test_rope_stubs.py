"""Wave 0 stub tests confirming rope is importable.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestsFlextInfraRefactorRopeStubs:
    """Behavior contract for test_rope_stubs."""

    def test_rope_project_wrapper(self, tmp_path: Path) -> None:
        """Confirm the Rope project wrapper creates a live project."""
        project = u.Infra.init_rope_project(tmp_path)
        tm.that(project, none=False)
        try:
            tm.that(project.root.real_path, none=False)
        finally:
            project.close()

    def test_rope_find_occurrences_wrapper(self, tmp_path: Path) -> None:
        """Confirm occurrence search works through the utility wrapper."""
        package_dir = tmp_path / "demo"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        target = package_dir / "mod.py"
        target.write_text("class Demo:\n    pass\n\nvalue = Demo()\n", encoding="utf-8")
        project = u.Infra.init_rope_project(tmp_path)
        tm.that(project, none=False)
        try:
            resource = tm.not_none(u.Infra.get_resource_from_path(project, target))
            offset = tm.not_none(
                u.Infra.find_definition_offset(project, resource, "Demo")
            )
            hits = u.Infra.find_occurrences(project, resource, offset)
            tm.that(hits, empty=False)
        finally:
            project.close()
