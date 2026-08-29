"""Contract tests for the public docs CLI workflow."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm


class TestsDocsApplyContract:
    """The docs workflow uses read-only public Make contracts."""

    def test_generated_workflow_uses_read_only_make_docs(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
        ).read_text(encoding="utf-8")

        tm.that(workflow, has="make gen WHAT=check")
        tm.that(workflow, has="make docs WHAT=audit")
        tm.that(workflow, has="make docs WHAT=validate")
        tm.that(workflow, has="make docs WHAT=build")
        tm.that(workflow, lacks="python -m flext_infra docs")
        tm.that(workflow, lacks="docs generate")
        tm.that(workflow, lacks="--apply")


__all__: tuple[str, ...] = ()
