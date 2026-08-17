"""Runtime behavior tests for generated lazy package artifacts."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from flext_tests import tm
from tests import c, u


class TestsFlextInfraLazyInitRuntime:
    """Exercise generated roots through Python's real import machinery."""

    @staticmethod
    def _generate_package(tmp_path: Path) -> tuple[Path, Path]:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-runtime", package_name="flext_runtime"
        )
        package_root.joinpath("api.py").write_text(
            "from pathlib import Path\n"
            "COUNTER = Path(__file__).with_name('imports.txt')\n"
            "COUNTER.write_text(COUNTER.read_text() + 'x' if COUNTER.exists() else 'x')\n"
            "class FlextDemo:\n    pass\n"
            "primary = FlextDemo\n"
            "__all__ = ('FlextDemo', 'primary')\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        return workspace_root, package_root

    def test_generated_root_preserves_lazy_runtime_contract(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, package_root = self._generate_package(tmp_path)
        monkeypatch.syspath_prepend(str(workspace_root / c.Infra.DEFAULT_SRC_DIR))

        package = importlib.import_module("flext_runtime")

        tm.that("flext_runtime.api" in sys.modules, eq=False)
        tm.that(package.__all__, eq=("FlextDemo", "primary", "runtime"))
        tm.that(dir(package), eq=list(package.__all__))
        first = package.FlextDemo
        second = package.FlextDemo
        tm.that(first is second, eq=True)
        tm.that(package.primary is first, eq=True)
        tm.that(package_root.joinpath("imports.txt").read_text(), eq="x")

    def test_generated_root_preserves_import_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-failure", package_name="flext_failure"
        )
        package_root.joinpath("api.py").write_text(
            "raise ModuleNotFoundError('missing runtime dependency')\n"
            "class FlextDemo:\n    pass\n"
            "__all__ = ('FlextDemo',)\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        monkeypatch.syspath_prepend(str(workspace_root / c.Infra.DEFAULT_SRC_DIR))
        package = importlib.import_module("flext_failure")

        with pytest.raises(ModuleNotFoundError, match="missing runtime dependency"):
            _ = package.FlextDemo


__all__: list[str] = ["TestsFlextInfraLazyInitRuntime"]
