"""Shared fixtures for the generation Git-HEAD lock contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, u
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_tests import tm
from tests import u as test_u


def lock_repository(root: Path) -> Path:
    """Initialize one real Git fixture repository for lock testing."""
    root.mkdir(parents=True)
    test_u.Tests.initialize_git_repo(root)
    return root


def lock_owner(root: Path) -> FlextInfraCodegenMiseArtifacts:
    """Build the read-only mise-artifacts owner over one fixture root."""
    return FlextInfraCodegenMiseArtifacts(
        repository_root=root, apply_changes=False, check_only=True
    )


def lock_identity(root: Path) -> m.Infra.GitIdentityReport:
    """Resolve the authenticated Git identity of one fixture repository."""
    identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root))
    validated: m.Infra.GitIdentityReport = tm.ok(identity)
    return validated


__all__: list[str] = ["lock_identity", "lock_owner", "lock_repository"]
