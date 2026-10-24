"""Real native gate failures preserve independent operation execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraCli
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraGateOperationIsolation:
    """Observe actual Ruff failures and Markdown repair effects through the CLI."""

    @staticmethod
    @pytest.mark.parametrize("fail_fast", [False, True])
    def test_project_findings_preserve_declared_execution_policy(
        tmp_path: Path, *, fail_fast: bool
    ) -> None:
        """The final status stays red and independent effects follow explicit policy."""
        project = u.Tests.mk_project(tmp_path, "native-fixture", with_src=True)
        broken = project / "src" / "broken.py"
        broken.write_text("def broken(:\n", encoding="utf-8")
        before = broken.read_bytes()
        document = project / "README.md"
        original = "# Fixture\n\n\nParagraph.\n"
        document.write_text(original, encoding="utf-8")

        exit_code = FlextInfraCli.infra_main([
            "check",
            "run",
            "--repository-root",
            str(project),
            "--gates",
            f"{c.Infra.LINT},{c.Infra.MARKDOWN}",
            "--apply",
            *(("--fail-fast",) if fail_fast else ()),
        ])

        tm.that(exit_code, eq=1)
        tm.that(broken.read_bytes(), eq=before)
        tm.that(
            document.read_text(encoding="utf-8"),
            eq=original if fail_fast else "# Fixture\n\nParagraph.\n",
        )
