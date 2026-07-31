"""Typed runtime environment observations for the Beads lifecycle."""

from __future__ import annotations

import os

from flext_infra import c, m


class FlextInfraUtilitiesBeadsRuntime:
    """Build the Beads runtime context from the active process environment."""

    @classmethod
    def context_from_environment(cls) -> m.Infra.BeadsRuntimeContext:
        """Return a validated model describing whether this process owns the tracker."""
        return m.Infra.BeadsRuntimeContext(
            in_transaction=os.environ.get(c.Infra.WORKTREE_TRANSACTION_ENV) == "1",
            in_ci=os.environ.get(c.Infra.ENV_VAR_GITHUB_ACTIONS) == "true",
        )
