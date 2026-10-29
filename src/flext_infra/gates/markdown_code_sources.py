"""Embedded-Python source collection for the ``markdown-code`` gate.

Fenced ``python``` blocks on the governed markdown surface and doctest
examples inside tracked docstrings are collected once as named sources, each
mapped back to its documentation origin. The gate writes them into one
temporary tree so ruff validates and formats them in single invocations. The
gate is selected by its input kinds; a project whose inputs yield no source is
reported clean.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from doctest import DocTestParser
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, u

if TYPE_CHECKING:
    from flext_infra import m, p


class FlextInfraMarkdownCodeSources:
    """Collect embedded Python from documentation as named, located sources."""

    @staticmethod
    def syntax_broken(code: str, origin: Path) -> bool:
        """Identify documentation fragments owned by the Markdown syntax validator.

        Returns:
            The resulting ``bool``.

        """
        try:
            compile(code, str(origin), "exec")
        except SyntaxError:
            return True
        return False

    @staticmethod
    def source_name(relative_posix: str, index: int) -> str:
        """Encode one block's documentation location into a temp source filename.

        Returns:
            The resulting ``str``.

        """
        return c.Infra.MARKDOWN_CODE_SOURCE_FORMAT.format(
            relative_posix.replace("/", "__").replace(".", "_"),
            index,
        )

    @staticmethod
    @cache
    def formattable_fences(
        content: str,
        origin: Path,
    ) -> tuple[tuple[int, m.Cli.MarkdownFence], ...]:
        """Index governed ``python`` fences and keep those that compile.

        A pure function of the document text: extraction and write-back of
        one run share a single parse of each unchanged document.

        Returns:
            The ``(index, fence)`` pairs; the index counts every governed fence.

        """
        return tuple(
            (index, fence)
            for index, fence in enumerate(
                filter(u.Infra.docs_is_python_fence, u.Cli.markdown_fences(content)),
            )
            if not FlextInfraMarkdownCodeSources.syntax_broken(fence.code, origin)
        )

    @staticmethod
    def fenced_block_sources(
        project_dir: Path,
        markdown_files: Sequence[Path],
    ) -> Iterator[tuple[str, str, tuple[str, int]]]:
        """Yield one named source per parseable fenced ``python`` block.

        Blocks carrying the ``notest`` fence marker and unparseable fragments
        are excluded. The Markdown validator owns syntax errors; this gate owns
        only formatting of Python blocks that compile. Sources are produced
        lazily, so a presence query stops at the first one.

        Yields:
            ``(source name, code, (relative path, opening line))`` triples.

        """
        for md_path in markdown_files:
            relative_posix = md_path.relative_to(project_dir).as_posix()
            content = md_path.read_text(c.DEFAULT_ENCODING)
            for index, fence in FlextInfraMarkdownCodeSources.formattable_fences(
                content,
                md_path,
            ):
                yield (
                    FlextInfraMarkdownCodeSources.source_name(relative_posix, index),
                    fence.code,
                    (relative_posix, fence.opening_line),
                )

    @staticmethod
    def docstring_sources(
        project_dir: Path,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> Iterator[tuple[str, str, tuple[str, int]]]:
        """Yield one named source per doctest example in tracked docstrings.

        Docstring write-back stays outside the fix contract on purpose: a
        formatter rewrite inside prose is a semantics risk, so docstring
        findings remain manual repairs. Example line numbers are approximate
        within the docstring (stdlib ``doctest`` reports positions relative to
        its input). A doctest example requires its interactive prompt, so a
        module whose text carries no prompt holds no example and is not
        parsed.

        Yields:
            ``(source name, code, (relative path, docstring line))`` triples.

        """
        parser = DocTestParser()
        for py_path in u.Infra.governed_scope_files(project_dir, ["*.py"], scope_facts):
            text = py_path.read_text(c.DEFAULT_ENCODING)
            if c.Infra.MARKDOWN_CODE_DOCTEST_PROMPT in text:
                yield from FlextInfraMarkdownCodeSources._module_doctest_sources(
                    parser,
                    py_path,
                    py_path.relative_to(project_dir).as_posix(),
                    text,
                )

    @staticmethod
    def _module_doctest_sources(
        parser: DocTestParser,
        py_path: Path,
        relative_posix: str,
        text: str,
    ) -> Iterator[tuple[str, str, tuple[str, int]]]:
        """Yield one named source per doctest example of one module.

        Yields:
            ``(source name, code, (relative path, docstring line))`` triples.

        """
        example_index = 0
        for node in ast.walk(ast.parse(text)):
            # Only these carry docstrings; ast.walk also yields expression
            # nodes and ast.get_docstring raises TypeError on those.
            if not isinstance(node, c.Infra.AST_SCOPE_OWNER_TYPES) or not node.body:
                continue
            docstring = ast.get_docstring(node, clean=False)
            if docstring is None:
                continue
            body_start = node.body[0].lineno
            for example in parser.get_examples(docstring):
                compile(example.source, str(py_path), "exec")
                yield (
                    FlextInfraMarkdownCodeSources.source_name(
                        relative_posix,
                        example_index,
                    ),
                    example.source,
                    (relative_posix, body_start + example.lineno),
                )
                example_index += 1


__all__: list[str] = ["FlextInfraMarkdownCodeSources"]
