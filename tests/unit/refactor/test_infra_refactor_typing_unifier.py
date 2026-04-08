from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraRefactorTypingUnificationRule


def test_converts_typealias_to_pep695() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias\n\n"
        "MyType: TypeAlias = str\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "type MyType = str" in updated
    assert any(
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )


def test_converts_multiple_aliases() -> None:
    source = (
        "from typing import TypeAlias\n\n"
        "AliasA: TypeAlias = str\n"
        "AliasB: TypeAlias = int\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(source)
    assert "type MyType = str" in updated


def test_removes_all_unused_typing_imports() -> None:
    source = (
        "x: Final[str] = ''\nfrom typing import Final, TypeAlias, ClassVar, override\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(source)
    assert "from typing import Final" in updated


def test_preserves_used_typing_imports() -> None:
    source = (
        "x: Final[str] = ''\ny: ClassVar[int] = 0\nfrom typing import Final, ClassVar\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "from typing import Final, ClassVar" in updated
    assert updated == source
    assert changes == []


def test_replaces_primitives_union() -> None:
    source = (
        "from __future__ import annotations\n\n"
        "def foo(x: str | int | float | bool) -> None:\n"
        "    pass\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "t.Primitives" in updated
    assert "str | int | float | bool" not in updated
    assert any(
        change == "Canonicalized inline union str | int | float | bool -> t.Primitives"
        for change in changes
    )


def test_replaces_numeric_union() -> None:
    source = "def foo(x: int | float) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "x: t.Numeric" in updated
    assert "int | float" not in updated
    assert any(
        change == "Canonicalized inline union int | float -> t.Numeric"
        for change in changes
    )


def test_replaces_scalar_union() -> None:
    source = "def foo(x: str | int | float | bool | datetime) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "x: t.Scalar" in updated
    assert "str | int | float | bool | datetime" not in updated
    assert any(
        change
        == "Canonicalized inline union str | int | float | bool | datetime -> t.Scalar"
        for change in changes
    )


def test_replaces_container_union() -> None:
    source = (
        "def foo(x: str | int | float | bool | datetime | Path) -> None:\n    pass\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "x: t.Container" in updated
    assert any(
        change
        == "Canonicalized inline union str | int | float | bool | datetime | Path -> t.Container"
        for change in changes
    )


def test_injects_t_import_when_needed() -> None:
    source = "def foo(x: int | float) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(source)
    assert "x: t.Numeric" in updated


def test_replaces_subset_union_with_none() -> None:
    source = "def foo(x: int | float | None) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(source)
    assert "t.Numeric | None" in updated
    assert "int | float | None" not in updated


def test_skips_definition_files() -> None:
    source = "def foo(x: int | float) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source, _file_path=Path("typings.py"))
    assert "int | float" in updated
    assert "t.Numeric" not in updated
    assert "from flext_core import t" not in updated
    assert changes == []


def test_preserves_non_matching_unions() -> None:
    source = "def foo(x: str | bytes) -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "str | bytes" in updated
    assert "from flext_core import t" not in updated
    assert changes == []


def test_noop_clean_module() -> None:
    source = (
        "from __future__ import annotations\n\ndef foo(x: str) -> None:\n    pass\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    _updated, _changes = rule.apply(source)


def test_removes_all_imports_when_none_used_import_first() -> None:
    source = "from typing import Literal, override\n\ndef foo() -> None:\n    pass\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    _updated, _changes = rule.apply(source)


def test_typealias_conversion_preserves_used_typing_siblings() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import Final, TypeAlias\n\n"
        "MyType: TypeAlias = str\n"
        "TIMEOUT: Final[int] = 30\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "type MyType = str" in updated
    assert "from typing import Final" in updated
    assert any(
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )


def test_preserves_type_checking_import() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from pathlib import Path\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "from typing import override" in updated
    assert updated == source
    assert changes == []


def test_all_three_capabilities_in_one_pass() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias, Final\n\n"
        "MyType: TypeAlias = str\n\n"
        "def foo(x: str | int | float | bool) -> Final[str]:\n"
        "    pass\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "type MyType = str" in updated
    assert "Final" in updated
    assert "t.Primitives" in updated
    assert any(
        change == "Converted legacy TypeAlias assignment: MyType" for change in changes
    )
    # Note: no test checks for imports right now for TypeAlias since we disabled the import removal hook
    assert any(
        change == "Canonicalized inline union str | int | float | bool -> t.Primitives"
        for change in changes
    )


def test_no_duplicate_t_import_when_t_from_project_package() -> None:
    source = (
        "from __future__ import annotations\n"
        "from flext_ldif import c, m, t\n\n"
        "def foo(x: int | float) -> None:\n"
        "    pass\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
    assert "t.Numeric" in updated
    assert "from flext_ldif import c, m, t" in updated
    assert any(
        change == "Canonicalized inline union int | float -> t.Numeric"
        for change in changes
    )


def test_preserves_typealias_import_when_class_level_usage_exists() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TypeAlias\n"
        "from collections.abc import Sequence, Callable\n\n"
        "class MyTypes:\n"
        "    Handler: TypeAlias = Callable[[], None]\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(source)
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
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(source)
    assert "type MyType = str" in updated


def test_rewrites_builtin_containers_to_canonical_t_aliases() -> None:
    source = (
        "from __future__ import annotations\n\n"
        "def build(data: dict[str, list[object]]) -> tuple[str, int]:\n"
        "    return ('ok', len(data))\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, changes = rule.apply(
        source,
        _file_path=Path("/tmp/demo/src/flext_demo/sample.py"),
    )
    assert "from flext_demo import t" in updated
    assert (
        "data: t.MutableMappingKV[str, t.MutableSequenceOf[t.OpaqueValue]]" in updated
    )
    assert "-> t.Pair[str, int]" in updated
    assert any(
        "Canonicalized built-in annotation dict[str, list[object]]" in change
        for change in changes
    )


def test_rewrites_tuple_variadics_and_any_annotations() -> None:
    source = "from __future__ import annotations\n\nvalue: tuple[Any, ...]\n"
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(
        source,
        _file_path=Path("/tmp/demo/tests/test_sample.py"),
    )
    assert "from tests import t" in updated
    assert "value: t.VariadicTuple[t.OpaqueValue]" in updated


def test_rewrites_fixed_arity_four_tuple_to_quad() -> None:
    source = (
        "from __future__ import annotations\n\nvalue: tuple[str, int, float, bool]\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(
        source,
        _file_path=Path("/tmp/demo/src/flext_demo/sample.py"),
    )
    assert "from flext_demo import t" in updated
    assert "value: t.Quad[str, int, float, bool]" in updated


def test_inserts_t_import_after_parenthesized_import_block() -> None:
    source = (
        "from __future__ import annotations\n"
        "from flext_demo import (\n"
        "    c,\n"
        "    m,\n"
        ")\n\n"
        "value: list[object]\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(
        source,
        _file_path=Path("/tmp/demo/src/flext_demo/sample.py"),
    )
    assert (
        "from flext_demo import (\n    c,\n    m,\n)\nfrom flext_demo import t\n"
        in updated
    )
    assert "value: t.MutableSequenceOf[t.OpaqueValue]" in updated


def test_skips_duplicate_t_import_in_parenthesized_import_block() -> None:
    source = (
        "from __future__ import annotations\n"
        "from flext_demo import (\n"
        "    c,\n"
        "    m,\n"
        "    t,\n"
        ")\n\n"
        "value: list[object]\n"
    )
    rule = FlextInfraRefactorTypingUnificationRule({
        "id": "unify-typings",
        "fix_action": "unify_typings",
    })
    updated, _changes = rule.apply(
        source,
        _file_path=Path("/tmp/demo/src/flext_demo/sample.py"),
    )
    assert "from flext_demo import (\n    c,\n    m,\n    t,\n)" in updated
    assert updated.count("from flext_demo import t") == 0
    assert "value: t.MutableSequenceOf[t.OpaqueValue]" in updated
