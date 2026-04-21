"""Project-level integration tests for class nesting file execution."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import c
from flext_infra.refactor.engine_file import FlextInfraRefactorFileExecutor
from tests import m, t, u


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


class TestProjectLevelRefactor:
    """Test class nesting refactor across a project."""

    def test_project_processes_without_errors(self, tmp_path: Path) -> None:
        """Test that full project processes without errors."""
        src_dir = tmp_path / "src" / "test_project"
        src_dir.mkdir(parents=True)
        test_file = src_dir / "dispatcher.py"
        test_file.write_text(
            "\nclass TimeoutEnforcer:\n    pass\n\nclass RateLimiter:\n    pass\n",
        )
        config_file = tmp_path / "mappings.yml"
        config_file.write_text(
            "\nclass_nesting:\n  - loose_name: TimeoutEnforcer\n    current_file: src/test_project/dispatcher.py\n    target_namespace: FlextDispatcher\n    target_name: TimeoutEnforcer\n    confidence: high\n  - loose_name: RateLimiter\n    current_file: src/test_project/dispatcher.py\n    target_namespace: FlextDispatcher\n    target_name: RateLimiter\n    confidence: high\n",
        )
        result = _apply_rule(tmp_path, test_file, config_file, dry_run=True)
        assert result.success
        assert result.modified is True

    def test_no_type_errors_introduced(self, tmp_path: Path) -> None:
        """Verify no type errors are introduced by refactoring."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"
        test_file.write_text(
            "\nfrom typing import Optional\n\nclass Helper:\n    def process(self, x: Optional[int] = None) -> int:\n        return x or 0\n",
        )
        config_file = tmp_path / "mappings.yml"
        config_file.write_text(
            "\nclass_nesting:\n  - loose_name: Helper\n    current_file: src/test.py\n    target_namespace: FlextUtilities\n    target_name: Helper\n    confidence: high\n",
        )
        result = _apply_rule(tmp_path, test_file, config_file, dry_run=True)
        assert result.success
        assert result.refactored_code is not None
        assert (
            "Optional[int]" in result.refactored_code or "int" in result.refactored_code
        )
