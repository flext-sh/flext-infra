"""Owner-merge dispatch for governed .vscode/settings.json artifacts."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, t, u
from flext_infra.services.codegen import FlextInfraCodegen


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

        result = FlextInfraCodegen.render_vscode_settings(root)

        tm.ok(result)
        doc = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.json_parse(result.value))
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

    def test_merge_reaches_fixed_point_after_apply(self, tmp_path: Path) -> None:
        """Replan a written merge artifact with zero residual drift."""
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
