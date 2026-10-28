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

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacadeSyntax,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesFacadeComponents,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeClassMove,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesInventory,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesSemanticCutover,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)


class FlextInfraUtilitiesCodegenFacades(
    FlextInfraUtilitiesCodegenFacadeSyntax,
    FlextInfraUtilitiesRopeClassMove,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesSemanticCutover,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesWorkspaceSnapshot,
):
    """Compose declared facade owners and resolve consumed protocols."""

    class _UpstreamSourceView:
        """Keep publication reads and member identities in one captured epoch."""

        def __init__(
            self,
            project: p.Infra.RopeProject,
            sources: t.MappingKV[str, t.Pair[Path, str]],
        ) -> None:
            self.project = project
            self.sources = sources
            self.resolve = (
                FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                    project, sources=sources
                )
            )

        def source(self, module: p.Infra.RopeParsedModule) -> str:
            """Read exports from the captured provider's actual source origin.

            Returns:
                Captured text, native module text, or the native package initializer.

            Raises:
                ValueError: If the provider has no resource or a conflicting origin.
                TypeError: If a file provider is not a native source module.

            """
            resource = module.get_resource()
            if resource is None:
                message = f"Publication provider has no source: {module.get_name()}"
                raise ValueError(message)
            path = Path(resource.real_path)
            if resource.is_folder():
                path /= c.Infra.INIT_PY
            captured = self.sources.get(module.get_name())
            if captured is not None:
                if captured[0] != path:
                    message = f"Publication source origin differs: {module.get_name()}"
                    raise ValueError(message)
                return captured[1]
            if resource.is_folder():
                return self.project.source_text(path)
            if not FlextInfraUtilitiesRopeRuntime.source_module(module):
                message = f"Publication provider is not source: {module.get_name()}"
                raise TypeError(message)
            return module.source_code

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

    @classmethod
    def candidate_python_sources(
        cls,
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
            for path, source in (cls.facade_original_sources(scope, states)).items()
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
            declared_sources,
        )
        source = cls._inherit_upstream_namespace(
            project, facade_path, source, captured_sources=sources
        )
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
                (facade_path, source),
                family=c.Infra.FacadeFamily.T,
                binding=(project, sources),
            )
            return cls._generated_facade(
                pkg_dir,
                source,
                family=c.Infra.FacadeFamily.T,
                binding=(project, sources),
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
                    (facade_path, source),
                    family=c.Infra.FacadeFamily.T,
                    binding=(project, sources),
                ),
                family=c.Infra.FacadeFamily.T,
                binding=(project, sources),
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
        declared_sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
        owner = cls._complete_type_owner(
            pkg_dir,
            (facade_path, facade),
            sources,
            binding=(project, declared_sources),
        )
        alias = (
            f"_{facade.name}"
            if owner.attributes[0] == facade.name
            else owner.attributes[0]
        )
        imported = (
            f"{owner.attributes[0]} as {alias}"
            if owner.attributes[0] == facade.name
            else alias
        )
        rendered = (
            f"{ast.get_source_segment(source, tree.body[0])}\n\n"
            "# Generated type facade; declarations belong to "
            f"{owner.target}.\n"
            f"from {owner.target.rpartition('.')[0]} "
            f"import {imported}\n\n\n"
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
            binding=(project, sources),
        )

    @classmethod
    def _complete_type_owner(
        cls,
        pkg_dir: Path,
        facade: t.Pair[Path, ast.ClassDef],
        sources: t.MappingKV[Path, str],
        *,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[str, t.Pair[Path, str]]],
    ) -> m.Infra.SourceClassReference:
        """Admit one exported complete owner and its declaration-time facade base.

        Returns:
            The actual declaring module and class, independent of facade spelling.

        Raises:
            ValueError: If publication or bases do not retain the elected identity.

        """
        project, declared_sources = binding
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
            (path, binding.value.id)
            for path, content in sources.items()
            if path.is_relative_to(pkg_dir / directory)
            and path.name != c.Infra.INIT_PY
            and "t"
            in FlextInfraUtilitiesRopeModulePatch.facade_letter_names_at(project, path)
            for binding in FlextInfraUtilitiesRopeModulePatch.runtime_alias_bindings(
                content,
                alias="t",
            )
            if isinstance(binding, ast.Assign)
            and isinstance(binding.value, ast.Name)
            and binding.value.id
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                content
            )
            and any(
                isinstance(node, ast.ClassDef) and node.name == binding.value.id
                for node in ast.parse(content, filename=str(path)).body
            )
        )
        if len(owners) != 1:
            msg = f"expected one full exported type owner: {facade[0]}"
            raise ValueError(msg)
        owner, owner_class = owners[0]
        view = cls._UpstreamSourceView(project, declared_sources)
        reference = m.Infra.SourceClassReference(
            target=next(
                name for name, (path, _) in declared_sources.items() if path == owner
            ),
            attributes=(owner_class,),
            qualified_base=owner_class,
        )
        owner_binding = view.resolve(reference)
        owner_object = owner_binding.get_object()
        provider = owner_binding.get_definition_location()[0]
        if (
            not FlextInfraUtilitiesRopeRuntime.abstract_class(owner_object)
            or provider is None
            or (resource := provider.get_resource()) is None
            or Path(resource.real_path) != owner
            or view.resolve(
                m.Infra.SourceClassReference(
                    target=reference.target,
                    attributes=("t",),
                    qualified_base="t",
                )
            ).get_object()
            is not owner_object
        ):
            msg = f"unsupported complete type owner binding: {owner}"
            raise ValueError(msg)
        pymodule = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            next(text for path, text in declared_sources.values() if path == facade[0]),
            resource=project.get_resource(
                facade[0].relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        if len(facade[1].bases) > 1 or any(
            cls._declared_base_binding(view, pymodule, facade, base).get_object()
            is not owner_object
            for base in facade[1].bases
        ):
            msg = f"unsupported complete type facade bases: {facade[0]}"
            raise ValueError(msg)
        return reference

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
                package_name,
                owners_dir,
                source,
                declarations,
                declared_sources,
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
                    (facade_path, source),
                    family=selected_family,
                    binding=(project, sources),
                ),
                family=selected_family,
                binding=(project, sources),
            )
        source = cls._inherit_upstream_namespace(
            project, facade_path, source, captured_sources=sources
        )
        if selected_family is not c.Infra.FacadeFamily.P:
            rendered = cls._render_declared_facade(
                pkg_dir,
                (facade_path, source),
                family=selected_family,
                binding=(project, sources),
            )
        else:
            rendered = cls._render_protocol_facade(
                pkg_dir, facade_path, source, binding=(project, sources)
            )
        return cls._generated_facade(
            pkg_dir, rendered, family=selected_family, binding=(project, sources)
        )

    @classmethod
    def family_subfacade_identity(
        cls,
        directory: Path,
        family_root: Path,
        *,
        family: c.Infra.FacadeFamily,
        project: p.Infra.RopeProject,
    ) -> t.Pair[Path, str]:
        """Derive one recursive domain publication from its elected family.

        Returns:
            The declared sibling owner, or the canonical path for a new owner.

        Raises:
            ValueError: The domain has no canonical family or project identity.
            TypeError: If Native domain owner is not a class.

        """
        declared = cls.facade_families()[family]
        if family_root.name != declared.directory or directory == family_root:
            message = f"Subfacade has no nested family domain: {directory}"
            raise ValueError(message)
        domains = directory.relative_to(family_root).parts
        if not all(
            name.startswith("_") and name.lstrip("_").isidentifier() for name in domains
        ):
            message = f"Subfacade has a noncanonical domain path: {directory}"
            raise ValueError(message)
        path = directory.parent / f"{directory.name.lstrip('_')}.py"
        owners = cls.family_subfacade_owners(project, directory)
        if len(owners) > 1:
            evidence: list[str] = []
            for owner_path, owner_name in owners:
                module = cls.require_semantic_module(
                    project.get_pymodule(cls.file_resource_at(project, owner_path))
                )
                owner = module.get_attributes()[owner_name].get_object()
                if not cls.py_class(owner):
                    message = f"Native domain owner is not a class: {owner_name}"
                    raise TypeError(message)
                for relation, suppliers in (
                    ("bases", tuple(owner.get_superclasses())),
                    (
                        "members",
                        tuple(cls._component_member_suppliers(owner, project=project)),
                    ),
                    ("calls", tuple(cls._component_callable_suppliers(owner))),
                ):
                    identities = tuple(
                        f"{supplier.get_module().get_resource()}:{supplier.get_name()}"
                        for supplier in suppliers
                        if cls.py_class(supplier)
                    )
                    evidence.append(
                        f"{owner_path}:{owner_name} {relation}"
                        f"[{len(identities)}]={identities[:8]}"
                    )
            message = (
                f"Competing native domain facade owners: {directory}: {owners}; "
                f"native composition evidence: {evidence}"
            )
            raise ValueError(message)
        if owners:
            if (
                owners[0][0] == family_root / c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
                and owners[0][0] != path
            ):
                message = (
                    "Root family base cannot be relocated as a domain facade: "
                    f"{directory}"
                )
                raise ValueError(message)
            return path, owners[0][1]
        prefix = cls.project_prefix(path, source_project=project)
        if not prefix:
            message = f"Subfacade has no project class identity: {path}"
            raise ValueError(message)
        domain = u.derive_class_stem(
            "-".join(name.lstrip("_").replace("_", "-") for name in domains)
        )
        return path, f"{prefix}{declared.suffix}{domain}"

    @classmethod
    def family_subfacade_owners(
        cls, project: p.Infra.RopeProject, directory: Path
    ) -> list[t.Pair[Path, str]]:
        """Elect authored compositions beside or inside their native child domain.

        A holder must compose another domain module's native class. Its own nested
        declarations do not establish an independent domain-composition identity.
        A declaration inside the native child domain outranks an external
        composition, and the canonical sibling outranks both. A holder whose
        declared suppliers span more than one private domain directory is a
        family-root composition, never a single-domain owner. Incomparable
        publications at the elected precedence remain competing owners. Entity
        specializations consume a domain rather than publish its namespace; an
        existing canonical sibling still requires native domain composition proof.

        Returns:
            Existing compositions, without deriving ownership from class spelling.

        """
        owners: list[t.Pair[Path, str]] = []
        classes: list[p.Infra.RopeSourceClass] = []
        priorities: list[t.Pair[bool, t.Pair[bool, bool]]] = []
        model = FlextInfraUtilitiesDeclarationPayload.identity_name(
            project, "pydantic.BaseModel"
        ).get_object()
        canonical = directory.parent / f"{directory.name.lstrip('_')}.py"
        for path in sorted({
            *cls._facade_source_membership(project, directory.parent),
            *cls._facade_source_membership(project, directory),
        }):
            if path.name == c.Infra.INIT_PY:
                continue
            module = cls.require_semantic_module(
                project.get_pymodule(cls.file_resource_at(project, path))
            )
            exports = cls.public_export_names_source(project.source_text(path))
            for name in exports:
                binding = module.get_attributes().get(name)
                if binding is None or not cls.py_class(owner := binding.get_object()):
                    continue
                if owner.get_module() is not module or owner.get_name() != name:
                    continue
                if (
                    cls._component_defines_methods(owner)
                    and path.parent != directory.parent
                ):
                    continue
                declared_suppliers = (
                    *owner.get_superclasses(),
                    *cls._component_member_suppliers(owner, project=project),
                    *(
                        cls._component_callable_suppliers(owner)
                        if path == canonical
                        else ()
                    ),
                )
                evidence = any(
                    cls.py_class(supplier)
                    and supplier is not owner
                    and (resource := supplier.get_module().get_resource()) is not None
                    and Path(resource.real_path).parent == directory
                    and Path(resource.real_path) != path
                    and (
                        path == canonical
                        or (
                            model not in cls.class_ancestry(supplier)
                            and cls._subfacade_namespace_supplier(
                                supplier, project=project
                            )
                        )
                    )
                    for supplier in declared_suppliers
                )
                if evidence:
                    supplier_directories = {
                        Path(resource.real_path).parent
                        for supplier in declared_suppliers
                        if (
                            cls.py_class(supplier)
                            and (resource := supplier.get_module().get_resource())
                            is not None
                            and Path(resource.real_path).parent.name.startswith("_")
                        )
                    }
                    if len(supplier_directories) > 1 and path != canonical:
                        continue
                    owners.append((path, name))
                    classes.append(owner)
                    priorities.append((
                        path == canonical,
                        (path.parent == directory, path.parent == directory.parent),
                    ))
        composed = tuple(
            frozenset(
                ancestor
                for supplier in (
                    owner,
                    *cls._component_member_suppliers(owner, project=project),
                )
                if cls.py_class(supplier)
                for ancestor in cls.class_ancestry(supplier)
            )
            for owner in classes
        )
        return [
            owner
            for index, owner in enumerate(owners)
            if priorities[index] == max(priorities)
            and not any(
                classes[index] in lineage and classes[other] not in composed[index]
                for other, lineage in enumerate(composed)
                if other != index and priorities[other] == priorities[index]
            )
        ]

    @classmethod
    def _subfacade_namespace_supplier(
        cls,
        supplier: p.Infra.RopeSourceClass,
        *,
        project: p.Infra.RopeProject,
    ) -> bool:
        """Prove that a consumed class is its module's exported namespace holder.

        Nested entities and their bases are consumers' specialization contracts,
        not evidence that their enclosing consumer publishes the source namespace.

        Returns:
            Whether a source-declared export binds the same native class object.

        """
        module = supplier.get_module()
        resource = module.get_resource()
        if resource is None:
            return False
        exports = cls.public_export_names_source(
            project.source_text(Path(resource.real_path))
        )
        attributes = module.get_attributes()
        return any(
            (binding := attributes.get(name)) is not None
            and binding.get_object() is supplier
            for name in exports
        )

    @classmethod
    def _maximal_native_owner_indices(
        cls, owners: t.SequenceOf[p.Infra.RopePyObject]
    ) -> tuple[int, ...]:
        """Return owners not already composed by another strict native descendant."""
        ancestry = tuple(cls.class_ancestry(owner) for owner in owners)
        return tuple(
            index
            for index, owner in enumerate(owners)
            if not any(
                owner in lineage and owners[other] not in ancestry[index]
                for other, lineage in enumerate(ancestry)
                if other != index
            )
        )

    @classmethod
    def _component_defines_methods(cls, owner: p.Infra.RopeSourceClass) -> bool:
        """Read direct callable declarations without inferring nested class metadata.

        Returns:
            Whether the owner's lexical class scope declares a method.

        Raises:
            TypeError: The native class has no class declaration.

        """
        declaration = owner.get_ast()
        if not isinstance(declaration, ast.ClassDef):
            message = f"Native class has no class declaration: {owner.get_name()}"
            raise TypeError(message)
        parents = cls.ast_parent_map(declaration)
        for node in ast.walk(declaration):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            parent = parents[id(node)]
            while parent is not declaration:
                if isinstance(parent, ast.ClassDef):
                    break
                parent = parents[id(parent)]
            else:
                return True
        return False

    @classmethod
    def _component_callable_suppliers(
        cls, owner: p.Infra.RopeSourceClass
    ) -> Generator[p.Infra.RopePyObject]:
        """Yield native class receivers called in directly declared method bodies.

        Imports and annotations do not establish executable domain delegation.
        Each receiver resolves in its actual native lexical scope, without loading
        the implementation or inferring ownership from its spelling.

        Yields:
            Native class receivers with a resolved callable member.

        Raises:
            TypeError: If the native owner lacks source or a parent is not an AST.

        """
        module = owner.get_module()
        if not FlextInfraUtilitiesRopeRuntime.source_module(module):
            message = (
                f"Callable component has no native source module: {owner.get_name()}"
            )
            raise TypeError(message)
        for scope in owner.get_scope().get_scopes():
            if not FlextInfraUtilitiesRopeRuntime.py_function(
                function := scope.pyobject
            ):
                continue
            declaration = function.get_ast()
            if not isinstance(declaration, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            parents = cls.ast_parent_map(declaration)
            for statement in declaration.body:
                for node in ast.walk(statement):
                    if not isinstance(node, ast.Call) or not isinstance(
                        node.func, ast.Attribute
                    ):
                        continue
                    if cls._component_direct_method_call(node, declaration, parents):
                        lexical = FlextInfraUtilitiesRopeRuntime.scope_at(
                            module,
                            FlextInfraUtilitiesRopeRuntime.source_offset(
                                module.source_code, node.func.value
                            ),
                        )
                        receiver = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                            lexical, node.func.value
                        )
                        called = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                            lexical, node.func
                        )
                        if (
                            receiver is not None
                            and cls.py_class(supplier := receiver.get_object())
                            and called is not None
                            and FlextInfraUtilitiesRopeRuntime.py_function(
                                called.get_object()
                            )
                        ):
                            yield supplier

    @staticmethod
    def _component_direct_method_call(
        node: ast.Call,
        declaration: ast.FunctionDef | ast.AsyncFunctionDef,
        parents: t.MappingKV[int, p.Infra.RopeAstNode],
    ) -> bool:
        """Exclude annotations and nested declarations from method call evidence.

        Returns:
            Whether the call belongs to the directly declared method body.

        Raises:
            TypeError: If the native parent mapping contains a non-AST node.

        """
        child: ast.AST = node
        parent = parents[id(child)]
        while parent is not declaration:
            if not isinstance(parent, ast.AST):
                message = "Callable component parent is not a native AST"
                raise TypeError(message)
            if isinstance(
                parent, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ) or (isinstance(parent, ast.AnnAssign) and parent.annotation is child):
                return False
            child, parent = parent, parents[id(parent)]
        return True

    @classmethod
    def _component_member_suppliers(
        cls,
        owner: p.Infra.RopeSourceClass,
        *,
        project: p.Infra.RopeProject,
    ) -> Generator[p.Infra.RopePyObject]:
        """Read declaration-time aliases after superclass evidence is exhausted.

        A same-name class assignment binds its imported declaration before the
        assignment, not the unresolved self-reference inferred in its class scope.
        Ordinary class publications supply composition only when an existing
        public namespace already authenticates this holder through native MRO.

        Yields:
            Objects bound by the class's own declared members.

        Raises:
            ValueError: If a member's binding is ambiguous.
            TypeError: The native owner does not expose a class declaration.

        """
        for scope in owner.get_scope().get_scopes():
            if cls.py_class(nested := scope.pyobject):
                yield from nested.get_superclasses()
                yield from cls._component_member_suppliers(nested, project=project)
        declaration = owner.get_ast()
        if not isinstance(declaration, ast.ClassDef):
            message = f"Component owner has no class declaration: {owner.get_name()}"
            raise TypeError(message)
        members = owner.get_scope().get_defined_names()
        declared = cls._declared_namespace_members(declaration) - {
            node.name
            for node in declaration.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        }
        composition = FlextInfraUtilitiesFacadeComponents.facade_composes_class(
            owner, source_project=project
        )
        for name in sorted(declared):
            member = members[name]
            kind = FlextInfraUtilitiesFacadeMembers.facade_member_kind(
                member, source_project=project
            )
            if kind is c.Infra.FacadeMemberKind.CONSTANT or (
                not composition and kind is c.Infra.FacadeMemberKind.TYPE
            ):
                continue
            binding = cls.class_assignment_binding(member, classes_only=False)
            if binding is None:
                message = (
                    "Ambiguous native component member: "
                    f"{member.get_definition_location()}"
                )
                raise ValueError(message)
            yield binding.get_object()

    @classmethod
    def family_subfacade_seed(
        cls,
        path: Path,
        class_name: str,
        *,
        directory: Path,
        sources: t.MappingKV[Path, str],
    ) -> str:
        """Keep the authored composition, or seed its generated declaration.

        Returns:
            The one source declaration whose MRO the existing renderer composes.

        Raises:
            ValueError: An existing sibling publishes another class.

        """
        source = sources.get(path)
        if source is not None:
            classes = tuple(
                node.name.value
                for node in parse_module(source).body
                if isinstance(node, ClassDef)
            )
            if classes != (class_name,):
                message = f"Subfacade sibling has competing ownership: {path}"
                raise ValueError(message)
            return source
        initializer = sources.get(directory / c.Infra.INIT_PY)
        documentation = (
            parse_module(initializer).get_docstring(clean=False)
            if initializer is not None
            else None
        )
        if not documentation:
            message = f"Subfacade domain has no governed documentation: {directory}"
            raise ValueError(message)
        return (
            f"{documentation!r}\n\n"
            "from __future__ import annotations\n\n\n"
            f"class {class_name}:\n"
            '    """Compose the domain declarations through their native MRO."""\n\n\n'
            f"__all__: list[str] = [{class_name!r}]\n"
        )

    @classmethod
    def family_subfacade_source_owner(
        cls,
        path: Path,
        class_name: str,
        *,
        directory: Path,
        project: p.Infra.RopeProject,
    ) -> Path | None:
        """Locate the elected native declaration before its canonical module move.

        Returns:
            The actual source owner, including an already canonical sibling.

        Raises:
            ValueError: Multiple native owners declare the selected composition.

        """
        if path.parent != directory.parent:
            message = f"Subfacade destination has another domain authority: {path}"
            raise ValueError(message)
        owners = tuple(
            candidate
            for candidate, name in cls.family_subfacade_owners(project, directory)
            if name == class_name
        )
        if len(owners) > 1:
            message = (
                f"Competing recursive subfacade declarations: {class_name}: {owners}"
            )
            raise ValueError(message)
        return owners[0] if owners else None

    @classmethod
    def render_family_subfacade(
        cls,
        directory: Path,
        path: Path,
        *,
        family: c.Infra.FacadeFamily,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> str:
        """Compose a recursive domain through the same family MRO renderer.

        Returns:
            The generated sibling facade, without writing source files.

        """
        module = cls.require_semantic_module(
            project.get_pymodule(cls.file_resource_at(project, path))
        )
        callable_boundary = any(
            candidate == path
            and (binding := module.get_attributes().get(name)) is not None
            and cls.py_class(owner := binding.get_object())
            and cls._component_defines_methods(owner)
            for candidate, name in cls.family_subfacade_owners(project, directory)
        )
        rendered = (
            sources[path]
            if callable_boundary
            else cls._render_declared_facade(
                directory.parent,
                (path, sources[path]),
                family=family,
                binding=(project, sources),
                owners_dir=directory,
            )
        )
        return cls._generated_facade(
            directory.parent,
            rendered,
            family=family,
            binding=(project, sources),
            owners_dir=directory,
        )

    @staticmethod
    def _component_stage_plans(
        planned: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        additions: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> None:
        """Admit stage effects only through the authenticated plan composer.

        Ordered composition advances desired bytes for a destination only when
        the original authority agrees; competing stage effects escape from the
        composer unchanged.

        """
        composed = FlextInfraUtilitiesCodegenFilePlan.codegen_compose_file_plans(
            (*staged.values(), *additions), ordered=True
        )
        staged.clear()
        staged.update((plan.path, plan) for plan in composed)
        composed = FlextInfraUtilitiesCodegenFilePlan.codegen_compose_file_plans(
            (*planned.values(), *additions), ordered=True
        )
        planned.clear()
        planned.update((plan.path, plan) for plan in composed)

    @classmethod
    def _require_component_snapshot(
        cls,
        root: Path,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> Path:
        """Verify the snapshot is the native capture of this repository.

        Returns:
            The resolved repository root on provenance match.

        Raises:
            ValueError: The snapshot belongs to another repository.

        """
        if (
            snapshot.workspace_root != root
            or Path(snapshot.engine.root.real_path) != root
        ):
            message = f"Component snapshot belongs to another repository: {root}"
            raise ValueError(message)
        return root

    @classmethod
    def plan_component_facades(
        cls,
        root: Path,
        *,
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        snapshot: p.Infra.WorkspaceSnapshot,
        planners: t.Pair[p.Infra.SourceInitializerPlanner, p.Infra.SourceViewProvider],
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Compose recursive domains, root facades and exports in one candidate.

        Existing file plans retain their physical witnesses and tombstones.
        Ownership is elected from the observed snapshot before initializers can
        withhold an export that its pending native move still needs to replace.
        The current candidate continues to own moves, rewrites and final bindings.
        Stateless provider publications retire only after native callable consumer
        closure. Entity and stateful-helper declarations are not compatibility
        providers and retain their original publication contracts.
        Every source move and seed is rebound before its renderer consumes it.
        The supplied initializer capability uses the existing lazy-export
        planner; this utility neither publishes nor implements another renderer.
        The caller supplies its existing epoch-bound source views. Unchanged
        candidates borrow the same native project; every actual effect rebinds
        before dependent rendering without replacing physical plan witnesses.
        A selected destination must declare its admitted family in this native
        view. Only that package's private family and its native move consumers
        join the candidate. A package initializer with no family selects its
        recursive package domains; None explicitly selects all owned families.

        Returns:
            Component, relocation and dependent initializer plans.

        """
        root = cls._require_component_snapshot(root.resolve(), snapshot)
        initializer_planner, source_view = planners
        staged = {plan.path: plan for plan in declared_files}
        planned: dict[Path, m.Infra.CodegenFilePlan] = {}
        utility_paths: set[Path] = set()

        def elected_domains() -> p.Result[
            t.SequenceOf[t.Triple[Path, Path, c.Infra.FacadeFamily]]
        ]:
            """Elect the selected recursive domains from the observed capture.

            Election authority is the observed capture, unconditionally:
            pending initializers may withhold a consumed parent export in the
            candidate view, and a vanished export never revokes the input
            declaration's native ownership. Import rebinds are derived from
            the recorded move and staged before rendering, never elected
            from a candidate view whose publisher is pending retirement.

            Returns:
                The elected domains, or the first staged failure.

            """
            with source_view(root, declared_files=tuple(staged.values())) as binding:
                return cls._component_selected_domains(
                    root, snapshot, binding, selection=selection
                )

        def finalize_roots() -> p.Result[bool]:
            """Stage root facades, close consumers and replan initializers.

            Returns:
                Success, or the first root, consumer or initializer failure.

            """
            roots = cls._component_root_plans(
                root, snapshot, staged, source_view=source_view, selection=selection
            )
            if roots.failure:
                return r[bool].from_failure(roots)
            cls._component_stage_plans(
                planned, staged, tuple(plan for plan, _ in roots.value)
            )
            utility_paths.update(
                plan.path
                for plan, family in roots.value
                if family is c.Infra.FacadeFamily.U
            )
            consumers = cls._component_consumer_plans(
                root, utility_paths, staged, source_view=source_view
            )
            cls._component_stage_plans(planned, staged, consumers)
            initializers = initializer_planner(
                root,
                declared_files=tuple(staged.values()),
                snapshot=snapshot,
                selection=selection,
            )
            if initializers.failure:
                return r[bool].from_failure(initializers)
            cls._component_stage_plans(planned, staged, initializers.value)
            return r[bool].ok(value=True)

        def plan_cohort(
            domains: t.SequenceOf[t.Triple[Path, Path, c.Infra.FacadeFamily]],
        ) -> p.Result[bool]:
            """Seed, move and render every domain, deepest first.

            Election authority stays the observed capture; the recorded move
            and the renderer own the candidate-side rebind. Initializer
            replanning runs after each depth's actual effects so dependent
            renders consume their real interfaces.

            Returns:
                Success, or the first planner failure in any depth cohort.

            """
            for depth in sorted(
                {len(domain[1].parts) for domain in domains}, reverse=True
            ):
                targets = tuple(
                    domain for domain in domains if len(domain[1].parts) == depth
                )
                seeds = {
                    domain: cls._component_seed(
                        root,
                        domain,
                        staged,
                        source_view=source_view,
                        ownership_project=snapshot.engine,
                    )
                    for domain in targets
                }
                moved = tuple(
                    plan for _, seed_moved in seeds.values() for plan in seed_moved
                )
                cls._component_stage_plans(planned, staged, moved)
                initializers = initializer_planner(
                    root,
                    declared_files=tuple(staged.values()),
                    snapshot=snapshot,
                    selection=selection,
                )
                if initializers.failure:
                    return r[bool].from_failure(initializers)
                cls._component_stage_plans(planned, staged, initializers.value)
                cls._component_rebind_imports(
                    snapshot,
                    staged,
                    planned,
                    source_view=source_view,
                    selection=selection,
                )
                for domain, (seed, _) in seeds.items():
                    final = cls._component_render(
                        root, domain, seed, staged, source_view=source_view
                    )
                    cls._component_stage_plans(planned, staged, (final,))
                    if domain[2] is c.Infra.FacadeFamily.U:
                        utility_paths.add(final.path)
            return r[bool].ok(value=True)

        return (
            elected_domains()
            .flat_map(plan_cohort)
            .flat_map(lambda _: finalize_roots())
            .map(lambda _: tuple(planned.values()))
        )

    @classmethod
    def _component_rebind_imports(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        planned: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> None:
        """Stage root-facade import rebinds after this cohort's recorded moves.

        The rebind is derived from the recorded move: the staged view already
        contains the destination module and the retired publisher, so the seed
        elects the surviving publisher instead of the retired one. The root is
        the snapshot's verified workspace root.

        """
        root = snapshot.workspace_root
        with source_view(root, declared_files=tuple(staged.values())) as binding:
            rebound = cls._component_root_import_seeds(
                root, snapshot, binding, selection=selection
            )
        cls._component_stage_plans(planned, staged, rebound)

    @classmethod
    def _component_root_import_seeds(
        cls,
        root: Path,
        snapshot: p.Infra.WorkspaceSnapshot,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        *,
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Rebind unique native publications before querying generated ancestry.

        The component renderer still owns the final MRO. These import-only seeds
        retain physical witnesses and never fabricate a declaration or a base.

        Returns:
            The relocated import seeds for every generated root facade.

        """
        project, sources = binding
        return tuple(
            plan
            for package, family in cls._component_root_families(
                root, snapshot, binding, selection=selection
            )
            for plan in cls._component_import_seed_plans(
                root, project, sources, package, family
            )
        )

    @classmethod
    def _component_import_seed_plans(
        cls,
        root: Path,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        package: Path,
        family: c.Infra.FacadeFamily,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Rewrite one generated root facade's relocated member imports.

        Returns:
            The relocation plan, or no plan when the facade keeps its imports.

        """
        path = cls.facade_module_path(package, family, project=project, sources=sources)
        if path is None or not sources[path].startswith(c.Infra.AUTOGEN_HEADER):
            return ()
        directory = package / cls.facade_families()[family].directory
        if directory / c.Infra.INIT_PY not in sources:
            return ()
        package_name = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            package, project_root=root, source_project=project
        )
        prefix = f"{package_name}.{directory.name}"
        module = cls.require_semantic_module(
            project.get_pymodule(
                cls.file_resource_at(project, directory / c.Infra.INIT_PY)
            )
        )
        source = sources[path]
        tree = ast.parse(source)
        base_names = {
            node.id
            for declaration in ast.walk(tree)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            for node in ast.walk(base)
            if isinstance(node, ast.Name)
        }
        for statement in ast.walk(tree):
            if not isinstance(statement, ast.ImportFrom) or statement.module != prefix:
                continue
            for alias in statement.names:
                name = alias.asname or alias.name
                current = module.get_attributes().get(name)
                if name not in base_names or (
                    current is not None and cls.abstract_class(current.get_object())
                ):
                    continue
                if not any(
                    f"class {name}(" in content or f"class {name}:" in content
                    for content in sources.values()
                ):
                    # A base declared nowhere is retired: the root facade
                    # composition rebuild drops its import and base, so no
                    # publisher is required.
                    continue
                target = cls._component_seed_publisher(
                    project, sources, directory, prefix, name
                )
                if target is None:
                    continue
                source = cls._relocated_import_source(
                    source,
                    package_name,
                    (prefix, name),
                    target,
                )
        if source == sources[path]:
            return ()
        before = project.source_state(path, required=True)
        return (
            m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=before,
                desired_content=source.encode(c.DEFAULT_ENCODING),
                desired_mode=before.mode,
            ),
        )

    @classmethod
    def _component_seed_publisher(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        directory: Path,
        prefix: str,
        name: str,
    ) -> str | None:
        """Locate the unique child initializer publishing a relocated owner.

        Returns:
            The child package importing the native class declaration, or ``None``
            when no child publishes it anymore and the declared-facade stage owns
            the retired binding.

        Raises:
            ValueError: The owner has competing child-facade publishers.

        """
        publishers: list[str] = []
        declaring: dict[str, Path] = {}
        for child, content in sources.items():
            if child.suffix != ".py" or child.parent == directory:
                continue
            if not child.is_relative_to(directory):
                continue
            declares = f"class {name}(" in content or f"class {name}:" in content
            if child.name != c.Infra.INIT_PY:
                # The recorded move's destination declares the holder in the
                # candidate view; it is the surviving publisher, and being
                # the shallowest declaring module it outranks retired child
                # initializer re-exports.
                previous = declaring.get(name)
                if declares and (
                    previous is None or len(child.parts) < len(previous.parts)
                ):
                    declaring[name] = child
                continue
            if name not in cls.public_export_names_source(content):
                continue
            exported = (
                cls
                .require_semantic_module(
                    project.get_pymodule(cls.file_resource_at(project, child))
                )
                .get_attributes()
                .get(name)
            )
            if exported is None or not cls.py_class(exported.get_object()):
                continue
            publishers.append(
                ".".join((prefix, *child.parent.relative_to(directory).parts))
            )
        if len(publishers) > 1:
            message = (
                "Relocated facade import has competing native publishers: "
                f"{name}: {publishers}"
            )
            raise ValueError(message)
        if name in declaring:
            destination = declaring[name]
            return ".".join((prefix, *destination.parent.relative_to(directory).parts))
        return publishers[0] if publishers else None

    @classmethod
    def _component_consumer_plans(
        cls,
        root: Path,
        utility_paths: set[Path],
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Close receiver rewrites before retiring their component publications.

        The shared candidate advances between these dependent steps. A file
        changed by both retains its last source and original publication witness.

        Returns:
            The closed consumer plans, also bound into the shared candidate.

        """
        with source_view(root, declared_files=tuple(staged.values())) as (project, _):
            consumers = FlextInfraUtilitiesFacadeComponents.plan_component_consumers(
                root, source_project=project, declared_files=tuple(staged.values())
            )
        planned = {plan.path: plan for plan in consumers}
        staged.update(planned)
        retired = cls._component_provider_retirements(
            root, utility_paths, staged, source_view=source_view
        )
        planned.update((plan.path, plan) for plan in retired)
        staged.update(planned)
        return tuple(planned.values())

    @classmethod
    def _component_root_plans(
        cls,
        root: Path,
        snapshot: p.Infra.WorkspaceSnapshot,
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[
        t.VariadicTuple[t.Pair[m.Infra.CodegenFilePlan, c.Infra.FacadeFamily]]
    ]:
        """Plan root compositions against each updated shared candidate view.

        Returns:
            Original root plans and families, or the unchanged selection failure.

        """
        result_type = r[
            t.VariadicTuple[t.Pair[m.Infra.CodegenFilePlan, c.Infra.FacadeFamily]]
        ]
        planned: list[t.Pair[m.Infra.CodegenFilePlan, c.Infra.FacadeFamily]] = []
        with source_view(root, declared_files=tuple(staged.values())) as binding:
            families = cls._component_root_families(
                root, snapshot, binding, selection=selection
            )
        for package, family in families:
            with source_view(root, declared_files=tuple(staged.values())) as binding:
                final = cls._component_root_facade(
                    root, package, family, binding[0], binding[1]
                )
            selection_error = cls._component_selection_error(selection, final)
            if selection_error is not None:
                return result_type.fail(selection_error)
            if final is not None:
                planned.append((final, family))
                staged[final.path] = final
        return result_type.ok(tuple(planned))

    @classmethod
    def _component_provider_retirements(
        cls,
        root: Path,
        paths: set[Path],
        staged: t.MappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Retire exact stateless providers after their candidate consumers close.

        Native role, public composition and effective callable identity are all
        required. A remaining publication consumer, including a mutation target,
        rejects the cohort instead of retaining an alias or changing its owner.

        Returns:
            Updated compositions retaining the original physical witnesses.

        Raises:
            ValueError: A composed provider differs or still has an alias consumer.

        """
        publications: dict[
            t.Pair[p.Infra.RopeClassObject, str], p.Infra.RopeClassObject
        ] = {}
        updates: dict[Path, str] = {}
        with source_view(root, declared_files=tuple(staged.values())) as (
            project,
            sources,
        ):
            captured = cls._captured_publication_sources(
                project, captured_sources=sources
            )
            for path in sorted(paths):
                source = sources[path]
                facade, namespace, scope, _, bases, _ = cls._facade_namespace_context(
                    cls._UpstreamSourceView(project, captured), source, path
                )
                holder = cls.require_class_object(
                    project
                    .get_pymodule(cls.file_resource_at(project, path))
                    .get_attributes()[facade.name]
                    .get_object(),
                    "component publication owner",
                )
                if namespace is not facade:
                    holder = cls.require_class_object(
                        holder.get_attributes()[namespace.name].get_object(),
                        "component namespace publication owner",
                    )
                if not (
                    cls.py_class(holder)
                    and FlextInfraUtilitiesFacadeComponents.facade_composes_class(
                        holder, source_project=project
                    )
                ):
                    continue
                ancestors = cls._protocol_ancestor_objects(bases)
                providers: set[p.Infra.RopeClassObject] = set()
                for member in namespace.body:
                    alias = cls._namespace_class_alias(member, generated=True)
                    if alias is None:
                        continue
                    binding = cls.resolve_symbol(scope, alias[1])
                    if binding is None or not cls.py_class(
                        target := binding.get_object()
                    ):
                        continue
                    if target not in ancestors or not cls.utility_behavior_provider(
                        project, target
                    ):
                        continue
                    if not cls._component_methods_are_composed(holder, target):
                        message = (
                            f"composed provider callable differs: {path}:{alias[0]}"
                        )
                        raise ValueError(message)
                    publications[holder, alias[0]] = target
                    providers.add(target)
                if providers:
                    updates[path] = cls._remove_namespace_class_shadows(
                        source,
                        (namespace, scope),
                        bases,
                        family="utility",
                        composed_providers=frozenset(providers),
                    )
            FlextInfraUtilitiesFacadeComponents.assert_provider_publications_closed(
                project, publications
            )
        return tuple(
            staged[path].model_copy(
                update={"desired_content": source.encode(c.DEFAULT_ENCODING)}
            )
            for path, source in updates.items()
        )

    @classmethod
    def _component_methods_are_composed(
        cls,
        holder: p.Infra.RopeClassObject,
        provider: p.Infra.RopeClassObject,
    ) -> bool:
        """Prove every public provider function keeps its exact effective identity.

        Returns:
            Whether composition preserves the provider's complete callable API.

        """
        return all(
            name.startswith("_")
            or not cls.py_function(value := attribute.get_object())
            or (
                (effective := holder.get_attributes().get(name)) is not None
                and effective.get_object() is value
            )
            for name, attribute in provider.get_attributes().items()
        )

    @staticmethod
    def _component_selection_error(
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
        final: m.Infra.CodegenFilePlan | None,
    ) -> str | None:
        """Validate that a selected facade retains its declared destination.

        Returns:
            The selection diagnostic, or no error for a valid destination.

        """
        if selection is None or selection[1] is None:
            return None
        if final is None:
            return f"selected facade has no source owner: {selection}"
        if final.path != selection[0]:
            return f"component selection changed facade destination: {final.path}"
        return None

    @classmethod
    def _component_selected_domains(
        cls,
        root: Path,
        snapshot: p.Infra.WorkspaceSnapshot,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        *,
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[t.VariadicTuple[t.Triple[Path, Path, c.Infra.FacadeFamily]]]:
        """Inventory domains and validate selection in the shared source view.

        Returns:
            The selected domains or the unchanged selection failure diagnostic.

        """
        result_type = r[t.VariadicTuple[t.Triple[Path, Path, c.Infra.FacadeFamily]]]
        owned = cls.workspace_python_files(snapshot, root, project=binding[0])
        domains = cls._component_domains(
            root, {path: binding[1][path] for path in owned}
        )
        if selection is not None:
            destination, family = selection
            if family is None:
                if (
                    not destination.is_relative_to(root)
                    or destination.name != c.Infra.INIT_PY
                    or destination not in binding[1]
                ):
                    return result_type.fail(
                        f"component selection has no declared package: {selection}"
                    )
                return result_type.ok(
                    tuple(
                        domain
                        for domain in domains
                        if domain[1].is_relative_to(destination.parent)
                    )
                )
            if (
                not destination.is_relative_to(root)
                or destination not in binding[1]
                or FlextInfraUtilitiesRopeModulePatch.facade_letter_names_at(
                    binding[0], destination
                )
                != frozenset({family.value})
            ):
                return result_type.fail(
                    f"component selection has no declared facade family: {selection}"
                )
            family_root = destination.parent / cls.facade_families()[family].directory
            domains = tuple(
                domain
                for domain in domains
                if domain[0] == family_root and domain[2] is family
            )
        return result_type.ok(domains)

    @classmethod
    def _component_root_families(
        cls,
        root: Path,
        snapshot: p.Infra.WorkspaceSnapshot,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        *,
        selection: t.Pair[Path, c.Infra.FacadeFamily | None] | None,
    ) -> t.VariadicTuple[t.Pair[Path, c.Infra.FacadeFamily]]:
        """Inventory root families from the same epoch-bound source view.

        Returns:
            The selected root family or all declared package families in order.

        """
        if selection is not None and selection[1] is not None:
            return ((selection[0].parent, selection[1]),)
        project, sources = binding
        layout = cls.layout(root, rope_project=project)
        packages = {
            path.parent
            for path in cls.workspace_python_files(snapshot, root, project=project)
            if path.suffix == c.Infra.EXT_PYTHON
            and path.parent / c.Infra.INIT_PY in sources
        }
        if layout is not None and layout.class_stem:
            packages.add(layout.package_dir)
        return tuple(
            (package, c.Infra.FacadeFamily(declared_family.letter))
            for declared_family in cls.facade_families().values()
            for package in sorted(packages)
            if selection is None or package.is_relative_to(selection[0].parent)
            if (layout is not None and package == layout.package_dir)
            or cls.facade_module_path(
                package,
                c.Infra.FacadeFamily(declared_family.letter),
                project=project,
                sources=sources,
            )
            is not None
        )

    @classmethod
    def _component_root_facade(
        cls,
        root: Path,
        package: Path,
        family: c.Infra.FacadeFamily,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> m.Infra.CodegenFilePlan | None:
        """Plan one root family through its existing renderer and source witness.

        Returns:
            The root facade plan, or no plan when this package owns no family.

        Raises:
            ValueError: If Rendered.

        """
        path = cls.facade_module_path(package, family, project=project, sources=sources)
        if family is c.Infra.FacadeFamily.T:
            if path is None or not project.source_query(
                package / cls.facade_families()[family].directory,
                "isdir",
            ):
                return None
            rendered = cls.render_type_facade(package, path, sources, project=project)
        else:
            rendered = cls.render_utility_facade(
                package, family=family, project=project, sources=sources
            )
        if rendered is None:
            return None
        if path is None:
            message = f"Rendered {family} facade has no declaring module"
            raise ValueError(message)
        before = project.source_state(path, required=False)
        return m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=before,
            desired_content=rendered.encode(c.DEFAULT_ENCODING),
            desired_mode=(
                before.mode
                if before.mode is not None
                else config.Infra.codegen.modes.file_default
            ),
        )

    @classmethod
    def _component_domains(
        cls, root: Path, sources: t.MappingKV[Path, str]
    ) -> t.VariadicTuple[t.Triple[Path, Path, c.Infra.FacadeFamily]]:
        """Elect recursive private domains in deepest-first source order.

        Returns:
            Family roots, component directories and their declared families.

        """
        domains = {
            (family_root, directory, c.Infra.FacadeFamily(letter))
            for letter, family in (cls.facade_families().items())
            for path in sources
            for family_root in path.parents
            if family_root.is_relative_to(root) and family_root.name == family.directory
            for directory in path.parents
            if directory != family_root
            and directory.is_relative_to(family_root)
            and all(
                part.startswith("_")
                for part in directory.relative_to(family_root).parts
            )
        }
        return tuple(
            sorted(domains, key=lambda item: (-len(item[1].parts), item[1], item[2]))
        )

    @classmethod
    def _component_seed(
        cls,
        root: Path,
        domain: t.Triple[Path, Path, c.Infra.FacadeFamily],
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
        ownership_project: p.Infra.RopeProject,
    ) -> t.Pair[m.Infra.CodegenFilePlan, t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Elect observed ownership and move it through the current candidate.

        Pending initializers may already withhold a consumed parent export. They
        cannot revoke the input declaration's native public ownership before its
        coupled move and importer rewrites restore the complete interface.

        Returns:
            The seeded publication and any authenticated module-move plans.

        Raises:
            ValueError: If the destination exists without elected source ownership.

        """
        family_root, directory, family = domain
        moved: t.VariadicTuple[m.Infra.CodegenFilePlan] = ()
        with source_view(root, declared_files=tuple(staged.values())) as binding:
            project = binding[0]
            path, name = cls.family_subfacade_identity(
                directory, family_root, family=family, project=ownership_project
            )
            owner = cls.family_subfacade_source_owner(
                path, name, directory=directory, project=ownership_project
            )
            owner = cls._component_candidate_owner(
                project,
                (path, name),
                directory,
                observed_owner=owner,
                declared_files=staged,
            )
            if owner != path and project.source_query(path, "exists"):
                message = cls._component_destination_conflict(
                    project, (path, name), directory, owner
                )
                raise ValueError(message)
            if owner is None or owner == path:
                seed = cls._component_seed_file(root, (path, name), directory, binding)
                staged[path] = seed
                return seed, moved
            if owner is not None and owner != path:
                captured = {
                    source_path: project.source_text(source_path)
                    for resource in project.get_python_files()
                    for source_path in (Path(resource.real_path).resolve(),)
                }
                u.Cli.info(
                    "component owner move "
                    f"directory={directory} destination={path} "
                    f"owner={owner} captured={len(captured)} "
                    f"owner_captured={owner in captured} "
                    f"owner_resolved={owner.resolve() in captured}"
                )
                moved = cls.plan_module_move(
                    project,
                    owner,
                    destination_file=path,
                    inputs=cls.NativeSourceView(
                        captured,
                        tuple(
                            project.source_state(candidate, required=False)
                            for candidate in captured
                        ),
                        declared_files=tuple(staged.values()),
                    ),
                )
                staged.update((plan.path, plan) for plan in moved)
        with source_view(root, declared_files=tuple(staged.values())) as binding:
            seed = cls._component_seed_file(root, (path, name), directory, binding)
            staged[path] = seed
        return seed, moved

    @classmethod
    def _component_candidate_owner(
        cls,
        project: p.Infra.RopeProject,
        identity: t.Pair[Path, str],
        directory: Path,
        *,
        observed_owner: Path | None,
        declared_files: t.MappingKV[Path, m.Infra.CodegenFilePlan],
    ) -> Path | None:
        """Follow a recorded creation or move without discarding observed ownership.

        A move must retain its original retirement witness. Every prospective
        canonical owner still requires the same native composition election;
        a missing declaration, competing owner or unresolved class stays an error.

        Returns:
            The observed owner or its proven, recorded canonical successor.

        Raises:
            ValueError: A recorded destination has no matching native composition.

        """
        path, name = identity
        created = declared_files.get(path)
        if (
            created is None
            or created.before.content is not None
            or created.desired_content is None
        ):
            return observed_owner
        if observed_owner is not None and observed_owner != path:
            retired = declared_files.get(observed_owner)
            if (
                retired is None
                or retired.before.content is None
                or retired.desired_content is not None
            ):
                return observed_owner
        owner = cls.family_subfacade_source_owner(
            path, name, directory=directory, project=project
        )
        if owner != path:
            raise ValueError(
                cls._component_destination_conflict(
                    project, identity, directory, observed_owner
                )
            )
        return owner

    @classmethod
    def _component_destination_conflict(
        cls,
        project: p.Infra.RopeProject,
        identity: t.Pair[Path, str],
        directory: Path,
        owner: Path | None,
    ) -> str:
        """Describe the native evidence for an occupied publication destination.

        Returns:
            The original conflict diagnostic with source and export identities.

        """
        path, name = identity
        module = cls.require_semantic_module(
            project.get_pymodule(cls.file_resource_at(project, path))
        )
        source = project.source_text(path)
        exports = cls.public_export_names_source(source)
        matches = module.source_code == source if cls.source_module(module) else None
        evidence = cls._component_export_evidence(module, tuple(exports)[:8])
        return (
            f"Subfacade destination has unrelated ownership: {path}; "
            f"elected_class={name}; source_owner={owner}; "
            f"domain={directory}; project={project.root.real_path}; "
            f"module={module.get_name()}; "
            f"candidate_source_matches_native={matches}; "
            f"exports[{len(exports)}]={evidence}"
        )

    @classmethod
    def _component_export_evidence(
        cls,
        module: p.Infra.RopeSemanticModule,
        exports: t.VariadicTuple[str],
    ) -> list[str]:
        """Describe declaration provenance without reading consumer payload values.

        Returns:
            Native export, provider and superclass identities for the diagnostic.

        """
        evidence: list[str] = []
        for exported in exports:
            binding_name = module.get_attributes().get(exported)
            if binding_name is None or not cls.py_class(
                declaration := binding_name.get_object()
            ):
                evidence.append(f"{exported}: native_class=False")
                continue
            provider = declaration.get_module()
            resource = provider.get_resource()
            native_declaration = declaration.get_ast()
            lexical_base_count = (
                len(native_declaration.bases)
                if isinstance(native_declaration, ast.ClassDef)
                else None
            )
            bases = tuple(declaration.get_superclasses())
            origins = tuple(
                (
                    supplier.get_name(),
                    supplier.get_module().get_name(),
                    base_resource.real_path if base_resource is not None else None,
                )
                for supplier in bases[:8]
                if cls.py_class(supplier)
                for base_resource in (supplier.get_module().get_resource(),)
            )
            evidence.append(
                f"{exported}: class={declaration.get_name()} "
                f"module={provider.get_name()} "
                f"resource={resource.real_path if resource else None} "
                f"local_module={provider is module} "
                f"lexical_bases={lexical_base_count} "
                f"bases[{len(bases)}]={origins}"
            )
        return evidence

    @classmethod
    def _component_seed_file(
        cls,
        root: Path,
        identity: t.Pair[Path, str],
        directory: Path,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> m.Infra.CodegenFilePlan:
        """Seed one publication against its authentic physical before state.

        Returns:
            The candidate declaration with its original publication witness.

        """
        path, name = identity
        source = cls.family_subfacade_seed(
            path, name, directory=directory, sources=binding[1]
        )
        before = binding[0].source_state(path, required=False)
        return m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=before,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=(
                before.mode
                if before.mode is not None
                else config.Infra.codegen.modes.file_default
            ),
        )

    @classmethod
    def _component_render(
        cls,
        root: Path,
        domain: t.Triple[Path, Path, c.Infra.FacadeFamily],
        seed: m.Infra.CodegenFilePlan,
        staged: t.MappingKV[Path, m.Infra.CodegenFilePlan],
        *,
        source_view: p.Infra.SourceViewProvider,
    ) -> m.Infra.CodegenFilePlan:
        """Render the seed and child exports in the caller's exact candidate view.

        Returns:
            The final component plan retaining its original physical witness.

        """
        _, directory, family = domain
        with source_view(root, declared_files=tuple(staged.values())) as binding:
            rendered = cls.render_family_subfacade(
                directory,
                seed.path,
                family=family,
                project=binding[0],
                sources=binding[1],
            )
        return seed.model_copy(
            update={"desired_content": rendered.encode(c.DEFAULT_ENCODING)}
        )

    @classmethod
    def _render_explicit_class_facade(
        cls,
        pkg_dir: Path,
        source_entry: t.Pair[Path, str],
        *,
        family: c.Infra.FacadeFamily,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        owners_dir: Path | None = None,
    ) -> str:
        """Preserve authored class publications without inheriting their owners.

        Returns:
            Source retaining binding names and direct declaration imports.

        Raises:
            ValueError: If a facade base cannot be resolved or does not match any owner.

        """
        facade_path, source = source_entry
        project, contents = binding
        component = owners_dir is not None
        if owners_dir is None:
            owners_dir = (
                pkg_dir
                / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                    family
                ].directory
            )
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=contents, project=project
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations, sources
        )
        cls._explicit_class_facade(
            project, facade_path, source, declarations, binding=(sources, family)
        )
        scope, namespace, owners = cls._explicit_publication_scope(
            (project, sources), (facade_path, source), declarations
        )
        if not owners:
            return (
                cls._inherit_upstream_namespace(
                    project, facade_path, source, captured_sources=contents
                )
                if not component
                or family
                in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    source
                )
                else source
            )
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
        return (
            cls._inherit_upstream_namespace(
                project, facade_path, source, captured_sources=contents
            )
            if not component
            or family
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(source)
            else source
        )

    @classmethod
    def _explicit_publication_scope(
        cls,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[str, t.Pair[Path, str]]],
        source_entry: t.Pair[Path, str],
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> t.Triple[
        p.Infra.RopeScope,
        ast.ClassDef,
        t.VariadicTuple[p.Infra.RopeClassObject],
    ]:
        """Resolve authored publication aliases in their native lexical scope.

        Returns:
            The lexical scope, namespace and declared owners published there.

        """
        project, sources = binding
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
        return scope, namespace, owners

    @classmethod
    def _inherit_upstream_namespace(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        *,
        captured_sources: t.MappingKV[Path, str],
    ) -> str:
        """Compose upstream package letters and retain their inherited namespace.

        Elect the same-letter export by native class identity, not class spelling.
        A distinct occupied letter uses a lowercase package-qualified import alias;
        it never creates a second runtime facade or wrapper.
        Nested namespaces come from the outer base's declaration-time binding in
        this exact rendered source, never a later write to the exported letter.
        Every lookup shares the full captured cohort across import normalization.
        Its existing file inventory supplies the module map without another
        recursive discovery of the same native source view.

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
        package_name = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            path.parent,
            project_root=Path(project.root.real_path),
            source_project=project,
        )
        if not package_name:
            message = f"Facade has no captured publishing package: {path}"
            raise ValueError(message)
        consumer_module = f"{package_name}.{path.stem}"
        sources = cls._captured_publication_sources(project, captured_sources)
        if consumer_module in sources and sources[consumer_module][0] != path:
            message = f"Competing captured facade module: {consumer_module}"
            raise ValueError(message)
        sources[consumer_module] = (path, source)
        view = cls._UpstreamSourceView(project, sources)
        updated = cls._upstream_import_references(
            view, path, module, next(iter(letters))
        )
        if updated != source:
            source = updated
            sources = {**sources, consumer_module: (path, source)}
            view = cls._UpstreamSourceView(project, sources)
            module = FlextInfraUtilitiesRopeRuntime.build_string_module(
                project,
                source,
                resource=project.get_resource(
                    path.relative_to(Path(project.root.real_path)).as_posix()
                ),
            )
        facade, namespace = cls._facade_classes(ast.parse(source), path)
        if namespace is facade:
            return source
        bases = [ast.unparse(base) for base in namespace.bases]
        for base in facade.bases:
            binding = cls._declared_base_binding(view, module, (path, facade), base)
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

    @staticmethod
    def _captured_publication_sources(
        project: p.Infra.RopeProject,
        captured_sources: t.MappingKV[Path, str],
    ) -> t.MutableMappingKV[str, t.Pair[Path, str]]:
        """Index captured origins by their native publishing module identity.

        Returns:
            The captured cohort with competing module origins rejected.

        Raises:
            ValueError: If two captured paths declare the same module.

        """
        root = Path(project.root.real_path)
        sources: t.MutableMappingKV[str, t.Pair[Path, str]] = {}
        for source_path, captured_source in captured_sources.items():
            package_name = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                source_path.parent, project_root=root, source_project=project
            )
            if not package_name:
                continue
            module_name = (
                package_name
                if source_path.name == c.Infra.INIT_PY
                else f"{package_name}.{source_path.stem}"
            )
            if module_name in sources and sources[module_name][0] != source_path:
                message = f"Competing captured publication modules: {module_name}"
                raise ValueError(message)
            sources[module_name] = (source_path, captured_source)
        return sources

    @classmethod
    def _upstream_base_imports(
        cls,
        view: _UpstreamSourceView,
        path: Path,
        module: p.Infra.RopePyModule,
        letter: str,
        context: CodemodContext,
    ) -> Generator[
        tuple[
            tuple[str, p.Infra.RopePyObject, str],
            list[ast.Name],
            t.Triple[str, str, str | None],
        ]
    ]:
        """Resolve facade base imports through their publishing package identity.

        Yields:
            Native owners with authenticated public class names, lexical
            references and original import declarations. Header references retain
            their declaration-time environment across later family publication.

        Raises:
            ValueError: If a renamed base has no native references.

        """
        source = module.source_code
        facade = cls._facade_classes(ast.parse(source), path)[0]
        base_references = [
            node
            for base in facade.bases
            for node in ast.walk(base)
            if isinstance(node, ast.Name)
        ]
        base_names = {letter, *(node.id for node in base_references)}
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
                    view,
                    path,
                    origin,
                    alias.name,
                    letter,
                )
                if publication is None:
                    continue
                names = cls._upstream_reference_names(
                    view,
                    module,
                    (alias.asname or alias.name, publication[1]),
                    context,
                    header=(path, facade),
                )
                if not names and (alias.asname or alias.name) != letter:
                    message = (
                        "Unresolved native upstream base references: "
                        f"{path}:{alias.asname or alias.name}"
                    )
                    raise ValueError(message)
                if not names:
                    RemoveImportsVisitor.remove_unused_import(
                        context, origin, alias.name, alias.asname
                    )
                yield publication, names, (origin, alias.name, alias.asname)

    @classmethod
    def _upstream_import_references(
        cls,
        view: _UpstreamSourceView,
        path: Path,
        module: p.Infra.RopePyModule,
        letter: str,
    ) -> str:
        """Schedule upstream same-letter imports without capturing lexical bindings.

        Original Rope imports authorize cleanup requests. Rewrite references and
        add imports together, then let the native unused-import pass retain live
        bindings, exports and string annotations on the resulting source. Public
        owner identity is elected at module completion, while base references keep
        their declaration-time origin across the later local letter publication.
        Publication resolution shares the injected project's captured source view,
        including staged initializers; owned files never become external providers.
        A package-qualified name that captures another owner raises ValueError
        with the original collision-reference evidence attached.

        Returns:
            Source with identity-resolved references and public letter imports.

        """
        source = module.source_code
        references: dict[tuple[int, int], str] = {}
        context = CodemodContext(full_package_name=module.get_name().rpartition(".")[0])
        elected: dict[str, p.Infra.RopePyObject] = {}
        imports: set[t.Pair[str, str]] = set()
        removed_import = False
        for (
            publication,
            names,
            original_import,
        ) in cls._upstream_base_imports(view, path, module, letter, context):
            if not names:
                removed_import = True
                continue
            occupied = cls._upstream_letter_occupied(
                view,
                module,
                names,
                letter,
                (path, publication[1]),
            )
            occupied |= letter in elected and elected[letter] is not publication[1]
            destination = original_import[2] or (
                f"{publication[0].replace('.', '_').lower()}_{letter}"
                if occupied
                else letter
            )
            if occupied and (
                cls._upstream_letter_occupied(
                    view,
                    module,
                    names,
                    destination,
                    (path, publication[1]),
                )
            ):
                message = f"Occupied upstream facade import: {path}:{destination}"
                error = ValueError(message)
                error.add_note(
                    "Collision references: "
                    + repr([
                        (
                            node.id,
                            node.lineno,
                            node.col_offset,
                            cls._upstream_letter_occupied(
                                view,
                                module,
                                [node],
                                destination,
                                (path, publication[1]),
                            ),
                        )
                        for node in names
                    ])
                )
                raise error
            if destination == letter:
                elected[letter] = publication[1]
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
            cls._rewrite_upstream_references(context, source, references)
            if imports or removed_import
            else source
        )

    @classmethod
    def _upstream_reference_names(
        cls,
        view: _UpstreamSourceView,
        module: p.Infra.RopePyModule,
        binding: t.Pair[str, p.Infra.RopePyObject],
        context: CodemodContext,
        *,
        header: t.Pair[Path, ast.ClassDef],
    ) -> list[ast.Name]:
        """Resolve native references and schedule only their imported owners.

        Cleanup still requires the later native unused-import verdict, including
        string annotations and exports. Non-import bindings authorize no removal.
        Class-header names use the existing declaration-order binding owner so
        later publication of the local family letter cannot hide their origin.
        Header imports resolve through the same complete captured source cohort.

        Returns:
            Names whose lexical resolution retains the imported identity.

        Raises:
            ValueError: If an imported reference has no declared module origin.

        """
        source = module.source_code
        bound, owner = binding
        names: list[ast.Name] = []
        path, facade = header
        headers = {
            (node.lineno, node.col_offset): declaration
            for declaration in ast.walk(facade)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            for node in ast.walk(base)
            if isinstance(node, ast.Name)
        }
        for node in ast.walk(ast.parse(source)):
            if not (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == bound
            ):
                continue
            resolved = (
                cls._declared_facade_base_binding(
                    view,
                    module,
                    (path, headers[node.lineno, node.col_offset]),
                    (node, node, ()),
                )
                if (node.lineno, node.col_offset) in headers
                else FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    FlextInfraUtilitiesRopeRuntime.scope_at(
                        module,
                        FlextInfraUtilitiesRopeRuntime.source_offset(source, node),
                        declaration_line=node.lineno,
                    ),
                    node,
                )
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

    @classmethod
    def _upstream_letter_occupied(
        cls,
        view: _UpstreamSourceView,
        module: p.Infra.RopePyModule,
        names: t.SequenceOf[ast.Name],
        letter: str,
        binding: t.Pair[Path, p.Infra.RopePyObject],
    ) -> bool:
        """Preserve lexical collisions and the facade's own type-alias publication.

        Header slots use their captured declaration-time bindings, not an imported
        letter retained by Rope after the module publishes its own facade.
        Publication and collision checks retain the same captured source cohort.

        Returns:
            Whether replacing a reference would capture an occupied letter.

        """
        source = module.source_code
        facade, _ = cls._facade_classes(ast.parse(source), binding[0])
        headers = {
            (node.lineno, node.col_offset): declaration
            for declaration in ast.walk(facade)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            for node in ast.walk(base)
            if isinstance(node, ast.Name)
        }
        header_bindings = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
            m.Infra.SourceBindingInventoryRequest(
                project=view.project,
                module=module.get_name(),
                path=binding[0],
                source=source,
                required_line=facade.lineno,
            ),
            {},
            provider=module,
        )
        occupied = False
        for node in names:
            if (node.lineno, node.col_offset) in headers:
                candidate = ast.copy_location(ast.Name(id=letter, ctx=ast.Load()), node)
                enclosing = cls._enclosing_facade_base_binding(
                    module,
                    (binding[0], headers[node.lineno, node.col_offset]),
                    (candidate, candidate, ()),
                )
                if enclosing is not None:
                    occupied |= enclosing.get_object() is not binding[1]
                    continue
                if letter not in header_bindings:
                    continue
                reference = header_bindings[letter]
                if reference is None:
                    occupied = True
                    continue
                declared = view.resolve(reference)
                occupied |= declared.get_object() is not binding[1]
                continue
            lexical = FlextInfraUtilitiesRopeRuntime.scope_at(
                module,
                FlextInfraUtilitiesRopeRuntime.source_offset(source, node),
                declaration_line=node.lineno,
            )
            existing = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                lexical, ast.Name(id=letter, ctx=ast.Load())
            )
            occupied |= existing is not None and existing.get_object() is not binding[1]
        return occupied

    @staticmethod
    def _upstream_base_publication(
        view: _UpstreamSourceView,
        path: Path,
        origin: str,
        name: str,
        letter: str,
    ) -> tuple[str, p.Infra.RopePyObject, str] | None:
        """Resolve a base's same-letter publication by native class identity.

        Completed source declarations elect the exported owner, not Rope's stale
        imported-letter binding. The nominal export must retain the same identity,
        but composition imports the canonical upstream letter (ADR-028 decision 10).
        Admission requires a class belonging to a foreign publishing package.
        Owner, letter, nominal and export inventory use the same captured view.

        Returns:
            The publishing package, owner and authenticated public class name,
            or no same-letter publication.

        Raises:
            ValueError: If an origin, base or required nominal publication is invalid.

        """
        resource = view.project.find_module(origin)
        if resource is None:
            message = f"Unresolved facade import origin: {origin}"
            raise ValueError(message)
        binding = view.resolve(
            m.Infra.SourceClassReference(
                target=origin, attributes=(name,), qualified_base=f"{origin}.{name}"
            ),
        )
        owner = binding.get_object()
        publisher = origin
        package = resource
        if not package.is_folder():
            publisher = publisher.rpartition(".")[0]
            package = view.project.find_module(publisher)
        if package is None:
            message = f"Facade base has no publishing package: {origin}"
            raise ValueError(message)
        package_module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            view.project, package
        )
        public_exports = (
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                view.source(package_module)
            )
        )
        exported = (
            view.resolve(
                m.Infra.SourceClassReference(
                    target=publisher,
                    attributes=(letter,),
                    qualified_base=f"{publisher}.{letter}",
                ),
            )
            if letter in public_exports
            else None
        )
        if exported is None or exported.get_object() is not owner:
            if FlextInfraUtilitiesRopeRuntime.py_class(owner):
                declaring = owner.get_module()
                declared_exports = (
                    FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                        view.source(declaring)
                    )
                )
                if letter in declared_exports:
                    declared = view.resolve(
                        m.Infra.SourceClassReference(
                            target=declaring.get_name(),
                            attributes=(letter,),
                            qualified_base=f"{declaring.get_name()}.{letter}",
                        ),
                    )
                else:
                    declared = None
                if declared is not None and declared.get_object() is owner:
                    message = (
                        "Upstream facade letter is not published by its "
                        f"package: {publisher}:{letter}"
                    )
                    raise ValueError(message)
            return None
        if (
            Path(package.real_path).resolve() == path.parent.resolve()
            or not FlextInfraUtilitiesRopeRuntime.py_class(owner)
        ):
            message = (
                "Facade base requires a foreign published class: "
                f"{path}:{publisher}:{letter}"
            )
            raise ValueError(message)
        class_name = owner.get_name()
        nominal = (
            view.resolve(
                m.Infra.SourceClassReference(
                    target=publisher,
                    attributes=(class_name,),
                    qualified_base=f"{publisher}.{class_name}",
                ),
            )
            if class_name in public_exports
            else None
        )
        if nominal is None or nominal.get_object() is not owner:
            message = (
                "Upstream facade class is not published by its "
                f"package: {publisher}:{class_name}"
            )
            failure = ValueError(message)
            failure.add_note(
                f"facade={path}; import={origin}.{name}; letter={letter}; "
                f"selected={owner.get_module().get_name()}:{class_name}; "
                "captured_sources="
                f"{
                    tuple(
                        (module, str(captured[0]))
                        for module, captured in view.sources.items()
                        if module == publisher or module.startswith(f'{publisher}.')
                    )
                }"
            )
            raise failure
        return publisher, owner, class_name

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
        exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            updated.code
        )
        rebound = {
            name
            for name in exports
            if FlextInfraUtilitiesRopeModulePatch.runtime_alias_bindings(
                updated.code, alias=name
            )
        }
        # These exports publish local assignments, not the superseded imports.
        unpublished = FlextInfraUtilitiesRopeModulePatch.rewrite_all_declaration(
            updated.code, names=[name for name in exports if name not in rebound]
        )
        cleaned = (
            RemoveImportsVisitor(context)
            .transform_module(parse_module(unpublished))
            .code
        )
        return FlextInfraUtilitiesRopeModulePatch.rewrite_all_declaration(
            cleaned, names=list(exports)
        )

    @classmethod
    def _generated_facade(
        cls,
        pkg_dir: Path,
        source: str,
        *,
        family: c.Infra.FacadeFamily,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        owners_dir: Path | None = None,
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
        project, contents = binding
        if owners_dir is None:
            owners_dir = (
                pkg_dir
                / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                    family
                ].directory
            )
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=contents, project=project
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations, sources
        )
        source = cls._wrap_facade_imports(
            cls._merged_facade_imports(cls._canonical_exports(source))
        )
        context = CodemodContext()
        RemoveImportsVisitor.remove_unused_import(
            context, c.Infra.TYPING_GUARD_MODULE, c.Infra.TYPING_GUARD_NAME
        )
        rewritten = RemoveImportsVisitor(context).transform_module(parse_module(source))
        source = rewritten.code
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
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=binding[1], project=binding[0]
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations, sources
        )
        sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
        owners, _ = cls._facade_protocol_owners(
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                c.Infra.FacadeFamily.P
            ].directory,
            binding[1],
            project=binding[0],
        )
        facade, namespace, scope, typing_objects, base_objects, markers = (
            cls._facade_namespace_context(
                cls._UpstreamSourceView(binding[0], sources), source, facade_path
            )
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
                source, (namespace, scope), base_objects, family="protocol"
            )
        source = cls._insert_protocol_imports(source, additions, package=package_name)
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
        view: _UpstreamSourceView,
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
        project = view.project
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
        next(
            child
            for child in scope.get_scopes()
            if child.get_start() == namespace.lineno
        )
        base_objects = tuple(
            FlextInfraUtilitiesRopeRuntime.require_class_object(
                cls._declared_base_binding(
                    view,
                    module,
                    (facade_path, namespace),
                    base,
                ).get_object(),
                f"facade base: {facade_path}:{ast.unparse(base)}",
            )
            for base in namespace.bases
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
        namespace_binding: t.Pair[ast.ClassDef, p.Infra.RopeScope],
        base_objects: tuple[p.Infra.RopePyObject, ...],
        *,
        family: Literal["protocol", "model", "utility"],
        composed_providers: frozenset[p.Infra.RopeClassObject] = frozenset(),
    ) -> str:
        """Keep declared owners authoritative over their generated class bindings.

        Entity and stateful-helper publications retain their native declarations.
        A stateless method-provider publication may also retire after exact MRO
        coverage and the complete callable consumer cohort have been proved by
        the composition owner. Being a base alone never establishes that proof.

        Returns:
            Source without derived class bindings or proven redundant assignments.

        Raises:
            ValueError: If an authored contract assignment is unresolved or ambiguous.

        """
        generated = source.startswith(c.Infra.AUTOGEN_HEADER)
        aliases = [
            (member, alias)
            for member in namespace_binding[0].body
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
            name, expression, _ = alias
            shadowed = (
                generated
                and name in inherited
                and FlextInfraUtilitiesRopeRuntime.abstract_class(inherited[name])
            )
            value = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                namespace_binding[1], expression
            )
            target = value.get_object() if value is not None else None
            if generated and family == "utility" and target in composed_providers:
                shadows.append(member)
                continue
            inherited_class = (
                target is not None
                and FlextInfraUtilitiesRopeRuntime.abstract_class(target)
                and name in inherited
                and FlextInfraUtilitiesRopeRuntime.abstract_class(inherited[name])
            )
            retired_member = cls._namespace_member_is_retired(
                namespace_binding[1], expression, owners
            )
            shadowed = shadowed or retired_member
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
            target = cls._namespace_class_annotation_target(
                namespace_binding[1], alias, value, family=family
            )
            if target is None:
                continue
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
    def _namespace_member_is_retired(
        scope: p.Infra.RopeScope,
        expression: ast.expr,
        owners: t.SequenceOf[p.Infra.RopePyObject],
    ) -> bool:
        """Recognize a removed member only on its exact inherited native owner.

        Returns:
            Whether the publication names a member absent from that owner.

        """
        if not isinstance(expression, ast.Attribute):
            return False
        resolved = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
            scope, expression.value
        )
        return (
            resolved is not None
            and resolved.get_object() in owners
            and expression.attr not in resolved.get_object().get_attributes()
        )

    @staticmethod
    def _namespace_class_annotation_target(
        scope: p.Infra.RopeScope,
        alias: t.Triple[str, ast.expr, ast.expr | None],
        value: p.Infra.RopePyName | None,
        *,
        family: Literal["protocol", "model", "utility"],
    ) -> p.Infra.RopeClassObject | None:
        """Authenticate a class publication against its native annotation identity.

        Returns:
            The identical native class, or no class for an unannotated unresolved
            binding or a non-class value.

        Raises:
            ValueError: An annotation is unresolved or identifies another object.

        """
        name, _, annotation = alias
        resolved = (
            FlextInfraUtilitiesRopeRuntime.resolve_symbol(scope, annotation)
            if annotation is not None
            else value
        )
        if value is None or resolved is None:
            if annotation is not None:
                message = f"Unresolved {family} class attribute: {name}"
                raise ValueError(message)
            return None
        target = value.get_object()
        if not FlextInfraUtilitiesRopeRuntime.abstract_class(target):
            return None
        if target is not resolved.get_object():
            message = (
                f"ambiguous {family} class attribute {name}: "
                "annotation does not identify the declared contract"
            )
            raise ValueError(message)
        return target

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
        source_entry: t.Pair[Path, str],
        *,
        family: c.Infra.FacadeFamily,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
        owners_dir: Path | None = None,
    ) -> str:
        """Compose explicitly exported declarations without reverse family imports.

        An MRO-authenticated public composition retains its provider declarations;
        its class publications do not turn the holder into an assignment facade.

        Returns:
            A facade whose direct owners preserve the existing source C3 order.

        """
        facade_path, source = source_entry
        component_owners = owners_dir
        if owners_dir is None:
            owners_dir = (
                pkg_dir
                / FlextInfraUtilitiesCodegenNamespace.facade_families()[
                    family
                ].directory
            )
        sources, declarations, package_name = cls._declared_sources(
            pkg_dir, owners_dir, contents=binding[1], project=binding[0]
        )
        source = cls._rebind_declared_imports(
            package_name, owners_dir, source, declarations, sources
        )
        sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
        if cls._explicit_class_facade(
            binding[0], facade_path, source, declarations, binding=(sources, family)
        ):
            return cls._render_explicit_class_facade(
                pkg_dir,
                (facade_path, source),
                family=family,
                binding=binding,
                owners_dir=component_owners,
            )
        facade, namespace = cls._facade_classes(
            ast.parse(source, filename=str(facade_path)),
            facade_path,
        )
        view = cls._UpstreamSourceView(binding[0], sources)
        retired = cls._retired_owned_bases(
            view,
            (pkg_dir, owners_dir),
            (facade_path, namespace),
            {item.qualified_base for item in declarations},
        )
        if retired:
            source, context = cls._retired_facade_projection(
                package_name, source, namespace, retired
            )
            sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
            view = cls._UpstreamSourceView(binding[0], sources)
            facade, namespace = cls._facade_classes(
                ast.parse(source, filename=str(facade_path)),
                facade_path,
            )
        else:
            context = CodemodContext(full_package_name=package_name)
        if family in {
            c.Infra.FacadeFamily.C,
            c.Infra.FacadeFamily.M,
            c.Infra.FacadeFamily.U,
        }:
            declarations = cls._namespace_component_declarations(
                view,
                (facade_path, source),
                declarations,
                family=family,
            )
        contract = cls._declared_facade_contract(
            cls._independent_publishers(
                pkg_dir, owners_dir, sources, package_name=package_name
            ),
            declarations,
            (facade, namespace),
            composed=(
                namespace is facade
                and cls.py_class(
                    owner := binding[0]
                    .get_pymodule(cls.file_resource_at(binding[0], facade_path))
                    .get_attributes()[facade.name]
                    .get_object()
                )
                and FlextInfraUtilitiesFacadeComponents.facade_composes_class(
                    owner, source_project=binding[0]
                )
            ),
            source_bases=cls._declared_namespace_bases(
                m.Infra.SourceBindingInventoryRequest(
                    project=binding[0],
                    module=f"{package_name}.{facade_path.stem}",
                    path=facade_path,
                    source=source,
                    required_line=namespace.lineno,
                ),
                (facade, namespace),
            ),
        )
        contract = (
            cls._direct_domain_declarations(view, contract[0]),
            contract[1],
            contract[2],
        )
        source = cls._reorder_declared_facade(
            context,
            source,
            namespace,
            contract,
            ordering=(
                view.resolve.class_order(contract[0]),
                bool(retired),
            ),
        )
        if family in {c.Infra.FacadeFamily.M, c.Infra.FacadeFamily.U}:
            sources[f"{package_name}.{facade_path.stem}"] = (facade_path, source)
            source = cls._remove_rendered_namespace_class_shadows(
                binding[0],
                source,
                facade_path,
                family="model" if family is c.Infra.FacadeFamily.M else "utility",
                sources=sources,
            )
        source = cls._collapse_inherited_owner_references(
            binding[0], facade_path, source
        )
        return cls._wrap_facade_imports(source)

    @staticmethod
    def _declared_namespace_bases(
        request: m.Infra.SourceBindingInventoryRequest,
        classes: t.Pair[ast.ClassDef, ast.ClassDef],
    ) -> t.VariadicTuple[m.Infra.SourceClassReference]:
        """Read a facade namespace's ordered bases through its source inventory.

        Returns:
            The ordered references of the actual facade namespace declaration.

        Raises:
            ValueError: The facade or its namespace is not a class declaration.

        """
        facade, namespace = classes
        definitions: dict[str, m.Infra.SourceClassDefinition] = {}
        declaration = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
            request, definitions
        )[facade.name]
        if declaration is None:
            message = f"Non-class facade declaration: {request.path}:{facade.name}"
            raise ValueError(message)
        owner = definitions[declaration.target]
        if namespace is not facade:
            declaration = owner.members[namespace.name]
            if declaration is None:
                message = f"Non-class facade namespace: {request.path}:{namespace.name}"
                raise ValueError(message)
            owner = definitions[declaration.target]
        return owner.bases

    @staticmethod
    def _direct_domain_declarations(
        view: _UpstreamSourceView,
        declarations: list[m.Infra.SourceClassReference],
    ) -> list[m.Infra.SourceClassReference]:
        """Keep maximal native owners rather than their already composed ancestors.

        Returns:
            Direct domain owners; duplicate native identities remain an error.

        """
        reachable = view.resolve.class_reaches(declarations, declarations)
        return [
            item
            for index, item in enumerate(declarations)
            if not any(
                item.qualified_base in ancestors
                and declarations[other].qualified_base not in reachable[index]
                for other, ancestors in enumerate(reachable)
                if other != index
            )
        ]

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
        cls._declared_facade_stale_imports(
            context, source, set(existing) - set(ordered)
        )
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
            cls._UpstreamSourceView(
                project,
                {
                    name: (path, source) if path == facade_path else (path, text)
                    for name, (path, text) in sources.items()
                },
            ),
            (facade_path, source),
            declarations,
            family=family,
        )

    @classmethod
    def _namespace_component_declarations(
        cls,
        view: _UpstreamSourceView,
        source_entry: t.Pair[Path, str],
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        *,
        family: c.Infra.FacadeFamily = c.Infra.FacadeFamily.M,
    ) -> list[m.Infra.SourceClassReference]:
        """Elect namespace providers independently of whole class publications.

        Model publications never compose the namespace. Mixed constants retain
        plain owners as both named publications and namespace providers, but never
        inherit enum declarations. Direct native static or class methods admit
        utility composition without introducing new effective instance methods;
        meaningful methodless subfacades retain exported, locally owned native MROs;
        methods already inherited under the same name and native identity remain
        valid. This proves neither statelessness nor retirement of publications.
        A native ``typing.ClassVar`` binding declares class metadata rather than
        an instance descriptor; resolve that identity at the annotation's owner.

        Returns:
            The declared plain namespace providers.

        Raises:
            ValueError: If descriptors coexist with an undeclared stateful role.

        """
        project = view.project
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
        inherited_bases = (
            cls._facade_namespace_context(
                view,
                source,
                facade_path,
            )[4]
            if family is c.Infra.FacadeFamily.U
            else ()
        )
        components: list[m.Infra.SourceClassReference] = []
        has_unpublished = False
        for declaration, owner in zip(
            declarations,
            cls._declared_facade_owners(project, declarations, view.sources),
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
                if not methods and not cls._meaningful_utility_subfacade(
                    view, declaration, owner
                ):
                    continue
                if not methods <= {"classmethod", "staticmethod"}:
                    continue
                if any(
                    FlextInfraUtilitiesRopeRuntime.py_function(
                        value := attribute.get_object()
                    )
                    and value.get_kind() not in {"classmethod", "staticmethod"}
                    and (
                        (
                            inherited := next(
                                (
                                    base.get_attributes()[name]
                                    for base in inherited_bases
                                    if name in base.get_attributes()
                                ),
                                None,
                            )
                        )
                        is None
                        or inherited.get_object() is not value
                    )
                    for name, attribute in owner.get_attributes().items()
                ):
                    continue
                if not cls.utility_namespace_declaration(project, owner):
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

    @classmethod
    def _meaningful_utility_subfacade(
        cls,
        view: _UpstreamSourceView,
        declaration: m.Infra.SourceClassReference,
        owner: p.Infra.RopeSourceClass,
    ) -> bool:
        """Prove a methodless wrapper composes exported, locally owned behavior.

        Returns:
            Whether native MRO and source exports establish a nonempty domain owner.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        path = view.sources[declaration.target][0]
        bases = owner.get_superclasses()
        return (
            bool(bases)
            and any(
                runtime.py_function(attribute.get_object())
                for attribute in owner.get_attributes().values()
            )
            and all(cls._utility_domain_base(view, path, base) for base in bases)
        )

    @classmethod
    def _utility_domain_base(
        cls,
        view: _UpstreamSourceView,
        path: Path,
        base: p.Infra.RopePyObject,
    ) -> bool:
        """Authenticate an exported local base and its inherited storage contract.

        Returns:
            Whether this native class is an owned utility namespace provider.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        if not runtime.py_class(base):
            return False
        module = base.get_module()
        resource = module.get_resource()
        captured = view.sources.get(module.get_name())
        if resource is None or captured is None:
            return False
        origin = Path(resource.real_path)
        return (
            captured[0] == origin
            and (
                origin.parent == path.parent
                or (
                    origin.parent.parent == path.parent
                    and origin.parent.name.startswith("_")
                )
            )
            and base.get_name()
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                captured[1]
            )
            and all(
                not runtime.py_class(ancestor)
                or cls.utility_namespace_declaration(view.project, ancestor)
                for ancestor in (
                    FlextInfraUtilitiesDeclarationPayload.class_ancestry(base)
                )
            )
        )

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
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> str:
        """Resolve the rendered namespace before removing inherited shadows.

        Returns:
            The facade source without redundant inherited class declarations.

        Raises:
            TypeError: An inherited owner is not a native class object.

        """
        _, namespace, scope, _, base_objects, _ = cls._facade_namespace_context(
            cls._UpstreamSourceView(project, sources), source, facade_path
        )
        try:
            return cls._remove_namespace_class_shadows(
                source, (namespace, scope), base_objects, family=family
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
        facades: t.Pair[ast.ClassDef, ast.ClassDef],
        *,
        composed: bool,
        source_bases: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> tuple[list[m.Infra.SourceClassReference], set[str], bool]:
        """Filter declared owners, then append the namespace's own base owners.

        An owner whose nested class the namespace already composes as a base
        (``Owner.Namespace``) contributes through that nested class only, never
        additionally as a whole owner. Existing bases retain their declaration-time
        identities, not later module aliases that may name this facade itself.
        A holder already composed by a public namespace is not replaced by its
        own member publications; its providers form the same declaration's MRO.

        Returns:
            The final declarations, their qualified names, and whether the
            facade binds the namespace through assignment.

        """
        facade, namespace = facades
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
        bound_namespace = (
            not composed
            and namespace is facade
            and any(
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
        )
        if bound_namespace:
            filtered.clear()
        filtered.extend(
            m.Infra.SourceClassReference(
                target=reference.target,
                attributes=reference.attributes,
                qualified_base=ast.unparse(base),
            )
            for base, reference in zip(
                namespace.bases, source_bases[: len(namespace.bases)], strict=True
            )
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
                    if (alias.asname or alias.name) in declared_names:
                        RemoveImportsVisitor.remove_unused_import(
                            context,
                            node.module,
                            alias.name,
                            alias.asname,
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

    @classmethod
    def _retired_owned_bases(
        cls,
        view: _UpstreamSourceView,
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
        facade_path = facade[0]
        candidates = tuple(
            base
            for base in facade[1].bases
            if cls._base_name(base) not in declared_names
        )
        if not candidates:
            return frozenset()
        project = view.project
        contents = dict(view.sources.values())
        projection_is_autogen = contents[facade_path].startswith(c.Infra.AUTOGEN_HEADER)
        barrel_state = project.source_state(roots[1] / c.Infra.INIT_PY, required=False)
        barrel = (
            None
            if barrel_state.content is None
            else barrel_state.content.decode(c.DEFAULT_ENCODING)
        )
        pymodule = FlextInfraUtilitiesRopeRuntime.build_string_module(
            project,
            contents[facade_path],
            resource=project.get_resource(
                facade_path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
        )
        retired: set[str] = set()
        for base in candidates:
            expression = base.value if isinstance(base, ast.Subscript) else base
            imported: p.Infra.RopePyName | None = None
            if isinstance(expression, ast.Name):
                imported = FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                    pymodule
                    .get_source_binding_index()
                    .context_at(
                        FlextInfraUtilitiesRopeRuntime.source_offset(
                            pymodule.source_code, expression
                        )
                    )
                    .environment,
                    expression,
                )
            if (
                projection_is_autogen
                and imported is not None
                and cls._departed_projected_binding(
                    project,
                    imported,
                    roots[1],
                    barrel,
                    declared_names=declared_names,
                )
            ):
                retired.add(ast.unparse(base))
                continue
            binding = cls._declared_base_binding(view, pymodule, facade, base)
            holder = binding.get_definition_location()[0]
            provider = holder.get_resource() if holder is not None else None
            if provider is None:
                if projection_is_autogen and (
                    cls._departed_projected_binding(
                        project,
                        binding,
                        roots[1],
                        barrel,
                        declared_names=declared_names,
                    )
                ):
                    retired.add(ast.unparse(base))
                else:
                    cls._require_facade_base_owner(
                        project,
                        binding,
                        facade_path,
                        ast.unparse(base),
                    )
                continue
            path = Path(provider.real_path).resolve()
            if (
                cls._retired_family_provider(
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

    @classmethod
    def _declared_base_binding(
        cls,
        view: _UpstreamSourceView,
        pymodule: p.Infra.RopePyModule,
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
        binding = cls._declared_facade_base_binding(
            view, pymodule, facade, (base, head, attributes)
        )
        if FlextInfraUtilitiesRopeRuntime.semantic_module(binding.get_object()):
            message = f"Module used as a class base: {ast.unparse(base)}"
            raise ValueError(message)
        if not FlextInfraUtilitiesRopeRuntime.abstract_class(binding.get_object()):
            message = f"Non-class facade base origin: {facade[0]}:{ast.unparse(base)}"
            raise ValueError(message)
        return binding

    @classmethod
    def _declared_facade_base_binding(
        cls,
        view: _UpstreamSourceView,
        pymodule: p.Infra.RopePyModule,
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
            (name, text)
            for name, (path, text) in view.sources.items()
            if path == facade[0]
        )
        binding = cls._enclosing_facade_base_binding(pymodule, facade, reference)
        if binding is not None:
            return binding
        definitions: dict[str, m.Infra.SourceClassDefinition] = {}
        visible = FlextInfraUtilitiesRopeSourceBasesInventory.inventory(
            m.Infra.SourceBindingInventoryRequest(
                project=view.project,
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
            return view.resolve(
                m.Infra.SourceClassReference(
                    target=origin.target,
                    attributes=(*origin.attributes, *reference[2]),
                    qualified_base=".".join((
                        origin.target,
                        *origin.attributes,
                        *reference[2],
                    )),
                ),
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

        A later class-local declaration does not shadow the module at this header.

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
        if declaring is not pymodule or line is None:
            message = (
                f"Unproven preceding facade base: {facade[0]}:"
                f"{ast.unparse(reference[0])}"
            )
            raise ValueError(message)
        if line >= facade[1].lineno:
            return None
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

    @classmethod
    def _require_facade_base_owner(
        cls,
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
        ) or cls._upstream_binding(project, project, binding):
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

    @classmethod
    def _rebind_declared_imports(
        cls,
        package_name: str,
        owners_dir: Path,
        source: str,
        declarations: t.SequenceOf[m.Infra.SourceClassReference],
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> str:
        """Import declared owners from their nearest publishing package.

        Declarations elect exports; the existing joint initializer plan publishes
        them. A nested domain owns its own members, so each imported owner binds
        from its declaring module's immediate package, never a concrete leaf and
        never an ancestor that stopped flattening descendants.

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
        declaring, packaged = cls._declared_owner_publications(sources)
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
                owner = declaring.get(alias.name)
                target = cls._declared_import_target(owner, packaged)
                if module == prefix and target is not None and target != prefix:
                    source = cls._relocated_import_source(
                        source, package_name, (module, alias.name), target
                    )
                    continue
                if alias.name not in owners or module == prefix:
                    continue
                source = cls._relocated_import_source(
                    source, package_name, (module, alias.name), prefix
                )
        return source

    @staticmethod
    def _declared_owner_publications(
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> t.Pair[dict[str, str], set[str]]:
        """Map every public export to its nearest declaring package.

        A nested domain owns its own members, so each exported owner binds
        from its declaring module's immediate package; initializer modules
        mark their own packages as packaged publishers.

        Returns:
            The owner-to-module map and the packaged module set.

        """
        declaring: dict[str, str] = {}
        packaged: set[str] = set()
        for module, (path, content) in sources.items():
            if path.name == c.Infra.INIT_PY:
                packaged.add(module)
            for (
                name
            ) in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                content
            ):
                previous = declaring.get(name)
                if previous is None or module.count(".") >= previous.count("."):
                    declaring[name] = module
        return declaring, packaged

    @staticmethod
    def _declared_import_target(
        owner: str | None,
        packaged: t.Container[str],
    ) -> str | None:
        """Resolve the publishing binding for one declared owner import.

        Returns:
            The owner binding when packaged, its parent package, or no target.

        """
        if owner is None:
            return None
        return owner if owner in packaged else owner.rpartition(".")[0]

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
        declarations = cls._elect_declared_owner_names(project, declarations, sources)
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

    @classmethod
    def _elect_declared_owner_names(
        cls,
        project: p.Infra.RopeProject,
        declarations: list[m.Infra.SourceClassReference],
        sources: t.MappingKV[str, t.Pair[Path, str]],
    ) -> list[m.Infra.SourceClassReference]:
        """Keep native descendants when multiple modules publish the same name.

        Returns:
            Declarations retaining every incomparable publisher for ambiguity checks.

        """
        grouped: dict[str, list[m.Infra.SourceClassReference]] = {}
        for declaration in declarations:
            grouped.setdefault(declaration.qualified_base, []).append(declaration)
        return [
            items[index]
            for items in grouped.values()
            for index in (
                cls._maximal_native_owner_indices(
                    cls._declared_facade_owners(project, items, sources)
                )
                if len(items) > 1
                else (0,)
            )
        ]

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
                    pymodule.get_scope().get_names().get(family),
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
                    FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                        cls._receiver_scope(pymodule, receiver), receiver
                    ),
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
        imported_binding: p.Infra.RopePyName | None,
        receiver: ast.Name,
        *,
        owned: t.VariadicTuple[Path],
        resolved: t.MutableMappingKV[p.Infra.RopeImportedModule, Path],
    ) -> bool:
        """Check an original native binding for the owned facade import.

        Returns:
            True when Rope resolves the receiver to its own letter imported
            from the package, its initializer, or the facade module itself.

        """
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
                    name for base in node.bases if (name := cls._base_name(base))
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
