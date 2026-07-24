"""Tests for the rope-native syntactic structure boundary."""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c, m, u

_SOURCE = (
    "from typing import ClassVar, TYPE_CHECKING\n"
    "import importlib\n"
    "if TYPE_CHECKING:\n"
    "    from foo import Bar\n"
    "type MyAlias = int\n"
    "class Widget:\n"
    "    CONST: ClassVar[int] = 1\n"
    "    plain = 2\n"
    "    def method(self):\n"
    "        import os\n"
    "        return os\n"
)


class TestsFlextInfraRopeStructure:
    """Behavior contract for the LogicalLineFinder-backed structure boundary."""

    @staticmethod
    def _by_line() -> dict[int, m.Infra.LogicalStatement]:
        return {s.line: s for s in u.Infra.logical_statements(_SOURCE)}

    def test_reports_real_statement_lines_not_target_module_lines(self) -> None:
        by_line = self._by_line()

        inline_import = by_line[10]

        tm.that(inline_import.category, eq=c.Infra.StatementCategory.IMPORT)
        tm.that(inline_import.text.strip(), eq="import os")

    def test_categorizes_pep695_type_alias(self) -> None:
        by_line = self._by_line()

        tm.that(by_line[5].category, eq=c.Infra.StatementCategory.TYPE_ALIAS)

    def test_categorizes_type_checking_guard(self) -> None:
        by_line = self._by_line()

        tm.that(by_line[3].category, eq=c.Infra.StatementCategory.IF_GUARD)

    def test_tracks_enclosing_class_for_classvar(self) -> None:
        by_line = self._by_line()

        classvar = by_line[7]

        tm.that(classvar.category, eq=c.Infra.StatementCategory.ANN_ASSIGN)
        tm.that(classvar.enclosing_kind, eq=c.Infra.RopeScopeKind.CLASS)
        tm.that(classvar.enclosing_name, eq="Widget")

    def test_tracks_enclosing_function_for_inline_import(self) -> None:
        by_line = self._by_line()

        inline_import = by_line[10]

        tm.that(inline_import.enclosing_kind, eq=c.Infra.RopeScopeKind.FUNCTION)
        tm.that(inline_import.enclosing_name, eq="method")

    def test_module_level_statement_has_module_encloser(self) -> None:
        by_line = self._by_line()

        tm.that(by_line[2].enclosing_kind, eq=c.Infra.RopeScopeKind.MODULE)

    def test_empty_source_returns_no_statements(self) -> None:
        tm.that(u.Infra.logical_statements(""), eq=())
