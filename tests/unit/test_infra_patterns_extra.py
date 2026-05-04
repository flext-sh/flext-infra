"""Tests for flext_infra.patterns — pattern types and edge cases."""

from __future__ import annotations

from tests import c


class TestsFlextInfraInfraPatternsExtra:
    """Tests for pattern type consistency."""

    def test_all_patterns_are_compiled_regex(self) -> None:
        pattern_type = type(c.Infra.MYPY_HINT_RE)
        patterns = [
            c.Infra.MYPY_HINT_RE,
            c.Infra.MYPY_STUB_RE,
            c.Infra.MARKDOWN_LINK_RE,
            c.Infra.MARKDOWN_LINK_URL_RE,
            c.Infra.HEADING_RE,
            c.Infra.HEADING_H2_H3_RE,
            c.Infra.ANCHOR_LINK_RE,
            c.Infra.INLINE_CODE_RE,
        ]
        for pattern in patterns:
            assert isinstance(pattern, pattern_type)

    def test_patterns_are_string_patterns(self) -> None:
        patterns = [
            c.Infra.MYPY_HINT_RE,
            c.Infra.MYPY_STUB_RE,
            c.Infra.MARKDOWN_LINK_RE,
        ]
        for pattern in patterns:
            assert isinstance(pattern.pattern, str)

    def test_markdown_link_with_special_chars_in_url(self) -> None:
        text = "[Link](https://example.com/path?query=value&other=123)"
        match = c.Infra.MARKDOWN_LINK_RE.search(text)
        assert match is not None
        assert "query=value" in match.group(2)

    def test_heading_with_trailing_whitespace(self) -> None:
        text = "## Title   "
        match = c.Infra.HEADING_H2_H3_RE.search(text)
        assert match is not None
        assert match.group(2) == "Title"

    def test_inline_code_with_special_chars(self) -> None:
        text = "Code: `foo_bar-baz.txt`"
        match = c.Infra.INLINE_CODE_RE.search(text)
        assert match is not None
        assert "foo_bar-baz.txt" in match.group(0)

    def test_anchor_link_with_hyphens(self) -> None:
        text = "[Section](#my-section-name)"
        match = c.Infra.ANCHOR_LINK_RE.search(text)
        assert match is not None
        assert match.group(2) == "my-section-name"
