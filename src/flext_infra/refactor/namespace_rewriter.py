"""Namespace enforcement rewriting operations."""

from __future__ import annotations

import ast
import operator
import re
import token
import tokenize
from collections import defaultdict
from io import StringIO
from pathlib import Path

from flext_infra import c, m, u
from flext_infra.refactor._detectors.import_alias_detector import ImportAliasDetector
from flext_infra.refactor.dependency_analyzer import (
    FlextInfraRefactorDependencyAnalyzerFacade,
)

load_python_module = FlextInfraRefactorDependencyAnalyzerFacade.load_python_module


class NamespaceEnforcementRewriter:
    """Rewrite source files to enforce namespace conventions."""

    @staticmethod
    def _preferred_file_name(*, family: str) -> str:
        pattern = c.Infra.FAMILY_FILES.get(
            family,
            "utilities.py",
        )
        return pattern.lstrip("*")

    @staticmethod
    def _base_import_for_family(*, family: str) -> str:
        class_name = f"Flext{c.Infra.FAMILY_SUFFIXES.get(family, 'Utilities')}"
        return f"from flext_core import {class_name}"

    @staticmethod
    def _base_class_for_family(*, family: str) -> str:
        return f"Flext{c.Infra.FAMILY_SUFFIXES.get(family, 'Utilities')}"

    @staticmethod
    def _write_missing_facade_file(
        *,
        file_path: Path,
        family: str,
        class_name: str,
    ) -> None:
        alias = family
        import_stmt = NamespaceEnforcementRewriter._base_import_for_family(
            family=family,
        )
        base_class = NamespaceEnforcementRewriter._base_class_for_family(family=family)
        content = (
            '"""Auto-generated facade to enforce MRO namespace contracts."""\n\n'
            "from __future__ import annotations\n\n"
            f"{import_stmt}\n\n"
            f"class {class_name}({base_class}):\n"
            "    pass\n\n"
            f"{alias} = {class_name}\n"
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _ = file_path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)

    @classmethod
    def ensure_missing_facades(
        cls,
        *,
        project_root: Path,
        project_name: str,
        facade_statuses: list[m.Infra.FacadeStatus],
    ) -> None:
        """Create missing facade module files for the project."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / "__init__.py").is_file()
        ]
        if len(package_dirs) == 0:
            return
        primary_package = package_dirs[0]
        stem = FlextInfraRefactorDependencyAnalyzerFacade.NamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        for status in facade_statuses:
            if status.exists:
                continue
            suffix = c.Infra.FAMILY_SUFFIXES[status.family]
            class_name = f"{stem}{suffix}"
            file_name = cls._preferred_file_name(family=status.family)
            target_path = primary_package / file_name
            if target_path.exists():
                content = target_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                mutated = False
                class_signature = f"class {class_name}("
                if (
                    class_signature not in content
                    and f"class {class_name}:" not in content
                ):
                    base_class = cls._base_class_for_family(family=status.family)
                    snippet = f"\n\nclass {class_name}({base_class}):\n    pass\n"
                    content = content.rstrip() + snippet
                    mutated = True
                alias_line = f"{status.family} = {class_name}"
                if alias_line not in content:
                    content = content.rstrip() + f"\n\n{alias_line}\n"
                    mutated = True
                if mutated:
                    _ = target_path.write_text(
                        content,
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                continue
            cls._write_missing_facade_file(
                file_path=target_path,
                family=status.family,
                class_name=class_name,
            )

    @staticmethod
    def rewrite_import_alias_violations(*, py_files: list[Path]) -> None:
        """Rewrite deep import aliases to use facade shortcuts."""
        deep_import_re = re.compile(
            r"^(\s*)from\s+(flext_core|flext_infra)(\.\S+)\s+import\s+(.+)$",
        )
        runtime_alias_names_by_package = (
            ImportAliasDetector.RUNTIME_ALIAS_NAMES_BY_PACKAGE
        )

        def _build_replacement(*, package: str, imported_names: list[str]) -> str:
            ordered_aliases = runtime_alias_names_by_package.get(package, ())
            ordered = [
                alias for alias in ordered_aliases if alias in set(imported_names)
            ]
            return f"from {package} import {', '.join(ordered)}"

        for file_path in py_files:
            if file_path.name == "__init__.py":
                continue
            parsed_file = load_python_module(file_path)
            if parsed_file is None:
                continue
            if ImportAliasDetector.is_facade_or_subclass_file(
                file_path=file_path,
                tree=parsed_file.tree,
            ):
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            lines = source.splitlines(keepends=True)
            changed = False
            seen_replacements: set[str] = set()
            seen_aliases_by_package: dict[str, list[set[str]]] = {
                package: [] for package in runtime_alias_names_by_package
            }
            for line in lines:
                stripped = line.strip()
                for package in runtime_alias_names_by_package:
                    prefix = f"from {package} import "
                    if not stripped.startswith(prefix):
                        continue
                    candidate_clause = stripped.removeprefix(prefix)
                    candidate_names = ImportAliasDetector.parse_imported_names(
                        candidate_clause,
                    )
                    if len(candidate_names) == 0:
                        continue
                    replacement = _build_replacement(
                        package=package,
                        imported_names=candidate_names,
                    )
                    seen_replacements.add(replacement)
                    seen_aliases_by_package[package].append(set(candidate_names))
            new_lines: list[str] = []
            for line in lines:
                match = deep_import_re.match(line.rstrip())
                if match:
                    indent = match.group(1)
                    if len(indent) > 0:
                        new_lines.append(line)
                        continue
                    module_suffix = match.group(3)
                    if "._" in module_suffix:
                        new_lines.append(line)
                        continue
                    stripped_line = line.strip()
                    if (
                        "(" in stripped_line and ")" not in stripped_line
                    ) or stripped_line.endswith("\\"):
                        new_lines.append(line)
                        continue
                    pkg = match.group(2)
                    import_clause = match.group(4)
                    if " as " in import_clause:
                        new_lines.append(line)
                        continue
                    imported_names = ImportAliasDetector.parse_imported_names(
                        import_clause,
                    )
                    if len(imported_names) == 0:
                        new_lines.append(line)
                        continue
                    if "*" in imported_names:
                        new_lines.append(line)
                        continue
                    allowed_aliases = set(runtime_alias_names_by_package.get(pkg, ()))
                    if not all(name in allowed_aliases for name in imported_names):
                        new_lines.append(line)
                        continue
                    replacement = _build_replacement(
                        package=pkg,
                        imported_names=imported_names,
                    )
                    target_names = set(imported_names)
                    has_superset = any(
                        target_names.issubset(existing)
                        for existing in seen_aliases_by_package.get(pkg, [])
                    )
                    if has_superset:
                        changed = True
                        continue
                    if replacement and replacement not in seen_replacements:
                        new_lines.append(f"{indent}{replacement}\n")
                        seen_replacements.add(replacement)
                        seen_aliases_by_package[pkg].append(target_names)
                        changed = True
                        continue
                    if replacement and replacement in seen_replacements:
                        changed = True
                        continue
                new_lines.append(line)
            if changed:
                _ = file_path.write_text(
                    "".join(new_lines),
                    encoding=c.Infra.Encoding.DEFAULT,
                )

    @classmethod
    def rewrite_namespace_source_violations(
        cls,
        *,
        violations: list[m.Infra.NamespaceSourceViolation],
        parse_failures: list[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite wrong-source alias imports to use correct project facade."""
        violations_by_file: dict[Path, list[m.Infra.NamespaceSourceViolation]] = (
            defaultdict(
                list,
            )
        )
        for violation in violations:
            violations_by_file[Path(violation.file)].append(violation)
        for file_path, file_violations in violations_by_file.items():
            parsed = load_python_module(
                file_path,
                stage="namespace-source-rewrite",
                parse_failures=parse_failures,
            )
            if parsed is None:
                continue
            source = parsed.source
            tree = parsed.tree
            line_map: dict[int, ast.ImportFrom] = {
                stmt.lineno: stmt
                for stmt in tree.body
                if isinstance(stmt, ast.ImportFrom)
                and stmt.module is not None
                and stmt.level == 0
                and stmt.end_lineno is not None
            }
            violations_by_line: dict[int, list[m.Infra.NamespaceSourceViolation]] = (
                defaultdict(
                    list,
                )
            )
            for violation in file_violations:
                violations_by_line[violation.line].append(violation)
            lines = source.splitlines(keepends=True)
            moved_by_source: dict[str, list[str]] = defaultdict(list)
            changed = False
            for line_no in sorted(violations_by_line, reverse=True):
                stmt = line_map.get(line_no)
                if stmt is None or stmt.module is None or stmt.end_lineno is None:
                    continue
                alias_to_source = {
                    violation.alias: violation.correct_source
                    for violation in violations_by_line[line_no]
                }
                kept_names: list[str] = []
                for alias in stmt.names:
                    if alias.name == "*":
                        continue
                    alias_text = alias.name
                    if alias.asname is not None:
                        alias_text = f"{alias.name} as {alias.asname}"
                    correct_source = alias_to_source.get(alias.name)
                    if correct_source is None or alias.asname is not None:
                        kept_names.append(alias_text)
                        continue
                    if alias.name not in moved_by_source[correct_source]:
                        moved_by_source[correct_source].append(alias.name)
                    changed = True
                replacement_lines: list[str] = []
                if len(kept_names) > 0:
                    replacement_lines.append(
                        f"from {stmt.module} import {', '.join(kept_names)}\n",
                    )
                start = stmt.lineno - 1
                end = stmt.end_lineno
                lines[start:end] = replacement_lines
            if not changed:
                continue
            rewritten_source = "".join(lines)
            try:
                rewritten_tree: ast.Module = ast.parse(rewritten_source)
            except SyntaxError:
                continue
            final_lines = rewritten_source.splitlines(keepends=True)
            existing_imports_by_source: dict[str, ast.ImportFrom] = {}
            for stmt in rewritten_tree.body:
                if not isinstance(stmt, ast.ImportFrom):
                    continue
                if stmt.module is None or stmt.level != 0:
                    continue
                if stmt.module in moved_by_source:
                    existing_imports_by_source[stmt.module] = stmt
            for source_name, moved_aliases in moved_by_source.items():
                existing_stmt = existing_imports_by_source.get(source_name)
                if existing_stmt is not None and existing_stmt.end_lineno is not None:
                    existing_names = [
                        alias.name
                        for alias in existing_stmt.names
                        if alias.name != "*" and alias.asname is None
                    ]
                    if len(existing_names) == 0:
                        continue
                    merged_names = list(existing_names)
                    for alias_name in moved_aliases:
                        if alias_name not in merged_names:
                            merged_names.append(alias_name)
                    start = existing_stmt.lineno - 1
                    end = existing_stmt.end_lineno
                    final_lines[start:end] = [
                        f"from {source_name} import {', '.join(merged_names)}\n",
                    ]
                    continue
                insert_at = cls._namespace_source_import_insert_index(lines=final_lines)
                final_lines[insert_at:insert_at] = [
                    f"from {source_name} import {', '.join(moved_aliases)}\n",
                ]
            _ = file_path.write_text(
                "".join(final_lines),
                encoding=c.Infra.Encoding.DEFAULT,
            )
            u.Infra.run_ruff_fix(file_path, include_format=True, quiet=True)

    @classmethod
    def rewrite_mro_completeness_violations(
        cls,
        *,
        violations: list[m.Infra.MROCompletenessViolation],
        parse_failures: list[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite facade class headers adding missing MRO bases and Ruff-format."""
        violations_by_file: dict[Path, list[m.Infra.MROCompletenessViolation]] = (
            defaultdict(
                list,
            )
        )
        for violation in violations:
            violations_by_file[Path(violation.file)].append(violation)
        for file_path, file_violations in violations_by_file.items():
            parsed = load_python_module(
                file_path,
                stage="mro-completeness-rewrite",
                parse_failures=parse_failures,
            )
            if parsed is None:
                continue
            lines = parsed.source.splitlines(keepends=True)
            changed = False
            missing_by_facade: dict[str, set[str]] = defaultdict(set)
            for violation in file_violations:
                missing_by_facade[violation.facade_class].add(violation.missing_base)
            facade_nodes = [
                stmt
                for stmt in parsed.tree.body
                if isinstance(stmt, ast.ClassDef) and stmt.name in missing_by_facade
            ]
            for class_node in sorted(
                facade_nodes,
                key=operator.attrgetter("lineno"),
                reverse=True,
            ):
                current_bases = [
                    base_name
                    for base_name in (
                        cls._extract_base_name(base_expr)
                        for base_expr in class_node.bases
                    )
                    if len(base_name) > 0
                ]
                missing_bases = sorted(missing_by_facade[class_node.name])
                proposed_bases = current_bases + [
                    base_name
                    for base_name in missing_bases
                    if base_name not in current_bases
                ]
                if len(proposed_bases) == len(current_bases):
                    continue
                indent = " " * class_node.col_offset
                new_header = (
                    f"{indent}class {class_node.name}({', '.join(proposed_bases)}):\n"
                )
                start = class_node.lineno - 1
                end = start
                while end < len(lines):
                    if lines[end].rstrip().endswith("):"):
                        break
                    end += 1
                if end >= len(lines):
                    continue
                lines[start : end + 1] = [new_header]
                changed = True
            if not changed:
                continue
            _ = file_path.write_text(
                "".join(lines),
                encoding=c.Infra.Encoding.DEFAULT,
            )
            u.Infra.run_ruff_fix(file_path, include_format=True, quiet=True)

    @staticmethod
    def _extract_base_name(base_expr: ast.expr) -> str:
        if isinstance(base_expr, ast.Name):
            return base_expr.id
        if isinstance(base_expr, ast.Attribute):
            return base_expr.attr
        if isinstance(base_expr, ast.Subscript):
            return NamespaceEnforcementRewriter._extract_base_name(base_expr.value)
        return ""

    @staticmethod
    def _namespace_source_import_insert_index(*, lines: list[str]) -> int:
        insert_at = 0
        for index, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) == 0:
                if index <= insert_at:
                    insert_at = index + 1
                continue
            if stripped.startswith("from __future__ import "):
                insert_at = index + 1
                continue
            if stripped.startswith(("import ", "from ")):
                insert_at = index + 1
                continue
            break
        return insert_at

    @staticmethod
    def rewrite_runtime_alias_violations(*, py_files: list[Path]) -> None:
        """Rewrite runtime alias statements to match expected patterns."""
        for file_path in py_files:
            expected = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(
                file_path.name,
            )
            if expected is None:
                continue
            alias_name, expected_suffix = expected
            parsed = load_python_module(file_path)
            if parsed is None:
                continue
            source, tree = parsed.source, parsed.tree
            class_candidates = [
                node.name
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name.endswith(expected_suffix)
            ]
            if len(class_candidates) != 1:
                continue
            target_class = class_candidates[0]
            lines = source.splitlines()
            kept_lines = [
                line
                for line in lines
                if not line.strip().startswith(f"{alias_name} = ")
            ]
            kept_source = "\n".join(kept_lines).rstrip()
            rewritten = f"{kept_source}\n\n{alias_name} = {target_class}\n"
            _ = file_path.write_text(rewritten, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def rewrite_missing_future_annotations(*, py_files: list[Path]) -> None:
        """Add missing future annotations imports to source files."""
        for file_path in py_files:
            if file_path.name == "py.typed":
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            if "from __future__ import annotations" in source:
                continue
            lines = source.splitlines()
            if len(lines) == 0:
                continue
            insert_idx = 0
            if lines[0].startswith("#!"):
                insert_idx = 1
            if insert_idx < len(lines) and re.match(
                r"^#.*coding[:=]",
                lines[insert_idx],
            ):
                insert_idx += 1
            if insert_idx < len(lines) and (
                lines[insert_idx].startswith('"""')
                or lines[insert_idx].startswith("'''")
            ):
                docstring_single_line_quote_count = 2
                quote = lines[insert_idx][:3]
                line_text = lines[insert_idx]
                if line_text.count(quote) >= docstring_single_line_quote_count:
                    insert_idx += 1
                else:
                    for idx in range(insert_idx + 1, len(lines)):
                        if quote in lines[idx]:
                            insert_idx = idx + 1
                            break
            new_lines = (
                lines[:insert_idx]
                + ["", "from __future__ import annotations", ""]
                + lines[insert_idx:]
            )
            _ = file_path.write_text(
                "\n".join(new_lines).rstrip() + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )

    @classmethod
    def rewrite_manual_protocol_violations(
        cls,
        *,
        project_root: Path,
        py_files: list[Path],
        violations: list[m.Infra.ManualProtocolViolation],
    ) -> None:
        """Move manual protocol definitions to their canonical files."""
        grouped_names: dict[Path, set[str]] = defaultdict(set)
        for violation in violations:
            grouped_names[Path(violation.file)].add(violation.name)
        protocol_moves: list[tuple[Path, Path, tuple[str, ...]]] = []
        for source_file, protocol_names in grouped_names.items():
            move_result = cls._move_protocol_classes_to_canonical_file(
                project_root=project_root,
                source_file=source_file,
                protocol_names=protocol_names,
            )
            if move_result is None:
                continue
            protocol_moves.append(move_result)
        if len(protocol_moves) > 0:
            cls._rewrite_moved_protocol_imports(
                project_root=project_root,
                py_files=py_files,
                protocol_moves=protocol_moves,
            )

    @classmethod
    def _move_protocol_classes_to_canonical_file(
        cls,
        *,
        project_root: Path,
        source_file: Path,
        protocol_names: set[str],
    ) -> tuple[Path, Path, tuple[str, ...]] | None:
        parsed = load_python_module(source_file)
        if parsed is None:
            return None
        source, tree = parsed.source, parsed.tree
        class_nodes: list[ast.ClassDef] = []
        remove_ranges: list[tuple[int, int]] = []
        blocks: list[str] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name not in protocol_names:
                continue
            if not FlextInfraRefactorDependencyAnalyzerFacade.ManualProtocolDetector.is_protocol_class(
                stmt,
            ):
                continue
            block = ast.get_source_segment(source, stmt)
            if block is None:
                lines = source.splitlines()
                block = "\n".join(lines[stmt.lineno - 1 : stmt.end_lineno])
            if stmt.end_lineno is None:
                continue
            class_nodes.append(stmt)
            remove_ranges.append((stmt.lineno, stmt.end_lineno))
            blocks.append(block.strip("\n"))
        if len(class_nodes) == 0:
            return None
        target_file = cls._manual_protocol_target_file(
            project_root=project_root,
            source_file=source_file,
        )
        cls._append_protocol_blocks(
            project_root=project_root,
            target_file=target_file,
            blocks=blocks,
        )
        source_lines = source.splitlines()
        filtered_lines: list[str] = []
        for line_number, line_content in enumerate(source_lines, start=1):
            should_skip = any(
                start <= line_number <= end for start, end in remove_ranges
            )
            if should_skip:
                continue
            filtered_lines.append(line_content)
        rewritten = "\n".join(filtered_lines).rstrip()
        normalized = re.sub(r"\n{3,}", "\n\n", rewritten)
        _ = source_file.write_text(normalized + "\n", encoding=c.Infra.Encoding.DEFAULT)
        moved_names = tuple(sorted({node.name for node in class_nodes}))
        return (source_file, target_file, moved_names)

    @classmethod
    def rewrite_manual_typing_alias_violations(
        cls,
        *,
        project_root: Path,
        violations: list[m.Infra.ManualTypingAliasViolation],
        parse_failures: list[m.Infra.ParseFailureViolation],
    ) -> None:
        """Move manual typing aliases to their canonical files."""
        grouped_names: dict[Path, set[str]] = defaultdict(set)
        for violation in violations:
            grouped_names[Path(violation.file)].add(violation.name)
        for source_file, alias_names in grouped_names.items():
            cls._move_typing_aliases_to_canonical_file(
                project_root=project_root,
                source_file=source_file,
                alias_names=alias_names,
                parse_failures=parse_failures,
            )

    @classmethod
    def _move_typing_aliases_to_canonical_file(
        cls,
        *,
        project_root: Path,
        source_file: Path,
        alias_names: set[str],
        parse_failures: list[m.Infra.ParseFailureViolation],
    ) -> None:
        parsed = load_python_module(
            source_file,
            stage="manual-typing-rewrite",
            parse_failures=parse_failures,
        )
        if parsed is None:
            return
        source, tree = parsed.source, parsed.tree
        remove_ranges: list[tuple[int, int]] = []
        blocks: list[str] = []
        for stmt in tree.body:
            if isinstance(stmt, ast.TypeAlias):
                alias_name = stmt.name.id
                if alias_name not in alias_names:
                    continue
                if stmt.end_lineno is None:
                    continue
                block = ast.get_source_segment(source, stmt)
                if block is None:
                    lines = source.splitlines()
                    block = "\n".join(lines[stmt.lineno - 1 : stmt.end_lineno])
                remove_ranges.append((stmt.lineno, stmt.end_lineno))
                blocks.append(block.strip("\n"))
                continue
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id not in alias_names:
                    continue
                if stmt.end_lineno is None:
                    continue
                annotation_src = ast.get_source_segment(source, stmt.annotation) or ""
                if "TypeAlias" not in annotation_src:
                    continue
                block = ast.get_source_segment(source, stmt)
                if block is None:
                    lines = source.splitlines()
                    block = "\n".join(lines[stmt.lineno - 1 : stmt.end_lineno])
                remove_ranges.append((stmt.lineno, stmt.end_lineno))
                blocks.append(block.strip("\n"))
        if len(blocks) == 0:
            return
        target_file = cls._manual_typings_target_file(
            project_root=project_root,
            source_file=source_file,
        )
        cls._append_typing_alias_blocks(target_file=target_file, blocks=blocks)
        source_lines = source.splitlines()
        filtered_lines: list[str] = []
        for line_number, line_content in enumerate(source_lines, start=1):
            should_skip = any(
                start <= line_number <= end for start, end in remove_ranges
            )
            if not should_skip:
                filtered_lines.append(line_content)
        rewritten = "\n".join(filtered_lines).rstrip()
        normalized = re.sub(r"\n{3,}", "\n\n", rewritten)
        _ = source_file.write_text(normalized + "\n", encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def _manual_typings_target_file(*, project_root: Path, source_file: Path) -> Path:
        parts = source_file.parts
        if "src" in parts:
            src_index = parts.index("src")
            if src_index + 1 < len(parts):
                package_name = parts[src_index + 1]
                return (
                    project_root
                    / c.Infra.Paths.DEFAULT_SRC_DIR
                    / package_name
                    / "typings.py"
                )
        return source_file.parent / "typings.py"

    @staticmethod
    def _append_typing_alias_blocks(*, target_file: Path, blocks: list[str]) -> None:
        if len(blocks) == 0:
            return
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else ""
        )
        updated = target_source
        if "from __future__ import annotations" not in updated:
            updated = "from __future__ import annotations\n\n" + updated.lstrip("\n")
        merged_blocks = "\n\n".join(blocks)
        updated = updated.rstrip() + "\n\n" + merged_blocks + "\n"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        _ = target_file.write_text(updated, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def rewrite_compatibility_alias_violations(
        *,
        violations: list[m.Infra.CompatibilityAliasViolation],
        parse_failures: list[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite compatibility alias violations in source files."""
        grouped: dict[Path, dict[str, str]] = defaultdict(dict)
        for violation in violations:
            grouped[Path(violation.file)][violation.alias_name] = violation.target_name
        for file_path, alias_map in grouped.items():
            parsed = load_python_module(
                file_path,
                stage="compatibility-alias-rewrite",
                parse_failures=parse_failures,
            )
            if parsed is None:
                continue
            source = parsed.source
            assignment_lines: set[int] = set()
            for stmt in parsed.tree.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                if len(stmt.targets) != 1:
                    continue
                target = stmt.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                if not isinstance(stmt.value, ast.Name):
                    continue
                if target.id in alias_map and stmt.value.id == alias_map[target.id]:
                    assignment_lines.add(stmt.lineno)
            if len(assignment_lines) == 0:
                continue
            kept_lines = [
                line
                for idx, line in enumerate(source.splitlines(keepends=True), start=1)
                if idx not in assignment_lines
            ]
            kept_source = "".join(kept_lines)
            line_buffer = kept_source.splitlines(keepends=True)
            replacements_by_line: dict[int, list[tuple[int, int, str]]] = defaultdict(
                list,
            )
            token_generator = tokenize.generate_tokens(StringIO(kept_source).readline)
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
                    line_text = (
                        line_text[:start_col] + replacement + line_text[end_col:]
                    )
                line_buffer[line_idx] = line_text
            rewritten = "".join(line_buffer)
            if rewritten != source:
                _ = file_path.write_text(rewritten, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def _manual_protocol_target_file(*, project_root: Path, source_file: Path) -> Path:
        parts = source_file.parts
        if "src" in parts:
            src_index = parts.index("src")
            if src_index + 1 < len(parts):
                package_name = parts[src_index + 1]
                return (
                    project_root
                    / c.Infra.Paths.DEFAULT_SRC_DIR
                    / package_name
                    / "protocols.py"
                )
        return source_file.parent / "protocols.py"

    @classmethod
    def _append_protocol_blocks(
        cls,
        *,
        project_root: Path,
        target_file: Path,
        blocks: list[str],
    ) -> None:
        if len(blocks) == 0:
            return
        project_name = project_root.name
        class_stem = FlextInfraRefactorDependencyAnalyzerFacade.NamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        protocols_class = f"{class_stem}Protocols"
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else ""
        )
        updated = target_source
        if "from __future__ import annotations" not in updated:
            updated = "from __future__ import annotations\n\n" + updated.lstrip("\n")
        if "from typing import Protocol" not in updated:
            updated = updated.rstrip() + "\n\nfrom typing import Protocol\n"
        if (
            f"class {protocols_class}(" not in updated
            and f"class {protocols_class}:" not in updated
        ):
            updated = updated.rstrip() + f"\n\nclass {protocols_class}:\n    pass\n"
        alias_line = f"p = {protocols_class}"
        if alias_line not in updated:
            updated = updated.rstrip() + f"\n\n{alias_line}\n"
        for block in blocks:
            class_header = block.splitlines()[0].strip()
            if class_header in updated:
                continue
            updated = updated.rstrip() + "\n\n" + block + "\n"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        _ = target_file.write_text(
            updated.rstrip() + "\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )

    @staticmethod
    def _rewrite_moved_protocol_imports(
        *,
        project_root: Path,
        py_files: list[Path],
        protocol_moves: list[tuple[Path, Path, tuple[str, ...]]],
    ) -> None:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR

        def _module_path(file_path: Path) -> str:
            try:
                relative = file_path.relative_to(src_dir)
            except ValueError:
                return ""
            parts = list(relative.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            return ".".join(parts)

        source_target_names: list[tuple[str, str, set[str]]] = []
        for source_file, target_file, moved_name_seq in protocol_moves:
            source_module = _module_path(source_file)
            target_module = _module_path(target_file)
            if not source_module or not target_module or source_module == target_module:
                continue
            source_target_names.append(
                (source_module, target_module, set(moved_name_seq)),
            )
        if len(source_target_names) == 0:
            return
        for py_file in py_files:
            parsed = load_python_module(py_file)
            if parsed is None:
                continue
            source = parsed.source
            tree = parsed.tree
            new_lines = source.splitlines(keepends=True)
            changed = False
            for stmt in tree.body:
                if not isinstance(stmt, ast.ImportFrom):
                    continue
                if stmt.module is None:
                    continue
                for source_module, target_module, moved_names in source_target_names:
                    if stmt.module != source_module:
                        continue
                    imported = [alias.name for alias in stmt.names if alias.name != "*"]
                    if not any(name in moved_names for name in imported):
                        continue
                    if stmt.lineno <= 0 or stmt.lineno > len(new_lines):
                        continue
                    line_index = stmt.lineno - 1
                    line_text = new_lines[line_index]
                    new_lines[line_index] = line_text.replace(
                        source_module,
                        target_module,
                    )
                    changed = True
            if changed:
                _ = py_file.write_text(
                    "".join(new_lines),
                    encoding=c.Infra.Encoding.DEFAULT,
                )


__all__ = ["NamespaceEnforcementRewriter"]
