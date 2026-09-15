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

from pathlib import Path
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst import Import, ImportFrom

from flext_core import r
from flext_infra import t
from flext_infra.models import m
from flext_infra.utilities import u
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flext_infra import p

__all__: list[str] = ["FlextInfraCodegenLazyInitImportAlignmentMixin"]


# ---------------------------------------------------------------------------
# Layer classification (SSOT-driven; order read from config, not frozen here)
# ---------------------------------------------------------------------------


def layer_of_module(module_name: str, order: Sequence[str]) -> str | None:
    """Return the canonical layer of a project module path."""
    for seg in reversed(module_name.split(".")):
        for layer in order:
            if seg in {layer, f"_{layer}"}:
                return layer
    return None


def dotted_name(node: cst.BaseExpression) -> str:
    """Return the full dotted name of a Name/Attribute import expression."""
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{dotted_name(node.value)}.{node.attr.value}"
    return ""


def is_project_internal(target: str, project_package: str) -> bool:
    """Return whether an import target lives inside the project namespace."""
    if target == project_package:
        return True
    return bool(target.startswith(project_package + "."))


def relative_import_form(
    source_module: str, target_module: str, package_dirs: Sequence[str]
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
    src_depth = len(src_parts) if src_is_pkg else len(src_parts) - 1
    tgt_depth = len(tgt_parts) if tgt_is_pkg else len(tgt_parts) - 1
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
# CST visitor: detect project imports needing realignment
# ---------------------------------------------------------------------------


class _ImportAlignmentVisitor(cst.CSTVisitor):
    def __init__(
        self,
        source_module: str,
        project_package: str,
        order: tuple[str, ...],
        package_dirs: frozenset[str],
        file_path: Path,
    ) -> None:
        self._source_module = source_module
        self._source_pkg = _drop_segment(source_module)
        self._project_package = project_package
        self._order = order
        self._package_dirs = package_dirs
        self._file_path = file_path
        self._project_imports: list[tuple[cst.ImportFrom | cst.Import, str, str]] = []
        self._needs_realign = False
        self._module_uses_future = False

    def needs_realign(self) -> bool:
        return self._needs_realign

    @property
    def project_imports(self) -> list[tuple[cst.ImportFrom | cst.Import, str, str]]:
        """The project imports collected during the CST walk."""
        return self._project_imports

    @override
    def visit_ImportFrom(self, node: ImportFrom) -> None:
        self._collect_from(node)

    @override
    def visit_Import(self, node: Import) -> None:
        self._collect_plain(node)

    def _collect_from(self, node: ImportFrom) -> None:
        if node.module is None:
            return
        target = dotted_name(node.module)
        if not is_project_internal(target, self._project_package):
            return
        if self._is_future_import(target):
            self._module_uses_future = True
            return
        self._record(node, target)

    def _collect_plain(self, node: Import) -> None:
        for alias in node.names:
            target = dotted_name(alias.name)
            if not is_project_internal(target, self._project_package):
                continue
            if self._is_future_import(target):
                self._module_uses_future = True
                continue
            self._record(node, target)

    def _is_future_import(self, target: str) -> bool:
        return target == "__future__" or target.startswith("__future__.")

    def _names_from_tuple(
        self, names: cst.ImportTarget | cst.ImportStar | None
    ) -> list[str]:
        result: list[str] = []
        if isinstance(names, cst.ImportStar):
            return result
        if isinstance(names, cst.ImportAlias):
            result.append(dotted_name(names.name))
            return result
        if isinstance(names, cst.Tuple):
            result.extend(
                dotted_name(elt.value.name)
                for elt in names.elements
                if isinstance(elt, cst.Element) and isinstance(elt.value, cst.ImportAlias)
            )
            return result
        result.extend(
            dotted_name(alias.name)
            for alias in names
            if isinstance(alias, cst.ImportAlias)
        )
        return result

    def _record(self, node: cst.ImportFrom | cst.Import, target: str) -> None:
        target_layer = layer_of_module(target, self._order)
        if target_layer is None:
            return
        source_layer = layer_of_module(self._source_module, self._order)
        if source_layer is None:
            source_layer = self._fallback_layer()
        if source_layer == target_layer:
            return
        self._needs_realign = True
        self._project_imports.append((node, target, target_layer))

    def _fallback_layer(self) -> str:
        for layer in reversed(self._order):
            return layer
        return self._order[-1] if self._order else "services"


# ---------------------------------------------------------------------------
# Import rewrite helpers
# ---------------------------------------------------------------------------


def _alias_text(alias: cst.ImportAlias) -> str:
    """Render one import alias with its optional ``as`` binding."""
    base = dotted_name(alias.name)
    if alias.asname is not None:
        return f"{base} as {alias.asname.name.value}"
    return base


def _format_import_names(node: ImportFrom) -> str:
    if node.names is None:
        return ""
    if isinstance(node.names, cst.ImportStar):
        return "*"
    if isinstance(node.names, cst.ImportAlias):
        aliases = [_alias_text(node.names)]
    elif isinstance(node.names, cst.Tuple):
        aliases = [
            _alias_text(elt.value)
            for elt in node.names.elements
            if isinstance(elt, cst.Element) and isinstance(elt.value, cst.ImportAlias)
        ]
    else:
        aliases = [
            _alias_text(alias)
            for alias in node.names
            if isinstance(alias, cst.ImportAlias)
        ]
    return " " + ", ".join(aliases) if aliases else ""


def _rewrite_import(
    *,
    node: cst.ImportFrom | cst.Import,
    target: str,
    source_module: str,
    order: tuple[str, ...],
    package_dirs: frozenset[str],
) -> str | None:
    source_layer = layer_of_module(source_module, order)
    if source_layer is None:
        source_layer = order[-1] if order else "services"
    target_layer = layer_of_module(target, order)
    if target_layer is None:
        return None

    if isinstance(node, Import):
        return None

    source_is_pkg = source_module in package_dirs
    target_is_pkg = target in package_dirs
    if source_is_pkg:
        source_depth = len(source_module.split("."))
    else:
        source_depth = len(source_module.split(".")) - 1
    if target_is_pkg:
        target_depth = len(target.split("."))
    else:
        target_depth = len(target.split(".")) - 1
    common = 0
    src_parts = source_module.split(".")
    tgt_parts = target.split(".")
    for i in range(min(source_depth, target_depth)):
        if src_parts[i] == tgt_parts[i]:
            common += 1
        else:
            break
    ups = source_depth - common
    downs = tgt_parts[common:]
    relative = "." * ups + ".".join(downs) if ups or downs else "."

    if isinstance(node, ImportFrom):
        names = _format_import_names(node)
        return _render_from(relative=relative, names=names)
    return None


def _render_from(*, relative: str, names: str) -> str:
    if names == "*":
        return f"from {relative} import *"
    return f"from {relative} import{names}"


# ---------------------------------------------------------------------------
# Mixin: align imports across all scanned modules
# ---------------------------------------------------------------------------


class FlextInfraCodegenLazyInitImportAlignmentMixin:
    """Align project imports to canonical layer order."""

    def align_imports(
        self,
        *,
        rope_workspace: FlextInfraRopeWorkspace,
        index: m.Infra.RopeWorkspaceIndex,
        project_package: str,
        package_dirs: t.SequenceOf[Path],
        config: m.Infra.LazyInitConfig | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Produce CodegenFilePlans for import realignment."""
        order = (
            tuple(config.import_layer_order)
            if config
            else (
                "settings",
                "config",
                "c",
                "t",
                "p",
                "m",
                "u",
                "base",
                "services",
                "api",
                "cli",
            )
        )
        pkg_dirs_set = frozenset(str(d.resolve()) for d in package_dirs)
        repo_root = rope_workspace.repository_root

        file_plans: list[m.Infra.CodegenFilePlan] = []
        for entry in index.modules_by_path.values():
            if entry.is_package_init:
                continue
            if not entry.module_name:
                continue
            file_path = entry.file_path
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            source_module = entry.module_name
            visitor = _ImportAlignmentVisitor(
                source_module=source_module,
                project_package=project_package,
                order=order,
                package_dirs=pkg_dirs_set,
                file_path=file_path,
            )
            try:
                tree = cst.parse_module(content)
            except cst.ParserSyntaxError:
                continue
            tree.visit(visitor)
            if not visitor.needs_realign():
                continue
            new_content = self._rewrite_module(
                tree=tree,
                visitor=visitor,
                source_module=source_module,
                order=order,
                package_dirs=pkg_dirs_set,
            )
            if new_content is None or new_content == content:
                continue
            before = u.Cli.atomic_read_binary_file_state(file_path, required=False)
            if before.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(before)
            desired = new_content.encode("utf-8")
            plan = m.Infra.CodegenFilePlan(
                project=repo_root,
                path=file_path.resolve(),
                before=before.value,
                desired_content=desired,
                desired_mode=0o644,
            )
            file_plans.append(plan)

        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(file_plans))

    def _rewrite_module(
        self,
        *,
        tree: cst.Module,
        visitor: _ImportAlignmentVisitor,
        source_module: str,
        order: tuple[str, ...],
        package_dirs: frozenset[str],
    ) -> str | None:
        class _ImportRewriteTransformer(cst.CSTTransformer):
            """Replace collected ImportFrom nodes with their realigned forms."""

            def __init__(self, mapping: dict[cst.ImportFrom, str]) -> None:
                self._mapping = mapping

            @override
            def leave_ImportFrom(
                self, original: ImportFrom, updated: ImportFrom
            ) -> cst.ImportFrom:
                replacement = self._mapping.get(original)
                if replacement is None:
                    return updated
                statement = cst.parse_statement(replacement)
                if isinstance(statement, cst.SimpleStatementLine):
                    for inner in statement.body:
                        if isinstance(inner, cst.ImportFrom):
                            return inner
                if isinstance(statement, cst.ImportFrom):
                    return statement
                return updated

        mapping: dict[cst.ImportFrom, str] = {}
        for node, target, _target_layer in visitor.project_imports:
            if not isinstance(node, ImportFrom):
                continue
            replacement = _rewrite_import(
                node=node,
                target=target,
                source_module=source_module,
                order=order,
                package_dirs=package_dirs,
            )
            if replacement is not None:
                mapping[node] = replacement
        if not mapping:
            return None
        rewritten = tree.visit(_ImportRewriteTransformer(mapping))
        if rewritten.code == tree.code:
            return None
        return rewritten.code
