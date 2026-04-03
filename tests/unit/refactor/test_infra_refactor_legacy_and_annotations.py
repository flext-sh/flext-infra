"""Unit tests for FlextInfraRefactorLegacyRemovalRule and EnsureFutureAnnotationsRule."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from tests import t

from flext_infra import (
    FlextInfraRefactorEnsureFutureAnnotationsRule,
    FlextInfraRefactorLegacyRemovalRule,
)


def _create_resource(
    rope_project: t.Infra.RopeProject, source: str, filename: str = "target.py"
) -> t.Infra.RopeResource:
    path = Path(rope_project.root.real_path) / filename
    path.write_text(source, encoding="utf-8")
    return cast("t.Infra.RopeResource", rope_project.get_resource(filename))


def test_ensure_future_annotations_after_docstring() -> None:
    source = '"""doc"""\n\nimport os\n'
    rule = FlextInfraRefactorEnsureFutureAnnotationsRule({
        "id": "ensure-future-annotations",
    })
    updated, _ = rule.apply(source)
    assert '"""doc"""\n\nfrom __future__ import annotations\n\nimport os\n' in updated


def test_ensure_future_annotations_moves_existing_import_to_top() -> None:
    source = "import os\nfrom __future__ import annotations\n"
    rule = FlextInfraRefactorEnsureFutureAnnotationsRule({
        "id": "ensure-future-annotations",
    })
    updated, _ = rule.apply(source)
    assert updated.startswith("from __future__ import annotations\n")
    assert "\nimport os\n" in updated


def test_legacy_wrapper_function_is_inlined_as_alias(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "def run(value: int) -> int:\n    return execute(value)\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({"id": "remove-wrapper-functions"})
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "def run" not in updated
    assert "run = execute" in updated


def test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "def run(a: int, b: int) -> int:\n    return execute(a=a, b=b)\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({"id": "remove-wrapper-functions"})
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "def run" not in updated
    assert "run = execute" in updated


def test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "def run(a: int, *args, **kwargs: t.Scalar) -> int:\n    return execute(a, *args, **kwargs)\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({"id": "remove-wrapper-functions"})
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "def run" not in updated
    assert "run = execute" in updated


def test_legacy_wrapper_non_passthrough_is_not_inlined(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "def run(a: int, b: int) -> int:\n    return execute(a, b + 1)\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({"id": "remove-wrapper-functions"})
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "def run" in updated
    assert "run = execute" not in updated


def test_legacy_rule_uses_fix_action_remove_for_aliases(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "OldName = NewName\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({
        "id": "custom-legacy-rule",
        "fix_action": "remove",
    })
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "OldName = NewName" not in updated


def test_legacy_import_bypass_collapses_to_primary_import(
    rope_project: t.Infra.RopeProject,
) -> None:
    source = "try:\n    from new_mod import Thing\nexcept ImportError:\n    from old_mod import Thing\n"
    resource = _create_resource(rope_project, source)
    rule = FlextInfraRefactorLegacyRemovalRule({"id": "remove-import-bypasses"})
    updated, _ = rule.apply(rope_project, resource, dry_run=True)
    assert "try:" not in updated
    assert "from new_mod import Thing" in updated
    assert "from old_mod import Thing" not in updated
