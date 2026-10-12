"""Focused cProfile report service contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.services import FlextInfraValidationCommandRoutes
from flext_infra.validate import FlextInfraCProfileReport
from tests import c, m, tm, u


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    @staticmethod
    @pytest.mark.parametrize("inventory_only", [False, True])
    def test_real_profile_renders_bounded_text(
        tmp_path: Path,
        *,
        inventory_only: bool,
    ) -> None:
        """Test real profile renders bounded text."""
        policy = config.Infra.tooling.tools.pytest
        repository_root = tmp_path / "project[scope]"
        report_dir = repository_root / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        profile_target = repository_root / "profile_target.py"
        profile_target.write_text("_ = sum(range(10))\n", encoding="utf-8")
        profiled = u.Cli.run_checked(
            [
                sys.executable,
                "-m",
                "cProfile",
                "-o",
                str(profile_path),
                str(profile_target),
            ],
            cwd=repository_root,
        )
        tm.ok(profiled)
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=None,
            deadline_monotonic=None,
            report_directory=report_dir,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                report_dir / "run-context.json",
                context.model_dump_json(),
            ),
        )
        receipt = context.model_copy(
            update={"profile_sha256": u.Cli.sha256_bytes(profile_path.read_bytes())},
        )
        parent_receipt = profile_path.with_suffix(".pstats.json")
        tm.ok(u.Cli.atomic_write_text_file(parent_receipt, receipt.model_dump_json()))
        inventory = report_dir / c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
        selection = report_dir / c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
        for collection in (inventory,) if inventory_only else (selection, inventory):
            collection.write_bytes(profile_path.read_bytes())
            tm.ok(
                u.Cli.atomic_write_text_file(
                    collection.with_suffix(".pstats.json"),
                    receipt.model_dump_json(),
                ),
            )
        plan = m.Infra.PytestSelectionPlan(
            manifest_path=(inventory if inventory_only else selection).with_suffix(
                ".json",
            ),
            node_ids=(),
            whole_target=True,
            inventory_collected=True,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                report_dir / "selection-plan.json",
                plan.model_dump_json(),
            ),
        )

        result = FlextInfraCProfileReport(
            repository_root=repository_root,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
            run_receipt=parent_receipt,
        ).execute()

        tm.ok(result)
        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")
        rendered = output_path.read_text(encoding="utf-8")
        tm.that(rendered, has=f"{profile_target}:1(<module>)")
        tm.that(rendered.count(f"Profile: {inventory}\n"), eq=1)
        tm.that(
            rendered.count(f"Profile: {selection}\n"), eq=0 if inventory_only else 1
        )

    @staticmethod
    def test_validate_route_uses_typed_profile_owner() -> None:
        """Test validate route uses typed profile owner."""
        routes = {
            route.name: route.model_cls
            for route in FlextInfraValidationCommandRoutes.validate_command_routes
        }

        tm.that(routes["cprofile-report"], eq=FlextInfraCProfileReport)

    @staticmethod
    def test_profile_artifacts_cannot_escape_workspace_reports(
        tmp_path: Path,
    ) -> None:
        """Test profile artifacts cannot escape workspace reports."""
        policy = config.Infra.tooling.tools.pytest

        with pytest.raises(ValueError, match="cProfile path must stay under"):
            FlextInfraCProfileReport(
                repository_root=tmp_path,
                profile=tmp_path / "outside.pstats",
                output=tmp_path / "outside.txt",
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            )
