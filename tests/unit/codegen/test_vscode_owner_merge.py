"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config
from flext_infra.services.codegen import FlextInfraCodegen


class TestsVscodeOwnerMerge:
    """Prove the public VS Code owner reaches canonical merged content."""

    def test_merge_marks_drift_and_renders_canonical_content(
        self, tmp_path: Path
    ) -> None:
        """Render canonical settings while preserving a consumer-owned key."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        _ = settings_path.write_text(
            '{"python.languageServer": "None"}\n', encoding="utf-8"
        )

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = json.loads(result.value)
        tm.that(doc["python.languageServer"], eq="None")
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        search_paths = doc[c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY]
        tm.that(
            search_paths,
            eq=list(
                config.Infra.codegen.vscode.list_settings[
                    c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY
                ]
            ),
        )
        tm.that("./apps/*/.venv" in search_paths, eq=False)

    def test_merge_reaches_fixed_point_after_apply(self, tmp_path: Path) -> None:
        """Render a written canonical document to the same fixed point."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        _ = settings_path.write_text("{}\n", encoding="utf-8")
        first = FlextInfraCodegen.render_vscode_settings(root)
        tm.ok(first)
        _ = settings_path.write_text(first.value, encoding="utf-8")

        second = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(second)
        tm.that(second.value, eq=first.value)
