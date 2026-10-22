"""Public Git orchestration service for flext-infra consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import FlextInfraGitLanes, m, s, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraGitService(s[m.Infra.GitStatusReport]):
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
    def execute(self) -> p.Result[m.Infra.GitStatusReport]:
        """Capture porcelain status for the selected repository.

        Returns:
            The resulting ``p.Result[m.Infra.GitStatusReport]``.

        """
        return u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=self._repo()))

    @classmethod
    def verify_clean(
        cls,
        request: m.Infra.GitStatusRequest,
    ) -> p.Result[m.Infra.GitStatusReport]:
        """Report staged, unstaged, and untracked work without rejecting WIP.

        Preserve recovery objects without probing them for ordinary admission.
        Technical Git failures propagate unchanged from the status use case.

        Returns:
            The resulting ``p.Result[m.Infra.GitStatusReport]``.

        """
        return cls(repository_root=request.repo_root).execute()

    @staticmethod
    def verify_lane(
        request: m.Infra.GitLaneVerificationRequest,
    ) -> p.Result[m.Infra.GitOidReport]:
        """Run the shared, effect-free lane admission owner.

        Returns:
            Live integration identity or the original admission failure.

        """
        return u.Infra.git_verify_lane(request)

    @classmethod
    def verify_lanes(
        cls,
        request: m.Infra.GitLaneVerificationRequest,
    ) -> p.Result[m.Infra.GitLaneReport]:
        """Fail on stashes, merged-but-alive branches and orphan or merged worktrees.

        The one census evaluator owns the verdict; the service only publishes it.

        Returns:
            The resulting ``p.Result[m.Infra.GitLaneReport]``.

        """
        return FlextInfraGitLanes.verify_lanes(request)


__all__: list[str] = ["FlextInfraGitService"]
