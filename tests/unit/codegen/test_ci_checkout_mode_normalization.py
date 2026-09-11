"""Verify ci.yml normalizes runner checkout modes before any gate runs."""

from __future__ import annotations

from flext_tests import tm

from .test_ci_integration_branch_triggers import TestsCiIntegrationBranchTriggers


class TestsCiCheckoutModeNormalization:
    """Runner umask 002 checks out 0664; canonical Mise artifacts demand 0o644."""

    def test_ci_job_normalizes_checkout_modes_before_gates(self) -> None:
        rendered = TestsCiIntegrationBranchTriggers._render_ci(
            repository_branch="0.12.0-dev"
        )
        tm.that("chmod -R go-w ." in rendered, eq=True)
        normalize_at = rendered.index("Normalize checkout modes")
        for gate in ("setup (blocking)", "gen check (blocking)", "check (blocking)"):
            tm.that(normalize_at < rendered.index(gate), eq=True)


__all__: tuple[str, ...] = ()
