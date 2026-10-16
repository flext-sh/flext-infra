"""Declared facade composition and consumer-selected protocol owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Generator, MutableMapping
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal

from flext_cli import u

from libcst import Arg, ClassDef, Module, Name, parse_module
from libcst.codemod import CodemodContext
from libcst.codemod.commands.rename import RenameCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import c, m, p, t
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
from flext_infra._utilities.codegen_facade_syntax import (
    FlextInfraUtilitiesCodegenFacadeSyntax,
)
from flext_infra._utilities.codemod_project import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities.iteration_workspace import (
    FlextInfraUtilitiesIterationWorkspace,
)


class FlextInfraUtilitiesCodegenFacades(FlextInfraUtilitiesCodegenFacadeSyntax):
    """Compose declared facade owners and resolve consumed protocols."""

    @staticmethod
    @contextmanager
    def facade_source_project(
        root: Path,
        *,
        source_states: tuple[m.Cli.AtomicFileState, ...] = (),
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> Generator[
        t.Triple[
            p.Infra.RopeProject,
            m.Infra.CodemodSourceEpoch,
            t.MappingKV[Path, str],
        ]
    ]:
        """Share one authenticated native source graph across a planning pass.

        Yields:
            The closed Rope project, original epoch and planned source overlay.

        """
        if not source_states:
            paths = FlextInfraUtilitiesIterationWorkspace.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(root,)),
            ).unwrap()
            source_states = tuple(
                u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in paths
            )
        captured = FlextInfraUtilitiesCodemodProject.codemod_binding_snapshot(
            root,
            source_states,
            projects=(
                m.Infra.CodemodBindingProject(
                    root=root,
                    source_paths=tuple(
                        state.path
                        for state in source_states
                        if state.path.is_relative_to(root)
                        and state.path.suffix
                        in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                    ),
                ),
            ),
        )
        epoch = FlextInfraUtilitiesCodemodProject.codemod_source_epoch(captured)
        u.Cli.atomic_verify_binary_file_states(epoch.snapshot.states).unwrap()
        proposed = {
            plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
            for plan in declared_files
            if plan.desired_content is not None
        }
        sources = {**epoch.sources, **proposed}
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as live,
            closing(
                FlextInfraUtilitiesRopeRuntime.snapshot_project(
                    live,
                    proposed,
                    captured=epoch,
                    declared_files=tuple(
                        plan
                        for plan in declared_files
                        if plan.desired_content is not None
                    ),
                )
            ) as project,
            project.frozen_layout(),
        ):
            yield project, epoch, sources
            u.Cli.atomic_verify_binary_file_states(epoch.snapshot.states).unwrap()

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
        return cls._generated_facade(
            pkg_dir, rendered, family="t", contents=sources
        )

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
        project: p.Infra.RopeProject | None = None,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> str | None:
        """Render uniquely discovered utility, protocol or model owners.

        Constants, utilities and models compose the declarations published by
        their configured private family. Protocol consumers select missing
        protocol owners through resolved imports. Existing namespace runtime
        bindings and owner base chains retain their declared identities.
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
        if project is None or sources is None:
            if project is not None or sources is not None:
                message = "Facade rendering requires its project and source epoch together"
                raise ValueError(message)
            with cls.facade_source_project(pkg_dir.parent) as (captured, _, contents):
                return cls.render_utility_facade(
                    pkg_dir, family=family, project=captured, sources=contents
                )
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
        source = sources[facade_path]
        match family:
            case "c" | "m" | "u":
                rendered = cls._render_declared_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    family=family,
                    binding=(project, sources),
                )
            case "p":
                rendered = cls._render_protocol_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    binding=(project, sources),
                )
        return cls._generated_facade(
            pkg_dir, rendered, family=family, contents=sources
        )

    @classmethod
    def _generated_facade(
        cls,
        pkg_dir: Path,
        source: str,
        *,
        family: Literal["c", "t", "u", "p", "m"],
        contents: t.MappingKV[Path, str],
    ) -> str:
        """Publish composition through the declared family export boundaries.

        Authored declarations and unrelated imports retain their syntax. The
        namespace rule catalog owns their architecture checks; generation only
        rewires bindings the selected family explicitly publishes.

        Returns:
            Generated composition carrying the canonical ownership marker.

        """
        tree = ast.parse(source)
        _, declarations = cls._declared_sources(
            pkg_dir,
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory,
            contents=contents,
        )
        published = {
            f"{declaration.target}.{declaration.qualified_base}": (
                f"{declaration.target.rpartition('.')[0]}.{declaration.qualified_base}"
            )
            for declaration in declarations
        }
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            module = f"{pkg_dir.name}.{node.module}" if node.level else node.module
            for alias in node.names:
                target = published.get(f"{module}.{alias.name}")
                if target is None:
                    continue
                source = (
                    RenameCommand(
                        CodemodContext(full_package_name=pkg_dir.name),
                        old_name=f"{module}.{alias.name}",
                        new_name=target,
                    )
                    .transform_module(parse_module(source))
                    .code
                )
        source = cls._wrap_facade_imports(cls._merged_facade_imports(source))
        if source.startswith(c.Infra.AUTOGEN_HEADERS):
            return source
        return f"{c.Infra.AUTOGEN_HEADER}\n{source}"

    @classmethod
    def _render_protocol_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        source: str,
        *,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> str:
        """Compose protocol owners selected by their resolved consumers.

        Returns:
            The projected source with its existing namespace bindings preserved.

        Raises:
            ValueError: If a consumer requires competing provider declarations.

        """
        project, contents = binding
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        family = c.Infra.FacadeFamily.P
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        owners, ancestors = cls._facade_protocol_owners(owners_dir, contents)
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
            cls._required_protocol_members(
                pkg_dir,
                facade_path,
                nested_namespace=namespace is not facade,
                namespace=namespace.name,
                binding=binding,
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
        if not additions:
            return source
        source = cls._insert_protocol_imports(
            source,
            additions,
            package=pkg_dir.name,
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
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> str:
        """Compose explicitly exported declarations without reverse family imports.

        Returns:
            A facade whose direct owners preserve the existing source C3 order.

        """
        project, contents = binding
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        sources, declarations = cls._declared_sources(
            pkg_dir, owners_dir, contents=contents
        )
        source = cls._rebind_declared_imports(pkg_dir, owners_dir, source, declarations)
        sources[f"{pkg_dir.name}.{facade_path.stem}"] = (facade_path, source)
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        independent = cls._independent_publishers(pkg_dir, owners_dir, sources)
        retired = cls._retired_owned_bases(
            project,
            sources,
            (pkg_dir, owners_dir),
            (facade_path, namespace),
            {item.qualified_base for item in declarations},
        )
        if retired:
            source, context = cls._retired_facade_projection(
                pkg_dir, source, namespace, retired
            )
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
        ordered = cls._declared_facade_order(project, sources, declarations)
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
    def _retired_facade_projection(
        cls,
        pkg_dir: Path,
        source: str,
        namespace: ast.ClassDef,
        retired: frozenset[str],
    ) -> t.Pair[str, CodemodContext]:
        wrapper = MetadataWrapper(parse_module(source))
        owner = cls._facade_namespace_cst(wrapper, namespace)
        context = CodemodContext(full_package_name=pkg_dir.name, wrapper=wrapper)
        retained_bases: list[Arg] = []
        for base in owner.bases:
            expression = ast.unparse(
                ast.parse(wrapper.module.code_for_node(base.value), mode="eval").body
            )
            if expression in retired:
                RemoveImportsVisitor.remove_unused_import_by_node(context, base.value)
            else:
                retained_bases.append(base)
        candidate = wrapper.module.deep_replace(
            owner, owner.with_changes(bases=tuple(retained_bases))
        )
        if not isinstance(candidate, Module):
            message = "Retired facade-base projection did not preserve the module"
            raise TypeError(message)
        return candidate.code, context

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
        project: p.Infra.RopeProject,
        sources: t.MutableMappingKV[str, t.Pair[Path, str]],
        declarations: list[m.Infra.SourceClassReference],
    ) -> t.SequenceOf[str]:
        """Resolve the C3 base order of the facade's declared owners.

        Returns:
            The ordered base names the facade namespace must compose.

        """
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
    def _retired_owned_bases(
        project: t.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        roots: t.Pair[Path, Path],
        facade: t.Pair[Path, ast.ClassDef],
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
        facade_path, namespace = facade
        candidates = tuple(
            base
            for base in namespace.bases
            if FlextInfraUtilitiesCodegenFacades._base_name(base) not in declared_names
        )
        if not candidates:
            return frozenset()
        resource = project.get_resource(
            facade_path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project, dict(sources.values())[facade_path], resource=resource
        ).get_scope()
        retired: set[str] = set()
        for base in candidates:
            expression = base.value if isinstance(base, ast.Subscript) else base
            head = expression
            while isinstance(head, ast.Attribute):
                head = head.value
            if head is not expression and (
                FlextInfraUtilitiesCodegenFacades._upstream_binding(
                    project,
                    project,
                    FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, head),
                )
            ):
                continue
            binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                scope,
                expression,
            )
            if binding is None:
                message = (
                    f"Unresolved facade base: {facade_path}:{ast.unparse(base)}"
                )
                raise ValueError(message)
            value = binding.get_object()
            if FlextInfraUtilitiesRopeRuntime.semantic_module(value):
                message = f"Module used as a class base: {ast.unparse(base)}"
                raise ValueError(message)
            holder = binding.get_definition_location()[0]
            provider = holder.get_resource() if holder is not None else None
            if provider is None:
                if (
                    FlextInfraUtilitiesRopeRuntime.abstract_class(value)
                    and not FlextInfraUtilitiesRopeRuntime.py_class(value)
                ) or FlextInfraUtilitiesCodegenFacades._upstream_binding(
                    project,
                    project,
                    binding,
                ):
                    continue
                message = (
                    f"Facade base has no source owner: "
                    f"{facade_path}:{ast.unparse(base)}"
                )
                raise ValueError(message)
            path = Path(provider.real_path).resolve()
            if path.is_relative_to(roots[0].resolve()) and not path.is_relative_to(
                roots[1].resolve(),
            ):
                retired.add(ast.unparse(base))
        return frozenset(retired)

    @staticmethod
    def _upstream_binding(
        project: t.Infra.RopeProject,
        snapshot: p.Infra.RopeProject,
        binding: p.Infra.RopePyName | None,
    ) -> bool:
        """Return whether a facade base binding is upstream inheritance.

        The facade snapshot captures only the project's own sources, so a
        name imported from an installed upstream package has no source holder
        there and its module is absent from the snapshot. Its import
        provenance still resolves through the full import project; such a
        base, and any attribute reached through it (``Upstream.Nested``), is
        inherited and never retired. An import whose module the import project
        cannot resolve raises.

        Returns:
            Whether the binding is an absolute import of a module the snapshot
            does not capture.

        """
        if (
            not isinstance(binding, p.Infra.RopeImportedName)
            or binding.get_definition_location()[0] is not None
        ):
            return False
        imported = binding.imported_module
        if (
            imported.level
            or imported.module_name is None
            or snapshot.find_module(imported.module_name) is not None
        ):
            return False
        FlextInfraUtilitiesRopeRuntime.imported_module_path(project, binding)
        return True

    @staticmethod
    def _rebind_declared_imports(
        pkg_dir: Path,
        owners_dir: Path,
        source: str,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> str:
        """Rebind obsolete leaf imports to their current declaration modules.

        Package-form imports already name the public family boundary. Its
        initializer owns publishing the declared bindings.

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
            if not module.startswith(f"{prefix}."):
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
        *,
        contents: t.MappingKV[Path, str],
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
        captured = {
            path: source
            for path, source in contents.items()
            if path.is_relative_to(pkg_dir) and path.suffix == c.Infra.EXT_PYTHON
        }
        for path, content in sorted(captured.items()):
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
    def _required_protocol_members(
        pkg_dir: Path,
        facade_path: Path,
        *,
        nested_namespace: bool,
        namespace: str,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> frozenset[str]:
        """Collect consumed members through their actual imported Rope identities.

        Returns:
            The required public members; invalid source positions fail at Rope.

        """
        project, contents = binding
        family = c.Infra.FacadeFamily.P
        methods: set[str] = set()
        for path, source in sorted(contents.items()):
            if (
                path == facade_path
                or not path.is_relative_to(pkg_dir)
                or path.suffix != c.Infra.EXT_PYTHON
            ):
                continue
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
            for reference in ast.walk(tree):
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
                    or not public_receiver
                    or receiver.id != family
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
                binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    FlextInfraUtilitiesRopeRuntime.scope_at(pymodule, offset),
                    receiver,
                )
                if (
                    not isinstance(binding, p.Infra.RopeImportedName)
                    or binding.imported_name != family
                ):
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
                if declared not in {
                    pkg_dir,
                    pkg_dir / c.Infra.INIT_PY,
                    facade_path,
                }:
                    continue
                methods.add(reference.attr)
        return frozenset(method for method in methods if not method.startswith("_"))

    @staticmethod
    def _facade_protocol_owners(
        owners_dir: Path,
        contents: t.MappingKV[Path, str],
    ) -> t.Pair[
        t.VariadicTuple[t.Triple[str, str, frozenset[str]]],
        t.MappingKV[str, frozenset[str]],
    ]:
        owners: list[t.Triple[str, str, frozenset[str]]] = []
        ancestors: MutableMapping[str, frozenset[str]] = {}
        for path, source in sorted(contents.items()):
            if (
                path.name == c.Infra.INIT_PY
                or not path.is_relative_to(owners_dir)
                or path.suffix != c.Infra.EXT_PYTHON
            ):
                continue
            tree = ast.parse(
                source,
                filename=str(path),
            )
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                    continue
                members = tuple(
                    member for member in node.body if isinstance(member, ast.ClassDef)
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
    def _insert_protocol_imports(
        source: str,
        additions: t.SequenceOf[t.Pair[str, str]],
        *,
        package: str,
    ) -> str:
        # The owner lives in the package being rendered. Naming this project
        # instead made every generated consumer facade import from flext-infra,
        # a module that does not exist in the consumer's own distribution.

        directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            c.Infra.FacadeFamily.P
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
