"""Shared conformance helpers for codegen tests."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c
from flext_infra.codegen import FlextInfraCodegenConform
from tests import u
from tests.unit.workspace import WorktreeFixture


def _conformed_root(tmp_path: Path) -> Path:
    """Materialize one governed project and conform it to a fixed point."""
    root = tmp_path / "repo"
    WorktreeFixture.initialize_governed_project(
        root,
        "fixture-project",
        workspace="fixture-workspace",
        database="fixture-database",
        issue_prefix="fixture-prefix",
    )
    u.Tests.commit_git_changes(root, "Declare project identity")
    tm.ok(
        FlextInfraCodegenConform.execute_request(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
    )
    return root
