"""Explicit persisted artifact-reference extraction."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import ClassVar

from flext_infra import c, m, t
from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit


class FlextInfraReferenceExtraction:
    """Extract explicit authority-bearing references from persisted text."""

    _AUTOLINK: ClassVar[t.RegexPattern] = re.compile(r"<([^<>\s]+)>")
    _REFERENCE: ClassVar[t.RegexPattern] = re.compile(r"^\s*\[[^]]+\]:\s*(\S+)")
    _HTML: ClassVar[t.RegexPattern] = re.compile(
        r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE
    )
    _AT_PATH: ClassVar[t.RegexPattern] = re.compile(r"(?<!\w)@([^\s`'\"<>]+)")
    _INLINE_CODE: ClassVar[t.RegexPattern] = re.compile(r"`([^`]+)`")
    _AUTHORITY_CUE: ClassVar[t.RegexPattern] = re.compile(
        r"\b(?:canonical|authority|reference|pointer|read|load|see|lives in)\b",
        re.IGNORECASE,
    )
    _GITHUB_LOCATOR: ClassVar[t.RegexPattern] = re.compile(r"https://github\.com/\S+")
    _FILE_LOCATOR: ClassVar[t.RegexPattern] = re.compile(r"file://\S+")
    _HOME_LOCATOR: ClassVar[t.RegexPattern] = re.compile(r"~[/\\]\S+")
    _VAR_LOCATOR: ClassVar[t.RegexPattern] = re.compile(r"\$\{?[A-Z_]+\}?[/\\]\S+")
    # Ordered: the escape alternative precedes the plain absolute one so a
    # `../` sequence is reported once, never re-matched by the absolute form.
    _ESCAPE_LOCATOR: ClassVar[t.RegexPattern] = re.compile(r"(?:\.\./)+[^\s`'\"<>]+")
    _ABSOLUTE_LOCATOR: ClassVar[t.RegexPattern] = re.compile(
        r"(?:[A-Za-z]:[\\/]|/)[^\s`'\"<>]+"
    )
    _LOCATORS: ClassVar[tuple[t.RegexPattern, ...]] = (
        _GITHUB_LOCATOR,
        _FILE_LOCATOR,
        _HOME_LOCATOR,
        _VAR_LOCATOR,
        _ABSOLUTE_LOCATOR,
        _ESCAPE_LOCATOR,
    )

    @classmethod
    def targets(
        cls, payload: m.Infra.GitCandidatePayload
    ) -> t.SequenceOf[tuple[int, str]]:
        """Return one-based line numbers paired with each reference candidate."""
        text = payload.content.decode(c.Cli.ENCODING_DEFAULT)
        if payload.mode == "120000":
            return ((1, text),)
        name = Path(payload.path).name
        semantic_agent_file = payload.path.endswith(".prompt.md") or name in {
            "AGENTS.md",
            "CLAUDE.md",
            "SKILL.md",
            "copilot-instructions.md",
        }
        semantic_source = (
            payload.path.endswith((".py", ".j2", ".md"))
            or "/tests/" in f"/{payload.path}"
        )
        targets: list[tuple[int, str]] = []
        if not semantic_agent_file and not semantic_source:
            return tuple(targets)
        in_fence = False
        for number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            targets.extend((number, target) for target in cls._line_targets(line))
        return tuple(dict.fromkeys(targets))

    @classmethod
    def _line_targets(cls, line: str) -> t.StrSequence:
        targets = list(FlextInfraUtilitiesDocsAudit.docs_markdown_link_targets(line))
        targets.extend(match.group(1) for match in cls._AUTOLINK.finditer(line))
        targets.extend(match.group(1) for match in cls._HTML.finditer(line))
        targets.extend(match.group(1) for match in cls._AT_PATH.finditer(line))
        reference = cls._REFERENCE.match(line)
        if reference is not None:
            targets.append(reference.group(1))
        targets.extend(
            match.group(1)
            for match in cls._INLINE_CODE.finditer(line)
            if cls._looks_like_locator(match.group(1))
        )
        if not targets and cls._AUTHORITY_CUE.search(line):
            for locator in cls._LOCATORS:
                matches = [match.group(0) for match in locator.finditer(line)]
                if matches:
                    targets.extend(matches)
                    break
        return targets

    @staticmethod
    def _looks_like_locator(value: str) -> bool:
        return value.startswith((
            "@",
            "../",
            "./",
            "/",
            "~",
            "$",
            "file://",
            "https://",
        ))

    @staticmethod
    def effective_path(
        path: str, template_entries: t.SequenceOf[m.Infra.TemplateEntrySpec]
    ) -> PurePosixPath:
        """Map a template source path onto its generated destination path."""
        for entry in template_entries:
            if path.endswith(entry.source.as_posix()):
                return PurePosixPath(entry.destination)
        return PurePosixPath(path)

    @classmethod
    def escapes_repository(
        cls,
        source: str,
        target: str,
        template_entries: t.SequenceOf[m.Infra.TemplateEntrySpec],
    ) -> bool:
        """Report whether target resolves outside the repository root."""
        normalized = target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
        if not normalized or normalized.split(":", 1)[0] in {"http", "https"}:
            return False
        if normalized.startswith(("file://", "~/", "~\\", "$", "/", "\\")):
            return True
        depth = 0
        for part in (
            cls.effective_path(source, template_entries).parent / normalized
        ).parts:
            if part == "..":
                if depth == 0:
                    return True
                depth -= 1
            elif part != ".":
                depth += 1
        return False


__all__: tuple[str, ...] = ("FlextInfraReferenceExtraction",)
