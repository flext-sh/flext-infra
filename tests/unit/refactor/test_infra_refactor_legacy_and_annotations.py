"""Unit tests for legacy-removal and future-annotations text execution."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraRefactorTextExecutor, c
from tests import t


class _TextRuleHarness:
    def __init__(
        self,
        kind: c.Infra.RefactorRuleKind,
        settings: t.Infra.InfraMapping,
    ) -> None:
        self._executor = FlextInfraRefactorTextExecutor()
        self._kind = kind
        self._settings = settings

    def apply(self, source: str) -> t.Infra.TransformResult:
        return self._executor._apply_text_rule_selection(
            self._kind,
            self._settings,
            source,
            Path("target.py"),
        )


class TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations:
    """Behavior contract for test_infra_refactor_legacy_and_annotations."""

    def test_ensure_future_annotations_after_docstring(self) -> None:
        source = '"""doc"""\n\nimport os\n'
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS,
            {
                "id": "ensure-future-annotations",
            },
        )
        updated, _ = rule.apply(source)
        assert (
            '"""doc"""\n\nfrom __future__ import annotations\n\nimport os\n' in updated
        )

    def test_ensure_future_annotations_moves_existing_import_to_top(self) -> None:
        source = "import os\nfrom __future__ import annotations\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS,
            {
                "id": "ensure-future-annotations",
            },
        )
        updated, _ = rule.apply(source)
        assert updated.startswith("from __future__ import annotations\n")
        assert "\nimport os\n" in updated

    def test_legacy_wrapper_function_is_inlined_as_alias(self) -> None:
        source = "def run(value: int) -> int:\n    return execute(value)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        assert "def run" not in updated
        assert "run = execute" in updated

    def test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias(self) -> None:
        source = "def run(a: int, b: int) -> int:\n    return execute(a=a, b=b)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        assert "def run" not in updated
        assert "run = execute" in updated

    def test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias(self) -> None:
        source = "def run(a: int, *args, **kwargs: t.Scalar) -> int:\n    return execute(a, *args, **kwargs)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        assert "def run" not in updated
        assert "run = execute" in updated

    def test_legacy_wrapper_non_passthrough_is_not_inlined(self) -> None:
        source = "def run(a: int, b: int) -> int:\n    return execute(a, b + 1)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        assert "def run" in updated
        assert "run = execute" not in updated

    def test_legacy_rule_uses_fix_action_remove_for_aliases(self) -> None:
        source = "OldName = NewName\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL,
            {
                "id": "custom-legacy-rule",
                "fix_action": "remove",
            },
        )
        updated, _ = rule.apply(source)
        assert "OldName = NewName" not in updated

    def test_legacy_import_bypass_collapses_to_primary_import(self) -> None:
        source = "try:\n    from new_mod import Thing\nexcept ImportError:\n    from old_mod import Thing\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-import-bypasses"}
        )
        updated, _ = rule.apply(source)
        assert "try:" not in updated
        assert "from new_mod import Thing" in updated
        assert "from old_mod import Thing" not in updated
