"""AST utility library for safe Python code transformations.

Provides stateless helper functions for parsing, analyzing, and generating
Python code using the ast module.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins as _builtins_module
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import FlextInfraUtilitiesParsing, FlextInfraUtilitiesRefactor, c, t


class FlextInfraUtilitiesCodegenTransforms:
    """Utility helpers for AST-based code transformations."""

    @staticmethod
    def find_insert_position(tree: ast.Module) -> int:
        """Find insertion point after module docstring/imports."""
        last_import_idx = 0
        for i, stmt in enumerate(tree.body):
            if isinstance(stmt, (ast.Import, ast.ImportFrom)) or (
                isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            ):
                last_import_idx = i + 1
        return last_import_idx

    @staticmethod
    def find_standalone_finals(tree: ast.Module) -> Sequence[ast.AnnAssign]:
        """Find module-level Final-annotated assignments.

        Returns all top-level ``X: Final = ...`` and ``X: Final[T] = ...``
        statements.  The caller decides whether to move them based on
        additional guards (private prefix, circular-import risk, etc.).
        """
        matches: MutableSequence[ast.AnnAssign] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.AnnAssign):
                continue
            if FlextInfraUtilitiesRefactor.is_final_annotation(
                annotation=stmt.annotation,
            ):
                matches.append(stmt)
        return matches

    @staticmethod
    def find_standalone_typealiases(tree: ast.Module) -> Sequence[ast.stmt]:
        """Find module-level TypeAlias declarations (old-style and PEP 695).

        Detects both ``X: TypeAlias = ...`` (ast.AnnAssign) and
        ``type X = ...`` (ast.TypeAlias, PEP 695 / Python 3.12+).
        """
        matches: MutableSequence[ast.stmt] = []
        for stmt in tree.body:
            # Old-style: X: TypeAlias = ...
            if isinstance(stmt, ast.AnnAssign):
                annotation = stmt.annotation
                if isinstance(annotation, ast.Name) and annotation.id == "TypeAlias":
                    matches.append(stmt)
                continue
            # PEP 695: type X = ...
            if isinstance(stmt, ast.TypeAlias):
                matches.append(stmt)
        return matches

    @staticmethod
    def find_standalone_typevars(tree: ast.Module) -> Sequence[ast.Assign]:
        """Find module-level TypeVar/ParamSpec/TypeVarTuple assignments.

        Detects ``X = TypeVar(...)``, ``P = ParamSpec(...)``, and
        ``Ts = TypeVarTuple(...)`` at module level.
        """
        typevar_names = {"TypeVar", "ParamSpec", "TypeVarTuple"}
        matches: MutableSequence[ast.Assign] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if not isinstance(stmt.value, ast.Call):
                continue
            func = stmt.value.func
            if (isinstance(func, ast.Name) and func.id in typevar_names) or (
                isinstance(func, ast.Attribute) and func.attr in typevar_names
            ):
                matches.append(stmt)
        return matches

    @staticmethod
    def generate_module_skeleton(
        class_name: str,
        base_class: str,
        docstring: str,
    ) -> str:
        """Generate a minimal base module file with correct imports."""
        pkg = "flext_tests" if base_class.startswith("FlextTests") else "flext_core"
        import_line = f"from {pkg} import {base_class}"
        return f'"""Module skeleton for {class_name}.\n\n{docstring}\n\nCopyright (c) 2025 FLEXT Team. All rights reserved.\nSPDX-License-Identifier: MIT\n"""\n\nfrom __future__ import annotations\n\n{import_line}\n\n\nclass {class_name}({base_class}):\n    """{docstring}"""\n'

    @staticmethod
    def get_node_name(node: ast.stmt) -> str:
        """Extract assignment target name from a statement.

        Handles ast.Assign, ast.AnnAssign, and ast.TypeAlias (PEP 695).
        """
        if isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                return target.id
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return node.target.id
        if isinstance(node, ast.TypeAlias):
            return node.name.id
        return ""

    @staticmethod
    def get_top_level_names_in_node(node: ast.stmt) -> frozenset[str]:
        """Collect all Name references used in a node."""
        names: t.Infra.StrSet = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
        return frozenset(names)

    @staticmethod
    def get_type_param_names(node: ast.stmt) -> frozenset[str]:
        """Extract locally-scoped type parameter names from a PEP 695 type alias.

        ``type X[T, *Ts, **P] = ...`` defines T, Ts, P as local type params.
        These names are part of the node itself and must NOT be treated as
        external dependencies when checking resolvability.
        """
        if not isinstance(node, ast.TypeAlias):
            return frozenset()
        names: t.Infra.StrSet = set()
        for tp in node.type_params:
            if isinstance(tp, (ast.TypeVar, ast.TypeVarTuple, ast.ParamSpec)):
                names.add(tp.name)
        return frozenset(names)

    @staticmethod
    def external_deps_for_node(node: ast.stmt) -> frozenset[str]:
        """Compute external name dependencies for a node (excluding self-name and type params)."""
        names_used = FlextInfraUtilitiesCodegenTransforms.get_top_level_names_in_node(
            node,
        )
        node_name = FlextInfraUtilitiesCodegenTransforms.get_node_name(node)
        type_params = FlextInfraUtilitiesCodegenTransforms.get_type_param_names(node)
        return frozenset(
            n for n in names_used if n != node_name and n not in type_params
        )

    @staticmethod
    def collect_available_names(
        tree: ast.Module,
        *,
        include_builtins: bool = False,
        include_definitions: bool = False,
    ) -> t.Infra.StrSet:
        """Collect names available in a module (imports and optionally definitions)."""
        available: t.Infra.StrSet = set()
        if include_builtins:
            available.update(dir(_builtins_module))
        for stmt in tree.body:
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    imported_name = alias.asname or alias.name
                    available.add(imported_name.split(".")[0])
            elif isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    imported_name = alias.asname or alias.name
                    if imported_name != "*":
                        available.add(imported_name)
            elif include_definitions:
                name = FlextInfraUtilitiesCodegenTransforms.get_node_name(stmt)
                if name:
                    available.add(name)
        return available

    @staticmethod
    def collect_source_import_map(tree: ast.Module) -> MutableMapping[str, ast.stmt]:
        """Build a mapping of name -> import statement from a module's imports."""
        source_imports: MutableMapping[str, ast.stmt] = {}
        for stmt in tree.body:
            match stmt:
                case ast.Import():
                    for alias in stmt.names:
                        imported_name = alias.asname or alias.name
                        top_name = imported_name.split(".")[0]
                        source_imports[top_name] = stmt
                case ast.ImportFrom():
                    for alias in stmt.names:
                        imported_name = alias.asname or alias.name
                        if imported_name != "*":
                            source_imports[imported_name] = stmt
                case _:
                    pass
        return source_imports

    @staticmethod
    def all_deps_resolvable(node: ast.stmt, target_tree: ast.Module) -> bool:
        """Check if all names used in node are available in the target module.

        Called AFTER copy_required_imports to verify the copy succeeded.
        A name is available if it's imported or defined in the target module.
        """
        names_used = FlextInfraUtilitiesCodegenTransforms.external_deps_for_node(node)
        if not names_used:
            return True
        available = FlextInfraUtilitiesCodegenTransforms.collect_available_names(
            target_tree,
            include_builtins=True,
            include_definitions=True,
        )
        return all(n in available for n in names_used)

    @staticmethod
    def copy_required_imports(
        node: ast.stmt,
        source_tree: ast.Module,
        target_tree: ast.Module,
    ) -> None:
        """Copy imports needed by node from source_tree to target_tree.

        Mutates target_tree for analysis accumulation only - the tree is
        never written to disk via ast.unparse.
        """
        cls_ref = FlextInfraUtilitiesCodegenTransforms
        names_used = cls_ref.external_deps_for_node(node)
        if not names_used:
            return
        source_imports = cls_ref.collect_source_import_map(source_tree)
        target_available = cls_ref.collect_available_names(target_tree)
        seen_modules: t.Infra.StrSet = set()
        imports_to_add: MutableSequence[ast.stmt] = []
        for name in sorted(names_used):
            if name in target_available:
                continue
            if name not in source_imports:
                continue
            import_stmt = source_imports[name]
            import_key = ast.unparse(import_stmt)
            if import_key in seen_modules:
                continue
            seen_modules.add(import_key)
            imports_to_add.append(import_stmt)
        if not imports_to_add:
            return
        last_import_idx = cls_ref.find_insert_position(target_tree)
        for i, imp in enumerate(imports_to_add):
            target_tree.body.insert(last_import_idx + i, imp)

    @staticmethod
    def find_missing_deps(
        node: ast.stmt,
        target_tree: ast.Module,
    ) -> frozenset[str]:
        """Find names required by node that are not available in target_tree."""
        names_used = FlextInfraUtilitiesCodegenTransforms.external_deps_for_node(node)
        if not names_used:
            return frozenset()
        target_available = FlextInfraUtilitiesCodegenTransforms.collect_available_names(
            target_tree,
            include_builtins=True,
            include_definitions=True,
        )
        return names_used - target_available

    @staticmethod
    def has_first_party_provider(
        missing: frozenset[str],
        source_tree: ast.Module,
    ) -> bool:
        """Check if any missing names come from a first-party (flext_*) import."""
        for stmt in source_tree.body:
            if isinstance(stmt, ast.ImportFrom) and stmt.module:
                if stmt.module.startswith("flext"):
                    for alias in stmt.names:
                        imported = alias.asname or alias.name
                        if imported in missing:
                            return True
            elif isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    top = (alias.asname or alias.name).split(".")[0]
                    if top.startswith("flext") and top in missing:
                        return True
        return False

    @staticmethod
    def needs_first_party_import(
        node: ast.stmt,
        source_tree: ast.Module,
        target_tree: ast.Module,
    ) -> bool:
        """Check if moving node to target would require a first-party import.

        First-party imports (from flext_*) into typings.py create circular
        import chains because typings.py is imported by result.py, runtime.py,
        and other foundational modules. If the node depends on names that come
        from first-party imports and those names are NOT already available in
        the target module, moving the node is unsafe.
        """
        missing = FlextInfraUtilitiesCodegenTransforms.find_missing_deps(
            node,
            target_tree,
        )
        if not missing:
            return False
        return FlextInfraUtilitiesCodegenTransforms.has_first_party_provider(
            missing,
            source_tree,
        )

    @staticmethod
    def names_provided_by_import(stmt: ast.Import | ast.ImportFrom) -> t.Infra.StrSet:
        """Return the set of names that an import statement provides."""
        provided: t.Infra.StrSet = set()
        if isinstance(stmt, ast.Import):
            provided.update(
                (alias.asname or alias.name).split(".")[0] for alias in stmt.names
            )
        else:
            for alias in stmt.names:
                imported = alias.asname or alias.name
                if imported != "*":
                    provided.add(imported)
        return provided

    @staticmethod
    def collect_import_texts_for_nodes(
        nodes: Sequence[ast.stmt],
        source_lines: t.StrSequence,
        source_tree: ast.Module,
        target_text: str,
    ) -> t.StrSequence:
        """Collect import text lines from source needed by moved nodes.

        Returns import statement strings that should be added to the target
        file. Skips imports already present in the target text.
        """
        all_names: t.Infra.StrSet = set()
        for node in nodes:
            all_names.update(
                FlextInfraUtilitiesCodegenTransforms.external_deps_for_node(node),
            )
        if not all_names:
            return []
        import_texts: MutableSequence[str] = []
        seen: t.Infra.StrSet = set()
        for stmt in source_tree.body:
            if not isinstance(stmt, (ast.Import, ast.ImportFrom)):
                continue
            provided = FlextInfraUtilitiesCodegenTransforms.names_provided_by_import(
                stmt,
            )
            if not (provided & all_names):
                continue
            start = stmt.lineno
            end = stmt.end_lineno or start
            text = "\n".join(source_lines[start - 1 : end]).strip()
            if text not in seen and text not in target_text:
                seen.add(text)
                import_texts.append(text)
        return import_texts

    @staticmethod
    def find_all_assignment(
        tree: ast.Module,
    ) -> tuple[ast.Assign | None, t.StrSequence]:
        """Find the ``__all__`` assignment and extract its literal string entries."""
        for stmt in tree.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name) or target.id != "__all__":
                continue
            if not isinstance(stmt.value, (ast.List, ast.Tuple)):
                continue
            names: MutableSequence[str] = []
            is_literal_list = True
            for element in stmt.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    names.append(element.value)
                    continue
                is_literal_list = False
                break
            if not is_literal_list:
                continue
            return stmt, names
        return None, []

    @staticmethod
    def collect_all_defined_names(tree: ast.Module) -> t.Infra.StrSet:
        """Collect all top-level defined/imported names in a module (for __all__ pruning)."""
        available: t.Infra.StrSet = set()
        for stmt in tree.body:
            if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                available.add(stmt.name)
                continue
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    imported = alias.asname or alias.name
                    available.add(imported.split(".")[0])
                continue
            if isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    imported = alias.asname or alias.name
                    if imported != "*":
                        available.add(imported)
                continue
            found_name = FlextInfraUtilitiesCodegenTransforms.get_node_name(stmt)
            if found_name:
                available.add(found_name)
        return available

    @staticmethod
    def render_all_block(filtered: t.StrSequence) -> str:
        """Render the ``__all__`` assignment text from filtered names."""
        if not filtered:
            return "__all__ = []"
        return (
            "__all__ = [\n" + "\n".join(f'    "{name}",' for name in filtered) + "\n]"
        )

    @staticmethod
    def prune_stale_all_assignment(*, path: Path) -> bool:
        """Remove stale entries from __all__ that no longer exist in the module."""
        try:
            source = path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return False
        tree = FlextInfraUtilitiesParsing.parse_ast_from_source(source)
        if tree is None:
            return False
        assignment, exports = FlextInfraUtilitiesCodegenTransforms.find_all_assignment(
            tree,
        )
        if assignment is None or not exports:
            return False
        available = FlextInfraUtilitiesCodegenTransforms.collect_all_defined_names(tree)
        filtered = [
            name for name in exports if name in available or name.startswith("__")
        ]
        if filtered == exports:
            return False
        block = FlextInfraUtilitiesCodegenTransforms.render_all_block(filtered)
        lines = source.splitlines()
        if assignment.lineno <= 0 or assignment.end_lineno is None:
            return False
        start = assignment.lineno - 1
        end = assignment.end_lineno
        updated_lines = [*lines[:start], block, *lines[end:]]
        updated = "\n".join(updated_lines)
        if source.endswith("\n"):
            updated += "\n"
        if updated == source:
            return False
        path.write_text(updated, encoding=c.Infra.Encoding.DEFAULT)
        return True

    @staticmethod
    def name_exists_in_module(name: str, tree: ast.Module) -> bool:
        """Check if a top-level name is already defined in a module.

        Handles ast.Assign, ast.AnnAssign, and ast.TypeAlias (PEP 695).
        """
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return True
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and (stmt.target.id == name)
            ):
                return True
            if isinstance(stmt, ast.TypeAlias) and stmt.name.id == name:
                return True
        return False


__all__ = ["FlextInfraUtilitiesCodegenTransforms"]
