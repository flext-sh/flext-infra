"""Conform never leaks orphan ``-transaction-<hex>`` sibling worktrees (flext-f73ii)."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c
from flext_infra.codegen import FlextInfraCodegenConform
from tests import u
from tests.unit.codegen._helpers import _conformed_root

_TRANSACTION_MARKER = "-transaction-"


def _transaction_worktree_siblings(root: Path) -> tuple[str, ...]:
    """Name sibling directories that look like detached transaction worktrees."""
    return tuple(
        entry.name
        for entry in root.parent.iterdir()
        if entry.is_dir() and _TRANSACTION_MARKER in entry.name
    )


def _seed_committed_drift(tmp_path: Path) -> tuple[Path, Path]:
    """Materialize the managed tree, then commit one drifted managed Makefile.

    Returns the conformed repository root and the drifted file: the shared
    builder owns where the repository lives below ``tmp_path``.
    """
    root = _conformed_root(tmp_path)
    drifted = root / c.Infra.MAKEFILE_FILENAME
    drifted.write_text(
        f"{drifted.read_text(encoding='utf-8')}# managed drift\n", encoding="utf-8"
    )
    u.Tests.commit_git_changes(root, "Seed committed managed drift")
    return root, drifted


@pytest.mark.slow
class TestCodegenConformNeverLeavesTransactionWorktrees:
    """Conform mutates the repository in place; no detached sibling may survive.

    flext-f73ii: the retired isolated-transaction mechanism spawned a sibling
    ``<repo>-transaction-<hex>`` detached worktree and leaked it on the
    drift/error exit path, holding staged generated output in a commit
    unreachable from any branch (one ``git gc`` away from destruction).
    """

    def test_drift_check_error_path_leaves_no_transaction_worktree(
        self, tmp_path: Path
    ) -> None:
        """The read-only drift exit fails loud without spawning any worktree."""
        root, drifted = _seed_committed_drift(tmp_path)
        before = _transaction_worktree_siblings(root)
        drifted_bytes = drifted.read_bytes()

        result = FlextInfraCodegenConform.execute_request(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        tm.fail(result, has="codegen drift detected")
        tm.that(_transaction_worktree_siblings(root), eq=before)
        tm.that(drifted.read_bytes(), eq=drifted_bytes)

    def test_apply_convergence_leaves_no_transaction_worktree(
        self, tmp_path: Path
    ) -> None:
        """The apply path converges in place and never leaks a sibling worktree."""
        root, drifted = _seed_committed_drift(tmp_path)
        before = _transaction_worktree_siblings(root)

        # Convergence is proven behaviorally: the drift marker is rewritten
        # away and a second apply reaches a byte-identical fixed point; the
        # execute return shape is not part of this invariant.
        FlextInfraCodegenConform.execute_request(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.that(drifted.read_text(encoding="utf-8"), lacks="# managed drift")
        converged_bytes = drifted.read_bytes()
        FlextInfraCodegenConform.execute_request(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.that(drifted.read_bytes(), eq=converged_bytes)
        tm.that(_transaction_worktree_siblings(root), eq=before)
