"""Verify native lock consistency through the declared uv runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, p, r, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraWorkspaceLockCompleteness:
    """Delegate manifest freshness and graph completeness to native uv."""

    @classmethod
    def execute_request(cls, request: p.Infra.WorkspaceRequest) -> p.Result[int]:
        """Verify the native project elected for the supplied checkout.

        Returns:
            Zero after native validation, or its original execution failure.

        """
        return cls.verify_lock(request.repository_root)

    @staticmethod
    def verify_lock(repository_root: Path) -> p.Result[int]:
        """Check the lock without resolution, installation or lock mutation.

        Returns:
            Zero after native validation, or its original execution failure.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        selected = context.value
        executable = u.Infra.managed_mise_binary(c.Infra.UV, selected.runtime_root)
        if executable.failure:
            return r[int].from_failure(executable)
        checked = u.Cli.run_checked(
            (
                str(executable.value),
                "lock",
                "--check",
                "--project",
                str(selected.runtime_root),
                "--python",
                str(
                    u.Infra.runtime_python(
                        selected.project_root, runtime_root=selected.runtime_root
                    )
                ),
                "--no-python-downloads",
            ),
            cwd=selected.runtime_root,
            options=m.Cli.ProcessOptions(
                env={"MISE_AUTO_INSTALL": c.ParserBooleanToken.ZERO},
                remove_env_keys=config.Infra.codegen.make.native_environment_unset,
            ),
            timeout=c.Infra.TIMEOUT_LONG,
        )
        if checked.failure:
            return r[int].from_failure(checked)
        return r[int].ok(0)


__all__: tuple[str, ...] = ("FlextInfraWorkspaceLockCompleteness",)
