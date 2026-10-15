"""Canonical FLEXT import-law enforcement engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import override

import libcst as cst
from libcst.helpers import get_full_name_for_node
from libcst.metadata import MetadataWrapper, QualifiedNameProvider, ScopeProvider

from flext_infra import c, m, t, u
from flext_infra.refactor import (
    FlextInfraImportNormalizationPlacementMixin,
    FlextInfraImportNormalizationRoutesMixin,
)


class FlextInfraImportNormalization(
    FlextInfraImportNormalizationRoutesMixin,
    FlextInfraImportNormalizationPlacementMixin,
):
    """Rewrite one module's imports into the FLEXT import law.

    The law (operator-ruling-2026-10-08-import-law), applied to every module
    of a namespace (the source package or an internal tier such as
    ``tests``) except the generated package initializers:

    1. Every import lives at module level; ``try/except ImportError`` guards
       become plain imports.
    2. Imports follow the tooling layer order (settings, config, c, t, p, m,
       u, other, base, services, api, cli): a reverse import read only in
       annotations moves under ``if TYPE_CHECKING:``; a reverse import read
       at runtime keeps its place and its finding, for manual repair.
    3. A root alias (facade and operational letters, ``config``,
       ``settings``, names the namespace root re-exports) binds through the
       module's own namespace root; facade modules keep the letters they
       declare; family packages and runtime facade dependencies retain their
       external providers, and settings/config modules keep their own law.
    4. A concrete object binds through the nearest package ``__init__`` that
       publishes it lazily.
    5. A root alias the module reads but binds nowhere is imported from its
       namespace root; an alias imported from the module's own root that the
       module also defines is dropped.

    ``make mod`` runs it over every governed file; the ``make fix`` lint
    recipe ``normalize-imports`` runs it over each file Ruff reports for
    ``import-outside-top-level``, so both verbs converge on one fixed point.
    """

    @classmethod
    def apply_files(cls, project_root: Path, files: t.SequenceOf[Path]) -> bool:
        """Normalize every given file; return whether any source changed.

        Returns:
            Whether at least one file changed.

        """
        changed = False
        published = 0
        u.Infra._codemod_progress(
            f"import normalization start project={project_root} files={len(files)}",
        )
        import_graph, _modules = u.Infra.project_import_graph(project_root)
        due = 0.0
        for ordinal, file_path in enumerate(files, start=1):
            identity = (
                f"project={project_root} file={file_path} "
                f"position={ordinal}/{len(files)}"
            )
            source = file_path.read_text(encoding=c.DEFAULT_ENCODING)
            if source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            due = u.Infra._codemod_progress(
                f"import normalization semantic {identity}",
                due,
            )
            normalized = cls.normalize_source(
                project_root=project_root,
                file_path=file_path,
                source=source,
                import_graph=import_graph,
            )
            candidate = normalized if normalized is not None else source
            due = u.Infra._codemod_progress(
                f"import normalization format {identity}",
                due,
            )
            candidate = u.Infra.normalize_source(
                project_root,
                file_path,
                candidate,
            ).unwrap()
            if candidate != source:
                due = u.Infra._codemod_progress(
                    f"import normalization publish {identity}",
                    due,
                )
                file_path.write_text(candidate, encoding=c.DEFAULT_ENCODING)
                changed = True
                published += 1
        u.Infra._codemod_progress(
            f"import normalization finish project={project_root} "
            f"files={len(files)} published={published}",
        )
        return changed

    @classmethod
    def normalize_source(
        cls,
        *,
        project_root: Path,
        file_path: Path,
        source: str,
        import_graph: t.MappingKV[str, frozenset[str]] | None = None,
    ) -> str | None:
        """Return the canonical form of one module, or ``None`` when unchanged.

        Returns:
            The rewritten source, or ``None`` when the module is out of scope
            or already canonical.

        Raises:
            ValueError: If ``root_exports is None``.

        """
        if file_path.name == c.Infra.INIT_PY:
            return None
        located = u.Infra.import_namespace(project_root, file_path)
        if located is None:
            return None
        namespace_dir, module = located
        root_exports = u.Infra.import_lazy_exports(project_root, namespace_dir.name)
        if root_exports is None:
            msg = f"{namespace_dir} is a namespace without an owned package init"
            raise ValueError(msg)
        if import_graph is None:
            import_graph, _modules = u.Infra.project_import_graph(project_root)
        facade_dependencies = u.Infra.import_facade_dependencies(
            module,
            root_exports,
            import_graph,
        )
        current = cls._unalias_imports(state_scope=namespace_dir.name, source=source)
        for _ in range(c.Infra.IMPORT_NORMALIZATION_MAX_PASSES):
            tree = ast.parse(current, filename=str(file_path))
            state = m.Infra.ImportLawPass(
                scope=m.Infra.ImportLawScope(
                    project_root=project_root.resolve(),
                    file_path=file_path,
                    namespace_dir=namespace_dir,
                    module=module,
                    layer=u.Infra.module_import_layer(module),
                    own_exports=cls._declared_exports(tree),
                    facade_dependencies=facade_dependencies,
                    family_letter=cls._family_letter(namespace_dir, file_path),
                    direct_imports=u.Infra.import_direct_module(
                        namespace_dir,
                        file_path,
                    )
                    or u.Infra.import_bootstrap_dependency(
                        namespace_dir.name,
                        module,
                        import_graph,
                    ),
                ),
                tree=tree,
                parents=cls._parent_map(tree),
                bindings=cls._module_bindings(tree),
                root_exports=root_exports,
            )
            updated = cls._one_pass(state, current)
            if updated is None:
                break
            current = updated
        return current if current != source else None

    @staticmethod
    def _unalias_imports(*, state_scope: str, source: str) -> str:
        """Remove own-package aliases, refusing capture of shadowed bindings.

        Returns:
            Source with references bound to the imported identity renamed.

        """
        tree = ast.parse(source)
        selected = {
            (alias.asname, f"{node.module}.{alias.name}"): alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".")[0] == state_scope
            for alias in node.names
            if alias.asname is not None
            and alias.asname != alias.name
            and alias.asname not in c.Infra.ALIAS_NAMES
        }
        if not selected:
            return source

        class _Unalias(cst.CSTTransformer):
            METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)

            @override
            def leave_Name(
                self,
                original_node: cst.Name,
                updated_node: cst.Name,
            ) -> cst.Name:
                names = tuple(
                    self.get_metadata(QualifiedNameProvider, original_node, ())
                )
                targets = {
                    selected[key]
                    for name in names
                    if (key := (original_node.value, name.name)) in selected
                }
                if not targets:
                    return updated_node
                if len(targets) != 1 or len(names) != 1:
                    msg = f"ambiguous imported alias: {original_node.value}"
                    raise ValueError(msg)
                target = next(iter(targets))
                if target == original_node.value:
                    return updated_node
                scope = self.get_metadata(ScopeProvider, original_node, None)
                if scope is None:
                    msg = f"import alias reference has no scope: {original_node.value}"
                    raise ValueError(msg)
                if scope[target]:
                    msg = f"import alias destination is occupied: {target}"
                    raise ValueError(msg)
                return updated_node.with_changes(value=target)

            @override
            def leave_ImportFrom(
                self,
                original_node: cst.ImportFrom,
                updated_node: cst.ImportFrom,
            ) -> cst.ImportFrom:
                module = (
                    get_full_name_for_node(original_node.module)
                    if original_node.module is not None
                    else None
                )
                if isinstance(updated_node.names, cst.ImportStar):
                    return updated_node
                return updated_node.with_changes(
                    names=tuple(
                        alias.with_changes(asname=None)
                        if alias.asname is not None
                        and isinstance(alias.asname.name, cst.Name)
                        and (
                            alias.asname.name.value,
                            f"{module}.{get_full_name_for_node(alias.name)}",
                        )
                        in selected
                        else alias
                        for alias in updated_node.names
                    )
                )

        return MetadataWrapper(cst.parse_module(source)).visit(_Unalias()).code

    @classmethod
    def _one_pass(cls, state: m.Infra.ImportLawPass, source: str) -> str | None:
        """Apply the first rewrite category that changes the module.

        Every category's edits are computed against the text they mutate, so
        categories never share a pass; the caller re-parses between passes.

        Returns:
            The rewritten source, or ``None`` when every category is a no-op.

        Raises:
            ValueError: If one category plans overlapping edits.

        """
        lines = source.splitlines()
        cls._validate_import_boundary(state)
        builders = (
            lambda: cls._relative_import_edits(state, lines),
            lambda: cls._guard_edits(state.tree, lines),
            lambda: cls._placement_edits(state, lines),
            lambda: cls._route_edits(state, lines),
            lambda: cls._root_alias_binding_edits(state, lines),
            lambda: cls._layer_order_edits(state, lines),
        )
        for build in builders:
            edits = build()
            if not edits:
                continue
            applied = cls._apply_edits(source, edits)
            if applied is None:
                msg = f"{state.scope.file_path}: overlapping import-law edits {edits}"
                raise ValueError(msg)
            if applied != source:
                return applied
        return None

    @classmethod
    def _validate_import_boundary(cls, state: m.Infra.ImportLawPass) -> None:
        """Reject forbidden dependencies before hoisting, deferral or routing.

        Raises:
            ValueError: If a layer-zero module imports its own namespace or a
                family binds its own facade, including TYPE_CHECKING imports.

        """
        scope = state.scope
        role = u.Infra.import_module_role(scope.module)
        for node in cls._iter_imports(state.tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                continue  # The next pass validates the absolute rewrite.
            for alias in node.names:
                target = (
                    node.module or ""
                    if isinstance(node, ast.ImportFrom)
                    else alias.name
                )
                if target.split(".")[0] != scope.namespace:
                    continue
                if role == "layer0":
                    msg = (
                        f"{scope.file_path}: layer-zero module imports its own "
                        f"namespace: {target}"
                    )
                    raise ValueError(msg)
                if role != "family" or scope.family_letter is None:
                    continue
                provider = (
                    state.root_exports.get(alias.name, "")
                    if isinstance(node, ast.ImportFrom) and target == scope.namespace
                    else target
                )
                family = u.Infra.facade_families()[scope.family_letter]
                if provider not in {
                    f"{scope.namespace}.{family.module}",
                    f"{scope.namespace}.{scope.family_letter}",
                } and not (
                    target == scope.namespace and alias.name == scope.family_letter
                ):
                    continue
                if (
                    isinstance(node, ast.ImportFrom)
                    and target == scope.namespace
                    and node in state.tree.body
                    and any(
                        isinstance(statement, ast.Assign | ast.AnnAssign)
                        and (alias.asname or alias.name)
                        in cls._module_bindings(
                            ast.Module(body=[statement], type_ignores=[]),
                        )
                        for statement in state.tree.body
                    )
                ):
                    # The existing binding repair removes this redundant import.
                    continue
                msg = (
                    f"{scope.file_path}: family imports its own facade: "
                    f"{target}.{alias.name}"
                )
                raise ValueError(msg)

    @staticmethod
    def _declared_exports(tree: ast.Module) -> frozenset[str]:
        """Return the names one module declares in its literal ``__all__``.

        Returns:
            The resulting ``frozenset[str]``.

        """
        for node in tree.body:
            target = (
                node.targets[0]
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                else node.target
                if isinstance(node, ast.AnnAssign)
                else None
            )
            value = node.value if isinstance(node, ast.Assign | ast.AnnAssign) else None
            if (
                isinstance(target, ast.Name)
                and target.id == "__all__"
                and isinstance(value, ast.List | ast.Tuple)
            ):
                return frozenset(
                    element.value
                    for element in value.elts
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                )
        return frozenset()

    @staticmethod
    def _family_letter(namespace_dir: Path, file_path: Path) -> str | None:
        """Return the facade letter of the family package holding one module.

        Returns:
            The family letter, or ``None`` outside every family package.

        """
        relative = file_path.resolve().relative_to(namespace_dir.resolve())
        return next(
            (
                letter
                for part in (*relative.parts[:-1], relative.stem)
                for letter, family in u.Infra.facade_families().items()
                if part in {family.directory, family.module}
            ),
            None,
        )


__all__: list[str] = ["FlextInfraImportNormalization"]
