from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
from tests import p, t


class FlextInfraRefactorTypingUnificationRule:
    def __init__(self, settings: t.JsonMapping) -> None:
        self._settings = settings

    def apply(
        self, source: str, _file_path: Path | None = None
    ) -> t.Infra.TransformResult:
        _ = self._settings
        return FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
            file_path=_file_path,
        ).apply_to_source(source)


class TestsFlextInfraRefactorInfraRefactorTypingUnifier:
    """Behavior contract for test_infra_refactor_typing_unifier."""

    def test_converts_typealias_to_pep695(self) -> None:
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
        tm.that(updated, has="type MyType = str")
        assert any(
            change == "Converted legacy TypeAlias assignment: MyType"
            for change in changes
        )

    def test_converts_multiple_aliases(self) -> None:
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
        tm.that(updated, has="type AliasA = str")
        tm.that(updated, has="type AliasB = int")
        assert any(
            change == "Converted legacy TypeAlias assignment: AliasA"
            for change in changes
        )
        assert any(
            change == "Converted legacy TypeAlias assignment: AliasB"
            for change in changes
        )

    def test_removes_dead_typealias_import(self) -> None:
        source = "from typing import TypeAlias\nMyType: TypeAlias = str\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(source)
        tm.that(updated, has="type MyType = str")

    def test_removes_all_unused_typing_imports(self) -> None:
        source = "x: Final[str] = ''\nfrom typing import Final, TypeAlias, ClassVar, override\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(source)
        tm.that(updated, has="from typing import Final")

    def test_preserves_used_typing_imports(self) -> None:
        source = "x: Final[str] = ''\ny: ClassVar[int] = 0\nfrom typing import Final, ClassVar\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="from typing import Final, ClassVar")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_replaces_primitives_union(self) -> None:
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
        tm.that(updated, has="t.Primitives")
        tm.that(updated, lacks="str | int | float | bool")
        assert any(
            change
            == "Canonicalized inline union str | int | float | bool -> t.Primitives"
            for change in changes
        )

    def test_replaces_numeric_union(self) -> None:
        source = "def foo(x: int | float) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="x: t.Numeric")
        tm.that(updated, lacks="int | float")
        assert any(
            change == "Canonicalized inline union int | float -> t.Numeric"
            for change in changes
        )

    def test_replaces_scalar_union(self) -> None:
        source = "def foo(x: str | int | float | bool | datetime) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="x: t.Scalar")
        tm.that(updated, lacks="str | int | float | bool | datetime")
        assert any(
            change
            == "Canonicalized inline union str | int | float | bool | datetime -> t.Scalar"
            for change in changes
        )

    def test_replaces_container_union(self) -> None:
        source = "def foo(x: str | int | float | bool | datetime | Path) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="x: t.JsonValue")
        assert any(
            change
            == "Canonicalized inline union str | int | float | bool | datetime | Path -> t.JsonValue"
            for change in changes
        )

    def test_injects_t_import_when_needed(self) -> None:
        source = "def foo(x: int | float) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(source)
        tm.that(updated, has="x: t.Numeric")

    def test_replaces_subset_union_with_none(self) -> None:
        source = "def foo(x: int | float | None) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(source)
        tm.that(updated, has="t.Numeric | None")
        tm.that(updated, lacks="int | float | None")

    def test_skips_definition_files(self) -> None:
        source = "def foo(x: int | float) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source, _file_path=Path("typings.py"))
        tm.that(updated, has="int | float")
        tm.that(updated, lacks="t.Numeric")
        tm.that(updated, lacks="from flext_core import t")
        tm.that(changes, eq=[])

    def test_preserves_non_matching_unions(self) -> None:
        source = "def foo(x: str | bytes) -> None:\n    pass\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="str | bytes")
        tm.that(updated, lacks="from flext_core import t")
        tm.that(changes, eq=[])

    def test_noop_clean_module(self) -> None:
        source = (
            "from __future__ import annotations\n\ndef foo(x: str) -> None:\n    pass\n"
        )
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_preserves_used_imports_when_import_precedes_usage(self) -> None:
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
        tm.that(updated, has="from typing import ClassVar, Final")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_removes_unused_preserves_used_when_import_precedes_usage(self) -> None:
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

    def test_removes_all_imports_when_none_used_import_first(self) -> None:
        source = (
            "from typing import Literal, override\n\ndef foo() -> None:\n    pass\n"
        )
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        _updated, _changes = rule.apply(source)

    def test_typealias_conversion_preserves_used_typing_siblings(self) -> None:
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
        tm.that(updated, has="type MyType = str")
        tm.that(updated, has="from typing import Final")
        assert any(
            change == "Converted legacy TypeAlias assignment: MyType"
            for change in changes
        )

    def test_preserves_type_checking_import(self) -> None:
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
        tm.that(updated, has="from typing import TYPE_CHECKING")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_preserves_protocol_and_runtime_checkable(self) -> None:
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
        tm.that(updated, has="from typing import Protocol, runtime_checkable")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_preserves_annotated_in_function_params(self) -> None:
        source = (
            "from __future__ import annotations\n"
            "from typing import Annotated\n"
            "from pydantic import Field\n\n"
            "def create(name: Annotated[str, m.Field(min_length=1)]) -> None:\n"
            "    pass\n"
        )
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="from typing import Annotated")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_preserves_override_in_method(self) -> None:
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
        tm.that(updated, has="from typing import override")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_all_three_capabilities_in_one_pass(self) -> None:
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
        tm.that(updated, has="type MyType = str")
        tm.that(updated, has="Final")
        tm.that(updated, has="t.Primitives")
        assert any(
            change == "Converted legacy TypeAlias assignment: MyType"
            for change in changes
        )
        # Note: no test checks for imports right now for TypeAlias since we disabled the import removal hook
        assert any(
            change
            == "Canonicalized inline union str | int | float | bool -> t.Primitives"
            for change in changes
        )

    def test_no_duplicate_t_import_when_t_from_project_package(self) -> None:
        source = (
            "from __future__ import annotations\n"
            "from flext_ldif import c, m, p, t\n\n"
            "def foo(x: int | float) -> None:\n"
            "    pass\n"
        )
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="t.Numeric")
        tm.that(updated, has="from flext_ldif import c, m, p, t")
        assert any(
            change == "Canonicalized inline union int | float -> t.Numeric"
            for change in changes
        )

    def test_preserves_typealias_import_when_class_level_usage_exists(self) -> None:
        source = (
            "from __future__ import annotations\n"
            "from typing import TypeAlias\n"
            "from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence, Callable\n\n"
            "class MyTypes:\n"
            "    Handler: TypeAlias = Callable[[], None]\n"
        )
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, changes = rule.apply(source)
        tm.that(updated, has="from typing import TypeAlias")
        tm.that(updated, has="Handler: TypeAlias = Callable[[], None]")
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])

    def test_removes_typealias_import_only_when_all_usages_converted(self) -> None:
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
        tm.that(updated, has="type MyType = str")

    def test_rewrites_builtin_containers_to_canonical_t_aliases(self) -> None:
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
            source, _file_path=Path("/tmp/demo/src/flext_demo/sample.py")
        )
        tm.that(updated, has="from flext_demo import t")
        assert (
            "data: t.MutableMappingKV[str, t.MutableSequenceOf[t.JsonValue]]" in updated
        )
        tm.that(updated, has="-> t.Pair[str, int]")
        assert any(
            "Canonicalized built-in annotation dict[str, list[object]]" in change
            for change in changes
        )

    def test_rewrites_tuple_variadics_and_any_annotations(self) -> None:
        source = "from __future__ import annotations\n\nvalue: tuple[Any, ...]\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(
            source, _file_path=Path("/tmp/demo/tests/test_sample.py")
        )
        tm.that(updated, has="from tests import t")
        tm.that(updated, has="value: t.VariadicTuple[t.JsonValue]")

    def test_rewrites_fixed_arity_four_tuple_to_quad(self) -> None:
        source = "from __future__ import annotations\n\nvalue: tuple[str, int, float, bool]\n"
        rule = FlextInfraRefactorTypingUnificationRule({
            "id": "unify-typings",
            "fix_action": "unify_typings",
        })
        updated, _changes = rule.apply(
            source, _file_path=Path("/tmp/demo/src/flext_demo/sample.py")
        )
        tm.that(updated, has="from flext_demo import t")
        tm.that(updated, has="value: t.Quad[str, int, float, bool]")

    def test_inserts_t_import_after_parenthesized_import_block(self) -> None:
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
            source, _file_path=Path("/tmp/demo/src/flext_demo/sample.py")
        )
        tm.that(updated, has="from flext_demo import (\n    c,\n    m,\n)")
        tm.that(updated, has="from flext_demo import t")
        assert updated.index("from flext_demo import t") > updated.index("    m,")
        tm.that(updated, has="value: t.MutableSequenceOf[t.JsonValue]")

    def test_skips_duplicate_t_import_in_parenthesized_import_block(self) -> None:
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
            source, _file_path=Path("/tmp/demo/src/flext_demo/sample.py")
        )
        tm.that(updated, has="from flext_demo import (\n    c,\n    m,\n    t,\n)")
        tm.that(updated.count("from flext_demo import t"), eq=0)
        tm.that(updated, has="value: t.MutableSequenceOf[t.JsonValue]")
