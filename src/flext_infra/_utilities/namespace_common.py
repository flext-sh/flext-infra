"""Shared text/path helpers for namespace refactor utilities."""

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

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRopeSource,
    c,
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
            MutableSequence[t.Triple[int, int, str]],
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


__all__: list[str] = ["FlextInfraUtilitiesRefactorNamespaceCommon"]
