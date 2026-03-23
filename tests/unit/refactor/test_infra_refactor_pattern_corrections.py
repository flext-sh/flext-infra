"""Unit tests for FlextInfraRefactorPatternCorrectionsRule."""

from __future__ import annotations

import libcst as cst

from flext_infra import (
    FlextInfraRefactorPatternCorrectionsRule,
)


def test_pattern_rule_converts_dict_annotations_to_mapping() -> None:
    source = "def f(data: Mapping[str, t.NormalizedValue]) -> Mapping[str, t.NormalizedValue]:\n    return data\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "fix-container-invariance-annotations",
        "fix_action": "convert_dict_to_mapping_annotations",
    })
    updated_tree, _ = rule.apply(tree)
    updated = updated_tree.code
    assert "from collections.abc import Mapping" in updated
    assert "data: Mapping[str, t.NormalizedValue]" in updated
    assert "-> Mapping[str, t.NormalizedValue]" in updated


def test_pattern_rule_optionally_converts_return_annotations_to_mapping() -> None:
    source = "def f(data: Mapping[str, t.NormalizedValue]) -> Mapping[str, t.NormalizedValue]:\n    return data\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "fix-container-invariance-annotations",
        "fix_action": "convert_dict_to_mapping_annotations",
        "include_return_annotations": True,
    })
    updated_tree, _ = rule.apply(tree)
    updated = updated_tree.code
    assert "data: Mapping[str, t.NormalizedValue]" in updated
    assert "-> Mapping[str, t.NormalizedValue]" in updated


def test_pattern_rule_keeps_dict_param_when_subscript_mutated() -> None:
    source = 'def f(data: Mapping[str, t.NormalizedValue]) -> Mapping[str, t.NormalizedValue]:\n    data["k"] = "v"\n    return data\n'
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "fix-container-invariance-annotations",
        "fix_action": "convert_dict_to_mapping_annotations",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert updated == source
    assert changes == []


def test_pattern_rule_keeps_dict_param_when_copy_used() -> None:
    source = "def f(data: Mapping[str, t.NormalizedValue]) -> Mapping[str, t.NormalizedValue]:\n    clone = data.copy()\n    return clone\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "fix-container-invariance-annotations",
        "fix_action": "convert_dict_to_mapping_annotations",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert updated == source
    assert changes == []


def test_pattern_rule_skips_overload_signatures() -> None:
    source = "from typing import overload\n\n@overload\ndef f(data: Mapping[str, t.NormalizedValue]) -> str: ...\n\ndef f(data: Mapping[str, t.NormalizedValue]) -> str:\n    return str(data)\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "fix-container-invariance-annotations",
        "fix_action": "convert_dict_to_mapping_annotations",
    })
    updated_tree, _ = rule.apply(tree)
    updated = updated_tree.code
    assert "@overload" in updated
    assert "def f(data: Mapping[str, t.NormalizedValue]) -> str: ..." in updated
    assert "def f(data: Mapping[str, t.NormalizedValue]) -> str:" in updated


def test_pattern_rule_removes_configured_redundant_casts() -> None:
    source = 'value = cast("t.ConfigMap", result.unwrap_or(t.ConfigMap(root={})))\n'
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "remove-validated-redundant-casts",
        "fix_action": "remove_redundant_casts",
        "redundant_type_targets": ["t.ConfigMap"],
    })
    updated_tree, _ = rule.apply(tree)
    updated = updated_tree.code
    assert "cast(" not in updated
    assert "value = result.unwrap_or(t.ConfigMap(root={}))" in updated


def test_pattern_rule_removes_nested_type_object_cast_chain() -> None:
    source = 'value = cast("type", cast("t.NormalizedValue", FlextSettings))\n'
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "remove-validated-redundant-casts",
        "fix_action": "remove_redundant_casts",
        "redundant_type_targets": ["type"],
    })
    updated_tree, _ = rule.apply(tree)
    updated = updated_tree.code
    assert "cast(" not in updated
    assert "value = FlextSettings" in updated


def test_pattern_rule_keeps_type_cast_when_not_nested_object_cast() -> None:
    source = 'metadata_cls = cast("type", FlextRuntime.Metadata)\n'
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorPatternCorrectionsRule({
        "id": "remove-validated-redundant-casts",
        "fix_action": "remove_redundant_casts",
        "redundant_type_targets": ["type"],
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert updated == source
    assert changes == []
