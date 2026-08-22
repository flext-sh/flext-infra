"""Tests that workspace-root checks fan out through the declared topology.

A workspace root delegates each check to its member instead of aggregating
member paths into one root process. This preserves project isolation while
ensuring the global gate covers every member declared by the workspace SSOT.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm


class TestsFlextInfraWorkspaceCheckScope:
    def test_workspace_root_check_fans_out_to_every_member(self) -> None:
        """The root selects declared members and forwards check gates."""
        # The member list is rendered from the manifest at generation time, so
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
                "WORKSPACE_MEMBERS :={% for member in workspace_members %} "
                "{{ member }}{% endfor %}"
            ),
        )
        tm.that(template, has="ALLOWED_PROJECTS := . $(WORKSPACE_MEMBERS)")
        tm.that(template, has="override WORKSPACE := $(WORKSPACE_ROOT)/$(PROJECT)")
        tm.that(template, has="$(WORKSPACE_ORCHESTRATE) --verb check")
        tm.that(template, has='--make-arg "CHECK_GATES=$$gates"')
