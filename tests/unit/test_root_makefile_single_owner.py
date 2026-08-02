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
        surfaces = config.Infra.codegen.surfaces
        entries = tuple(
            entry for entry in surfaces.entries if entry.make_role == "wrapper"
        )

        tm.that(entries, len=1)
        tm.that(entries[0].path, eq=surfaces.make_wrapper_path)
        tm.that(entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)
        tm.that(entries[0].profiles, has=c.Infra.MakeProfile.STANDALONE)

    def test_no_divergent_workspace_makefile_template_remains(self) -> None:
        """The retired dedicated workspace Makefile template no longer exists."""
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        dedicated = templates_root / "workspace_makefile.mk.j2"

        tm.that(dedicated.exists(), eq=False)

    def test_wrapper_delegates_only_to_the_configured_engine(self) -> None:
        """The catalog-owned wrapper includes its catalog-owned engine."""
        surfaces = config.Infra.codegen.surfaces
        wrapper = next(
            entry for entry in surfaces.entries if entry.make_role == "wrapper"
        )
        source = tm.not_none(wrapper.source)
        templates_root = Path(flext_infra.__file__).resolve().parent / "templates"
        generic = (templates_root / surfaces.root / source).read_text(encoding="utf-8")

        tm.that(generic, has="include {{ make_engine_path }}")
        tm.that(generic, lacks="custom.mk")


__all__: tuple[str, ...] = ()
