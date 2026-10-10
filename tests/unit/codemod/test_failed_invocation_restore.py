"""A failed rewriting invocation publishes nothing on disk.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import m, p, r, t, u

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class TestsFlextInfraFailedInvocationRestore:
    """Record governed sources first; restore them when the run fails."""

    ORIGINAL = '"""Probe module."""\n\nfrom __future__ import annotations\n\nLIMIT = 3\n'
    REWRITTEN = '"""Probe module."""\n\nfrom __future__ import annotations\n\nLIMIT = (\n'
    EMPTY_REPORT = m.Infra.ModScanReport(
        findings=0,
        actionable=0,
        detection_only=0,
        non_actionable_with_fix=0,
        files=frozenset(),
        entries=(),
    )

    @classmethod
    def _workspace(cls, tmp_path: Path) -> t.Pair[Path, Path]:
        """Write one governed probe module into a Git-rooted workspace.

        Returns:
            The repository root and the probe module path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "restore_probe.py"
        tm.ok(u.Cli.atomic_write_text_file(module, cls.ORIGINAL))
        # Publication runs through the codegen transaction, which coordinates
        # only inside an exact Git worktree root, exactly as in production.
        u.Tests.initialize_git_repo(root)
        return root, module

    @classmethod
    def _rewrite(
        cls,
        module: Path,
        outcome: p.Result[t.Cli.ResultValue],
    ) -> Callable[[], p.Result[t.Cli.ResultValue]]:
        """Return an operation that rewrites ``module`` and yields ``outcome``.

        Returns:
            The rewriting operation.

        """

        def operation() -> p.Result[t.Cli.ResultValue]:
            tm.ok(u.Cli.atomic_write_text_file(module, cls.REWRITTEN))
            return outcome

        return operation

    def test_failed_result_restores_rewritten_sources(self, tmp_path: Path) -> None:
        """A failed verdict restores the recorded bytes and names the restore."""
        root, module = self._workspace(tmp_path)

        result = FlextInfraCodemodSemanticApply.run_restoring(
            root,
            self.EMPTY_REPORT,
            (),
            self._rewrite(module, r[t.Cli.ResultValue].fail("phase verdict failed")),
        )

        tm.fail(result, has="phase verdict failed")
        tm.fail(result, has="restored 1 rewritten source(s)")
        tm.that(module.read_text(encoding="utf-8"), eq=self.ORIGINAL)

    def test_raised_failure_restores_and_stays_the_raised_one(
        self,
        tmp_path: Path,
    ) -> None:
        """An exception restores the sources and escapes unchanged."""
        root, module = self._workspace(tmp_path)

        def operation() -> p.Result[t.Cli.ResultValue]:
            tm.ok(u.Cli.atomic_write_text_file(module, self.REWRITTEN))
            msg = "phase raised"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="phase raised"):
            FlextInfraCodemodSemanticApply.run_restoring(
                root,
                self.EMPTY_REPORT,
                (),
                operation,
            )

        tm.that(module.read_text(encoding="utf-8"), eq=self.ORIGINAL)

    def test_successful_run_keeps_its_rewrites(self, tmp_path: Path) -> None:
        """A successful run publishes its rewrites unchanged."""
        root, module = self._workspace(tmp_path)

        result = FlextInfraCodemodSemanticApply.run_restoring(
            root,
            self.EMPTY_REPORT,
            (),
            self._rewrite(module, r[t.Cli.ResultValue].ok(value=True)),
        )

        tm.ok(result)
        tm.that(module.read_text(encoding="utf-8"), eq=self.REWRITTEN)
