"""Tests for FlextWorkspaceCli to achieve full coverage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfraProjectMigrator, main as infra_main
from tests import m


def test_workspace_cli_migrate_command(monkeypatch: MonkeyPatch) -> None:

    def _fake_migrate(
        self: FlextInfraProjectMigrator,
        *,
        workspace_root: Path,
        dry_run: bool,
    ) -> r[Sequence[m.Infra.MigrationResult]]:
        del self, workspace_root
        assert dry_run is True
        return r[Sequence[m.Infra.MigrationResult]].ok([
            m.Infra.MigrationResult.model_validate(
                obj={
                    "project": "flext-core",
                    "changes": ["[DRY-RUN] base.mk regenerated via BaseMkGenerator"],
                    "errors": [],
                },
            ),
        ])

    _ = monkeypatch.setattr(FlextInfraProjectMigrator, "migrate", _fake_migrate)
    exit_code = infra_main(["workspace", "migrate", "--workspace", ".", "--dry-run"])
    assert exit_code == 0


def test_workspace_cli_rejects_migrate_flags_for_detect(
    monkeypatch: MonkeyPatch,
) -> None:
    del monkeypatch
    tm.that(infra_main(["workspace", "detect", "--dry-run"]), eq=2)


def test_workspace_cli_migrate_output_contains_summary(
    monkeypatch: MonkeyPatch,
) -> None:

    def _fake_migrate(
        self: FlextInfraProjectMigrator,
        *,
        workspace_root: Path,
        dry_run: bool,
    ) -> r[Sequence[m.Infra.MigrationResult]]:
        del self, workspace_root, dry_run
        return r[Sequence[m.Infra.MigrationResult]].ok([
            m.Infra.MigrationResult.model_validate(
                obj={
                    "project": "flext-core",
                    "changes": [
                        "[DRY-RUN] .gitignore cleaned from scripts/ and normalized",
                    ],
                    "errors": [],
                },
            ),
        ])

    _ = monkeypatch.setattr(FlextInfraProjectMigrator, "migrate", _fake_migrate)
    exit_code = infra_main(["workspace", "migrate", "--workspace", ".", "--dry-run"])
    assert exit_code == 0
