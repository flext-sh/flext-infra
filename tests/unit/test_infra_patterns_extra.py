"""Tests for flext_infra.patterns — pattern types and edge cases."""

from __future__ import annotations

import re

from flext_infra import u


class TestFlextInfraPatternsPatternTypes:
    """Tests for pattern type consistency."""

    def test_all_patterns_are_compiled_regex(self) -> None:
        patterns = [
            u.Infra.MYPY_HINT_RE,
            u.Infra.MYPY_STUB_RE,
            u.Infra.MARKDOWN_LINK_RE,
            u.Infra.MARKDOWN_LINK_URL_RE,
            u.Infra.HEADING_RE,
            u.Infra.HEADING_H2_H3_RE,
            u.Infra.ANCHOR_LINK_RE,
            u.Infra.INLINE_CODE_RE,
        ]
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)

    def test_patterns_are_string_patterns(self) -> None:
        patterns = [
            u.Infra.MYPY_HINT_RE,
            u.Infra.MYPY_STUB_RE,
            u.Infra.MARKDOWN_LINK_RE,
        ]
        for pattern in patterns:
            assert hasattr(pattern, "pattern")
            assert isinstance(pattern.pattern, str)


class TestFlextInfraPatternsEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_markdown_link_with_special_chars_in_url(self) -> None:
        text = "[Link](https://example.com/path?query=value&other=123)"
        match = u.Infra.MARKDOWN_LINK_RE.search(text)
        assert match is not None
        assert "query=value" in match.group(2)

    def test_heading_with_trailing_whitespace(self) -> None:
        text = "## Title   "
        match = u.Infra.HEADING_H2_H3_RE.search(text)
        assert match is not None
        assert match.group(2) == "Title"

    def test_inline_code_with_special_chars(self) -> None:
        text = "Code: `foo_bar-baz.txt`"
        match = u.Infra.INLINE_CODE_RE.search(text)
        assert match is not None
        assert "foo_bar-baz.txt" in match.group(0)

    def test_anchor_link_with_hyphens(self) -> None:
        text = "[Section](#my-section-name)"
        match = u.Infra.ANCHOR_LINK_RE.search(text)
        assert match is not None
        assert match.group(2) == "my-section-name"
