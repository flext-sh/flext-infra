"""Tests for rope Project initialization and hook infrastructure on FlextInfraRefactorEngine."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flext_infra import m
from flext_infra.refactor.engine import FlextInfraRefactorEngine


@pytest.fixture
def engine() -> FlextInfraRefactorEngine:
    """Create a fresh engine instance."""
    return FlextInfraRefactorEngine()


@pytest.fixture
def fake_workspace(tmp_path: Path) -> Path:
    """Create a fake workspace with flext-* project dirs containing src/."""
    for name in ("flext-core", "flext-api", "flext-cli"):
        (tmp_path / name / "src").mkdir(parents=True)
    # non-flext dir should be excluded
    (tmp_path / "docs" / "src").mkdir(parents=True)
    # flext dir without src/ should be excluded
    (tmp_path / "flext-empty").mkdir()
    return tmp_path


class TestInitRopeProject:
    """Tests for _init_rope_project method."""

    def test_creates_project_with_ropefolder_none(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """_init_rope_project creates Project with ropefolder=None."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            engine._init_rope_project(fake_workspace)
            call_kwargs = mock_project.call_args
            assert call_kwargs.kwargs.get("ropefolder") is None

    def test_creates_project_with_save_objectdb_false(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """_init_rope_project sets save_objectdb=False."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            engine._init_rope_project(fake_workspace)
            call_kwargs = mock_project.call_args
            assert call_kwargs.kwargs.get("save_objectdb") is False

    def test_ignored_resources_includes_required_patterns(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """_init_rope_project ignored_resources includes .venv, *.pyc, dist/, __pycache__, .mypy_cache, .git."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            engine._init_rope_project(fake_workspace)
            ignored = mock_project.call_args.kwargs.get("ignored_resources", [])
            for pattern in (
                ".venv",
                "*.pyc",
                "dist/",
                "__pycache__",
                ".mypy_cache",
                ".git",
            ):
                assert pattern in ignored, f"{pattern} not in ignored_resources"

    def test_source_folders_includes_existing_flext_src_dirs(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """_init_rope_project source_folders includes all flext-*/src dirs that exist."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            engine._init_rope_project(fake_workspace)
            source_folders = mock_project.call_args.kwargs.get("source_folders", [])
            expected = sorted([
                str(fake_workspace / "flext-api" / "src"),
                str(fake_workspace / "flext-cli" / "src"),
                str(fake_workspace / "flext-core" / "src"),
            ])
            assert sorted(source_folders) == expected

    def test_source_folders_excludes_non_flext_dirs(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """Non-flext dirs and flext dirs without src/ are excluded from source_folders."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            engine._init_rope_project(fake_workspace)
            source_folders = mock_project.call_args.kwargs.get("source_folders", [])
            assert str(fake_workspace / "docs" / "src") not in source_folders
            assert str(fake_workspace / "flext-empty" / "src") not in source_folders


class TestRopeProjectProperty:
    """Tests for rope_project property."""

    def test_rope_project_none_before_init(
        self, engine: FlextInfraRefactorEngine
    ) -> None:
        """rope_project returns None before _init_rope_project is called."""
        assert engine.rope_project is None

    def test_rope_project_returns_project_after_init(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """rope_project returns Project instance after _init_rope_project."""
        with patch("flext_infra._utilities.rope.RopeProject") as mock_project:
            mock_instance = MagicMock()
            mock_project.return_value = mock_instance
            engine._init_rope_project(fake_workspace)
            assert engine.rope_project is mock_instance


class TestRopeHooks:
    """Tests for pre/post hook methods."""

    def test_pre_hooks_returns_empty_sequence(
        self, engine: FlextInfraRefactorEngine, tmp_path: Path
    ) -> None:
        """_run_rope_pre_hooks returns empty sequence (stub for Plan 02)."""
        results = engine._run_rope_pre_hooks(tmp_path, dry_run=False)
        assert isinstance(results, Sequence)
        assert len(results) == 0

    def test_post_hooks_returns_empty_sequence(
        self, engine: FlextInfraRefactorEngine, tmp_path: Path
    ) -> None:
        """_run_rope_post_hooks returns empty sequence (stub for Plan 02)."""
        results = engine._run_rope_post_hooks(tmp_path, dry_run=False)
        assert isinstance(results, Sequence)
        assert len(results) == 0

    def test_dry_run_passed_to_hooks(
        self, engine: FlextInfraRefactorEngine, tmp_path: Path
    ) -> None:
        """Hooks accept dry_run parameter without error."""
        pre = engine._run_rope_pre_hooks(tmp_path, dry_run=True)
        post = engine._run_rope_post_hooks(tmp_path, dry_run=True)
        assert len(pre) == 0
        assert len(post) == 0


class TestHookCallOrdering:
    """Test that hooks are called in correct order around refactor_files."""

    def test_hook_call_ordering_in_refactor_project(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """refactor_project calls pre_hooks -> refactor_files -> post_hooks in order."""
        call_order: list[str] = []

        def mock_pre(*_args: object, **_kwargs: object) -> list[m.Infra.Result]:
            call_order.append("pre")
            return []

        def mock_refactor_files(
            *_args: object, **_kwargs: object
        ) -> list[m.Infra.Result]:
            call_order.append("refactor")
            return []

        def mock_post(*_args: object, **_kwargs: object) -> list[m.Infra.Result]:
            call_order.append("post")
            return []

        engine._run_rope_pre_hooks = mock_pre
        engine.refactor_files = mock_refactor_files
        engine._run_rope_post_hooks = mock_post

        # Patch safety stash and file iteration to avoid real filesystem ops
        engine._try_safety_stash = MagicMock(return_value=("", None))

        with (
            patch.object(
                engine.rule_loader, "extract_project_scan_dirs", return_value=[]
            ),
            patch.object(
                engine.rule_loader, "extract_engine_file_filters", return_value=([], [])
            ),
            patch("flext_infra.refactor.engine.u") as mock_u,
        ):
            mock_u.Infra.iter_python_files.return_value = MagicMock(
                is_failure=False, value=[]
            )
            mock_u.Infra.refactor_info = MagicMock()
            engine.refactor_project(fake_workspace, dry_run=True, apply_safety=False)

        assert call_order == ["pre", "refactor", "post"]

    def test_hook_call_ordering_in_refactor_workspace(
        self, engine: FlextInfraRefactorEngine, fake_workspace: Path
    ) -> None:
        """refactor_workspace calls pre_hooks before and post_hooks after project loop."""
        call_order: list[str] = []

        def mock_pre(*_args: object, **_kwargs: object) -> list[m.Infra.Result]:
            call_order.append("pre")
            return []

        def mock_refactor_project(
            *_args: object, **_kwargs: object
        ) -> list[m.Infra.Result]:
            call_order.append("project")
            return []

        def mock_post(*_args: object, **_kwargs: object) -> list[m.Infra.Result]:
            call_order.append("post")
            return []

        engine._run_rope_pre_hooks = mock_pre
        engine.refactor_project = mock_refactor_project
        engine._run_rope_post_hooks = mock_post
        engine._try_safety_stash = MagicMock(return_value=("", None))

        with patch("flext_infra.refactor.engine.u") as mock_u:
            mock_u.Infra.discover_project_roots.return_value = [
                fake_workspace / "flext-core"
            ]
            mock_u.Infra.refactor_info = MagicMock()
            mock_u.Infra.refactor_header = MagicMock()
            engine.refactor_workspace(fake_workspace, dry_run=True, apply_safety=False)

        assert call_order == ["pre", "project", "post"]
