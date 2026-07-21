"""Unit tests for legacy-removal and future-annotations via the public service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.refactor.service import FlextInfraRefactorService
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


_KIND_PRIMARY_FIX_ACTION: dict[c.Infra.RefactorRuleKind, str] = {
    c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS: "ensure_future_annotations",
    c.Infra.RefactorRuleKind.LEGACY_REMOVAL: "remove",
}


class _TextRuleHarness:
    def __init__(
        self, kind: c.Infra.RefactorRuleKind, settings: t.Infra.InfraMapping
    ) -> None:
        self._kind = kind
        self._settings = settings

    def apply(self, source: str) -> tuple[str, list[str]]:
        workspace = Path(tempfile.mkdtemp())
        file_path = workspace / "src" / "target.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(source, encoding="utf-8")
        rules_dir = workspace / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        config_path = workspace / "settings.yml"
        config_path.write_text("session: test\n", encoding="utf-8")
        fix_action = self._settings.get("fix_action") or _KIND_PRIMARY_FIX_ACTION[
            self._kind
        ]
        rule_lines = [
            "",
            "rules:",
            "  - id: " + str(self._settings["id"]),
            f"    fix_action: {fix_action}",
            "    enabled: true",
        ]
        (rules_dir / "rules.yml").write_text(
            "\n".join(rule_lines) + "\n", encoding="utf-8"
        )
        service = FlextInfraRefactorService(config_path=config_path)
        tm.ok(service.load_rules())
        result = service.refactor_file(file_path)
        tm.that(result.success, eq=True)
        return file_path.read_text(encoding="utf-8"), list(result.changes)


class TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations:
    """Behavior contract for test_infra_refactor_legacy_and_annotations."""

    def test_ensure_future_annotations_after_docstring(self) -> None:
        source = '"""doc"""\n\nimport os\n'
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS,
            {"id": "ensure-future-annotations"},
        )
        updated, _ = rule.apply(source)
        assert (
            '"""doc"""\n\nfrom __future__ import annotations\n\nimport os\n' in updated
        )

    def test_ensure_future_annotations_moves_existing_import_to_top(self) -> None:
        source = "import os\nfrom __future__ import annotations\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS,
            {"id": "ensure-future-annotations"},
        )
        updated, _ = rule.apply(source)
        assert updated.startswith("from __future__ import annotations\n")
        tm.that(updated, has="\nimport os\n")

    def test_legacy_wrapper_function_is_inlined_as_alias(self) -> None:
        source = "def run(value: int) -> int:\n    return execute(value)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        tm.that(updated, lacks="def run")
        tm.that(updated, has="run = execute")

    def test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias(self) -> None:
        source = "def run(a: int, b: int) -> int:\n    return execute(a=a, b=b)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        tm.that(updated, lacks="def run")
        tm.that(updated, has="run = execute")

    def test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias(self) -> None:
        source = "def run(a: int, *args, **kwargs: t.Scalar) -> int:\n    return execute(a, *args, **kwargs)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        tm.that(updated, lacks="def run")
        tm.that(updated, has="run = execute")

    def test_legacy_wrapper_non_passthrough_is_not_inlined(self) -> None:
        source = "def run(a: int, b: int) -> int:\n    return execute(a, b + 1)\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-wrapper-functions"}
        )
        updated, _ = rule.apply(source)
        tm.that(updated, has="def run")
        tm.that(updated, lacks="run = execute")

    def test_legacy_rule_uses_fix_action_remove_for_aliases(self) -> None:
        source = "OldName = NewName\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL,
            {"id": "custom-legacy-rule", "fix_action": "remove"},
        )
        updated, _ = rule.apply(source)
        tm.that(updated, lacks="OldName = NewName")

    def test_legacy_import_bypass_collapses_to_primary_import(self) -> None:
        source = "try:\n    from new_mod import Thing\nexcept ImportError:\n    from old_mod import Thing\n"
        rule = _TextRuleHarness(
            c.Infra.RefactorRuleKind.LEGACY_REMOVAL, {"id": "remove-import-bypasses"}
        )
        updated, _ = rule.apply(source)
        tm.that(updated, lacks="try:")
        tm.that(updated, has="from new_mod import Thing")
        tm.that(updated, lacks="from old_mod import Thing")
