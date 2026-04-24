"""Shared helpers and MRO/future-import rewrites for namespace refactors."""

from __future__ import annotations

import operator
import re
import token
import tokenize
from collections import defaultdict
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from io import StringIO
from pathlib import Path

from flext_cli import u

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRopeSource,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorNamespaceCommon:
    """Shared text and path helpers for namespace refactor utilities."""

    @staticmethod
    def shared_workspace_root(*, py_files: Sequence[Path]) -> Path:
        existing_files = [path.resolve() for path in py_files if path.exists()]
        if not existing_files:
            return Path.cwd()
        project_root = FlextInfraUtilitiesIteration.resolve_project_root(
            existing_files[0],
        )
        return (
            project_root.parent
            if project_root is not None
            else existing_files[0].parent
        )

    @staticmethod
    def _parse_simple_from_import_line(
        line: str,
    ) -> t.Infra.TransformResult | None:
        stripped = line.strip()
        if (
            not stripped.startswith("from ")
            or "(" in stripped
            or ")" in stripped
            or " as " in stripped
        ):
            return None
        module_name, separator, imported_names = stripped.removeprefix(
            "from "
        ).partition(" import ")
        if not separator or not module_name or not imported_names:
            return None
        names = [name.strip() for name in imported_names.split(",") if name.strip()]
        return (module_name, names)

    @staticmethod
    def insert_import_lines(
        *,
        lines: t.StrSequence,
        imports: t.StrSequence,
    ) -> t.StrSequence:
        if not imports:
            return list(lines)
        insert_idx = (
            FlextInfraUtilitiesRopeSource.index_after_docstring_and_future_imports(
                lines
            )
        )
        return [*lines[:insert_idx], *imports, *lines[insert_idx:]]

    @staticmethod
    def canonical_target_file(
        *,
        project_root: Path,
        source_file: Path,
        filename: str,
    ) -> Path:
        parts = source_file.parts
        src_dir: str = c.Infra.DEFAULT_SRC_DIR
        if src_dir in parts:
            src_index = parts.index(src_dir)
            if src_index + 1 < len(parts):
                package_name = parts[src_index + 1]
                return project_root / src_dir / package_name / filename
        return source_file.parent / filename

    @staticmethod
    def find_top_level_block(
        *,
        lines: t.StrSequence,
        header: str,
    ) -> tuple[int, int] | None:
        start_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith(header):
                start_idx = idx
                break
        if start_idx < 0:
            return None
        end_idx = len(lines)
        for idx in range(start_idx + 1, len(lines)):
            line = lines[idx]
            if line and not line.startswith((" ", "\t")) and not line.startswith("#"):
                end_idx = idx
                break
        return (start_idx, end_idx)

    @staticmethod
    def compat_assignment_target(
        line: str,
        *,
        alias_map: t.StrMapping,
    ) -> str | None:
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            return None
        left, right = [part.strip() for part in stripped.split("=", 1)]
        return left if alias_map.get(left) == right else None

    @staticmethod
    def apply_token_replacements(
        *,
        source: str,
        alias_map: t.StrMapping,
    ) -> str:
        line_buffer = source.splitlines(keepends=True)
        replacements_by_line: Mapping[
            int,
            MutableSequence[t.Infra.Triple[int, int, str]],
        ] = defaultdict(list)
        token_generator = tokenize.generate_tokens(StringIO(source).readline)
        for tok in token_generator:
            if tok.type != token.NAME:
                continue
            replacement = alias_map.get(tok.string)
            if replacement is None:
                continue
            start_line, start_col = tok.start
            end_line, end_col = tok.end
            if start_line != end_line:
                continue
            replacements_by_line[start_line - 1].append((
                start_col,
                end_col,
                replacement,
            ))
        for line_idx, replacements in replacements_by_line.items():
            if line_idx < 0 or line_idx >= len(line_buffer):
                continue
            line_text = line_buffer[line_idx]
            for start_col, end_col, replacement in sorted(
                replacements,
                key=operator.itemgetter(0),
                reverse=True,
            ):
                line_text = line_text[:start_col] + replacement + line_text[end_col:]
            line_buffer[line_idx] = line_text
        return "".join(line_buffer)

    @staticmethod
    def class_name_to_module(class_name: str) -> str:
        """Convert CamelCase class names to snake_case module names."""
        head = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", head).lower()


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
            source = file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
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
                FlextInfraUtilitiesRefactorNamespaceMro.insert_import_lines(
                    lines=lines,
                    imports=imports,
                )
            )
            _ = file_path.write_text(
                "\n".join(rewritten_lines).rstrip() + "\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            _ = u.Cli.run_checked(["ruff", "check", "--fix", str(file_path)])
            _ = u.Cli.run_checked(["ruff", "format", str(file_path)])

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
            f"from {FlextInfraUtilitiesRefactorNamespaceCommon.class_name_to_module(base)} import {base}"
            for base in sorted(new_bases)
            if base not in existing_imports
        ]

    @staticmethod
    def rewrite_missing_future_annotations(
        *,
        py_files: Sequence[Path],
    ) -> None:
        for file_path in py_files:
            if file_path.name == c.Infra.PY_TYPED:
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            if c.Infra.FUTURE_ANNOTATIONS in source:
                continue
            lines = source.splitlines()
            if not lines:
                continue
            insert_idx = (
                FlextInfraUtilitiesRopeSource.index_after_docstring_and_future_imports(
                    lines
                )
            )
            rewritten = (
                lines[:insert_idx]
                + ["", c.Infra.FUTURE_ANNOTATIONS, ""]
                + lines[insert_idx:]
            )
            _ = file_path.write_text(
                "\n".join(rewritten).rstrip() + "\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )


__all__: list[str] = [
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceMro",
]
