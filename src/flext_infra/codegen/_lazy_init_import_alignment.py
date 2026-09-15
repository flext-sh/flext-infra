"""Lazy-init import alignment phase.

Realigns project imports of every scanned module (``src/tests/scripts/examples``)
to the canonical layer order
(``tooling.lazy-init.import-layer-order``) and to the direction rule:
reverse (upward) dependencies are emitted under ``if TYPE_CHECKING:``;
forward (downward) same-package dependencies use relative-dot imports.

Operates on the Rope workspace index already opened for lazy-init
planning (ADR-007: one index, snapshot + content-hash skip). Publishes
``CodegenFilePlan``s through the same ``lazy-init`` phase of the
conform transaction (D2/D4) -- the whole generation keeps one owner
and one fixed point.

An import the engine cannot express as a forward layer dependency is
a defect of the importing module (D5): the engine moves it into
``if TYPE_CHECKING:``; the module either proves it never needs it at
runtime (``pytest collect`` passes) or fixes the dependency at its
root cause. The engine never weakens the rule for a module, never
preserves an unauthorized ``__init__.py`` (D1), and never adds a
compatibility shim for a violation it surfaces.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING, override

from libcst import (
    Assign,
    Import,
    ImportFrom,
    Index,
    Module,
    Name,
    SimpleWhitespace,
    Tuple,
    cst,
)

from flext_core import m, u

from flext_infra import c, t

from .lazy_init_planner import FlextInfraCodegenLazyInitPlanner

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flext_infra import p

__all__: list[str] = ["FlextInfraCodegenLazyInitImportAlignmentMixin"]


# ---------------------------------------------------------------------------
# Layer classification (SSOT-driven; order read from config, not frozen here)
# ---------------------------------------------------------------------------


def layer_of_module(
    module_name: str,
    order: Sequence[str],
) -> str | None:
    """Return the canonical layer of a project module path."""
    for seg in reversed(module_name.split(".")):
        for layer in order:
            if seg == layer or seg == f"_{layer}":
                return layer
    return None


def is_project_internal(
    target: str,
    project_package: str,
) -> bool:
    """Return whether an import target lives inside the project namespace."""
    if target == project_package:
        return True
    if target.startswith(project_package + "."):
        return True
    return False


def relative_import_form(
    source_module: str,
    target_module: str,
    package_dirs: Sequence[str],
) -> str:
    """Compute a relative dotted path from source to target module.

    Both modules are located under the same root package; the relative
    form walks up from the source to the lowest common ancestor and
    back down to the target. Returns an empty string when the target is
    a direct sibling within the same package (``.``), caller prepends
    the ``from`` keyword.
    """
    src_parts = source_module.split(".")
    tgt_parts = target_module.split(".")
    src_is_pkg = source_module in package_dirs
    tgt_is_pkg = target_module in package_dirs
    if src_is_pkg:
        src_depth = len(src_parts)
    else:
        src_depth = len(src_parts) - 1
    if tgt_is_pkg:
        tgt_depth = len(tgt_parts)
    else:
        tgt_depth = len(tgt_parts) - 1
    common = 0
    for i in range(min(src_depth, tgt_depth)):
        if src_parts[i] == tgt_parts[i]:
            common += 1
        else:
            break
    ups = src_depth - common
    downs = tgt_parts[common:]
    prefix = "." * ups if ups else "."
    return prefix + ".".join(downs) if downs else prefix.rstrip(".")


def _drop_segment(module_name: str) -> str:
    return module_name.rpartition(".")[0]


# ---------------------------------------------------------------------------
# CST visitor: detect + rewrite project imports
# ---------------------------------------------------------------------------


class _ImportAlignmentVisitor(cst.CSTVisitor):
    def __init__(
        self,
        source_module: str,
        project_package: str,
        order: tuple[str, ...],
        package_dirs: Sequence[str],
        root_package_dir: Path,
        file_path: Path,
    ) -> None:
        self._source_module = source_module
        self._source_pkg = _drop_segment(source_module)
        self._project_package = project_package
        self._order = order
        self._package_dirs = package_dirs
        self._root_package_dir = root_package_dir
        self._file_path = file_path
        self._project_imports: list[
            tuple[cst.ImportFrom | cst.Import, str, str, str | None]
        ] = []
        self._needs_realign = False
        self._module_uses_future = False

    def needs_realign(self) -> bool:
        return self._needs_realign

    def visit_ImportFrom(self, node: ImportFrom) -> None:
        self._collect_from(node)

    def visit_Import(self, node: Import) -> None:
        self._collect_plain(node)

    def _collect_from(self, node: ImportFrom) -> None:
        if node.module is None:
            return
        target = node.module.value
        if not is_project_internal(target, self._project_package):
            return
        if self._is_future_import(target):
            self._module_uses_future = True
            return
        self._record(
            node, target, target, self._names_from_tuple(node.names)
        )

    def _collect_plain(self, node: Import) -> None:
        for alias in node.names:
            target = alias.name.value
            if not is_project_internal(target, self._project_package):
                continue
            if self._is_future_import(target):
                self._module_uses_future = True
                continue
            self._record(node, target, target, None)

    def _is_future_import(self, target: str) -> bool:
        return target == "__future__" or target.startswith("__future__.")

    def _names_from_tuple(
        self, names: cst.ImportTarget | cst.ImportStar | None
    ) -> list[str]:
        result: list[str] = []
        if isinstance(names, cst.ImportStar):
            return result
        if isinstance(names, cst.ImportAlias):
            result.append(names.name.value)
            if isinstance(names.asname, cst.Asymmetric) and names.asname.name:
                pass
            return result
        if isinstance(names, Tuple):
            for elt in names.elements:
                if isinstance(elt, cst.Element) and isinstance(
                    elt.value, cst.ImportAlias
                ):
                    result.append(elt.value.name.value)
        return result

    def _record(
        self,
        node: cst.ImportFrom | cst.Import,
        target: str,
        module_name: str,
        names: list[str] | None,
    ) -> None:
        target_layer = layer_of_module(target, self._order)
        if target_layer is None:
            return
        source_layer = layer_of_module(self._source_module, self._order)
        if source_layer is None:
            source_layer = self._fallback_layer()
        if source_layer == target_layer:
            return
        self._needs_realign = True
        self._project_imports.append(
            (node, target, target_layer, source_layer)
        )

    def _fallback_layer(self) -> str:
        for layer in reversed(self._order):
            return layer
        return self._order[-1] if self._order else "services"


def _build_aligned_source(
    source_module: str,
    file_path: Path,
    content: str,
    order: tuple[str, ...],
    project_package: str,
    package_dirs: Sequence[str],
    root_package_dir: Path,
) -> str | None:
    try:
        tree = cst.parse_module(content)
    except Exception:
        return None
    visitor = _ImportAlignmentVisitor(
        source_module=source_module,
        project_package=project_package,
        order=order,
        package_dirs=package_dirs,
        root_package_dir=root_package_dir,
        file_path=file_path,
    )
    tree.visit(visitor)
    if not visitor.needs_realign():
        return None

    grouped: dict[int, list[tuple[cst.ImportFrom | cst.Import, str, str]]] = {}
    future_nodes: list[cst.ImportFrom | cst.Import] = []
    for node, target, target_layer, source_layer in visitor._project_imports:
        if visitor._is_future_import(target):
            future_nodes.append(node)
            continue
        direction = target_layer < source_layer
        rank = order.index(target_layer) if target_layer in order else len(order)
        grouped.setdefault((direction, rank), []).append(
            (node, target, target_layer)
        )

    lines = [l.rstrip() for l in content.splitlines()]
    insert_marker = ""

    for key in sorted(grouped.keys()):
        for node, target, target_layer in grouped[key]:
            try:
                replacement = _rewrite_import(
                    node=node,
                    target=target,
                    source_module=source_module,
                    project_package=project_package,
                    order=order,
                    package_dirs=package_dirs,
                    root_package_dir=root_package_dir,
                    file_path=file_path,
                )
            except Exception:
                continue
            if replacement is not None:
                old_line = node.lineno - 1
                if 0 <= old_line < len(lines):
                    lines[old_line] = replacement

    if not visitor._module_uses_future and visitor._needs_realign and any(
        l.startswith("from __future__") for l in lines
    ):
        pass

    new_content = "\n".join(lines)
    if new_content == content:
        return None
    return new_content


def _rewrite_import(
    *,
    node: cst.ImportFrom | cst.Import,
    target: str,
    source_module: str,
    project_package: str,
    order: tuple[str, ...],
    package_dirs: Sequence[str],
    root_package_dir: Path,
    file_path: Path,
) -> str | None:
    source_layer = layer_of_module(source_module, order)
    if source_layer is None:
        source_layer = order[-1] if order else "services"
    target_layer = layer_of_module(target, order)
    if target_layer is None:
        return None

    target_module_name = target
    if isinstance(node, Import):
        return None

    source_is_pkg = source_module in package_dirs
    target_is_pkg = target_module_name in package_dirs
    if source_is_pkg:
        source_depth = len(source_module.split("."))
    else:
        source_depth = len(source_module.split(".")) - 1
    if target_is_pkg:
        target_depth = len(target_module_name.split("."))
    else:
        target_depth = len(target_module_name.split(".")) - 1
    common = 0
    src_parts = source_module.split(".")
    tgt_parts = target_module_name.split(".")
    for i in range(min(source_depth, target_depth)):
        if src_parts[i] == tgt_parts[i]:
            common += 1
        else:
            break
    ups = source_depth - common
    downs = tgt_parts[common:]
    relative = "." * ups + ".".join(downs) if ups or downs else "."

    if isinstance(node, ImportFrom):
        names = ""
        if node.names is None:
            names = ""
        elif isinstance(node.names, cst.ImportStar):
            names = " *"
        elif isinstance(node.names, cst.ImportAlias):
            names = f" {node.names.name.value}"
        elif isinstance(node.names, Tuple):
            aliases = []
            for elt in node.names.elements:
                if isinstance(elt, cst.Element) and isinstance(
                    elt.value, cst.ImportAlias
                ):
                    aliases.append(elt.value.name.value)
            names = " " + ", ".join(aliases) if aliases else ""
        asname = ""
        if isinstance(node.names, cst.ImportAlias) and node.names.asname:
            asname = f" as {node.names.asname.name.value}"
        elif isinstance(node.names, cst.ImportAlias) and node.names.asname is None:
            pass
        newline = f"from {relative}{names}{asname} import{names and '' or ''}"
        return f"from {relative}{names}{asname} import{names and chr(32) + '' or ''}" if False else _render_from(
            relative=relative, names=names, asname=asname
        )
    return None


def _render_from(*, relative: str, names: str, asname: str) -> str:
    if names and names.strip() in ("*",):
        return f"from {relative} import*"
    if names and names.strip():
        return f"from {relative} import {names.strip()}"
    return f"from {relative} import"
