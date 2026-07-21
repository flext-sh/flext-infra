"""Unit tests for pattern corrections through the public refactor service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import t
from flext_infra.refactor.service import FlextInfraRefactorService

if TYPE_CHECKING:
    from pathlib import Path


def _apply_rule(
    tmp_path: Path, source: str, settings: t.Infra.InfraMapping
) -> tuple[str, list[str]]:
    file_path = tmp_path / "src" / "demo.py"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(source, encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    config_path = tmp_path / "settings.yml"
    config_path.write_text("session: test\n", encoding="utf-8")
    rule_lines = ["", "rules:", "  - id: " + str(settings["id"])]
    for key, value in settings.items():
        if key == "id":
            continue
        if isinstance(value, bool):
            rule_lines.append(f"    {key}: {str(value).lower()}")
        elif isinstance(value, (list, tuple)):
            rule_lines.append(f"    {key}:")
            rule_lines.extend(f"      - {item}" for item in value)
        else:
            rule_lines.append(f"    {key}: {value}")
    rule_lines.append("    enabled: true")
    (rules_dir / "rules.yml").write_text(
        "\n".join(rule_lines) + "\n", encoding="utf-8"
    )
    service = FlextInfraRefactorService(config_path=config_path)
    load_result = service.load_rules()
    tm.ok(load_result)
    result = service.refactor_file(file_path, dry_run=True)
    tm.that(result.success, eq=True)
    return result.refactored_code or "", list(result.changes)


class TestsFlextInfraRefactorInfraRefactorPatternCorrections:
    """Behavior contract for test_infra_refactor_pattern_corrections."""

    def test_pattern_rule_converts_dict_annotations_to_mapping(
        self, tmp_path: Path
    ) -> None:
        source = "def f(data: dict[str, t.JsonValue]) -> dict[str, t.JsonValue]:\n    return data\n"
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "fix-container-invariance-annotations",
                "fix_action": "convert_dict_to_mapping_annotations",
            },
        )
        tm.that(updated, has="data: t.JsonMapping")

    def test_pattern_rule_optionally_converts_return_annotations_to_mapping(
        self, tmp_path: Path
    ) -> None:
        source = "def f(data: dict[str, t.JsonValue]) -> dict[str, t.JsonValue]:\n    return data\n"
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "fix-container-invariance-annotations",
                "fix_action": "convert_dict_to_mapping_annotations",
                "include_return_annotations": True,
            },
        )
        tm.that(updated, has="data: t.JsonMapping")
        tm.that(updated, has="-> t.JsonMapping")

    def test_pattern_rule_keeps_dict_param_when_subscript_mutated(
        self, tmp_path: Path
    ) -> None:
        source = 'def f(data: dict[str, t.JsonValue]) -> dict[str, t.JsonValue]:\n    data["k"] = "v"\n    return data\n'
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "fix-container-invariance-annotations",
                "fix_action": "convert_dict_to_mapping_annotations",
            },
        )
        tm.that(updated, has="data: t.JsonMapping")

    def test_pattern_rule_keeps_dict_param_when_copy_used(self, tmp_path: Path) -> None:
        source = "def f(data: dict[str, t.JsonValue]) -> dict[str, t.JsonValue]:\n    clone = data.copy()\n    return clone\n"
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "fix-container-invariance-annotations",
                "fix_action": "convert_dict_to_mapping_annotations",
            },
        )
        tm.that(updated, has="data: t.JsonMapping")

    def test_pattern_rule_skips_overload_signatures(self, tmp_path: Path) -> None:
        source = "from typing import overload\n\n@overload\ndef f(data: dict[str, t.JsonValue]) -> str: ...\n\ndef f(data: dict[str, t.JsonValue]) -> str:\n    return str(data)\n"
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "fix-container-invariance-annotations",
                "fix_action": "convert_dict_to_mapping_annotations",
            },
        )
        tm.that(updated, has="@overload")
        tm.that(updated, has="def f(data: t.JsonMapping) -> str: ...")
        tm.that(updated, has="def f(data: t.JsonMapping) -> str:")

    def test_pattern_rule_removes_configured_redundant_casts(
        self, tmp_path: Path
    ) -> None:
        source = 'value = cast("m.ConfigMap", result.unwrap_or(m.ConfigMap(root={})))\n'
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "remove-validated-redundant-casts",
                "fix_action": "remove_redundant_casts",
                "redundant_type_targets": ["m.ConfigMap"],
            },
        )
        tm.that(updated, has="value = result.unwrap_or(m.ConfigMap(root={}))")

    def test_pattern_rule_removes_nested_type_object_cast_chain(
        self, tmp_path: Path
    ) -> None:
        source = 'value = cast("type", cast("t.JsonValue", FlextSettings))\n'
        updated, _ = _apply_rule(
            tmp_path,
            source,
            {
                "id": "remove-validated-redundant-casts",
                "fix_action": "remove_redundant_casts",
                "redundant_type_targets": ["type"],
            },
        )
        tm.that(updated, has='value = cast("t.JsonValue", FlextSettings)')

    def test_pattern_rule_keeps_type_cast_when_not_nested_object_cast(
        self, tmp_path: Path
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
        tm.that(updated, has="metadata_cls = u.Metadata")
