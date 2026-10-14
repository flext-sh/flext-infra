"""Census-derived constant consumer cutover across declared workspace members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import libcst as cst
from flext_cli import cli
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
)


class FlextInfraUtilitiesSemanticConstantConsumers(
    FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Derive constant paths from declarations and rewrite proven bindings."""

    @classmethod
    def _plan_constant_consumers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose constant declaration repairs with their consumer cutover.

        Returns:
            The complete edits against the original immutable source inventory.
        """
        declarations = cls._constant_declarations(rope_workspace, sources)
        working = dict(sources)
        working.update({edit.file_path: edit.updated_source for edit in declarations})
        consumers = cls._plan_constant_imports(rope_workspace, working)
        if consumers.failure:
            return consumers
        working.update({
            edit.file_path: edit.updated_source for edit in consumers.value
        })
        changes = {
            edit.file_path: edit.changes for edit in (*declarations, *consumers.value)
        }
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=source,
                updated_source=working[path],
                changes=changes[path],
            )
            for path, source in sources.items()
            if source != working[path]
        ))

    @classmethod
    def _constant_declarations(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Repair typing.Final in constants class suites by Rope identity.

        A module Final retains its contract. A class constant must be a
        ClassVar so a composed Pydantic namespace never turns it into a field.
        Aliased typing imports resolve through the lexical Rope scope; a
        same-spelled user type is not a typing qualifier.

        Returns:
            Syntax-preserving declaration edits within the constants family.
        """
        candidates = tuple(
            (path, source)
            for path, source in cls._editable_sources(sources)
            if "Final" in source
            and workspace.convention(path).module_policy.expected_alias == "c"
        )
        if not candidates:
            return ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        project = runtime.snapshot_project(workspace.rope_project, sources)
        try:
            return tuple(
                edit
                for path, source in candidates
                if (
                    edit := cls._constant_annotation_edit(project, path, source)
                ) is not None
            )
        finally:
            project.close()

    @classmethod
    def _constant_annotation_edit(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
    ) -> m.Infra.SemanticMigrationEdit | None:
        """Plan one module's identity-proven Final-to-ClassVar repair.

        Returns:
            The source edit, or None when no class declaration needs repair.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        module = project.get_pymodule(resource)
        final = project.get_module("typing").get_attribute("Final")
        classvar = project.get_module("typing").get_attribute("ClassVar")
        evaluate = runtime.runtime_callable("rope.base.evaluate", "eval_str")
        wrapper = MetadataWrapper(cst.parse_module(source))
        positions = wrapper.resolve(PositionProvider)
        offsets = [0]
        for line in source.splitlines(keepends=True):
            offsets.append(offsets[-1] + len(line))

        class Rewrite(cst.CSTTransformer):
            """Rewrite only proven typing qualifiers in constants class suites."""

            depth: int = 0
            functions: int = 0
            changes: int = 0

            def visit_ClassDef(self, node: cst.ClassDef) -> None:
                self.depth += 1

            def leave_ClassDef(
                self, original_node: cst.ClassDef, updated_node: cst.ClassDef
            ) -> cst.ClassDef:
                self.depth -= 1
                return updated_node

            def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
                self.functions += 1

            def leave_FunctionDef(
                self,
                original_node: cst.FunctionDef,
                updated_node: cst.FunctionDef,
            ) -> cst.FunctionDef:
                self.functions -= 1
                return updated_node

            def leave_AnnAssign(
                self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
            ) -> cst.AnnAssign:
                annotation = original_node.annotation.annotation
                if (
                    not self.depth
                    or self.functions
                    or not isinstance(annotation, cst.Subscript)
                ):
                    return updated_node
                position = positions[annotation.value].start
                scope = runtime.scope_at(
                    module, offsets[position.line - 1] + position.column
                )
                binding = evaluate(
                    scope, wrapper.module.code_for_node(annotation.value)
                )
                if not runtime.same_name(final, binding):
                    return updated_node
                existing = scope.lookup("ClassVar")
                if existing is not None and not runtime.same_name(classvar, existing):
                    message = f"constant ClassVar binding is shadowed in {path}"
                    raise ValueError(message)
                self.changes += 1
                return updated_node.with_changes(
                    annotation=updated_node.annotation.with_changes(
                        annotation=annotation.with_changes(value=cst.Name("ClassVar"))
                    )
                )

        rewrite = Rewrite()
        updated = wrapper.module.visit(rewrite)
        if not rewrite.changes:
            return None
        context = CodemodContext()
        AddImportsVisitor.add_needed_import(context, "typing", "ClassVar")
        updated = AddImportsVisitor(context).transform_module(updated)
        return m.Infra.SemanticMigrationEdit(
            file_path=path,
            original_source=source,
            updated_source=updated.code,
            changes=(f"typing.Final class constants -> ClassVar: {rewrite.changes}",),
        )

    @classmethod
    def _plan_constant_imports(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve every imported constants owner once for the complete census.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        cli.display_text(f"census: resolve constants imports in {len(sources)} modules")
        imports = tuple(
            node
            for path, source in cls._editable_sources(sources)
            for node in ast.walk(ast.parse(source, filename=str(path)))
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
            and not node.level
        )
        if not any(
            imported.name not in c.Infra.ALIAS_NAMES
            or (imported.name == "c" and imported.asname is not None)
            for node in imports
            for imported in node.names
        ):
            # Canonical non-constant facade letters and unrenamed c require no
            # constant-owner cutover; their identities are already explicit.
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        statements = tuple(ast.unparse(node) for node in imports)
        modules = facade_owner.source_modules(sources, statements)
        cli.display_text(f"census: indexed {len(modules)} source identities")
        discovered = facade_owner.discover(modules)
        owners = {
            package: tuple(owner for owner in declarations if owner[1] == "c")
            for package, declarations in discovered.items()
        }
        bindings, _exports = facade_owner.declared_exports(modules)
        cli.display_text(f"census: indexed {len(bindings)} declared bindings")
        ancestry = FlextInfraUtilitiesPrivateImportAncestry
        bases = ancestry.FlextInfraUtilitiesPrivateImportAncestry.class_bases(
            modules,
        )
        references: t.MutableMappingKV[t.Pair[str, str], str | None] = {}
        cli.display_text(f"census: indexed {len(bases)} class declarations")
        family_modules = frozenset(
            name
            for declarations in owners.values()
            for _tree, _alias, _root, file_name in declarations
            for name in (Path(file_name).stem, f"_{Path(file_name).stem}")
        )
        constant_names = frozenset((
            "c",
            *(
                root_name
                for declarations in owners.values()
                for _tree, _alias, root_name, _file_name in declarations
            ),
            *(
                identity.rsplit(".", 1)[-1]
                for identity in bases
                if family_modules.intersection(identity.split("."))
            ),
        ))

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            if (
                path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
                and (path.parent / c.Infra.CONSTANTS_PY).is_file()
            ):
                return source, ()
            # Declaration parts compose c; importing that still-assembling
            # facade inside its own parts is a dependency cycle.
            if family_modules.intersection(
                path.relative_to(rope_workspace.repository_root).parts
            ):
                return source, ()
            if not any(
                imported.name in constant_names
                and not (imported.name == "c" and imported.asname is None)
                for node in ast.walk(ast.parse(source, filename=str(path)))
                if isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
                for imported in node.names
            ):
                return source, ()
            return cls._rewrite_constant_consumer(
                path,
                source,
                rope_workspace,
                (owners, bindings, bases),
                references,
            )

        return cls._semantic_edits(cls._editable_sources(sources), rewrite)

    @classmethod
    def _rewrite_constant_consumer(
        cls,
        path: Path,
        source: str,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        index: t.Infra.ConstantFacadeIndex,
        references: t.MutableMappingKV[t.Pair[str, str], str | None],
    ) -> t.Infra.TransformResult:
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        convention = rope_workspace.convention(path)
        policy = convention.module_policy
        if policy.expected_alias == "c" or policy.expected_family == "Constants":
            return source, ()
        layout = convention.project_layout
        if layout is None:
            return source, ()
        tree = ast.parse(source, filename=str(path))
        package = cls._constant_facade_package(tree, layout.package_name, path)
        context = (tree, package, index, references)
        removals, replacements = cls._constant_replacement_state(context)
        if not replacements:
            return source, ()
        facade_owner.require_unshadowed_alias(
            tree,
            package,
            "c",
            path,
            removals,
        )
        plan = m.Infra.PrivateImportRewritePlan(
            removals={module: frozenset(names) for module, names in removals.items()},
            obsolete_imports={},
            replacements=replacements,
            public_imports={"c": package},
        )
        updated = cls._rewrite_private_import_source(
            source,
            plan,
            runtime_public_imports=frozenset({"c"}),
        )
        return updated, tuple(
            f"constant consumer {identity} -> {reference}"
            for identity, reference in sorted(replacements.items())
        )

    @classmethod
    def _constant_replacement_state(
        cls,
        context: t.Infra.ConstantConsumerContext,
    ) -> t.Pair[
        t.MutableMappingKV[str, set[str]],
        t.MutableStrMapping,
    ]:
        tree, package, index, references = context
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        owners, bindings, bases = index
        removals: t.MutableMappingKV[str, set[str]] = {}
        replacements: t.MutableStrMapping = {}
        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.ImportFrom)
                or not node.module
                or node.level
                or not node.module.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
            ):
                continue
            for imported in node.names:
                if imported.name == "c" and imported.asname is None:
                    continue
                local_name = imported.asname or imported.name
                if cls._is_composition_base(tree, local_name):
                    continue
                qualified = f"{node.module}.{imported.name}"
                key = package, qualified
                if key not in references:
                    references[key] = facade_owner.public_reference(
                        owners=owners.get(package, ()),
                        package=package,
                        qualified=qualified,
                        bindings=bindings,
                        class_bases=bases,
                    )
                reference = references[key]
                if reference is None:
                    continue
                removals.setdefault(node.module, set()).add(imported.name)
                replacements[qualified] = reference
        return removals, replacements

    @staticmethod
    def _is_composition_base(tree: ast.AST, local_name: str) -> bool:
        return any(
            isinstance(base, ast.Name) and base.id == local_name
            for declaration in ast.walk(tree)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
        )

    @staticmethod
    def _constant_facade_package(
        tree: ast.Module,
        declared_package: str,
        path: Path,
    ) -> str:
        """Select the existing c binding, or the module's declared facade.

        Returns:
            The resolved constants facade package name.

        Raises:
            ValueError: If multiple constants facades are bound as ``c``.

        """
        public_packages = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and not node.level
            and any(item.name == "c" and item.asname is None for item in node.names)
        }
        if len(public_packages) > 1:
            msg = f"multiple constants facades bound as c in {path}"
            raise ValueError(msg)
        return next(iter(public_packages), declared_package)


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantConsumers"]
