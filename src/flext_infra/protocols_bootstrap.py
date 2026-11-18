"""Normalize legacy Pydantic syntax out of protocol source modules.

Source inventory, planning and this entrypoint import only the Python standard
library. Guarded publication lives in
``flext_infra._utilities.protocol_publication`` and loads on first use, so
this module stays importable before the package exists.

Run it before the public CLI when legacy protocol source prevents package import::

    python -P src/flext_infra/protocols_bootstrap.py ROOT -- codegen generate

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import itertools
import operator
import sys
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeIs, override

if TYPE_CHECKING:
    from flext_infra import FlextInfraCli
    from flext_infra._utilities.protocol_publication import (
        FlextInfraUtilitiesProtocolPublication,
    )


_SOURCE_BOOTSTRAP_MARKER = "# AUTO-GENERATED FILE - Source bootstrap"
_SOURCE_BOOTSTRAP_CONTRACT_DOCSTRING = (
    "Structural data contract projected from the owning model."
)
_MAX_IMPORT_LINE_LENGTH = 88
_GENERATED_INIT_HEADER = "# AUTO-GENERATED FILE — Regenerate with: make gen"
_FIELD_ALIAS_KEYWORDS = frozenset({"alias", "validation_alias", "serialization_alias"})
_FIELD_ASSIGNMENT_KEYWORDS = _FIELD_ALIAS_KEYWORDS | frozenset({
    "default",
    "default_factory",
    "exclude",
})
_PYDANTIC_MODEL_BASES = frozenset({"BaseSettings", "Value"})
_PARTITION_MIN_PARTS = 2
_LAZY_EXPORT_MAPPING_INDEX = 2


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


def _is_pydantic_field(node: ast.expr) -> TypeIs[ast.Call]:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "m"
        and node.func.attr == "Field"
    )


def _field_alias_keywords(node: ast.expr) -> tuple[ast.keyword, ...]:
    """Return field-name metadata which Pydantic rejects on a type alias."""
    if not _is_pydantic_field(node):
        return ()
    return tuple(
        keyword for keyword in node.keywords if keyword.arg in _FIELD_ALIAS_KEYWORDS
    )


def _field_assignment_keywords(node: ast.expr) -> tuple[ast.keyword, ...]:
    """Return metadata that Pydantic requires on the field declaration."""
    if not _is_pydantic_field(node):
        return ()
    return tuple(
        keyword
        for keyword in node.keywords
        if keyword.arg in _FIELD_ASSIGNMENT_KEYWORDS
    )


def _field_without_alias_keywords(node: ast.Call) -> ast.expr | None:
    """Keep non-field metadata when extracting field-name metadata from an alias.

    Returns:
        The resulting ``ast.expr | None``.

    """
    retained = [
        keyword for keyword in node.keywords if keyword.arg not in _FIELD_ALIAS_KEYWORDS
    ]
    if not node.args and not retained:
        return None
    return ast.copy_location(
        ast.Call(
            func=copy.deepcopy(node.func),
            args=copy.deepcopy(node.args),
            keywords=retained,
        ),
        node,
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
    for index, character in enumerate(source.encode("utf-8")):
        if character == ord("\n"):
            offsets.append(index + 1)
    return tuple(offsets)


def _span(node: ast.stmt | ast.expr, offsets: Sequence[int]) -> tuple[int, int]:
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

    @override
    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        self.generic_visit(node)
        if not (
            _is_annotated(node.value)
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

    @override
    def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
        self.generic_visit(node)
        if (
            isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "m"
            and node.value.attr
            in {"Infra", self.owner.partition("Protocols")[0].removeprefix("Flext")}
        ):
            self.changed = True
            self.requires_facade = True
            node.value.value.id = "p"
            return node
        if not (
            isinstance(node.value, ast.Name)
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


def _import_with_names(
    node: ast.Import | ast.ImportFrom, names: Sequence[ast.alias]
) -> str:
    """Render retained native bindings in their original import form.

    Returns:
        The retained declaration, or an empty replacement when none remain.

    """
    if not names:
        return ""
    return ast.unparse(
        ast.Import(names=list(names))
        if isinstance(node, ast.Import)
        else ast.ImportFrom(module=node.module, names=list(names), level=node.level)
    )


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
        patches.append(
            _Patch(*_span(node, offsets), _import_with_names(node, retained))
        )
    return patches


def _remove_unused_pydantic_imports(
    tree: ast.Module, offsets: Sequence[int]
) -> list[_Patch]:
    """Remove Pydantic bindings only when normalization made them unused.

    Returns:
        Patches removing only bindings no longer referenced by the source.

    """
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    patches: list[_Patch] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module is None or not node.module.startswith("pydantic"):
                continue
        elif isinstance(node, ast.Import):
            if not any(alias.name.startswith("pydantic") for alias in node.names):
                continue
        else:
            continue
        retained = [
            alias for alias in node.names if (alias.asname or alias.name) in names
        ]
        if len(retained) == len(node.names):
            continue
        patches.append(
            _Patch(*_span(node, offsets), _import_with_names(node, retained))
        )
    return patches


def _remove_redundant_type_checking_imports(
    tree: ast.Module, offsets: Sequence[int]
) -> list[_Patch]:
    """Keep one ``TYPE_CHECKING`` binding when a module imports it repeatedly.

    Returns:
        Patches removing duplicate native typing bindings.

    """
    typing_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "typing"
        and any(alias.name == "TYPE_CHECKING" for alias in node.names)
    ]
    patches: list[_Patch] = []
    for node in typing_imports[1:]:
        retained = [alias for alias in node.names if alias.name != "TYPE_CHECKING"]
        patches.append(
            _Patch(*_span(node, offsets), _import_with_names(node, retained))
        )
    return patches


def _protocol_import_provider(
    tree: ast.Module, package_name: str
) -> tuple[tuple[ast.ImportFrom, ...], ast.ImportFrom]:
    """Elect the declared facade import without substituting foreign providers.

    Returns:
        Existing bindings and their exact provider declaration.

    Raises:
        ValueError: Distinct facade import origins compete.

    """
    imports = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and any((alias.asname or alias.name) == "p" for alias in node.names)
    )
    local = tuple(
        node
        for node in imports
        if node.level == 0
        and node.module in {package_name, f"{package_name}.protocols"}
    )
    foreign = tuple(node for node in imports if node not in local)
    providers = {
        _import_with_names(node, [alias])
        for node in foreign
        for alias in node.names
        if (alias.asname or alias.name) == "p"
    }
    if len(providers) > 1:
        origins = "; ".join(ast.unparse(node) for node in imports)
        message = f"protocol facade has competing import origins: {origins}"
        raise ValueError(message)
    if foreign:
        # Inside the protocol family the own letter is the facade under
        # assembly (ENFORCE-051): a local binding beside the upstream one is a
        # duplicate and is dropped; the upstream provider is bound once.
        original = foreign[0]
        binding = next(
            alias for alias in original.names if (alias.asname or alias.name) == "p"
        )
        return (*foreign, *local), ast.ImportFrom(
            module=original.module, names=[binding], level=original.level
        )
    return local, ast.ImportFrom(
        module=package_name, names=[ast.alias(name="p")], level=0
    )


def _typing_p_import_patches(
    tree: ast.Module, offsets: Sequence[int], package_name: str
) -> list[_Patch]:
    """Retain runtime bindings and canonicalize annotation-only facade imports.

    Returns:
        Source patches preserving the declared provider and evaluation context.

    Raises:
        ValueError: A runtime use has only a deferred binding.

    """
    if any(
        isinstance(node, ast.Import)
        and any(
            (alias.asname or alias.name.partition(".")[0]) == "p"
            for alias in node.names
        )
        for node in ast.walk(tree)
    ):
        return []
    imports, provider = _protocol_import_provider(tree, package_name)
    needs_p = any(
        isinstance(node, ast.Name) and node.id == "p" for node in ast.walk(tree)
    )
    if needs_p and not annotation_reference_only(tree, "p"):
        if any(node in tree.body for node in imports):
            return []
        if imports:
            message = "runtime protocol use has only a deferred facade binding"
            raise ValueError(message)
        insertion = _import_insertion_offset(tree, offsets)
        return [_Patch(insertion, insertion, f"\n{ast.unparse(provider)}\n")]
    return _deferred_protocol_import_patches(
        tree, offsets, imports, provider, needs_p=needs_p
    )


def _deferred_protocol_import_patches(
    tree: ast.Module,
    offsets: Sequence[int],
    imports: tuple[ast.ImportFrom, ...],
    provider: ast.ImportFrom,
    *,
    needs_p: bool,
) -> list[_Patch]:
    """Preserve one deferred provider and remove redundant facade imports.

    Returns:
        Non-overlapping patches for the declared typing-only bindings.

    """
    declaration = ast.unparse(provider)
    type_checking_blocks = tuple(
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
    )
    type_checking = type_checking_blocks[0] if type_checking_blocks else None
    p_only_blocks = {
        block
        for block in type_checking_blocks
        if not block.orelse
        and block.body
        and all(
            isinstance(statement, ast.ImportFrom)
            and any((alias.asname or alias.name) == "p" for alias in statement.names)
            and all((alias.asname or alias.name) == "p" for alias in statement.names)
            for statement in block.body
        )
    }
    patches: list[_Patch] = []
    canonical_import = next(
        (
            node
            for node in imports
            if node in (type_checking.body if type_checking is not None else ())
            and node.module == provider.module
            and node.level == provider.level
            and any(
                (alias.name, alias.asname)
                == (provider.names[0].name, provider.names[0].asname)
                for alias in node.names
            )
        ),
        None,
    )
    for block in p_only_blocks:
        if block is type_checking and canonical_import is not None:
            continue
        patches.append(
            _Patch(
                *_span(block, offsets),
                (
                    f"if TYPE_CHECKING:\n    {declaration}"
                    if block is type_checking and needs_p
                    else ""
                ),
            )
        )
    for node in imports:
        if any(node in block.body for block in p_only_blocks):
            continue
        if node is canonical_import:
            continue
        patches.append(
            _Patch(
                *_span(node, offsets),
                _import_with_names(
                    node,
                    [
                        alias
                        for alias in node.names
                        if (alias.asname or alias.name) != "p"
                    ],
                ),
            )
        )
    if needs_p and canonical_import is None and type_checking not in p_only_blocks:
        # A new ``TYPE_CHECKING`` block follows every top-level import, so the
        # guard name is bound before the block evaluates it.
        top_level_imports = [
            node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        insertion = (
            offsets[type_checking.body[0].lineno - 1]
            if type_checking is not None and type_checking not in p_only_blocks
            else (
                _span(top_level_imports[-1], offsets)[1]
                if top_level_imports
                else _import_insertion_offset(tree, offsets)
            )
        )
        has_type_checking = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "typing"
            and any(alias.name == "TYPE_CHECKING" for alias in node.names)
            for node in tree.body
        )
        patches.append(
            _Patch(
                insertion,
                insertion,
                (
                    ""
                    if type_checking is not None and type_checking not in p_only_blocks
                    else (
                        "\n"
                        if has_type_checking
                        else "\nfrom typing import TYPE_CHECKING\n\n"
                    )
                )
                + (
                    f"{' ' * type_checking.body[0].col_offset}{declaration}\n"
                    if type_checking is not None and type_checking not in p_only_blocks
                    else f"if TYPE_CHECKING:\n    {declaration}\n"
                ),
            )
        )
    return patches


def annotation_reference_only(
    tree: ast.Module,
    alias: str,
    runtime_annotation_ids: frozenset[int] = frozenset(),
) -> bool:
    """Prove every loaded alias belongs to a deferred type expression.

    Returns:
        Whether every reference is deferred, excluding runtime model fields.

    """
    if not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(entry.name == "annotations" for entry in node.names)
        for node in tree.body
    ):
        return False
    nodes = tuple(ast.walk(tree))
    deferred_ids = {
        id(child)
        for node in nodes
        for annotation in _type_reference_nodes(node)
        if annotation is not None and id(annotation) not in runtime_annotation_ids
        for child in ast.walk(annotation)
    }
    uses = [node for node in nodes if isinstance(node, ast.Name) and node.id == alias]
    return bool(uses) and all(id(node) in deferred_ids for node in uses)


def _type_reference_nodes(node: ast.AST) -> tuple[ast.expr | None, ...]:
    """Identify existing native type-expression subtrees.

    Returns:
        Annotation, generic-bound and generic-default nodes.

    """
    annotations: tuple[ast.expr | None, ...] = ()
    if isinstance(node, ast.AnnAssign | ast.arg):
        annotations = (node.annotation,)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        annotations = (node.returns,)
    elif isinstance(node, ast.TypeAlias):
        annotations = (node.value,)
    elif isinstance(node, ast.TypeVar):
        annotations = (node.bound, node.default_value)
    elif isinstance(node, ast.ParamSpec | ast.TypeVarTuple):
        annotations = (node.default_value,)
    return annotations


def _annotation_patches(
    tree: ast.Module, protocols: Sequence[ast.ClassDef], offsets: Sequence[int]
) -> list[_Patch]:
    patches: list[_Patch] = []
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
            replacement, _ = _normalized_annotation(annotation, owner)
            if replacement is not None:
                start, end = _span(annotation, offsets)
                patches.append(_Patch(start, end, ast.unparse(replacement)))
        # A Protocol member declares its type, never a value: an ``Ellipsis``
        # placeholder is not assignable to the declared type, so the whole
        # ``= value`` suffix is removed. A ``TypeAlias`` keeps its value.
        patches.extend(
            _Patch(
                _span(statement.annotation, offsets)[1],
                _span(statement.value, offsets)[1],
                "",
            )
            for statement in protocol.body
            if isinstance(statement, ast.AnnAssign)
            and statement.value is not None
            and not _is_type_alias_annotation(statement.annotation)
        )
    return patches


def _cleanup_normalized_imports(source: str, filename: str) -> str:
    """Remove imports rendered unnecessary by source-only normalization.

    Returns:
        The resulting ``str``.

    """
    tree = ast.parse(source, filename=filename)
    offsets = _line_offsets(source)
    cleaned = _apply_patches(
        source,
        [
            *_remove_unused_m_imports(tree, offsets),
            *_remove_unused_pydantic_imports(tree, offsets),
            *_remove_redundant_type_checking_imports(tree, offsets),
        ],
    )
    ast.parse(cleaned, filename=filename)
    return cleaned


def normalize_protocol_source(
    source: str, *, package_name: str, filename: str = "<protocol>"
) -> str:
    """Return source with Pydantic field syntax removed from ``Protocol`` bodies."""
    tree = ast.parse(source, filename=filename)
    offsets = _line_offsets(source)
    protocols = tuple(_protocol_classes(tree))
    if not protocols:
        return source
    patches = _annotation_patches(tree, protocols, offsets)
    missing_decorators: list[ast.ClassDef] = [
        protocol for protocol in protocols if not _has_runtime_checkable(protocol)
    ]
    for protocol in missing_decorators:
        line_start = offsets[protocol.lineno - 1]
        indentation = source.encode("utf-8")[
            line_start : line_start + protocol.col_offset
        ].decode("utf-8")
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
    normalized = _apply_patches(source, patches)
    normalized_tree = ast.parse(normalized, filename=filename)
    normalized = _apply_patches(
        normalized,
        _typing_p_import_patches(
            normalized_tree, _line_offsets(normalized), package_name
        ),
    )
    ast.parse(normalized, filename=filename)
    normalized = _cleanup_normalized_imports(normalized, filename)
    ast.parse(normalized, filename=filename)
    return normalized


def _apply_patches(source: str, patches: Sequence[_Patch]) -> str:
    ordered = sorted(patches, key=lambda patch: (patch.start, patch.end), reverse=True)
    for current, following in itertools.pairwise(ordered):
        if following.end > current.start:
            msg = "protocol normalizer produced overlapping source patches"
            raise ValueError(msg)
    payload = source.encode("utf-8")
    for patch in ordered:
        payload = (
            payload[: patch.start]
            + patch.replacement.encode("utf-8")
            + payload[patch.end :]
        )
    return payload.decode("utf-8")


def _is_type_alias_annotation(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id == "TypeAlias") or (
        isinstance(node, ast.Attribute) and node.attr == "TypeAlias"
    )


def _type_alias_binding(node: ast.stmt) -> tuple[str, ast.expr] | None:
    """Return one explicit PEP 695 or ``TypeAlias`` declaration."""
    if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
        return node.name.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and _is_type_alias_annotation(node.annotation)
        and node.value is not None
    ):
        return node.target.id, node.value
    return None


def _annotated_alias_metadata(
    value: ast.expr,
) -> tuple[ast.expr, tuple[ast.keyword, ...]] | None:
    """Separate rejected field-name metadata from an ``Annotated`` type alias.

    Returns:
        The resulting ``tuple[ast.expr, tuple[ast.keyword, ...]] | None``.

    Raises:
        TypeError: If m.Field alias metadata must be an AST call.

    """
    if not (
        isinstance(value, ast.Subscript)
        and _is_annotated(value.value)
        and isinstance(value.slice, ast.Tuple)
        and value.slice.elts
    ):
        return None
    base, *metadata = value.slice.elts
    extracted: list[ast.keyword] = []
    retained: list[ast.expr] = []
    for item in metadata:
        aliases = _field_alias_keywords(item)
        if not aliases:
            retained.append(item)
            continue
        extracted.extend(copy.deepcopy(aliases))
        if not isinstance(item, ast.Call):
            msg = "m.Field alias metadata must be an AST call"
            raise TypeError(msg)
        cleaned = _field_without_alias_keywords(item)
        if cleaned is not None:
            retained.append(cleaned)
    if not extracted:
        return None
    normalized = (
        copy.deepcopy(base)
        if not retained
        else ast.copy_location(
            ast.Subscript(
                value=copy.deepcopy(value.value),
                slice=ast.Tuple(
                    elts=[copy.deepcopy(base), *copy.deepcopy(retained)],
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            ),
            value,
        )
    )
    return normalized, tuple(extracted)


def _pydantic_model_base(node: ast.expr, known: set[str]) -> bool:
    """Recognize local Pydantic model bases without treating ``m`` as typing.

    Returns:
        The resulting ``bool``.

    """
    if isinstance(node, ast.Name):
        return node.id in known
    if isinstance(node, ast.Subscript):
        return _pydantic_model_base(node.value, known)
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "m"
        and (node.attr.endswith("Model") or node.attr in _PYDANTIC_MODEL_BASES)
    )


def _is_protocol_class(node: ast.ClassDef, protocols: set[str]) -> bool:
    """Keep structural protocols out of runtime Pydantic field normalization.

    Returns:
        The resulting ``bool``.

    """
    return any(
        _is_protocol_base(base) or (isinstance(base, ast.Name) and base.id in protocols)
        for base in node.bases
    )


def _field_alias_reference(annotation: ast.expr) -> tuple[str, list[ast.expr]] | None:
    if isinstance(annotation, ast.Name):
        return annotation.id, []
    if not (
        isinstance(annotation, ast.Subscript)
        and _is_annotated(annotation.value)
        and isinstance(annotation.slice, ast.Tuple)
        and annotation.slice.elts
        and isinstance(annotation.slice.elts[0], ast.Name)
    ):
        return None
    return annotation.slice.elts[0].id, list(annotation.slice.elts[1:])


def _field_annotation_with_alias_metadata(
    annotation: ast.expr, keywords: Sequence[ast.keyword]
) -> ast.expr:
    """Attach extracted alias metadata to the Pydantic field declaration.

    Returns:
        The resulting ``ast.expr``.

    Raises:
        ValueError: If field alias metadata requires a direct type-alias field
            annotation.

    """
    reference = _field_alias_reference(annotation)
    if reference is None:
        msg = "field alias metadata requires a direct type-alias field annotation"
        raise ValueError(msg)
    alias, existing = reference
    return ast.copy_location(
        ast.Subscript(
            value=ast.Name(id="Annotated", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    ast.Name(id=alias, ctx=ast.Load()),
                    *copy.deepcopy(existing),
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="m", ctx=ast.Load()),
                            attr="Field",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=copy.deepcopy(list(keywords)),
                    ),
                ],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        ),
        annotation,
    )


def _field_value_with_alias_metadata(
    value: ast.expr | None,
    arguments: Sequence[ast.expr],
    keywords: Sequence[ast.keyword],
) -> ast.expr:
    """Merge field-name metadata into an existing field declaration or default.

    Returns:
        The resulting ``ast.expr``.

    """
    if isinstance(value, ast.Call) and _is_pydantic_field(value):
        existing = {
            keyword.arg for keyword in value.keywords if keyword.arg is not None
        }
        positional_default = bool(value.args)
        return ast.copy_location(
            ast.Call(
                func=copy.deepcopy(value.func),
                args=copy.deepcopy(value.args) or copy.deepcopy(list(arguments)),
                keywords=[
                    *copy.deepcopy(value.keywords),
                    *[
                        copy.deepcopy(keyword)
                        for keyword in keywords
                        if keyword.arg not in existing
                        and not (positional_default and keyword.arg == "default")
                    ],
                ],
            ),
            value,
        )
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="m", ctx=ast.Load()),
            attr="Field",
            ctx=ast.Load(),
        ),
        args=(
            copy.deepcopy(list(arguments)) if value is None else [copy.deepcopy(value)]
        ),
        keywords=[
            copy.deepcopy(keyword)
            for keyword in keywords
            if value is None or keyword.arg != "default"
        ],
    )


def _field_without_redundant_default(value: ast.expr) -> ast.expr | None:
    """Remove an alias default duplicated by a direct positional field default.

    Returns:
        The resulting ``ast.expr | None``.

    """
    if not (_is_pydantic_field(value) and value.args):
        return None
    keywords = [keyword for keyword in value.keywords if keyword.arg != "default"]
    if len(keywords) == len(value.keywords):
        return None
    return ast.copy_location(
        ast.Call(
            func=copy.deepcopy(value.func),
            args=copy.deepcopy(value.args),
            keywords=copy.deepcopy(keywords),
        ),
        value,
    )


def _direct_annotated_field_metadata(
    annotation: ast.expr,
) -> tuple[ast.expr, tuple[ast.expr, ...], tuple[ast.keyword, ...]] | None:
    """Extract complete ``m.Field`` metadata from a direct model annotation.

    Returns:
        The resulting ``tuple[ast.expr, tuple[ast.expr, ...], tuple[ast.keyword, ...]] |
            None``.

    Raises:
        TypeError: If m.Field alias metadata must be an AST call.

    """
    if not (
        isinstance(annotation, ast.Subscript)
        and _is_annotated(annotation.value)
        and isinstance(annotation.slice, ast.Tuple)
        and annotation.slice.elts
    ):
        return None
    base, *metadata = annotation.slice.elts
    retained: list[ast.expr] = []
    arguments: list[ast.expr] = []
    keywords: list[ast.keyword] = []
    for item in metadata:
        if not _field_assignment_keywords(item):
            retained.append(item)
            continue
        if not isinstance(item, ast.Call):
            msg = "m.Field alias metadata must be an AST call"
            raise TypeError(msg)
        arguments.extend(copy.deepcopy(item.args))
        keywords.extend(copy.deepcopy(item.keywords))
    if not keywords:
        return None
    normalized = (
        copy.deepcopy(base)
        if not retained
        else ast.copy_location(
            ast.Subscript(
                value=copy.deepcopy(annotation.value),
                slice=ast.Tuple(
                    elts=[copy.deepcopy(base), *copy.deepcopy(retained)],
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            ),
            annotation,
        )
    )
    return normalized, tuple(arguments), tuple(keywords)


def _direct_field_alias_patches(
    field: ast.AnnAssign, offsets: Sequence[int]
) -> list[_Patch]:
    """Move direct ``Annotated`` field aliases into the field declaration.

    Returns:
        The resulting ``list[_Patch]``.

    """
    normalized = _direct_annotated_field_metadata(field.annotation)
    if normalized is None:
        return []
    annotation, arguments, keywords = normalized
    value = _field_value_with_alias_metadata(field.value, arguments, keywords)
    annotation_patch = _Patch(
        *_span(field.annotation, offsets), ast.unparse(annotation)
    )
    if field.value is not None:
        return [
            annotation_patch,
            _Patch(*_span(field.value, offsets), ast.unparse(value)),
        ]
    end = _span(field.annotation, offsets)[1]
    return [annotation_patch, _Patch(end, end, f" = {ast.unparse(value)}")]


type _AliasEntry = tuple[ast.expr, tuple[ast.keyword, ...], ast.stmt]


def _suite_aliases(
    statements: Sequence[ast.stmt],
    visible: Mapping[str, _AliasEntry],
    inherited_alias_names: set[str],
) -> tuple[dict[str, _AliasEntry], set[str]]:
    """Collect alias declarations visible inside one statement suite.

    Returns:
        The alias metadata by name and every declared alias name.

    """
    aliases = dict(visible)
    alias_names = set(inherited_alias_names) | set(aliases)
    for statement in statements:
        binding = _type_alias_binding(statement)
        if binding is None:
            continue
        alias_names.add(binding[0])
        normalized = _annotated_alias_metadata(binding[1])
        if normalized is not None:
            aliases[binding[0]] = (*normalized, statement)
    return aliases, alias_names


def _suite_model_names(statements: Sequence[ast.stmt]) -> set[str]:
    """Return the Pydantic model classes declared directly in one suite.

    Returns:
        The resulting ``set[str]``.

    """
    models: set[str] = set()
    protocols: set[str] = set()
    changed = True
    while changed:
        changed = False
        for statement in statements:
            if not isinstance(statement, ast.ClassDef):
                continue
            if any(_is_protocol_base(base) for base in statement.bases):
                protocols.add(statement.name)
                continue
            if statement.name in models or _is_protocol_class(statement, protocols):
                continue
            if any(_pydantic_model_base(base, models) for base in statement.bases):
                models.add(statement.name)
                changed = True
    return models


def _model_field_patches(
    field: ast.AnnAssign,
    aliases: Mapping[str, _AliasEntry],
    alias_names: set[str],
    offsets: Sequence[int],
    used_aliases: dict[int, ast.expr],
) -> list[_Patch]:
    """Plan alias-metadata repairs for one model field.

    Returns:
        The resulting ``list[_Patch]``.

    """
    reference = _field_alias_reference(field.annotation)
    if reference is None or reference[0] not in alias_names:
        direct = _direct_field_alias_patches(field, offsets)
        if direct:
            return direct
    patches: list[_Patch] = []
    if field.value is not None:
        normalized_value = _field_without_redundant_default(field.value)
        if normalized_value is not None:
            patches.append(
                _Patch(*_span(field.value, offsets), ast.unparse(normalized_value))
            )
    if reference is None or reference[0] not in aliases:
        return patches
    value, keywords, declaration = aliases[reference[0]]
    patches.append(
        _Patch(
            *_span(field.annotation, offsets),
            ast.unparse(
                _field_annotation_with_alias_metadata(field.annotation, keywords)
            ),
        )
    )
    used_aliases[id(declaration)] = value
    return patches


def _visit_model_suite(
    statements: Sequence[ast.stmt],
    visible: Mapping[str, _AliasEntry],
    inherited_alias_names: set[str],
    offsets: Sequence[int],
    used_aliases: dict[int, ast.expr],
) -> list[_Patch]:
    """Plan field repairs for one suite and every nested class suite.

    Returns:
        The resulting ``list[_Patch]``.

    """
    aliases, alias_names = _suite_aliases(statements, visible, inherited_alias_names)
    models = _suite_model_names(statements)
    field_patches: list[_Patch] = []
    for statement in statements:
        if not isinstance(statement, ast.ClassDef):
            continue
        if statement.name in models:
            for field in statement.body:
                if isinstance(field, ast.AnnAssign):
                    field_patches.extend(
                        _model_field_patches(
                            field, aliases, alias_names, offsets, used_aliases
                        )
                    )
        field_patches.extend(
            _visit_model_suite(
                statement.body, aliases, alias_names, offsets, used_aliases
            )
        )
    return field_patches


def _model_alias_patches(source: str, filename: str) -> list[_Patch]:
    """Plan field-only repairs for alias metadata in one local model module.

    Returns:
        The resulting ``list[_Patch]``.

    """
    tree = ast.parse(source, filename=filename)
    offsets = _line_offsets(source)
    used_aliases: dict[int, ast.expr] = {}
    field_patches = _visit_model_suite(tree.body, {}, set(), offsets, used_aliases)
    alias_patches = [
        _Patch(*_span(binding[1], offsets), ast.unparse(value))
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt)
        and (binding := _type_alias_binding(node)) is not None
        and (value := used_aliases.get(id(node))) is not None
    ]
    return [*field_patches, *alias_patches]


def normalize_model_alias_source(source: str, *, filename: str = "<model>") -> str:
    """Move Pydantic field-name metadata from local aliases to model fields.

    Returns:
        The resulting ``str``.

    """
    normalized = _apply_patches(source, _model_alias_patches(source, filename))
    ast.parse(normalized, filename=filename)
    return normalized


def normalize_model_alias_tree(repository_root: Path) -> tuple[Path, ...]:
    """Normalize runtime Pydantic models before the first package import.

    Returns:
        The resulting ``tuple[Path, ...]``.

    """
    root = repository_root.expanduser().resolve(strict=True)
    manifest = root / "pyproject.toml"
    package = declared_protocol_package(root, manifest.read_text(encoding="utf-8"))
    package_root = root / "src" / Path(*package.split("."))
    if not package_root.is_dir():
        return ()
    changed: list[Path] = []
    protocol_root = package_root / "_protocols"
    for path in sorted(package_root.rglob("*.py")):
        if path.is_relative_to(protocol_root):
            continue
        source = path.read_text(encoding="utf-8")
        normalized = normalize_model_alias_source(source, filename=str(path))
        if normalized != source:
            path.write_text(normalized, encoding="utf-8")
            changed.append(path)
    return tuple(changed)


def declared_protocol_package(root: Path, manifest_source: str) -> str:
    """Read the selected source package from its original project declaration.

    Returns:
        The declared import path of the project's protocol source family.

    Raises:
        ValueError: The declaration does not elect a valid Python package.

    """
    payload = tomllib.loads(manifest_source)
    project = payload.get("project", {})
    flext = payload.get("tool", {}).get("flext", {})
    docs = flext.get("docs", {})
    name = docs.get("package_name") or project.get("name", "").replace("-", "_")
    if not isinstance(name, str) or not all(
        part.isidentifier() for part in name.split(".")
    ):
        message = (
            f"project declares no valid Python package name: {root / 'pyproject.toml'}"
        )
        raise ValueError(message)
    return name


def _protocol_contract_signature(node: ast.ClassDef) -> str:
    """Return the structural signature of one nested Protocol contract."""
    body = [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    decorators = [
        decorator
        for decorator in node.decorator_list
        if not (isinstance(decorator, ast.Name) and decorator.id == "runtime_checkable")
    ]
    return ast.dump(
        ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=body,
            decorator_list=decorators,
        ),
        include_attributes=False,
    )


def _declares_mirrored_model_entity(
    protocol_root: Path,
    protocol_path: Path,
    name: str,
    declarations: dict[Path, frozenset[str]],
) -> bool:
    """Authenticate a model-path contract through one captured declaration inventory.

    Returns:
        The resulting ``bool``.

    """
    model_path = (
        protocol_root.parent / "_models" / protocol_path.relative_to(protocol_root)
    )
    if model_path not in declarations:
        if not model_path.is_file():
            declarations[model_path] = frozenset()
        else:
            tree = ast.parse(
                model_path.read_text(encoding="utf-8"), filename=str(model_path)
            )
            declarations[model_path] = frozenset(
                member.name
                for holder in tree.body
                if isinstance(holder, ast.ClassDef)
                for member in holder.body
                if isinstance(member, ast.ClassDef)
            )
    return name in declarations[model_path]


def is_source_bootstrap_owned(
    protocol_path: Path,
    contract: ast.ClassDef | None = None,
    *,
    contract_docstrings: Sequence[str] = (_SOURCE_BOOTSTRAP_CONTRACT_DOCSTRING,),
) -> bool:
    """Whether this protocol source is replaceable source-bootstrap output.

    The header and the emitted contract docstring are deliberate provenance:
    only source-bootstrap projections may yield a divergent duplicate to the
    model-path canonical contract.

    Returns:
        The resulting ``bool``.

    """
    return protocol_path.read_text(encoding="utf-8").startswith(
        _SOURCE_BOOTSTRAP_MARKER
    ) or (contract is not None and ast.get_docstring(contract) in contract_docstrings)


def _canonical_protocol_contracts(
    root: Path, protocol_root: Path, planned_sources: Mapping[Path, str]
) -> dict[str, tuple[Path, str]]:
    """Elect the canonical contract of every mirrored model entity.

    Returns:
        The canonical owner path and signature by protocol name.

    Raises:
        ValueError: If competing canonical protocol contracts.

    """
    canonical: dict[str, tuple[Path, str]] = {}
    declarations: dict[Path, frozenset[str]] = {}
    for relative, source in planned_sources.items():
        path = root / relative
        if not path.is_relative_to(protocol_root):
            continue
        tree = ast.parse(source, filename=str(path))
        holder = next(
            (node for node in tree.body if isinstance(node, ast.ClassDef)), None
        )
        if holder is None:
            continue
        for member in (node for node in holder.body if isinstance(node, ast.ClassDef)):
            if not _declares_mirrored_model_entity(
                protocol_root, path, member.name, declarations
            ):
                continue
            signature = _protocol_contract_signature(member)
            previous = canonical.setdefault(member.name, (path, signature))
            if previous != (path, signature):
                msg = (
                    "competing canonical protocol contracts "
                    f"{member.name}: {previous[0]} and {path}"
                )
                raise ValueError(msg)
    return canonical


def _retired_member_patches(
    path: Path,
    holder: ast.ClassDef,
    canonical: Mapping[str, tuple[Path, str]],
    offsets: Sequence[int],
) -> list[_Patch]:
    """Plan removal of legacy holder members displaced by canonical owners.

    Returns:
        The resulting ``list[_Patch]``.

    Raises:
        ValueError: If incompatible legacy protocol contract.

    """
    retired_members: list[ast.ClassDef] = []
    for member in (node for node in holder.body if isinstance(node, ast.ClassDef)):
        elected = canonical.get(member.name)
        if elected is None:
            continue
        canonical_path, signature = elected
        actual = _protocol_contract_signature(member)
        if actual != signature and not is_source_bootstrap_owned(path, member):
            msg = (
                "incompatible legacy protocol contract "
                f"{holder.name}.{member.name}: {path}; canonical owner "
                f"{canonical_path}"
            )
            raise ValueError(msg)
        retired_members.append(member)
    remaining = [
        statement
        for statement in holder.body
        if statement not in retired_members
        and not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    patches: list[_Patch] = []
    for index, member in enumerate(retired_members):
        start_line = min([
            member.lineno,
            *(decorator.lineno for decorator in member.decorator_list),
        ])
        patches.append(
            _Patch(
                offsets[start_line - 1],
                _span(member, offsets)[1],
                " " * (holder.col_offset + 4) + "pass"
                if not remaining and index == 0
                else "",
            )
        )
    return patches


def consolidate_protocol_owners(
    repository_root: Path, planned_sources: Mapping[Path, str]
) -> tuple[Path, ...]:
    """Retire equivalent legacy contracts displaced by projected source owners.

    The model projection is the authoritative identity/path inventory.  It may
    relocate a contract from an old aggregate holder such as ``Base`` to the
    protocol module mirroring its declaring model.  A same-named declaration in
    any other holder is safe to remove only when its structural contract is
    identical. Source-bootstrap-owned holders are projections, so their stale
    declarations yield to the canonical model-path contract; an authored
    divergence remains an explicit admission error.

    Returns:
        The resulting ``tuple[Path, ...]``.

    """
    root = repository_root.expanduser().resolve()
    package = declared_protocol_package(
        root, (root / "pyproject.toml").read_text(encoding="utf-8")
    )
    protocol_root = root / "src" / Path(*package.split(".")) / "_protocols"
    canonical = _canonical_protocol_contracts(root, protocol_root, planned_sources)
    canonical_owners = {owner for owner, _ in canonical.values()}
    changed: list[Path] = []
    for path in sorted(protocol_root.rglob("*.py")):
        if path.name == "__init__.py" or path in canonical_owners:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        offsets = _line_offsets(source)
        patches = [
            patch
            for holder in tree.body
            if isinstance(holder, ast.ClassDef)
            for patch in _retired_member_patches(path, holder, canonical, offsets)
        ]
        if patches:
            updated = _apply_patches(source, patches)
            ast.parse(updated, filename=str(path))
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return tuple(changed)


def merge_class_lineages[TIdentity: str | tuple[str, str]](
    lineages: Sequence[Sequence[TIdentity]], *, message: str
) -> tuple[TIdentity, ...]:
    """Merge declared class lineages through C3 precedence rules.

    Returns:
        The consistent linearized ancestry.

    """
    sequences = [list(lineage) for lineage in lineages]
    result: list[TIdentity] = []
    while any(sequences):
        candidate = next(
            (
                sequence[0]
                for sequence in sequences
                if sequence and all(sequence[0] not in other[1:] for other in sequences)
            ),
            None,
        )
        if candidate is None:
            failure = ValueError(message)
            heads = tuple(
                dict.fromkeys(sequence[0] for sequence in sequences if sequence)
            )
            conflicts = tuple(
                (head, sequence[0])
                for head in heads
                for sequence in sequences
                if sequence and head in sequence[1:]
            )
            failure.add_note(
                f"blocked_c3_heads={heads}; precedence_conflicts={conflicts}"
            )
            raise failure
        result.append(candidate)
        for sequence in sequences:
            if sequence and sequence[0] == candidate:
                sequence.pop(0)
    return tuple(result)


def _protocol_holders(
    package_root: Path, *, sources: Mapping[Path, str]
) -> tuple[tuple[str, str], ...]:
    holders: list[tuple[str, str]] = []
    for path in sorted(
        set(package_root.rglob("*.py"))
        | {path for path in sources if path.is_relative_to(package_root)}
    ):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(_protocol_source(path, sources=sources), filename=str(path))
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


def _declared_module_exports(tree: ast.Module) -> tuple[str, ...] | None:
    """Read one module's literal ``__all__`` through its syntax tree.

    Returns:
        The declared export names in source order, or ``None`` without ``__all__``.

    Raises:
        ValueError: ``__all__`` is not a literal list or tuple of strings.

    """
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets, value = [statement.target], statement.value
        else:
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in targets
        ):
            continue
        if not isinstance(value, (ast.List, ast.Tuple)) or not all(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in value.elts
        ):
            message = "__all__ is not a literal sequence of strings"
            raise ValueError(message)
        return tuple(
            item.value
            for item in value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
    return None


def _family_member_modules(
    directory: Path, *, sources: Mapping[Path, str]
) -> tuple[Path, ...]:
    """List the direct modules of one protocol family package, initializer apart.

    Returns:
        The resulting ``tuple[Path, ...]``.

    """
    return tuple(
        sorted({
            path
            for path in (*directory.glob("*.py"), *sources)
            if path.parent == directory
            and path.suffix == ".py"
            and path.name != "__init__.py"
            and (path in sources or path.is_file())
        })
    )


def _family_declaring_module(
    protocol_root: Path,
    prefix: str,
    provider: str,
    name: str,
    *,
    sources: Mapping[Path, str],
) -> str | None:
    """Resolve a name imported through a family package to its declaring module.

    The family package's own initializer is a projection, never an authority:
    the declaring module is elected by scanning the package's modules' ``__all__``.

    Returns:
        The absolute module declaring ``name``, or ``None`` when ``provider`` is
        not a protocol family package or none of its modules declares ``name``.

    Raises:
        ValueError: More than one module of the family declares ``name``.

    """
    if not provider.startswith(f"{prefix}."):
        return None
    relative = provider.removeprefix(f"{prefix}.")
    directory = protocol_root.joinpath(*relative.split("."))
    candidates: list[str] = []
    for path in _family_member_modules(directory, sources=sources):
        tree = ast.parse(_protocol_source(path, sources=sources), filename=str(path))
        if name in (_declared_module_exports(tree) or ()):
            candidates.append(f"{provider}.{path.stem}")
    if len(candidates) > 1:
        message = (
            f"protocol family export is declared by several modules: "
            f"{provider}.{name} -> {', '.join(candidates)}"
        )
        raise ValueError(message)
    return candidates[0] if candidates else None


def _import_from_bindings(
    statement: ast.ImportFrom,
    prefix: str,
    module: str,
    package_root: Path,
    sources: Mapping[Path, str],
) -> dict[str, str]:
    """Resolve the declared origin of every name bound by one ``from`` import.

    Returns:
        The origin identity by bound name.

    """
    provider = statement.module or ""
    if statement.level:
        provider = importlib.util.resolve_name(
            "." * statement.level + provider,
            f"{prefix}{module}".rpartition(".")[0],
        )
    exports = (
        _existing_protocol_exports(package_root, sources=sources)
        if provider == prefix
        else {}
    )
    bindings: dict[str, str] = {}
    for imported in statement.names:
        if imported.name in exports:
            origin = f"{prefix}{exports[imported.name]}.{imported.name}"
        else:
            declaring = _family_declaring_module(
                package_root, prefix, provider, imported.name, sources=sources
            )
            origin = (
                f"{declaring}.{imported.name}"
                if declaring is not None
                else f"{provider}.{imported.name}"
            )
        bindings[imported.asname or imported.name] = origin
    return bindings


def _statement_bindings(
    statement: ast.stmt, prefix: str, module: str
) -> dict[str, str | None]:
    """Return the names one non-``from`` module statement binds.

    Returns:
        The origin identity by bound name, ``None`` for local values.

    """
    bindings: dict[str, str | None] = {}
    if isinstance(statement, ast.Import):
        for imported in statement.names:
            root_name = imported.name.partition(".")[0]
            bindings[imported.asname or root_name] = (
                imported.name if imported.asname else root_name
            )
    elif isinstance(statement, ast.ClassDef):
        bindings[statement.name] = f"{prefix}{module}.{statement.name}"
    elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
        bindings[statement.name] = None
    elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else (statement.target,)
        )
        for target in targets:
            for name in ast.walk(target):
                if isinstance(name, ast.Name):
                    bindings[name.id] = None
    return bindings


def _holder_bindings(
    node: ast.ClassDef,
    tree: ast.Module,
    module: str,
    package_root: Path,
    *,
    sources: Mapping[Path, str],
) -> dict[str, str | None]:
    """Collect the module bindings visible at one class-definition statement.

    Returns:
        The origin identity by bound name, ``None`` for local values.

    """
    prefix = f"{package_root.parent.name}._protocols"
    bindings: dict[str, str | None] = {}
    for statement in tree.body:
        if statement is node:
            break
        if isinstance(statement, ast.ImportFrom):
            bindings.update(
                _import_from_bindings(statement, prefix, module, package_root, sources)
            )
        else:
            bindings.update(_statement_bindings(statement, prefix, module))
    return bindings


def _base_reference(base: ast.expr) -> tuple[str, tuple[str, ...]] | None:
    """Split one class base into its root name and attribute path.

    Returns:
        The root name and attribute parts, or ``None`` for other expressions.

    """
    expression = base.value if isinstance(base, ast.Subscript) else base
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    if isinstance(expression, ast.Name):
        return expression.id, tuple(reversed(parts))
    return None


def _holder_base_names(
    node: ast.ClassDef,
    holders: Mapping[str, str],
    module: str,
    package_root: Path,
    bindings: Mapping[str, str | None],
) -> tuple[str, ...]:
    """Authenticate source bases at their class-definition statement.

    Returns:
        Local holder or native standard-library identities in declared order.

    Raises:
        ValueError: A base is shadowed, unsupported or has an unresolved provider.

    """
    prefix = f"{package_root.parent.name}._protocols"
    identities = {f"{prefix}{target}.{name}": name for name, target in holders.items()}
    names: list[str] = []
    standard = {
        f"{ancestor.__module__}.{ancestor.__qualname__}"
        for ancestor in Protocol.__mro__
    }
    for base in node.bases:
        reference = _base_reference(base)
        if reference is None:
            message = (
                f"protocol base is not a declared identity: "
                f"{module}:{ast.unparse(base)}"
            )
            raise ValueError(message)
        root_name, parts = reference
        if root_name == "object" and root_name not in bindings and not parts:
            names.append("builtins.object")
            continue
        origin = bindings.get(root_name)
        identity = ".".join((origin, *parts)) if origin is not None else ""
        if isinstance(base, ast.Subscript) and identity not in standard:
            message = (
                f"protocol base specialization is unproved: "
                f"{module}:{ast.unparse(base)}"
            )
            raise ValueError(message)
        if identity in identities:
            names.append(identities[identity])
        elif identity in standard:
            names.append(identity)
        else:
            message = (
                f"protocol base has no authenticated runtime declaration: "
                f"{module}:{ast.unparse(base)}"
            )
            raise ValueError(message)
    return tuple(names) or ("builtins.object",)


def _protocol_holder_modules(
    package_root: Path,
    holders: Sequence[tuple[str, str]],
    *,
    sources: Mapping[Path, str],
) -> dict[str, str]:
    """Merge existing and planned holder owners, rejecting competing modules.

    Returns:
        The owning module by holder name.

    Raises:
        ValueError: A holder has competing source owners.

    """
    modules: dict[str, str] = {}
    for name, module in (*_protocol_holders(package_root, sources=sources), *holders):
        if name in modules and modules[name] != module:
            message = f"protocol holder has competing source owners: {name}"
            raise ValueError(message)
        modules[name] = module
    return modules


def _protocol_holder_graph(
    package_root: Path,
    modules: Mapping[str, str],
    *,
    sources: Mapping[Path, str],
) -> dict[str, tuple[str, ...]]:
    """Build the declared base graph of every holder and of ``Protocol``.

    Returns:
        The declared base identities by holder identity.

    Raises:
        ValueError: A holder has no local module or declaration.

    """
    graph: dict[str, tuple[str, ...]] = {}
    for holder, module in modules.items():
        path = _protocol_module_path(package_root, module, sources=sources)
        if path is None:
            message = f"protocol holder has no local module: {holder} -> {module}"
            raise ValueError(message)
        tree = ast.parse(_protocol_source(path, sources=sources), filename=str(path))
        declaration = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == holder
            ),
            None,
        )
        if declaration is None:
            message = f"protocol holder is missing its declaration: {holder} -> {path}"
            raise ValueError(message)
        bindings = _holder_bindings(
            declaration, tree, module, package_root, sources=sources
        )
        graph[holder] = _holder_base_names(
            declaration, modules, module, package_root, bindings
        )
    for ancestor in Protocol.__mro__:
        graph[f"{ancestor.__module__}.{ancestor.__qualname__}"] = tuple(
            f"{base.__module__}.{base.__qualname__}" for base in ancestor.__bases__
        )
    return graph


def _holder_lineage(
    holder: str,
    graph: Mapping[str, tuple[str, ...]],
    linearized: dict[str, tuple[str, ...]],
    active: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    """Linearize one holder ancestry through C3, memoized in ``linearized``.

    Returns:
        The holder followed by its C3-ordered ancestors.

    Raises:
        ValueError: The ancestry is cyclic or unresolved.

    """
    if holder in linearized:
        return linearized[holder]
    if holder in active:
        message = f"cyclic protocol holder inheritance: {holder}"
        raise ValueError(message)
    if holder not in graph:
        message = f"protocol holder ancestry is unresolved: {holder}"
        raise ValueError(message)
    bases = graph[holder]
    parents = tuple(
        _holder_lineage(base, graph, linearized, active | {holder}) for base in bases
    )
    linearized[holder] = (
        holder,
        *merge_class_lineages(
            (*parents, bases),
            message=f"protocol holder has inconsistent C3 ancestry: {holder}",
        ),
    )
    return linearized[holder]


def _aggregate_protocol_holders(
    package_root: Path,
    holders: Sequence[tuple[str, str]],
    *,
    sources: Mapping[Path, str],
) -> tuple[tuple[str, str], ...]:
    """Elect nearest declared owners and prove their composition through C3.

    Source owners, imports and class precedence are validated by the holder
    module, graph and lineage helpers, which raise ``ValueError`` on conflict.

    Returns:
        Source-ordered maximal holders without redundant ancestor bases.

    """
    modules = _protocol_holder_modules(package_root, holders, sources=sources)
    graph = _protocol_holder_graph(package_root, modules, sources=sources)
    linearized: dict[str, tuple[str, ...]] = {}
    selected = tuple(holder for holder, _module in holders)
    inherited = {
        base
        for holder in selected
        for base in _holder_lineage(holder, graph, linearized)[1:]
    }
    nearest = tuple(holder for holder in selected if holder not in inherited)
    merge_class_lineages(
        (*[_holder_lineage(holder, graph, linearized) for holder in nearest], nearest),
        message="aggregate protocol holders have inconsistent C3 precedence",
    )
    return tuple((holder, modules[holder]) for holder in nearest)


def _render_facade_import(module: str, holder: str) -> str:
    """Render one aggregate import within the project's Ruff line limit.

    Returns:
        The static import statement, wrapped when necessary.

    """
    statement = f"from flext_infra._protocols{module} import {holder}"
    return (
        statement
        if len(statement) <= _MAX_IMPORT_LINE_LENGTH
        else f"from flext_infra._protocols{module} import (\n    {holder},\n)"
    )


def _render_lazy_export_type_import(module: str, holder: str) -> str:
    """Render one type-only protocol barrel binding within Ruff's line limit.

    Returns:
        The resulting ``str``.

    """
    statement = f"from flext_infra._protocols{module} import {holder}"
    return (
        statement
        if len(statement) <= _MAX_IMPORT_LINE_LENGTH - 4
        else f"from flext_infra._protocols{module} import (\n    {holder},\n)"
    )


def _render_lazy_export_mapping_entry(holder: str, module: str) -> str:
    """Render one protocol barrel map entry within Ruff's line limit.

    Returns:
        The resulting ``str``.

    """
    indentation = "            "
    statement = f'{indentation}"{holder}": "{module}",'
    return (
        statement
        if len(statement) <= _MAX_IMPORT_LINE_LENGTH
        else f'{indentation}"{holder}":\n{indentation}    "{module}",'
    )


def _pascal_case(value: str) -> str:
    """Return the class-name component for one snake-case module segment."""
    return "".join(part.capitalize() for part in value.split("_") if part)


def _partition_owner_name(holder: str, module_name: str) -> str:
    """Derive the canonical domain holder from one partition member holder.

    Returns:
        The resulting ``str``.

    Raises:
        ValueError: If cannot derive protocol partition owner from.

    """
    suffix = _pascal_case(module_name)
    if not suffix or not holder.endswith(suffix):
        msg = f"cannot derive protocol partition owner from {holder!r}: {module_name!r}"
        raise ValueError(msg)
    return holder[: -len(suffix)]


def _partition_owner_text(
    package_root: Path, domain: str, owner: str, members: Sequence[tuple[str, str]]
) -> tuple[str, str]:
    """Render the member imports and class header of one partition owner.

    Returns:
        The import block and the rendered owner class.

    """
    imports = "\n".join(
        f"from {package_root.parent.name}._protocols{module} import {holder}"
        for holder, module in members
    )
    bases = ",\n        ".join(holder for holder, _module in members)
    rendered_class = (
        f"class {owner}(\n"
        f"    {bases},\n"
        "):\n"
        f'    """Canonical structural contracts for the {domain} domain."""\n'
    )
    return imports, rendered_class


def _partition_owner_patches(
    source: str,
    tree: ast.Module,
    existing: ast.ClassDef,
    imports: str,
    rendered_class: str,
) -> list[_Patch]:
    """Plan the import insertion and header rewrite of a baseless owner.

    Returns:
        The resulting ``list[_Patch]``.

    """
    offsets = _line_offsets(source)
    line_start = offsets[existing.lineno - 1]
    header_end = source.encode("utf-8").index(b":", line_start) + 1
    insertion = _import_insertion_offset(tree, offsets)
    return [
        _Patch(insertion, insertion, f"\n{imports}\n"),
        _Patch(line_start, header_end, rendered_class.rstrip("\n")),
    ]


def _render_partition_owner(
    package_root: Path,
    relative_directory: Path,
    members: Sequence[tuple[str, str]],
    *,
    sources: dict[Path, str],
) -> tuple[str, str]:
    """Create or update the canonical holder for one private protocol partition.

    Returns:
        The resulting ``tuple[str, str]``.

    Raises:
        ValueError: If protocol partition has no domain name; or if canonical protocol
            partition owner is missing; or if canonical protocol partition owner has
            incompatible bases.

    """
    domain = relative_directory.name.removeprefix("_")
    if not domain:
        msg = f"protocol partition has no domain name: {relative_directory}"
        raise ValueError(msg)
    owner = _partition_owner_name(members[0][0], members[0][1].rsplit(".", 1)[-1])
    owner_module = "." + ".".join((*relative_directory.parent.parts, domain))
    owner_path = package_root.joinpath(*relative_directory.parent.parts, f"{domain}.py")
    imports, rendered_class = _partition_owner_text(
        package_root, domain, owner, members
    )
    if not owner_path.exists() and owner_path not in sources:
        sources[owner_path] = (
            "# AUTO-GENERATED FILE - Source bootstrap protocol domain owner.\n"
            '"""Canonical owner for partitioned protocol contracts."""\n\n'
            "from __future__ import annotations\n\n"
            f"{imports}\n\n\n"
            f"{rendered_class}\n"
            f'__all__: tuple[str, ...] = ("{owner}",)\n'
        )
        return owner, owner_module
    source = _protocol_source(owner_path, sources=sources)
    tree = ast.parse(source, filename=str(owner_path))
    existing = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == owner
        ),
        None,
    )
    if existing is None:
        msg = f"canonical protocol partition owner is missing {owner}: {owner_path}"
        raise ValueError(msg)
    member_names = tuple(holder for holder, _module in members)
    if existing.bases:
        if not set(member_names).issubset(
            base.id for base in existing.bases if isinstance(base, ast.Name)
        ):
            msg = (
                f"canonical protocol partition owner has incompatible bases: "
                f"{owner_path}"
            )
            raise ValueError(msg)
        return owner, owner_module
    sources[owner_path] = _apply_patches(
        source,
        _partition_owner_patches(source, tree, existing, imports, rendered_class),
    )
    return owner, owner_module


def _plan_partition_owners(
    package_root: Path, *, sources: dict[Path, str]
) -> tuple[tuple[str, str], ...]:
    """Materialize canonical owners for every private protocol partition.

    Returns:
        The resulting ``tuple[tuple[str, str], ...]``.

    """
    holders = _protocol_holders(package_root, sources=sources)
    by_directory: dict[Path, list[tuple[str, str]]] = {}
    for holder, module in holders:
        relative = Path(*module[1:].split("."))
        if len(
            relative.parts
        ) < _PARTITION_MIN_PARTS or not relative.parent.name.startswith("_"):
            continue
        by_directory.setdefault(relative.parent, []).append((holder, module))
    owners: list[tuple[str, str]] = []
    for directory, members in sorted(
        by_directory.items(), key=lambda item: item[0].as_posix()
    ):
        owners.append(
            _render_partition_owner(
                package_root, directory, sorted(members), sources=sources
            )
        )
    return tuple(owners)


def _protocol_module_path(
    protocol_root: Path, module: str, *, sources: Mapping[Path, str]
) -> Path | None:
    """Return a local protocol module path for one lazy-export target."""
    if not module.startswith(".") or module.startswith(".."):
        return None
    candidate = protocol_root.joinpath(*module[1:].split("."))
    module_file = candidate.with_suffix(".py")
    if module_file in sources or module_file.is_file():
        return module_file
    package_init = candidate / "__init__.py"
    return package_init if package_init in sources or package_init.is_file() else None


def _lazy_export_mapping(node: ast.AST) -> ast.Dict | None:
    """Return the native dictionary passed to ``install_lazy_exports``.

    Returns:
        The ``MappingProxyType`` dictionary literal, or ``None`` for other nodes.

    """
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "install_lazy_exports"
        and len(node.args) > _LAZY_EXPORT_MAPPING_INDEX
    ):
        return None
    proxy = node.args[_LAZY_EXPORT_MAPPING_INDEX]
    if not (
        isinstance(proxy, ast.Call)
        and isinstance(proxy.func, ast.Name)
        and proxy.func.id == "MappingProxyType"
        and proxy.args
    ):
        return None
    contents = proxy.args[0]
    return contents if isinstance(contents, ast.Dict) else None


def _existing_protocol_exports(
    protocol_root: Path, *, sources: Mapping[Path, str]
) -> dict[str, str]:
    """Read live mappings from the protocol barrel's native lazy exports.

    Returns:
        The resulting ``dict[str, str]``.

    """
    initializer = protocol_root / "__init__.py"
    if initializer not in sources and not initializer.is_file():
        return {}
    source = _protocol_source(initializer, sources=sources)
    tree = ast.parse(source, filename=str(initializer))
    contents = next(
        (
            mapping
            for node in ast.walk(tree)
            if (mapping := _lazy_export_mapping(node)) is not None
        ),
        None,
    )
    if contents is None:
        return {}
    exports: dict[str, str] = {}
    for key, value in zip(contents.keys, contents.values, strict=True):
        if not (
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            continue
        module_path = _protocol_module_path(protocol_root, value.value, sources=sources)
        if module_path is None:
            continue
        module_tree = ast.parse(
            _protocol_source(module_path, sources=sources), filename=str(module_path)
        )
        if any(
            isinstance(node, ast.ClassDef) and node.name == key.value
            for node in module_tree.body
        ):
            exports[key.value] = value.value
    return exports


def plan_protocol_facades(
    repository_root: Path, *, declared_sources: Mapping[Path, str] | None = None
) -> Mapping[Path, str]:
    """Plan lazy exports and ancestry-minimal sources without runtime imports.

    Returns:
        The dependency-closed source effects over the complete candidate view.

    """
    sources = dict(declared_sources or {})
    package = repository_root / "src" / "flext_infra"
    protocol_root = package / "_protocols"
    partition_owners = _plan_partition_owners(protocol_root, sources=sources)
    holders = tuple(
        (holder, module)
        for holder, module in _protocol_holders(protocol_root, sources=sources)
        if not Path(*module[1:].split(".")).parent.name.startswith("_")
    )
    holders = tuple(sorted(dict((*holders, *partition_owners)).items()))
    exports_by_name = _existing_protocol_exports(protocol_root, sources=sources)
    partition_member_names = {
        holder
        for holder, module in _protocol_holders(protocol_root, sources=sources)
        if Path(*module[1:].split(".")).parent.name.startswith("_")
    }
    for holder in partition_member_names:
        exports_by_name.pop(holder, None)
    exports_by_name.update(dict(holders))
    exports_by_name = dict(sorted(exports_by_name.items()))
    holder_exports = _aggregate_protocol_holders(
        protocol_root, holders, sources=sources
    )
    mapping_entries = "\n".join(
        itertools.starmap(_render_lazy_export_mapping_entry, exports_by_name.items())
    )
    mapping_entries = f"{mapping_entries}\n" if mapping_entries else ""
    imports = "\n".join(
        _render_facade_import(module, holder)
        for holder, module in sorted(holder_exports, key=operator.itemgetter(1, 0))
    )
    type_imports = "\n".join(
        _render_lazy_export_type_import(module, holder)
        for holder, module in exports_by_name.items()
    )
    indented_type_imports = type_imports.replace("\n", "\n    ")
    bases = ",\n        ".join(holder for holder, _module in holder_exports)
    sources[protocol_root / "__init__.py"] = (
        "# AUTO-GENERATED FILE - Source bootstrap protocol exports.\n"
        '"""Lazy protocol mirror exports.\n\n'
        "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
        "SPDX-License-Identifier: MIT\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from types import MappingProxyType\n"
        "from typing import TYPE_CHECKING\n\n"
        "from flext_core.lazy import install_lazy_exports\n\n"
        + (
            f"if TYPE_CHECKING:\n    {indented_type_imports}\n\n"
            if type_imports
            else ""
        )
        + "# fmt: off\n"
        "_LAZY_IMPORTS = MappingProxyType(\n"
        "    {\n"
        f"{mapping_entries}"
        "    }\n"
        ")\n"
        "__all__ = tuple(_LAZY_IMPORTS)\n\n"
        "install_lazy_exports(\n"
        "    __name__,\n"
        "    globals(),\n"
        "    _LAZY_IMPORTS,\n"
        "    public_exports=__all__,\n"
        ")\n"
        "# fmt: on\n"
    )
    sources[package / "protocols.py"] = (
        "# AUTO-GENERATED FILE - Source bootstrap protocol facade.\n"
        '"""Structural contracts projected from source model declarations.\n\n'
        "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
        "SPDX-License-Identifier: MIT\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from flext_cli import FlextCliProtocols\n\n"
        f"{imports}\n\n\n"
        "class FlextInfraProtocols(FlextCliProtocols):\n"
        '    """Structural contracts for flext-infra."""\n\n'
        + (
            f"    class Infra(\n        {bases},\n    ):\n"
            if bases
            else "    class Infra:\n"
        )
        + '        """Aggregate source-derived protocol contracts."""\n\n\n'
        "p = FlextInfraProtocols\n"
        '__all__: list[str] = ["FlextInfraProtocols", "p"]\n'
    )
    return sources


def _family_export_key(name: str) -> tuple[int, str]:
    """Order one public name like the lazy-init renderer: constants, classes, rest.

    Returns:
        The resulting ``tuple[int, str]``.

    """
    return (0 if name.isupper() else 1 if name[:1].isupper() else 2, name)


def _family_init_docstring(module_name: str) -> str:
    """Return the package docstring the lazy-init renderer derives from the path."""
    label = ". ".join(
        " ".join(word.capitalize() for word in part.strip("_").split("_"))
        for part in module_name.split(".")
    )
    return (
        f'"""{label} package.\n\n'
        "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
        "SPDX-License-Identifier: MIT\n"
        '"""'
    )


def _render_family_init(
    module_name: str, members: Sequence[tuple[str, Sequence[str]]]
) -> str:
    """Render one protocol family initializer in the lazy-init generator layout.

    The result carries the generator header, so ``make gen`` owns it afterwards.

    Returns:
        The initializer source: type-only imports, ``__all__`` and the lazy mapping.

    Raises:
        ValueError: Two modules of the family declare the same export.

    """
    owners: dict[str, str] = {}
    for stem, names in members:
        for name in names:
            if name in owners:
                message = (
                    f"protocol family export is declared by several modules: "
                    f"{module_name}.{name} -> {owners[name]}, {stem}"
                )
                raise ValueError(message)
            owners[name] = stem
    imports: list[str] = []
    for stem, names in sorted(members, key=operator.itemgetter(0)):
        if not names:
            continue
        ordered = sorted(names, key=_family_export_key)
        compact = f"    from {module_name}.{stem} import {', '.join(ordered)}"
        imports.append(
            compact
            if len(compact) <= _MAX_IMPORT_LINE_LENGTH
            else f"    from {module_name}.{stem} import (\n"
            + "".join(f"        {name},\n" for name in ordered)
            + "    )"
        )
    exported = sorted(owners, key=_family_export_key)
    entries: list[str] = []
    for name in exported:
        line = f'        "{name}": ".{owners[name]}",'
        entries.append(
            line
            if len(line) <= _MAX_IMPORT_LINE_LENGTH
            else f'        "{name}": (\n            ".{owners[name]}"\n        ),'
        )
    mapping = "\n".join(entries)
    return (
        f"{_GENERATED_INIT_HEADER}\n"
        f"{_family_init_docstring(module_name)}\n\n"
        "from __future__ import annotations\n\n"
        "from types import MappingProxyType\n"
        "from typing import TYPE_CHECKING\n\n"
        "from flext_core.lazy import install_lazy_exports\n\n"
        + (f"if TYPE_CHECKING:\n{chr(10).join(imports)}\n\n\n" if imports else "")
        + "_LAZY_IMPORTS = MappingProxyType({\n"
        f"{mapping}\n"
        "})\n"
        "__all__ = tuple(_LAZY_IMPORTS)\n\n"
        "install_lazy_exports(\n"
        "    __name__,\n"
        "    globals(),\n"
        "    _LAZY_IMPORTS,\n"
        "    public_exports=__all__,\n"
        ")\n"
    )


def plan_protocol_family_inits(
    repository_root: Path,
    *,
    package_name: str,
    declared_sources: Mapping[Path, str],
) -> Mapping[Path, str]:
    """Plan a lazy-export initializer for every protocol family package lacking one.

    A family package is a private (underscore-prefixed) directory of projected
    protocol modules. Its exports derive from the ``__all__`` of its direct
    modules. An absent initializer, or a generated stub that installs no lazy
    exports, is planned; an authored or already lazy initializer belongs to the
    lazy-init generator and is never rewritten here.

    Returns:
        The initializer sources to write, keyed by destination path.

    Raises:
        ValueError: A family module declares no literal ``__all__``.

    """
    sources = dict(declared_sources)
    package_root = repository_root / "src" / Path(*package_name.split("."))
    protocol_root = package_root / "_protocols"
    directories = sorted({
        path.parent
        for path in sources
        if path.suffix == ".py"
        and path.name != "__init__.py"
        and path.parent != protocol_root
        and path.parent.is_relative_to(protocol_root)
        and path.parent.name.startswith("_")
    })
    planned: dict[Path, str] = {}
    for directory in directories:
        initializer = directory / "__init__.py"
        existing = sources.get(initializer)
        if existing is not None and (
            not existing.startswith(_GENERATED_INIT_HEADER)
            or "install_lazy_exports(" in existing
        ):
            continue
        members: list[tuple[str, tuple[str, ...]]] = []
        for path in _family_member_modules(directory, sources=sources):
            tree = ast.parse(
                _protocol_source(path, sources=sources), filename=str(path)
            )
            names = _declared_module_exports(tree)
            if names is None:
                message = f"protocol family module declares no __all__: {path}"
                raise ValueError(message)
            members.append((path.stem, names))
        module_name = ".".join((
            package_name,
            "_protocols",
            *directory.relative_to(protocol_root).parts,
        ))
        planned[initializer] = _render_family_init(module_name, members)
    return planned


def _protocol_source(path: Path, *, sources: Mapping[Path, str]) -> str:
    """Read a declared candidate without importing its runtime package.

    Returns:
        Its exact declared source, or its unchanged physical source.

    """
    return sources[path] if path in sources else path.read_text(encoding="utf-8")


def _publication() -> type[FlextInfraUtilitiesProtocolPublication]:
    """Resolve the guarded publication owner on first use.

    The bootstrap core stays importable before the package exists; the
    facade publication capabilities load when the script route first
    needs them, keeping this module's stdlib-only inventory contract.

    Returns:
        The publication owner class.

    """
    return importlib.import_module(
        "flext_infra._utilities.protocol_publication"
    ).FlextInfraUtilitiesProtocolPublication


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
    publication = _publication()
    initialized = publication.publish_protocol_family_inits(root)
    model_changed = normalize_model_alias_tree(root)
    changed = publication.normalize_protocol_tree(root)
    if (
        declared_protocol_package(
            root, (root / "pyproject.toml").read_text(encoding="utf-8")
        )
        == "flext_infra"
    ):
        publication.publish_protocol_facades(root)
    sys.stdout.write(f"normalized model alias fields: {len(model_changed)}\n")
    sys.stdout.write(f"normalized protocol modules: {len(changed)}\n")
    sys.stdout.write(f"published protocol family initializers: {len(initialized)}\n")
    if len(arguments) == 1:
        return 0
    command = arguments[2:] if arguments[1] == "--" else arguments[1:]
    sys.path.insert(0, str(root / "src"))
    cli: type[FlextInfraCli] = importlib.import_module("flext_infra").FlextInfraCli
    return cli.infra_main(command)


if __name__ == "__main__":
    if not sys.flags.safe_path:
        msg = "protocol source bootstrap requires Python -P safe path"
        raise SystemExit(msg)
    raise SystemExit(main())
