"""Unit tests for the enforcement fixer transformers.

Covers the small, targeted source-to-source transformers used by the
flext-infra enforcement pipeline.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra.transformers.bare_except import FlextInfraRefactorBareExcept
from flext_infra.transformers.compatibility_alias import (
    FlextInfraRefactorCompatibilityAlias,
)
from flext_infra.transformers.future_import import FlextInfraRefactorFutureImport
from flext_infra.transformers.hardcoded_version import (
    FlextInfraRefactorHardcodedVersion,
)
from flext_infra.transformers.open_encoding import FlextInfraRefactorOpenEncoding
from flext_infra.transformers.print_to_logger import FlextInfraRefactorPrintToLogger
from flext_infra.transformers.remove_breakpoint import (
    FlextInfraRefactorRemoveBreakpoint,
)
from flext_infra.transformers.typing_dict_attr import (
    FlextInfraRefactorTypingDictAttr,
)
from flext_infra.transformers.typing_dict_import import (
    FlextInfraRefactorTypingDictImport,
)
from flext_infra.transformers.typing_unifier import (
    FlextInfraRefactorTypingUnifier,
)


def _transform(
    source: str,
    transformer: FlextInfraRefactorBareExcept
    | FlextInfraRefactorCompatibilityAlias
    | FlextInfraRefactorFutureImport
    | FlextInfraRefactorHardcodedVersion
    | FlextInfraRefactorOpenEncoding
    | FlextInfraRefactorRemoveBreakpoint
    | FlextInfraRefactorTypingDictAttr
    | FlextInfraRefactorTypingDictImport
    | FlextInfraRefactorTypingUnifier,
) -> tuple[str, Sequence[str]]:
    """Apply a stateless transformer to source text."""
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


def _transform_print(tmp_path: Path, source: str) -> tuple[str, Sequence[str]]:
    """Apply the print-to-logger transformer with a synthetic package path."""
    package_root = tmp_path / "flext_core" / "src" / "flext_core"
    package_root.mkdir(parents=True)
    file_path = package_root / "module.py"
    transformer = FlextInfraRefactorPrintToLogger(file_path=file_path)
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersFutureImport:
    """Behavior contract for FlextInfraRefactorFutureImport."""

    def test_future_import_already_present_is_unchanged(self) -> None:
        source = "from __future__ import annotations\n\nx = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        assert code == source
        assert changes == []

    def test_future_import_inserted_at_top_when_absent(self) -> None:
        source = "x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        assert code == "from __future__ import annotations\nx = 1\n"
        assert changes

    def test_future_import_inserted_after_shebang_and_comments(self) -> None:
        source = (
            "#!/usr/bin/env python3\n"
            "# -*- coding: utf-8 -*-\n"
            "# leading comment\n"
            "\n"
            "x = 1\n"
        )
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        expected = (
            "#!/usr/bin/env python3\n"
            "# -*- coding: utf-8 -*-\n"
            "# leading comment\n"
            "\n"
            "from __future__ import annotations\n"
            "x = 1\n"
        )
        assert code == expected
        assert changes

    def test_future_import_normalizes_duplicate_before_docstring(self) -> None:
        source = (
            "from __future__ import annotations\n"
            '"""Module docstring."""\n'
            "\n"
            "from __future__ import annotations\n"
            "\n"
            "import os\n"
        )
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        expected = (
            '"""Module docstring."""\n'
            "\n"
            "from __future__ import annotations\n"
            "\n"
            "import os\n"
        )
        assert code == expected
        assert changes


class TestsFlextInfraTransformersBareExcept:
    """Behavior contract for FlextInfraRefactorBareExcept."""

    def test_bare_except_rewritten_to_exception(self) -> None:
        source = "def foo():\n    try:\n        pass\n    except:\n        pass\n"
        code, changes = _transform(source, FlextInfraRefactorBareExcept())
        assert "    except Exception:\n" in code
        assert "    except:\n" not in code
        assert changes

    def test_bare_except_preserves_indentation(self) -> None:
        source = "try:\n    pass\nexcept:\n    pass\n"
        code, _ = _transform(source, FlextInfraRefactorBareExcept())
        assert "except Exception:\n" in code
        assert "except:\n" not in code

    def test_specific_except_unchanged(self) -> None:
        source = (
            "def foo():\n    try:\n        pass\n    except ValueError:\n        pass\n"
        )
        code, changes = _transform(source, FlextInfraRefactorBareExcept())
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersRemoveBreakpoint:
    """Behavior contract for FlextInfraRefactorRemoveBreakpoint."""

    def test_breakpoint_call_removed(self) -> None:
        source = "def foo():\n    breakpoint()\n    x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "breakpoint()" not in code
        assert "x = 1\n" in code
        assert changes

    def test_import_pdb_set_trace_removed(self) -> None:
        source = "import pdb; pdb.set_trace()\n"
        code, changes = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "import pdb" not in code
        assert "pdb.set_trace()" not in code
        assert changes

    def test_adjacent_blank_lines_preserved(self) -> None:
        source = "x = 1\n\nbreakpoint()\n\ny = 2\n"
        code, _ = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "breakpoint()" not in code
        assert "x = 1\n" in code
        assert "y = 2\n" in code
        assert "\n" in code


class TestsFlextInfraTransformersOpenEncoding:
    """Behavior contract for FlextInfraRefactorOpenEncoding."""

    def test_open_without_encoding_gets_utf8(self) -> None:
        source = 'with open("x.txt") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", encoding="utf-8")' in code
        assert changes

    def test_open_with_mode_gets_utf8(self) -> None:
        source = 'with open("x.txt", "w") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", "w", encoding="utf-8")' in code
        assert changes

    def test_open_with_multiple_args_gets_utf8(self) -> None:
        source = 'with open("x.txt", "w", buffering=1) as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", "w", buffering=1, encoding="utf-8")' in code
        assert changes

    def test_open_with_encoding_unchanged(self) -> None:
        source = 'with open("x.txt", encoding="latin-1") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersPrintToLogger:
    """Behavior contract for FlextInfraRefactorPrintToLogger."""

    def test_print_rewritten_to_fetch_logger_info(self, tmp_path: Path) -> None:
        source = 'print("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert 'u.fetch_logger(__name__).info("hello")' in code
        assert "print(" not in code
        assert changes

    def test_u_import_added_when_missing(self, tmp_path: Path) -> None:
        source = 'print("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert "from flext_core import u" in code
        assert changes

    def test_u_import_not_duplicated(self, tmp_path: Path) -> None:
        source = 'from flext_core import c, u\n\nprint("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert code.count("from flext_core import") == 1
        assert "from flext_core import c, u" in code
        assert 'u.fetch_logger(__name__).info("hello")' in code
        assert changes


class TestsFlextInfraTransformersTypingDictImport:
    """Behavior contract for FlextInfraRefactorTypingDictImport."""

    def test_typing_dict_import_removed_and_rewritten(self, tmp_path: Path) -> None:
        source = (
            "from typing import Dict, List\n\n"
            "def foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert "from typing import Dict" not in code
        assert "from typing import List" in code
        assert "t.MappingKV[str, int]" in code
        assert "from flext_core import t" in code
        assert changes

    def test_typing_dict_import_only_removed_when_empty(
        self,
        tmp_path: Path,
    ) -> None:
        source = (
            "from typing import Dict\n\ndef foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert "from typing import" not in code
        assert "t.MappingKV[str, int]" in code
        assert changes

    def test_t_import_not_duplicated(self, tmp_path: Path) -> None:
        source = (
            "from typing import Dict\n"
            "from flext_core import t\n\n"
            "def foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert code.count("from flext_core import t") == 1
        assert "t.MappingKV[str, int]" in code
        assert changes

    def test_no_dict_does_not_add_t_import(self, tmp_path: Path) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersTypingDictAttr:
    """Behavior contract for FlextInfraRefactorTypingDictAttr."""

    def test_typing_dict_attr_rewritten(self, tmp_path: Path) -> None:
        source = (
            "import typing\n\ndef foo(x: typing.Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert "typing.Dict" not in code
        assert "t.MappingKV[str, int]" in code
        assert "from flext_core import t" in code
        assert changes

    def test_t_import_not_duplicated(self, tmp_path: Path) -> None:
        source = (
            "import typing\n"
            "from flext_core import t\n\n"
            "def foo(x: typing.Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert code.count("from flext_core import t") == 1
        assert "t.MappingKV[str, int]" in code
        assert changes

    def test_no_typing_dict_does_not_add_t_import(self, tmp_path: Path) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersTypingUnifier:
    """Behavior contract for FlextInfraRefactorTypingUnifier."""

    def test_builtin_annotation_canonicalized(self, tmp_path: Path) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "def foo(x: dict[str, int]) -> list[str]:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map={},
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert "t.MutableMappingKV[str, int]" in code
        assert "t.MutableSequenceOf[str]" in code
        assert "from flext_core import t" in code
        assert changes

    def test_no_builtin_annotation_does_not_add_t_import(
        self,
        tmp_path: Path,
    ) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map={},
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersHardcodedVersion:
    """Behavior contract for FlextInfraRefactorHardcodedVersion."""

    def test_hardcoded_version_reported(self) -> None:
        source = '__version__ = "1.2.3"\n'
        code, changes = _transform(source, FlextInfraRefactorHardcodedVersion())
        assert code == source
        assert changes
        assert "importlib.metadata" in changes[0]

    def test_no_version_unchanged(self) -> None:
        source = "x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorHardcodedVersion())
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersCompatibilityAlias:
    """Behavior contract for FlextInfraRefactorCompatibilityAlias."""

    def test_compat_assignment_removed_and_references_rewritten(self) -> None:
        source = (
            "from flext_core import FlextConstants\n\n"
            "FC = FlextConstants\n\n"
            "def foo():\n"
            "    return FC.SOME_VALUE\n"
        )
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        assert "FC = FlextConstants\n" not in code
        assert "FlextConstants.SOME_VALUE" in code
        assert changes

    def test_compat_import_rewritten_to_canonical_alias(self) -> None:
        source = (
            "from flext_core import FlextConstants\n\n"
            "def foo():\n"
            "    return FlextConstants.SOME_VALUE\n"
        )
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        assert "from flext_core import c\n" in code
        assert "FlextConstants.SOME_VALUE" not in code
        assert "c.SOME_VALUE" in code
        assert changes

    def test_skip_names_preserved(self) -> None:
        source = "__version__ = __version_info__\n"
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        assert code == source
        assert changes == []

    def test_same_name_assignment_preserved(self) -> None:
        source = "Foo = Foo\n"
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        assert code == source
        assert changes == []
