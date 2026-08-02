"""Behavior tests for fix-forward refactor execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.refactor.service import FlextInfraRefactorService
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorFixForward:
    """Verify successful mutations remain applied when another file fails."""

    def test_refactor_files_keeps_converged_changes_without_backups(
        self, tmp_path: Path
    ) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n"
            "  - id: ensure-future-annotations\n"
            "    enabled: true\n"
            "    fix_action: ensure_future_annotations\n".strip()
            + "\n",
            encoding="utf-8",
        )
        config_path = tmp_path / "settings.yml"
        config_path.write_text(
            'refactor:\n  project_scan_dirs: ["src"]\n', encoding="utf-8"
        )
        converged_file = tmp_path / "converged.py"
        converged_file.write_text("import os\n", encoding="utf-8")
        missing_file = tmp_path / "missing.py"
        service = FlextInfraRefactorService(config_path=config_path)
        loaded = service.load_rules()
        tm.ok(loaded)

        converged, failed = service.refactor_files([converged_file, missing_file])

        tm.that(converged.success, eq=True)
        tm.that(converged.modified, eq=True)
        tm.that(failed.success, eq=False)
        tm.that(
            converged_file.read_text(encoding="utf-8"),
            has="from __future__ import annotations",
        )
        tm.that(converged_file.with_suffix(".py.bak").exists(), eq=False)


__all__: list[str] = []
