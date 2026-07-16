"""Integration test for single-file class-nesting execution flow.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override

import pytest
from flext_tests import tm

from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader
from flext_infra.refactor.orchestrator import FlextInfraRefactorOrchestrator
from tests import m, t, u

pytestmark = [pytest.mark.integration]


class _FileRuleHarness(FlextInfraRefactorOrchestrator):
    def __init__(self, loader: FlextInfraRefactorRuleLoader, config_path: Path) -> None:
        super().__init__(loader)
        self._config_path = config_path

    @override
    def _load_class_nesting_config(self) -> t.Infra.ContainerDict:
        return u.Cli.yaml_load_mapping(self._config_path)


def _apply_rule(
    workspace_root: Path, file_path: Path, config_path: Path, *, dry_run: bool
) -> p.Infra.Result:
    rules_dir = workspace_root / "rules"
    rules_dir.mkdir()
    (rules_dir / "class-nesting.yml").write_text(
        "rules:\n"
        "  - id: class-nesting-refactor\n"
        "    enabled: true\n"
        "    fix_action: nest_classes\n",
        encoding="utf-8",
    )
    settings_path = workspace_root / "settings.yml"
    settings_path.write_text("refactor: {}\n", encoding="utf-8")
    loader = FlextInfraRefactorRuleLoader(settings_path)
    loaded = loader.load_rules()
    if loaded.failure:
        raise RuntimeError(loaded.error or "Unable to load class-nesting rule")
    rule = _FileRuleHarness(loader, config_path)
    return rule.refactor_file(file_path, dry_run=dry_run, gates=())


class TestsFlextInfraIntegrationRefactorNestingFile:
    """Behavior contract for test_refactor_nesting_file."""

    def test_class_nesting_refactor_single_file_end_to_end(
        self, tmp_path: Path
    ) -> None:
        """Verify class nesting refactor handles unknown module families gracefully."""
        fixture_file = (
            Path(__file__).parent.parent
            / "fixtures/namespace_validator/rule0_valid.pysrc"
        )
        source = fixture_file.read_text(encoding="utf-8")
        target_dir = tmp_path / "nonstandard_dir"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "single_file_refactor_target.py"
        target_file.write_text(
            source
            + "\n\n"
            + "class ResultHelpers:\n"
            + "    pass\n\n"
            + "def build(value: ResultHelpers) -> ResultHelpers:\n"
            + "    if isinstance(value, ResultHelpers):\n"
            + "        return ResultHelpers()\n"
            + "    return value\n",
            encoding="utf-8",
        )
        config_path = tmp_path / "class-nesting-mappings.yml"
        config_path.write_text(
            "confidence_threshold: low\n"
            "class_nesting:\n"
            "  - loose_name: ResultHelpers\n"
            f"    current_file: {target_file.as_posix()}\n"
            "    target_namespace: FlextUtilities\n"
            "    target_name: ResultHelpers\n"
            "    confidence: high\n"
            "helper_consolidation: []\n",
            encoding="utf-8",
        )
        result = _apply_rule(tmp_path, target_file, config_path, dry_run=False)
        # Module family policy treats unknown families as out-of-scope (no policy
        # to enforce against), so the refactor proceeds gracefully and the loose
        # ``ResultHelpers`` class is nested under ``FlextUtilities`` per the
        # mapping config.
        tm.that(result.success, eq=True)
        tm.that(result.modified, eq=True)
        tm.that(result.refactored_code, none=False)
        tm.that(result.refactored_code, has="class FlextUtilities:")
        tm.that(result.refactored_code, has="class ResultHelpers:")
