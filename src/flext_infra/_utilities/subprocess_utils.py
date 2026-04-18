"""Subprocess helpers for flext-infra validators and codegen.

Centralizes subprocess invocations behind a controlled entrypoint so
callers (guards, generators) never touch ``subprocess`` directly. This
file matches the ``**/*subprocess_utils*`` pattern in
``pyproject.toml [tool.ruff.lint.per-file-ignores]`` which exempts
S404/S603 for legitimate subprocess use — downstream modules then stay
free of local ``# noqa`` bypasses.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from typing import ClassVar


class FlextInfraUtilitiesSubprocessUtils:
    """Controlled subprocess entrypoints for infra guards and generators."""

    _flext_enforcement_exempt: ClassVar[bool] = True

    @staticmethod
    def run_python_import_smoke(module_name: str) -> tuple[int, str]:
        """Run ``python -c 'import <module_name>'`` in a fresh process.

        Returns (returncode, stderr_last_line). Used by Guard 7
        (fresh-process import smoke test) to detect cycles the lazy
        loader would otherwise mask.
        """
        completed = subprocess.run(
            [sys.executable, "-c", f"import {module_name}"],
            capture_output=True,
            check=False,
        )
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        last_line = stderr.splitlines()[-1] if stderr else ""
        return completed.returncode, last_line

    @staticmethod
    def run_captured(
        command: Sequence[str],
        *,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        """Run a command with captured output. Used by codegen/test helpers."""
        return subprocess.run(
            command,
            capture_output=True,
            check=check,
        )


__all__: list[str] = ["FlextInfraUtilitiesSubprocessUtils"]
