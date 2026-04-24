"""Unit tests for FlextInfraRefactorEngine rule dispatch and project scanning."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import (
    FlextInfraRefactorEngine,
    c,
)


class TestsFlextInfraRefactorInfraRefactorEngine:
    """Behavior contract for test_infra_refactor_engine."""

    def test_rule_dispatch_prefers_fix_action_metadata(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        config_path = tmp_path / "settings.yml"
        config_path.write_text("engine: test\n", encoding="utf-8")
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: custom-rule-a\n    enabled: true\n    fix_action: remove\n  - id: custom-rule-b\n    enabled: true\n    fix_action: replace_with_alias\n  - id: custom-rule-c\n    enabled: true\n    fix_action: reorder_methods\n  - id: custom-rule-d2\n    enabled: true\n    fix_action: migrate_to_class_mro\n  - id: custom-rule-e\n    enabled: true\n    fix_action: ensure_future_annotations\n  - id: custom-rule-f\n    enabled: true\n    fix_action: propagate_symbol_renames\n    import_symbol_renames:\n      Old: New\n  - id: custom-rule-g\n    enabled: true\n    fix_action: propagate_signature_migrations\n    signature_migrations:\n      - id: migrate-keyword\n        enabled: true\n        target_simple_names:\n          - run\n        keyword_renames:\n          old: new\n  - id: custom-rule-h\n    enabled: true\n    fix_action: convert_dict_to_mapping_annotations\n".strip()
            + "\n",
            encoding="utf-8",
        )
        engine = FlextInfraRefactorEngine(config_path=config_path)
        result = engine.load_rules()
        assert result.success
        assert len(engine.rule_loader.rules) == 8
        assert [rule_kind for rule_kind, _settings in engine.rule_loader.rules] == [
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL,
            c.Infra.RefactorRuleKind.IMPORT_MODERNIZER,
            c.Infra.RefactorRuleKind.CLASS_RECONSTRUCTOR,
            c.Infra.RefactorRuleKind.MRO_CLASS_MIGRATION,
            c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS,
            c.Infra.RefactorRuleKind.SYMBOL_PROPAGATION,
            c.Infra.RefactorRuleKind.SIGNATURE_PROPAGATION,
            c.Infra.RefactorRuleKind.PATTERN_CORRECTIONS,
        ]

    def test_rule_dispatch_fails_on_invalid_pattern_rule_config(
        self, tmp_path: Path
    ) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        config_path = tmp_path / "settings.yml"
        config_path.write_text("engine: test\n", encoding="utf-8")
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: custom-pattern-rule\n    enabled: true\n    fix_action: remove_redundant_casts\n".strip()
            + "\n",
            encoding="utf-8",
        )
        engine = FlextInfraRefactorEngine(config_path=config_path)
        result = engine.load_rules()
        tm.fail(result)
        assert result.error is not None
        assert "redundant_type_targets" in result.error

    def test_rule_dispatch_ignores_unknown_rule_mapping(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        config_path = tmp_path / "settings.yml"
        config_path.write_text("engine: test\n", encoding="utf-8")
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: custom-unknown-rule\n    enabled: true\n".strip() + "\n",
            encoding="utf-8",
        )
        engine = FlextInfraRefactorEngine(config_path=config_path)
        result = engine.load_rules()
        assert result.success
        assert engine.rule_loader.rules == []

    def test_engine_keeps_file_rules_declarative(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        config_path = tmp_path / "settings.yml"
        config_path.write_text("engine: test\n", encoding="utf-8")
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: custom-import-rule\n    enabled: true\n    fix_action: replace_with_alias\n".strip()
            + "\n",
            encoding="utf-8",
        )
        engine = FlextInfraRefactorEngine(config_path=config_path)
        engine.set_rule_filters(["custom-import-rule"])
        result = engine.load_rules()
        assert result.success
        assert engine.rule_loader.file_rules == []

    def test_rule_dispatch_drops_legacy_id_fallback_mapping(
        self, tmp_path: Path
    ) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        config_path = tmp_path / "settings.yml"
        config_path.write_text("engine: test\n", encoding="utf-8")
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: modernize-import-fallback\n    enabled: true\n".strip()
            + "\n",
            encoding="utf-8",
        )
        engine = FlextInfraRefactorEngine(config_path=config_path)
        result = engine.load_rules()
        assert result.success
        assert engine.rule_loader.rules == []

    def test_refactor_project_scans_tests_and_scripts_dirs(
        self, tmp_path: Path
    ) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: ensure-future-annotations\n    enabled: true\n    fix_action: ensure_future_annotations\n".strip()
            + "\n",
            encoding="utf-8",
        )
        config_path = tmp_path / "settings.yml"
        config_path.write_text(
            "\nrefactor_engine:\n  project_scan_dirs:\n    - tests\n    - scripts\n".strip()
            + "\n",
            encoding="utf-8",
        )
        project_root = tmp_path / "sample"
        tests_dir = project_root / "tests"
        scripts_dir = project_root / "scripts"
        tests_dir.mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        (tests_dir / "test_sample.py").write_text("import os\n", encoding="utf-8")
        (scripts_dir / "task.py").write_text("import sys\n", encoding="utf-8")
        engine = FlextInfraRefactorEngine(config_path=config_path)
        loaded = engine.load_rules()
        assert loaded.success
        results = engine.refactor_project(project_root)
        assert len(results) == 2
        assert all(result.success for result in results)
        assert all(result.modified for result in results)

    def test_refactor_files_skips_non_python_inputs(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rules.yml").write_text(
            "\nrules:\n  - id: ensure-future-annotations\n    enabled: true\n    fix_action: ensure_future_annotations\n".strip()
            + "\n",
            encoding="utf-8",
        )
        config_path = tmp_path / "settings.yml"
        config_path.write_text('refactor_engine:\n  project_scan_dirs: ["src"]\n')
        py_file = tmp_path / "sample.py"
        py_file.write_text("import os\n", encoding="utf-8")
        md_file = tmp_path / "README.md"
        md_file.write_text("# doc\n", encoding="utf-8")
        engine = FlextInfraRefactorEngine(config_path=config_path)
        loaded = engine.load_rules()
        assert loaded.success
        results = engine.refactor_files([py_file, md_file], dry_run=True)
        assert len(results) == 2
        md_result = next(item for item in results if item.file_path == md_file)
        assert md_result.success
        assert not md_result.modified
        assert "Skipped non-Python file" in md_result.changes

    def test_refactor_file_rolls_back_invalid_output_and_preserves_backup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        file_path = tmp_path / "sample.py"
        original = "value = 1\n"
        file_path.write_text(original, encoding="utf-8")
        engine = FlextInfraRefactorEngine(config_path=tmp_path / "missing.yml")
        engine.rule_loader.rules = [
            (
                c.Infra.RefactorRuleKind.LEGACY_REMOVAL,
                {c.Infra.RK_ID: "broken", c.Infra.RK_ENABLED: True},
            )
        ]
        engine.rule_loader.file_rules = []
        monkeypatch.setattr(
            engine.orchestrator,
            "_apply_text_rule_selection",
            lambda kind, settings, source, file_path: (
                "def broken(:\n",
                ["broke syntax"],
            ),
        )

        result = engine.refactor_file(file_path, dry_run=False)

        assert not result.success
        assert not result.modified
        assert file_path.read_text(encoding="utf-8") == original
        assert file_path.with_suffix(".py.bak").exists()
