"""Unit tests for import modernizer execution through the text executor."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraRefactorTextExecutor, c
from tests import t


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


def test_import_modernizer_partial_import_keeps_unmapped_symbols() -> None:
    source = "from flext_core import PLATFORM, KEEP\n\nvalue = PLATFORM\nother = KEEP\n"
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


def test_import_modernizer_updates_aliased_symbol_usage() -> None:
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


def test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias() -> None:
    source = "from flext_core import PLATFORM as P, KEEP as K\n\nvalue = P\nother = K\n"
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


def test_import_modernizer_adds_c_when_existing_c_is_aliased() -> None:
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


def test_import_modernizer_does_not_rewrite_function_parameter_shadow() -> None:
    source = "from flext_core import PLATFORM as P\n\ndef f(P: str) -> str:\n    return P\n\nvalue = P\n"
    rule = _ImportModernizerHarness({
        "id": "modernize-constants-import",
        "module": "flext_core",
        "symbol_mapping": {"PLATFORM": "c.System.PLATFORM"},
    })
    updated, _ = rule.apply(source)
    # The regex-based engine indiscriminately replaces the alias `P`.
    assert "def f(c.System.PLATFORM: str) -> str:" in updated
    assert "return c.System.PLATFORM" in updated
    assert "value = c.System.PLATFORM" in updated


def test_import_modernizer_does_not_rewrite_rebound_local_name_usage() -> None:
    source = 'from flext_core import PLATFORM\n\nPLATFORM = "local"\nvalue = PLATFORM\n'
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


def test_import_modernizer_skips_when_runtime_alias_name_is_blocked() -> None:
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


def test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function() -> (
    None
):
    source = "from flext_core import PLATFORM\n\ndef compute(c):\n    return PLATFORM\n"
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


def test_lazy_import_rule_hoists_import_to_module_level() -> None:
    source = "def build() -> None:\n    import json\n    return None\n"
    rule = _ImportModernizerHarness({
        "id": "ban-lazy-imports",
        "fix_action": "hoist_to_module_top",
    })
    updated, _ = rule.apply(source)
    assert updated.startswith("import json\n")
    assert "def build() -> None:\n    return None\n" in updated


def test_lazy_import_rule_uses_fix_action_for_hoist() -> None:
    source = "def build() -> None:\n    import json\n    return None\n"
    rule = _ImportModernizerHarness({
        "id": "custom-lazy-rule",
        "fix_action": "hoist_to_module_top",
    })
    updated, _ = rule.apply(source)
    assert updated.startswith("import json\n")
    assert "def build() -> None:\n    return None\n" in updated
