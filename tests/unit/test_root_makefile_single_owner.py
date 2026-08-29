"""Exactly one generator owns every generated Makefile, including the root.

The conform engine (``base/Makefile.j2``) is the SINGLE owner of the generated
Makefile for every repository. The same local-only template serves every
consumer, so there
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
    def test_single_makefile_entry_owns_the_surface_without_profiles(self) -> None:
        """One profile-free render entry owns the Makefile."""
        entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(entries, len=1)
        tm.that("profiles" in type(entries[0]).model_fields, eq=False)

    def test_no_divergent_workspace_makefile_template_remains(self) -> None:
        """The retired dedicated workspace Makefile template no longer exists."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        dedicated = templates_root / "workspace_makefile.mk.j2"

        tm.that(dedicated.exists(), eq=False)

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

    def test_generator_owner_self_hosts_through_its_setup_runtime(self) -> None:
        """The owner validates the pending owner source, not an older baseline."""
        makefile = Path(__file__).resolve().parents[2] / c.Infra.MAKEFILE_FILENAME
        content = makefile.read_text(encoding="utf-8")

        tm.that(content, has="FLEXT_INFRA_BOOTSTRAP = $(PROJECT_FLEXT_INFRA)")

    def test_fix_routes_declared_fixable_gates_through_checker(self) -> None:
        """The local fix verb reaches every gate that advertises a fixer."""
        makefile = Path(__file__).resolve().parents[2] / c.Infra.MAKEFILE_FILENAME
        content = makefile.read_text(encoding="utf-8")
        expected = ",".join(config.Infra.codegen.make.check_gates_fixable)

        tm.that(content, has=f"CHECK_GATES_FIXABLE := {expected}")
        tm.that(content, has="ruff check --fix $(RUFF_PATHS)")
        tm.that(
            content,
            has=(
                'check run --workspace "$(PROJECT_ROOT)" '
                '--gates "$(CHECK_GATES_FIXABLE)" --projects . --fix'
            ),
        )


__all__: tuple[str, ...] = ()
