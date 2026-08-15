"""Contract tests for the public docs CLI workflow."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm


class TestsDocsApplyContract:
    """The docs workflow uses the public CLI after Make verb retirement."""

    def test_generated_workflow_uses_public_docs_cli(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
        ).read_text(encoding="utf-8")

        tm.that(workflow, has="python -m flext_infra docs audit")
        tm.that(workflow, has="python -m flext_infra docs generate")
        tm.that(workflow, has="python -m flext_infra docs validate")
        tm.that(workflow, has="python -m flext_infra docs build")
        tm.that(workflow, has="--workspace . --output-dir .reports/docs")
        tm.that(workflow, lacks="make docs")


__all__: tuple[str, ...] = ()
