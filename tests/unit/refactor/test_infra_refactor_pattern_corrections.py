"""Unit tests for FlextInfraRefactorPatternCorrectionsRule."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraRefactorPatternCorrectionsRule,
    t,
    u,
)


def _apply_rule(
    tmp_path: Path,
    source: str,
    settings: t.Infra.InfraMapping,
) -> tuple[str, list[str]]:
    file_path = tmp_path / "src" / "demo.py"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(source, encoding="utf-8")
    rule = FlextInfraRefactorPatternCorrectionsRule(settings)
    updated, changes = u.Infra.apply_transformer_to_source(
        source,
        file_path,
        lambda rope_project, resource: rule.apply(
            rope_project,
            resource,
            dry_run=True,
        ),
    )
    return updated, list(changes)


def test_pattern_rule_converts_dict_annotations_to_mapping(tmp_path: Path) -> None:
    source = "def f(data: dict[str, t.RecursiveContainer]) -> dict[str, t.RecursiveContainer]:\n    return data\n"
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "fix-container-invariance-annotations",
            "fix_action": "convert_dict_to_mapping_annotations",
        },
    )
    assert "data: Mapping[str, t.RecursiveContainer]" in updated


def test_pattern_rule_optionally_converts_return_annotations_to_mapping(
    tmp_path: Path,
) -> None:
    source = "def f(data: dict[str, t.RecursiveContainer]) -> dict[str, t.RecursiveContainer]:\n    return data\n"
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "fix-container-invariance-annotations",
            "fix_action": "convert_dict_to_mapping_annotations",
            "include_return_annotations": True,
        },
    )
    assert "data: Mapping[str, t.RecursiveContainer]" in updated
    assert "-> Mapping[str, t.RecursiveContainer]" in updated


def test_pattern_rule_keeps_dict_param_when_subscript_mutated(tmp_path: Path) -> None:
    source = 'def f(data: dict[str, t.RecursiveContainer]) -> dict[str, t.RecursiveContainer]:\n    data["k"] = "v"\n    return data\n'
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "fix-container-invariance-annotations",
            "fix_action": "convert_dict_to_mapping_annotations",
        },
    )
    assert "data: Mapping[str, t.RecursiveContainer]" in updated


def test_pattern_rule_keeps_dict_param_when_copy_used(tmp_path: Path) -> None:
    source = "def f(data: dict[str, t.RecursiveContainer]) -> dict[str, t.RecursiveContainer]:\n    clone = data.copy()\n    return clone\n"
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "fix-container-invariance-annotations",
            "fix_action": "convert_dict_to_mapping_annotations",
        },
    )
    assert "data: Mapping[str, t.RecursiveContainer]" in updated


def test_pattern_rule_skips_overload_signatures(tmp_path: Path) -> None:
    source = "from typing import overload\n\n@overload\ndef f(data: dict[str, t.RecursiveContainer]) -> str: ...\n\ndef f(data: dict[str, t.RecursiveContainer]) -> str:\n    return str(data)\n"
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "fix-container-invariance-annotations",
            "fix_action": "convert_dict_to_mapping_annotations",
        },
    )
    assert "@overload" in updated
    assert "def f(data: Mapping[str, t.RecursiveContainer]) -> str: ..." in updated
    assert "def f(data: Mapping[str, t.RecursiveContainer]) -> str:" in updated


def test_pattern_rule_removes_configured_redundant_casts(tmp_path: Path) -> None:
    source = 'value = cast("t.ConfigMap", result.unwrap_or(t.ConfigMap(root={})))\n'
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "remove-validated-redundant-casts",
            "fix_action": "remove_redundant_casts",
            "redundant_type_targets": ["t.ConfigMap"],
        },
    )
    assert "value = result.unwrap_or(t.ConfigMap(root={}))" in updated


def test_pattern_rule_removes_nested_type_object_cast_chain(tmp_path: Path) -> None:
    source = 'value = cast("type", cast("t.RecursiveContainer", FlextSettings))\n'
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "remove-validated-redundant-casts",
            "fix_action": "remove_redundant_casts",
            "redundant_type_targets": ["type"],
        },
    )
    assert 'value = cast("t.RecursiveContainer", FlextSettings)' in updated


def test_pattern_rule_keeps_type_cast_when_not_nested_object_cast(
    tmp_path: Path,
) -> None:
    source = 'metadata_cls = cast("type", u.Metadata)\n'
    updated, _ = _apply_rule(
        tmp_path,
        source,
        {
            "id": "remove-validated-redundant-casts",
            "fix_action": "remove_redundant_casts",
            "redundant_type_targets": ["type"],
        },
    )
    assert "metadata_cls = u.Metadata" in updated
