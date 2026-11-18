"""Census object classification, violation building, and impact map — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, p, u


class FlextInfraRefactorCensusObjects:
    """Object classification, violation/key construction, and impact-map results.

    Composed into FlextInfraRefactorCensus via inheritance; self-contained
    (static/cls helpers over report Object/Violation models, no census state).
    """

    @staticmethod
    def _selected_families(family_names: Sequence[str] | None) -> frozenset[str]:
        """Return the selected families.

        Returns:
            The selected families.

        """
        if not family_names:
            return frozenset()
        families = u.Infra.facade_families()
        resolved = {
            (families[name].suffix if name in families else name).lower()
            for name in family_names
        }
        return frozenset(resolved)

    @staticmethod
    def _violation(
        item: p.Infra.Object,
        *,
        kind: str,
        description: str,
    ) -> p.Infra.Violation:
        """Violation.

        Returns:
            The resulting ``m.Infra.Violation``.

        """
        return m.Infra.Violation(
            project=item.project,
            object_name=item.name,
            object_kind=item.kind,
            kind=kind,
            file_path=item.file_path,
            line=item.line,
            description=description,
        )

    @staticmethod
    def unused(item: p.Infra.Object, *, source_project: p.Infra.RopeProject) -> bool:
        """Report a public object with collected evidence of zero references.

        Returns:
            Whether the object is proven unused and is no pytest entry point.

        """
        return (
            item.reference_evidence_collected
            and not item.is_facade_member
            and item.references_count == 0
            and not item.name.startswith("_")
            and not FlextInfraRefactorCensusObjects._is_pytest_entry_point(item)
            and not FlextInfraRefactorCensusObjects._is_published_export(
                item, source_project=source_project
            )
        )

    @staticmethod
    def _is_published_export(
        item: p.Infra.Object, *, source_project: p.Infra.RopeProject
    ) -> bool:
        """Keep package ABI bindings even when Rope sees only typing imports.

        Returns:
            The resulting ``bool``.

        """
        if item.scope_path != item.name:
            return False
        package_name = item.module_name.rpartition(".")[0]
        package_dir = Path(item.file_path).parent
        while package_name:
            init_path = package_dir / c.Infra.INIT_PY
            if init_path.is_file():
                module = u.Infra.resolve_pymodule(
                    source_project,
                    source_project.get_file(
                        init_path.relative_to(
                            Path(source_project.root.real_path)
                        ).as_posix()
                    ),
                )
                for export_name in u.Infra.public_export_names_source(module):
                    module_name, original_name = u.Infra.imported_symbol_binding_source(
                        module.source_code,
                        current_module=package_name,
                        symbol_name=export_name,
                        package_module=True,
                    )
                    if module_name == item.module_name and original_name == item.name:
                        return True
            package_name = package_name.rpartition(".")[0]
            package_dir = package_dir.parent
        return False

    @staticmethod
    def _is_pytest_entry_point(item: p.Infra.Object) -> bool:
        """Return whether the object is a pytest entry point in a test module.

        Pytest discovers ``test_*`` callables in test modules and executes
        them without any in-repository reference, so a zero reference count
        never makes one a removal candidate: census apply would otherwise
        delete the tests it is asked to validate.

        Returns:
            Whether the object is a pytest entry point in a test module.

        """
        return (
            item.kind in {"class", "function", "method"}
            and item.name.startswith(c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX)
            and u.Infra.pytest_test_module(Path(item.file_path))
        )

    @classmethod
    def _removal_candidate(
        cls,
        item: p.Infra.Object,
        *,
        include_unused: bool,
        unused: bool,
    ) -> p.Infra.RemovalCandidate | None:
        """Build a removal candidate for an object.

        Returns:
            The resulting ``m.Infra.RemovalCandidate | None``.

        """
        if include_unused and unused:
            reason, suggested_action = "unused", "delete_object_definition"
        else:
            return None
        return m.Infra.RemovalCandidate(
            project=item.project,
            object_name=item.name,
            object_kind=item.kind,
            file_path=item.file_path,
            line=item.line,
            scope_path=item.scope_path,
            reason=reason,
            suggested_action=suggested_action,
            runtime_reference_sites=item.runtime_reference_sites,
            script_reference_sites=item.script_reference_sites,
        )

    @staticmethod
    def _object_key(item: p.Infra.Object) -> str:
        """Object key.

        Returns:
            The resulting ``str``.

        """
        return f"{item.file_path}:{item.line}:{item.scope_path}:{item.kind}"

    @classmethod
    def _impact_map_results(
        cls,
        report: p.Infra.WorkspaceReport,
    ) -> tuple[p.Infra.Result, ...]:
        """Impact map results.

        Returns:
            The resulting ``tuple[p.Infra.Result, ...],``.

        """
        changes_by_file: MutableMapping[Path, list[str]] = defaultdict(list)
        for candidate in report.removal_candidates:
            source_path = Path(candidate.file_path)
            cls._append_impact_change(
                changes_by_file,
                source_path,
                f"{candidate.suggested_action}: {candidate.object_name} "
                f"({candidate.reason})",
            )
            for site in cls._reference_sites(candidate):
                cls._append_impact_change(
                    changes_by_file,
                    Path(site.file_path),
                    f"remove reference to {candidate.object_name} "
                    f"at line {site.line} ({site.surface})",
                )
        return tuple(
            m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=True,
                changes=tuple(changes_by_file[file_path]),
            )
            for file_path in sorted(changes_by_file, key=Path.as_posix)
        )

    @staticmethod
    def _append_impact_change(
        changes_by_file: Mapping[Path, MutableSequence[str]],
        file_path: Path,
        change: str,
    ) -> None:
        """Append impact change."""
        normalized_path = file_path.resolve()
        if change not in changes_by_file[normalized_path]:
            changes_by_file[normalized_path].append(change)

    @staticmethod
    def _reference_sites(
        candidate: p.Infra.RemovalCandidate,
    ) -> tuple[p.Infra.ReferenceSite, ...]:
        """Return all reference sites for a removal candidate.

        Returns:
            All reference sites for a removal candidate.

        """
        return (*candidate.runtime_reference_sites, *candidate.script_reference_sites)

    @staticmethod
    def _object_reference_sites(
        item: p.Infra.Object | None,
    ) -> tuple[p.Infra.ReferenceSite, ...]:
        """Return the unique reference sites indexed for one census object.

        Returns:
            The deduplicated reference sites of every indexed surface.

        """
        if item is None:
            return ()
        unique: MutableMapping[tuple[str, int, str], p.Infra.ReferenceSite] = {}
        for site in (
            *item.all_reference_sites,
            *item.runtime_reference_sites,
            *item.script_reference_sites,
        ):
            unique.setdefault((site.file_path, site.line, site.surface), site)
        return tuple(unique.values())

    @staticmethod
    def _bound_names(tree: ast.Module) -> frozenset[str]:
        """Return module-level names bound by declarations or imports.

        Returns:
            The names the module already binds at its own scope.

        """
        names: set[str] = set()
        for node in tree.body:
            match node:
                case ast.ClassDef() | ast.FunctionDef() | ast.AsyncFunctionDef():
                    names.add(node.name)
                case ast.Assign():
                    names.update(
                        target.id
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    )
                case ast.AnnAssign(target=ast.Name(id=name)):
                    names.add(name)
                case ast.Import():
                    names.update(
                        alias.asname or alias.name.partition(".")[0]
                        for alias in node.names
                    )
                case ast.ImportFrom():
                    names.update(alias.asname or alias.name for alias in node.names)
                case _:
                    pass
        return frozenset(names)

    @staticmethod
    def _declared_all(tree: ast.Module) -> tuple[str, ...]:
        """Return the literal names declared by the module ``__all__``.

        Returns:
            The declared names, or an empty tuple when ``__all__`` is dynamic.

        """
        for node in tree.body:
            match node:
                case (
                    ast.Assign(
                        targets=[ast.Name(id="__all__")],
                        value=ast.List() | ast.Tuple() | ast.Set() as value,
                    )
                    | ast.AnnAssign(
                        target=ast.Name(id="__all__"),
                        value=ast.List() | ast.Tuple() | ast.Set() as value,
                    )
                ):
                    return tuple(
                        element.value
                        for element in value.elts
                        if isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                    )
                case _:
                    pass
        return ()

    @staticmethod
    def _declared_alias(node: ast.stmt) -> tuple[str, str, str] | None:
        """Return ``(alias, target, kind)`` when the statement only renames.

        Returns:
            The alias binding, or ``None`` for any other statement.

        """
        match node:
            case ast.Assign(targets=[ast.Name(id=alias)], value=ast.Name(id=target)):
                return alias, target, "assignment"
            case ast.AnnAssign(target=ast.Name(id=alias), value=ast.Name(id=target)):
                return alias, target, "assignment"
            case ast.ImportFrom():
                return next(
                    (
                        (imported.asname, imported.name, "import-alias")
                        for imported in node.names
                        if imported.asname is not None
                        and imported.asname != imported.name
                    ),
                    None,
                )
            case _:
                return None

    @staticmethod
    def _forwards_variadics(
        node: ast.FunctionDef | ast.AsyncFunctionDef, call: ast.Call
    ) -> bool:
        """Return whether a call forwards exactly ``*args, **kwargs``.

        Returns:
            True when both variadic parameters are forwarded unchanged.

        """
        vararg, kwarg = node.args.vararg, node.args.kwarg
        if vararg is None or kwarg is None:
            return False
        match call:
            case ast.Call(
                args=[ast.Starred(value=ast.Name(id=star))],
                keywords=[ast.keyword(arg=None, value=ast.Name(id=double))],
            ):
                return star == vararg.arg and double == kwarg.arg
            case _:
                return False

    @classmethod
    def _wrapper_target(cls, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Return the forwarded callable when the function is a pass-through.

        Returns:
            The forwarded callable expression, or an empty string.

        """
        body = cls._behavior(node.body)
        match body:
            case [
                ast.Return(value=ast.Call(func=ast.Name() | ast.Attribute()) as call)
            ]:
                parameters = tuple(argument.arg for argument in node.args.args)
                positional = tuple(
                    argument.id
                    for argument in call.args
                    if isinstance(argument, ast.Name)
                )
                forwarded = (
                    len(positional) == len(call.args)
                    and positional == parameters
                    and not call.keywords
                ) or cls._forwards_variadics(node, call)
                return ast.unparse(call.func) if forwarded else ""
            case _:
                return ""

    @staticmethod
    def _behavior(body: Sequence[ast.stmt]) -> tuple[ast.stmt, ...]:
        """Return the statements of a body without its docstring.

        Returns:
            The body statements that carry behavior or declarations.

        """
        return tuple(
            statement
            for statement in body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        )

    @classmethod
    def _is_ceremony(cls, node: ast.ClassDef) -> bool:
        """Return whether a class holds no behavior beyond one declaration.

        Returns:
            True for an empty class or a single stored declaration.

        """
        if any(
            not (isinstance(base, ast.Name) and base.id == "object")
            for base in node.bases
        ):
            return False
        body = cls._behavior(node.body)
        return not body or (
            len(body) == 1
            and isinstance(body[0], ast.Pass | ast.AnnAssign | ast.Assign)
        )

    @classmethod
    def _module_alias_rows(
        cls,
        path: Path,
        tree: ast.Module,
        module_name: str,
        by_site: Mapping[tuple[str, str], p.Infra.Object],
    ) -> tuple[p.Infra.AliasCensus, ...]:
        """Classify the alias bindings and repeated exports of one module.

        Returns:
            The module's alias rows; only owned cures are ``fixable``.

        """
        declared_all = cls._declared_all(tree)
        bound = cls._bound_names(tree)
        own_classes = frozenset(
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        )
        rows: list[p.Infra.AliasCensus] = []
        for node in tree.body:
            declared = cls._declared_alias(node)
            if declared is None:
                continue
            alias, target, kind = declared
            if alias in c.Infra.CENSUS_FAMILY_NAMES and target in own_classes:
                continue
            if kind == "import-alias" and target in c.Infra.CENSUS_FAMILY_NAMES:
                kind = c.Infra.CENSUS_FAMILY_ALIAS_KIND
            item = by_site.get((str(path), alias))
            users = cls._object_reference_sites(item)
            dynamic = bool(item is not None and item.references_count and not users)
            public = alias in declared_all
            reason = (
                "reference sites not collected"
                if dynamic
                else "public export requires review"
                if public
                else "requires local facade namespace"
                if kind == c.Infra.CENSUS_FAMILY_ALIAS_KIND
                else ""
            )
            rows.append(
                m.Infra.AliasCensus.model_validate({
                    "name": (alias),
                    "canonical": (target),
                    "owner_module": (module_name),
                    "kind": (kind),
                    "users": (users),
                    "fixable": (target in bound and not reason),
                    "reason": (reason),
                    "cure": (c.Infra.CENSUS_ALIAS_CURE),
                }),
            )
        counts = Counter(declared_all)
        rows.extend(
            m.Infra.AliasCensus(
                name=name,
                canonical=name,
                owner_module=module_name,
                kind="all-entry",
                reason="duplicate __all__ entry belongs to the generator",
                cure=c.Infra.CENSUS_MANUAL_CURE,
            )
            for name, count in counts.items()
            if count >= c.Infra.CENSUS_MIN_REPEATED_EXPORTS
        )
        return tuple(rows)

    @classmethod
    def _module_shortest_rows(
        cls,
        path: Path,
        tree: ast.Module,
        by_site: Mapping[tuple[str, str], p.Infra.Object],
    ) -> tuple[p.Infra.ShortestFormCensus, ...]:
        """Classify pass-through wrappers and ceremony classes of one module.

        Returns:
            Review-only shortest-form rows for the module.

        """
        rows: list[p.Infra.ShortestFormCensus] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                forwarded = (
                    ""
                    if node.name in c.Infra.CENSUS_ENTRYPOINT_NAMES
                    else cls._wrapper_target(node)
                )
                if forwarded:
                    rows.append(
                        m.Infra.ShortestFormCensus.model_validate({
                            "target": (node.name),
                            "current_form": (f"def {node.name}"),
                            "canonical_form": (forwarded),
                            "kind": ("wrapper"),
                            "users": (
                                cls._object_reference_sites(
                                    by_site.get((str(path), node.name))
                                )
                            ),
                            "reason": ("requires delegation proof"),
                            "cure": (c.Infra.CENSUS_MANUAL_CURE),
                        }),
                    )
            elif isinstance(node, ast.ClassDef) and cls._is_ceremony(node):
                rows.append(
                    m.Infra.ShortestFormCensus.model_validate({
                        "target": (node.name),
                        "current_form": (f"class {node.name}"),
                        "canonical_form": ("owner value or type"),
                        "kind": ("ceremony"),
                        "users": (
                            cls._object_reference_sites(
                                by_site.get((str(path), node.name))
                            )
                        ),
                        "reason": ("ceremony class requires owner review"),
                        "cure": (c.Infra.CENSUS_MANUAL_CURE),
                    }),
                )
        return tuple(rows)

    @classmethod
    def _duplicate_rows(
        cls, duplicates: Sequence[p.Infra.DuplicateGroup]
    ) -> tuple[p.Infra.DuplicateCensus, ...]:
        """Project duplicate groups into rows; only identity groups are fixable.

        Returns:
            One row per duplicate group with its elected canonical owner.

        """
        rows: list[p.Infra.DuplicateCensus] = []
        for group in duplicates:
            users: MutableMapping[tuple[str, int, str], p.Infra.ReferenceSite] = {}
            for definition in group.definitions:
                for site in cls._object_reference_sites(definition):
                    users.setdefault((site.file_path, site.line, site.surface), site)
            fixable = group.value_identical and not group.semantic_candidate
            reason = (
                ""
                if fixable
                else "structural duplicate requires review"
                if group.semantic_candidate
                else "payloads differ"
            )
            rows.append(
                m.Infra.DuplicateCensus.model_validate({
                    "name": (group.name),
                    "kind": (group.kind),
                    "canonical_owner": (group.canonical),
                    "modules": (
                        tuple(
                            sorted({
                                definition.module_name
                                for definition in group.definitions
                            })
                        )
                    ),
                    "payload_fingerprint": (
                        next(
                            (
                                definition.payload_fingerprint
                                for definition in group.definitions
                            ),
                            "",
                        )
                    ),
                    "users": (tuple(users.values())),
                    "fixable": (fixable),
                    "reason": (reason),
                    "cure": (
                        c.Infra.CENSUS_DUPLICATE_CURE
                        if fixable
                        else c.Infra.CENSUS_MANUAL_CURE
                    ),
                }),
            )
        return tuple(rows)

    @classmethod
    def extermination_rows(
        cls,
        *,
        sources: Mapping[Path, str],
        objects: Sequence[p.Infra.Object],
        duplicates: Sequence[p.Infra.DuplicateGroup],
        census_kinds: frozenset[str] | None,
    ) -> tuple[
        tuple[p.Infra.AliasCensus, ...],
        tuple[p.Infra.DuplicateCensus, ...],
        tuple[p.Infra.ShortestFormCensus, ...],
    ]:
        """Classify aliases, duplicate declarations and shortest-form defects.

        The rows consume the existing inventory and duplicate groups; ``fixable``
        is true only where ``ban-compat-alias`` or ``duplicate-apply`` already
        own the cure. Generated projections and package initializers are skipped.

        Returns:
            Alias, duplicate and shortest-form rows selected by ``census_kinds``.

        """

        def wanted(selectors: frozenset[str]) -> bool:
            return not census_kinds or bool(census_kinds & selectors)

        by_site = {(item.file_path, item.name): item for item in objects}
        modules = {Path(item.file_path): item.module_name for item in objects}
        aliases: list[p.Infra.AliasCensus] = []
        shortest: list[p.Infra.ShortestFormCensus] = []
        for path, source in sorted(sources.items()):
            if path.name == c.Infra.INIT_PY or source.lstrip().startswith(
                c.Infra.AUTOGEN_HEADER
            ):
                continue
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            if wanted(c.Infra.CENSUS_ALIAS_SELECTORS):
                aliases.extend(
                    cls._module_alias_rows(
                        path, tree, modules.get(path, path.stem), by_site
                    )
                )
            if wanted(c.Infra.CENSUS_SHORTEST_SELECTORS):
                shortest.extend(cls._module_shortest_rows(path, tree, by_site))
        duplicate_rows = (
            cls._duplicate_rows(duplicates)
            if wanted(c.Infra.CENSUS_DUPLICATE_SELECTORS)
            else ()
        )
        return tuple(aliases), duplicate_rows, tuple(shortest)

    @staticmethod
    def cure_command(cure: str) -> str:
        """Map a cure owner to its individual validation command.

        Returns:
            The command an owner runs before any batch window.

        """
        return c.Infra.CENSUS_CURE_COMMANDS.get(cure, c.Infra.CENSUS_MANUAL_CURE)

    @staticmethod
    def _is_flext_owned(value: p.ModuleOwned) -> bool:
        """Return True iff `value`'s defining module is in the flext package tree.

        Used to filter the parent inventory so that builtin attributes
        inherited by str/int/dict/list constants do not pollute collision
        candidates with names like `count`, `index`, `replace`, etc.

        Returns:
            True iff `value`'s defining module is in the flext package tree.

        """
        module_name = getattr(value, "__module__", "")
        if not isinstance(module_name, str):
            return False
        return module_name.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)


__all__: list[str] = ["FlextInfraRefactorCensusObjects"]
