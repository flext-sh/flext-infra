"""Tests for FlextInfraCodegenPyTyped.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from tests import c, t


class TestsFlextInfraCodegenPyTyped:
    def test_creates_marker_in_dir_with_py_files(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 1
        assert (pkg / c.Infra.PY_TYPED).exists()

    def test_removes_stale_marker_when_no_py_files(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "emptypkg"
        pkg.mkdir(parents=True)
        (pkg / c.Infra.PY_TYPED).touch()
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 1
        assert not (pkg / c.Infra.PY_TYPED).exists()

    def test_check_only_does_not_write_marker(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run(check_only=True)

        assert count == 1
        assert not (pkg / c.Infra.PY_TYPED).exists()

    def test_check_only_does_not_remove_marker(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "emptypkg"
        pkg.mkdir(parents=True)
        (pkg / c.Infra.PY_TYPED).touch()
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run(check_only=True)

        assert count == 1
        assert (pkg / c.Infra.PY_TYPED).exists()

    @pytest.mark.parametrize("skip_dir", tuple(c.Tests.CODEGEN_SKIPPED_DIRS))
    def test_skips_known_excluded_directories(
        self, tmp_path: Path, skip_dir: str
    ) -> None:
        skipped_pkg = tmp_path / "src" / skip_dir / "mypkg"
        skipped_pkg.mkdir(parents=True)
        (skipped_pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 0
        assert not (skipped_pkg / c.Infra.PY_TYPED).exists()

    def test_no_change_when_marker_already_exists(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / c.Infra.PY_TYPED).touch()
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 0

    def test_execute_returns_success(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        result = svc.execute()

        assert result.success

    def test_tests_dir_packages_also_scanned(self, tmp_path: Path) -> None:
        test_pkg = tmp_path / "tests" / "unit"
        test_pkg.mkdir(parents=True)
        (test_pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 1
        assert (test_pkg / c.Infra.PY_TYPED).exists()

    def test_skips_nested_hidden_virtualenv_directories(self, tmp_path: Path) -> None:
        venv_pkg = tmp_path / "src" / ".cache" / ".venv" / "mypkg"
        venv_pkg.mkdir(parents=True)
        (venv_pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 0

    def test_only_expected_namespace_marker_is_created(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 1
        assert (pkg / c.Infra.PY_TYPED).exists()
        for namespace_file in c.Tests.CODEGEN_NAMESPACE_FILES - {
            c.Infra.PY_TYPED,
            c.Infra.INIT_PY,
        }:
            assert not (pkg / namespace_file).exists()

    def test_multiple_packages_all_get_markers(self, tmp_path: Path) -> None:
        for name in ("pkga", "pkgb", "pkgc"):
            pkg = tmp_path / "src" / name
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
        svc = FlextInfraCodegenPyTyped.model_validate({"workspace_root": tmp_path})

        count = svc.run()

        assert count == 3
        for name in ("pkga", "pkgb", "pkgc"):
            assert (tmp_path / "src" / name / c.Infra.PY_TYPED).exists()


__all__: t.StrSequence = []
