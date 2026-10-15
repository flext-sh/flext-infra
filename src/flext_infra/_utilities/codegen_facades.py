"""Consumer-driven projection of utility, protocol and model facade owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Literal, override

from libcst import (
    Arg,
    ClassDef,
    Comma,
    CSTTransformer,
    ImportFrom,
    ImportStar,
    LeftParen,
    Module,
    Name,
    ParenthesizedWhitespace,
    RightParen,
    SimpleWhitespace,
    parse_expression,
    parse_module,
)
from libcst.codemod import CodemodContext
from libcst.codemod.commands.rename import RenameCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)


class FlextInfraUtilitiesCodegenFacades:
    """Project local ``u``, ``p`` and ``m`` owners selected by package consumers."""

    @classmethod
    def render_type_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        sources: t.MappingKV[Path, str],
    ) -> str:
        """Project a complete exported type owner without duplicating its body.

        Only the existing class/t export contract is supported. Ambiguous owners
        or extra public declarations fail rather than being silently discarded.

        Returns:
            Generated facade source inheriting its complete declared type owner.

        Raises:
            ValueError: If the facade lacks module documentation, declares an
                unsupported class, exports, or declarations, or does not resolve
                to exactly one full exported type owner.

        """
        source = sources[facade_path]
        tree = ast.parse(source, filename=str(facade_path))
        if ast.get_docstring(tree) is None:
            msg = f"type facade has no module documentation: {facade_path}"
            raise ValueError(msg)
        facade, _namespace = cls._facade_classes(tree, facade_path)
        if facade.decorator_list or facade.type_params:
            msg = f"unsupported type facade class: {facade_path}"
            raise ValueError(msg)
        exports = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        )
        if (
            len(exports) != 1
            or exports[0].value is None
            or set(ast.literal_eval(exports[0].value)) != {facade.name, "t"}
        ):
            msg = f"unsupported type facade exports: {facade_path}"
            raise ValueError(msg)
        bindings = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "t"
            and isinstance(node.value, ast.Name)
            and node.value.id == facade.name
        )
        if len(bindings) != 1 or any(
            not isinstance(node, ast.Import | ast.ImportFrom)
            and not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            and not (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Name)
                and node.test.id == "TYPE_CHECKING"
                and not node.orelse
                and all(
                    isinstance(item, ast.Import | ast.ImportFrom) for item in node.body
                )
            )
            and node is not facade
            and node not in exports
            and node not in bindings
            for node in tree.body
        ):
            msg = f"unsupported type facade declarations: {facade_path}"
            raise ValueError(msg)
        directory = FlextInfraUtilitiesCodegenNamespace.facade_families()["t"].directory
        owners = tuple(
            path
            for path, content in sources.items()
            if path.is_relative_to(pkg_dir / directory)
            and path.name != c.Infra.INIT_PY
            and "t"
            in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_source(
                content, filename=str(path)
            )
            and any(
                isinstance(binding, ast.Assign)
                and isinstance(binding.value, ast.Name)
                and binding.value.id == facade.name
                for binding in (
                    FlextInfraUtilitiesRopeModulePatch.runtime_alias_bindings(
                        content,
                        alias="t",
                    )
                )
            )
            and any(
                isinstance(node, ast.ClassDef) and node.name == facade.name
                for node in ast.parse(content, filename=str(path)).body
            )
        )
        if len(owners) != 1:
            msg = f"expected one full exported type owner: {facade_path}"
            raise ValueError(msg)
        module = (
            owners[0].relative_to(pkg_dir).with_suffix("").as_posix().replace("/", ".")
        )
        alias = f"_{facade.name}"
        rendered = (
            f"{ast.get_source_segment(source, tree.body[0])}\n\n"
            "# Generated type facade; declarations belong to "
            f"{pkg_dir.name}.{module}.\n"
            f"from {pkg_dir.name}.{module} import {facade.name} as {alias}\n\n\n"
            f"class {facade.name}({alias}):\n"
            '    """Public type facade inheriting its '
            'complete canonical owner."""\n\n\n'
            f"t = {facade.name}\n\n"
            f"{ast.get_source_segment(source, exports[0])}\n"
        )
        return cls._generated_facade(pkg_dir, rendered, family="t")

    @staticmethod
    def facade_module_path(pkg_dir: Path, family: str) -> Path | None:
        """Return the package module that declares facade letter ``family``.

        The owner of a facade letter is the module that publishes it in its own
        ``__all__`` (generator law p.1); it is derived from the package, never
        from a letter-to-filename table. ``None`` means no module declares it.

        Returns:
            The declaring package module, or ``None`` when none declares it.

        Raises:
            ValueError: If multiple package modules declare the same facade letter.

        """
        owners = tuple(
            module
            for module in sorted(pkg_dir.glob(c.Infra.EXT_PYTHON_GLOB))
            if module.name != c.Infra.INIT_PY
            and family
            in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_source(
                module.read_text(encoding=c.DEFAULT_ENCODING),
                filename=str(module),
            )
        )
        if len(owners) > 1:
            message = (
                f"facade letter {family!r} is declared by more than one module "
                f"in {pkg_dir}: {[owner.name for owner in owners]}"
            )
            raise ValueError(message)
        return owners[0] if owners else None

    @classmethod
    def render_utility_facade(
        cls,
        pkg_dir: Path,
        *,
        family: Literal["c", "u", "p", "m"] = "u",
    ) -> str | None:
        """Render uniquely discovered utility, protocol or model owners.

        Package consumers select called utility methods or referenced protocol
        and model members through imports resolved to this package's facade.
        Discovery scans Python modules recursively in the configured private
        family and follows owner base chains. Existing namespace runtime bindings,
        including simple assignment aliases, are retained rather than replaced.
        Missing owners contribute imports and bases only; a namespace without
        bases is updated through its unique concrete-syntax class span.
        Rendering returns source without publishing it.

        Returns:
            Rendered source, including unchanged source when no owner is added,
            or ``None`` when there is no private family to project or an empty
            owner directory has no declaring facade.

        Raises:
            ValueError: If facade declarations or required owners are ambiguous,
                a nonempty private family has no facade, the facade class shape
                or base expression is unsupported, import resolution fails, or
                base insertion cannot identify a valid source span.

        """
        facade_path = cls.facade_module_path(pkg_dir, family)
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        # Why: only owners-without-facade is incomplete -- the owners would have
        # no public surface at all. A facade with no owners directory is the
        # legitimate pure re-export shape this same generator emits for a package
        # that adds no local utilities (src/flext: `class FlextRootUtilities(u)`),
        # and there is simply nothing to project onto it.
        if not owners_dir.is_dir():
            return None
        if facade_path is None:
            # Conform preflights its family directories before rendering files.
            # An empty directory contains no owner requiring a public surface.
            if not any(owners_dir.iterdir()):
                return None
            message = f"utility owners in {pkg_dir} have no public facade"
            raise ValueError(message)
        source: str = facade_path.read_text(encoding=c.DEFAULT_ENCODING)
        match family:
            case "c" | "m":
                rendered = cls._render_declared_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    family=family,
                )
            case "u" | "p":
                rendered = cls._render_interface_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    family=family,
                )
        return cls._generated_facade(pkg_dir, rendered, family=family)

    @classmethod
    def _generated_facade(
        cls,
        pkg_dir: Path,
        source: str,
        *,
        family: Literal["c", "t", "u", "p", "m"],
    ) -> str:
        """Publish lawful composition and identity-proven lazy-package imports.

        Returns:
            Generated composition carrying the canonical ownership marker.

        Raises:
            ValueError: If authored declarations or unpublished imports remain.

        """
        tree = ast.parse(source)
        sources, declarations = cls._declared_sources(
            pkg_dir,
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory,
        )
        facade, namespace = cls._facade_classes(tree, pkg_dir)
        aliases = {declaration.qualified_base for declaration in declarations}
        for statement in tree.body:
            if (
                statement is facade
                or isinstance(statement, ast.Import | ast.ImportFrom)
                or (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                )
            ):
                continue
            value = (
                statement.value
                if isinstance(
                    statement,
                    ast.Assign | ast.AnnAssign,
                )
                else None
            )
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else (statement.target,)
                if isinstance(statement, ast.AnnAssign)
                else ()
            )
            if (
                targets
                and all(isinstance(target, ast.Name) for target in targets)
                and (
                    all(
                        isinstance(target, ast.Name) and target.id == "__all__"
                        for target in targets
                    )
                    or (isinstance(value, ast.Name) and value.id == facade.name)
                )
            ):
                continue
            message = f"Facade preserves authored module declaration: {pkg_dir}:{statement.lineno}"
            raise ValueError(message)
        for owner in (facade, namespace) if namespace is not facade else (facade,):
            for statement in owner.body:
                if (
                    isinstance(statement, ast.Pass)
                    or (statement is namespace and namespace is not facade)
                    or (
                        isinstance(statement, ast.Expr)
                        and isinstance(statement.value, ast.Constant)
                        and isinstance(statement.value.value, str)
                    )
                    or (
                        isinstance(statement, ast.Assign)
                        and isinstance(statement.value, ast.Name)
                        and statement.value.id in aliases
                        and all(
                            isinstance(target, ast.Name) for target in statement.targets
                        )
                    )
                ):
                    continue
                message = (
                    f"Facade preserves authored declaration before generation: "
                    f"{pkg_dir}:{owner.name}:{statement.lineno}"
                )
                raise ValueError(message)
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            module = f"{pkg_dir.name}.{node.module}" if node.level else node.module
            if not module.startswith(f"{pkg_dir.name}."):
                continue
            provider_state = sources.get(module)
            if provider_state is None:
                message = f"Generated facade has unresolved owned import: {module}"
                raise ValueError(message)
            leaf, provider = provider_state
            if leaf.name == c.Infra.INIT_PY:
                continue
            exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                provider,
            )
            for alias in node.names:
                if alias.name not in exports:
                    message = (
                        f"Generated facade imports unpublished owner: "
                        f"{module}.{alias.name}"
                    )
                    raise ValueError(message)
                source = (
                    RenameCommand(
                        CodemodContext(full_package_name=pkg_dir.name),
                        old_name=f"{module}.{alias.name}",
                        new_name=f"{module.rpartition('.')[0]}.{alias.name}",
                    )
                    .transform_module(parse_module(source))
                    .code
                )
        if source.startswith(c.Infra.AUTOGEN_HEADERS):
            return source
        return f"{c.Infra.AUTOGEN_HEADER}\n{source}"

    @classmethod
    def _render_interface_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        source: str,
        *,
        family: Literal["u", "p"],
    ) -> str:
        """Validate consumer ownership before composing an interface facade.

        Returns:
            The projected source with its existing namespace bindings preserved.

        Raises:
            ValueError: If a consumer requires competing provider declarations.

        """
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        owners, ancestors = cls._utility_owners(owners_dir, family=family)
        reachable = cls._reachable_bases(
            tuple(cls._base_name(base) for base in namespace.bases),
            ancestors,
        )
        additions: list[t.Pair[str, str]] = []
        declared = {
            member.name
            for member in namespace.body
            if isinstance(member, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        }
        declared.update(
            target.id
            for member in namespace.body
            if isinstance(member, ast.Assign | ast.TypeAlias)
            or (isinstance(member, ast.AnnAssign) and member.value is not None)
            for target in (
                member.targets
                if isinstance(member, ast.Assign)
                else [
                    member.name if isinstance(member, ast.TypeAlias) else member.target,
                ]
            )
            if isinstance(target, ast.Name)
        )
        for method in sorted(
            cls._required_methods(
                pkg_dir,
                facade_path,
                nested_namespace=namespace is not facade,
                namespace=namespace.name,
                family=family,
            ),
        ):
            if method in declared:
                continue
            candidates = tuple(
                (module, class_name)
                for module, class_name, methods in owners
                if method in methods
            )
            if not candidates or any(
                class_name in reachable for _module, class_name in candidates
            ):
                continue
            if len(candidates) != 1:
                message = (
                    f"ambiguous {family}.{namespace.name} owner for {method}: "
                    + ", ".join(f"{module}:{name}" for module, name in candidates)
                )
                raise ValueError(message)
            module, class_name = candidates[0]
            additions.append((module, class_name))
            reachable.update(cls._reachable_bases((class_name,), ancestors))
        if family == "u":
            return cls._render_declared_facade(
                pkg_dir,
                facade_path,
                source,
                family=family,
            )
        if not additions:
            return source
        source = cls._insert_imports(
            source,
            additions,
            package=pkg_dir.name,
            family=family,
        )
        _, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        return cls._insert_bases(source, namespace, additions)

    @classmethod
    def _render_declared_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        source: str,
        *,
        family: Literal["c", "m", "u"],
    ) -> str:
        """Compose explicitly exported declarations without reverse family imports.

        Returns:
            A facade whose direct owners preserve the existing source C3 order.

        """
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        sources, declarations = cls._declared_sources(pkg_dir, owners_dir)
        source = cls._rebind_declared_imports(pkg_dir, owners_dir, source, declarations)
        sources[f"{pkg_dir.name}.{facade_path.stem}"] = (facade_path, source)
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        independent = cls._independent_publishers(pkg_dir, owners_dir, sources)
        with FlextInfraUtilitiesRopeCore.open_import_project(pkg_dir.parent) as project:
            retired = cls._retired_owned_bases(
                project,
                sources,
                pkg_dir,
                owners_dir,
                facade_path,
                namespace,
                {item.qualified_base for item in declarations},
            )
        if retired:
            wrapper = MetadataWrapper(parse_module(source))
            owner = cls._facade_namespace_cst(wrapper, namespace)
            context = CodemodContext(
                full_package_name=pkg_dir.name,
                wrapper=wrapper,
            )
            retained_bases: list[Arg] = []
            for base in owner.bases:
                expression = ast.unparse(
                    ast.parse(
                        wrapper.module.code_for_node(base.value),
                        mode="eval",
                    ).body,
                )
                if expression in retired:
                    RemoveImportsVisitor.remove_unused_import_by_node(
                        context,
                        base.value,
                    )
                else:
                    retained_bases.append(base)
            candidate = wrapper.module.deep_replace(
                owner,
                owner.with_changes(bases=tuple(retained_bases)),
            )
            if not isinstance(candidate, Module):
                message = "Retired facade-base projection did not preserve the module"
                raise TypeError(message)
            source = candidate.code
            sources[f"{pkg_dir.name}.{facade_path.stem}"] = (facade_path, source)
            facade, namespace = cls._facade_classes(
                ast.parse(source, filename=str(facade_path)),
                facade_path,
            )
        else:
            context = CodemodContext(full_package_name=pkg_dir.name)
        declarations, declared_names, bound_namespace = cls._declared_facade_contract(
            independent,
            declarations,
            facade,
            namespace,
            facade_target=f"{pkg_dir.name}.{facade_path.stem}",
        )
        ordered = cls._declared_facade_order(pkg_dir, sources, declarations)
        existing = tuple(cls._base_name(base) for base in namespace.bases)
        if existing == ordered and not retired:
            return cls._wrap_facade_imports(source)
        if bound_namespace:
            cls._declared_facade_stale_imports(context, source, declared_names)
        cls._declared_facade_declared_imports(
            context,
            declarations,
            declared_names,
            existing,
        )
        return cls._declared_facade_render(context, source, namespace, ordered)

    @classmethod
    def _declared_facade_contract(
        cls,
        independent: frozenset[str],
        declarations: list[m.Infra.SourceClassReference],
        facade: ast.ClassDef,
        namespace: ast.ClassDef,
        *,
        facade_target: str,
    ) -> tuple[list[m.Infra.SourceClassReference], set[str], bool]:
        """Filter declared owners, then append the namespace's own base owners.

        Returns:
            The final declarations, their qualified names, and whether the
            facade binds the namespace through assignment.

        """
        filtered = [
            item
            for item in declarations
            if item.qualified_base not in independent
            or item.qualified_base in {cls._base_name(base) for base in namespace.bases}
        ]
        declared_names = {item.qualified_base for item in filtered}
        bound_namespace = namespace is facade and any(
            isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Name)
            and statement.value.id in declared_names
            and any(
                isinstance(target, ast.Name)
                and target.id[0].isupper()
                and statement.value.id.endswith(target.id)
                for target in statement.targets
            )
            for statement in facade.body
        )
        if bound_namespace:
            filtered.clear()
        filtered.extend(
            m.Infra.SourceClassReference(
                target=facade_target,
                attributes=tuple(
                    ast.unparse(
                        base.value if isinstance(base, ast.Subscript) else base
                    ).split(".")
                ),
                qualified_base=ast.unparse(base),
            )
            for base in namespace.bases
            if cls._base_name(base) not in declared_names
        )
        return filtered, declared_names, bound_namespace

    @classmethod
    def _declared_facade_order(
        cls,
        pkg_dir: Path,
        sources: t.MutableMappingKV[str, t.Pair[Path, str]],
        declarations: list[m.Infra.SourceClassReference],
    ) -> t.SequenceOf[str]:
        """Resolve the C3 base order of the facade's declared owners.

        Returns:
            The ordered base names the facade namespace must compose.

        """
        with FlextInfraUtilitiesRopeCore.open_import_project(pkg_dir.parent) as project:
            return FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_order(
                project,
                sources,
                declarations,
            )

    @staticmethod
    def _declared_facade_stale_imports(
        context: CodemodContext,
        source: str,
        declared_names: set[str],
    ) -> None:
        """Drop imports of names the facade now binds through assignment."""
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                for alias in node.names:
                    if alias.name in declared_names:
                        RemoveImportsVisitor.remove_unused_import(
                            context,
                            node.module,
                            alias.name,
                        )

    @staticmethod
    def _declared_facade_declared_imports(
        context: CodemodContext,
        declarations: list[m.Infra.SourceClassReference],
        declared_names: set[str],
        existing: tuple[str, ...],
    ) -> None:
        """Register the imports the reordered facade bases require."""
        for item in declarations:
            if (
                item.qualified_base in declared_names
                and item.qualified_base not in existing
            ):
                AddImportsVisitor.add_needed_import(
                    context,
                    item.target,
                    item.qualified_base,
                )

    @classmethod
    def _declared_facade_render(
        cls,
        context: CodemodContext,
        source: str,
        namespace: ast.ClassDef,
        ordered: t.SequenceOf[str],
    ) -> str:
        """Reorder the namespace bases and apply the registered imports.

        Returns:
            The projected facade source.

        Raises:
            ValueError: If the namespace has no unique concrete source span.
            TypeError: If the projection does not preserve the source module.

        """
        wrapper = MetadataWrapper(parse_module(source))
        owner = cls._facade_namespace_cst(wrapper, namespace)
        updated = wrapper.module.deep_replace(
            owner,
            owner.with_changes(bases=cls._declared_facade_bases(owner, ordered)),
        )
        if not isinstance(updated, Module):
            message = "Declared facade projection did not preserve the module"
            raise TypeError(message)
        result = AddImportsVisitor(context).transform_module(updated)
        return cls._wrap_facade_imports(
            RemoveImportsVisitor(context).transform_module(result).code
        )

    @staticmethod
    def _wrap_facade_imports(source: str) -> str:
        """Keep projected imports inside the configured Ruff line budget.

        Returns:
            Source with long single-line from-imports parenthesized.

        """
        module = parse_module(source)

        class WrapImports(CSTTransformer):
            """Wrap each emitted import in a single concrete-syntax traversal."""

            @override
            def leave_ImportFrom(
                self,
                original_node: ImportFrom,
                updated_node: ImportFrom,
            ) -> ImportFrom:
                """Preserve bindings and wrap only imports exceeding the budget.

                Returns:
                    The original import or its parenthesized equivalent.

                """
                if (
                    isinstance(updated_node.names, ImportStar)
                    or "\n" in module.code_for_node(original_node)
                    or len(module.code_for_node(original_node))
                    <= config.Infra.tooling.tools.ruff.line_length
                ):
                    return updated_node
                return updated_node.with_changes(
                    lpar=LeftParen(
                        whitespace_after=ParenthesizedWhitespace(
                            last_line=SimpleWhitespace("    "),
                        ),
                    ),
                    names=tuple(
                        alias.with_changes(
                            comma=Comma(
                                whitespace_after=ParenthesizedWhitespace(
                                    last_line=SimpleWhitespace(
                                        "    "
                                        if index < len(updated_node.names) - 1
                                        else "",
                                    ),
                                ),
                            ),
                        )
                        for index, alias in enumerate(updated_node.names)
                    ),
                    rpar=RightParen(),
                )

        return module.visit(WrapImports()).code

    @staticmethod
    def _declared_facade_bases(
        owner: ClassDef,
        ordered: t.SequenceOf[str],
    ) -> tuple[Arg, ...]:
        """Build the reordered base arguments for the facade namespace.

        Returns:
            One base argument per ordered name, preserving the source C3 order.

        """
        return tuple(
            (
                owner.bases[-1] if index == len(ordered) - 1 else owner.bases[0]
            ).with_changes(value=parse_expression(name))
            if owner.bases
            else Arg(parse_expression(name))
            for index, name in enumerate(ordered)
        )

    @staticmethod
    def _facade_namespace_cst(
        wrapper: MetadataWrapper,
        namespace: ast.ClassDef,
    ) -> ClassDef:
        """Resolve the unique concrete class span of the projected namespace.

        Returns:
            The concrete namespace class.

        Raises:
            ValueError: If the namespace lacks one exact class span.

        """
        owners = tuple(
            node
            for node, span in wrapper.resolve(PositionProvider).items()
            if isinstance(node, ClassDef)
            and span.start.line == namespace.lineno
            and node.name.value == namespace.name
        )
        if len(owners) != 1:
            message = "Facade namespace has no unique concrete source span"
            raise ValueError(message)
        return owners[0]

    @staticmethod
    def _retired_owned_bases(
        project: t.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        pkg_dir: Path,
        owners_dir: Path,
        facade_path: Path,
        namespace: ast.ClassDef,
        declared_names: set[str],
    ) -> frozenset[str]:
        """Retire own bases whose source no longer belongs to this family.

        Upstream inheritance and source-proven current family providers remain.
        Unknown bindings fail instead of being classified by their spelling.

        Returns:
            Existing base expressions whose providers moved out of the family.

        Raises:
            ValueError: If an existing base has no resolved source identity.

        """
        snapshot = FlextInfraUtilitiesRopeRuntime.snapshot_project(
            project,
            dict(sources.values()),
        )
        try:
            resource = snapshot.get_resource(
                facade_path.relative_to(Path(snapshot.root.real_path)).as_posix(),
            )
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(snapshot, resource)
            scope = module.get_scope()
            retired: set[str] = set()
            for base in namespace.bases:
                if FlextInfraUtilitiesCodegenFacades._base_name(base) in declared_names:
                    continue
                expression = base.value if isinstance(base, ast.Subscript) else base
                binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    scope,
                    expression,
                )
                if binding is None:
                    message = (
                        f"Unresolved facade base: {facade_path}:{ast.unparse(base)}"
                    )
                    raise ValueError(message)
                holder, _line = binding.get_definition_location()
                provider = holder.get_resource() if holder is not None else None
                if provider is None:
                    value = binding.get_object()
                    if FlextInfraUtilitiesRopeRuntime.abstract_class(
                        value
                    ) and not FlextInfraUtilitiesRopeRuntime.py_class(value):
                        continue
                    message = f"Facade base has no source owner: {facade_path}:{ast.unparse(base)}"
                    raise ValueError(message)
                path = Path(provider.real_path).resolve()
                if path.is_relative_to(pkg_dir.resolve()) and not path.is_relative_to(
                    owners_dir.resolve(),
                ):
                    retired.add(ast.unparse(base))
            return frozenset(retired)
        finally:
            snapshot.close()

    @staticmethod
    def _rebind_declared_imports(
        pkg_dir: Path,
        owners_dir: Path,
        source: str,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> str:
        """Bind published owner names to their current declaration modules.

        Returns:
            Source with obsolete owned import origins replaced.

        Raises:
            ValueError: If published owner spellings compete.

        """
        owners = {item.qualified_base: item.target for item in declarations}
        if len(owners) != len(declarations):
            message = "Competing declared facade import bindings"
            raise ValueError(message)
        prefix = ".".join(owners_dir.relative_to(pkg_dir.parent).parts)
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            module = f"{pkg_dir.name}.{node.module}" if node.level else node.module
            if module != prefix and not module.startswith(f"{prefix}."):
                continue
            for alias in node.names:
                target = owners.get(alias.name)
                if target is None or target == module:
                    continue
                context = CodemodContext(full_package_name=pkg_dir.name)
                source = (
                    RenameCommand(
                        context,
                        old_name=f"{module}.{alias.name}",
                        new_name=f"{target}.{alias.name}",
                    )
                    .transform_module(parse_module(source))
                    .code
                )
        return source

    @staticmethod
    def _declared_sources(
        pkg_dir: Path,
        owners_dir: Path,
    ) -> t.Pair[
        t.MutableMappingKV[str, t.Pair[Path, str]],
        list[m.Infra.SourceClassReference],
    ]:
        """Capture source identities and explicitly exported family declarations.

        Returns:
            Source snapshots and declared class references.

        Raises:
            ValueError: If distinct publishers compete for a parent facade name.

        """
        sources: t.MutableMappingKV[str, t.Pair[Path, str]] = {}
        declarations: list[m.Infra.SourceClassReference] = []
        for path in sorted(pkg_dir.rglob(c.Infra.EXT_PYTHON_GLOB)):
            content = path.read_text(encoding=c.DEFAULT_ENCODING)
            # Conflict-marked projections belong to recovery, not source analysis.
            if (
                path.name == c.Infra.INIT_PY
                and any(
                    content.startswith(header) for header in c.Infra.AUTOGEN_HEADERS
                )
                and any(line.startswith("<<<<<<<") for line in content.splitlines())
            ):
                continue
            relative = path.relative_to(pkg_dir.parent).with_suffix("")
            module = ".".join(
                relative.parts[:-1] if path.name == c.Infra.INIT_PY else relative.parts
            )
            sources[module] = (path, content)
            # Child packages own their publishers, not the parent facade's names.
            # Keep their snapshots so declared MRO bases still resolve normally.
            if path.parent != owners_dir or path.name == c.Infra.INIT_PY:
                continue
            exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                content
            )
            declarations.extend(
                m.Infra.SourceClassReference(
                    target=module,
                    attributes=(node.name,),
                    qualified_base=node.name,
                )
                for node in ast.parse(content, filename=str(path)).body
                if isinstance(node, ast.ClassDef) and node.name in exports
            )
        # Repeated declarations of one module attribute publish its final binding.
        declarations = list(
            {(item.target, item.attributes): item for item in declarations}.values()
        )
        competing: t.MutableMappingKV[str, list[str]] = {}
        for item in declarations:
            competing.setdefault(item.qualified_base, []).append(
                f"{item.target}:{'.'.join(item.attributes)}"
            )
        if len(competing) != len(declarations):
            message = "Competing declared facade owner names: " + "; ".join(
                f"{name} [{', '.join(owners)}]"
                for name, owners in sorted(competing.items())
                if len(owners) > 1
            )
            raise ValueError(message)
        return sources, declarations

    @staticmethod
    def _independent_publishers(
        pkg_dir: Path,
        owners_dir: Path,
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> frozenset[str]:
        """Find declared owners re-exported by their own separate public facade.

        Returns:
            Original symbol names explicitly published outside family facades.

        """
        families = {
            f"{item.module}.py"
            for item in FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        }
        origin = f"{pkg_dir.name}.{owners_dir.name}"
        published: set[str] = set()
        for path, content in sources.values():
            if path.parent != pkg_dir or path.name in families:
                continue
            exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                content
            )
            for node in ast.parse(content, filename=str(path)).body:
                if isinstance(node, ast.ImportFrom) and node.module == origin:
                    published.update(
                        alias.name
                        for alias in node.names
                        if (alias.asname or alias.name) in exports
                    )
        return frozenset(published)

    @staticmethod
    def _required_methods(
        pkg_dir: Path,
        facade_path: Path,
        *,
        nested_namespace: bool,
        namespace: str,
        family: Literal["u", "p", "m"],
    ) -> frozenset[str]:
        """Collect consumed members through their actual imported Rope identities.

        Returns:
            The required public members; invalid source positions fail at Rope.

        """
        methods: set[str] = set()
        with FlextInfraUtilitiesRopeCore.open_import_project(pkg_dir.parent) as project:
            for path in (
                candidate
                for candidate in sorted(pkg_dir.rglob(f"*{c.Infra.EXT_PYTHON}"))
                if candidate != facade_path
            ):
                source = path.read_text(encoding=c.DEFAULT_ENCODING)
                # Generated initializers propagate declarations; they are not
                # authored consumers and may await replacement in this plan.
                if path.name == c.Infra.INIT_PY and source.startswith(
                    c.Infra.AUTOGEN_HEADERS,
                ):
                    continue
                tree = ast.parse(source, filename=str(path))
                imported_receivers = {
                    alias.asname or alias.name.split(".", 1)[0]
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names
                }
                pymodule: t.Infra.RopePyModule | None = None
                module_paths: t.MutableMappingKV[p.Infra.RopeImportedModule, Path] = {}
                for reference in (
                    node.func if isinstance(node, ast.Call) else node
                    for node in ast.walk(tree)
                    if family != "u" or isinstance(node, ast.Call)
                ):
                    if not isinstance(reference, ast.Attribute):
                        continue
                    receiver = reference.value
                    public_receiver = not nested_namespace or (
                        isinstance(receiver, ast.Attribute)
                        and receiver.attr == namespace
                    )
                    receiver = (
                        receiver.value
                        if nested_namespace
                        and public_receiver
                        and isinstance(receiver, ast.Attribute)
                        else receiver
                    )
                    if (
                        not isinstance(receiver, ast.Name)
                        or receiver.id not in imported_receivers
                        or (
                            family != "u"
                            and (not public_receiver or receiver.id != family)
                        )
                    ):
                        continue
                    if pymodule is None:
                        resource = project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix(),
                        )
                        pymodule = FlextInfraUtilitiesRopeRuntime.build_string_module(
                            project,
                            source,
                            resource=resource,
                        )
                    offset = pymodule.lines.get_line_start(receiver.lineno)
                    offset += len(
                        pymodule.lines
                        .get_line(receiver.lineno)
                        .encode(c.DEFAULT_ENCODING)[: receiver.col_offset]
                        .decode(c.DEFAULT_ENCODING),
                    )
                    scope = FlextInfraUtilitiesRopeRuntime.scope_at(
                        pymodule,
                        offset,
                    )
                    binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                        scope,
                        receiver,
                    )
                    if not isinstance(
                        binding, p.Infra.RopeImportedName
                    ) or family not in {"u", binding.imported_name}:
                        continue
                    imported = binding.imported_module
                    if (
                        imported.level == 0
                        and imported.module_name is not None
                        and imported.module_name.split(".", 1)[0]
                        in sys.stdlib_module_names
                    ):
                        # Standard-library imports cannot declare owned facades.
                        # Built-in modules have no source resource for Rope.
                        continue
                    declared = FlextInfraUtilitiesRopeRuntime.imported_module_path(
                        project,
                        binding,
                        resolved=module_paths,
                    )
                    owner_directory = (
                        pkg_dir
                        / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                            family
                        ].directory
                    )
                    lower_owner = (
                        family == "u"
                        and declared.is_relative_to(owner_directory)
                        and not path.is_relative_to(owner_directory)
                    )
                    if not lower_owner and (
                        not public_receiver
                        or receiver.id != family
                        or binding.imported_name != family
                        or declared
                        not in {
                            pkg_dir,
                            pkg_dir / c.Infra.INIT_PY,
                            facade_path,
                        }
                    ):
                        continue
                    methods.add(reference.attr)
        return frozenset(method for method in methods if not method.startswith("_"))

    @staticmethod
    def _utility_owners(
        owners_dir: Path,
        *,
        family: Literal["u", "p", "m"],
    ) -> t.Pair[
        t.VariadicTuple[t.Triple[str, str, frozenset[str]]],
        t.MappingKV[str, frozenset[str]],
    ]:
        owners: list[t.Triple[str, str, frozenset[str]]] = []
        ancestors: MutableMapping[str, frozenset[str]] = {}
        for path in sorted(owners_dir.rglob(c.Infra.EXT_PYTHON_GLOB)):
            if path.name == c.Infra.INIT_PY:
                continue
            tree = ast.parse(
                path.read_text(encoding=c.DEFAULT_ENCODING),
                filename=str(path),
            )
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                    continue
                if family == "u":
                    members = tuple(
                        member
                        for member in node.body
                        if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
                    )
                else:
                    members = tuple(
                        member
                        for member in node.body
                        if isinstance(member, ast.ClassDef)
                    )
                methods = frozenset(
                    member.name for member in members if not member.name.startswith("_")
                )
                module = path.relative_to(owners_dir).with_suffix("").as_posix()
                owners.append((module.replace("/", "."), node.name, methods))
                ancestors[node.name] = frozenset(
                    name
                    for base in node.bases
                    if (name := FlextInfraUtilitiesCodegenFacades._base_name(base))
                )
        return tuple(owners), ancestors

    @staticmethod
    def _facade_classes(
        tree: ast.Module,
        path: Path,
    ) -> t.Pair[ast.ClassDef, ast.ClassDef]:
        """Resolve one facade and its single declared utility namespace.

        Returns:
            The facade and its namespace, or the facade when no namespace exists.

        Raises:
            ValueError: If the facade or inherited namespace identity is ambiguous.

        """
        facades = tuple(node for node in tree.body if isinstance(node, ast.ClassDef))
        if len(facades) != 1:
            message = f"expected one utility facade class in {path}"
            raise ValueError(message)
        nested = tuple(
            node for node in facades[0].body if isinstance(node, ast.ClassDef)
        )
        if len(nested) > 1:
            ancestors = {ast.unparse(base) for base in facades[0].bases}
            namespaces = tuple(
                node
                for node in nested
                if any(
                    ast.unparse(base) in ancestors
                    or (
                        isinstance(base, ast.Attribute)
                        and ast.unparse(base.value) in ancestors
                        and base.attr == node.name
                    )
                    for base in node.bases
                )
            )
            if len(namespaces) > 1:
                message = f"competing inherited utility namespaces in {path}"
                raise ValueError(message)
            return facades[0], namespaces[0] if namespaces else facades[0]
        # Multiple nested declarations are entities on the facade, not competing
        # facade identities. Only a sole namespace can own the nested projection.
        return facades[0], nested[0] if len(nested) == 1 else facades[0]

    @classmethod
    def _base_name(cls, base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        # Why: a generic base carries the same owner as its unsubscripted form.
        # `class X(FlextLdifUtilitiesTransformer[m.Ldif.Entry])` names
        # FlextLdifUtilitiesTransformer exactly like the bare base does, and the
        # type argument decides nothing about facade reachability.
        if isinstance(base, ast.Subscript):
            return cls._base_name(base.value)
        message = f"unsupported utility facade base: {ast.dump(base)}"
        raise ValueError(message)

    @staticmethod
    def _reachable_bases(
        roots: t.SequenceOf[str],
        ancestors: t.MappingKV[str, frozenset[str]],
    ) -> set[str]:
        reachable = set(roots)
        pending = list(roots)
        while pending:
            for base in ancestors.get(pending.pop(), frozenset()):
                if base not in reachable:
                    reachable.add(base)
                    pending.append(base)
        return reachable

    @staticmethod
    def _insert_imports(
        source: str,
        additions: t.SequenceOf[t.Pair[str, str]],
        *,
        package: str,
        family: Literal["u", "p", "m"],
    ) -> str:
        # The owner lives in the package being rendered. Naming this project
        # instead made every generated consumer facade import from flext-infra,
        # a module that does not exist in the consumer's own distribution.

        directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            family
        ].directory
        context = CodemodContext()
        for module, class_name in additions:
            owner = f"{package}.{directory}.{module}"
            AddImportsVisitor.add_needed_import(
                context,
                owner,
                class_name,
            )
        return AddImportsVisitor(context).transform_module(parse_module(source)).code

    @classmethod
    def _insert_bases(
        cls,
        source: str,
        namespace: ast.ClassDef,
        additions: t.SequenceOf[t.Pair[str, str]],
    ) -> str:
        if not namespace.bases:
            wrapper = MetadataWrapper(parse_module(source))
            positions = wrapper.resolve(PositionProvider)
            owners = tuple(
                node
                for node, span in positions.items()
                if isinstance(node, ClassDef)
                and span.start.line == namespace.lineno
                and span.start.column
                == len(
                    source
                    .splitlines()[namespace.lineno - 1]
                    .encode(c.DEFAULT_ENCODING)[: namespace.col_offset]
                    .decode(c.DEFAULT_ENCODING),
                )
            )
            if len(owners) != 1:
                message = "facade namespace has no unique concrete source span"
                raise ValueError(message)
            owner = owners[0]
            updated = wrapper.module.deep_replace(
                owner,
                owner.with_changes(
                    bases=tuple(Arg(Name(name)) for _module, name in additions),
                ),
            )
            if not isinstance(updated, Module):
                message = "facade base projection did not preserve the module"
                raise ValueError(message)
            return updated.code
        last_base = namespace.bases[-1]
        if last_base.end_lineno is None or last_base.end_col_offset is None:
            message = "utility namespace base has no source span"
            raise ValueError(message)
        # A base listed after Protocol has no consistent MRO, so owners
        # projected onto a protocol namespace go before its terminal Protocol.
        precede = cls._base_name(last_base) == c.Infra.PROTOCOL_BASE
        lines = source.encode(c.DEFAULT_ENCODING).splitlines(keepends=True)
        line, column = (
            (last_base.lineno, last_base.col_offset)
            if precede
            else (last_base.end_lineno, last_base.end_col_offset)
        )
        offset = sum(map(len, lines[: line - 1])) + column
        separator = (
            ", "
            if last_base.lineno == namespace.lineno
            else ",\n" + " " * last_base.col_offset
        )
        inserted = "".join(
            name + separator if precede else separator + name
            for _module, name in additions
        )
        encoded = b"".join(lines)
        return (
            encoded[:offset] + inserted.encode(c.DEFAULT_ENCODING) + encoded[offset:]
        ).decode(c.DEFAULT_ENCODING)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFacades"]
