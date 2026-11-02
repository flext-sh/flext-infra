"""Normalize legacy Pydantic syntax out of protocol source modules.

This module deliberately imports only the Python standard library so it can repair
``src/<package>/_protocols`` before importing the package that owns those sources.

Run it before the public CLI when legacy protocol source prevents package import::

    python src/flext_infra/_protocols_bootstrap.py /path/to/flext-infra
"""

from __future__ import annotations

import argparse
import ast
import itertools
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _Patch:
    """One non-overlapping source replacement."""

    start: int
    end: int
    replacement: str


def _is_protocol_base(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Protocol") or (
        isinstance(node, ast.Attribute) and node.attr == "Protocol"
    )


def _is_pydantic_field(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "m"
        and node.func.attr == "Field"
    )


def _is_annotated(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Annotated") or (
        isinstance(node, ast.Attribute) and node.attr == "Annotated"
    )


def _line_offsets(source: str) -> tuple[int, ...]:
    offsets = [0]
    for index, character in enumerate(source):
        if character == "\n":
            offsets.append(index + 1)
    return tuple(offsets)


def _span(node: ast.AST, offsets: Sequence[int]) -> tuple[int, int]:
    if node.lineno is None or node.col_offset is None:
        msg = "AST node has no source location"
        raise ValueError(msg)
    if node.end_lineno is None or node.end_col_offset is None:
        msg = "AST node has no source end location"
        raise ValueError(msg)
    return (
        offsets[node.lineno - 1] + node.col_offset,
        offsets[node.end_lineno - 1] + node.end_col_offset,
    )


class _PydanticAnnotatedMetadataRemover(ast.NodeTransformer):
    """Remove only ``m.Field`` metadata from every nested ``Annotated`` form."""

    changed: bool

    def __init__(self) -> None:
        self.changed = False

    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        node = self.generic_visit(node)
        if not (
            isinstance(node, ast.Subscript)
            and _is_annotated(node.value)
            and isinstance(node.slice, ast.Tuple)
            and node.slice.elts
        ):
            return node
        value, *metadata = node.slice.elts
        retained = [item for item in metadata if not _is_pydantic_field(item)]
        if len(retained) == len(metadata):
            return node
        self.changed = True
        if not retained:
            return ast.copy_location(value, node)
        return ast.copy_location(
            ast.Subscript(
                value=node.value,
                slice=ast.Tuple(elts=[value, *retained], ctx=ast.Load()),
                ctx=ast.Load(),
            ),
            node,
        )


def _normalized_annotation(annotation: ast.expr) -> ast.expr | None:
    remover = _PydanticAnnotatedMetadataRemover()
    normalized = remover.visit(
        ast.fix_missing_locations(ast.parse(ast.unparse(annotation), mode="eval").body)
    )
    return normalized if remover.changed else None


def _protocol_classes(tree: ast.Module) -> Iterable[ast.ClassDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            _is_protocol_base(base) for base in node.bases
        ):
            yield node


def _has_runtime_checkable(node: ast.ClassDef) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "runtime_checkable"
        for decorator in node.decorator_list
    )


def _runtime_checkable_import(tree: ast.Module) -> ast.ImportFrom | None:
    return next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "typing"
            and any(alias.name == "runtime_checkable" for alias in node.names)
        ),
        None,
    )


def _import_insertion_offset(tree: ast.Module, offsets: Sequence[int]) -> int:
    future_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "__future__"
    ]
    if future_imports:
        return _span(future_imports[-1], offsets)[1]
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        return _span(tree.body[0], offsets)[1]
    return 0


def _remove_unused_m_imports(tree: ast.Module, offsets: Sequence[int]) -> list[_Patch]:
    if any(isinstance(node, ast.Name) and node.id == "m" for node in ast.walk(tree)):
        return []
    patches: list[_Patch] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            retained = [
                alias for alias in node.names if (alias.asname or alias.name) != "m"
            ]
        else:
            continue
        if len(retained) == len(node.names):
            continue
        start, end = _span(node, offsets)
        replacement = (
            ""
            if not retained
            else ast.unparse(
                ast.Import(names=retained)
                if isinstance(node, ast.Import)
                else ast.ImportFrom(
                    module=node.module, names=retained, level=node.level
                )
            )
        )
        patches.append(_Patch(start, end, replacement))
    return patches


def normalize_protocol_source(source: str, *, filename: str = "<protocol>") -> str:
    """Return source with Pydantic field syntax removed from ``Protocol`` bodies."""
    tree = ast.parse(source, filename=filename)
    offsets = _line_offsets(source)
    protocols = tuple(_protocol_classes(tree))
    if not protocols:
        return source
    patches: list[_Patch] = []
    missing_decorators: list[ast.ClassDef] = []
    for protocol in protocols:
        if not _has_runtime_checkable(protocol):
            missing_decorators.append(protocol)
        for statement in protocol.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            replacement = _normalized_annotation(statement.annotation)
            if replacement is not None:
                start, end = _span(statement.annotation, offsets)
                patches.append(_Patch(start, end, ast.unparse(replacement)))
            if statement.value is not None:
                start, end = _span(statement.value, offsets)
                patches.append(_Patch(start, end, "..."))
    for protocol in missing_decorators:
        if protocol.lineno is None:
            msg = "Protocol class has no source location"
            raise ValueError(msg)
        line_start = offsets[protocol.lineno - 1]
        indentation = source[line_start : line_start + protocol.col_offset]
        patches.append(
            _Patch(line_start, line_start, f"{indentation}@runtime_checkable\n")
        )
    if missing_decorators and _runtime_checkable_import(tree) is None:
        insertion = _import_insertion_offset(tree, offsets)
        suffix = "\n" if insertion else ""
        patches.append(
            _Patch(
                insertion, insertion, f"{suffix}from typing import runtime_checkable\n"
            )
        )
    if not patches:
        return source
    normalized = _apply_patches(source, patches)
    normalized_tree = ast.parse(normalized, filename=filename)
    normalized_offsets = _line_offsets(normalized)
    normalized = _apply_patches(
        normalized,
        _remove_unused_m_imports(normalized_tree, normalized_offsets),
    )
    ast.parse(normalized, filename=filename)
    return normalized


def _apply_patches(source: str, patches: Sequence[_Patch]) -> str:
    ordered = sorted(patches, key=lambda patch: (patch.start, patch.end), reverse=True)
    for current, following in itertools.pairwise(ordered):
        if following.end > current.start:
            msg = "protocol normalizer produced overlapping source patches"
            raise ValueError(msg)
    for patch in ordered:
        source = source[: patch.start] + patch.replacement + source[patch.end :]
    return source


def normalize_protocol_tree(repository_root: Path) -> tuple[Path, ...]:
    """Normalize every source protocol module below one repository root."""
    package_root = repository_root / "src" / "flext_infra" / "_protocols"
    if not package_root.is_dir():
        msg = f"protocol source directory does not exist: {package_root}"
        raise FileNotFoundError(msg)
    changed: list[Path] = []
    for path in sorted(package_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        normalized = normalize_protocol_source(source, filename=str(path))
        if normalized != source:
            path.write_text(normalized, encoding="utf-8")
            changed.append(path)
    return tuple(changed)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the source-only bootstrap and print the number of changed modules."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository_root", type=Path)
    arguments = parser.parse_args(argv)
    changed = normalize_protocol_tree(arguments.repository_root.resolve())
    print(f"normalized protocol modules: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
