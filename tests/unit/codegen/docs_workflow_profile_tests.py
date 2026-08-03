"""Contract tests for the generated documentation workflow projection."""

from __future__ import annotations

from flext_infra import config, m
from flext_tests import tm

_DOCS_DESTINATION = ".github/workflows/docs.yml"
_CI_DESTINATION = ".github/workflows/ci.yml"


def _artifact(destination: str) -> m.Infra.TemplateEntrySpec:
    """Return the declared render artifact for one destination."""
    for entry in config.Infra.codegen.templates.entries:
        if entry.destination == destination:
            return entry
    msg = f"artifact is not declared: {destination}"
    raise AssertionError(msg)


class TestsDocsWorkflowProfile:
    """Every checkout that owns a docs gate also owns the workflow that runs it.

    The docs workflow calls ``uv sync``; the generated projection is what
    installs uv beforehand. Restricting the projection to ``workspace-root``
    left members with a stale hand-written copy that never installed uv, so
    the job died with "uv: command not found" (exit 127).
    """

    def test_docs_workflow_reaches_every_profile_that_ci_reaches(self) -> None:
        """The docs workflow is projected wherever the CI workflow is."""
        docs = _artifact(_DOCS_DESTINATION)
        ci = _artifact(_CI_DESTINATION)

        tm.that(sorted(docs.profiles), eq=sorted(ci.profiles))

    def test_docs_workflow_is_projected_to_workspace_members(self) -> None:
        """A workspace member receives the generated docs workflow."""
        docs = _artifact(_DOCS_DESTINATION)

        tm.that("workspace-member" in docs.profiles, eq=True)


__all__: tuple[str, ...] = ()
