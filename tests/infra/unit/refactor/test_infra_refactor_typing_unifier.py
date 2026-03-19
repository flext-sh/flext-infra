from __future__ import annotations

from pathlib import Path

import libcst as cst

from flext_infra.rules.type_alias_unification import (
    FlextInfraRefactorTypingUnificationRule,
)


def test_converts_typealias_to_pep695() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias\n\n"
        "MyType: TypeAlias = str\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "type MyType = str" in updated
    assert "TypeAlias" not in updated
    assert any(
        "Converted legacy TypeAlias assignment: MyType" == change for change in changes
    )
    assert any("Removed typing import: TypeAlias" == change for change in changes)


def test_converts_multiple_aliases() -> None:
    source = (
        "from typing import TypeAlias\n\n"
        "AliasA: TypeAlias = str\n"
        "AliasB: TypeAlias = int\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "type AliasA = str" in updated
    assert "type AliasB = int" in updated
    assert any(
        "Converted legacy TypeAlias assignment: AliasA" == change for change in changes
    )
    assert any(
        "Converted legacy TypeAlias assignment: AliasB" == change for change in changes
    )


def test_removes_dead_typealias_import() -> None:
    source = "from typing import TypeAlias\nMyType: TypeAlias = str\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import" not in updated
    assert "type MyType = str" in updated
    assert any("Removed empty typing import" == change for change in changes)


def test_removes_all_unused_typing_imports() -> None:
    source = (
        "x: Final[str] = ''\nfrom typing import Final, TypeAlias, ClassVar, override\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import Final" in updated
    assert "TypeAlias" not in updated
    assert "ClassVar" not in updated
    assert "override" not in updated
    assert any("Removed typing import: TypeAlias" == change for change in changes)
    assert any("Removed unused typing import: ClassVar" == change for change in changes)
    assert any("Removed unused typing import: override" == change for change in changes)


def test_preserves_used_typing_imports() -> None:
    source = (
        "x: Final[str] = ''\ny: ClassVar[int] = 0\nfrom typing import Final, ClassVar\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import Final, ClassVar" in updated
    assert updated == source
    assert changes == []


def test_replaces_primitives_union() -> None:
    source = (
        "from __future__ import annotations\n\n"
        "def foo(x: str | int | float | bool) -> None:\n"
        "    pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "t.Primitives" in updated
    assert "str | int | float | bool" not in updated
    assert "from flext_core import t" in updated
    assert any(
        "Canonicalized inline union -> t.Primitives" == change for change in changes
    )


def test_replaces_numeric_union() -> None:
    source = "def foo(x: int | float) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Numeric" in updated
    assert "int | float" not in updated
    assert any(
        "Canonicalized inline union -> t.Numeric" == change for change in changes
    )


def test_replaces_scalar_union() -> None:
    source = "def foo(x: str | int | float | bool | datetime) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Scalar" in updated
    assert "str | int | float | bool | datetime" not in updated
    assert any("Canonicalized inline union -> t.Scalar" == change for change in changes)


def test_replaces_container_union() -> None:
    source = (
        "def foo(x: str | int | float | bool | datetime | Path) -> None:\n    pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Container" in updated
    assert "str | int | float | bool | datetime | Path" not in updated
    assert any(
        "Canonicalized inline union -> t.Container" == change for change in changes
    )


def test_injects_t_import_when_needed() -> None:
    source = "def foo(x: str | int | float | bool) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from flext_core import t" in updated
    assert "x: t.Primitives" in updated
    assert any("Added import: from flext_core import t" == change for change in changes)


def test_skips_union_with_none() -> None:
    source = "def foo(x: str | int | float | bool | None) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "str | int | float | bool | None" in updated
    assert "t.Primitives" not in updated
    assert changes == []


def test_skips_definition_files() -> None:
    source = "def foo(x: str | int | float | bool) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree, file_path=Path("typings.py"))
    updated = updated_tree.code
    assert "str | int | float | bool" in updated
    assert "t.Primitives" not in updated
    assert "from flext_core import t" not in updated
    assert changes == []


def test_preserves_non_matching_unions() -> None:
    source = "def foo(x: str | bytes) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "str | bytes" in updated
    assert "from flext_core import t" not in updated
    assert changes == []


def test_noop_clean_module() -> None:
    source = (
        "from __future__ import annotations\n\ndef foo(x: str) -> None:\n    pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert updated == source
    assert changes == []
