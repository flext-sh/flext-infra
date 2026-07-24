"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from flext_tests import tm

from flext_infra import config
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    def test_merge_marks_drift_and_renders_canonical_content(
        self, tmp_path: Path
    ) -> None:
        """Plan a changed merge artifact with canonical and custom keys."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        _ = settings_path.write_text(
            '{"python.languageServer": "None"}\n', encoding="utf-8"
        )

        result = FlextInfraCodegenConform._complete_governed_plans(  # ruff:ignore[private-member-access]
            root, (), config.Infra.codegen
        )

        tm.ok(result)
        plan = next(f for f in result.value if f.path == settings_path)
        tm.that(plan.changed, eq=True)
        tm.that(plan.owner, eq="vscode")
        tm.that(plan.policy, eq="merge")
        doc = json.loads(plan.rendered)
        tm.that(doc["python.languageServer"], eq="None")
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        tm.that(
            doc["python-envs.workspaceSearchPaths"],
            eq=["./.venv", "./*/.venv", "./apps/*/.venv"],
        )

    def test_merge_reaches_fixed_point_after_apply(self, tmp_path: Path) -> None:
        """Replan a written merge artifact with zero residual drift."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        _ = settings_path.write_text("{}\n", encoding="utf-8")
        first = FlextInfraCodegenConform._complete_governed_plans(  # ruff:ignore[private-member-access]
            root, (), config.Infra.codegen
        )
        tm.ok(first)
        plan = next(f for f in first.value if f.path == settings_path)
        _ = settings_path.write_text(plan.rendered, encoding="utf-8")

        second = FlextInfraCodegenConform._complete_governed_plans(  # ruff:ignore[private-member-access]
            root, (), config.Infra.codegen
        )

        tm.ok(second)
        plan_fixed = next(f for f in second.value if f.path == settings_path)
        tm.that(plan_fixed.changed, eq=False)
