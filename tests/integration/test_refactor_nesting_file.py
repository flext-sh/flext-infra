"""Integration test for single-file class-nesting execution flow."""

from __future__ import annotations

from pathlib import Path
from typing import override

import pytest

from flext_infra import FlextInfraRefactorFileExecutor, c
from tests import m, t, u

pytestmark = [pytest.mark.integration]


class _FileRuleHarness(FlextInfraRefactorFileExecutor):
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._class_nesting_config = None
        self._class_nesting_policy_by_family = None
        self._class_nesting_gate = None

    @override
    def _load_class_nesting_config(self) -> t.Infra.ContainerDict:
        return u.Cli.yaml_load_mapping(self._config_path)


def _apply_rule(
    workspace_root: Path,
    file_path: Path,
    config_path: Path,
    *,
    dry_run: bool,
) -> m.Infra.Result:
    rule = _FileRuleHarness(config_path)
    rope_project = u.Infra.init_rope_project(workspace_root)
    try:
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            raise FileNotFoundError(file_path)
        return rule._apply_file_rule_selection(
            c.Infra.RefactorFileRuleKind.CLASS_NESTING,
            {},
            rope_project,
            resource,
            dry_run=dry_run,
        )
    finally:
        rope_project.close()


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
        utilities_dir = tmp_path / "_utilities"
        utilities_dir.mkdir(parents=True, exist_ok=True)
        target_file = utilities_dir / "single_file_refactor_target.py"
        target_file.write_text(
            source
            + "\n\n"
            + "from pkg import ResultHelpers\n\n"
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
            f"confidence_threshold: low\nclass_nesting:\n  - loose_name: ResultHelpers\n    current_file: {target_file.as_posix()}\n    target_namespace: FlextUtilities\n    target_name: ResultHelpers\n    confidence: high\nhelper_consolidation: []\n",
            encoding="utf-8",
        )
        result = _apply_rule(tmp_path, target_file, config_path, dry_run=False)
        # Module family policy rejects temp paths as unknown_module_family
        assert not result.success
        assert result.changes
        assert any("unknown_module_family" in v for v in result.changes)
