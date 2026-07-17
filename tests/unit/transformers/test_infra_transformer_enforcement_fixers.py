"""Unit tests for the enforcement fixer transformers.

Covers the small, targeted source-to-source transformers used by the
flext-infra enforcement pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.compatibility_alias import (
    FlextInfraRefactorCompatibilityAlias,
)
from flext_infra.transformers.future_import import FlextInfraRefactorFutureImport
from flext_infra.transformers.hardcoded_version import (
    FlextInfraRefactorHardcodedVersion,
)
from flext_infra.transformers.open_encoding import FlextInfraRefactorOpenEncoding
from flext_infra.transformers.pattern import FlextInfraRefactorPatternTransformer
from flext_infra.transformers.typing_dict_attr import FlextInfraRefactorTypingDictAttr
from flext_infra.transformers.typing_dict_import import (
    FlextInfraRefactorTypingDictImport,
)
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
from flext_tests import tm

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def _transform(
    source: str,
    transformer: FlextInfraRefactorCompatibilityAlias
    | FlextInfraRefactorFutureImport
    | FlextInfraRefactorHardcodedVersion
    | FlextInfraRefactorOpenEncoding
    | FlextInfraRefactorPatternTransformer
    | FlextInfraRefactorTypingDictAttr
    | FlextInfraRefactorTypingDictImport
    | FlextInfraRefactorTypingUnifier,
) -> tuple[str, Sequence[str]]:
    """Apply a stateless transformer to source text."""
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersFutureImport:
    """Behavior contract for FlextInfraRefactorFutureImport."""

    def test_future_import_already_present_is_unchanged(self) -> None:
        """Verify future import already present is unchanged."""
        source = "from __future__ import annotations\n\nx = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_future_import_inserted_at_top_when_absent(self) -> None:
        """Verify future import inserted at top when absent."""
        source = "x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        tm.that(code, eq="from __future__ import annotations\nx = 1\n")
        tm.that(changes, empty=False)

    def test_future_import_inserted_after_shebang_and_comments(self) -> None:
        """Verify future import inserted after shebang and comments."""
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
        tm.that(code, eq=expected)
        tm.that(changes, empty=False)

    def test_future_import_normalizes_duplicate_before_docstring(self) -> None:
        """Verify future import normalizes duplicate before docstring."""
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
        tm.that(code, eq=expected)
        tm.that(changes, empty=False)


class TestsFlextInfraTransformersOpenEncoding:
    """Behavior contract for FlextInfraRefactorOpenEncoding."""

    def test_open_without_encoding_gets_utf8(self) -> None:
        """Verify open without encoding gets utf8."""
        source = 'with open("x.txt") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, has='open("x.txt", encoding="utf-8")')
        tm.that(changes, empty=False)

    def test_open_with_mode_gets_utf8(self) -> None:
        """Verify open with mode gets utf8."""
        source = 'with open("x.txt", "w") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, has='open("x.txt", "w", encoding="utf-8")')
        tm.that(changes, empty=False)

    def test_open_with_multiple_args_gets_utf8(self) -> None:
        """Verify open with multiple args gets utf8."""
        source = 'with open("x.txt", "w", buffering=1) as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, has='open("x.txt", "w", buffering=1, encoding="utf-8")')
        tm.that(changes, empty=False)

    def test_open_binary_mode_unchanged(self) -> None:
        """Verify open binary mode unchanged."""
        source = 'with open("x.bin", "rb") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_open_keyword_binary_mode_unchanged(self) -> None:
        """Verify open keyword binary mode unchanged."""
        source = 'with open("x.bin", mode="rb") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_open_dynamic_mode_unchanged(self) -> None:
        """Verify open dynamic mode unchanged."""
        source = 'with open("x.txt", mode) as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_path_open_text_mode_gets_utf8(self) -> None:
        """Verify path open text mode gets utf8."""
        source = 'Path("x.txt").open("w")\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, has='Path("x.txt").open("w", encoding="utf-8")')
        tm.that(changes, empty=False)

    def test_path_open_binary_mode_unchanged(self) -> None:
        """Verify path open binary mode unchanged."""
        source = 'Path("x.bin").open("rb")\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_open_with_encoding_unchanged(self) -> None:
        """Verify open with encoding unchanged."""
        source = 'with open("x.txt", encoding="latin-1") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_open_dynamic_mode_return_unchanged(self) -> None:
        """Verify open dynamic mode return unchanged."""
        source = 'def read(mode):\n    return open("x.txt", mode)\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_path_open_write_binary_mode_unchanged(self) -> None:
        """Verify path open write binary mode unchanged."""
        source = 'with Path("x.bin").open("wb") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersTypingDictImport:
    """Behavior contract for FlextInfraRefactorTypingDictImport."""

    def test_typing_dict_import_removed_and_rewritten(self, tmp_path: Path) -> None:
        """Verify typing dict import removed and rewritten."""
        source = (
            "from typing import Dict, List\n\n"
            "def foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, lacks="from typing import Dict")
        tm.that(code, has="from typing import List")
        tm.that(code, has="t.MappingKV[str, int]")
        tm.that(code, has="from flext_core import t")
        tm.that(changes, empty=False)

    def test_typing_dict_import_only_removed_when_empty(self, tmp_path: Path) -> None:
        """Verify typing dict import only removed when empty."""
        source = (
            "from typing import Dict\n\ndef foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, lacks="from typing import")
        tm.that(code, has="t.MappingKV[str, int]")
        tm.that(changes, empty=False)

    def test_t_import_not_duplicated(self, tmp_path: Path) -> None:
        """Verify t import not duplicated."""
        source = (
            "from typing import Dict\n"
            "from flext_core import t\n\n"
            "def foo(x: Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code.count("from flext_core import t"), eq=1)
        tm.that(code, has="t.MappingKV[str, int]")
        tm.that(changes, empty=False)

    def test_no_dict_does_not_add_t_import(self, tmp_path: Path) -> None:
        """Verify no dict does not add t import."""
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingDictImport(
            file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersTypingDictAttr:
    """Behavior contract for FlextInfraRefactorTypingDictAttr."""

    def test_typing_dict_attr_rewritten(self, tmp_path: Path) -> None:
        """Verify typing dict attr rewritten."""
        source = (
            "import typing\n\ndef foo(x: typing.Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(file_path=tmp_path / "module.py")
        code, changes = transformer.apply_to_source(source)
        tm.that(code, lacks="typing.Dict")
        tm.that(code, has="t.MappingKV[str, int]")
        tm.that(code, has="from flext_core import t")
        tm.that(changes, empty=False)

    def test_t_import_not_duplicated(self, tmp_path: Path) -> None:
        """Verify t import not duplicated."""
        source = (
            "import typing\n"
            "from flext_core import t\n\n"
            "def foo(x: typing.Dict[str, int]) -> None:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(file_path=tmp_path / "module.py")
        code, changes = transformer.apply_to_source(source)
        tm.that(code.count("from flext_core import t"), eq=1)
        tm.that(code, has="t.MappingKV[str, int]")
        tm.that(changes, empty=False)

    def test_no_typing_dict_does_not_add_t_import(self, tmp_path: Path) -> None:
        """Verify no typing dict does not add t import."""
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingDictAttr(file_path=tmp_path / "module.py")
        code, changes = transformer.apply_to_source(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersTypingUnifier:
    """Behavior contract for FlextInfraRefactorTypingUnifier."""

    def test_builtin_annotation_canonicalized(self, tmp_path: Path) -> None:
        """Verify builtin annotation canonicalized."""
        source = (
            "from __future__ import annotations\n\n"
            "def foo(x: dict[str, int]) -> list[str]:\n    pass\n"
        )
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map={}, file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="t.MutableMappingKV[str, int]")
        tm.that(code, has="t.MutableSequenceOf[str]")
        tm.that(code, has="from flext_core import t")
        tm.that(changes, empty=False)

    def test_no_builtin_annotation_does_not_add_t_import(self, tmp_path: Path) -> None:
        """Verify no builtin annotation does not add t import."""
        source = (
            "from __future__ import annotations\n\n"
            "def foo(result):\n"
            "    assert result.success\n"
        )
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map={}, file_path=tmp_path / "module.py"
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersPattern:
    """Behavior contract for FlextInfraRefactorPatternTransformer."""

    def test_bare_except_pattern(self) -> None:
        """Verify bare except pattern."""
        source = "try:\n    pass\nexcept:\n    pass\n"
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"^(?P<indent>\s*)except\s*:(?P<trail>.*)$",
                    "replacement": r"\g<indent>except Exception:\g<trail>",
                    "change_message": "Rewrote bare except to except Exception",
                    "flags": ["MULTILINE"],
                }
            ]
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="except Exception:")
        tm.that(code, lacks="except:")
        tm.that(changes, empty=False)

    def test_specific_except_pattern_unchanged(self) -> None:
        """Verify specific except pattern unchanged."""
        source = (
            "def foo():\n    try:\n        pass\n    except ValueError:\n        pass\n"
        )
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"^(?P<indent>\s*)except\s*:(?P<trail>.*)$",
                    "replacement": r"\g<indent>except Exception:\g<trail>",
                    "change_message": "Rewrote bare except to except Exception",
                    "flags": ["MULTILINE"],
                }
            ]
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_breakpoint_patterns_remove_debuggers(self) -> None:
        """Verify breakpoint patterns remove debuggers."""
        source = "x = 1\n\nbreakpoint()\n\nimport pdb; pdb.set_trace()\n\ny = 2\n"
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"^[ \t]*breakpoint\s*\(\s*\)\s*[;\n]",
                    "replacement": "\n",
                    "change_message": "Removed debugger statement",
                    "flags": ["MULTILINE"],
                },
                {
                    "regex": (
                        r"^[ \t]*import\s+pdb\s*;\s*pdb\.set_trace"
                        r"\s*\(\s*\)\s*[;\n]"
                    ),
                    "replacement": "\n",
                    "change_message": "Removed debugger statement",
                    "flags": ["MULTILINE"],
                },
            ]
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, lacks="breakpoint()")
        tm.that(code, lacks="pdb.set_trace()")
        tm.that(code, has="x = 1\n")
        tm.that(code, has="y = 2\n")
        tm.that(changes, empty=False)

    def test_open_encoding_pattern(self) -> None:
        """Verify open encoding pattern."""
        source = 'with open("x.txt") as f:\n    pass\n'
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bopen\s*\(\s*(?P<args>[^)]*)\s*\)",
                    "replacement": r'open(\g<args>, encoding="utf-8")',
                    "change_message": 'Added encoding="utf-8" to open() call',
                }
            ]
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has='open("x.txt", encoding="utf-8")')
        tm.that(changes, empty=False)

    def test_pattern_with_required_alias(self, tmp_path: Path) -> None:
        """Verify pattern with required alias."""
        source = "def foo(x):\n    return print(x)\n"
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bprint\s*\(\s*(?P<args>[^)]*)\s*\)",
                    "replacement": r"u.fetch_logger(__name__).info(\g<args>)",
                    "change_message": "Rewrote print() to logger",
                }
            ],
            required_alias="u",
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="u.fetch_logger(__name__).info")
        tm.that(code, has="from flext_core import u")
        tm.that(changes, empty=False)

    def test_pattern_required_alias_not_duplicated(self, tmp_path: Path) -> None:
        """Verify pattern required alias not duplicated."""
        source = 'from flext_core import c, u\n\nprint("hello")\n'
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bprint\s*\(\s*(?P<args>[^)]*)\s*\)",
                    "replacement": r"u.fetch_logger(__name__).info(\g<args>)",
                    "change_message": "Rewrote print() to logger",
                }
            ],
            required_alias="u",
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code.count("from flext_core import"), eq=1)
        tm.that(code, has="from flext_core import c, u")
        tm.that(code, has='u.fetch_logger(__name__).info("hello")')
        tm.that(changes, empty=False)

    def test_pattern_no_match_leaves_source_unchanged(self) -> None:
        """Verify pattern no match leaves source unchanged."""
        source = "x = 1\n"
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bprint\s*\(\s*(?P<args>[^)]*)\s*\)",
                    "replacement": r"u.fetch_logger(__name__).info(\g<args>)",
                    "change_message": "Rewrote print() to logger",
                }
            ],
            required_alias="u",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersHardcodedVersion:
    """Behavior contract for FlextInfraRefactorHardcodedVersion."""

    def test_hardcoded_version_reported(self) -> None:
        """Verify hardcoded version reported."""
        source = '__version__ = "1.2.3"\n'
        code, changes = _transform(source, FlextInfraRefactorHardcodedVersion())
        tm.that(code, eq=source)
        tm.that(changes, empty=False)
        tm.that(changes[0], has="importlib.metadata")

    def test_no_version_unchanged(self) -> None:
        """Verify no version unchanged."""
        source = "x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorHardcodedVersion())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersCompatibilityAlias:
    """Behavior contract for FlextInfraRefactorCompatibilityAlias."""

    def test_compat_assignment_removed_and_references_rewritten(self) -> None:
        """Verify compat assignment removed and references rewritten."""
        source = (
            "from flext_core import FlextConstants\n\n"
            "FC = FlextConstants\n\n"
            "def foo():\n"
            "    return FC.SOME_VALUE\n"
        )
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        tm.that(code, lacks="FC = FlextConstants\n")
        tm.that(code, has="FlextConstants.SOME_VALUE")
        tm.that(changes, empty=False)

    def test_compat_import_rewritten_to_canonical_alias(self) -> None:
        """Verify compat import rewritten to canonical alias."""
        source = (
            "from flext_core import FlextConstants\n\n"
            "def foo():\n"
            "    return FlextConstants.SOME_VALUE\n"
        )
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        tm.that(code, has="from flext_core import c\n")
        tm.that(code, lacks="FlextConstants.SOME_VALUE")
        tm.that(code, has="c.SOME_VALUE")
        tm.that(changes, empty=False)

    def test_skip_names_preserved(self) -> None:
        """Verify skip names preserved."""
        source = "__version__ = __version_info__\n"
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])

    def test_same_name_assignment_preserved(self) -> None:
        """Verify same name assignment preserved."""
        source = "Foo = Foo\n"
        code, changes = _transform(source, FlextInfraRefactorCompatibilityAlias())
        tm.that(code, eq=source)
        tm.that(changes, eq=[])


class TestsFlextInfraTransformersPatternList:
    """Pattern-driven rewrites for ENFORCE-091/092 typing.List."""

    def test_typing_list_import_rewritten(self, tmp_path: Path) -> None:
        """Verify typing list import rewritten."""
        source = (
            "from __future__ import annotations\n"
            "from typing import List\n"
            "x: List[int] = []\n"
        )
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bList\s*\[",
                    "replacement": "t.SequenceOf[",
                    "change_message": "Rewrote List[...] to t.SequenceOf[...]",
                }
            ],
            required_alias="t",
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="t.SequenceOf[int]")
        tm.that(code, has="from flext_core import t")
        tm.that(code, lacks="List[int]")
        tm.that(changes, empty=False)

    def test_typing_list_attr_rewritten(self, tmp_path: Path) -> None:
        """Verify typing list attr rewritten."""
        source = (
            "from __future__ import annotations\n"
            "import typing\n"
            "x: typing.List[int] = []\n"
        )
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\btyping\s*\.\s*List\s*\[",
                    "replacement": "t.SequenceOf[",
                    "change_message": "Rewrote typing.List[...] to t.SequenceOf[...]",
                }
            ],
            required_alias="t",
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="t.SequenceOf[int]")
        tm.that(code, has="from flext_core import t")
        tm.that(code, lacks="typing.List")
        tm.that(changes, empty=False)


class TestsFlextInfraTransformersPatternStructlog:
    """Pattern-driven rewrite for ENFORCE-094 direct structlog."""

    def test_structlog_get_logger_rewritten(self, tmp_path: Path) -> None:
        """Verify structlog get logger rewritten."""
        source = (
            "from __future__ import annotations\n"
            "import structlog\n"
            "logger = structlog.get_logger()\n"
        )
        transformer = FlextInfraRefactorPatternTransformer(
            patterns=[
                {
                    "regex": r"\bstructlog\s*\.\s*get_logger\s*\(\s*\)",
                    "replacement": "u.fetch_logger(__name__)",
                    "change_message": (
                        "Rewrote structlog.get_logger() to u.fetch_logger()"
                    ),
                }
            ],
            required_alias="u",
            file_path=tmp_path / "module.py",
        )
        code, changes = transformer.apply_to_source(source)
        tm.that(code, has="u.fetch_logger(__name__)")
        tm.that(code, has="from flext_core import u")
        tm.that(code, lacks="structlog.get_logger()")
        tm.that(changes, empty=False)
