"""Canonical command and test-boundary checks for documentation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import shlex
from collections.abc import Mapping, MutableSequence, Sequence

from flext_cli import u

from flext_infra import c, config, m
from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts
from flext_infra._utilities._docs.docs_base import FlextInfraUtilitiesDocsBase


class FlextInfraUtilitiesDocsCommandContract:
    """Detect documentation that bypasses canonical Make and test ownership."""

    @staticmethod
    def _docs_command_candidates(
        line: str,
        *,
        fence_language: str | None,
        spans: Sequence[m.Cli.MarkdownCodeSpan],
    ) -> Sequence[str]:
        """Return executable shell snippets, excluding surrounding prose.

        Returns:
            Executable shell snippets, excluding surrounding prose.

        """
        if fence_language is not None:
            return (
                (line,) if fence_language in c.Infra.DOCS_SHELL_FENCE_LANGUAGES else ()
            )
        stripped = line.lstrip()
        if stripped.startswith("$ "):
            return (stripped[2:],)
        return tuple(
            span.content
            for span in spans
            if len(span.content.split()) > 1
            and c.Infra.DOCS_INLINE_COMMAND_DIRECTIVE_RE.search(span.prefix) is not None
        )

    @staticmethod
    def _docs_fence_lines(
        content: str,
    ) -> tuple[Mapping[int, str], frozenset[int]]:
        """Map fence body lines to their language and collect delimiter lines.

        Returns:
            The ``(body line -> language, delimiter lines)`` pair.

        """
        bodies: dict[int, str] = {}
        delimiters: set[int] = set()
        for fence in u.Cli.markdown_fences(content):
            body_end = fence.opening_line + len(fence.code.splitlines())
            bodies.update(
                dict.fromkeys(
                    range(fence.opening_line + 1, body_end + 1), fence.language
                ),
            )
            delimiters.add(fence.opening_line)
            if body_end < fence.closing_line:
                delimiters.add(fence.closing_line)
        return (bodies, frozenset(delimiters))

    @staticmethod
    def _make_selector_issue(
        arguments: str,
        verb: m.Infra.MakeVerbSpec,
    ) -> str:
        """Return the first named input absent from the operation's contract.

        Returns:
            The resulting ``str``.

        """
        allowed = frozenset((
            *config.Infra.codegen.make.common_arguments,
            config.Infra.codegen.make.ci.variable,
            *verb.arguments,
        ))
        for token in shlex.split(arguments, comments=True):
            selector = c.Infra.MAKE_ASSIGNMENT_RE.match(token)
            if selector is None:
                continue
            selector_name = selector.group(0).split("=", maxsplit=1)[0].rstrip(":?+")
            if selector_name not in allowed:
                return f"invented Make selector `{selector_name}`"
        return ""

    @staticmethod
    def _candidate_issue(
        candidate: str,
        effective_verbs: Sequence[m.Infra.MakeVerbSpec],
    ) -> str:
        """Return the command-contract issue one candidate command violates.

        Returns:
            The resulting ``str``.

        """
        make_match = c.Infra.DOCS_MAKE_COMMAND_RE.match(candidate)
        if c.Infra.DOCS_RAW_PYTEST_COMMAND_RE.match(candidate):
            return "direct pytest command bypasses `make test`"
        if c.Infra.DOCS_RAW_TOOL_COMMAND_RE.match(candidate):
            return "direct tool command bypasses the root Make dispatcher"
        if make_match is None:
            return ""
        verb = make_match.group("verb").lower()
        verb_spec = next(
            (spec for spec in effective_verbs if spec.name == verb),
            None,
        )
        if c.Infra.DOCS_APPLY_RE.search(make_match.group("args")) is not None:
            return (
                "legacy `APPLY` flag is exterminated: verbs always "
                "execute their declared operation"
            )
        if verb_spec is None:
            return f"Make verb `{verb}` is not declared by the config SSOT"
        return FlextInfraUtilitiesDocsCommandContract._make_selector_issue(
            make_match.group("args"),
            verb_spec,
        )

    @classmethod
    def _docs_line_issue(
        cls,
        line: str,
        *,
        fence_language: str | None,
        spans: Sequence[m.Cli.MarkdownCodeSpan],
        effective_verbs: Sequence[m.Infra.MakeVerbSpec],
    ) -> str:
        """Return the command-contract issue one document line violates.

        Returns:
            The resulting ``str``.

        """
        issue = ""
        for (
            candidate
        ) in FlextInfraUtilitiesDocsCommandContract._docs_command_candidates(
            line,
            fence_language=fence_language,
            spans=spans,
        ):
            issue = cls._candidate_issue(candidate, effective_verbs)
            if issue:
                break
        if not issue and c.Infra.DOCS_TEST_DOUBLE_HEADING_RE.match(line):
            return "test-double guidance is prohibited"
        if (
            not issue
            and fence_language in {"py", "python", "python3"}
            and (c.Infra.DOCS_TEST_DOUBLE_CODE_RE.search(line) is not None)
        ):
            return "test-double code bypasses public-facade test ownership"
        return issue

    @classmethod
    def docs_command_contract_content_issues(
        cls,
        content: str,
        *,
        relative_path: str,
        effective_verbs: Sequence[m.Infra.MakeVerbSpec],
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return command-contract issues from one Markdown document.

        Returns:
            Command-contract issues from one Markdown document.

        """
        issues: MutableSequence[m.Infra.AuditIssue] = []
        bodies, delimiters = cls._docs_fence_lines(content)
        spans: dict[int, list[m.Cli.MarkdownCodeSpan]] = {}
        for span in u.Cli.markdown_code_spans(content):
            spans.setdefault(span.line, []).append(span)
        for number, line in enumerate(content.splitlines(), start=1):
            if number in delimiters:
                continue
            issue = cls._docs_line_issue(
                line,
                fence_language=bodies.get(number),
                spans=spans.get(number, ()),
                effective_verbs=effective_verbs,
            )
            if issue:
                issues.append(
                    m.Infra.AuditIssue(
                        file=relative_path,
                        issue_type="command_contract",
                        severity="high",
                        message=f"line {number}: {issue}",
                    ),
                )
        return issues

    @staticmethod
    def docs_command_contract_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect live guide/standard issues through typed scope discovery.

        ``iter_scope_markdown_files`` owns every formal scope exclusion; this
        detector carries no path allowlist or bypass.

        Returns:
            The resulting ``Sequence[m.Infra.AuditIssue]``.

        Raises:
            ValueError: If ``loaded.failure``.

        """
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            scope.path,
        )
        if loaded.failure:
            if loaded.exception is not None:
                raise loaded.exception
            raise ValueError(loaded.error)
        effective_verbs = (
            *loaded.value.spec.make.verbs,
            *(
                loaded.value.spec.repository.extra_verbs
                if loaded.value.spec.repository
                else ()
            ),
        )
        issues: MutableSequence[m.Infra.AuditIssue] = []
        docs_root = scope.path / c.Infra.DIR_DOCS
        for path in FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope):
            if not path.is_relative_to(docs_root):
                continue
            relative_docs_path = path.relative_to(docs_root)
            relative_path = path.relative_to(scope.path).as_posix()
            if (
                not relative_docs_path.parts
                or relative_docs_path.parts[0]
                not in c.Infra.DOCS_COMMAND_CONTRACT_DIRNAMES
            ):
                continue
            content = path.read_text(
                encoding=c.DEFAULT_ENCODING,
                errors=c.Infra.IGNORE,
            )
            issues.extend(
                FlextInfraUtilitiesDocsCommandContract.docs_command_contract_content_issues(
                    content,
                    relative_path=relative_path,
                    effective_verbs=effective_verbs,
                ),
            )
        return issues


__all__: list[str] = ["FlextInfraUtilitiesDocsCommandContract"]
