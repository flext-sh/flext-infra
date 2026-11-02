"""Normalize legacy Pydantic syntax out of protocol source modules.

This module deliberately imports only the Python standard library so it can repair
``src/<package>/_protocols`` before importing the package that owns those sources.

Run it before the public CLI when legacy protocol source prevents package import::

    python src/flext_infra/_protocols_bootstrap.py /path/to/flext-infra -- codegen generate

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import itertools
import sys
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


def _is_model_metadata(node: ast.expr) -> bool:
    return _is_pydantic_field(node) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "m"
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
        retained = [item for item in metadata if not _is_model_metadata(item)]
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


class _ModelReferenceRewriter(ast.NodeTransformer):
    """Replace concrete model holders with structural protocol routes."""

    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.changed = False
        self.requires_facade = False

    def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
        node = self.generic_visit(node)
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "m"
            and node.value.attr == "Infra"
        ):
            self.changed = True
            self.requires_facade = True
            node.value.value.id = "p"
            return node
        if not (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id.startswith("FlextInfraModels")
        ):
            return node
        self.changed = True
        if node.value.id == self.owner.replace("Protocols", "Models"):
            node.value.id = self.owner
            return node
        self.requires_facade = True
        return ast.copy_location(
            ast.Attribute(
                value=ast.Attribute(
                    value=ast.Name(id="p", ctx=ast.Load()),
                    attr="Infra",
                    ctx=ast.Load(),
                ),
                attr=node.attr,
                ctx=ast.Load(),
            ),
            node,
        )


def _normalized_annotation(
    annotation: ast.expr, owner: str
) -> tuple[ast.expr | None, bool]:
    remover = _PydanticAnnotatedMetadataRemover()
    rewriter = _ModelReferenceRewriter(owner)
    normalized = rewriter.visit(
        remover.visit(
            ast.fix_missing_locations(
                ast.parse(ast.unparse(annotation), mode="eval").body
            )
        )
    )
    return (
        normalized if remover.changed or rewriter.changed else None,
        rewriter.requires_facade,
    )


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


def _has_infra_facade_import(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "flext_infra"
        and any((alias.asname or alias.name) == "p" for alias in node.names)
        for node in tree.body
    )


def _annotation_patches(
    tree: ast.Module, protocols: Sequence[ast.ClassDef], offsets: Sequence[int]
) -> tuple[list[_Patch], bool]:
    patches: list[_Patch] = []
    requires_facade = False
    owner = next(
        (
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef) and "Protocols" in node.name
        ),
        "",
    )
    for protocol in protocols:
        annotations: list[ast.expr] = []
        for candidate in protocol.body:
            if isinstance(candidate, ast.AnnAssign):
                annotations.append(candidate.annotation)
            elif isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if candidate.returns is not None:
                    annotations.append(candidate.returns)
                annotations.extend(
                    argument.annotation
                    for argument in (
                        *candidate.args.posonlyargs,
                        *candidate.args.args,
                        *candidate.args.kwonlyargs,
                    )
                    if argument.annotation is not None
                )
        for annotation in annotations:
            replacement, needs_facade = _normalized_annotation(annotation, owner)
            requires_facade = requires_facade or needs_facade
            if replacement is not None:
                start, end = _span(annotation, offsets)
                patches.append(_Patch(start, end, ast.unparse(replacement)))
        for statement in protocol.body:
            if isinstance(statement, ast.AnnAssign) and statement.value is not None:
                start, end = _span(statement.value, offsets)
                patches.append(_Patch(start, end, "..."))
    return patches, requires_facade


def normalize_protocol_source(source: str, *, filename: str = "<protocol>") -> str:
    """Return source with Pydantic field syntax removed from ``Protocol`` bodies."""
    tree = ast.parse(source, filename=filename)
    offsets = _line_offsets(source)
    protocols = tuple(_protocol_classes(tree))
    if not protocols:
        return source
    patches, requires_facade = _annotation_patches(tree, protocols, offsets)
    requires_facade = requires_facade or any(
        isinstance(node, ast.Name) and node.id == "p"
        for protocol in protocols
        for node in ast.walk(protocol)
    )
    missing_decorators: list[ast.ClassDef] = [
        protocol for protocol in protocols if not _has_runtime_checkable(protocol)
    ]
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
    if requires_facade and not _has_infra_facade_import(tree):
        insertion = _import_insertion_offset(tree, offsets)
        patches.append(_Patch(insertion, insertion, "\nfrom flext_infra import p\n"))
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


def _protocol_holders(package_root: Path) -> tuple[tuple[str, str], ...]:
    holders: list[tuple[str, str]] = []
    for path in sorted(package_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        holder = next(
            (
                node.name
                for node in tree.body
                if isinstance(node, ast.ClassDef) and "Protocols" in node.name
            ),
            None,
        )
        if holder is not None:
            module = "." + ".".join(
                path.relative_to(package_root).with_suffix("").parts
            )
            holders.append((holder, module))
    return tuple(holders)


def publish_protocol_facades(repository_root: Path) -> None:
    """Publish lazy protocol exports and the aggregate ``p.Infra`` source facade."""
    package = repository_root / "src" / "flext_infra"
    protocol_root = package / "_protocols"
    holders = _protocol_holders(protocol_root)
    exports = ",\n    ".join(f'"{holder}"' for holder, _module in holders)
    mappings = ",\n        ".join(
        f'"{holder}": "{module}"' for holder, module in holders
    )
    imports = "\n".join(
        f"from flext_infra._protocols{module} import {holder}"
        for holder, module in holders
    )
    bases = ",\n        ".join(holder for holder, _module in holders)
    protocol_root.joinpath("__init__.py").write_text(
        "# AUTO-GENERATED FILE - Source bootstrap protocol exports.\n"
        '"""Lazy protocol mirror exports."""\n\n'
        "from __future__ import annotations\n\n"
        "from types import MappingProxyType\n\n"
        "from flext_core.lazy import install_lazy_exports\n\n"
        f"__all__: tuple[str, ...] = (\n    {exports},\n)\n\n"
        "install_lazy_exports(__name__, globals(), MappingProxyType({\n"
        f"        {mappings},\n"
        "    }), public_exports=__all__)\n",
        encoding="utf-8",
    )
    package.joinpath("protocols.py").write_text(
        "# AUTO-GENERATED FILE - Source bootstrap protocol facade.\n"
        '"""Structural contracts projected from source model declarations."""\n\n'
        "from __future__ import annotations\n\n"
        "from flext_cli import FlextCliProtocols\n"
        f"{imports}\n\n\n"
        "class FlextInfraProtocols(FlextCliProtocols):\n"
        '    """Structural contracts for flext-infra."""\n\n'
        "    class Infra(\n"
        f"        {bases},\n"
        "    ):\n"
        '        """Aggregate source-derived protocol contracts."""\n\n'
        "p = FlextInfraProtocols\n"
        '__all__: list[str] = ["FlextInfraProtocols", "p"]\n',
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Normalize protocol source, then optionally invoke the public CLI.

    Returns:
        The public CLI's exit status, or zero when only normalization was requested.

    Raises:
        ValueError: The repository-root argument is absent.

    """
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if not arguments:
        msg = "protocol bootstrap requires a repository root"
        raise ValueError(msg)
    root = Path(arguments[0]).resolve()
    normalize_protocol_tree(root)
    publish_protocol_facades(root)
    if len(arguments) == 1:
        return 0
    command = arguments[2:] if arguments[1] == "--" else arguments[1:]
    sys.path.insert(0, str(root / "src"))
    from flext_infra.cli import FlextInfraCli

    return FlextInfraCli.infra_main(command)


if __name__ == "__main__":
    raise SystemExit(main())
