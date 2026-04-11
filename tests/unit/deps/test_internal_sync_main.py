from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import main


class TestMain:
    def test_main_success(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        tm.that(
            main(["deps", "internal-sync", "--workspace", str(tmp_path)]),
            eq=0,
        )

    def test_main_failure(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "not [toml",
            encoding="utf-8",
        )
        tm.that(
            main(["deps", "internal-sync", "--workspace", str(tmp_path)]),
            eq=1,
        )
