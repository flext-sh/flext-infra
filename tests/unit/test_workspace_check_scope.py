"""Tests that workspace checks fan out through the declared topology.

A workspace delegates each check to its subproject instead of aggregating
subproject paths into one root process. This preserves project isolation while
ensuring the global gate covers every repository declared by local topology.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm


class TestsFlextInfraWorkspaceCheckScope:
    def test_workspace_check_fans_out_to_every_subproject(self) -> None:
        """The workspace selects declared subprojects and forwards check gates."""
        # The subproject list is rendered from local topology at generation time, so
        # the contract lives in the template, not in this checkout's topology.

        template = (
            Path(flext_infra.__file__).resolve().parent
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        ).read_text(encoding="utf-8")

        tm.that(
            template,
            has=(
                "WORKSPACE_SUBPROJECTS :={% for subproject in workspace_subprojects %} "
                "{{ subproject }}{% endfor %}"
            ),
        )
        tm.that(template, has="ALLOWED_PROJECTS := . $(WORKSPACE_SUBPROJECTS)")
        tm.that(template, has="override WORKSPACE := $(WORKSPACE_ROOT)/$(PROJECT)")
        tm.that(template, has="$(WORKSPACE_ORCHESTRATE) --verb check")
        tm.that(template, has='--make-arg "CHECK_GATES=$$gates"')
