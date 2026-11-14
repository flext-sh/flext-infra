"""A stopped native scan keeps every completed batch's cache fragments.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, r, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class TestsFlextInfraCodemodScanCacheBatchProgress:
    """A scan stopped mid-way leaves its finished batches for the next run."""

    class _StopAfter:
        """Run the native scanner for the first calls, then stop like a timeout."""

        def __init__(self, completed: int) -> None:
            self.remaining = completed

        def run_to_file(self, *args: object, **kwargs: object) -> object:
            """Delegate while budget remains; then fail like a killed scanner.

            Returns:
                The delegated outcome, or a stopped-scanner failure.

            """
            if self.remaining == 0:
                return r[object].fail("scanner stopped by its budget")
            self.remaining -= 1
            return u.Cli.run_to_file(*args, **kwargs)

    @staticmethod
    def _project(tmp_path: Path) -> Path:
        """Build a project with several scannable sources.

        Returns:
            The project root.

        """
        root = u.Tests.mk_project(
            tmp_path,
            "scan-batch",
            pyproject='[project]\nname = "scan-batch"\nversion = "0.1.0"\n',
            with_src=True,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / "scan_batch"
        sources = {
            package / c.Infra.INIT_PY: "__all__: list[str] = []\n",
            package / "alpha.py": "ALPHA = 1\n",
            package / "beta.py": "BETA = 2\n",
            package / "gamma.py": "GAMMA = 3\n",
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        return root

    @classmethod
    def test_stopped_scan_keeps_completed_batches(
        cls,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Only the batches after the stop are misses on the next run."""
        root = cls._project(tmp_path)
        monkeypatch.setattr(config.Infra.codegen.make, "scan_batch_files", 1)
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            plan = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        targets = u.Infra.ast_grep_scan_targets(root)
        stopped = tm.ok(
            FlextInfraModGateEngine.native_findings(
                root, plan, targets, runner=cls._StopAfter(2)
            )
        )
        tm.that(len(stopped.native_failures), eq=1)
        first = capsys.readouterr().err
        tm.that(first, has=" hit=0 miss=4\n")
        tm.ok(FlextInfraModGateEngine.native_findings(root, plan, targets))
        tm.that(capsys.readouterr().err, has=" hit=2 miss=2\n")


__all__: list[str] = ["TestsFlextInfraCodemodScanCacheBatchProgress"]
