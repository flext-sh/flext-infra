"""Tests that exactly one generator owns the workspace root Makefile.

Two owners writing the same path is a defect on its own; so is each owner
including a different custom surface. Both generators must include the single
custom.mk surface, so a target defined there is picked up regardless of which
generator produced the file.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import c, config


class TestsFlextInfraRootMakefileSingleOwner:
    def test_generic_template_entry_excludes_the_workspace_root(self) -> None:
        """The root profile is served by its dedicated generator only."""
        entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(entries, len=1)
        tm.that(entries[0].profiles, lacks=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_both_generators_agree_on_one_custom_include(self) -> None:
        """A single custom-include name exists across both Makefile templates."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        generic = (templates_root / "project" / "base" / "Makefile.j2").read_text(
            encoding="utf-8"
        )
        dedicated = (templates_root / "workspace_makefile.mk.j2").read_text(
            encoding="utf-8"
        )

        # Both generators must include the SAME single custom surface, so a
        # target written in it is never silently dropped. The generic template
        # injects the directive from the constants SSOT; the dedicated one is
        # a captured Makefile and carries the literal directive.
        tm.that(dedicated, has=c.Infra.MAKEFILE_CUSTOM_INCLUDE)
        tm.that(generic, has="{{ makefile_custom_include }}")
        tm.that(dedicated, lacks="workspace_custom.mk")
        tm.that(generic, lacks="workspace_custom.mk")
