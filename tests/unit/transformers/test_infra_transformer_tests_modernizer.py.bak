"""Unit tests for the tests modernizer transformer."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra.transformers.tests_modernizer import FlextInfraRefactorTestsModernizer
from flext_tests import tm


def _modernized(source: str) -> tuple[str, list[str]]:
    """Apply the tests modernizer and validate its return contract."""
    transformer = FlextInfraRefactorTestsModernizer()
    code, changes = transformer.apply_to_source(source)
    if not isinstance(code, str):
        msg = "tests modernizer returned non-string source"
        raise TypeError(msg)
    if not isinstance(changes, Sequence):
        msg = "tests modernizer returned non-sequence changes"
        raise TypeError(msg)
    change_list: list[str] = []
    for change in changes:
        if not isinstance(change, str):
            msg = "tests modernizer returned non-string change"
            raise TypeError(msg)
        change_list.append(change)
    return code, change_list


def _transform(source: str) -> str:
    """Apply the tests modernizer to source text."""
    code, _changes = _modernized(source)
    return code


def _transform_with_changes(source: str) -> tuple[str, list[str]]:
    """Apply the tests modernizer and return code plus change descriptions."""
    return _modernized(source)


class TestsFlextInfraTransformersTestsModernizer:
    """Behavior contract for FlextInfraRefactorTestsModernizer."""

    def test_import_unittest_removed(self) -> None:
        source = "import unittest\n\nclass TestFoo(unittest.TestCase):\n    pass\n"
        code = _transform(source)
        tm.that(code, lacks="import unittest")

    def test_class_inheriting_unittest_testcase_rewritten(self) -> None:
        source = (
            "import unittest\n\n"
            "class TestFoo(unittest.TestCase):\n"
            "    def test_foo(self):\n"
            "        pass\n"
        )
        code = _transform(source)
        tm.that(code, has="class TestsFlextFoo(FlextTestsCase):")
        tm.that(code, lacks="class TestFoo(unittest.TestCase):")
        tm.that(code, has="from flext_tests.base import FlextTestsCase")

    def test_assert_equal_rewritten_with_tm_import(self) -> None:
        source = (
            "import unittest\n\n"
            "class TestFoo(unittest.TestCase):\n"
            "    def test_foo(self):\n"
            "        self.assertEqual(1, 2)\n"
        )
        code = _transform(source)
        tm.that(code, has="tm.that(1, eq=2)")
        tm.that(code, lacks="self.assertEqual(1, 2)")
        tm.that(code, has="from tests import tm")

    def test_assert_true_rewritten(self) -> None:
        source = (
            "import unittest\n\n"
            "class TestFoo(unittest.TestCase):\n"
            "    def test_foo(self):\n"
            "        self.assertTrue(x)\n"
        )
        code = _transform(source)
        tm.that(code, has="tm.that(x, eq=True)")
        tm.that(code, lacks="self.assertTrue(x)")

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = "from tests import tm\n\ndef foo():\n    pass\n"
        code, changes = _transform_with_changes(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])
