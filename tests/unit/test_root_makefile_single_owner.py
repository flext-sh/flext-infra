"""Exactly one generator owns every generated Makefile, including the root.

The conform engine (``base/Makefile.j2``) is the SINGLE owner of the generated
Makefile for every profile. The workspace-root profile is served by the same
template — its member gate fan-out is rendered behind a profile gate — so there
is no second, divergent generator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra import c, config
from flext_tests import tm


class TestsFlextInfraRootMakefileSingleOwner:
    def test_single_makefile_entry_owns_every_profile(self) -> None:
        """One render entry owns the Makefile for both effective profiles."""
        entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(entries, len=1)
        tm.that(entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE)
        tm.that(entries[0].profiles, has=c.Infra.MakeProfile.STANDALONE)

    def test_no_divergent_workspace_makefile_template_remains(self) -> None:
        """The retired dedicated workspace Makefile template no longer exists."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        dedicated = templates_root / "workspace_makefile.mk.j2"

        tm.that(dedicated.exists(), eq=False)

    def test_generic_template_carries_the_single_custom_include(self) -> None:
        """The sole template injects the one custom-include directive from SSOT."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        generic = (templates_root / "project" / "base" / "Makefile.j2").read_text(
            encoding="utf-8"
        )

        tm.that(generic, has="{{ makefile_custom_include }}")
        tm.that(generic, lacks="workspace_custom.mk")

    def test_generic_template_routes_generation_through_conform_once(self) -> None:
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        generic = (templates_root / "project" / "base" / "Makefile.j2").read_text(
            encoding="utf-8"
        )
        lines = generic.splitlines()
        marker_lines = tuple(
            line
            for line in lines
            if line.startswith(("<<<<<<< ", ">>>>>>> ")) or line == "======="
        )
        check_body = generic.split("_builtin_gen_check:", 1)[1].split("\n\n", 1)[0]
        all_body = generic.split("_builtin_gen_all:", 1)[1].split("\n\n", 1)[0]

        tm.that(marker_lines, eq=())
        tm.that(check_body.count("codegen conform"), eq=1)
        tm.that(all_body.count("codegen conform"), eq=1)
        tm.that(check_body, lacks=["codegen init", "deps modernize"])
        tm.that(all_body, lacks=["codegen init", "deps modernize"])


__all__: tuple[str, ...] = ()
