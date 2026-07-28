"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestsVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def _plan(root: Path, settings: str) -> m.Infra.CodegenPlan:
        """Plan the governed surface through the public conform contract."""
        pyproject = tm.ok(u.Cli.files_read_text(Path.cwd() / "pyproject.toml"))
        tm.ok(u.Cli.atomic_write_text_file(root / "pyproject.toml", pyproject))
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        tm.ok(
            u.Cli.atomic_write_text_file(root / ".vscode" / "settings.json", settings)
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed VS Code settings"], cwd=root
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        planned = FlextInfraCodegenConform(workspace_root=root).plan(request)
        tm.ok(planned)
        return m.Infra.CodegenPlan.model_validate(planned.value)

    def test_merge_marks_drift_and_renders_canonical_content(
        self, infra_git_repo: Path
    ) -> None:
        """Plan a changed merge artifact with canonical and custom keys."""
        root = infra_git_repo
        settings_path = root / ".vscode" / "settings.json"
        result = self._plan(root, '{"python.languageServer": "None"}\n')

        plan = next(f for f in result.files if f.path == settings_path)
        tm.that(plan.changed, eq=True)
        tm.that(plan.owner, eq="vscode")
        tm.that(plan.policy, eq="merge")
        doc = json.loads(plan.rendered)
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

    def test_merge_reaches_fixed_point_after_apply(self, infra_git_repo: Path) -> None:
        """Replan a written merge artifact with zero residual drift."""
        root = infra_git_repo
        settings_path = root / ".vscode" / "settings.json"
        first = self._plan(root, "{}\n")
        plan = next(f for f in first.files if f.path == settings_path)
        tm.ok(u.Cli.atomic_write_text_file(settings_path, plan.rendered))
        tm.ok(u.Cli.run_checked(["git", "add", settings_path.as_posix()], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Apply VS Code settings"], cwd=root
            )
        )
        request = first.request.model_copy(
            update={"mode": c.Infra.CodegenConformMode.CHECK}
        )
        second = tm.ok(FlextInfraCodegenConform(workspace_root=root).plan(request))

        plan_fixed = next(f for f in second.files if f.path == settings_path)
        tm.that(plan_fixed.changed, eq=False)
