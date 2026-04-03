"""MRO and future-import rewrites for namespace refactors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra.constants import FlextInfraConstants as c
from flext_infra.models import FlextInfraModels as m
from flext_infra.refactor._utilities_namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraUtilitiesRefactorNamespaceMro(
    FlextInfraUtilitiesRefactorNamespaceCommon
):
    """Helpers for MRO completeness and future-import rewrites."""

    @staticmethod
    def rewrite_mro_completeness_violations(
        *,
        violations: Sequence[m.Infra.MROCompletenessViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        _ = parse_failures
        violations_by_file: Mapping[
            Path,
            MutableSequence[m.Infra.MROCompletenessViolation],
        ] = defaultdict(list)
        for violation in violations:
            violations_by_file[Path(violation.file)].append(violation)
        core_bases = frozenset(
            f"Flext{suffix}" for suffix in c.Infra.FAMILY_SUFFIXES.values()
        )
        for file_path, grouped in violations_by_file.items():
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            lines = source.splitlines()
            missing_by_facade: Mapping[str, t.Infra.StrSet] = defaultdict(set)
            for violation in grouped:
                missing_by_facade[violation.facade_class].add(violation.missing_base)
            new_bases: t.Infra.StrSet = set()
            changed = False
            for idx, line in enumerate(lines):
                stripped = line.strip()
                for facade_name, missing in missing_by_facade.items():
                    if not stripped.startswith(f"class {facade_name}"):
                        continue
                    updated, added = (
                        FlextInfraUtilitiesRefactorNamespaceMro._rewrite_class_header(
                            line=line,
                            facade_name=facade_name,
                            missing=missing,
                            core_bases=core_bases,
                        )
                    )
                    if updated != line:
                        lines[idx] = updated
                        new_bases.update(added)
                        changed = True
            if not changed:
                continue
            imports = FlextInfraUtilitiesRefactorNamespaceMro._build_missing_imports(
                lines=lines,
                new_bases=new_bases,
            )
            rewritten_lines = (
                FlextInfraUtilitiesRefactorNamespaceMro._insert_import_lines(
                    lines=lines,
                    imports=imports,
                )
            )
            _ = file_path.write_text(
                "\n".join(rewritten_lines).rstrip() + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
            FlextInfraUtilitiesFormatting.run_ruff_fix(
                file_path,
                include_format=True,
                quiet=True,
            )

    @staticmethod
    def _rewrite_class_header(
        *,
        line: str,
        facade_name: str,
        missing: t.Infra.StrSet,
        core_bases: frozenset[str],
    ) -> tuple[str, t.Infra.StrSet]:
        prefix = f"class {facade_name}"
        stripped = line.strip()
        if not stripped.startswith(prefix):
            return (line, set())
        if stripped.endswith(":") and "(" not in stripped:
            current_bases: MutableSequence[str] = []
            indent = line[: len(line) - len(line.lstrip())]
            suffix = ":"
        else:
            start = stripped.find("(")
            end = stripped.rfind(")")
            if start < 0 or end < 0 or end <= start:
                return (line, set())
            current_bases = [
                item.strip()
                for item in stripped[start + 1 : end].split(",")
                if item.strip()
            ]
            indent = line[: len(line) - len(line.lstrip())]
            suffix = stripped[end + 1 :] or ":"
        proposed = list(current_bases) + [
            base for base in sorted(missing) if base not in current_bases
        ]
        if any(base in core_bases for base in missing):
            proposed = [base for base in proposed if base not in core_bases]
        if proposed == current_bases:
            return (line, set())
        rewritten = f"{indent}class {facade_name}({', '.join(proposed)}){suffix}"
        return (rewritten, set(proposed) - set(current_bases))

    @staticmethod
    def _build_missing_imports(
        *,
        lines: t.StrSequence,
        new_bases: t.Infra.StrSet,
    ) -> t.StrSequence:
        existing_imports: t.Infra.StrSet = set()
        for line in lines:
            parsed = (
                FlextInfraUtilitiesRefactorNamespaceMro._parse_simple_from_import_line(
                    line,
                )
            )
            if parsed is None:
                continue
            _module_name, names = parsed
            existing_imports.update(names)
        return [
            f"from {FlextInfraUtilitiesFormatting.class_name_to_module(base)} import {base}"
            for base in sorted(new_bases)
            if base not in existing_imports
        ]

    @staticmethod
    def rewrite_missing_future_annotations(
        *,
        py_files: Sequence[Path],
    ) -> None:
        for file_path in py_files:
            if file_path.name == "py.typed":
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            if c.Infra.SourceCode.FUTURE_ANNOTATIONS in source:
                continue
            lines = source.splitlines()
            if not lines:
                continue
            insert_idx = (
                FlextInfraUtilitiesParsing.index_after_docstring_and_future_imports(
                    lines
                )
            )
            rewritten = (
                lines[:insert_idx]
                + ["", c.Infra.SourceCode.FUTURE_ANNOTATIONS, ""]
                + lines[insert_idx:]
            )
            _ = file_path.write_text(
                "\n".join(rewritten).rstrip() + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )


__all__ = ["FlextInfraUtilitiesRefactorNamespaceMro"]
