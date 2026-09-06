"""Ultra-thin workspace service facade composed through FLEXT.

Owns no business logic itself: it composes the private ``_workspace`` service
parts (environment sync today) so callers reach one canonical workspace
surface instead of importing scattered generators.
"""

from __future__ import annotations

from flext_infra.services.workspace._workspace.environment_beads import (
    FlextInfraWorkspaceEnvironmentSync,
)

__all__: list[str] = ["FlextInfraWorkspaceEnvironmentSync"]
