"""Unit tests for FlextInfraRefactorSafetyManager integration."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import overload, override

from flext_infra import FlextInfraRefactorEngine, FlextInfraRefactorSafetyManager, t
from tests import p, r, u


class EngineSafetyStub(FlextInfraRefactorSafetyManager):
    """Test double for safety manager lifecycle operations."""

    def __init__(self) -> None:
        """Initialize call capture state for assertions."""
        super().__init__()
        self.calls: MutableSequence[str] = []
        self.kept_paths: Sequence[Path] = []

    @override
    def create_pre_transformation_stash(
        self,
        workspace_root: Path,
        *,
        label: str = "flext-refactor-pre-transform",
    ) -> p.Result[str]:
        _ = workspace_root
        _ = label
        self.calls.append("stash")
        return r[str].ok("stash@{0}")

    @override
    def save_checkpoint_state(
        self,
        workspace_root: Path,
        *,
        status: str,
        stash_ref: str,
        processed_targets: t.StrSequence,
    ) -> p.Result[bool]:
        _ = workspace_root
        _ = status
        _ = stash_ref
        _ = processed_targets
        self.calls.append("checkpoint")
        return r[bool].ok(True)

    @override
    def run_semantic_validation(self, workspace_root: Path) -> p.Result[bool]:
        _ = workspace_root
        self.calls.append("validate")
        return r[bool].ok(True)

    @override
    def clear_checkpoint(self, *, keep: Sequence[Path] = ()) -> p.Result[bool]:
        self.kept_paths = list(keep)
        self.calls.append("clear")
        return r[bool].ok(True)

    @override
    def request_emergency_stop(self, reason: str) -> None:
        _ = reason
        self.calls.append("stop")

    @overload
    def rollback(self, workspace_root: Path, stash_ref: str = "") -> p.Result[bool]: ...

    @overload
    def rollback(self, workspace_root: str, /) -> None: ...

    @override
    def rollback(
        self,
        workspace_root: Path | str,
        stash_ref: str = "",
    ) -> p.Result[bool] | None:
        _ = stash_ref
        self.calls.append("rollback")
        if isinstance(workspace_root, Path):
            return r[bool].ok(True)
        return None

    @override
    def is_emergency_stop_requested(self) -> bool:
        self.calls.append("is_stop")
        return False


def test_refactor_project_integrates_safety_manager(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "rules.yml").write_text(
        "\nrules:\n  - id: ensure-future-annotations\n    enabled: true\n    fix_action: ensure_future_annotations\n".strip()
        + "\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "settings.yml"
    config_path.write_text('refactor_engine:\n  project_scan_dirs: ["src"]\n')
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "sample.py").write_text("import os\n", encoding="utf-8")
    engine = FlextInfraRefactorEngine(config_path=config_path)
    stub = EngineSafetyStub()
    engine.orchestrator.safety_manager = stub
    loaded = engine.load_rules()
    assert loaded.success
    results = engine.refactor_project(tmp_path, dry_run=False, apply_safety=True)
    assert results
    assert all(item.success for item in results)
    assert stub.calls == ["stash", "checkpoint", "validate", "clear"]
    assert stub.kept_paths == [src_dir / "sample.py"]


def test_clear_checkpoint_preserves_requested_backups(tmp_path: Path) -> None:
    keep_file = tmp_path / "keep.py"
    drop_file = tmp_path / "drop.py"
    keep_file.write_text("value = 1\n", encoding="utf-8")
    drop_file.write_text("value = 2\n", encoding="utf-8")
    manager = FlextInfraRefactorSafetyManager()
    created = manager.create_pre_transformation_stash(tmp_path)
    assert created.success

    cleared = manager.clear_checkpoint(keep=[keep_file])

    assert cleared.success
    assert keep_file.with_suffix(".py.bak").exists()
    assert not drop_file.with_suffix(".py.bak").exists()


def test_create_pre_transformation_stash_ignores_untracked_git_python_files(
    tmp_path: Path,
) -> None:
    init_result = u.Cli.run_raw(["git", "init"], cwd=tmp_path)
    assert init_result.success
    assert init_result.value.exit_code == 0
    email_result = u.Cli.run_raw(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
    )
    assert email_result.success
    assert email_result.value.exit_code == 0
    name_result = u.Cli.run_raw(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
    )
    assert name_result.success
    assert name_result.value.exit_code == 0
    tracked_file = tmp_path / "tracked.py"
    tracked_file.write_text("value = 1\n", encoding="utf-8")
    untracked_file = tmp_path / "untracked.py"
    untracked_file.write_text("value = 2\n", encoding="utf-8")
    add_result = u.Cli.run_raw(["git", "add", "tracked.py"], cwd=tmp_path)
    assert add_result.success
    assert add_result.value.exit_code == 0
    manager = FlextInfraRefactorSafetyManager()

    created = manager.create_pre_transformation_stash(tmp_path)

    assert created.success
    assert tracked_file.with_suffix(".py.bak").exists()
    assert not untracked_file.with_suffix(".py.bak").exists()
