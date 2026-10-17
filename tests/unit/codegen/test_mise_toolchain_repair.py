"""Explicit native installation repair refuses invalid requests before effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import settings
from tests import c, m, tm, u


class TestsFlextInfraMiseToolchainRepair:
    """Exercise process-start settings through the actual public CLI."""

    @staticmethod
    @pytest.mark.parametrize("selected", [False, True])
    def test_invalid_selection_fails_before_installation(
        tmp_path: Path,
        *,
        selected: bool,
    ) -> None:
        """Neither an absent selection nor an undeclared name installs a tool."""
        root = u.Tests.git_repository(tmp_path)
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        unknown = "x" * (
            max((len(tool.name) for tool in inputs.spec.toolchain.tools), default=0) + 1
        )
        name = u.type_adapter(str).validate_python(
            type(settings.Infra).model_fields["toolchain_repair_tool"].validation_alias,
        )
        before = frozenset(root.iterdir())
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "codegen",
                    "mise-repair",
                    "--repository-root",
                    str(root),
                ),
                cwd=root,
                timeout=c.Infra.TIMEOUT_SHORT,
                options=m.Cli.ProcessOptions(
                    env={name: unknown} if selected else {},
                    remove_env_keys=() if selected else (name,),
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=False)
        tm.that(
            result.stdout + result.stderr,
            has="undeclared tool" if selected else name,
        )
        tm.that(frozenset(root.iterdir()), eq=before)
