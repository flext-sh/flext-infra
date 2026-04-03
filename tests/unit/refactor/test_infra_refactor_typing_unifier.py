from __future__ import annotations

from pathlib import Path

import libcst as cst

from flext_infra import (
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
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )
    assert any(change == "Removed typing import: TypeAlias" for change in changes)


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
        change == "Converted legacy TypeAlias assignment: AliasA" for change in changes
    )
    assert any(
        change == "Converted legacy TypeAlias assignment: AliasB" for change in changes
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
    assert any(change == "Removed empty typing import" for change in changes)


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
    assert any(change == "Removed typing import: TypeAlias" for change in changes)
    assert any(change == "Removed unused typing import: ClassVar" for change in changes)
    assert any(change == "Removed unused typing import: override" for change in changes)


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
        "def foo(x: t.Primitives) -> None:\n"
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
    assert "t.Primitives" not in updated
    assert "from flext_core import t" in updated
    assert any(
        change == "Canonicalized inline union -> t.Primitives" for change in changes
    )


def test_replaces_numeric_union() -> None:
    source = "def foo(x: t.Numeric) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Numeric" in updated
    assert "t.Numeric" not in updated
    assert any(
        change == "Canonicalized inline union -> t.Numeric" for change in changes
    )


def test_replaces_scalar_union() -> None:
    source = "def foo(x: t.Primitives | datetime) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Scalar" in updated
    assert "t.Primitives | datetime" not in updated
    assert any(change == "Canonicalized inline union -> t.Scalar" for change in changes)


def test_replaces_container_union() -> None:
    source = "def foo(x: t.Container) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "x: t.Container" in updated
    assert "t.Container" not in updated
    assert any(
        change == "Canonicalized inline union -> t.Container" for change in changes
    )


def test_injects_t_import_when_needed() -> None:
    source = "def foo(x: t.Primitives) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from flext_core import t" in updated
    assert "x: t.Primitives" in updated
    assert any(change == "Added import: from flext_core import t" for change in changes)


def test_skips_union_with_none() -> None:
    source = "def foo(x: t.Primitives | None) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "t.Primitives | None" in updated
    assert "t.Primitives" not in updated
    assert changes == []


def test_skips_definition_files() -> None:
    source = "def foo(x: t.Primitives) -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree, _file_path=Path("typings.py"))
    updated = updated_tree.code
    assert "t.Primitives" in updated
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


def test_preserves_used_imports_when_import_precedes_usage() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import ClassVar, Final\n\n"
        "class Foo:\n"
        "    X: ClassVar[str] = 'hello'\n"
        "    Y: Final[int] = 42\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import ClassVar, Final" in updated
    assert updated == source
    assert changes == []


def test_removes_unused_preserves_used_when_import_precedes_usage() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import ClassVar, Final, Literal, override\n\n"
        "class Config:\n"
        "    NAME: Final[str] = 'app'\n"
        "    ITEMS: ClassVar[t.StrSequence] = []\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "Final" in updated
    assert "ClassVar" in updated
    assert "Literal" not in updated
    assert "override" not in updated
    assert any(change == "Removed unused typing import: Literal" for change in changes)
    assert any(change == "Removed unused typing import: override" for change in changes)


def test_removes_all_imports_when_none_used_import_first() -> None:
    source = "from typing import Literal, override\n\ndef foo() -> None:\n    pass\n"
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing" not in updated
    assert any(change == "Removed empty typing import" for change in changes)


def test_typealias_conversion_preserves_used_typing_siblings() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import Final, TypeAlias\n\n"
        "MyType: TypeAlias = str\n"
        "TIMEOUT: Final[int] = 30\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "type MyType = str" in updated
    assert "from typing import Final" in updated
    assert "TypeAlias" not in updated
    assert any(
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )
    assert any(change == "Removed typing import: TypeAlias" for change in changes)


def test_preserves_type_checking_import() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from pathlib import Path\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import TYPE_CHECKING" in updated
    assert updated == source
    assert changes == []


def test_preserves_protocol_and_runtime_checkable() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import Protocol, runtime_checkable\n\n"
        "@runtime_checkable\n"
        "class Connectable(Protocol):\n"
        "    def connect(self) -> None: ...\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import Protocol, runtime_checkable" in updated
    assert updated == source
    assert changes == []


def test_preserves_annotated_in_function_params() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import Annotated\n"
        "from pydantic import Field\n\n"
        "def create(name: Annotated[str, Field(min_length=1)]) -> None:\n"
        "    pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import Annotated" in updated
    assert updated == source
    assert changes == []


def test_preserves_override_in_method() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import override\n\n"
        "class Child:\n"
        "    @override\n"
        "    def run(self) -> None:\n"
        "        pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import override" in updated
    assert updated == source
    assert changes == []


def test_all_three_capabilities_in_one_pass() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias, Final\n\n"
        "MyType: TypeAlias = str\n\n"
        "def foo(x: t.Primitives) -> Final[str]:\n"
        "    pass\n"
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
    assert "from typing import Final" in updated
    assert "t.Primitives" in updated
    assert "from flext_core import t" in updated
    assert any(
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )
    assert any(change == "Removed typing import: TypeAlias" for change in changes)
    assert any(
        change == "Canonicalized inline union -> t.Primitives" for change in changes
    )
    assert any(change == "Added import: from flext_core import t" for change in changes)


def test_no_duplicate_t_import_when_t_from_project_package() -> None:
    source = (
        "from __future__ import annotations\n"
        "from flext_ldif import c, m, t\n\n"
        "def foo(x: t.Numeric) -> None:\n"
        "    pass\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "t.Numeric" in updated
    assert "from flext_core import t" not in updated
    assert "from flext_ldif import c, m, t" in updated
    assert updated.count("from flext_core") == 0
    assert any(
        change == "Canonicalized inline union -> t.Numeric" for change in changes
    )
    assert not any(
        change == "Added import: from flext_core import t" for change in changes
    )


def test_preserves_typealias_import_when_class_level_usage_exists() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias\n"
        "from collections.abc import Sequence, Callable\n\n"
        "class MyTypes:\n"
        "    Handler: TypeAlias = Callable[[], None]\n"
    )
    tree = cst.parse_module(source)
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated_tree, changes = rule.apply(tree)
    updated = updated_tree.code
    assert "from typing import TypeAlias" in updated
    assert "Handler: TypeAlias = Callable[[], None]" in updated
    assert updated == source
    assert changes == []


def test_removes_typealias_import_only_when_all_usages_converted() -> None:
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
    assert any(change == "Removed typing import: TypeAlias" for change in changes)
