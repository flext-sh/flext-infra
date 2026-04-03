"""Unit tests for class reconstructor, symbol and signature propagation rules."""

from __future__ import annotations

from flext_infra import (
    FlextInfraRefactorClassReconstructorRule,
    FlextInfraRefactorSignaturePropagationRule,
    FlextInfraRefactorSymbolPropagationRule,
)


def test_class_reconstructor_reorders_methods_by_config() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    def __init__(self) -> None:\n        return None\n\n    def a(self) -> None:\n        return None\n"
    rule = FlextInfraRefactorClassReconstructorRule({
        "id": "reorder-class-methods",
        "method_order": [
            {"category": "magic", "patterns": ["^__.+__$"]},
            {"category": "public", "visibility": "public"},
        ],
    })
    updated, _ = rule.apply(source)
    assert updated.index("def __init__") < updated.index("def a")
    assert updated.index("def a") < updated.index("def b")


def test_class_reconstructor_skips_interleaved_non_method_members() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    alias = b\n\n    def a(self) -> None:\n        return None\n"
    rule = FlextInfraRefactorClassReconstructorRule({
        "id": "reorder-class-methods",
        "method_order": [
            {"category": "magic", "patterns": ["^__.+__$"]},
            {"category": "public", "visibility": "public"},
        ],
    })
    updated, _ = rule.apply(source)
    assert updated == source


def test_class_reconstructor_reorders_each_contiguous_method_block() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    def a(self) -> None:\n        return None\n\n    alias = a\n\n    def d(self) -> None:\n        return None\n\n    def c(self) -> None:\n        return None\n"
    rule = FlextInfraRefactorClassReconstructorRule({
        "id": "reorder-class-methods",
        "method_order": [{"category": "public", "visibility": "public"}],
    })
    updated, _ = rule.apply(source)
    assert updated.index("def a") < updated.index("def b")
    assert updated.index("def c") < updated.index("def d")
    assert "alias = a" in updated


def test_symbol_propagation_renames_import_and_local_references() -> None:
    source = (
        "from flext_infra import LegacyRemovalRule\n\nrule_cls = LegacyRemovalRule\n"
    )
    rule = FlextInfraRefactorSymbolPropagationRule({
        "id": "propagate-refactor-api-renames",
        "fix_action": "propagate_symbol_renames",
        "target_modules": ["flext_infra"],
        "import_symbol_renames": {
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    })
    updated, _ = rule.apply(source)
    assert "from flext_infra import FlextInfraRefactorLegacyRemovalRule" in updated
    assert "rule_cls = FlextInfraRefactorLegacyRemovalRule" in updated


def test_symbol_propagation_keeps_alias_reference_when_asname_used() -> None:
    source = (
        "from flext_infra import LegacyRemovalRule as Legacy\n\nrule_cls = Legacy\n"
    )
    rule = FlextInfraRefactorSymbolPropagationRule({
        "id": "propagate-refactor-api-renames",
        "fix_action": "propagate_symbol_renames",
        "target_modules": ["flext_infra"],
        "import_symbol_renames": {
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    })
    updated, _ = rule.apply(source)
    assert (
        "from flext_infra import FlextInfraRefactorLegacyRemovalRule as Legacy"
        in updated
    )
    assert "rule_cls = Legacy" in updated


def test_symbol_propagation_updates_mro_base_references() -> None:
    source = "from flext_infra import LegacyRemovalRule\n\nclass RuleV2(LegacyRemovalRule):\n    pass\n"
    rule = FlextInfraRefactorSymbolPropagationRule({
        "id": "propagate-refactor-api-renames",
        "fix_action": "propagate_symbol_renames",
        "target_modules": ["flext_infra"],
        "import_symbol_renames": {
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    })
    updated, _ = rule.apply(source)
    assert "class RuleV2(FlextInfraRefactorLegacyRemovalRule):" in updated


def test_signature_propagation_renames_call_keyword() -> None:
    source = "result = migrate(project_root=root, dry_run=True)\n"
    rule = FlextInfraRefactorSignaturePropagationRule({
        "id": "propagate-refactor-signature-migrations",
        "fix_action": "propagate_signature_migrations",
        "signature_migrations": [
            {
                "id": "migrate-project-root-to-workspace-root",
                "enabled": True,
                "target_simple_names": ["migrate"],
                "keyword_renames": {"project_root": "workspace_root"},
            },
        ],
    })
    updated, _ = rule.apply(source)
    assert "migrate(workspace_root=root, dry_run=True)" in updated


def test_signature_propagation_removes_and_adds_keywords() -> None:
    source = "run(legacy=True)\n"
    rule = FlextInfraRefactorSignaturePropagationRule({
        "id": "propagate-refactor-signature-migrations",
        "fix_action": "propagate_signature_migrations",
        "signature_migrations": [
            {
                "id": "run-signature-v2",
                "enabled": True,
                "target_simple_names": ["run"],
                "remove_keywords": ["legacy"],
                "add_keywords": {"mode": '"modern"'},
            },
        ],
    })
    updated, _ = rule.apply(source)
    assert "run(mode" in updated
    assert "modern" in updated
