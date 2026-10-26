"""Compose declared facade bases while preserving class-publication identity.

Family packages publish their declarations through derived lazy exports. Facades
import those packages and compose upstream same-letter exports, never leaf modules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Generator, MutableMapping
from contextlib import contextmanager
from importlib.util import resolve_name
from pathlib import Path
from typing import Literal, override

from flext_cli import u
from libcst import (
    AnnAssign,
    Annotation,
    Arg,
    Assign,
    Attribute,
    BaseExpression,
    ClassDef,
    Comma,
    CSTNode,
    CSTTransformer,
    If,
    LeftParen,
    Module,
    Name,
    ParenthesizedWhitespace,
    RemovalSentinel,
    RightParen,
    SimpleStatementLine,
    SimpleWhitespace,
    TypeAlias,
    parse_module,
    parse_statement,
)
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacadeSyntax,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
    FlextInfraUtilitiesRopeAnalysisSourceScan,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope_source_bases_inventory import (
    FlextInfraUtilitiesRopeSourceBasesInventory,
)


class FlextInfraUtilitiesCodegenFacades(FlextInfraUtilitiesCodegenFacadeSyntax):
    """Compose declared facade owners and resolve consumed protocols."""

    @staticmethod
    @contextmanager
    def facade_source_project(
        root: Path,
        *,
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
        planned_sources: t.MappingKV[Path, str | None] | None = None,
        project_roots: t.VariadicTuple[Path] = (),
    ) -> Generator[t.Pair[p.Infra.RopeProject, MutableMapping[Path, str]]]:
        """Open one Rope view of the live tree overlaid with planned sources.

        ``declared_files`` and ``planned_sources`` overlay the live tree; the
        selected project roots' native source discovery owns the returned
        source view, including proposed additions and retirements.

        Yields:
            The native Rope project and the planned Python sources it sees.

        Raises:
            ValueError: If a declared project root lies outside ``root``.

        """
        root = root.resolve()
        project_roots = tuple(sorted({project.resolve() for project in project_roots}))
        if any(not project.is_relative_to(root) for project in project_roots):
            msg = "Rope declared project root is outside the original authority"
            raise ValueError(msg)
        if planned_sources:
            declared_files = FlextInfraUtilitiesCodegenFacades._facade_declared_sources(
                root, declared_files, planned_sources
            )
        original_root = next(path for path in (root, *root.parents) if path.is_dir())
        folders = FlextInfraUtilitiesCodegenFacades._planned_folders(
            root, project_roots, declared_files, original_root=original_root
        )
        with FlextInfraUtilitiesWorkspaceSnapshot.workspace_overlay_project(
            root,
            project_roots,
            declared_files=declared_files,
            additional_source_folders=folders,
        ) as project:
            yield (
                project,
                {
                    path: project.source_text(path)
                    for scope in project_roots or (root,)
                    for path in (
                        FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                            scope,
                            workspace_excluded_top_dirs=frozenset(),
                            source_project=project,
                        )
                    )
                },
            )

    @staticmethod
    def _planned_folders(
        root: Path,
        project_roots: tuple[Path, ...],
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        *,
        original_root: Path,
    ) -> tuple[str, ...]:
        """Elect declared live source roots together with proposed virtual roots.

        Returns:
            The live and proposed source-folder election of the overlaid view.

        """
        proposed = tuple(
            plan.path for plan in declared_files if plan.desired_content is not None
        )
        return tuple(
            sorted({
                ""
                if folder == original_root
                else folder.relative_to(original_root).as_posix()
                for folder in (
                    root,
                    *project_roots,
                    *(
                        project / name
                        for project in (root, *project_roots)
                        for name in config.Infra.source_scan.roots
                    ),
                )
                if folder.is_dir()
                or any(path.is_relative_to(folder) for path in proposed)
            }),
        )

    @staticmethod
    def require_source_project(value: p.AttributeProbe) -> p.Infra.RopeProject:
        """Admit the native project at its actual dynamic SDK boundary.

        Returns:
            The project exposing the native source capabilities.

        Raises:
            TypeError: If the SDK project does not expose the required capabilities.

        """
        if not isinstance(value, p.Infra.RopeProject):
            message = "facade source project has no native Rope capabilities"
            raise TypeError(message)
        return value

    @staticmethod
    def candidate_python_sources(
        candidate: m.Infra.StageSourcePlan,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> t.MutableMappingKV[Path, str]:
        """Select the candidate's Python sources from the given file states.

        Returns:
            Python text keyed by path, across the candidate's scopes.

        """
        return {
            path: source
            for scope in candidate.workspaces or (candidate.workspace,)
            for path, source in (
                FlextInfraUtilitiesCodegenFacades.facade_original_sources(scope, states)
            ).items()
        }

    @staticmethod
    def facade_original_sources(
        root: Path,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> t.MappingKV[Path, str]:
        """Select root-owned, non-ignored Python sources from file states.

        Returns:
            Python text keyed by path.

        """
        return {
            state.path: state.content.decode(c.DEFAULT_ENCODING)
            for state in states
            if state.content is not None
            and state.path.is_relative_to(root)
            and state.path.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
            and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                root, state.path
            )
        }

    @staticmethod
    def _facade_declared_sources(
        root: Path,
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        planned_sources: t.MappingKV[Path, str | None],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Add one file plan per planned source not already declared.

        Returns:
            The declared plans followed by the planned-source plans.

        Raises:
            ValueError: If a planned source competes with a declaration.

        """
        declarations = {plan.path: plan for plan in declared_files}
        for supplied_path, source in planned_sources.items():
            path = supplied_path.resolve()
            content = source.encode(c.DEFAULT_ENCODING) if source is not None else None
            declared = declarations.get(path)
            if declared is not None:
                if declared.desired_content != content:
                    message = f"Rope planned source has competing declarations: {path}"
                    raise ValueError(message)
                continue
            before = u.Cli.atomic_read_binary_file_state(path).unwrap()
            declarations[path] = m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=before,
                desired_content=content,
                desired_mode=(
                    None
                    if content is None
                    else (
                        before.mode
                        if before.mode is not None
                        else config.Infra.codegen.modes.file_default
                    )
                ),
            )
        return tuple(declarations.values())

    @classmethod
    def render_type_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        sources: t.MappingKV[Path, str],
        *,
        project: p.Infra.RopeProject,
    ) -> str:
        """Project a complete exported type owner without duplicating its body.

        Only the existing class/t export contract is supported. Ambiguous owners
        or extra public declarations fail rather than being silently discarded.
        Admission shares one parsed view of the rebound source so owner, alias
        and export nodes retain consistent identities and source offsets.

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
        facade, namespace = cls._facade_classes(tree, facade_path)
        if facade.decorator_list or facade.type_params:
            msg = f"unsupported type facade class: {facade_path}"
            raise ValueError(msg)
        declared_sources, declarations, package_name = cls._declared_sources(
            pkg_dir,
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()["t"].directory,
            contents=sources,
            project=project,
        )
        source = cls._rebind_declared_imports(
            package_name,
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()["t"].directory,
            source,
            declarations,
        )
        source = cls._inherit_upstream_namespace(project, facade_path, source)
        source = cls._publish_namespace_aliases(project, facade_path, source)
        if cls._explicit_class_facade(
            project,
            facade_path,
            source,
            declarations,
            binding=(declared_sources, c.Infra.FacadeFamily.T),
        ):
            source = cls._render_explicit_class_facade(
                pkg_dir,
                facade_path,
                source,
                family=c.Infra.FacadeFamily.T,
                binding=(project, sources),
            )
            return cls._generated_facade(
                pkg_dir,
                source,
                family=c.Infra.FacadeFamily.T,
                contents=sources,
                project=project,
            )
        tree = ast.parse(source, filename=str(facade_path))
        facade, namespace = cls._facade_classes(tree, facade_path)
        if any(
            cls._base_name(base) == item.qualified_base
            for base in namespace.bases
            for item in declarations
        ):
            return cls._generated_facade(
                pkg_dir,
                cls._render_declared_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    family=c.Infra.FacadeFamily.T,
                    binding=(project, sources),
                ),
                family=c.Infra.FacadeFamily.T,
                contents=sources,
                project=project,
            )
        exports = tuple(
            node
            for node in tree.body
            if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
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
            not isinstance(node, c.Infra.AST_IMPORT_TYPES)
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
                    isinstance(item, c.Infra.AST_IMPORT_TYPES) for item in node.body
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
        for parent in sorted({
            pkg_dir / directory,
            *(
                path.parent
                for path in sources
                if path.is_relative_to(pkg_dir / directory)
                and path.suffix == c.Infra.EXT_PYTHON
            ),
        }):
            cls._facade_source_membership(project, parent)
        owners = tuple(
            path
            for path, content in sources.items()
            if path.is_relative_to(pkg_dir / directory)
            and path.name != c.Infra.INIT_PY
            and "t"
            in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_at(project, path)
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
            f"{package_name}.{module}.\n"
            f"from {package_name}.{module.rpartition('.')[0]} "
            f"import {facade.name} as {alias}\n\n\n"
            f"class {facade.name}({alias}):\n"
            '    """Public type facade inheriting its '
            'complete canonical owner."""\n\n\n'
            f"t = {facade.name}\n\n"
            f"{ast.get_source_segment(source, exports[0])}\n"
        )
        return cls._generated_facade(
            pkg_dir,
            rendered,
            family=c.Infra.FacadeFamily.T,
            contents=sources,
            project=project,
        )

    @staticmethod
    def _facade_source_membership(
        project: p.Infra.RopeProject,
        directory: Path,
    ) -> tuple[Path, ...]:
        """Authenticate the native immediate Python election before parsing.

        Source text maps may contain only consumed provider files. Complete
        membership belongs to the injected native snapshot, not that partial
        text inventory; declared additions and retirements remain in that view.

        Returns:
            Native source paths matching the complete source snapshot.

        Raises:
            ValueError: Native membership differs from its complete source snapshot.

        """
        expected = tuple(
            sorted(
                path
                for path in project.source_children(directory)
                if path.suffix == c.Infra.EXT_PYTHON
                and project.source_query(path, "isfile")
            )
        )
        folder = project.get_folder(
            directory.relative_to(Path(project.root.real_path)).as_posix()
        )
        actual = tuple(
            sorted(
                Path(child.real_path)
                for child in folder.get_children()
                if not child.is_folder()
                and Path(child.real_path).suffix == c.Infra.EXT_PYTHON
            )
        )
        if actual != expected:
            message = (
                f"native facade source membership differs: {directory}; "
                f"added={sorted(set(actual) - set(expected))}; "
                f"removed={sorted(set(expected) - set(actual))}"
            )
            raise ValueError(message)
        return actual

    @classmethod
    def facade_module_path(
        cls,
        pkg_dir: Path,
        family: str,
        *,
        project: p.Infra.RopeProject | None = None,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> Path | None:
        """Return the package module that declares facade letter ``family``.

        The owner of a facade letter is the module that publishes it in its own
        ``__all__`` (generator law p.1); it is derived from the package, never
        from a letter-to-filename table. ``None`` means no module declares it.

        Returns:
            The declaring package module, or ``None`` when none declares it.

        Raises:
            ValueError: If multiple package modules declare the same facade letter.

        """
        if project is None or sources is None:
            if project is not None or sources is not None:
                message = (
                    "Facade election requires its project and source epoch together"
                )
                raise ValueError(message)
            with cls.facade_source_project(pkg_dir.parent) as (captured, contents):
                return cls.facade_module_path(
                    pkg_dir, family, project=captured, sources=contents
                )
        owners: list[Path] = []
        for module in cls._facade_source_membership(project, pkg_dir):
            if module.name == c.Infra.INIT_PY:
                continue
            if family in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_at(
                project, module
            ):
                owners.append(module)
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
        family: Literal[
            "c",
            "u",
            "p",
            "m",
            c.Infra.FacadeFamily.C,
            c.Infra.FacadeFamily.U,
            c.Infra.FacadeFamily.P,
            c.Infra.FacadeFamily.M,
        ] = "u",
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
                message = (
                    "Facade rendering requires its project and source epoch together"
                )
                raise ValueError(message)
            with cls.facade_source_project(pkg_dir.parent) as (captured, contents):
                return cls.render_utility_facade(
                    pkg_dir, family=family, project=captured, sources=contents
                )
        selected_family = c.Infra.FacadeFamily(family)
        facade_path = cls.facade_module_path(
            pkg_dir, family, project=project, sources=sources
        )
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                selected_family
            ].directory
        )
        # Why: only owners-without-facade is incomplete -- the owners would have
        # no public surface at all. A facade with no owners directory is the
        # legitimate pure re-export shape this same generator emits for a package
        # that adds no local utilities (src/flext: `class FlextRootUtilities(u)`),
        # and there is simply nothing to project onto it.
        # Declared virtual parents belong to the authenticated candidate too.
        if not project.source_query(owners_dir, "isdir"):
            return None
        if facade_path is None:
            # Conform preflights its family directories before rendering files.
            # An empty directory contains no owner requiring a public surface.
            if not cls._facade_source_membership(project, owners_dir):
                return None
            message = f"utility owners in {pkg_dir} have no public facade"
            raise ValueError(message)
        # Parser inputs share the native Rope reads. Unresolved module
        # inventory remains available to the MRO resolver without being read.
        sources = {
            path: (
                FlextInfraUtilitiesRopeRuntime.require_file_resource(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    ),
                    path,
                ).read()
                if path.is_relative_to(pkg_dir)
                and path.suffix == c.Infra.EXT_PYTHON
                and (
                    selected_family is c.Infra.FacadeFamily.P
                    or path.parent in {pkg_dir, owners_dir}
                    or path.name == c.Infra.INIT_PY
                )
                else content
            )
            for path, content in sources.items()
        }
        source = sources[facade_path]
        declared_sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=sources, project=project
        )
        if selected_family is c.Infra.FacadeFamily.M:
            cls._require_model_namespaces(project, declarations, declared_sources)
        source = cls._publish_namespace_aliases(
            project,
            facade_path,
            cls._rebind_declared_imports(
                package_name, owners_dir, source, declarations
            ),
        )
        explicit_parts = cls._explicit_class_facade(
            project,
            facade_path,
            source,
            declarations,
            binding=(declared_sources, selected_family),
        )
        if explicit_parts:
            return cls._generated_facade(
                pkg_dir,
                cls._render_explicit_class_facade(
                    pkg_dir,
                    facade_path,
                    source,
                    family=selected_family,
                    binding=(project, sources),
                ),
                family=selected_family,
                contents=sources,
                project=project,
            )
        source = cls._inherit_upstream_namespace(project, facade_path, source)
        if selected_family is not c.Infra.FacadeFamily.P:
            rendered = cls._render_declared_facade(
                pkg_dir,
                facade_path,
                source,
                family=selected_family,
                binding=(project, sources),
            )
        else:
            rendered = cls._render_protocol_facade(
                pkg_dir, facade_path, source, binding=(project, sources)
            )
        return cls._generated_facade(
            pkg_dir, rendered, family=selected_family, contents=sources, project=project
        )

    @classmethod
    def _render_explicit_class_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        source: str,
        *,
        family: c.Infra.FacadeFamily,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> str:
        """Preserve authored class publications without inheriting their owners.

        Returns:
            Source retaining binding names and direct declaration imports.

        Raises:
            ValueError: If a facade base cannot be resolved or does not match any owner.

        """
        project, contents = binding
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=contents, project=project
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations
        )
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        cls._explicit_class_facade(
            project, facade_path, source, declarations, binding=(sources, family)
        )
        scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        ).get_scope()
        if namespace is not facade:
            scope = next(
                child
                for child in scope.get_scopes()
                if child.get_start() == facade.lineno
            )
        published = tuple(
            resolved.get_object()
            for alias in (
                cls._namespace_class_alias(member) for member in namespace.body
            )
            if alias is not None
            for resolved in (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, alias[1]),
            )
            if resolved is not None
        )
        owners = tuple(
            owner
            for owner in cls._declared_facade_owners(project, declarations, sources)
            if any(owner is value for value in published)
        )
        if not owners:
            return cls._inherit_upstream_namespace(project, facade_path, source)
        retained: list[str] = []
        for base in namespace.bases:
            resolved = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                scope, base.value if isinstance(base, ast.Subscript) else base
            )
            if resolved is None:
                message = f"Unresolved facade base: {facade_path}:{ast.unparse(base)}"
                raise ValueError(message)
            if all(resolved.get_object() is not owner for owner in owners):
                retained.append(ast.unparse(base))
        if len(retained) != len(namespace.bases):
            source = cls._declared_facade_render(
                CodemodContext(), source, namespace, retained
            )
        return cls._inherit_upstream_namespace(project, facade_path, source)

    @classmethod
    def _inherit_upstream_namespace(
        cls, project: p.Infra.RopeProject, path: Path, source: str
    ) -> str:
        """Compose upstream package letters and retain their inherited namespace.

        Elect the same-letter export by native class identity, not class spelling.
        A distinct occupied letter uses a lowercase package-qualified import alias;
        it never creates a second runtime facade or wrapper.
        Nested namespaces come from the outer base's declaration-time binding in
        this exact rendered source, never a later write to the exported letter.

        Returns:
            Source with resolved upstream namespaces included as bases.

        Raises:
            ValueError: If the family, package publication or base is unresolved.

        """
        cls._facade_classes(ast.parse(source), path)
        module = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        letters = {
            str(family)
            for family in c.Infra.FacadeFamily
            if family
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(source)
        }
        if len(letters) != 1:
            message = f"Facade has no unique exported family letter: {path}"
            raise ValueError(message)
        source = cls._upstream_import_references(
            project, path, source, module, next(iter(letters))
        )
        facade, namespace = cls._facade_classes(ast.parse(source), path)
        if namespace is facade:
            return source
        module = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        sources = {module.get_name(): (path, source)}
        bases = [ast.unparse(base) for base in namespace.bases]
        for base in facade.bases:
            binding = cls._retired_base_binding(
                project, module, sources, (path, facade), base
            )
            resolved = binding.get_object().get_attributes().get(namespace.name)
            if resolved is not None and FlextInfraUtilitiesRopeRuntime.abstract_class(
                resolved.get_object()
            ):
                name = ast.unparse(
                    ast.Attribute(value=base, attr=namespace.name, ctx=ast.Load())
                )
                if name not in bases:
                    bases.append(name)
        if bases == [ast.unparse(base) for base in namespace.bases]:
            return source
        return cls._declared_facade_render(CodemodContext(), source, namespace, bases)

    @classmethod
    def _upstream_base_imports(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        module: p.Infra.RopePyModule,
        letter: str,
        context: CodemodContext,
    ) -> Generator[
        tuple[
            t.Pair[str, p.Infra.RopePyObject],
            list[ast.Name],
            t.Triple[str, str, str | None],
        ]
    ]:
        """Resolve facade base imports through their publishing package identity.

        Yields:
            Native owners, lexical references and original import declarations.

        Raises:
            ValueError: If a renamed base has no native references.

        """
        source = module.source_code
        facade = cls._facade_classes(ast.parse(source), path)[0]
        base_names = {
            node.id
            for base in facade.bases
            for node in ast.walk(base)
            if isinstance(node, ast.Name)
        }
        for statement in ast.parse(source, filename=str(path)).body:
            if (
                not isinstance(statement, ast.ImportFrom)
                or statement.module is None
                or not any(
                    (alias.asname or alias.name) in base_names
                    for alias in statement.names
                )
            ):
                continue
            origin = (
                resolve_name(
                    f"{'.' * statement.level}{statement.module}", module.get_name()
                )
                if statement.level
                else statement.module
            )
            for alias in statement.names:
                if (alias.asname or alias.name) not in base_names:
                    continue
                publication = cls._upstream_base_publication(
                    project, path, origin, alias.name, letter
                )
                if publication is None:
                    continue
                names = cls._upstream_reference_names(
                    module, source, alias.asname or alias.name, publication[1], context
                )
                if not names and (alias.asname or alias.name) != letter:
                    message = (
                        "Unresolved native upstream base references: "
                        f"{path}:{alias.asname or alias.name}"
                    )
                    raise ValueError(message)
                yield publication, names, (origin, alias.name, alias.asname)

    @staticmethod
    def _upstream_import_references(
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        module: p.Infra.RopePyModule,
        letter: str,
    ) -> str:
        """Schedule package imports without capturing distinct lexical bindings.

        Original Rope imports authorize cleanup requests. Rewrite references and
        add imports together, then let the native unused-import pass retain live
        bindings, exports and string annotations on the resulting source.

        Returns:
            Source with identity-resolved references and package-letter imports.

        Raises:
            ValueError: If a package-qualified letter would capture another owner.

        """
        references: dict[tuple[int, int], str] = {}
        context = CodemodContext(full_package_name=module.get_name().rpartition(".")[0])
        elected: p.Infra.RopePyObject | None = None
        imports: set[t.Pair[str, str]] = set()
        for (
            publication,
            names,
            original_import,
        ) in FlextInfraUtilitiesCodegenFacades._upstream_base_imports(
            project, path, module, letter, context
        ):
            occupied = FlextInfraUtilitiesCodegenFacades._upstream_letter_occupied(
                module, source, names, letter, (path, publication[1])
            )
            occupied |= elected is not None and elected is not publication[1]
            destination = (
                f"{publication[0].replace('.', '_').lower()}_{letter}"
                if occupied
                else letter
            )
            if occupied and (
                FlextInfraUtilitiesCodegenFacades._upstream_letter_occupied(
                    module, source, names, destination, (path, publication[1])
                )
            ):
                message = f"Occupied upstream facade import: {path}:{destination}"
                raise ValueError(message)
            if not occupied:
                elected = publication[1]
            import_alias = destination if destination != letter else None
            if original_import == (publication[0], letter, import_alias):
                continue
            RemoveImportsVisitor.remove_unused_import(context, *original_import)
            references.update(
                ((node.lineno, node.col_offset), destination) for node in names
            )
            request = (publication[0], destination)
            # Native aliased-import requests retain duplicates in their queue.
            if request not in imports:
                AddImportsVisitor.add_needed_import(
                    context,
                    publication[0],
                    letter,
                    asname=import_alias,
                )
                imports.add(request)
        return (
            FlextInfraUtilitiesCodegenFacades._rewrite_upstream_references(
                context, source, references
            )
            if imports
            else source
        )

    @staticmethod
    def _upstream_reference_names(
        module: p.Infra.RopePyModule,
        source: str,
        bound: str,
        owner: p.Infra.RopePyObject,
        context: CodemodContext,
    ) -> list[ast.Name]:
        """Resolve native references and schedule only their imported owners.

        Cleanup still requires the later native unused-import verdict, including
        string annotations and exports. Non-import bindings authorize no removal.

        Returns:
            Names whose lexical resolution retains the imported identity.

        Raises:
            ValueError: If an imported reference has no declared module origin.

        """
        names: list[ast.Name] = []
        for node in ast.walk(ast.parse(source)):
            if not (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == bound
            ):
                continue
            resolved = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                FlextInfraUtilitiesRopeRuntime.scope_at(
                    module,
                    FlextInfraUtilitiesRopeRuntime.source_offset(source, node),
                    declaration_line=node.lineno,
                ),
                node,
            )
            if resolved is None or resolved.get_object() is not owner:
                continue
            names.append(node)
            if not FlextInfraUtilitiesRopeRuntime.imported_name(resolved):
                continue
            imported = resolved.imported_module
            if imported.module_name is None:
                message = f"Upstream reference has no declared import origin: {bound}"
                raise ValueError(message)
            origin = (
                resolve_name(
                    f"{'.' * imported.level}{imported.module_name}",
                    module.get_name().rpartition(".")[0],
                )
                if imported.level
                else imported.module_name
            )
            RemoveImportsVisitor.remove_unused_import(
                context,
                origin,
                resolved.imported_name,
                bound if bound != resolved.imported_name else None,
            )
            if bound == resolved.imported_name:
                # ImportedName omits spelling of explicit ``as SameName`` imports.
                RemoveImportsVisitor.remove_unused_import(
                    context, origin, resolved.imported_name, bound
                )
        return names

    @staticmethod
    def _upstream_letter_occupied(
        module: p.Infra.RopePyModule,
        source: str,
        names: t.SequenceOf[ast.Name],
        letter: str,
        binding: t.Pair[Path, p.Infra.RopePyObject],
    ) -> bool:
        """Preserve lexical collisions except the facade's later own publication.

        Returns:
            Whether replacing a reference would capture an occupied letter.

        """
        facade, _ = FlextInfraUtilitiesCodegenFacades._facade_classes(
            ast.parse(source), binding[0]
        )
        own_aliases = FlextInfraUtilitiesRopeModulePatch.runtime_alias_bindings(
            source, alias=letter
        )
        occupied = False
        for node in names:
            lexical = FlextInfraUtilitiesRopeRuntime.scope_at(
                module,
                FlextInfraUtilitiesRopeRuntime.source_offset(source, node),
                declaration_line=node.lineno,
            )
            existing = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                lexical, ast.Name(id=letter, ctx=ast.Load())
            )
            if existing is None or existing.get_object() is binding[1]:
                continue
            if len(own_aliases) != 1:
                occupied = True
                continue
            if not (
                lexical.get_kind()
                in {c.Infra.RopeScopeKind.MODULE, c.Infra.RopeScopeKind.CLASS}
                and isinstance(own_aliases[0].value, ast.Name)
                and own_aliases[0].value.id == facade.name
                and node.lineno < own_aliases[0].lineno
                and existing.get_object()
                is module.get_scope().get_names()[facade.name].get_object()
            ):
                occupied = True
        return occupied

    @staticmethod
    def _upstream_base_publication(
        project: p.Infra.RopeProject, path: Path, origin: str, name: str, letter: str
    ) -> t.Pair[str, p.Infra.RopePyObject] | None:
        """Resolve a base's same-letter publication by native class identity.

        Returns:
            The publishing package and owner, or no same-letter publication.

        Raises:
            ValueError: If an origin, base or required publication is invalid.

        """
        resource = project.find_module(origin)
        if resource is None:
            message = f"Unresolved facade import origin: {origin}"
            raise ValueError(message)
        binding = (
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(project, resource)
            .get_attributes()
            .get(name)
        )
        if binding is None:
            message = f"Unresolved facade base import: {origin}:{name}"
            raise ValueError(message)
        owner = binding.get_object()
        publisher = origin
        package = resource
        if not package.is_folder():
            publisher = publisher.rpartition(".")[0]
            package = project.find_module(publisher)
        if package is None:
            message = f"Facade base has no publishing package: {origin}"
            raise ValueError(message)
        exported = (
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(project, package)
            .get_attributes()
            .get(letter)
        )
        if exported is None or exported.get_object() is not owner:
            if FlextInfraUtilitiesRopeRuntime.py_class(owner):
                declared = owner.get_module().get_attributes().get(letter)
                if declared is not None and declared.get_object() is owner:
                    message = (
                        "Upstream facade letter is not published by its "
                        f"package: {publisher}:{letter}"
                    )
                    raise ValueError(message)
            return None
        if Path(package.real_path).resolve() == path.parent.resolve():
            message = f"Facade cannot compose its own package letter: {path}"
            raise ValueError(message)
        return publisher, owner

    @staticmethod
    def _rewrite_upstream_references(
        context: CodemodContext,
        source: str,
        references: t.MappingKV[tuple[int, int], str],
    ) -> str:
        """Batch reference and import edits before one native unused-import pass.

        Returns:
            Source with matching references and their scheduled import changes.

        """
        wrapper = MetadataWrapper(parse_module(source))
        lines = source.splitlines()
        replacements = {
            node: references[key]
            for node, span in wrapper.resolve(PositionProvider).items()
            if isinstance(node, Name)
            and (
                key := (
                    span.start.line,
                    len(lines[span.start.line - 1][: span.start.column].encode()),
                )
            )
            in references
        }

        class RewriteNames(AddImportsVisitor):
            """Replace authenticated references while adding their native imports."""

            @override
            def leave_Name(
                self, original_node: t.Infra.Cst.Name, updated_node: t.Infra.Cst.Name
            ) -> t.Infra.Cst.Name:
                """Return the scheduled name or preserve the existing spelling.

                Returns:
                    The reference with its authenticated destination name.

                """
                return updated_node.with_changes(
                    value=replacements.get(original_node, updated_node.value)
                )

        updated: t.Infra.CstModule = wrapper.module.visit(RewriteNames(context))
        return RemoveImportsVisitor(context).transform_module(updated).code

    @classmethod
    def _generated_facade(
        cls,
        pkg_dir: Path,
        source: str,
        *,
        family: c.Infra.FacadeFamily,
        contents: t.MappingKV[Path, str],
        project: p.Infra.RopeProject,
    ) -> str:
        """Import composed family owners through the family package's lazy exports.

        Authored declarations and unrelated imports retain their syntax. The
        namespace rule catalog owns their architecture checks; generation only
        rewires the component imports the family package initializer publishes,
        so the facade imports ``pkg._family`` (its lazy ``__init__``), never a
        per-module path.

        Returns:
            Generated composition carrying the canonical ownership marker.

        """
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        _, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=contents, project=project
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations
        )
        source = cls._wrap_facade_imports(
            cls._merged_facade_imports(cls._canonical_exports(source))
        )
        if source.startswith(c.Infra.AUTOGEN_HEADER):
            return source
        return f"{c.Infra.AUTOGEN_HEADER}\n{source}"

    @staticmethod
    def _canonical_exports(source: str) -> str:
        """Publish the facade module's ``__all__`` in its one canonical form.

        A generated facade declares ``__all__: list[str] = [...]``; any other
        annotation or container is rewritten to it, keeping the exported names
        and their order. Imports that only the replaced annotation used are
        removed, and a ``TYPE_CHECKING`` block left empty goes with its guard
        import, so the facade never imports a foreign namespace just to
        annotate ``__all__``.

        Returns:
            Source whose module ``__all__`` uses the canonical form.

        Raises:
            ValueError: If the module ``__all__`` is not a literal sequence of names.

        """
        wrapper = MetadataWrapper(parse_module(source))
        module = wrapper.module
        exports = [
            (index, line.body[0])
            for index, line in enumerate(module.body)
            if isinstance(line, SimpleStatementLine)
            and len(line.body) == 1
            and isinstance(line.body[0], Assign | AnnAssign)
            and any(
                isinstance(target, Name) and target.value == "__all__"
                for target in (
                    (item.target for item in line.body[0].targets)
                    if isinstance(line.body[0], Assign)
                    else (line.body[0].target,)
                )
            )
        ]
        if len(exports) != 1:
            return source
        index, statement = exports[0]
        if statement.value is None:
            msg = "facade __all__ declares no exported names"
            raise ValueError(msg)
        names = ast.literal_eval(module.code_for_node(statement.value))
        if not isinstance(names, (list, tuple)) or not all(
            isinstance(name, str) for name in names
        ):
            msg = f"facade __all__ is not a literal sequence of names: {names!r}"
            raise ValueError(msg)
        canonical = parse_statement(
            f"__all__: list[str] = [{', '.join(f'"{name}"' for name in names)}]\n"
        )
        if module.code_for_node(module.body[index]) == module.code_for_node(canonical):
            return source
        context = CodemodContext(wrapper=wrapper)
        if isinstance(statement, AnnAssign):
            RemoveImportsVisitor.remove_unused_import_by_node(
                context, statement.annotation.annotation
            )
        updated = RemoveImportsVisitor(context).transform_module(
            module.with_changes(
                body=(*module.body[:index], canonical, *module.body[index + 1 :])
            )
        )
        retained = tuple(
            line
            for line in updated.body
            if not (
                isinstance(line, If)
                and isinstance(line.test, Name)
                and line.test.value == c.Infra.TYPING_GUARD_NAME
                and line.orelse is None
                and not line.body.body
            )
        )
        if len(retained) == len(updated.body):
            return updated.code
        guard_context = CodemodContext()
        RemoveImportsVisitor.remove_unused_import(
            guard_context, c.Infra.TYPING_GUARD_MODULE, c.Infra.TYPING_GUARD_NAME
        )
        return (
            RemoveImportsVisitor(guard_context)
            .transform_module(updated.with_changes(body=retained))
            .code
        )

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

        """
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()["p"].directory
        )
        _, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=binding[1], project=binding[0]
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations
        )
        owners, _ = cls._facade_protocol_owners(
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                c.Infra.FacadeFamily.P
            ].directory,
            binding[1],
            project=binding[0],
        )
        project = binding[0]
        facade, namespace, scope, typing_objects, base_objects, markers = (
            cls._facade_namespace_context(project, source, facade_path)
        )
        if not any(
            isinstance(member, c.Infra.AST_FUNCTION_TYPES)
            or (
                isinstance(member, ast.AnnAssign)
                and cls._namespace_class_alias(member) is None
            )
            for member in namespace.body
        ) and (
            any(
                owner is not typing_objects[0]
                and typing_objects[0]
                not in FlextInfraUtilitiesRopeRuntime.require_class_object(
                    owner, "protocol namespace base"
                ).get_superclasses()
                for owner in base_objects
            )
            or any(
                isinstance(member, ast.ClassDef)
                or (
                    (alias := cls._namespace_class_alias(member)) is not None
                    and (
                        resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                            scope, alias[1]
                        )
                    )
                    is not None
                    and typing_objects[0]
                    in FlextInfraUtilitiesRopeRuntime.require_class_object(
                        resolved.get_object(), "protocol namespace alias"
                    ).get_superclasses()
                )
                for member in namespace.body
            )
        ):
            source = cls._strip_protocol_namespace_markers(
                source, namespace, base_objects, typing_objects, scope
            )
            facade, namespace = cls._facade_classes(
                ast.parse(source, filename=str(facade_path)),
                facade_path,
                ignored_bases=markers,
            )
        additions = cls._select_protocol_owner_bases(
            facade_path,
            (facade, namespace),
            owners=owners,
            namespace_bindings=(scope, cls._protocol_ancestor_objects(base_objects)),
            binding=binding,
        )
        if not additions:
            return cls._remove_namespace_class_shadows(
                source, namespace, scope, base_objects, family="protocol"
            )
        package = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(
                pkg_dir.relative_to(Path(project.root.real_path)).as_posix()
            ),
        ).get_name()
        source = cls._insert_protocol_imports(source, additions, package=package)
        _, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
            ignored_bases=markers,
        )
        return cls._render_protocol_facade(
            pkg_dir,
            facade_path,
            cls._insert_bases(source, namespace, additions),
            binding=binding,
        )

    @classmethod
    def _facade_namespace_context(
        cls,
        project: p.Infra.RopeProject,
        source: str,
        facade_path: Path,
    ) -> tuple[
        ast.ClassDef,
        ast.ClassDef,
        p.Infra.RopeScope,
        t.Pair[p.Infra.RopePyObject, p.Infra.RopePyObject],
        tuple[p.Infra.RopePyObject, ...],
        frozenset[str],
    ]:
        """Resolve namespace roles and native typing identities before rewriting.

        Returns:
            The facade, namespace, lexical scope, typing identities, bases and markers.

        Raises:
            ValueError: If an authored namespace base cannot be resolved.

        """
        module = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        scope = module.get_scope()
        typing_objects = cls._protocol_typing_objects(project)
        # An interface marker shared by nested contracts is not a namespace owner.
        markers = frozenset(
            ast.unparse(base)
            for node in ast.parse(source, filename=str(facade_path)).body
            if isinstance(node, ast.ClassDef)
            for base in node.bases
            if (resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, base))
            is not None
            and resolved.get_object() is typing_objects[0]
        )
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
            ignored_bases=markers,
        )
        if namespace is not facade:
            scope = next(
                child
                for child in scope.get_scopes()
                if child.get_start() == facade.lineno
            )
        namespace_scope = next(
            child
            for child in scope.get_scopes()
            if child.get_start() == namespace.lineno
        )
        base_objects = tuple(
            FlextInfraUtilitiesRopeRuntime.require_class_object(
                namespace_scope.pyobject, f"facade namespace: {facade_path}"
            ).get_superclasses()
        )
        if len(base_objects) != len(namespace.bases):
            message = (
                f"Unresolved native facade bases: {facade_path}:{namespace.name}; "
                f"declared={tuple(ast.unparse(base) for base in namespace.bases)}; "
                f"resolved={len(base_objects)}"
            )
            raise ValueError(message)
        for position, (base, owner) in enumerate(
            zip(namespace.bases, base_objects, strict=True), start=1
        ):
            FlextInfraUtilitiesRopeRuntime.require_class_object(
                owner,
                f"facade base {position}: {facade_path}:{namespace.name}; "
                f"expression={ast.unparse(base)}; "
                f"SDK type={type(owner).__module__}.{type(owner).__qualname__}; "
                "resource=None",
            )
        return facade, namespace, scope, typing_objects, base_objects, markers

    @staticmethod
    def _protocol_typing_objects(
        project: p.Infra.RopeProject,
    ) -> t.Pair[p.Infra.RopePyObject, p.Infra.RopePyObject]:
        """Resolve the native typing identities.

        Returns:
            Protocol and runtime_checkable from the native semantic graph.

        """
        module = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project, "from typing import Protocol, runtime_checkable\n"
        )
        names = module.get_scope().get_names()
        return names["Protocol"].get_object(), names["runtime_checkable"].get_object()

    @staticmethod
    def _protocol_ancestor_objects(
        base_objects: tuple[p.Infra.RopePyObject, ...],
    ) -> list[p.Infra.RopePyObject]:
        """Collect inherited owners without admitting a same-named declaration.

        Returns:
            The exact transitive superclass identities of the namespace bases.

        Raises:
            TypeError: An elected ancestor lacks the native class capability.

        """
        inherited: list[p.Infra.RopePyObject] = []
        pending: list[t.Pair[p.Infra.RopePyObject, p.Infra.RopeClassObject | None]] = [
            (owner, None) for owner in base_objects
        ]
        while pending:
            owner, introducing = pending.pop(0)
            if owner not in inherited:
                inherited.append(owner)
                try:
                    native = FlextInfraUtilitiesRopeRuntime.require_class_object(
                        owner, "protocol ancestor"
                    )
                except TypeError as error:
                    error.add_note(
                        "Rejected ancestor SDK type: "
                        f"{type(owner).__module__}.{type(owner).__qualname__}; "
                        "resource=None"
                    )
                    if introducing is not None:
                        error.add_note(
                            f"Introducing class: {introducing.get_name()}; "
                            f"SDK type={type(introducing).__module__}."
                            f"{type(introducing).__qualname__}; "
                            "resource=None"
                        )
                    raise
                pending.extend((base, native) for base in native.get_superclasses())
        return inherited

    @staticmethod
    def _strip_protocol_namespace_markers(
        source: str,
        namespace: ast.ClassDef,
        base_objects: tuple[p.Infra.RopePyObject, ...],
        typing_objects: t.Pair[p.Infra.RopePyObject, p.Infra.RopePyObject],
        scope: p.Infra.RopeScope,
    ) -> str:
        """Remove interface markers only from the selected plain namespace.

        Returns:
            The namespace source without invalid protocol markers or decorators.

        Raises:
            TypeError: If the concrete rewrite does not preserve the source module.

        """
        protocol_decorators = {
            ast.unparse(decorator)
            for decorator in namespace.decorator_list
            if (
                resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    scope, decorator
                )
            )
            is not None
            and resolved.get_object() is typing_objects[1]
        }
        wrapper = MetadataWrapper(parse_module(source))
        for node, span in wrapper.resolve(PositionProvider).items():
            if not isinstance(node, ClassDef) or span.start.line != namespace.lineno:
                continue
            replacement = node.with_changes(
                bases=tuple(
                    base
                    for base in node.bases
                    if base_objects[node.bases.index(base)] is not typing_objects[0]
                ),
                decorators=tuple(
                    decorator
                    for decorator in node.decorators
                    if wrapper.module.code_for_node(decorator.decorator)
                    not in protocol_decorators
                ),
            )
            updated = wrapper.module.deep_replace(node, replacement)
            if not isinstance(updated, Module):
                message = "protocol namespace projection did not preserve the module"
                raise TypeError(message)
            source = updated.code
            break
        context = CodemodContext()
        for name in (c.Infra.PROTOCOL_BASE, "runtime_checkable"):
            RemoveImportsVisitor.remove_unused_import(context, "typing", name)
        return RemoveImportsVisitor(context).transform_module(parse_module(source)).code

    @staticmethod
    def _namespace_class_alias(
        member: ast.stmt,
        *,
        generated: bool = False,
    ) -> t.Triple[str, ast.expr, ast.expr | None] | None:
        """Read only direct class bindings, without admitting calls or PEP 695 aliases.

        A PEP 613 ``Name: TypeAlias = Owner`` publication is the canonical form
        (``_publish_namespace_aliases``); bare and ``type[...]`` bindings are
        read so generation can derive it from them.
        Generated facades also admit undecorated, non-generic subclasses whose
        only body statement is a docstring; authored classes keep their identity.

        Returns:
            The name, RHS and optional class annotation, or no supported binding.

        """
        if (
            isinstance(member, ast.AnnAssign)
            and isinstance(member.annotation, ast.Subscript)
            and isinstance(member.annotation.value, ast.Name)
            and member.annotation.value.id == "ClassVar"
        ):
            member = ast.AnnAssign(
                target=member.target,
                annotation=member.annotation.slice,
                value=member.value,
                simple=member.simple,
            )
        match member:
            case ast.ClassDef(
                name=name,
                bases=[(ast.Name() | ast.Attribute()) as value],
                decorator_list=[],
                keywords=[],
                type_params=[],
                body=[ast.Expr(value=ast.Constant(value=str()))],
            ) if generated:
                return name, value, None
            case ast.Assign(
                targets=[ast.Name(id=name)],
                value=(ast.Name() | ast.Attribute()) as value,
            ):
                return name, value, None
            case ast.AnnAssign(
                target=ast.Name(id=name),
                annotation=ast.Name(id="TypeAlias") | ast.Attribute(attr="TypeAlias"),
                value=(ast.Name() | ast.Attribute()) as value,
            ):
                return name, value, None
            case ast.AnnAssign(
                target=ast.Name(id=name),
                annotation=ast.Subscript(value=ast.Name(id="type"), slice=annotation),
                value=(ast.Name() | ast.Attribute()) as value,
            ):
                return name, value, annotation
            case _:
                return None

    @classmethod
    def _publish_namespace_aliases(
        cls, project: p.Infra.RopeProject, facade_path: Path, source: str
    ) -> str:
        """Derive ``Name: TypeAlias = Owner`` for every facade class publication.

        mypy types a bare or ``type[...]``-annotated class-scope binding as a
        variable, so ``c.Ns.Name.Member`` stops being a type; PEP 613 is the form
        mypy, pyright and pyrefly all type while binding the identical class.
        A bare binding of a class, or an annotated one whose ``type[...]`` names
        the bound class, derives that declaration one to one (generator law
        point 10). Ruff never autofixes it into a PEP 695 ``type`` statement,
        which would replace the class with a ``TypeAliasType``: UP040 is
        unfixable at the tooling SSOT and its findings on these publications
        are exempt only per authenticated identity (operator 2026-10-25,
        "Exceção UP040 por identidade"). Anything else keeps its form for the
        shadow removal and explicit-publication validation to judge.

        Returns:
            Source publishing every derivable facade class as a PEP 613 alias.

        """
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        candidates = [
            (owner is facade, member, binding)
            for owner in ((facade,) if namespace is facade else (facade, namespace))
            for member in owner.body
            if (
                binding := (
                    (member.name.id, member.value, None)
                    if isinstance(member, ast.TypeAlias)
                    and not member.type_params
                    and isinstance(member.value, ast.Name | ast.Attribute)
                    else None
                    if isinstance(member, ast.AnnAssign)
                    and isinstance(member.annotation, ast.Name | ast.Attribute)
                    else cls._namespace_class_alias(member)
                )
            )
            is not None
            and binding[0] != "model_config"
        ]
        if not candidates:
            return source
        module_scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        ).get_scope()
        facade_scope = next(
            child
            for child in module_scope.get_scopes()
            if child.get_start() == facade.lineno
        )
        publications: list[ast.stmt] = []
        for in_facade, member, (_, reference, declared) in candidates:
            scope = module_scope if in_facade else facade_scope
            value = FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, reference)
            target = value.get_object() if value is not None else None
            if target is None or not FlextInfraUtilitiesRopeRuntime.abstract_class(
                target
            ):
                continue
            annotated = (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, declared)
                if declared is not None
                else value
            )
            if annotated is not None and annotated.get_object() is target:
                publications.append(member)
        if not publications:
            return source
        return cls._alias_publication_statements(source, publications)

    @staticmethod
    def _alias_publication_statements(
        source: str, publications: t.SequenceOf[ast.stmt]
    ) -> str:
        """Rewrite selected class bindings to PEP 613 aliases in one traversal.

        Returns:
            Source with ``TypeAlias`` annotations and import, removing only the
            imports the replaced annotations left unused.

        """
        wrapper = MetadataWrapper(parse_module(source))
        lines = source.splitlines()
        positions = {(member.lineno, member.col_offset) for member in publications}
        context = CodemodContext(wrapper=wrapper)
        selected: set[CSTNode] = set()
        for node, span in wrapper.resolve(PositionProvider).items():
            if (
                not isinstance(node, Assign | AnnAssign | TypeAlias)
                or (
                    span.start.line,
                    len(lines[span.start.line - 1][: span.start.column].encode()),
                )
                not in positions
            ):
                continue
            if isinstance(node, AnnAssign):
                RemoveImportsVisitor.remove_unused_import_by_node(
                    context, node.annotation.annotation
                )
            selected.add(node)

        class PublishAliases(CSTTransformer):
            """Annotate each selected class binding as a PEP 613 alias."""

            @override
            def leave_TypeAlias(
                self, original_node: TypeAlias, updated_node: TypeAlias
            ) -> TypeAlias | AnnAssign:
                if original_node not in selected:
                    return updated_node
                return AnnAssign(
                    target=updated_node.name,
                    annotation=Annotation(Name("TypeAlias")),
                    value=updated_node.value,
                )

            @override
            def leave_Assign(
                self, original_node: Assign, updated_node: Assign
            ) -> Assign | AnnAssign:
                if original_node not in selected:
                    return updated_node
                return AnnAssign(
                    target=updated_node.targets[0].target,
                    annotation=Annotation(Name("TypeAlias")),
                    value=updated_node.value,
                )

            @override
            def leave_AnnAssign(
                self, original_node: AnnAssign, updated_node: AnnAssign
            ) -> AnnAssign:
                if original_node not in selected:
                    return updated_node
                return updated_node.with_changes(
                    annotation=Annotation(Name("TypeAlias"))
                )

        updated = wrapper.module.visit(PublishAliases())
        AddImportsVisitor.add_needed_import(context, "typing", "TypeAlias")
        updated = AddImportsVisitor(context).transform_module(updated)
        return RemoveImportsVisitor(context).transform_module(updated).code

    @classmethod
    def facade_class_publications(
        cls, root: Path, rows: t.MappingKV[Path, frozenset[int]]
    ) -> frozenset[t.Triple[Path, int, int]]:
        """Authenticate PEP 613 facade class publications at reported rows.

        A publication is ``Name: TypeAlias = Owner`` declared directly in an
        explicitly published facade class or in its nested namespace class, with
        ``TypeAlias`` bound by the module's own ``from typing import`` and
        ``Owner`` resolving, by native Rope identity, to a class. The existing
        publication owner authenticates the exported family alias and local class
        independently of the filename. Other classes, statements and unresolved
        owners authenticate nothing.

        Returns:
            Resolved path, row and one-based column of each authenticated
            publication.

        """
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        selected = {path.resolve(): wanted for path, wanted in rows.items() if wanted}
        if not selected:
            return frozenset()
        publications: set[t.Triple[Path, int, int]] = set()
        with cls.facade_source_project(root) as (project, sources):
            for path, wanted in sorted(selected.items()):
                source = sources[path]
                resource = project.get_file(
                    path.relative_to(Path(project.root.real_path)).as_posix()
                )
                published = (
                    FlextInfraUtilitiesRopeAnalysisImportState.published_facade_owner(
                        project, resource
                    )
                )
                if published is None or published[0] not in families:
                    continue
                tree = ast.parse(source, filename=str(path))
                if not any(
                    isinstance(node, ast.ImportFrom)
                    and node.module == "typing"
                    and not node.level
                    and any(
                        alias.name == "TypeAlias" and alias.asname is None
                        for alias in node.names
                    )
                    for node in tree.body
                ):
                    continue
                module_scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
                    project,
                    source,
                    resource=resource,
                ).get_scope()
                for owner in tree.body:
                    if not (
                        isinstance(owner, ast.ClassDef) and owner.name == published[1]
                    ):
                        continue
                    owner_scope = next(
                        child
                        for child in module_scope.get_scopes()
                        if child.get_start() == owner.lineno
                    )
                    members: list[t.Pair[p.Infra.RopeScope, ast.stmt]] = [
                        (module_scope, member) for member in owner.body
                    ]
                    members.extend(
                        (owner_scope, nested_member)
                        for nested in owner.body
                        if isinstance(nested, ast.ClassDef)
                        for nested_member in nested.body
                    )
                    for scope, member in members:
                        if cls._facade_class_publication(scope, member, wanted):
                            publications.add((
                                path,
                                member.lineno,
                                member.col_offset + 1,
                            ))
        return frozenset(publications)

    @staticmethod
    def _facade_class_publication(
        scope: p.Infra.RopeScope, member: ast.stmt, wanted: frozenset[int]
    ) -> bool:
        """Authenticate a selected PEP 613 binding against its native class owner.

        Returns:
            Whether the selected statement publishes a resolved native class.

        """
        if not isinstance(member, ast.AnnAssign):
            return False
        if not (
            member.lineno in wanted
            and isinstance(member.target, ast.Name)
            and isinstance(member.annotation, ast.Name)
            and member.annotation.id == "TypeAlias"
            and isinstance(member.value, ast.Name | ast.Attribute)
        ):
            return False
        value = FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, member.value)
        return value is not None and FlextInfraUtilitiesRopeRuntime.abstract_class(
            value.get_object()
        )

    @classmethod
    def _inherited_namespace_members(
        cls,
        base_objects: tuple[p.Infra.RopePyObject, ...],
        names: frozenset[str],
    ) -> t.MutableMappingKV[str, p.Infra.RopePyObject]:
        """Resolve effective inherited declarations in native-identity C3 order.

        Returns:
            The first actual declaration of each inherited name, not a DFS alias.

        """
        owners = {
            str(id(owner)): owner
            for owner in cls._protocol_ancestor_objects(base_objects)
        }
        lineages: t.MutableMappingKV[str, t.StrTuple] = {}

        def lineage(bases: t.SequenceOf[p.Infra.RopePyObject]) -> t.StrTuple:
            for base in bases:
                identity = str(id(base))
                if identity not in lineages:
                    lineages[identity] = (
                        identity,
                        *lineage(
                            FlextInfraUtilitiesRopeRuntime.require_class_object(
                                base, "namespace C3 ancestor"
                            ).get_superclasses()
                        ),
                    )
            return FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                [
                    *(lineages[str(id(base))] for base in bases),
                    tuple(str(id(base)) for base in bases),
                ],
                message="Inconsistent facade namespace class lineage",
            )

        members: t.MutableMappingKV[str, p.Infra.RopePyObject] = {}
        for identity in lineage(base_objects):
            owner = owners[identity]
            scope = (
                owner.get_scope()
                if FlextInfraUtilitiesRopeRuntime.py_class(owner)
                else None
            )
            attributes = (
                scope.get_defined_names()
                if scope is not None
                else owner.get_attributes()
            )
            for name in names:
                if name not in members and name in attributes:
                    members[name] = attributes[name].get_object()
        return members

    @classmethod
    def _remove_namespace_class_shadows(
        cls,
        source: str,
        namespace: ast.ClassDef,
        scope: p.Infra.RopeScope,
        base_objects: tuple[p.Infra.RopePyObject, ...],
        *,
        family: Literal["protocol", "model", "utility"],
    ) -> str:
        """Keep declared owners authoritative over their generated class bindings.

        A utility publication retires only when the same name inherits the same
        class object. Being a namespace base does not make its alias redundant.

        Returns:
            Source without derived class bindings or proven redundant assignments.

        Raises:
            ValueError: If an authored contract assignment is unresolved or ambiguous.

        """
        generated = source.startswith(c.Infra.AUTOGEN_HEADER)
        aliases = [
            (member, alias)
            for member in namespace.body
            if (alias := cls._namespace_class_alias(member, generated=generated))
            is not None
        ]
        if not aliases:
            return source
        inherited = cls._inherited_namespace_members(
            base_objects, frozenset(alias[0] for _, alias in aliases)
        )
        owners = cls._protocol_ancestor_objects(base_objects)
        shadows: list[ast.stmt] = []
        for member, alias in aliases:
            name, expression, annotation = alias
            shadowed = (
                generated
                and name in inherited
                and FlextInfraUtilitiesRopeRuntime.abstract_class(inherited[name])
            )
            value = FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, expression)
            target = value.get_object() if value is not None else None
            inherited_class = (
                target is not None
                and FlextInfraUtilitiesRopeRuntime.abstract_class(target)
                and any(
                    target is attribute.get_object()
                    for owner in owners
                    for attribute in owner.get_attributes().values()
                )
            )
            resolved = (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, expression.value)
                if isinstance(expression, ast.Attribute)
                else None
            )
            retired_member = (
                resolved is not None
                and resolved.get_object() in owners
                and isinstance(expression, ast.Attribute)
                and expression.attr not in resolved.get_object().get_attributes()
            )
            shadowed = shadowed or inherited_class or retired_member
            if (
                generated
                and shadowed
                and (
                    family != "utility"
                    or (target is not None and target is inherited.get(name))
                )
            ):
                # A projection cannot turn an inherited declaration into a new
                # alias or replace a different canonical member with its value.
                shadows.append(member)
                continue
            resolved = (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, annotation)
                if annotation is not None
                else value
            )
            if value is None or resolved is None:
                if annotation is not None:
                    message = f"Unresolved {family} class attribute: {name}"
                    raise ValueError(message)
                continue
            target = value.get_object()
            if not FlextInfraUtilitiesRopeRuntime.abstract_class(target):
                continue
            if target is not resolved.get_object():
                message = (
                    f"ambiguous {family} class attribute {name}: "
                    "annotation does not identify the declared contract"
                )
                raise ValueError(message)
            if target is inherited.get(name):
                shadows.append(member)
            elif inherited_class and (family != "utility" or name in inherited):
                message = (
                    f"ambiguous {family} class attribute {name}: "
                    "value does not identify the inherited contract"
                )
                raise ValueError(message)
        return cls._remove_shadow_statements(source, shadows) if shadows else source

    @staticmethod
    def _remove_shadow_statements(source: str, shadows: t.SequenceOf[ast.stmt]) -> str:
        """Remove proven shadows and prune only imports belonging to those nodes.

        Returns:
            Source with the selected derived bindings and unused imports removed.

        """
        wrapper = MetadataWrapper(parse_module(source))
        removals: set[CSTNode] = set()
        lines = source.splitlines()
        positions = {(member.lineno, member.col_offset) for member in shadows}
        context = CodemodContext(wrapper=wrapper)
        for node, span in wrapper.resolve(PositionProvider).items():
            if (
                not isinstance(node, Assign | AnnAssign | ClassDef)
                or (
                    span.start.line,
                    len(lines[span.start.line - 1][: span.start.column].encode()),
                )
                not in positions
            ):
                continue
            if isinstance(node, ClassDef):
                for base in node.bases:
                    RemoveImportsVisitor.remove_unused_import_by_node(
                        context, base.value
                    )
            elif node.value is not None:
                RemoveImportsVisitor.remove_unused_import_by_node(context, node.value)
            if isinstance(node, AnnAssign):
                RemoveImportsVisitor.remove_unused_import_by_node(
                    context, node.annotation.annotation
                )
            removals.add(node)

        class RemoveShadows(CSTTransformer):
            """Remove proven bindings in one identity-preserving traversal."""

            @override
            def on_leave[CSTNodeT: CSTNode](
                self, original_node: CSTNodeT, updated_node: CSTNodeT
            ) -> CSTNodeT | RemovalSentinel:
                if original_node in removals:
                    return RemovalSentinel.REMOVE
                return updated_node

        updated = wrapper.module.visit(RemoveShadows())
        return RemoveImportsVisitor(context).transform_module(updated).code

    @staticmethod
    def _declared_namespace_members(namespace: ast.ClassDef) -> set[str]:
        """Inventory declarations that must not be replaced by provider imports.

        Returns:
            The public and private names already declared in the namespace body.

        """
        declared = {
            member.name
            for member in namespace.body
            if isinstance(member, c.Infra.AST_DEFINITION_TYPES)
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
        return declared

    @classmethod
    def _select_protocol_owner_bases(
        cls,
        facade_path: Path,
        facades: t.Pair[ast.ClassDef, ast.ClassDef],
        *,
        owners: t.VariadicTuple[t.Triple[str, str, frozenset[str]]],
        namespace_bindings: t.Pair[p.Infra.RopeScope, list[p.Infra.RopePyObject]],
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> list[t.Pair[str, str]]:
        """Select unique missing owners from admitted native semantic modules.

        Returns:
            The unique provider modules and class names required by consumers.

        Raises:
            ValueError: If multiple providers own a missing namespace member.

        """
        facade, namespace = facades
        scope, inherited = namespace_bindings
        pkg_dir = facade_path.parent
        additions: list[t.Pair[str, str]] = []
        declared = cls._declared_namespace_members(namespace)
        aliases = {
            alias[0]: alias[1]
            for member in namespace.body
            if (alias := cls._namespace_class_alias(member)) is not None
        }
        protocols_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                c.Infra.FacadeFamily.P
            ].directory
        )
        for method in sorted(
            set(aliases)
            | cls._required_protocol_members(
                pkg_dir,
                facade_path,
                nested_namespace=namespace is not facade,
                namespace=namespace.name,
                binding=binding,
            ),
        ):
            candidates = tuple(
                (
                    module,
                    class_name,
                    FlextInfraUtilitiesRopeRuntime
                    .require_semantic_module(
                        binding[0].get_pymodule(
                            binding[0].get_resource(
                                (protocols_dir / Path(*module.split(".")))
                                .with_suffix(c.Infra.EXT_PYTHON)
                                .relative_to(Path(binding[0].root.real_path))
                                .as_posix()
                            )
                        )
                    )
                    .get_attributes()[class_name]
                    .get_object(),
                )
                for module, class_name, methods in owners
                if method in methods
            )
            if method in declared:
                expression = aliases.get(method)
                value = (
                    FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, expression)
                    if expression is not None
                    else None
                )
                if value is None or not FlextInfraUtilitiesRopeRuntime.abstract_class(
                    value.get_object()
                ):
                    continue
                candidates = tuple(
                    candidate
                    for candidate in candidates
                    if method in candidate[2].get_attributes()
                    and candidate[2].get_attributes()[method].get_object()
                    is value.get_object()
                )
            if not candidates or any(owner in inherited for _, _, owner in candidates):
                continue
            if len(candidates) != 1:
                message = (
                    f"ambiguous {c.Infra.FacadeFamily.P}.{namespace.name} "
                    f"owner for {method}: "
                    + ", ".join(f"{module}:{name}" for module, name, _ in candidates)
                )
                raise ValueError(message)
            if candidates[0][:2] not in additions:
                additions.append(candidates[0][:2])
        return additions

    @classmethod
    def _render_declared_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        source: str,
        *,
        family: c.Infra.FacadeFamily,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> str:
        """Compose explicitly exported declarations without reverse family imports.

        Returns:
            A facade whose direct owners preserve the existing source C3 order.

        """
        owners_dir = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[family].directory
        )
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=binding[1], project=binding[0]
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations
        )
        sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
        if cls._explicit_class_facade(
            binding[0], facade_path, source, declarations, binding=(sources, family)
        ):
            return cls._render_explicit_class_facade(
                pkg_dir, facade_path, source, family=family, binding=binding
            )
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        if family in {
            c.Infra.FacadeFamily.C,
            c.Infra.FacadeFamily.M,
            c.Infra.FacadeFamily.U,
        }:
            declarations = cls._namespace_component_declarations(
                binding[0],
                (facade_path, source),
                declarations,
                sources=sources,
                family=family,
            )
        retired = cls._retired_owned_bases(
            binding[0],
            sources,
            (pkg_dir, owners_dir),
            (facade_path, namespace),
            {item.qualified_base for item in declarations},
        )
        if retired:
            source, context = cls._retired_facade_projection(
                package_name, source, namespace, retired
            )
            sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
            facade, namespace = cls._facade_classes(
                ast.parse(source, filename=str(facade_path)),
                facade_path,
            )
        else:
            context = CodemodContext(full_package_name=package_name)
        contract = cls._declared_facade_contract(
            cls._independent_publishers(
                pkg_dir, owners_dir, sources, package_name=package_name
            ),
            declarations,
            facade,
            namespace,
            facade_target=f"{package_name}.{facade_path.stem}",
        )
        source = cls._reorder_declared_facade(
            context,
            source,
            namespace,
            contract,
            ordering=(
                FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_order(
                    binding[0], sources, contract[0]
                ),
                bool(retired),
            ),
        )
        if family in {c.Infra.FacadeFamily.M, c.Infra.FacadeFamily.U}:
            source = cls._remove_rendered_namespace_class_shadows(
                binding[0],
                source,
                facade_path,
                family="model" if family is c.Infra.FacadeFamily.M else "utility",
            )
        source = cls._collapse_inherited_owner_references(
            binding[0], facade_path, source
        )
        return cls._wrap_facade_imports(source)

    @classmethod
    def _collapse_inherited_owner_references(
        cls, project: p.Infra.RopeProject, facade_path: Path, source: str
    ) -> str:
        """Remove absent inherited qualifiers only after native identity proof.

        Returns:
            Source retaining each declaration's effective native class owner.

        """
        module = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        facade, _ = cls._facade_classes(ast.parse(source), facade_path)
        collapsed = set()
        for owner in ast.walk(facade):
            if not isinstance(owner, ast.ClassDef):
                continue
            for field in owner.body:
                if (
                    not isinstance(field, c.Infra.AST_ASSIGNMENT_TYPES)
                    or field.value is None
                ):
                    continue
                receivers = {
                    child.value
                    for child in ast.walk(field.value)
                    if isinstance(child, ast.Attribute)
                }
                for node in ast.walk(field.value):
                    if not (
                        isinstance(node, ast.Attribute)
                        and isinstance(node.ctx, ast.Load)
                        and node not in receivers
                    ):
                        continue
                    qualifier = cls._inherited_owner_reference(module, source, node)
                    if qualifier is not None:
                        collapsed.add((
                            qualifier.end_lineno,
                            qualifier.end_col_offset,
                        ))
        if collapsed:
            wrapper = MetadataWrapper(parse_module(source))
            lines = source.splitlines()
            selected = {
                node
                for node, span in wrapper.resolve(PositionProvider).items()
                if isinstance(node, Attribute)
                and (
                    span.end.line,
                    len(lines[span.end.line - 1][: span.end.column].encode()),
                )
                in collapsed
            }

            class CollapseOwner(CSTTransformer):
                """Remove only identity-authenticated, absent owner qualifiers."""

                @override
                def leave_Attribute(
                    self, original_node: Attribute, updated_node: Attribute
                ) -> BaseExpression:
                    """Return the receiver of an authenticated reference."""
                    return (
                        updated_node.value
                        if original_node in selected
                        else updated_node
                    )

            source = wrapper.module.visit(CollapseOwner()).code
        return source

    @staticmethod
    def _inherited_owner_reference(
        module: p.Infra.RopePyModule, source: str, node: ast.Attribute
    ) -> ast.Attribute | None:
        """Authenticate an absent qualifier and its complete inherited member path.

        Returns:
            The absent qualifier when its entire tail retains declaration identity.

        """
        scope = FlextInfraUtilitiesRopeRuntime.scope_at(
            module,
            FlextInfraUtilitiesRopeRuntime.source_offset(source, node),
            declaration_line=node.lineno,
        )
        path: list[ast.Attribute] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            path.append(current)
            current = current.value
        path.reverse()
        for index, qualifier in enumerate(path[:-1]):
            receiver = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                scope, qualifier.value
            )
            if receiver is None:
                continue
            namespace_owner = receiver.get_object()
            if (
                not FlextInfraUtilitiesRopeRuntime.abstract_class(namespace_owner)
                or qualifier.attr in namespace_owner.get_attributes()
            ):
                continue
            donors = [
                ancestor
                for ancestor in FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                    namespace_owner
                )
                if ancestor is not namespace_owner
                and FlextInfraUtilitiesRopeRuntime.py_class(ancestor)
                and ancestor.get_name() == qualifier.attr
            ]
            if len(donors) != 1:
                continue
            direct: p.Infra.RopePyObject = namespace_owner
            donated: p.Infra.RopePyObject = donors[0]
            for segment in path[index + 1 :]:
                member = direct.get_attributes().get(segment.attr)
                inherited = donated.get_attributes().get(segment.attr)
                if member is None or member is not inherited:
                    return None
                direct = member.get_object()
                donated = direct
            return qualifier
        return None

    @classmethod
    def _reorder_declared_facade(
        cls,
        context: CodemodContext,
        source: str,
        namespace: ast.ClassDef,
        contract: tuple[list[m.Infra.SourceClassReference], set[str], bool],
        *,
        ordering: t.Pair[t.StrTuple, bool],
    ) -> str:
        """Apply the resolved base order and imports only for changed contracts.

        Returns:
            Reordered source, or untouched source when no rewrite is due.

        """
        ordered, retired = ordering
        existing = tuple(cls._base_name(base) for base in namespace.bases)
        if existing == ordered and not retired:
            return source
        if contract[2]:
            cls._declared_facade_stale_imports(context, source, contract[1])
        cls._declared_facade_declared_imports(
            context, contract[0], contract[1], existing, source
        )
        return cls._declared_facade_render(context, source, namespace, ordered)

    @classmethod
    def _explicit_class_facade(
        cls,
        project: p.Infra.RopeProject,
        facade_path: Path,
        source: str,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        *,
        binding: tuple[t.MappingKV[str, t.Pair[Path, str]], c.Infra.FacadeFamily],
    ) -> bool:
        """Recognize definitive authored class-owner publications by identity.

        Returns:
            Whether the selected namespace explicitly publishes a family owner.

        Raises:
            ValueError: If an explicit class namespace contains ambiguous bindings.

        """
        sources, family = binding
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        aliases = [
            alias
            for member in namespace.body
            if (alias := cls._namespace_class_alias(member)) is not None
        ]
        if not aliases:
            return False
        scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        ).get_scope()
        if namespace is not facade:
            scope = next(
                child
                for child in scope.get_scopes()
                if child.get_start() == facade.lineno
            )
        owners = cls._declared_facade_owners(project, declarations, sources)
        resolved = [
            FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, expression)
            for _, expression, _ in aliases
        ]
        if not any(
            value is not None and any(value.get_object() is owner for owner in owners)
            for value in resolved
        ):
            return False
        names: set[str] = set()
        for alias, value in zip(aliases, resolved, strict=True):
            name, expression, annotation = alias
            if (
                name not in names
                and name == "model_config"
                and annotation is None
                and isinstance(expression, ast.Attribute)
                and expression.attr == name
            ):
                receiver = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    scope, expression.value
                )
                if (
                    receiver is not None
                    and any(receiver.get_object() is owner for owner in owners)
                    and cls._canonical_config_binding(
                        project, receiver.get_object(), name
                    )
                    and value is not None
                    and not FlextInfraUtilitiesRopeRuntime.abstract_class(
                        value.get_object()
                    )
                ):
                    names.add(name)
                    continue
            annotated = (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, annotation)
                if annotation is not None
                else value
            )
            if (
                name in names
                or value is None
                or not FlextInfraUtilitiesRopeRuntime.abstract_class(value.get_object())
                or annotated is None
                or annotated.get_object() is not value.get_object()
            ):
                message = (
                    f"Ambiguous explicit facade class binding: {facade_path}:{name}"
                )
                raise ValueError(message)
            names.add(name)
        for member in namespace.body:
            if isinstance(member, ast.Assign | ast.AnnAssign | ast.TypeAlias) and (
                cls._namespace_class_alias(member) is None
            ):
                message = (
                    f"Non-class binding in explicit facade namespace: {facade_path}"
                )
                raise ValueError(message)
        return family not in {
            c.Infra.FacadeFamily.C,
            c.Infra.FacadeFamily.M,
            c.Infra.FacadeFamily.U,
        } or not cls._namespace_component_declarations(
            project,
            (facade_path, source),
            declarations,
            sources=sources,
            family=family,
        )

    @classmethod
    def _namespace_component_declarations(
        cls,
        project: p.Infra.RopeProject,
        source_entry: t.Pair[Path, str],
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        *,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        family: c.Infra.FacadeFamily = c.Infra.FacadeFamily.M,
    ) -> list[m.Infra.SourceClassReference]:
        """Elect namespace providers independently of whole class publications.

        Model publications never compose the namespace. Mixed constants retain
        plain owners as both named publications and namespace providers, but never
        inherit enum declarations. Direct native static or class methods admit
        utility composition only without effective instance methods; they do not
        prove statelessness or retirement of class publications.
        A native ``typing.ClassVar`` binding declares class metadata rather than
        an instance descriptor; resolve that identity at the annotation's owner.

        Returns:
            The declared plain namespace providers.

        Raises:
            TypeError: If a utility provider has no native class syntax tree.
            ValueError: If descriptors coexist with an undeclared stateful role.

        """
        facade_path, source = source_entry
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)), facade_path
        )
        scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        ).get_scope()
        if namespace is not facade:
            scope = next(
                child
                for child in scope.get_scopes()
                if child.get_start() == facade.lineno
            )
        aliases = tuple(
            (alias[0], resolved.get_object())
            for member in namespace.body
            if (alias := cls._namespace_class_alias(member)) is not None
            and (
                resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    scope, alias[1]
                )
            )
            is not None
        )
        excluded = FlextInfraUtilitiesDeclarationPayload.identity_name(
            project,
            "enum.Enum" if family is c.Infra.FacadeFamily.C else "pydantic.BaseModel",
        ).get_object()
        classvar = FlextInfraUtilitiesRopeRuntime.qualified_name(
            project, "ClassVar", module_name="typing"
        )
        components: list[m.Infra.SourceClassReference] = []
        has_unpublished = False
        for declaration, owner in zip(
            declarations,
            cls._declared_facade_owners(project, declarations, sources),
            strict=True,
        ):
            if not FlextInfraUtilitiesRopeRuntime.py_class(owner) or any(
                ancestor is excluded
                for ancestor in (
                    FlextInfraUtilitiesDeclarationPayload.class_ancestry(owner)
                )
            ):
                continue
            if family is c.Infra.FacadeFamily.U:
                methods = {
                    value.get_kind()
                    for member in owner.get_scope().get_scopes()
                    if FlextInfraUtilitiesRopeRuntime.py_function(
                        value := member.pyobject
                    )
                }
                if not methods or not methods <= {"classmethod", "staticmethod"}:
                    continue
                if any(
                    FlextInfraUtilitiesRopeRuntime.py_function(
                        value := attribute.get_object()
                    )
                    and value.get_kind() not in {"classmethod", "staticmethod"}
                    for attribute in owner.get_attributes().values()
                ):
                    continue
                node = owner.get_ast()
                if not isinstance(node, ast.ClassDef):
                    message = "utility provider has no native class syntax tree"
                    raise TypeError(message)
                if node.decorator_list or any(
                    isinstance(member, ast.AnnAssign)
                    and not (
                        isinstance(member.annotation, ast.Subscript)
                        and FlextInfraUtilitiesRopeRuntime.same_name(
                            classvar,
                            FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                                owner.get_scope(), member.annotation.value
                            ),
                        )
                    )
                    for member in node.body
                ):
                    message = (
                        "Utility class has descriptors but an undeclared namespace "
                        f"role: {declaration.target}:{declaration.qualified_base}"
                    )
                    raise ValueError(message)
            published = any(owner is value for _, value in aliases)
            if family is c.Infra.FacadeFamily.M and published:
                continue
            components.append(declaration)
            has_unpublished |= not published
        return components if has_unpublished or family is c.Infra.FacadeFamily.U else []

    @staticmethod
    def _declared_facade_owners(
        project: p.Infra.RopeProject,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> list[p.Infra.RopeClassObject]:
        """Resolve publication owners through native module and attribute identity.

        Returns:
            The original class objects elected by their declared source paths.

        Raises:
            ValueError: A declared publication resolves to a non-class object.

        """
        owners: list[p.Infra.RopeClassObject] = []
        for item in declarations:
            owner: p.Infra.RopePyObject = (
                FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                    project.get_pymodule(
                        project.get_resource(
                            sources[item.target][0]
                            .relative_to(Path(project.root.real_path))
                            .as_posix()
                        )
                    )
                )
            )
            for attribute in item.attributes:
                owner = owner.get_attributes()[attribute].get_object()
            if not FlextInfraUtilitiesRopeRuntime.abstract_class(owner):
                message = f"Declared facade owner is not a class: {item.target}"
                raise ValueError(message)
            owners.append(owner)
        return owners

    @classmethod
    def _require_model_namespaces(
        cls,
        project: p.Infra.RopeProject,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> None:
        """Require every composed model owner to be a namespace holder.

        The ``m`` facade composes its family owners by MRO, so an owner that
        is itself a model would turn the facade namespace into a model. A
        model belongs nested inside its owner's namespace class.

        Raises:
            ValueError: A declared owner of the models family is a model class.

        """
        for item, owner in zip(
            declarations,
            cls._declared_facade_owners(project, declarations, sources),
            strict=True,
        ):
            if c.Infra.MODEL_CONFIG_ATTRIBUTE in owner.get_attributes():
                message = (
                    f"models family owner {item.qualified_base} in {item.target} "
                    "is a model class; nest it inside a namespace class that the "
                    "family module exports"
                )
                raise ValueError(message)

    @staticmethod
    def _canonical_config_binding(
        project: p.Infra.RopeProject, owner: p.Infra.RopePyObject, name: str
    ) -> bool:
        """Prove metadata construction at its declared owner by native SDK identity.

        Returns:
            Whether the owner binding calls the canonical configuration constructor.

        """
        binding = owner.get_attributes().get(name)
        if binding is None:
            return False
        module, line = binding.get_definition_location()
        if module is None or line is None:
            return False
        if not FlextInfraUtilitiesRopeRuntime.py_class(owner):
            return False
        scope = owner.get_scope()
        native = FlextInfraUtilitiesDeclarationPayload.identity_name(
            project, "pydantic.ConfigDict"
        )
        if not FlextInfraUtilitiesRopeRuntime.source_module(module):
            return False
        for node in ast.walk(ast.parse(module.source_code)):
            if (
                isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
                and node.lineno == line
                and isinstance(node.value, ast.Call)
            ):
                constructor = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    scope, node.value.func
                )
                return (
                    constructor is not None
                    and native.get_object()
                    in FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                        constructor.get_object()
                    )
                )
        return False

    @classmethod
    def _remove_rendered_namespace_class_shadows(
        cls,
        project: p.Infra.RopeProject,
        source: str,
        facade_path: Path,
        *,
        family: Literal["model", "utility"],
    ) -> str:
        """Resolve the rendered namespace before removing inherited shadows.

        Returns:
            The facade source without redundant inherited class declarations.

        Raises:
            TypeError: An inherited owner is not a native class object.

        """
        _, namespace, scope, _, base_objects, _ = cls._facade_namespace_context(
            project, source, facade_path
        )
        try:
            return cls._remove_namespace_class_shadows(
                source, namespace, scope, base_objects, family=family
            )
        except TypeError as error:
            if family == "model":
                error.add_note(
                    f"Model facade: {facade_path}; namespace={namespace.name}; "
                    f"bases={tuple(ast.unparse(base) for base in namespace.bases)}"
                )
            raise

    @classmethod
    def _retired_facade_projection(
        cls,
        package_name: str,
        source: str,
        namespace: ast.ClassDef,
        retired: frozenset[str],
    ) -> t.Pair[str, CodemodContext]:
        wrapper = MetadataWrapper(parse_module(source))
        owner = cls._facade_namespace_cst(wrapper, namespace)
        context = CodemodContext(full_package_name=package_name, wrapper=wrapper)
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

        An owner whose nested class the namespace already composes as a base
        (``Owner.Namespace``) contributes through that nested class only, never
        additionally as a whole owner.

        Returns:
            The final declarations, their qualified names, and whether the
            facade binds the namespace through assignment.

        """
        direct = {cls._base_name(base) for base in namespace.bases}
        nested = {
            ast.unparse(base.value if isinstance(base, ast.Subscript) else base).split(
                "."
            )[0]
            for base in namespace.bases
            if isinstance(
                base.value if isinstance(base, ast.Subscript) else base,
                ast.Attribute,
            )
        }
        nested_owners = {
            item.qualified_base
            for item in declarations
            if item.qualified_base in nested
        }
        filtered = [
            item
            for item in declarations
            if (item.qualified_base not in independent or item.qualified_base in direct)
            and item.qualified_base not in nested_owners
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
            if cls._base_name(base) not in declared_names | nested_owners
        )
        return filtered, declared_names, bound_namespace

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
        source: str,
    ) -> None:
        """Register the imports the reordered facade bases require."""
        imports = {
            (node.module, alias.name)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and not node.level
            for alias in node.names
            if alias.asname is None
        }
        for item in declarations:
            if (
                item.qualified_base in declared_names
                and item.qualified_base not in existing
                and (item.target.rpartition(".")[0], item.qualified_base) not in imports
            ):
                AddImportsVisitor.add_needed_import(
                    context,
                    item.target.rpartition(".")[0],
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
        project: p.Infra.RopeProject,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        roots: t.Pair[Path, Path],
        facade: t.Pair[Path, ast.ClassDef],
        declared_names: set[str],
    ) -> frozenset[str]:
        """Retire own bases whose source no longer publishes in this family.

        Authored inheritance and source-proven current family providers remain.
        Unknown bindings fail instead of being classified by their spelling.

        Returns:
            Existing base expressions whose providers left the family publication.

        """
        facade_path, namespace = facade
        candidates = tuple(
            base
            for base in namespace.bases
            if FlextInfraUtilitiesCodegenFacades._base_name(base) not in declared_names
        )
        if not candidates:
            return frozenset()
        contents = dict(sources.values())
        projection_is_autogen = contents[facade_path].startswith(c.Infra.AUTOGEN_HEADER)
        barrel = contents.get(roots[1] / c.Infra.INIT_PY)
        pymodule = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            contents[facade_path],
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
        )
        retired: set[str] = set()
        for base in candidates:
            binding = FlextInfraUtilitiesCodegenFacades._retired_base_binding(
                project, pymodule, sources, facade, base
            )
            holder = binding.get_definition_location()[0]
            provider = holder.get_resource() if holder is not None else None
            if provider is None:
                if projection_is_autogen and (
                    FlextInfraUtilitiesCodegenFacades._departed_projected_binding(
                        project,
                        binding,
                        roots[1],
                        barrel,
                        declared_names=declared_names,
                    )
                ):
                    retired.add(ast.unparse(base))
                else:
                    FlextInfraUtilitiesCodegenFacades._require_facade_base_owner(
                        project,
                        binding,
                        facade_path,
                        ast.unparse(base),
                    )
                continue
            path = Path(provider.real_path).resolve()
            if (
                FlextInfraUtilitiesCodegenFacades._retired_family_provider(
                    binding.get_object(),
                    path,
                    roots[1],
                    contents,
                    projection_is_autogen=projection_is_autogen,
                )
            ) or (
                path.is_relative_to(roots[0].resolve())
                and not path.is_relative_to(roots[1].resolve())
            ):
                retired.add(ast.unparse(base))
        return frozenset(retired)

    @staticmethod
    def _retired_base_binding(
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopePyModule,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        facade: t.Pair[Path, ast.ClassDef],
        base: ast.expr,
    ) -> p.Infra.RopePyName:
        """Resolve a base's native identity before deciding family retirement.

        Returns:
            The class binding visible at the facade declaration.

        Raises:
            ValueError: If the base is unresolved, a module or a non-class.

        """
        expression = base.value if isinstance(base, ast.Subscript) else base
        head = expression
        attributes: list[str] = []
        while isinstance(head, ast.Attribute):
            attributes.insert(0, head.attr)
            head = head.value
        binding = FlextInfraUtilitiesCodegenFacades._declared_facade_base_binding(
            project, pymodule, sources, facade, (base, head, attributes)
        )
        if FlextInfraUtilitiesRopeRuntime.semantic_module(binding.get_object()):
            message = f"Module used as a class base: {ast.unparse(base)}"
            raise ValueError(message)
        if not FlextInfraUtilitiesRopeRuntime.abstract_class(binding.get_object()):
            message = f"Non-class facade base origin: {facade[0]}:{ast.unparse(base)}"
            raise ValueError(message)
        return binding

    @staticmethod
    def _declared_facade_base_binding(
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopePyModule,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        facade: t.Pair[Path, ast.ClassDef],
        reference: t.Triple[ast.expr, ast.expr, t.SequenceOf[str]],
    ) -> p.Infra.RopePyName:
        """Resolve the declaration-time binding through its public source origin.

        Earlier enclosing-class declarations use Rope's recorded expression
        environment. Module-origin names retain the captured declaration-order
        inventory even inside nested headers, so later module rebinding cannot
        replace a base.

        Returns:
            The original native binding, including its declared attribute chain.

        Raises:
            ValueError: If the original declaration is unresolved or ambiguous.

        """
        # Module scopes include later writes; bases read the earlier binding.
        ((module_name, source),) = (
            (name, text) for name, (path, text) in sources.items() if path == facade[0]
        )
        binding = FlextInfraUtilitiesCodegenFacades._enclosing_facade_base_binding(
            pymodule, facade, reference
        )
        if binding is not None:
            return binding
        definitions: dict[str, m.Infra.SourceClassDefinition] = {}
        visible = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
            m.Infra.SourceBindingInventoryRequest(
                project=project,
                module=module_name,
                path=facade[0],
                source=source,
                required_line=facade[1].lineno,
            ),
            definitions,
            provider=pymodule,
        )
        origin = (
            visible.get(reference[1].id) if isinstance(reference[1], ast.Name) else None
        )
        if origin is None:
            message = (
                f"Unresolved facade base origin: {facade[0]}:"
                f"{ast.unparse(reference[0])}"
            )
            raise ValueError(message)
        if origin.target not in definitions:
            return FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_binding(
                project,
                m.Infra.SourceClassReference(
                    target=origin.target,
                    attributes=(*origin.attributes, *reference[2]),
                    qualified_base=".".join((
                        origin.target,
                        *origin.attributes,
                        *reference[2],
                    )),
                ),
                sources=sources,
            )
        declaration_line = int(origin.target.rsplit(":", 1)[1])
        declared_scope = pymodule.get_scope().get_inner_scope_for_line(declaration_line)
        parent = declared_scope.parent
        if declared_scope.get_start() != declaration_line or parent is None:
            message = f"Unresolved facade declaration: {origin.target}"
            raise ValueError(message)
        binding = parent.get_defined_names().get(declared_scope.pyobject.get_name())
        if binding is None or binding.get_object() is not declared_scope.pyobject:
            message = f"Ambiguous facade declaration: {origin.target}"
            raise ValueError(message)
        for attribute in (*origin.attributes, *reference[2]):
            binding = binding.get_object().get_attribute(attribute)
        return binding

    @staticmethod
    def _enclosing_facade_base_binding(
        pymodule: p.Infra.RopePyModule,
        facade: t.Pair[Path, ast.ClassDef],
        reference: t.Triple[ast.expr, ast.expr, t.SequenceOf[str]],
    ) -> p.Infra.RopePyName | None:
        """Prove the raw local binding precedes the header before resolving aliases.

        Returns:
            The original enclosing-class binding, or no enclosing-class owner.

        Raises:
            ValueError: If the local origin is unresolved or not proven to precede
                the header in this source module.

        """
        offset = FlextInfraUtilitiesRopeRuntime.source_offset(
            pymodule.source_code, reference[0]
        )
        scope = FlextInfraUtilitiesRopeRuntime.scope_at(
            pymodule, offset, declaration_line=facade[1].lineno
        )
        if (
            scope.get_kind() != c.Infra.RopeScopeKind.CLASS
            or not isinstance(reference[1], ast.Name)
            or reference[1].id not in scope.get_defined_names()
        ):
            return None
        declaring, line = scope.get_defined_names()[
            reference[1].id
        ].get_definition_location()
        if declaring is not pymodule or line is None or line >= facade[1].lineno:
            message = (
                f"Unproven preceding facade base: {facade[0]}:"
                f"{ast.unparse(reference[0])}"
            )
            raise ValueError(message)
        binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
            pymodule.get_source_binding_index().context_at(offset).environment,
            reference[1],
        )
        if binding is None:
            message = (
                f"Unresolved facade base origin: {facade[0]}:"
                f"{ast.unparse(reference[0])}"
            )
            raise ValueError(message)
        for attribute in reference[2]:
            binding = binding.get_object().get_attribute(attribute)
        return binding

    @staticmethod
    def _retired_family_provider(
        value: p.Infra.RopePyObject,
        path: Path,
        owners_dir: Path,
        contents: t.MappingKV[Path, str],
        *,
        projection_is_autogen: bool,
    ) -> bool:
        """Elect source-declared classes that left their generated family exports.

        Returns:
            Whether this native provider is an unpublished owned declaration.

        """
        if (
            not projection_is_autogen
            or path.parent != owners_dir.resolve()
            or path.name == c.Infra.INIT_PY
            or not FlextInfraUtilitiesRopeRuntime.py_class(value)
        ):
            return False
        return any(
            isinstance(node, ast.ClassDef) and node.name == value.get_name()
            for node in ast.parse(contents[path], filename=str(path)).body
        ) and value.get_name() not in (
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                contents[path]
            )
        )

    @staticmethod
    def _departed_projected_binding(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        owners_dir: Path,
        barrel: str | None,
        *,
        declared_names: set[str],
    ) -> bool:
        """Retire undefined generated imports from the elected family boundary.

        The caller proves the facade projection is generated; ``barrel`` is
        the family barrel text of ``owners_dir``. Authored facades and
        unresolved or external module providers stay errors. Rope resolves the
        exact family resource; spelling grants no ownership.

        Returns:
            Whether the generated base lost its own family's declared owner.

        A ``ValueError`` propagates from ``imported_module_path`` when a
        source-free binding has no native owner.

        """
        if not (
            isinstance(binding, p.Infra.RopeImportedName)
            and binding.get_definition_location()[0] is None
        ):
            return False
        provider = FlextInfraUtilitiesRopeRuntime.imported_module_path(project, binding)
        # The marker proves projection ownership, not export membership.
        # Only the current leaf declarations decide whether an owner left.
        return (
            provider in {owners_dir.resolve(), (owners_dir / c.Infra.INIT_PY).resolve()}
            and barrel is not None
            and barrel.startswith(c.Infra.AUTOGEN_HEADER)
            and binding.imported_name not in declared_names
        )

    @staticmethod
    def _require_facade_base_owner(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        facade_path: Path,
        expression: str,
    ) -> None:
        """Keep a source-free facade base only when it is abstract or upstream.

        Raises:
            ValueError: If the binding has no resolved source owner.

        """
        value = binding.get_object()
        if (
            FlextInfraUtilitiesRopeRuntime.abstract_class(value)
            and not FlextInfraUtilitiesRopeRuntime.py_class(value)
        ) or FlextInfraUtilitiesCodegenFacades._upstream_binding(
            project, project, binding
        ):
            return
        message = f"Facade base has no source owner: {facade_path}:{expression}"
        raise ValueError(message)

    @staticmethod
    def _upstream_binding(
        project: p.Infra.RopeProject,
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
        package_name: str,
        owners_dir: Path,
        source: str,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> str:
        """Import declared owners from their publishing family package.

        Declarations elect exports; the existing joint initializer plan publishes
        them. A stale barrel is never bypassed by importing a concrete leaf.

        Returns:
            Source with owned leaf import origins replaced by their package.

        Raises:
            ValueError: If published owner spellings compete.

        """
        owners = {item.qualified_base for item in declarations}
        if len(owners) != len(declarations):
            message = "Competing declared facade import bindings"
            raise ValueError(message)
        prefix = f"{package_name}.{owners_dir.name}"
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            module = (
                resolve_name(f"{'.' * node.level}{node.module}", package_name)
                if node.level
                else node.module
            )
            if module != prefix and not module.startswith(f"{prefix}."):
                continue
            for alias in node.names:
                if alias.name not in owners or module == prefix:
                    continue
                source = FlextInfraUtilitiesCodegenFacades._relocated_import_source(
                    source, package_name, (module, alias.name), prefix
                )
        return source

    @staticmethod
    def _relocated_import_source(
        source: str,
        package_name: str,
        imported: t.Pair[str, str],
        target: str,
    ) -> str:
        """Move one imported name to a new origin module, keeping its binding.

        The ``as`` alias, statement indentation and the remaining names of the
        original statement are preserved, so the rebound import binds exactly
        the names the module used before.

        Returns:
            Source whose import of ``imported`` now originates from ``target``.

        Raises:
            ValueError: If the source does not import ``imported``.

        """
        module, name = imported
        lines = source.splitlines(keepends=True)
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            origin = (
                resolve_name(f"{'.' * node.level}{node.module}", package_name)
                if node.level
                else node.module
            )
            moved = [alias for alias in node.names if alias.name == name]
            if origin != module or not moved:
                continue
            kept = [alias for alias in node.names if alias.name != name]
            statements = [
                *(
                    [ast.ImportFrom(module=node.module, names=kept, level=node.level)]
                    if kept
                    else []
                ),
                ast.ImportFrom(module=target, names=moved, level=0),
            ]
            indent = " " * node.col_offset
            replacement = "".join(
                f"{indent}{ast.unparse(statement)}\n" for statement in statements
            )
            return "".join([
                *lines[: node.lineno - 1],
                replacement,
                *lines[node.end_lineno or node.lineno :],
            ])
        msg = f"source does not import {name} from {module}"
        raise ValueError(msg)

    @classmethod
    def _declared_sources(
        cls,
        pkg_dir: Path,
        owners_dir: Path,
        *,
        contents: t.MappingKV[Path, str],
        project: p.Infra.RopeProject,
    ) -> t.Triple[
        t.MutableMappingKV[str, t.Pair[Path, str]],
        list[m.Infra.SourceClassReference],
        str,
    ]:
        """Capture source identities and explicitly exported family declarations.

        Package election uses the same authenticated view as its declarations,
        including proposed directories and project-boundary metadata.

        Returns:
            Source snapshots, declared class references and qualified package.

        Raises:
            ValueError: If distinct publishers compete for a parent facade name.

        """
        package_name = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            pkg_dir,
            project_root=Path(project.root.real_path),
            source_project=project,
        )
        if not package_name:
            message = f"Facade package has no elected import namespace: {pkg_dir}"
            raise ValueError(message)
        cls._facade_source_membership(project, owners_dir)
        sources: t.MutableMappingKV[str, t.Pair[Path, str]] = {}
        declarations: list[m.Infra.SourceClassReference] = []
        package_prefix = f"{pkg_dir}/"
        captured = {
            path: source
            for path, source in contents.items()
            if str(path).startswith(package_prefix)
            and path.suffix == c.Infra.EXT_PYTHON
        }
        for path, content in sorted(captured.items()):
            # Conflict-marked projections belong to recovery, not source analysis.
            if (
                path.name == c.Infra.INIT_PY
                and content.startswith(c.Infra.AUTOGEN_HEADER)
                and any(line.startswith("<<<<<<<") for line in content.splitlines())
            ):
                continue
            relative = path.relative_to(pkg_dir).with_suffix("")
            module = ".".join((
                package_name,
                *(
                    relative.parts[:-1]
                    if path.name == c.Infra.INIT_PY
                    else relative.parts
                ),
            ))
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
        return sources, declarations, package_name

    @staticmethod
    def _independent_publishers(
        pkg_dir: Path,
        owners_dir: Path,
        sources: t.MappingKV[str, t.Pair[Path, str]],
        *,
        package_name: str,
    ) -> frozenset[str]:
        """Find declared owners re-exported by their own separate public facade.

        Returns:
            Original symbol names explicitly published outside family facades.

        """
        families = {
            f"{item.module}.py"
            for item in FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        }
        origin = f"{package_name}.{owners_dir.name}"
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

    @classmethod
    def _required_protocol_members(
        cls,
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

        Raises:
            TypeError: If the native consumer exposes no source module or module AST.

        """
        project, contents = binding
        for parent in sorted({
            path.parent
            for path in contents
            if path.is_relative_to(pkg_dir) and path.suffix == c.Infra.EXT_PYTHON
        }):
            cls._facade_source_membership(project, parent)
        family = c.Infra.FacadeFamily.P
        methods: set[str] = set()
        for path, source in sorted(
            (path, source)
            for path, source in contents.items()
            if path != facade_path
            and path.is_relative_to(pkg_dir)
            and path.suffix == c.Infra.EXT_PYTHON
        ):
            # Generated initializers propagate declarations; they are not
            # authored consumers and may await replacement in this plan.
            if path.name == c.Infra.INIT_PY and source.startswith(
                c.Infra.AUTOGEN_HEADER,
            ):
                continue
            pymodule = project.get_pymodule(
                FlextInfraUtilitiesRopeRuntime.file_resource_at(project, path),
                force_errors=True,
            )
            if not FlextInfraUtilitiesRopeRuntime.source_module(pymodule):
                message = f"protocol consumer has no native source module: {path}"
                raise TypeError(message)
            tree = pymodule.get_ast()
            if not isinstance(tree, ast.Module):
                message = f"protocol consumer has no module syntax tree: {path}"
                raise TypeError(message)
            references = cls._family_receiver_references(
                tree, family, nested_namespace=nested_namespace, namespace=namespace
            )
            if not references:
                continue
            module_paths: t.MutableMappingKV[p.Infra.RopeImportedModule, Path] = {}
            # A letter whose single binding is one module-level import resolves
            # every load to that import, so the module scope answers once for
            # the whole module; any other binding keeps Rope's per-position
            # lexical lookup.
            if FlextInfraUtilitiesRopeAnalysisSourceScan.single_module_import_binding(
                tree, family
            ):
                if cls._facade_receiver_binding(
                    project,
                    pymodule.get_scope(),
                    references[0][0],
                    owned=(pkg_dir, pkg_dir / c.Infra.INIT_PY, facade_path),
                    resolved=module_paths,
                ):
                    methods.update(attribute for _, attribute in references)
                continue
            methods.update(
                attribute
                for receiver, attribute in references
                if cls._facade_receiver_binding(
                    project,
                    cls._receiver_scope(pymodule, receiver),
                    receiver,
                    owned=(pkg_dir, pkg_dir / c.Infra.INIT_PY, facade_path),
                    resolved=module_paths,
                )
            )
        return frozenset(method for method in methods if not method.startswith("_"))

    @staticmethod
    def _family_receiver_references(
        tree: ast.Module,
        family: str,
        *,
        nested_namespace: bool,
        namespace: str,
    ) -> t.VariadicTuple[t.Pair[ast.Name, str]]:
        """Return each ``<family>[.<namespace>].<member>`` load with its receiver.

        Returns:
            The receiver name node and the consumed member, in walk order.

        """
        references: list[t.Pair[ast.Name, str]] = []
        for reference in ast.walk(tree):
            if not isinstance(reference, ast.Attribute):
                continue
            receiver = reference.value
            if nested_namespace:
                if not (
                    isinstance(receiver, ast.Attribute) and receiver.attr == namespace
                ):
                    continue
                receiver = receiver.value
            if isinstance(receiver, ast.Name) and receiver.id == family:
                references.append((receiver, reference.attr))
        return tuple(references)

    @staticmethod
    def _facade_receiver_binding(
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        receiver: ast.Name,
        *,
        owned: t.VariadicTuple[Path],
        resolved: t.MutableMappingKV[p.Infra.RopeImportedModule, Path],
    ) -> bool:
        """Report whether one receiver load binds its letter from an owned module.

        Returns:
            True when Rope resolves the receiver to its own letter imported
            from the package, its initializer, or the facade module itself.

        """
        imported_binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
            scope, receiver
        )
        if (
            not isinstance(imported_binding, p.Infra.RopeImportedName)
            or imported_binding.imported_name != receiver.id
        ):
            return False
        imported = imported_binding.imported_module
        if (
            imported.level == 0
            and imported.module_name is not None
            and imported.module_name.split(".", 1)[0] in sys.stdlib_module_names
        ):
            # Standard-library imports cannot declare owned facades.
            # Built-in modules have no source resource for Rope.
            return False
        return (
            FlextInfraUtilitiesRopeRuntime.imported_module_path(
                project, imported_binding, resolved=resolved
            )
            in owned
        )

    @staticmethod
    def _receiver_scope(
        pymodule: t.Infra.RopePyModule,
        receiver: ast.Name,
    ) -> p.Infra.RopeScope:
        """Return Rope's lexical scope that binds one receiver load.

        Returns:
            Rope's lexical scope at the receiver position.

        """
        offset = pymodule.lines.get_line_start(receiver.lineno)
        offset += len(
            pymodule.lines
            .get_line(receiver.lineno)
            .encode(c.DEFAULT_ENCODING)[: receiver.col_offset]
            .decode(c.DEFAULT_ENCODING),
        )
        return FlextInfraUtilitiesRopeRuntime.scope_at(pymodule, offset)

    @classmethod
    def _facade_protocol_owners(
        cls,
        owners_dir: Path,
        contents: t.MappingKV[Path, str],
        *,
        project: p.Infra.RopeProject,
    ) -> t.Pair[
        t.VariadicTuple[t.Triple[str, str, frozenset[str]]],
        t.MappingKV[str, frozenset[str]],
    ]:
        parents = {
            path.parent
            for path in contents
            if path.is_relative_to(owners_dir) and path.suffix == c.Infra.EXT_PYTHON
        }
        parents.add(owners_dir)
        for parent in sorted(parents):
            cls._facade_source_membership(project, parent)
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
        *,
        ignored_bases: frozenset[str] = frozenset(),
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
            node
            for node in facades[0].body
            if isinstance(node, ast.ClassDef)
            and not (
                node.bases
                and all(ast.unparse(base) in ignored_bases for base in node.bases)
            )
        )
        if len(nested) > 1:
            ancestors = {
                ast.unparse(base)
                for base in facades[0].bases
                if ast.unparse(base) not in ignored_bases
            }
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
        published = {
            alias.name
            for node in ast.parse(source).body
            if isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == f"{package}.{directory}"
            for alias in node.names
            if alias.asname in {None, alias.name}
        }
        for module, class_name in additions:
            if class_name in published:
                continue
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
        wrapper = MetadataWrapper(parse_module(source))
        owner = cls._facade_namespace_cst(wrapper, namespace)
        additions_args = tuple(Arg(Name(name)) for _module, name in additions)
        # A base listed after Protocol has no consistent MRO, so owners
        # projected onto a protocol namespace go before its terminal Protocol.
        precede = bool(namespace.bases) and (
            cls._base_name(namespace.bases[-1]) == c.Infra.PROTOCOL_BASE
        )
        bases = (
            (*owner.bases[:-1], *additions_args, owner.bases[-1])
            if precede
            else (*owner.bases, *additions_args)
        )
        replacement = owner.with_changes(bases=bases)
        arguments = (*bases, *owner.keywords)
        header_length = namespace.col_offset + len(
            f"class {owner.name.value}("
            + ", ".join(wrapper.module.code_for_node(arg.value) for arg in arguments)
            + "):"
        )
        if (
            any(base.lineno != namespace.lineno for base in namespace.bases)
            or header_length
            > FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
        ):
            wrapped: list[t.Infra.CstArgument] = []
            for index, arg in enumerate(arguments):
                whitespace = (
                    arg.comma.whitespace_after
                    if isinstance(arg.comma, Comma)
                    and isinstance(arg.comma.whitespace_after, ParenthesizedWhitespace)
                    else ParenthesizedWhitespace()
                )
                wrapped.append(
                    arg.with_changes(
                        comma=Comma(
                            whitespace_after=whitespace.with_changes(
                                indent=True,
                                last_line=SimpleWhitespace(
                                    wrapper.module.default_indent
                                    if index < len(arguments) - 1
                                    else ""
                                ),
                            ),
                        ),
                    ),
                )
            opening = (
                owner.lpar.whitespace_after
                if isinstance(owner.lpar, LeftParen)
                and isinstance(owner.lpar.whitespace_after, ParenthesizedWhitespace)
                else ParenthesizedWhitespace()
            )
            replacement = replacement.with_changes(
                bases=tuple(wrapped[: len(bases)]),
                keywords=tuple(wrapped[len(bases) :]),
                lpar=LeftParen(
                    whitespace_after=opening.with_changes(
                        indent=True,
                        last_line=SimpleWhitespace(wrapper.module.default_indent),
                    ),
                ),
                rpar=RightParen(),
            )
        updated = wrapper.module.deep_replace(owner, replacement)
        if not isinstance(updated, Module):
            message = "facade base projection did not preserve the module"
            raise TypeError(message)
        return updated.code


__all__: list[str] = ["FlextInfraUtilitiesCodegenFacades"]
