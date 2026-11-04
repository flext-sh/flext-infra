"""Public Git orchestration service for flext-infra consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraGitLanes, m, p, s, u


class FlextInfraGitService(s[p.Infra.GitStatusReport]):
    """Thin public status reporting and lane admission use cases."""

    repository: Annotated[
        Path | None,
        m.Field(description="Repository path; defaults to repository_root"),
    ] = None

    def _repo(self) -> Path:
        """Resolve the single repository root for this invocation.

        Returns:
            The resulting ``Path``.

        """
        return (self.repository or self.repository_root).expanduser().resolve()

    @override
    def execute(self) -> p.Result[p.Infra.GitStatusReport]:
        """Capture porcelain status for the selected repository.

        Returns:
            The resulting ``p.Result[p.Infra.GitStatusReport]``.

        """
        return u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=self._repo()))

    @staticmethod
    def verify_lane(
        request: p.Infra.GitLaneVerificationRequest,
    ) -> p.Result[p.Infra.GitOidReport]:
        """Run the shared, effect-free lane admission owner.

        Returns:
            Live integration identity or the original admission failure.

        """
        return u.Infra.git_verify_lane(request)

    @classmethod
    def verify_lanes(
        cls,
        request: p.Infra.GitLaneVerificationRequest,
    ) -> p.Result[p.Infra.GitLaneReport]:
        """Fail on stashes, merged-but-alive branches and orphan or merged worktrees.

        The one census evaluator owns the verdict; the service only publishes it.

        Returns:
            The resulting ``p.Result[p.Infra.GitLaneReport]``.

        """
        return FlextInfraGitLanes.verify_lanes(request)

    @staticmethod
    def lane_ownership(
        request: p.Infra.GitLaneOwnershipRequest,
    ) -> p.Result[p.Infra.GitLaneOwnershipReceipt]:
        """Read authenticated prior ownership from an existing published checkpoint.

        Returns:
            The native producer receipt without changing current shared work.

        """
        return u.Infra.git_lane_ownership(request)


__all__: list[str] = ["FlextInfraGitService"]
