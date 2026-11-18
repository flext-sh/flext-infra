"""Public Git orchestration service for flext-infra consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import m, p, s, u


class FlextInfraGitService(s[p.Infra.GitStatusReport]):
    """Report the porcelain status of one repository."""

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


__all__: list[str] = ["FlextInfraGitService"]
