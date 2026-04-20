"""Source-level Rope rewrite helpers."""

from __future__ import annotations

import re
from collections.abc import (
    Sequence,
)
from operator import itemgetter
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRopeCore,
    c,
    t,
)


class FlextInfraUtilitiesRopeSource:
    """Text-oriented helpers shared by Rope-backed refactors."""

    _SILENT_FAILURE_RETURN_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s*)return\s+(?P<sentinel>False|None|\[\]|\{\})\s*(?:#.*)?$",
    )
    _SILENT_FAILURE_UNWRAP_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s*)return\s+.+?\.unwrap_or\((?P<sentinel>False|None|\[\]|\{\})\)\s*(?:#.*)?$",
    )
    _SILENT_FAILURE_IF_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s*)if\s+(?:(?P<failure_name>[A-Za-z_]\w*)\.failure|not\s+(?P<success_name>[A-Za-z_]\w*)\.success)\s*:\s*(?P<inline>.*)$",
    )
    _SILENT_FAILURE_EXCEPT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s*)except(?:\s+.+?)?(?:\s+as\s+(?P<exception_name>[A-Za-z_]\w*))?\s*:\s*(?P<inline>.*)$",
    )
    _FUNCTION_SIGNATURE_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"->\s*(?:r\[(?P<legacy_inner>.+)\]|p\.Result\[(?P<result_inner>.+)\])\s*:",
    )

    @staticmethod
    def remove_module_level_aliases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        allow: t.Infra.StrSet | None = None,
        apply: bool = True,
    ) -> tuple[str, t.StrSequence]:
        """Remove module-level ``X = Y`` identity aliases."""
        _ = rope_project
        allow_set = allow or set()
        source = resource.read()
        kept: list[str] = []
        removed: list[str] = []
        alias_pattern = re.compile(r"^([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*$")
        scope_depth = 0
        for line in source.splitlines(keepends=True):
            stripped = line.strip()
            if stripped.startswith(("class ", "def ")):
                scope_depth += 1
            if scope_depth > 0:
                kept.append(line)
                continue
            match = alias_pattern.match(stripped)
            if match is None:
                kept.append(line)
                continue
            target, value = match.group(1), match.group(2)
            if (
                target != value
                or target in allow_set
                or target
                in {
                    c.Infra.DUNDER_VERSION,
                    c.Infra.DUNDER_ALL,
                }
            ):
                kept.append(line)
            else:
                removed.append(f"{target} = {value}")
        if not removed:
            return source, []
        new_source = "".join(kept)
        if apply:
            resource.write(new_source)
        return new_source, removed

    @staticmethod
    def batch_replace_annotations(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        replacements: t.StrMapping,
        *,
        apply: bool = True,
    ) -> t.Infra.StrIntPair:
        """Apply multiple annotation replacements in one pass."""
        _ = rope_project
        source = resource.read()
        total = 0
        for old_annotation, new_annotation in replacements.items():
            pattern = re.compile(rf"\b{re.escape(old_annotation)}\b")
            source, count = pattern.subn(new_annotation, source)
            total += count
        if total > 0 and apply and source != resource.read():
            resource.write(source)
        return source, total

    @staticmethod
    def remove_redundant_cast(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool = True,
    ) -> t.Infra.StrIntPair:
        """Remove ``cast(Type, value)`` calls, replacing with just ``value``."""
        _ = rope_project
        source = resource.read()
        new_source, count = re.subn(
            r"\bcast\s*\(\s*[^,]+\s*,\s*([^)]+)\s*\)",
            r"\1",
            source,
        )
        if count > 0 and apply and new_source != source:
            resource.write(new_source)
        return new_source, count

    @staticmethod
    def rewrite_source_at_offsets(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        changes: Sequence[tuple[int, int, str]],
        *,
        apply: bool = True,
    ) -> str:
        """Apply offset-based edits (start, end, replacement) to source."""
        _ = rope_project
        source = resource.read()
        for start, end, replacement in sorted(
            changes,
            key=itemgetter(0),
            reverse=True,
        ):
            source = source[:start] + replacement + source[end:]
        if apply and source != resource.read():
            resource.write(source)
        return source

    @staticmethod
    def _indent_width(line: str) -> int:
        return len(line) - len(line.lstrip())

    @classmethod
    def _silent_failure_block_return(
        cls,
        lines: t.StrSequence,
        *,
        start_index: int,
        block_indent: int,
    ) -> tuple[int, str, str] | None:
        index = start_index + 1
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue
            if cls._indent_width(line) <= block_indent:
                return None
            match = cls._SILENT_FAILURE_RETURN_RE.match(line)
            if match is not None:
                return index, match.group("indent"), match.group("sentinel")
            return None
        return None

    @classmethod
    def _enclosing_result_inner(
        cls,
        lines: t.StrSequence,
        *,
        line_index: int,
    ) -> str | None:
        target_indent = cls._indent_width(lines[line_index])
        for index in range(line_index, -1, -1):
            line = lines[index]
            stripped = line.lstrip()
            if not stripped.startswith(("def ", "async def ")):
                continue
            if cls._indent_width(line) >= target_indent:
                continue
            signature_lines = [line.strip()]
            tail = index
            while tail + 1 < len(lines) and not lines[tail].rstrip().endswith(":"):
                tail += 1
                signature_lines.append(lines[tail].strip())
            signature = " ".join(signature_lines)
            match = cls._FUNCTION_SIGNATURE_RE.search(signature)
            if match is None:
                return None
            return match.group("legacy_inner") or match.group("result_inner")
        return None

    @staticmethod
    def _failure_label(name: str) -> str:
        label = name.removesuffix("_result").replace("_", " ").strip()
        return f"{label} failed" if label else "operation failed"

    @classmethod
    def collect_silent_failure_findings(
        cls,
        source: str,
    ) -> Sequence[tuple[int, int, str, str, tuple[int, int, str] | None]]:
        lines = source.splitlines(keepends=True)
        offsets: list[int] = []
        current_offset = 0
        for line in lines:
            offsets.append(current_offset)
            current_offset += len(line)
        findings: list[tuple[int, int, str, str, tuple[int, int, str] | None]] = []
        for index, line in enumerate(lines):
            unwrap_match = cls._SILENT_FAILURE_UNWRAP_RE.match(line)
            if unwrap_match is not None:
                sentinel = unwrap_match.group("sentinel")
                findings.append(
                    (
                        index + 1,
                        1,
                        "silent-failure-unwrap-or",
                        f"unwrap_or({sentinel}) hides a failure path",
                        None,
                    ),
                )
                continue
            guard_match = cls._SILENT_FAILURE_IF_RE.match(line)
            if guard_match is not None:
                block = cls._silent_failure_block_return(
                    lines,
                    start_index=index,
                    block_indent=cls._indent_width(line),
                )
                if block is None:
                    continue
                block_index, indent, sentinel = block
                result_name = (
                    guard_match.group("failure_name")
                    or guard_match.group("success_name")
                    or "result"
                )
                replacement: tuple[int, int, str] | None = None
                result_inner = cls._enclosing_result_inner(
                    lines, line_index=block_index
                )
                if result_inner is not None:
                    replacement = (
                        offsets[block_index],
                        offsets[block_index] + len(lines[block_index]),
                        (
                            f"{indent}return r[{result_inner}].fail("
                            f"{result_name}.error or {cls._failure_label(result_name)!r})\n"
                        ),
                    )
                findings.append(
                    (
                        block_index + 1,
                        1,
                        "silent-failure-guard",
                        (
                            f"failure branch for '{result_name}' returns {sentinel} "
                            "instead of propagating the error"
                        ),
                        replacement,
                    ),
                )
                continue
            except_match = cls._SILENT_FAILURE_EXCEPT_RE.match(line)
            if except_match is None:
                continue
            block = cls._silent_failure_block_return(
                lines,
                start_index=index,
                block_indent=cls._indent_width(line),
            )
            if block is None:
                continue
            block_index, indent, sentinel = block
            exception_name = except_match.group("exception_name")
            replacement = None
            result_inner = cls._enclosing_result_inner(lines, line_index=block_index)
            if result_inner is not None and exception_name is not None:
                replacement = (
                    offsets[block_index],
                    offsets[block_index] + len(lines[block_index]),
                    (
                        f"{indent}return r[{result_inner}].fail("
                        f"str({exception_name}), exception={exception_name})\n"
                    ),
                )
            findings.append(
                (
                    block_index + 1,
                    1,
                    "silent-failure-except",
                    (
                        f"exception branch returns {sentinel} instead of "
                        "propagating the caught error"
                    ),
                    replacement,
                ),
            )
        return findings

    @classmethod
    def fix_silent_failure_sentinels(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool = True,
    ) -> t.Infra.TransformResult:
        source = resource.read()
        findings = cls.collect_silent_failure_findings(source)
        changes: list[tuple[int, int, str]] = [
            change for *_, change in findings if change is not None
        ]
        if not changes:
            return source, []
        updated = cls.rewrite_source_at_offsets(
            rope_project,
            resource,
            changes,
            apply=apply,
        )
        return updated, [f"Replaced {len(changes)} silent failure sentinel return(s)"]

    @classmethod
    def apply_transformer_to_source(
        cls,
        source: str,
        file_path: Path,
        transformer_fn: t.Infra.RopeTransformFn,
    ) -> tuple[str, t.StrSequence]:
        """Run a rope transformer against source text via a temporary context."""
        workspace_root = FlextInfraUtilitiesDiscovery.project_root(
            file_path,
        )
        if workspace_root is None:
            return (source, [])
        original_disk_source = file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        try:
            with FlextInfraUtilitiesRopeCore.open_project(
                workspace_root,
            ) as rope_project:
                resource = FlextInfraUtilitiesRopeCore.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if resource is None:
                    return (source, [])
                if resource.read() != source:
                    resource.write(source)
                new_source, changes = transformer_fn(rope_project, resource)
                return (new_source, list(changes))
        finally:
            if (
                file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
                != original_disk_source
            ):
                file_path.write_text(
                    original_disk_source,
                    encoding=c.Infra.ENCODING_DEFAULT,
                )


__all__: list[str] = ["FlextInfraUtilitiesRopeSource"]
