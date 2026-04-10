"""Edge-case tests for public modernizer flows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraPyprojectModernizer
from tests import c, t, u


class TestFlextInfraPyprojectModernizerEdgeCases:
    """Validate edge cases through the public modernizer API."""

    @staticmethod
    def _args(**overrides: t.Infra.InfraValue) -> argparse.Namespace:
        defaults: t.MutableContainerMapping = {
            "project": None,
            "dry_run": False,
            "verbose": False,
            "audit": False,
            "skip_comments": False,
            "skip_check": True,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            pytest.param(None, 2, id="missing-root-pyproject"),
            pytest.param("", 0, id="empty-root-pyproject"),
            pytest.param("[invalid toml {", 2, id="invalid-root-pyproject"),
        ],
    )
    def test_run_handles_root_edge_cases(
        self,
        tmp_path: Path,
        content: str | None,
        expected: int,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (workspace / c.Infra.Files.PYPROJECT_FILENAME).write_text(
                content,
                encoding="utf-8",
            )
        modernizer = FlextInfraPyprojectModernizer(workspace)
        tm.that(
            modernizer.run(
                self._args(),
                u.Infra.CliArgs(workspace=workspace),
            ),
            eq=expected,
        )

    def test_audit_returns_zero_after_workspace_is_canonical(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(modernizer_workspace)
        apply_exit = modernizer.run(
            self._args(skip_comments=True, skip_check=True),
            u.Infra.CliArgs(workspace=modernizer_workspace, apply=True),
        )
        audit_exit = modernizer.run(
            self._args(audit=True, skip_comments=True),
            u.Infra.CliArgs(workspace=modernizer_workspace),
        )
        tm.that(apply_exit, eq=0)
        tm.that(audit_exit, eq=0)
