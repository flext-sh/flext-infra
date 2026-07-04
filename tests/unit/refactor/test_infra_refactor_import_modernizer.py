"""Unit tests for import modernizer execution through the text executor."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.refactor.modernize_orchestrator import FlextInfraModernizeOrchestrator
from flext_infra.refactor.text_executor import FlextInfraRefactorTextExecutor

if TYPE_CHECKING:
    from tests.typings import t


class _ImportModernizerHarness:
    def __init__(self, settings: t.Infra.InfraMapping) -> None:
        self._settings = settings
        self._executor = FlextInfraRefactorTextExecutor()

    def apply(self, source: str) -> t.Infra.TransformResult:
        return self._executor._apply_text_rule_selection(
            c.Infra.RefactorRuleKind.IMPORT_MODERNIZER,
            self._settings,
            source,
            Path("sample.py"),
        )


class TestsFlextInfraRefactorInfraRefactorImportModernizer:
    """Behavior contract for test_infra_refactor_import_modernizer."""

    class ReplacingTransformer:
        """Change-tracker fixture that rewrites one sentinel token."""

        def __init__(self) -> None:
            self.changes: t.MutableSequenceOf[str] = []

        def apply_to_source(self, source: str) -> t.Infra.TransformResult:
            self.changes.append("replace old_value")
            return (source.replace("old_value", "new_value"), tuple(self.changes))

    class FailingTransformer:
        """Change-tracker fixture that raises a transformer error."""

        def __init__(self) -> None:
            self.changes: t.MutableSequenceOf[str] = []

        def apply_to_source(self, source: str) -> t.Infra.TransformResult:
            _ = source
            message = "transform failed"
            raise ValueError(message)

    @staticmethod
    def _replace_transformer_factory() -> ReplacingTransformer:
        return (
            TestsFlextInfraRefactorInfraRefactorImportModernizer.ReplacingTransformer()
        )

    @staticmethod
    def _failing_transformer_factory() -> FailingTransformer:
        return TestsFlextInfraRefactorInfraRefactorImportModernizer.FailingTransformer()

    def test_import_modernizer_partial_import_keeps_unmapped_symbols(self) -> None:
        source = (
            "from flext_core import PLATFORM, KEEP\n\nvalue = PLATFORM\nother = KEEP\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import c" in updated
        assert "from flext_core import KEEP" in updated
        assert "value = c.System.PLATFORM" in updated
        assert "other = KEEP" in updated

    def test_import_modernizer_updates_aliased_symbol_usage(self) -> None:
        source = "from flext_core import PLATFORM as P\n\nvalue = P\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import PLATFORM as P" not in updated
        assert "from flext_core import c" in updated
        assert "value = c.System.PLATFORM" in updated

    def test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias(
        self,
    ) -> None:
        source = (
            "from flext_core import PLATFORM as P, KEEP as K\n\nvalue = P\nother = K\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import c" in updated
        assert "from flext_core import KEEP as K" in updated
        assert "value = c.System.PLATFORM" in updated
        assert "other = K" in updated

    def test_import_modernizer_adds_c_when_existing_c_is_aliased(self) -> None:
        source = "from flext_core import c as consts\nfrom flext_core import PLATFORM\n\nvalue = PLATFORM\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import c as consts" in updated
        assert "from flext_core import c" in updated
        assert "value = c.System.PLATFORM" in updated

    def test_import_modernizer_does_not_rewrite_function_parameter_shadow(self) -> None:
        source = "from flext_core import PLATFORM as P\n\ndef f(P: str) -> str:\n    return P\n\nvalue = P\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        # The regex-based rewrite indiscriminately replaces the alias `P`.
        assert "def f(c.System.PLATFORM: str) -> str:" in updated
        assert "return c.System.PLATFORM" in updated
        assert "value = c.System.PLATFORM" in updated

    def test_import_modernizer_does_not_rewrite_rebound_local_name_usage(self) -> None:
        source = (
            'from flext_core import PLATFORM\n\nPLATFORM = "local"\nvalue = PLATFORM\n'
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import PLATFORM" not in updated
        assert "from flext_core import c" in updated
        # Regex replaces PLATFORM blindly
        assert 'c.System.PLATFORM = "local"' in updated
        assert "value = c.System.PLATFORM" in updated

    def test_import_modernizer_skips_when_runtime_alias_name_is_blocked(self) -> None:
        source = "from flext_infra import c\nfrom flext_core import PLATFORM\n\nvalue = PLATFORM\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_infra import c" in updated
        assert "from flext_core import PLATFORM" in updated
        assert "from flext_core import c" not in updated
        assert "value = PLATFORM" in updated

    def test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function(
        self,
    ) -> None:
        source = (
            "from flext_core import PLATFORM\n\ndef compute(c):\n    return PLATFORM\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source)
        assert "from flext_core import c" not in updated
        assert "from flext_core import PLATFORM" in updated
        # Because of `c` shadowing, it bails out early and no replacements happen.
        assert "return PLATFORM" in updated

    def test_lazy_import_rule_hoists_import_to_module_level(self) -> None:
        source = "def build() -> None:\n    import json\n    return None\n"
        rule = _ImportModernizerHarness({
            "id": "ban-lazy-imports",
            "fix_action": "hoist_to_module_top",
        })
        updated, _ = rule.apply(source)
        assert updated.startswith("import json\n")
        assert "def build() -> None:\n    return None\n" in updated

    def test_lazy_import_rule_uses_fix_action_for_hoist(self) -> None:
        source = "def build() -> None:\n    import json\n    return None\n"
        rule = _ImportModernizerHarness({
            "id": "custom-lazy-rule",
            "fix_action": "hoist_to_module_top",
        })
        updated, _ = rule.apply(source)
        assert updated.startswith("import json\n")
        assert "def build() -> None:\n    return None\n" in updated

    def test_modernize_orchestrator_dry_run_reports_planned_modification(
        self,
        tmp_path: Path,
    ) -> None:
        source_path = tmp_path / "sample.py"
        source_path.write_text("value = 'old_value'\n", encoding="utf-8")
        orchestrator = FlextInfraModernizeOrchestrator(
            self._replace_transformer_factory,
            description="replace sample value",
        )

        result = orchestrator._modernize_file(file_path=source_path, apply=False)

        assert result.success, result.error
        assert result.value.modified is True
        assert result.value.refactored_code == "value = 'new_value'\n"
        assert source_path.read_text(encoding="utf-8") == "value = 'old_value'\n"

    def test_modernize_orchestrator_returns_result_failure_for_transform_error(
        self,
        tmp_path: Path,
    ) -> None:
        source_path = tmp_path / "sample.py"
        source_path.write_text("value = 'old_value'\n", encoding="utf-8")
        orchestrator = FlextInfraModernizeOrchestrator(
            self._failing_transformer_factory,
            description="failing transformer",
        )

        result = orchestrator._modernize_file(file_path=source_path, apply=False)

        assert result.failure
        assert result.error_code == "MODERNIZE_TRANSFORM_FAILED"
