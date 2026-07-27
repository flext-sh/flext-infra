"""Tests that exactly one custom Make surface exists, named custom.mk.

custom.mk is the legitimate extension point for custom commands, WHATs and
hooks. A second file (workspace_custom.mk) splits that responsibility: the
generated Makefile includes only one of them per profile, so any target written
in the other is silently dead.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import config


class TestsFlextInfraCustomMakeSurfaceIsSingle:
    def test_codegen_declares_only_the_custom_make_surface(self) -> None:
        """The managed-file catalog declares custom.mk and no sibling variant."""
        managed = tuple(
            item.path.as_posix() for item in config.Infra.codegen.managed_files
        )
        custom_surfaces = sorted(path for path in managed if path.endswith("custom.mk"))

        tm.that(custom_surfaces, eq=["custom.mk"])

    def test_no_template_emits_a_second_custom_surface(self) -> None:
        """No shipped template references a custom surface other than custom.mk."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        offenders = sorted(
            str(path.relative_to(templates_root))
            for path in templates_root.rglob("*.j2")
            if "workspace_custom.mk" in path.read_text(encoding="utf-8")
        )

        tm.that(offenders, eq=[])
