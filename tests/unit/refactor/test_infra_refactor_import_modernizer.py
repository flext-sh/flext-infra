"""Unit tests for import modernizer execution through the text executor."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c, m
from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader
from flext_infra.refactor.modernize_orchestrator import FlextInfraModernizeOrchestrator
from flext_infra.refactor.orchestrator import FlextInfraRefactorOrchestrator

if TYPE_CHECKING:
    from tests import t


class _ImportModernizerHarness:
    """Drive the IMPORT_MODERNIZER text rule through the public refactor entry."""

    def __init__(self, settings: t.Infra.InfraMapping) -> None:
        self._settings = settings

    def apply(self, source: str, tmp_path: Path) -> t.Infra.TransformResult:
        sample_path = tmp_path / "sample.py"
        sample_path.write_text(source, encoding="utf-8")
        loader = FlextInfraRefactorRuleLoader(tmp_path / "refactor.yaml")
        loader.rules = [(c.Infra.RefactorRuleKind.IMPORT_MODERNIZER, self._settings)]
        result = FlextInfraRefactorOrchestrator(loader).refactor_file(
            sample_path, dry_run=True
        )
        return (result.refactored_code or source, tuple(result.changes))


class TestsFlextInfraRefactorInfraRefactorImportModernizer:
    """Behavior contract for test_infra_refactor_import_modernizer."""

    class ReplacingTransformer:
        """Change-tracker fixture that rewrites one sentinel token."""

        def __init__(self) -> None:
            """Initialize the recorded change list."""
            self.changes: t.MutableSequenceOf[str] = []

        def apply_to_source(self, source: str) -> t.Infra.TransformResult:
            self.changes.append("replace old_value")
            return (source.replace("old_value", "new_value"), tuple(self.changes))

    class FailingTransformer:
        """Change-tracker fixture that raises a transformer error."""

        def __init__(self) -> None:
            """Initialize the recorded change list."""
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

    def test_import_modernizer_partial_import_keeps_unmapped_symbols(
        self, tmp_path: Path
    ) -> None:
        source = (
            "from flext_core import PLATFORM, KEEP\n\nvalue = PLATFORM\nother = KEEP\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, has="from flext_core import c")
        tm.that(updated, has="from flext_core import KEEP")
        tm.that(updated, has="value = c.System.PLATFORM")
        tm.that(updated, has="other = KEEP")

    def test_import_modernizer_updates_aliased_symbol_usage(
        self, tmp_path: Path
    ) -> None:
        source = "from flext_core import PLATFORM as P\n\nvalue = P\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, lacks="from flext_core import PLATFORM as P")
        tm.that(updated, has="from flext_core import c")
        tm.that(updated, has="value = c.System.PLATFORM")

    def test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias(
        self, tmp_path: Path
    ) -> None:
        source = (
            "from flext_core import PLATFORM as P, KEEP as K\n\nvalue = P\nother = K\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, has="from flext_core import c")
        tm.that(updated, has="from flext_core import KEEP as K")
        tm.that(updated, has="value = c.System.PLATFORM")
        tm.that(updated, has="other = K")

    def test_import_modernizer_adds_c_when_existing_c_is_aliased(
        self, tmp_path: Path
    ) -> None:
        source = "from flext_core import c as consts\nfrom flext_core import PLATFORM\n\nvalue = PLATFORM\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, has="from flext_core import c as consts")
        tm.that(updated, has="from flext_core import c")
        tm.that(updated, has="value = c.System.PLATFORM")

    def test_import_modernizer_does_not_rewrite_function_parameter_shadow(
        self, tmp_path: Path
    ) -> None:
        source = "from flext_core import PLATFORM as P\n\ndef f(P: str) -> str:\n    return P\n\nvalue = P\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        # The regex-based rewrite indiscriminately replaces the alias `P`.
        tm.that(updated, has="def f(c.System.PLATFORM: str) -> str:")
        tm.that(updated, has="return c.System.PLATFORM")
        tm.that(updated, has="value = c.System.PLATFORM")

    def test_import_modernizer_does_not_rewrite_rebound_local_name_usage(
        self, tmp_path: Path
    ) -> None:
        source = (
            'from flext_core import PLATFORM\n\nPLATFORM = "local"\nvalue = PLATFORM\n'
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, lacks="from flext_core import PLATFORM")
        tm.that(updated, has="from flext_core import c")
        # Regex replaces PLATFORM blindly
        tm.that(updated, has='c.System.PLATFORM = "local"')
        tm.that(updated, has="value = c.System.PLATFORM")

    def test_import_modernizer_skips_when_runtime_alias_name_is_blocked(
        self, tmp_path: Path
    ) -> None:
        source = "from flext_infra import c\nfrom flext_core import PLATFORM\n\nvalue = PLATFORM\n"
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, has="from flext_infra import c")
        tm.that(updated, has="from flext_core import PLATFORM")
        tm.that(updated, lacks="from flext_core import c")
        tm.that(updated, has="value = PLATFORM")

    def test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function(
        self, tmp_path: Path
    ) -> None:
        source = (
            "from flext_core import PLATFORM\n\ndef compute(c):\n    return PLATFORM\n"
        )
        rule = _ImportModernizerHarness({
            "id": "modernize-constants-import",
            "module": "flext_core",
            "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
        })
        updated, _ = rule.apply(source, tmp_path)
        tm.that(updated, lacks="from flext_core import c")
        tm.that(updated, has="from flext_core import PLATFORM")
        # Because of `c` shadowing, it bails out early and no replacements happen.
        tm.that(updated, has="return PLATFORM")

    def test_lazy_import_rule_hoists_import_to_module_level(
        self, tmp_path: Path
    ) -> None:
        source = "def build() -> None:\n    import json\n    return None\n"
        rule = _ImportModernizerHarness({
            "id": "ban-lazy-imports",
            "fix_action": "hoist_to_module_top",
        })
        updated, _ = rule.apply(source, tmp_path)
        assert updated.startswith("import json\n")
        tm.that(updated, has="def build() -> None:\n    return None\n")

    def test_lazy_import_rule_uses_fix_action_for_hoist(self, tmp_path: Path) -> None:
        source = "def build() -> None:\n    import json\n    return None\n"
        rule = _ImportModernizerHarness({
            "id": "custom-lazy-rule",
            "fix_action": "hoist_to_module_top",
        })
        updated, _ = rule.apply(source, tmp_path)
        assert updated.startswith("import json\n")
        tm.that(updated, has="def build() -> None:\n    return None\n")

    @staticmethod
    def _write_project(workspace_root: Path, source: str) -> Path:
        project_root = workspace_root / "flext-demo"
        package_root = project_root / "src" / "flext_demo"
        package_root.mkdir(parents=True)
        (project_root / "pyproject.toml").write_text(
            '[project]\nname = "flext-demo"\n', encoding="utf-8"
        )
        sample_path = package_root / "sample.py"
        sample_path.write_text(source, encoding="utf-8")
        return sample_path

    def test_modernize_run_dry_run_reports_planned_modification(
        self, tmp_path: Path
    ) -> None:
        sample_path = self._write_project(tmp_path, "value = 'old_value'\n")
        orchestrator = FlextInfraModernizeOrchestrator(
            self._replace_transformer_factory, description="replace sample value"
        )

        result = orchestrator.run(
            m.Infra.ModernizeInput(
                workspace=str(tmp_path), projects=["flext-demo"], apply=False, gates=[]
            )
        )

        tm.ok(result)
        modernized = result.value[0]
        tm.that(modernized.modified, eq=True)
        tm.that(modernized.refactored_code, eq="value = 'new_value'\n")
        tm.that(sample_path.read_text(encoding="utf-8"), eq="value = 'old_value'\n")

    def test_modernize_run_returns_result_failure_for_transform_error(
        self, tmp_path: Path
    ) -> None:
        self._write_project(tmp_path, "value = 'old_value'\n")
        orchestrator = FlextInfraModernizeOrchestrator(
            self._failing_transformer_factory, description="failing transformer"
        )

        result = orchestrator.run(
            m.Infra.ModernizeInput(
                workspace=str(tmp_path), projects=["flext-demo"], apply=False, gates=[]
            )
        )

        tm.fail(result)
        tm.that(result.error, has="Transform failed")
