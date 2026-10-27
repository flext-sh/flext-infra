"""Conservative structural evidence for duplication; never suppress raw findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import operator
import time
import tokenize
from bisect import bisect_left, bisect_right
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraDuplicationEvidence:
    """Own source analysis and provenance for exactly one scanner invocation.

    Python syntax uses disjoint half-open Unicode ranges. Retained definition
    effects override excluded syntax without changing candidate span boundaries.
    """

    def __init__(self) -> None:
        """Start an isolated source cache for one assessment."""
        self._sources: t.MutableMappingKV[
            str,
            tuple[
                bytes,
                str,
                tuple[
                    tuple[tokenize.TokenInfo, ...],
                    frozenset[str],
                    tuple[tuple[int, int], ...],
                ]
                | None,
            ],
        ] = {}

    @staticmethod
    def parse(raw: str) -> m.Infra.JscpdReport:
        """Validate an initial report without discarding a console trailer.

        The caller retains raw bytes, including any trailer, in its receipt.
        A second JSON document is not console output and fails closed.

        Returns:
            The validated complete scanner inventory.

        Raises:
            ValueError: If the report or trailing document is invalid.

        """
        text = raw.lstrip()
        _, end = json.JSONDecoder().raw_decode(text)
        trailer = text[end:].strip()
        if trailer.startswith(("{", "[")):
            msg = "unexpected second JSON document after jscpd report"
            raise ValueError(msg)
        if any(
            not line.startswith((
                "Using config from ",
                "Semantic clones",
                "ERROR: jscpd ",
                "jscpd semantic pass NOT EXECUTED:",
            ))
            for line in trailer.splitlines()
            if line.strip()
        ):
            msg = "unrecognized console trailer after jscpd report"
            raise ValueError(msg)
        return m.Infra.JscpdReport.model_validate_json(text[:end])

    def assess(
        self,
        report: m.Infra.JscpdReport,
        root: Path,
        config: m.Infra.ProjectDuplicationOverrides,
        *,
        raw_receipt: str,
        execution: str,
    ) -> m.Infra.DuplicationAssessment:
        """Keep every candidate; unsupported roles and failures remain blocking.

        Returns:
            Lossless evidence which never promotes acceptance.

        """
        started = time.monotonic()
        candidates: list[m.Infra.DuplicationCandidateEvidence] = []
        pairs: t.MutableMappingKV[tuple[str, str], int] = {}
        counts: t.MutableMappingKV[str, int] = {
            "raw": len(report.duplicates),
            "owned": 0,
            "mirror": 0,
            "self_span": 0,
            "raw_hard": 0,
        }
        for index, candidate in enumerate(report.duplicates):
            sides = (candidate.first_file, candidate.second_file)
            keys = tuple(
                f"{side.name}:{side.start_location.line}:{side.end_location.line}"
                for side in sides
            )
            pair = (min(keys), max(keys))
            canonical = pairs.setdefault(pair, index)
            owned = any(Path(side.name).is_relative_to(root) for side in sides)
            counts["owned"] += int(owned)
            counts["mirror"] += int(canonical != index)
            counts["self_span"] += int(keys[0] == keys[1])
            counts["raw_hard"] += int(
                owned and canonical == index and keys[0] != keys[1]
            )
            measures: tuple[m.Infra.DuplicationSpanMeasure, ...] = ()
            try:
                measures = self._candidate_measures(candidate, root)
                classification = self._classify(
                    candidate.format_name,
                    measures,
                    config,
                )
            except (
                OSError,
                UnicodeError,
                SyntaxError,
                ValueError,
                tokenize.TokenError,
            ) as exc:
                classification = m.Infra.DuplicationClassification(
                    disposition="analysis_error",
                    reason=f"{type(exc).__name__}: {exc}",
                )
            disposition = classification.disposition
            candidates.append(
                m.Infra.DuplicationCandidateEvidence(
                    index=index,
                    canonical_index=canonical,
                    candidate=candidate,
                    owned=owned,
                    self_span=keys[0] == keys[1],
                    disposition=disposition,
                    reason=classification.reason,
                    measures=measures,
                )
            )
        candidates = self._revalidate_sources(candidates)
        for disposition in {item.disposition for item in candidates}:
            counts[disposition] = sum(
                item.disposition == disposition for item in candidates
            )
        return m.Infra.DuplicationAssessment(
            policy="structural-evidence-v1-raw-hard",
            raw_sha256=hashlib.sha256(raw_receipt.encode()).hexdigest(),
            report=report,
            candidates=tuple(candidates),
            min_lines=config.min_lines,
            min_tokens=config.min_tokens,
            duration_seconds=time.monotonic() - started,
            source_count=len(self._sources),
            counts=counts,
            execution=execution,
            source_provenance=(
                "Current source bytes, fragment-bound on the first side only; "
                "scanner has no per-source fingerprints. Not proof of historical "
                "source identity or semantic equivalence; raw-hard preserved."
            ),
            budget_status=(
                "NOT VERIFIED: evidence-only; no acceptance promotion; "
                "memory/token usage not measured"
            ),
        )

    def _revalidate_sources(
        self,
        candidates: list[m.Infra.DuplicationCandidateEvidence],
    ) -> list[m.Infra.DuplicationCandidateEvidence]:
        """Keep per-candidate race failures in the lossless receipt.

        Returns:
            Candidates with causal errors for changed or newly unreadable sources.

        """
        errors: t.MutableMappingKV[str, str] = {}
        for name, (data, _, _) in self._sources.items():
            try:
                current = Path(name).read_bytes()
            except OSError as exc:
                errors[name] = f"{type(exc).__name__}: {exc}"
            else:
                if current != data:
                    errors[name] = f"source changed during assessment: {name}"
        verified: list[m.Infra.DuplicationCandidateEvidence] = []
        for item in candidates:
            failures = [
                errors[side.name]
                for side in (item.candidate.first_file, item.candidate.second_file)
                if side.name in errors
            ]
            verified.append(
                m.Infra.DuplicationCandidateEvidence.model_validate({
                    **item.model_dump(),
                    "disposition": "analysis_error",
                    "reason": "; ".join(failures),
                })
                if failures
                else item,
            )
        return verified

    def _candidate_measures(
        self,
        candidate: m.Infra.JscpdDuplicate,
        root: Path,
    ) -> tuple[m.Infra.DuplicationSpanMeasure, ...]:
        """Bind both reported spans to physical sources within this project.

        Returns:
            Both source-bound measurements.

        Raises:
            ValueError: If source scope or fragment provenance cannot be verified.

        """
        sides = (candidate.first_file, candidate.second_file)
        if any(
            not Path(side.name).resolve().is_relative_to(root.resolve())
            for side in sides
        ):
            msg = "candidate source outside selected project scope"
            raise ValueError(msg)
        measures = tuple(self._measure(side, candidate.format_name) for side in sides)
        lines = self._sources[sides[0].name][1].splitlines(keepends=True)
        span = "".join(
            lines[sides[0].start_location.line - 1 : sides[0].end_location.line]
        )
        if candidate.fragment.strip() not in span:
            msg = "first candidate fragment no longer matches reported source span"
            raise ValueError(msg)
        return measures

    @staticmethod
    def _classify(
        format_name: str,
        measures: tuple[m.Infra.DuplicationSpanMeasure, ...],
        config: m.Infra.ProjectDuplicationOverrides,
    ) -> m.Infra.DuplicationClassification:
        """Explain structural measurements without granting an exemption.

        Returns:
            Disposition and evidence reason.

        """
        if format_name in {"yaml", "json"}:
            return m.Infra.DuplicationClassification(
                disposition="authority_data_candidate",
                reason="Data may own policy; no format exemption",
            )
        if format_name != "python" or any(side.uncertainty for side in measures):
            return m.Infra.DuplicationClassification(
                disposition="unresolved",
                reason="; ".join(side.uncertainty for side in measures),
            )
        if all(side.tokens == 0 for side in measures):
            return m.Infra.DuplicationClassification(
                disposition="non_behavioral_only",
                reason="Only removable syntax; raw-hard preserved",
            )
        if any(
            not any(
                end - start + 1 >= config.min_lines and tokens >= config.min_tokens
                for start, end, tokens in side.runs
            )
            for side in measures
        ):
            return m.Infra.DuplicationClassification(
                disposition="below_existing_behavior_floor",
                reason="Below selected body floor; raw-hard preserved",
            )
        return m.Infra.DuplicationClassification(
            disposition="behavioral_candidate",
            reason="Bodies reach both floors; semantics need review",
        )

    def _measure(
        self,
        side: m.Infra.JscpdFile,
        format_name: str,
    ) -> m.Infra.DuplicationSpanMeasure:
        """Parse whole files and intersect tokens with the reported source span.

        Returns:
            Source-bound structural token measurements.

        Raises:
            ValueError: If the source path or span is invalid.

        """
        data, source = self._read_source(side)
        if format_name == "yaml":
            yaml_parsed = u.Cli.yaml_parse(source)
            if yaml_parsed.failure:
                msg = f"invalid YAML source: {yaml_parsed.error}"
                raise ValueError(msg)
        elif format_name == "json":
            json_parsed = u.Cli.json_parse(source)
            if json_parsed.failure:
                msg = f"invalid JSON source: {json_parsed.error}"
                raise ValueError(msg)
        elif format_name not in {"python", "txt"}:
            msg = f"unsupported source mapping for format {format_name}"
            raise ValueError(msg)
        retained: list[tokenize.TokenInfo] = []
        removed: set[str] = set()
        uncertainty = "Data role and independent oracle consumption not proven"
        if format_name == "python":
            retained, removed, uncertainty = self._python_tokens(side)
        runs = self._runs(retained)
        return m.Infra.DuplicationSpanMeasure(
            source=side.name,
            sha256=hashlib.sha256(data).hexdigest(),
            lines=sum(end - start + 1 for start, end, _ in runs),
            tokens=len(retained),
            runs=runs,
            removed=tuple(sorted(removed)),
            uncertainty=uncertainty,
        )

    def _read_source(
        self,
        side: m.Infra.JscpdFile,
    ) -> tuple[bytes, str]:
        """Read complete physical source with validated character coordinates.

        Returns:
            Complete source bytes and decoded text.

        Raises:
            ValueError: If the path or coordinates are invalid.

        """
        path = Path(side.name)
        if not path.is_absolute() or not path.is_file() or path.is_symlink():
            msg = f"not a physical absolute source file: {path}"
            raise ValueError(msg)
        if side.name not in self._sources:
            data = path.read_bytes()
            self._sources[side.name] = (data, data.decode("utf-8"), None)
        data, source, _ = self._sources[side.name]
        lines = source.splitlines()
        start = (side.start_location.line, side.start_location.column)
        end = (side.end_location.line, side.end_location.column)
        if start > end or start[0] > len(lines) or end[0] > len(lines):
            msg = f"source span out of bounds: {path}:{start}:{end}"
            raise ValueError(msg)
        if start[1] > len(lines[start[0] - 1].encode()) or end[1] > len(
            lines[end[0] - 1].encode()
        ):
            msg = f"source column out of bounds: {path}:{start}:{end}"
            raise ValueError(msg)
        for line, column in (start, end):
            lines[line - 1].encode()[:column].decode()
        return data, source

    def _python_tokens(
        self,
        side: m.Infra.JscpdFile,
    ) -> tuple[list[tokenize.TokenInfo], set[str], str]:
        """Intersect one captured Python analysis with this reported source span.

        Returns:
            Retained tokens, removed categories and uncertainty.

        """
        data, source, analysis = self._sources[side.name]
        if analysis is None:
            analysis = self._analyze_python(source, side.name)
            self._sources[side.name] = (data, source, analysis)
        tokens, removed, imports = analysis
        lines = source.splitlines()
        start = (
            side.start_location.line,
            len(
                lines[side.start_location.line - 1]
                .encode()[: side.start_location.column]
                .decode()
            ),
        )
        end = (
            side.end_location.line,
            len(
                lines[side.end_location.line - 1]
                .encode()[: side.end_location.column]
                .decode()
            ),
        )
        uncertain = any(start[0] <= right and left <= end[0] for left, right in imports)
        return (
            list(
                tokens[
                    bisect_left(
                        tokens, start, key=lambda token: token.start
                    ) : bisect_right(tokens, end, key=lambda token: token.start)
                ]
            ),
            set(removed),
            "Import activation effects unproven" if uncertain else "",
        )

    @classmethod
    def _analyze_python(
        cls,
        source: str,
        name: str,
    ) -> tuple[
        tuple[tokenize.TokenInfo, ...],
        frozenset[str],
        tuple[tuple[int, int], ...],
    ]:
        """Analyze captured Python once, keeping token and import source ordering.

        Excluded syntax and retained definition effects are independent range
        unions; retained membership takes precedence over excluded membership.

        Returns:
            Structural tokens, original removal categories and import line ranges.

        """
        tree = ast.parse(source, filename=name)
        excluded, keep, removed = cls._syntax_ranges(tree, source.splitlines())
        excluded_ranges = cls._range_union(excluded)
        retained_ranges = cls._range_union(keep)
        imports = tuple(
            (node.lineno, node.end_lineno or node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, c.Infra.AST_IMPORT_TYPES)
            and (not isinstance(node, ast.ImportFrom) or node.module != "__future__")
        )
        retained = tuple(
            token
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type
            not in {
                tokenize.ENCODING,
                tokenize.ENDMARKER,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.NEWLINE,
                tokenize.NL,
                tokenize.COMMENT,
            }
            and (
                not cls._inside_ranges(token.start, excluded_ranges)
                or cls._inside_ranges(token.start, retained_ranges)
            )
        )
        return retained, frozenset(removed), imports

    @staticmethod
    def _range_union(
        ranges: list[tuple[tuple[int, int], tuple[int, int]]],
    ) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
        """Merge half-open source intervals without adding covered positions.

        Returns:
            Ordered disjoint intervals with the original membership.

        """
        merged: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for left, right in sorted(ranges):
            if left >= right:
                continue
            if merged and left <= merged[-1][1]:
                previous_left, previous_right = merged[-1]
                merged[-1] = (previous_left, max(previous_right, right))
            else:
                merged.append((left, right))
        return tuple(merged)

    @staticmethod
    def _inside_ranges(
        position: tuple[int, int],
        ranges: tuple[tuple[tuple[int, int], tuple[int, int]], ...],
    ) -> bool:
        """Query ordered half-open interval membership at a Unicode position.

        Returns:
            Whether the position belongs to the disjoint range union.

        """
        index = bisect_right(ranges, position, key=operator.itemgetter(0)) - 1
        return index >= 0 and position < ranges[index][1]

    @classmethod
    def _syntax_ranges(
        cls,
        tree: ast.Module,
        lines: list[str],
    ) -> tuple[
        list[tuple[tuple[int, int], tuple[int, int]]],
        list[tuple[tuple[int, int], tuple[int, int]]],
        set[str],
    ]:
        """Derive removable syntax ranges without removing executable defaults.

        Returns:
            Excluded ranges, retained expression ranges and category names.

        """
        excluded: list[tuple[tuple[int, int], tuple[int, int]]] = []
        keep: list[tuple[tuple[int, int], tuple[int, int]]] = []
        removed: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, c.Infra.AST_IMPORT_TYPES):
                excluded.append(cls._coordinates(node, lines))
                removed.add("import_syntax")
            if (
                isinstance(node, c.Infra.AST_SCOPE_OWNER_TYPES)
                and ast.get_docstring(node, clean=False) is not None
            ):
                excluded.append(cls._coordinates(node.body[0], lines))
                removed.add("docstring")
            if isinstance(node, c.Infra.AST_FUNCTION_TYPES):
                excluded.append((
                    cls._coordinates(node, lines)[0],
                    cls._coordinates(node.body[0], lines)[0],
                ))
                removed.add("signature_syntax")
                keep.extend(
                    cls._coordinates(expression, lines)
                    for expression in cls._definition_effects(node)
                )
        return excluded, keep, removed

    @staticmethod
    def _definition_effects(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[ast.expr]:
        """Retain annotations conservatively, including deferred annotations.

        Returns:
            Expressions whose effects must not be measured as signature padding.

        """
        expressions = [
            *node.decorator_list,
            *node.args.defaults,
            *(value for value in node.args.kw_defaults if value is not None),
        ]
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if node.args.vararg:
            arguments.append(node.args.vararg)
        if node.args.kwarg:
            arguments.append(node.args.kwarg)
        expressions.extend(
            arg.annotation for arg in arguments if arg.annotation is not None
        )
        if node.returns:
            expressions.append(node.returns)
        expressions.extend(
            child
            for parameter in node.type_params
            for child in ast.walk(parameter)
            if isinstance(child, ast.expr)
        )
        return expressions

    @staticmethod
    def _coordinates(
        node: ast.stmt | ast.expr,
        lines: list[str],
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Convert AST UTF-8 byte offsets to tokenizer character coordinates.

        Returns:
            Half-open source range in physical lines and Unicode columns.

        """
        end_line = node.end_lineno or node.lineno
        return (
            (
                node.lineno,
                len(lines[node.lineno - 1].encode()[: node.col_offset].decode()),
            ),
            (
                end_line,
                len(lines[end_line - 1].encode()[: node.end_col_offset].decode()),
            ),
        )

    @staticmethod
    def _runs(retained: list[tokenize.TokenInfo]) -> tuple[tuple[int, int, int], ...]:
        """Keep disjoint executable regions separate instead of joining fragments.

        Returns:
            Physical line runs and lexical token counts.

        """
        per_line: t.MutableMappingKV[int, int] = {}
        for token in retained:
            per_line[token.start[0]] = per_line.get(token.start[0], 0) + 1
        runs: list[tuple[int, int, int]] = []
        for line, count in sorted(per_line.items()):
            if runs and runs[-1][1] + 1 == line:
                left, _, total = runs[-1]
                runs[-1] = (left, line, total + count)
            else:
                runs.append((line, line, count))
        return tuple(runs)


__all__ = ["FlextInfraDuplicationEvidence"]
