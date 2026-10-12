"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.codegen import FlextInfraCodegenConformArtifactRender
from tests import tm


class TestsFlextInfraArtifactRenderEmptyGuard:
    """A managed render that produced no content must fail loud, never publish.

    A workflow fragment gated on an undeclared capability layer (the
    ``private_dependency_auth`` incident, bead cosmos-dxtk7) rendered 0 bytes
    and was emitted verbatim: consumers inspected the directory, saw the
    artifact present, and concluded the capability was delivered while every
    step it owns was silently absent. The render funnel owns the refusal:
    empty render in, typed failure out, naming the template, the
    destination, and the declaration cause.
    """

    _FRAGMENT_TEMPLATE = Path(
        "base/.github/workflows/_fragments/private_dependency_auth.j2",
    )
    _FRAGMENT_DESTINATION = ".github/workflows/_fragments/private_dependency_auth"

    @staticmethod
    def test_empty_render_fails_loud_naming_template_and_cause() -> None:
        """A 0-byte render is a typed failure naming template and cause."""
        refused = FlextInfraCodegenConformArtifactRender._require_rendered_content(
            "",
            template_relpath=TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_TEMPLATE,
            destination=(TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_DESTINATION),
        )
        tm.that(refused.failure, eq=True)
        tm.that(
            refused.error,
            has=str(
                TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_TEMPLATE,
            ),
        )
        tm.that(
            refused.error,
            has=TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_DESTINATION,
        )
        tm.that(refused.error, has="render produced no content")
        tm.that(refused.error, has="consumer declaration error")

    @staticmethod
    def test_whitespace_render_fails_loud_with_planner_prefix() -> None:
        """A whitespace-only render is refused and carries the planner banner."""
        refused = FlextInfraCodegenConformArtifactRender._require_rendered_content(
            "  \n\t\n",
            template_relpath=TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_TEMPLATE,
            destination=(TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_DESTINATION),
            failure_prefix="stage=scaffold ",
        )
        tm.that(refused.failure, eq=True)
        tm.that(refused.error, has="stage=scaffold ")
        tm.that(refused.error, has="publishing a 0-byte artifact is forbidden")

    @staticmethod
    def test_rendered_content_passes_through_verbatim() -> None:
        """A render with real content passes through byte-exact."""
        content = "- name: step\n  run: echo hi\n"
        kept = FlextInfraCodegenConformArtifactRender._require_rendered_content(
            content,
            template_relpath=TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_TEMPLATE,
            destination=(TestsFlextInfraArtifactRenderEmptyGuard._FRAGMENT_DESTINATION),
        )
        tm.that(kept.failure, eq=False)
        tm.that(kept.value, eq=content)
