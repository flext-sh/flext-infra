"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.services.codegen import FlextInfraCodegen
from flext_tests import tm


class TestsVscodeOwnerMerge:
    """Prove the vscode owner merge renders canonical settings in conform."""

    @staticmethod
    def _plan(root: Path) -> m.Infra.CodegenPlan:
        created = FlextInfraCodegenProjectNew(
            name="flext-vscode-owner",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        request = m.Infra.CodegenConformRequest(root=root)
        planned = FlextInfraCodegenConform(workspace_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        return m.Infra.CodegenPlan.model_validate(planned.value)

    def test_merge_marks_drift_and_renders_canonical_content(
        self, infra_git_repo: Path
    ) -> None:
        """Plan a changed merge artifact with canonical and custom keys."""
        root = infra_git_repo
        settings_path = root / ".vscode" / "settings.json"
        _ = self._plan(root)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _ = settings_path.write_text(
            '{"python.languageServer": "None"}\n', encoding="utf-8"
        )

        request = m.Infra.CodegenConformRequest(root=root)
        replanned = tm.ok(
            FlextInfraCodegenConform(workspace_root=root, request=request).plan(request)
        )
        settings_plan = next(f for f in replanned.files if f.path == settings_path)
        tm.that(settings_plan.changed, eq=True)
        tm.that(settings_plan.owner, eq="vscode")
        tm.that(settings_plan.policy, eq="merge")
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(settings_plan.rendered))
        )
        tm.that(doc["python.languageServer"], eq="None")
        tm.that(doc["python.analysis.typeCheckingMode"], eq="strict")
        search_paths = t.Cli.JSON_LIST_ADAPTER.validate_python(
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

    def test_merge_reaches_fixed_point_after_apply(self, infra_git_repo: Path) -> None:
        """Replan a written merge artifact with zero residual drift."""
        root = infra_git_repo
        settings_path = root / ".vscode" / "settings.json"
        _ = self._plan(root)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _ = settings_path.write_text("{}\n", encoding="utf-8")
        request = m.Infra.CodegenConformRequest(root=root)
        changed = tm.ok(
            FlextInfraCodegenConform(workspace_root=root, request=request).plan(request)
        )
        settings_plan = next(f for f in changed.files if f.path == settings_path)
        _ = settings_path.write_text(settings_plan.rendered, encoding="utf-8")
        second = tm.ok(
            FlextInfraCodegenConform(workspace_root=root, request=request).plan(request)
        )
        plan_fixed = next(f for f in second.files if f.path == settings_path)
        tm.that(plan_fixed.changed, eq=False)

    def test_merge_accepts_vscode_jsonc_comments_and_trailing_commas(
        self, tmp_path: Path
    ) -> None:
        """Parse the JSONC syntax supported by VS Code settings files."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        _ = settings_path.write_text(
            (
                "{\n"
                "  // project setting\n"
                '  "editor.formatOnSave": true,\n'
                '  "url": "https://example.test/a//b",\n'
                "}\n"
            ),
            encoding="utf-8",
        )

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(result.value))
        )
        tm.that(doc["editor.formatOnSave"], eq=True)
        tm.that(doc["url"], eq="https://example.test/a//b")

    def test_merge_rejects_invalid_vscode_jsonc_without_rewriting(
        self, tmp_path: Path
    ) -> None:
        """Fail loudly when JSONC remains invalid after lexical normalization."""
        root = tmp_path / "project"
        settings_path = root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        invalid = "{ invalid json"
        _ = settings_path.write_text(invalid, encoding="utf-8")

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.fail(result)
        tm.that(settings_path.read_text(encoding="utf-8"), eq=invalid)
