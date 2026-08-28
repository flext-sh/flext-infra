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
    installs uv beforehand. Both closed topology profiles receive the same
    generated workflow, so no checkout retains a hand-written copy.
    """

    def test_docs_workflow_reaches_every_profile_that_ci_reaches(self) -> None:
        """The docs workflow is projected wherever the CI workflow is."""
        docs = _artifact(_DOCS_DESTINATION)
        ci = _artifact(_CI_DESTINATION)

        tm.that(sorted(docs.profiles), eq=sorted(ci.profiles))

    def test_docs_workflow_uses_only_the_closed_topology_profiles(self) -> None:
        """Docs projection accepts exactly workspace and standalone."""
        docs = _artifact(_DOCS_DESTINATION)

        tm.that(set(docs.profiles), eq={"workspace", "standalone"})


__all__: tuple[str, ...] = ()
