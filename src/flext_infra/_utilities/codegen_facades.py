"""Declared facade composition and consumer-selected protocol owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Callable, Generator, MutableMapping
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal, override

from flext_cli import u
from libcst import (
    AnnAssign,
    Arg,
    Assign,
    ClassDef,
    Comma,
    CSTNode,
    CSTTransformer,
    LeftParen,
    Module,
    Name,
    ParenthesizedWhitespace,
    RemovalSentinel,
    RightParen,
    SimpleWhitespace,
    parse_module,
)
from libcst.codemod import CodemodContext
from libcst.codemod.commands.rename import RenameCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope.project import FlextInfraRopeProject, require_value
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities.codegen_facade_syntax import (
    FlextInfraUtilitiesCodegenFacadeSyntax,
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
        planned_sources: t.MappingKV[Path, str | None] | None = None,
        project_roots: t.VariadicTuple[Path] = (),
    ) -> Generator[
        t.Triple[
            p.Infra.RopeProject,
            Callable[
                [],
                t.Triple[
                    tuple[m.Cli.AtomicFileState, ...],
                    tuple[m.Cli.AtomicDirectoryInventory, ...],
                    tuple[m.Cli.AtomicDirectoryChainPlan, ...],
                ],
            ],
            MutableMapping[Path, str],
        ]
    ]:
        """Share one authenticated native source graph across a planning pass.

        Yields:
            The native Rope project, original-state reader and planned sources.

        Raises:
            ValueError: If a declared project root lies outside the original
                authority.

        """
        root = root.resolve()
        project_roots = tuple(sorted({project.resolve() for project in project_roots}))
        if any(not project.is_relative_to(root) for project in project_roots):
            msg = "Rope declared project root is outside the original authority"
            raise ValueError(msg)
        known = {
            *(state.path for state in source_states),
            *(plan.path for plan in declared_files),
            *(state.path for plan in declared_files for state in plan.source_states),
        }
        iteration = FlextInfraUtilitiesIterationDirectory
        paths = {
            path
            for project in project_roots or (root,)
            if project.is_dir()
            for path in iteration.iter_directory_python_files(project)
        }
        source_states = (
            *source_states,
            *(
                u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in sorted(paths)
                if path not in known
            ),
        )
        if planned_sources:
            source_states, declared_files = (
                FlextInfraUtilitiesCodegenFacades._facade_declared_sources(
                    root, source_states, declared_files, planned_sources
                )
            )
        original_states = m.Infra.CodemodBindingSnapshot(
            states=(
                *source_states,
                *(state for plan in declared_files for state in plan.source_states),
                *(
                    plan.before
                    for plan in declared_files
                    if isinstance(plan.before, m.Cli.AtomicFileState)
                ),
            ),
        ).states
        proposed = {
            plan.path: plan.desired_content
            for plan in declared_files
            if plan.desired_content is not None
        }
        retired = frozenset(
            plan.path for plan in declared_files if plan.desired_content is None
        )
        # Consumed states include the dependency modules native reads loaded
        # from the checkout-local environment; they stay verified inputs, but
        # only repository-owned sources are planning targets (70dc29f1b9
        # republished site-packages/flext_cli/utilities.py otherwise).
        original_sources = FlextInfraUtilitiesCodegenFacades.facade_original_sources(
            root, source_states
        )
        sources = {
            **{
                path: source
                for path, source in original_sources.items()
                if path not in retired
            },
            **{
                plan.path: proposed[plan.path].decode(c.DEFAULT_ENCODING)
                for plan in declared_files
                if plan.path.is_relative_to(root)
                and plan.path.suffix == c.Infra.EXT_PYTHON
                and plan.path in proposed
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    root, plan.path
                )
            },
        }
        with (
            FlextInfraUtilitiesRopeCore.open_project(
                next(path for path in (root, *root.parents) if path.is_dir()),
                project_roots=project_roots or None,
            ) as live,
            closing(
                FlextInfraRopeProject.from_atomic_reads(
                    live,
                    original_states,
                    election=m.Infra.RopeProjectElection(
                        ignored_resources=tuple(
                            sorted(config.Infra.codegen.source_scan_ignored)
                        ),
                        source_folders=tuple(
                            sorted({
                                *(folder.path for folder in live.get_source_folders()),
                                *(
                                    ""
                                    if folder == Path(live.root.real_path)
                                    else folder.relative_to(
                                        live.root.real_path
                                    ).as_posix()
                                    for folder in (
                                        root,
                                        *project_roots,
                                        *(
                                            project / name
                                            for project in (root, *project_roots)
                                            for name in config.Infra.source_scan.roots
                                        ),
                                    )
                                    if any(
                                        path.is_relative_to(folder) for path in proposed
                                    )
                                ),
                            })
                        ),
                        extension_modules=FlextInfraUtilitiesRopeRuntime.extension_module_names(
                            live
                        ),
                        python_path_folders=tuple(
                            folder.real_path
                            for folder in live.get_python_path_folders()
                            if folder.is_folder()
                        ),
                    ),
                    sources={},
                    declared_files=declared_files,
                )
            ) as project,
        ):

            def consumed() -> t.Triple[
                tuple[m.Cli.AtomicFileState, ...],
                tuple[m.Cli.AtomicDirectoryInventory, ...],
                tuple[m.Cli.AtomicDirectoryChainPlan, ...],
            ]:
                """Return original file and native election evidence."""
                return (
                    project.consumed_source_states(),
                    project.consumed_source_directories(),
                    project.consumed_source_topology(),
                )

            with project.frozen_layout():
                yield (
                    FlextInfraUtilitiesCodegenFacades._require_source_project(project),
                    consumed,
                    sources,
                )
            # A body failure escapes at the yield; only a completed pass verifies.
            project.verify_source_states()

    @staticmethod
    def _require_source_project(value: p.AttributeProbe) -> p.Infra.RopeProject:
        """Admit the native project at its actual dynamic SDK boundary.

        Returns:
            The original project exposing authenticated source capabilities.

        Raises:
            TypeError: If the SDK project does not expose the required capabilities.

        """
        if not isinstance(value, p.Infra.RopeProject):
            message = "facade source project has no native Rope capabilities"
            raise TypeError(message)
        return value

    @staticmethod
    def facade_original_sources(
        root: Path,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> t.MappingKV[Path, str]:
        """Select root-owned Python sources while retaining all inputs as receipts.

        Returns:
            The canonical original source view shared by native planning owners.

        """
        return {
            state.path: state.content.decode(c.DEFAULT_ENCODING)
            for state in source_states
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
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        planned_sources: t.MappingKV[Path, str | None],
    ) -> t.Pair[
        t.VariadicTuple[m.Cli.AtomicFileState],
        t.VariadicTuple[m.Infra.CodegenFilePlan],
    ]:
        """Authenticate planned overlays against their original physical inputs.

        Returns:
            Original source receipts and their consistent publication plans.

        Raises:
            ValueError: If a declaration competes or a native input cannot be read.

        """
        originals = {state.path: state for state in source_states}
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
            original = originals.get(path)
            if original is None:
                original = require_value(u.Cli.atomic_read_binary_file_state(path))
                originals[path] = original
            chain = require_value(u.Cli.atomic_plan_directory_chain(path.parent))
            declarations[path] = m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=chain if chain.directories else original,
                desired_content=content,
                desired_mode=(
                    None
                    if content is None
                    else (
                        original.mode
                        if original.mode is not None
                        else config.Infra.codegen.modes.file_default
                    )
                ),
            )
        return tuple(originals.values()), tuple(declarations.values())

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
        parents = {
            path.parent
            for path in sources
            if path.is_relative_to(pkg_dir / directory)
            and path.suffix == c.Infra.EXT_PYTHON
        }
        parents.add(pkg_dir / directory)
        for parent in sorted(parents):
            cls._facade_source_membership(project, parent, sources)
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
            pkg_dir, rendered, family="t", contents=sources, project=project
        )

    @staticmethod
    def _facade_source_membership(
        project: p.Infra.RopeProject,
        directory: Path,
        sources: t.MappingKV[Path, str],
    ) -> tuple[Path, ...]:
        """Authenticate the native immediate Python election before parsing.

        Returns:
            Native source paths matching the captured declaration inventory.

        Raises:
            ValueError: Native membership differs from captured source paths.

        """
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
        expected = tuple(
            sorted(
                path
                for path in sources
                if path.parent == directory and path.suffix == c.Infra.EXT_PYTHON
            )
        )
        if expected and actual != expected:
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
            with cls.facade_source_project(pkg_dir.parent) as (captured, _, contents):
                return cls.facade_module_path(
                    pkg_dir, family, project=captured, sources=contents
                )
        owners: list[Path] = []
        for module in cls._facade_source_membership(project, pkg_dir, sources):
            if module.name == c.Infra.INIT_PY:
                continue
            resource = project.get_resource(
                module.relative_to(Path(project.root.real_path)).as_posix()
            )
            source = FlextInfraUtilitiesRopeRuntime.require_file_resource(
                resource, module
            ).read()
            if family in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_source(
                source, filename=str(module)
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
                message = (
                    "Facade rendering requires its project and source epoch together"
                )
                raise ValueError(message)
            with cls.facade_source_project(pkg_dir.parent) as (captured, _, contents):
                return cls.render_utility_facade(
                    pkg_dir, family=family, project=captured, sources=contents
                )
        facade_path = cls.facade_module_path(
            pkg_dir, family, project=project, sources=sources
        )
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
        # Parser inputs share the native read receipts. Unresolved module
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
                    family == "p"
                    or path.parent in {pkg_dir, owners_dir}
                    or path.name == c.Infra.INIT_PY
                )
                else content
            )
            for path, content in sources.items()
        }
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
            pkg_dir, rendered, family=family, contents=sources, project=project
        )

    @classmethod
    def _generated_facade(
        cls,
        pkg_dir: Path,
        source: str,
        *,
        family: Literal["c", "t", "u", "p", "m"],
        contents: t.MappingKV[Path, str],
        project: p.Infra.RopeProject,
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
            project=project,
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

        """
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
            isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
            or (
                isinstance(member, ast.AnnAssign)
                and cls._namespace_class_alias(member) is None
            )
            for member in namespace.body
        ) and (
            any(
                owner is not typing_objects[0]
                and typing_objects[0] not in owner.get_superclasses()
                for owner in base_objects
            )
            or any(
                isinstance(member, ast.ClassDef)
                or (
                    isinstance(member, ast.Assign)
                    and (
                        resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                            scope, member.value
                        )
                    )
                    is not None
                    and typing_objects[0] in resolved.get_object().get_superclasses()
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
        source = cls._insert_protocol_imports(source, additions, package=pkg_dir.name)
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
        base_objects: list[p.Infra.RopePyObject] = []
        for base in namespace.bases:
            resolved = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                scope, base.value if isinstance(base, ast.Subscript) else base
            )
            if resolved is None:
                message = f"Unresolved facade base: {ast.unparse(base)}"
                raise ValueError(message)
            base_objects.append(resolved.get_object())
        return facade, namespace, scope, typing_objects, tuple(base_objects), markers

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

        """
        inherited: list[p.Infra.RopePyObject] = []
        pending = list(base_objects)
        while pending:
            owner = pending.pop(0)
            if owner not in inherited:
                inherited.append(owner)
                pending.extend(owner.get_superclasses())
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
    ) -> t.Triple[str, ast.expr, ast.expr | None] | None:
        """Read only direct class bindings, without admitting calls or type aliases.

        Returns:
            The name, RHS and optional class annotation, or no supported binding.

        """
        match member:
            case ast.Assign(
                targets=[ast.Name(id=name)],
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
                        *lineage(base.get_superclasses()),
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
        family: Literal["protocol", "model"],
    ) -> str:
        """Keep declared owners authoritative over their generated class bindings.

        Returns:
            Source without derived class bindings or proven redundant assignments.

        Raises:
            ValueError: If an authored contract assignment is unresolved or ambiguous.

        """
        aliases = [
            (member, alias)
            for member in namespace.body
            if (alias := cls._namespace_class_alias(member)) is not None
        ]
        if not aliases:
            return source
        inherited = cls._inherited_namespace_members(
            base_objects, frozenset(alias[0] for _, alias in aliases)
        )
        shadows: list[ast.stmt] = []
        for member, alias in aliases:
            name, expression, annotation = alias
            value = FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, expression)
            target = value.get_object() if value is not None else None
            inherited_class = (
                target is not None
                and FlextInfraUtilitiesRopeRuntime.abstract_class(target)
                and any(
                    target is attribute.get_object()
                    for owner in cls._protocol_ancestor_objects(base_objects)
                    for attribute in owner.get_attributes().values()
                )
            )
            if source.startswith(c.Infra.AUTOGEN_HEADERS) and inherited_class:
                # A projection cannot turn an inherited declaration into a new
                # alias or replace a different canonical member with its value.
                shadows.append(member)
                continue
            annotated = (
                FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, annotation)
                if annotation is not None
                else value
            )
            if value is None or annotated is None:
                if annotation is not None:
                    message = f"Unresolved {family} class attribute: {name}"
                    raise ValueError(message)
                continue
            target = value.get_object()
            if not FlextInfraUtilitiesRopeRuntime.abstract_class(target):
                continue
            if target is not annotated.get_object():
                message = (
                    f"ambiguous {family} class attribute {name}: "
                    "annotation does not identify the declared contract"
                )
                raise ValueError(message)
            if target is inherited.get(name):
                shadows.append(member)
            elif inherited_class:
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
            Source with the selected assignments and unused imports removed.

        """
        wrapper = MetadataWrapper(parse_module(source))
        removals: set[CSTNode] = set()
        lines = source.splitlines()
        positions = {(member.lineno, member.col_offset) for member in shadows}
        context = CodemodContext(wrapper=wrapper)
        for node, span in wrapper.resolve(PositionProvider).items():
            if (
                not isinstance(node, Assign | AnnAssign)
                or (
                    span.start.line,
                    len(lines[span.start.line - 1][: span.start.column].encode()),
                )
                not in positions
            ):
                continue
            if node.value is not None:
                RemoveImportsVisitor.remove_unused_import_by_node(context, node.value)
            if isinstance(node, AnnAssign):
                RemoveImportsVisitor.remove_unused_import_by_node(
                    context, node.annotation.annotation
                )
            removals.add(node)

        class RemoveShadows(CSTTransformer):
            """Remove proven assignments in one identity-preserving traversal."""

            @override
            def leave_Assign(
                self, original_node: Assign, updated_node: Assign
            ) -> Assign | RemovalSentinel:
                if original_node in removals:
                    return RemovalSentinel.REMOVE
                return updated_node

            @override
            def leave_AnnAssign(
                self, original_node: AnnAssign, updated_node: AnnAssign
            ) -> AnnAssign | RemovalSentinel:
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
                        binding[0].get_module(f"{pkg_dir.name}._protocols.{module}")
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
            pkg_dir, owners_dir, contents=contents, project=project
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
        ordered = FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_order(
            project, sources, declarations
        )
        existing = tuple(cls._base_name(base) for base in namespace.bases)
        if existing != ordered or retired:
            if bound_namespace:
                cls._declared_facade_stale_imports(context, source, declared_names)
            cls._declared_facade_declared_imports(
                context,
                declarations,
                declared_names,
                existing,
            )
            source = cls._declared_facade_render(context, source, namespace, ordered)
        if family == "m":
            source = cls._remove_model_namespace_class_shadows(
                project, source, facade_path
            )
        return cls._wrap_facade_imports(source)

    @classmethod
    def _remove_model_namespace_class_shadows(
        cls, project: p.Infra.RopeProject, source: str, facade_path: Path
    ) -> str:
        """Resolve the rendered model namespace before removing inherited shadows.

        Returns:
            The model facade source without redundant inherited class declarations.

        """
        _, namespace, scope, _, base_objects, _ = cls._facade_namespace_context(
            project, source, facade_path
        )
        return cls._remove_namespace_class_shadows(
            source, namespace, scope, base_objects, family="model"
        )

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
        contents = dict(sources.values())
        projection_is_autogen = contents[facade_path].startswith(
            c.Infra.AUTOGEN_HEADERS
        )
        barrel = contents.get(roots[1] / c.Infra.INIT_PY)
        scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            contents[facade_path],
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
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
                message = f"Unresolved facade base: {facade_path}:{ast.unparse(base)}"
                raise ValueError(message)
            if FlextInfraUtilitiesRopeRuntime.semantic_module(binding.get_object()):
                message = f"Module used as a class base: {ast.unparse(base)}"
                raise ValueError(message)
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
                all((
                    projection_is_autogen,
                    path.parent == roots[1].resolve(),
                    path.name != c.Infra.INIT_PY,
                    FlextInfraUtilitiesRopeRuntime.py_class(binding.get_object()),
                ))
                and any(
                    isinstance(node, ast.ClassDef)
                    and node.name == binding.get_object().get_name()
                    for node in ast.parse(contents[path], filename=str(path)).body
                )
                and binding.get_object().get_name()
                not in (
                    FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                        contents[path]
                    )
                )
            ) or (
                path.is_relative_to(roots[0].resolve())
                and not path.is_relative_to(roots[1].resolve())
            ):
                retired.add(ast.unparse(base))
        return frozenset(retired)

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
            and barrel.startswith(c.Infra.AUTOGEN_HEADERS)
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

    @classmethod
    def _declared_sources(
        cls,
        pkg_dir: Path,
        owners_dir: Path,
        *,
        contents: t.MappingKV[Path, str],
        project: p.Infra.RopeProject,
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
        cls._facade_source_membership(project, owners_dir, contents)
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

        """
        project, contents = binding
        for parent in sorted({
            path.parent
            for path in contents
            if path.is_relative_to(pkg_dir) and path.suffix == c.Infra.EXT_PYTHON
        }):
            cls._facade_source_membership(project, parent, contents)
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
                c.Infra.AUTOGEN_HEADERS,
            ):
                continue
            tree = ast.parse(source, filename=str(path))
            pymodule: t.Infra.RopePyModule | None = None
            module_paths: t.MutableMappingKV[p.Infra.RopeImportedModule, Path] = {}
            for reference in (
                node for node in ast.walk(tree) if isinstance(node, ast.Attribute)
            ):
                receiver = reference.value
                public_receiver = not nested_namespace or (
                    isinstance(receiver, ast.Attribute) and receiver.attr == namespace
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
                imported_binding = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    FlextInfraUtilitiesRopeRuntime.scope_at(pymodule, offset),
                    receiver,
                )
                if (
                    not isinstance(imported_binding, p.Infra.RopeImportedName)
                    or imported_binding.imported_name != family
                ):
                    continue
                imported = imported_binding.imported_module
                if (
                    imported.level == 0
                    and imported.module_name is not None
                    and imported.module_name.split(".", 1)[0] in sys.stdlib_module_names
                ):
                    # Standard-library imports cannot declare owned facades.
                    # Built-in modules have no source resource for Rope.
                    continue
                declared = FlextInfraUtilitiesRopeRuntime.imported_module_path(
                    project,
                    imported_binding,
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
            cls._facade_source_membership(project, parent, contents)
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
