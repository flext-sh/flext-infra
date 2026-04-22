"""Unit tests for class reconstructor, symbol, and signature transformers."""

from __future__ import annotations

from flext_infra import (
    FlextInfraRefactorClassReconstructor,
    FlextInfraRefactorSignaturePropagator,
    FlextInfraRefactorSymbolPropagator,
)
from tests import m


def test_class_reconstructor_reorders_methods_by_config() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    def __init__(self) -> None:\n        return None\n\n    def a(self) -> None:\n        return None\n"
    updated, _ = FlextInfraRefactorClassReconstructor(
        order_config=[
            {"category": "magic", "patterns": ["^__.+__$"]},
            {"category": "public", "visibility": "public"},
        ],
    ).apply_to_source(source)
    assert updated.index("def __init__") < updated.index("def a")
    assert updated.index("def a") < updated.index("def b")


def test_class_reconstructor_skips_interleaved_non_method_members() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    alias = b\n\n    def a(self) -> None:\n        return None\n"
    updated, _ = FlextInfraRefactorClassReconstructor(
        order_config=[
            {"category": "magic", "patterns": ["^__.+__$"]},
            {"category": "public", "visibility": "public"},
        ],
    ).apply_to_source(source)
    assert updated == source


def test_class_reconstructor_reorders_each_contiguous_method_block() -> None:
    source = "class C:\n    def b(self) -> None:\n        return None\n\n    def a(self) -> None:\n        return None\n\n    alias = a\n\n    def d(self) -> None:\n        return None\n\n    def c(self) -> None:\n        return None\n"
    updated, _ = FlextInfraRefactorClassReconstructor(
        order_config=[{"category": "public", "visibility": "public"}],
    ).apply_to_source(source)
    assert updated.index("def a") < updated.index("def b")
    assert updated.index("def c") < updated.index("def d")
    assert "alias = a" in updated


def test_symbol_propagation_renames_import_and_local_references() -> None:
    source = (
        "from flext_infra import LegacyRemovalRule\n\nrule_cls = LegacyRemovalRule\n"
    )
    updated, _ = FlextInfraRefactorSymbolPropagator(
        target_modules={"flext_infra"},
        module_renames={},
        import_symbol_renames={
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    ).apply_to_source(source)
    assert "from flext_infra import FlextInfraRefactorLegacyRemovalRule" in updated
    assert "rule_cls = FlextInfraRefactorLegacyRemovalRule" in updated


def test_symbol_propagation_keeps_alias_reference_when_asname_used() -> None:
    source = (
        "from flext_infra import LegacyRemovalRule as Legacy\n\nrule_cls = Legacy\n"
    )
    updated, _ = FlextInfraRefactorSymbolPropagator(
        target_modules={"flext_infra"},
        module_renames={},
        import_symbol_renames={
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    ).apply_to_source(source)
    assert (
        "from flext_infra import FlextInfraRefactorLegacyRemovalRule as Legacy"
        in updated
    )
    assert "rule_cls = Legacy" in updated


def test_symbol_propagation_updates_mro_base_references() -> None:
    source = "from flext_infra import LegacyRemovalRule\n\nclass RuleV2(LegacyRemovalRule):\n    pass\n"
    updated, _ = FlextInfraRefactorSymbolPropagator(
        target_modules={"flext_infra"},
        module_renames={},
        import_symbol_renames={
            "LegacyRemovalRule": "FlextInfraRefactorLegacyRemovalRule",
        },
    ).apply_to_source(source)
    assert "class RuleV2(FlextInfraRefactorLegacyRemovalRule):" in updated


def test_signature_propagation_renames_call_keyword() -> None:
    source = "result = migrate(project_root=root, dry_run=True)\n"
    migration = m.Infra.SignatureMigration.model_validate({
        "id": "migrate-project-root-to-workspace-root",
        "enabled": True,
        "target_simple_names": ["migrate"],
        "keyword_renames": {"project_root": "workspace_root"},
    })
    updated = FlextInfraRefactorSignaturePropagator(
        migrations=[migration],
    ).apply_to_source(source)
    assert "migrate(workspace_root=root, dry_run=True)" in updated


def test_signature_propagation_removes_and_adds_keywords() -> None:
    source = "run(legacy=True)\n"
    migration = m.Infra.SignatureMigration.model_validate({
        "id": "run-signature-v2",
        "enabled": True,
        "target_simple_names": ["run"],
        "remove_keywords": ["legacy"],
        "add_keywords": {"mode": '"modern"'},
    })
    updated = FlextInfraRefactorSignaturePropagator(
        migrations=[migration],
    ).apply_to_source(source)
    assert "run(mode" in updated
    assert "modern" in updated
