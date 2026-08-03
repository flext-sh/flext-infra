"""Contract tests for the declared GitHub workflow surface."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm

_WORKFLOW_PREFIX = ".github/workflows/"


def _declared_workflows() -> set[str]:
    """Return every workflow filename the SSOT owns."""
    declared: set[str] = set()
    for entry in config.Infra.codegen.templates.entries:
        destination = str(entry.destination)
        if destination.startswith(_WORKFLOW_PREFIX):
            declared.add(destination.removeprefix(_WORKFLOW_PREFIX))
    for managed in config.Infra.codegen.managed_files:
        destination = managed.path.as_posix()
        if destination.startswith(_WORKFLOW_PREFIX):
            declared.add(destination.removeprefix(_WORKFLOW_PREFIX))
    return declared


class TestsWorkflowOrphanGuard:
    """The SSOT owns the CI surface, so it must name every workflow it allows.

    conform only iterates declared artifacts: a workflow added by hand is
    never visited, never regenerated, and never pruned. `codeql.yml` survived
    that way in a single member for months and blocked a promotion, because
    Code Scanning needs a paid entitlement on private repositories and the
    job could only ever fail.
    """

    def test_the_declared_workflow_surface_is_explicit(self) -> None:
        """The SSOT declares the exact workflow set it governs."""
        tm.that(sorted(_declared_workflows()), eq=sorted(_ALLOWED_WORKFLOWS))

    def test_code_scanning_is_not_projected_to_private_repositories(self) -> None:
        """No workflow requires a paid Code Security entitlement.

        CodeQL only runs on a private repository with GitHub Advanced
        Security. Projecting it without that entitlement guarantees a red
        check, so it stays out of the governed surface until the entitlement
        is an explicit, funded decision.
        """
        tm.that("codeql.yml" in _declared_workflows(), eq=False)


_ALLOWED_WORKFLOWS: tuple[str, ...] = (
    "ci-matrix.yml",
    "ci.yml",
    "docs.yml",
    "release.yml",
)

__all__: tuple[str, ...] = ()
