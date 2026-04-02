"""Namespace enforcement rewriting utilities for the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
import re
import token
import tokenize
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from io import StringIO
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
import tomlkit
from tomlkit.exceptions import TOMLKitError

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraNamespaceFacadeScanner,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesRefactorLoader,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorNamespace:
    """Namespace enforcement rewriting utilities as static methods for MRO chain."""

    _base_chains_cache: ClassVar[MutableMapping[Path, Mapping[str, Sequence[str]]]] = {}

    @staticmethod
    def build_expected_base_chains(
        *,
        project_root: Path,
    ) -> Mapping[str, Sequence[str]]:
        """Build expected MRO base chains from the project's path dependencies.

        Connects the dep graph SSOT (ExtraPathsManager) with the class name SSOT
        (FacadeScanner) to compute the expected base classes for each family.

        Results are memoized per project_root for the duration of the process.

        Returns:
            Mapping from family alias to sequence of expected base class names.
            E.g. ``{"m": ["FlextMeltanoModels", "FlextDbOracleModels"]}``.

        """
        resolved = project_root.resolve()
        cached = FlextInfraUtilitiesRefactorNamespace._base_chains_cache.get(resolved)
        if cached is not None:
            return cached
        result = FlextInfraUtilitiesRefactorNamespace._compute_base_chains(
            project_root=resolved,
        )
        FlextInfraUtilitiesRefactorNamespace._base_chains_cache[resolved] = result
        return result

    @staticmethod
    def _compute_base_chains(
        *,
        project_root: Path,
    ) -> Mapping[str, Sequence[str]]:
        """Compute expected MRO base chains (uncached)."""
        pyproject_path = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return {}
        try:
            doc = tomlkit.parse(
                pyproject_path.read_text(encoding=c.Infra.Encoding.DEFAULT),
            )
        except (OSError, TOMLKitError):
            return {}
        direct_dep_names = (
            FlextInfraUtilitiesRefactorNamespace._extract_dep_names_from_doc(
                doc=doc,
            )
        )
        if not direct_dep_names:
            return {}
        chains: MutableMapping[str, MutableSequence[str]] = defaultdict(list)
        for dep_name in direct_dep_names:
            if not dep_name:
                continue
            if dep_name == "flext-core" or not dep_name.startswith("flext-"):
                continue
            stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
                project_name=dep_name,
            )
            if not stem:
                continue
            for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
                chains[family].append(f"{stem}{suffix}")
        return chains

    @staticmethod
    def _extract_dep_names_from_doc(
        *,
        doc: tomlkit.TOMLDocument,
    ) -> Sequence[str]:
        """Extract direct dependency project names from a pyproject.toml document.

        Reads both PEP 621 (``project.dependencies``) and Poetry
        (``tool.poetry.dependencies``) path deps and returns project names.
        """
        dep_names: t.Infra.StrSet = set()
        raw: t.Infra.TomlData = doc.unwrap()
        FlextInfraUtilitiesRefactorNamespace._collect_pep621_deps(
            raw=raw,
            dep_names=dep_names,
        )
        FlextInfraUtilitiesRefactorNamespace._collect_poetry_deps(
            raw=raw,
            dep_names=dep_names,
        )
        return sorted(dep_names)

    @staticmethod
    def _collect_pep621_deps(
        *,
        raw: t.Infra.TomlData,
        dep_names: t.Infra.StrSet,
    ) -> None:
        """Collect PEP 621 ``project.dependencies`` with ``@ file:`` path refs."""
        project_val: t.Infra.InfraValue = raw.get("project")
        if not FlextUtilities.is_mapping(project_val):
            return
        deps_val: t.Infra.InfraValue = project_val.get("dependencies")
        if not isinstance(deps_val, Sequence) or isinstance(deps_val, str):
            return
        for item_val in deps_val:
            if not isinstance(item_val, str):
                continue
            if " @ " not in item_val:
                continue
            _name, path_part = item_val.split(" @ ", 1)
            path_part = path_part.strip().removeprefix("file:").strip()
            path_part = path_part.removeprefix("./").strip()
            if path_part:
                dep_names.add(Path(path_part).name)

    @staticmethod
    def _collect_poetry_deps(
        *,
        raw: t.Infra.TomlData,
        dep_names: t.Infra.StrSet,
    ) -> None:
        """Collect Poetry ``tool.poetry.dependencies`` with ``path = "..."``."""
        tool_val: t.Infra.InfraValue = raw.get("tool")
        if not FlextUtilities.is_mapping(tool_val):
            return
        poetry_val: t.Infra.InfraValue = tool_val.get("poetry")
        if not FlextUtilities.is_mapping(poetry_val):
            return
        deps_tbl_val: t.Infra.InfraValue = poetry_val.get("dependencies")
        if not FlextUtilities.is_mapping(deps_tbl_val):
            return
        for dep_entry in deps_tbl_val.values():
            if not FlextUtilities.is_mapping(dep_entry):
                continue
            dep_path_val: t.Infra.InfraValue = dep_entry.get("path")
            dep_path_str = FlextUtilities.ensure_str(dep_path_val)
            if dep_path_str:
                dep_path_clean = dep_path_str.strip().removeprefix("./").strip()
                if dep_path_clean:
                    dep_names.add(Path(dep_path_clean).name)

    @staticmethod
    def _base_import_for_family(
        *,
        family: str,
        base_chains: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        """Generate import statements for the base classes of a family.

        When ``base_chains`` is provided, imports are derived from dep graph
        dependencies instead of hardcoding ``flext_core``.
        """
        if base_chains:
            chain = base_chains.get(family, [])
            if chain:
                lines: MutableSequence[str] = []
                for base_class_name in chain:
                    module = FlextInfraUtilitiesFormatting.class_name_to_module(
                        base_class_name,
                    )
                    lines.append(f"from {module} import {base_class_name}")
                return "\n".join(lines)
        class_name = f"Flext{c.Infra.FAMILY_SUFFIXES.get(family, 'Utilities')}"
        return f"from flext_core import {class_name}"

    @staticmethod
    def _base_class_for_family(
        *,
        family: str,
        base_chains: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        """Return comma-separated base class names for a family."""
        if base_chains:
            chain = base_chains.get(family, [])
            if chain:
                return ", ".join(chain)
        return f"Flext{c.Infra.FAMILY_SUFFIXES.get(family, 'Utilities')}"

    @staticmethod
    def _write_missing_facade_file(
        *,
        file_path: Path,
        family: str,
        class_name: str,
        base_chains: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        alias = family
        import_stmt = FlextInfraUtilitiesRefactorNamespace._base_import_for_family(
            family=family,
            base_chains=base_chains,
        )
        base_class = FlextInfraUtilitiesRefactorNamespace._base_class_for_family(
            family=family,
            base_chains=base_chains,
        )
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

    @staticmethod
    def _canonical_target_file(
        *,
        project_root: Path,
        source_file: Path,
        filename: str,
    ) -> Path:
        """Resolve the canonical target file for a given filename in a project."""
        parts = source_file.parts
        if "src" in parts:
            src_index = parts.index("src")
            if src_index + 1 < len(parts):
                package_name = parts[src_index + 1]
                return (
                    project_root
                    / c.Infra.Paths.DEFAULT_SRC_DIR
                    / package_name
                    / filename
                )
        return source_file.parent / filename

    @staticmethod
    def _append_typing_alias_blocks(
        *,
        target_file: Path,
        blocks: t.StrSequence,
    ) -> None:
        if not blocks:
            return
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else ""
        )
        updated = target_source
        if c.Infra.SourceCode.FUTURE_ANNOTATIONS not in updated:
            updated = "from __future__ import annotations\n\n" + updated.lstrip("\n")
        merged_blocks = "\n\n".join(blocks)
        updated = updated.rstrip() + "\n\n" + merged_blocks + "\n"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        _ = target_file.write_text(updated, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def _is_ast_protocol_class(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                return True
            if isinstance(base, ast.Subscript):
                value = base.value
                if isinstance(value, ast.Name) and value.id == "Protocol":
                    return True
                if isinstance(value, ast.Attribute) and value.attr == "Protocol":
                    return True
        return False

    @staticmethod
    def _rewrite_moved_protocol_imports(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        protocol_moves: Sequence[
            t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]
        ],
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

        source_target_names: MutableSequence[
            t.Infra.Triple[str, str, t.Infra.StrSet]
        ] = []
        for source_file, target_file, moved_name_seq in protocol_moves:
            source_module = _module_path(source_file)
            target_module = _module_path(target_file)
            if not source_module or not target_module or source_module == target_module:
                continue
            source_target_names.append(
                (source_module, target_module, set(moved_name_seq)),
            )
        if not source_target_names:
            return
        for py_file in py_files:
            FlextInfraUtilitiesRefactorNamespace._rewrite_protocol_imports_in_file(
                py_file=py_file,
                source_target_names=source_target_names,
            )

    @staticmethod
    def _rewrite_protocol_imports_in_file(
        *,
        py_file: Path,
        source_target_names: Sequence[t.Infra.Triple[str, str, t.Infra.StrSet]],
    ) -> None:
        """Rewrite moved protocol imports in a single file."""
        parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
            py_file,
        )
        if parsed is None:
            return
        new_lines = parsed.source.splitlines(keepends=True)
        changed = False
        for stmt in parsed.tree.body:
            if not isinstance(stmt, ast.ImportFrom):
                continue
            if stmt.module is None:
                continue
            rewritten = FlextInfraUtilitiesRefactorNamespace._try_rewrite_import_stmt(
                stmt=stmt,
                new_lines=new_lines,
                source_target_names=source_target_names,
            )
            if rewritten:
                changed = True
        if changed:
            _ = py_file.write_text(
                "".join(new_lines),
                encoding=c.Infra.Encoding.DEFAULT,
            )

    @staticmethod
    def _try_rewrite_import_stmt(
        *,
        stmt: ast.ImportFrom,
        new_lines: MutableSequence[str],
        source_target_names: Sequence[t.Infra.Triple[str, str, t.Infra.StrSet]],
    ) -> bool:
        """Try to rewrite a single import statement. Returns True if rewritten."""
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
            return True
        return False

    @staticmethod
    def _remove_line_ranges_and_write(
        *,
        source: str,
        source_file: Path,
        remove_ranges: Sequence[t.Infra.IntPair],
    ) -> None:
        """Remove specified line ranges from source and write back to file."""
        source_lines = source.splitlines()
        filtered_lines: MutableSequence[str] = []
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
    def _move_protocol_classes_to_canonical_file(
        *,
        project_root: Path,
        source_file: Path,
        protocol_names: t.Infra.StrSet,
    ) -> t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]] | None:
        parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
            source_file,
        )
        if parsed is None:
            return None
        source, tree = parsed.source, parsed.tree
        class_nodes: MutableSequence[ast.ClassDef] = []
        remove_ranges: MutableSequence[t.Infra.IntPair] = []
        blocks: MutableSequence[str] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name not in protocol_names:
                continue
            if not FlextInfraUtilitiesRefactorNamespace._is_ast_protocol_class(
                stmt,
            ):
                continue
            if stmt.end_lineno is None:
                continue
            block = FlextInfraUtilitiesRefactorNamespace._extract_source_block(
                source=source,
                node=stmt,
            )
            class_nodes.append(stmt)
            remove_ranges.append((stmt.lineno, stmt.end_lineno))
            blocks.append(block)
        if not class_nodes:
            return None
        target_file = FlextInfraUtilitiesRefactorNamespace._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename="protocols.py",
        )
        FlextInfraUtilitiesRefactorNamespace._append_protocol_blocks(
            project_root=project_root,
            target_file=target_file,
            blocks=blocks,
        )
        FlextInfraUtilitiesRefactorNamespace._remove_line_ranges_and_write(
            source=source,
            source_file=source_file,
            remove_ranges=remove_ranges,
        )
        moved_names = tuple(sorted({node.name for node in class_nodes}))
        return (source_file, target_file, moved_names)

    @staticmethod
    def _move_typing_aliases_to_canonical_file(
        *,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
            source_file,
            stage="manual-typing-rewrite",
            parse_failures=parse_failures,
        )
        if parsed is None:
            return
        source, tree = parsed.source, parsed.tree
        remove_ranges: MutableSequence[t.Infra.IntPair] = []
        blocks: MutableSequence[str] = []
        for stmt in tree.body:
            matched = FlextInfraUtilitiesRefactorNamespace._match_typing_alias(
                stmt,
                source,
                alias_names,
            )
            if matched is not None:
                alias_end, block = matched
                remove_ranges.append((stmt.lineno, alias_end))
                blocks.append(block)
        if not blocks:
            return
        target_file = FlextInfraUtilitiesRefactorNamespace._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename="typings.py",
        )
        FlextInfraUtilitiesRefactorNamespace._append_typing_alias_blocks(
            target_file=target_file,
            blocks=blocks,
        )
        FlextInfraUtilitiesRefactorNamespace._remove_line_ranges_and_write(
            source=source,
            source_file=source_file,
            remove_ranges=remove_ranges,
        )

    @staticmethod
    def _extract_source_block(*, source: str, node: ast.stmt) -> str:
        """Extract source text for an AST node, with fallback to line slicing."""
        block = ast.get_source_segment(source, node)
        if block is None:
            lines = source.splitlines()
            block = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        return block.strip("\n")

    @staticmethod
    def _match_typing_alias(
        stmt: ast.stmt,
        source: str,
        alias_names: t.Infra.StrSet,
    ) -> tuple[int, str] | None:
        """Match a PEP 695 or TypeAlias stmt. Returns (end_lineno, block) or None."""
        if isinstance(stmt, ast.TypeAlias):
            if stmt.name.id not in alias_names or stmt.end_lineno is None:
                return None
            block = FlextInfraUtilitiesRefactorNamespace._extract_source_block(
                source=source,
                node=stmt,
            )
            return (stmt.end_lineno, block)
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            if stmt.target.id not in alias_names or stmt.end_lineno is None:
                return None
            annotation_src = ast.get_source_segment(source, stmt.annotation) or ""
            if "TypeAlias" not in annotation_src:
                return None
            block = FlextInfraUtilitiesRefactorNamespace._extract_source_block(
                source=source,
                node=stmt,
            )
            return (stmt.end_lineno, block)
        return None

    @staticmethod
    def _append_protocol_blocks(
        *,
        project_root: Path,
        target_file: Path,
        blocks: t.StrSequence,
    ) -> None:
        if not blocks:
            return
        project_name = project_root.name
        class_stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        protocols_class = f"{class_stem}Protocols"
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else ""
        )
        updated = target_source
        if c.Infra.SourceCode.FUTURE_ANNOTATIONS not in updated:
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
    def ensure_missing_facades(
        *,
        project_root: Path,
        project_name: str,
        facade_statuses: Sequence[m.Infra.FacadeStatus],
        workspace_root: Path | None = None,
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
        if not package_dirs:
            return
        primary_package = package_dirs[0]
        stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        base_chains: Mapping[str, Sequence[str]] | None = None
        if workspace_root is not None:
            chains = FlextInfraUtilitiesRefactorNamespace.build_expected_base_chains(
                project_root=project_root,
            )
            if chains:
                base_chains = chains
        for status in facade_statuses:
            if status.exists:
                continue
            suffix = c.Infra.FAMILY_SUFFIXES[status.family]
            class_name = f"{stem}{suffix}"
            file_name = c.Infra.FAMILY_FILES.get(
                status.family,
                "utilities.py",
            ).lstrip("*")
            target_path = primary_package / file_name
            if target_path.exists():
                FlextInfraUtilitiesRefactorNamespace._patch_existing_facade_file(
                    target_path=target_path,
                    family=status.family,
                    class_name=class_name,
                    base_chains=base_chains,
                )
                continue
            FlextInfraUtilitiesRefactorNamespace._write_missing_facade_file(
                file_path=target_path,
                family=status.family,
                class_name=class_name,
                base_chains=base_chains,
            )

    @staticmethod
    def _patch_existing_facade_file(
        *,
        target_path: Path,
        family: str,
        class_name: str,
        base_chains: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        """Append missing class def and alias to an existing facade file."""
        content = target_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        mutated = False
        class_signature = f"class {class_name}("
        if class_signature not in content and f"class {class_name}:" not in content:
            base_class = FlextInfraUtilitiesRefactorNamespace._base_class_for_family(
                family=family,
                base_chains=base_chains,
            )
            snippet = f"\n\nclass {class_name}({base_class}):\n    pass\n"
            content = content.rstrip() + snippet
            mutated = True
        alias_line = f"{family} = {class_name}"
        if alias_line not in content:
            content = content.rstrip() + f"\n\n{alias_line}\n"
            mutated = True
        if mutated:
            _ = target_path.write_text(
                content,
                encoding=c.Infra.Encoding.DEFAULT,
            )

    @staticmethod
    def rewrite_import_violations(
        *,
        py_files: Sequence[Path],
        project_package: str,
    ) -> None:
        """Normalize all imports: remove deep/submodule imports, keep canonical.

        Removes:
        - Imports from private submodules (``from pkg._sub import X``)
        - Imports of aliases/classes from submodule files (``from pkg.models import m``)
        - Duplicate/renamed alias imports (``from pkg.models import m as mm``)

        Skips ``__init__.py`` files and facade declaration files.
        """
        for file_path in py_files:
            if file_path.name == "__init__.py":
                continue
            FlextInfraUtilitiesRefactorNamespace._normalize_file_imports(
                file_path=file_path,
                project_package=project_package,
            )

    @staticmethod
    def _normalize_file_imports(
        *,
        file_path: Path,
        project_package: str,
    ) -> None:
        """Apply import normalization to a single file via CST rewrite."""
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return
        is_facade = FlextInfraUtilitiesRefactorNamespace._is_facade_file(
            tree=tree,
        )
        transformer = _NamespaceImportCleaner(
            project_package=project_package,
            is_facade=is_facade,
        )
        new_tree = tree.visit(transformer)
        if not transformer.changed:
            return
        file_path.write_text(new_tree.code, encoding=c.Infra.Encoding.DEFAULT)
        FlextInfraUtilitiesFormatting.run_ruff_fix(file_path)

    @staticmethod
    def _is_facade_file(
        *,
        tree: cst.Module,
    ) -> bool:
        """Check if a CST module is a facade declaration file."""
        return any(
            isinstance(item, cst.Assign)
            and isinstance(item.value, cst.Name)
            and any(
                isinstance(target.target, cst.Name)
                and len(target.target.value) <= _MAX_ALIAS_NAME_LEN
                for target in item.targets
            )
            for stmt in tree.body
            if isinstance(stmt, cst.SimpleStatementLine)
            for item in stmt.body
        )

    @staticmethod
    def rewrite_mro_completeness_violations(
        *,
        violations: Sequence[m.Infra.MROCompletenessViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite facade class headers adding missing MRO bases and imports.

        Uses libcst CSTTransformer for class header modification (robust against
        multi-line headers and unusual formatting), and ast for import injection.
        """
        violations_by_file: Mapping[
            Path,
            MutableSequence[m.Infra.MROCompletenessViolation],
        ] = defaultdict(list)
        for violation in violations:
            violations_by_file[Path(violation.file)].append(violation)
        core_bases = frozenset(
            f"Flext{suffix}" for suffix in c.Infra.FAMILY_SUFFIXES.values()
        )
        for file_path, file_violations in violations_by_file.items():
            missing_by_facade: Mapping[str, t.Infra.StrSet] = defaultdict(set)
            for violation in file_violations:
                missing_by_facade[violation.facade_class].add(violation.missing_base)
            FlextInfraUtilitiesRefactorNamespace._rewrite_mro_in_file(
                file_path=file_path,
                missing_by_facade=missing_by_facade,
                core_bases=core_bases,
                parse_failures=parse_failures,
            )

    @staticmethod
    def _rewrite_mro_in_file(
        *,
        file_path: Path,
        missing_by_facade: Mapping[str, t.Infra.StrSet],
        core_bases: frozenset[str],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite MRO bases and inject imports for a single facade file."""
        cst_tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if cst_tree is None:
            return
        rewriter = _MROBaseRewriter(
            missing_by_facade=missing_by_facade,
            core_bases=core_bases,
        )
        modified_tree = cst_tree.visit(rewriter)
        if not rewriter.changed:
            return
        lines = modified_tree.code.splitlines(keepends=True)
        new_imports = FlextInfraUtilitiesRefactorNamespace._build_missing_imports(
            file_path=file_path,
            new_bases=rewriter.new_bases,
            parse_failures=parse_failures,
        )
        if new_imports:
            parsed_for_insert = FlextInfraUtilitiesRefactorLoader.load_python_module(
                file_path,
                stage="mro-completeness-imports",
                parse_failures=parse_failures,
            )
            insert_line = 0
            if parsed_for_insert is not None:
                for imp_stmt in parsed_for_insert.tree.body:
                    if isinstance(imp_stmt, (ast.Import, ast.ImportFrom)):
                        insert_line = imp_stmt.end_lineno or imp_stmt.lineno
            for import_line in reversed(new_imports):
                lines.insert(insert_line, import_line)
        _ = file_path.write_text(
            "".join(lines),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        FlextInfraUtilitiesFormatting.run_ruff_fix(
            file_path,
            include_format=True,
            quiet=True,
        )

    @staticmethod
    def _build_missing_imports(
        *,
        file_path: Path,
        new_bases: t.Infra.StrSet,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> Sequence[str]:
        """Build import lines for bases not already imported in the file."""
        parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
            file_path,
            stage="mro-completeness-imports",
            parse_failures=parse_failures,
        )
        existing_imports: t.Infra.StrSet = set()
        if parsed is not None:
            for stmt in parsed.tree.body:
                if isinstance(stmt, ast.ImportFrom) and stmt.names:
                    existing_imports.update(alias.name for alias in stmt.names)
        imports: MutableSequence[str] = []
        for base_name in sorted(new_bases):
            if base_name in existing_imports:
                continue
            module = FlextInfraUtilitiesFormatting.class_name_to_module(
                base_name,
            )
            imports.append(f"from {module} import {base_name}\n")
        return imports

    @staticmethod
    def rewrite_runtime_alias_violations(*, py_files: Sequence[Path]) -> None:
        """Rewrite runtime alias statements to match expected patterns."""
        for file_path in py_files:
            expected = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(
                file_path.name,
            )
            if expected is None:
                continue
            alias_name, expected_suffix = expected
            parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
                file_path,
            )
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
    def rewrite_missing_future_annotations(
        *,
        py_files: Sequence[Path],
    ) -> None:
        """Add missing future annotations imports to source files."""
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
            insert_idx = FlextInfraUtilitiesRefactorNamespace._find_future_insert_index(
                lines=lines,
            )
            new_lines = (
                lines[:insert_idx]
                + ["", c.Infra.SourceCode.FUTURE_ANNOTATIONS, ""]
                + lines[insert_idx:]
            )
            _ = file_path.write_text(
                "\n".join(new_lines).rstrip() + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )

    @staticmethod
    def _find_future_insert_index(*, lines: Sequence[str]) -> int:
        """Find the line index after shebang, encoding, and module docstring."""
        insert_idx = 0
        if lines[0].startswith("#!"):
            insert_idx = 1
        if insert_idx < len(lines) and re.match(
            r"^#.*coding[:=]",
            lines[insert_idx],
        ):
            insert_idx += 1
        if insert_idx >= len(lines):
            return insert_idx
        line_text = lines[insert_idx]
        if not line_text.startswith(('"""', "'''")):
            return insert_idx
        docstring_single_line_quote_count = 2
        quote = line_text[:3]
        if line_text.count(quote) >= docstring_single_line_quote_count:
            return insert_idx + 1
        for idx in range(insert_idx + 1, len(lines)):
            if quote in lines[idx]:
                return idx + 1
        return insert_idx

    @staticmethod
    def rewrite_manual_protocol_violations(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        violations: Sequence[m.Infra.ManualProtocolViolation],
    ) -> None:
        """Move manual protocol definitions to their canonical files."""
        grouped_names: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped_names[Path(violation.file)].add(violation.name)
        protocol_moves: MutableSequence[
            t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]
        ] = []
        for source_file, protocol_names in grouped_names.items():
            move_result = FlextInfraUtilitiesRefactorNamespace._move_protocol_classes_to_canonical_file(
                project_root=project_root,
                source_file=source_file,
                protocol_names=protocol_names,
            )
            if move_result is None:
                continue
            protocol_moves.append(move_result)
        if protocol_moves:
            FlextInfraUtilitiesRefactorNamespace._rewrite_moved_protocol_imports(
                project_root=project_root,
                py_files=py_files,
                protocol_moves=protocol_moves,
            )

    @staticmethod
    def rewrite_manual_typing_alias_violations(
        *,
        project_root: Path,
        violations: Sequence[m.Infra.ManualTypingAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        """Move manual typing aliases to their canonical files."""
        grouped_names: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped_names[Path(violation.file)].add(violation.name)
        for source_file, alias_names in grouped_names.items():
            FlextInfraUtilitiesRefactorNamespace._move_typing_aliases_to_canonical_file(
                project_root=project_root,
                source_file=source_file,
                alias_names=alias_names,
                parse_failures=parse_failures,
            )

    @staticmethod
    def rewrite_compatibility_alias_violations(
        *,
        violations: Sequence[m.Infra.CompatibilityAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        """Rewrite compatibility alias violations in source files."""
        grouped: Mapping[Path, MutableMapping[str, str]] = defaultdict(dict)
        for violation in violations:
            grouped[Path(violation.file)][violation.alias_name] = violation.target_name
        for file_path, alias_map in grouped.items():
            FlextInfraUtilitiesRefactorNamespace._rewrite_compat_aliases_in_file(
                file_path=file_path,
                alias_map=alias_map,
                parse_failures=parse_failures,
            )

    @staticmethod
    def _rewrite_compat_aliases_in_file(
        *,
        file_path: Path,
        alias_map: Mapping[str, str],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        """Remove alias assignments and replace alias usages in a single file."""
        parsed = FlextInfraUtilitiesRefactorLoader.load_python_module(
            file_path,
            stage="compatibility-alias-rewrite",
            parse_failures=parse_failures,
        )
        if parsed is None:
            return
        source = parsed.source
        assignment_lines = (
            FlextInfraUtilitiesRefactorNamespace._find_alias_assignment_lines(
                tree=parsed.tree,
                alias_map=alias_map,
            )
        )
        if not assignment_lines:
            return
        kept_source = "".join(
            line
            for idx, line in enumerate(source.splitlines(keepends=True), start=1)
            if idx not in assignment_lines
        )
        rewritten = FlextInfraUtilitiesRefactorNamespace._apply_token_replacements(
            source=kept_source,
            alias_map=alias_map,
        )
        if rewritten != source:
            _ = file_path.write_text(rewritten, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def _find_alias_assignment_lines(
        *,
        tree: ast.Module,
        alias_map: Mapping[str, str],
    ) -> t.Infra.IntSet:
        """Find line numbers of ``AliasName = TargetName`` assignments to remove."""
        assignment_lines: t.Infra.IntSet = set()
        for stmt in tree.body:
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
        return assignment_lines

    @staticmethod
    def _apply_token_replacements(
        *,
        source: str,
        alias_map: Mapping[str, str],
    ) -> str:
        """Replace alias name tokens in source with their target names."""
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


class _MROBaseRewriter(cst.CSTTransformer):
    """CST transformer that adds missing MRO bases to facade class definitions."""

    def __init__(
        self,
        *,
        missing_by_facade: Mapping[str, t.Infra.StrSet],
        core_bases: frozenset[str],
    ) -> None:
        self._missing_by_facade = missing_by_facade
        self._core_bases = core_bases
        self.changed = False
        self.new_bases: t.Infra.StrSet = set()

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        class_name = updated_node.name.value
        missing = self._missing_by_facade.get(class_name)
        if not missing:
            return updated_node
        current_names = [
            FlextInfraUtilitiesParsing.cst_extract_base_name(arg.value)
            for arg in updated_node.bases
        ]
        proposed = list(current_names) + [
            b for b in sorted(missing) if b not in current_names
        ]
        # Remove core bases when dep-graph bases supersede them
        if any(b in self._core_bases for b in missing):
            proposed = [b for b in proposed if b not in self._core_bases]
        if proposed == current_names:
            return updated_node
        new_args: MutableSequence[cst.Arg] = []
        for i, name in enumerate(proposed):
            comma: cst.Comma | cst.MaybeSentinel = (
                cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
                if i < len(proposed) - 1
                else cst.MaybeSentinel.DEFAULT
            )
            new_args.append(cst.Arg(value=cst.Name(name), comma=comma))
        self.changed = True
        self.new_bases.update(set(proposed) - set(current_names))
        return updated_node.with_changes(bases=new_args)


_MAX_ALIAS_NAME_LEN: int = 2


class _NamespaceImportCleaner(cst.CSTTransformer):
    """CST transformer that removes deep/submodule imports for a project package."""

    def __init__(self, *, project_package: str, is_facade: bool) -> None:
        self._project_package = project_package
        self._is_facade = is_facade
        self.changed = False

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        is_private = self._should_clean_import(updated_node)
        if is_private is None:
            return updated_node
        if isinstance(updated_node.names, cst.ImportStar):
            self.changed = True
            return cst.RemovalSentinel.REMOVE
        return self._filter_import_aliases(
            updated_node=updated_node,
            is_private=is_private,
        )

    def _should_clean_import(
        self,
        node: cst.ImportFrom,
    ) -> bool | None:
        """Determine if an import should be cleaned. Returns None to skip."""
        module_name = FlextInfraUtilitiesParsing.cst_module_to_str(node.module)
        if not module_name or not module_name.startswith(self._project_package):
            return None
        if module_name == self._project_package:
            return None
        suffix = module_name[len(self._project_package) :]
        if not suffix.startswith("."):
            return None
        is_private = "._" in suffix
        if self._is_facade and not is_private:
            return None
        return is_private

    def _filter_import_aliases(
        self,
        *,
        updated_node: cst.ImportFrom,
        is_private: bool,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        """Filter import aliases, removing private/short ones."""
        names = updated_node.names
        if isinstance(names, cst.ImportStar):
            self.changed = True
            return cst.RemovalSentinel.REMOVE
        remaining: MutableSequence[cst.ImportAlias] = []
        for alias in names:
            name = (
                alias.name.value
                if isinstance(alias.name, cst.Name)
                else alias.name.attr.value
            )
            if alias.asname is not None:
                self.changed = True
                continue
            if is_private or len(name) <= _MAX_ALIAS_NAME_LEN:
                self.changed = True
                continue
            remaining.append(alias)
        if not remaining:
            self.changed = True
            return cst.RemovalSentinel.REMOVE
        if len(remaining) < len(names):
            self.changed = True
            cleaned = self._normalize_commas(remaining)
            return updated_node.with_changes(names=cleaned)
        return updated_node

    @staticmethod
    def _normalize_commas(
        aliases: Sequence[cst.ImportAlias],
    ) -> Sequence[cst.ImportAlias]:
        cleaned: MutableSequence[cst.ImportAlias] = []
        for idx, alias in enumerate(aliases):
            if idx < len(aliases) - 1:
                cleaned.append(
                    alias.with_changes(
                        comma=cst.Comma(
                            whitespace_after=cst.SimpleWhitespace(" "),
                        ),
                    ),
                )
            else:
                cleaned.append(
                    alias.with_changes(comma=cst.MaybeSentinel.DEFAULT),
                )
        return cleaned


__all__ = ["FlextInfraUtilitiesRefactorNamespace"]
