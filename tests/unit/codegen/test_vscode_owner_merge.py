"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, t, u
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
        raw_plan = tm.ok(FlextInfraCodegenConform(workspace_root=root).plan(request))
        return m.Infra.CodegenPlan.model_validate(raw_plan)

    def test_merge_marks_drift_and_renders_canonical_content(
        self, infra_git_repo: Path
    ) -> None:
        """Plan a changed merge artifact with canonical and custom keys."""
        root = infra_git_repo
        settings_path = root / ".vscode" / "settings.json"
        result = self._plan(root, '{"python.languageServer": "None"}\n')

        plan = next(file for file in result.files if file.path == settings_path)
        tm.that(plan.changed, eq=True)
        tm.that(plan.owner, eq="vscode")
        tm.that(plan.policy, eq="merge")
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(plan.rendered))
        )
        tm.that(doc["python.languageServer"], eq="None")
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        search_paths = t.Infra.STR_SEQ_ADAPTER.validate_python(
            doc[c.Infra.VSCODE_PYTHON_ENVS_SEARCH_PATHS_KEY]
        )
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
        plan = next(file for file in first.files if file.path == settings_path)
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

        plan_fixed = next(file for file in second.files if file.path == settings_path)
        tm.that(plan_fixed.changed, eq=False)
