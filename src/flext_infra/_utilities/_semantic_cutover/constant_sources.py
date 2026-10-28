"""Native constant declaration providers, independent of consumer orchestration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._rope.rope_structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesSemanticConstantSources:
    """Prove constant providers through native source and declaration identities."""

    @classmethod
    def _constant_derives_from(
        cls,
        project: p.Infra.RopeProject,
        candidate: p.Infra.RopePyName,
        qualified: str,
    ) -> bool:
        """Resolve a member's declaring ancestry through native class identity.

        Returns:
            Whether the native declaring class has the requested ancestor.

        Raises:
            TypeError: The declaration has no native source module.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = cls._constant_terminal(project, candidate, "enum member")
        module, line = binding.get_definition_location()
        if module is None or line is None:
            return False
        module = module.get_module()
        if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
            message = "Constant declarations require a native source module"
            raise TypeError(message)
        owner = runtime.scope_at(module, module.lines.get_line_start(line)).pyobject
        return runtime.qualified_name(project, qualified).get_object() in (
            FlextInfraUtilitiesDeclarationPayload.class_ancestry(owner)
        )

    @classmethod
    def _constant_declaration_bindings(
        cls,
        project: p.Infra.RopeProject,
        public: t.MappingKV[str, p.Infra.RopePyName],
    ) -> t.MappingKV[
        Path,
        t.Pair[p.Infra.RopePyModule, list[t.Pair[p.Infra.RopePyName, int]]],
    ]:
        """Group unique assignments by their native module and definition line.

        Returns:
            Native modules with their unique assignment bindings and lines.

        Raises:
            TypeError: A declaration has no native source module.

        """
        declarations: t.MutableMappingKV[
            Path,
            t.Pair[
                p.Infra.RopePyModule,
                list[t.Pair[p.Infra.RopePyName, int]],
            ],
        ] = {}
        for reference, candidate in public.items():
            binding = cls._constant_terminal(project, candidate, reference)
            if (
                not FlextInfraUtilitiesTypesRopeRuntime.assigned_name(binding)
                or len(binding.assignments) != 1
            ):
                continue
            module, line = binding.get_definition_location()
            if module is None or line is None:
                continue
            module = module.get_module()
            if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
                message = "Constant bindings require a native source module"
                raise TypeError(message)
            resource = module.get_resource()
            if resource is None:
                continue
            declarations.setdefault(Path(resource.real_path), (module, []))[1].append((
                binding,
                line,
            ))
        return declarations

    @classmethod
    def _binding_statement_matches(
        cls,
        module: p.Infra.RopeParsedModule,
        statement: m.Infra.LogicalStatement,
        binding: p.Infra.RopePyName,
        line: int,
    ) -> bool:
        """Match class assignment targets by native identity and definition line.

        Returns:
            Whether the statement declares the selected native binding.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        structure = FlextInfraUtilitiesRopeStructure
        if (
            statement.line != line
            or statement.enclosing_kind != c.Infra.RopeScopeKind.CLASS
            or statement.category
            not in {
                c.Infra.StatementCategory.ASSIGN,
                c.Infra.StatementCategory.ANN_ASSIGN,
            }
        ):
            return False
        target = structure.target_name(statement)
        return bool(target) and runtime.same_name(
            binding,
            runtime.expression_name(
                runtime.scope_at(module, statement.start_offset), target
            ),
        )

    @classmethod
    def _literal_constant_patterns(
        cls,
        project: p.Infra.RopeProject,
        public: t.MappingKV[str, p.Infra.RopePyName],
        *,
        literal_type: str = "__builtin__.str",
        frozen: bool = False,
    ) -> tuple[t.Pair[str, str], ...]:
        """Prove exact literal boundaries, decimal tokens and native constructors.

        Returns:
            Literal source expressions and their unique public references.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        structure = FlextInfraUtilitiesRopeStructure
        found: list[t.Pair[str, str]] = []
        arguments = dict[str, str]()
        if frozen:
            arguments["frozen"] = "name=__builtin__.frozenset"
        declarations = cls._constant_declaration_bindings(project, public)
        for path, (module, bindings) in declarations.items():
            source = module.source_code
            literal_regions = {
                (start, end)
                for start, end, metadata in refactors.ignored_regions(source)
                for prefix in (metadata.get("prefix"),)
                if prefix is None or "f" not in prefix.casefold()
            }
            statements = structure.logical_statements(source)
            for binding, line in bindings:
                for statement in statements:
                    if not cls._binding_statement_matches(
                        module, statement, binding, line
                    ):
                        continue
                    for start, end in refactors.semantic_regions(
                        module,
                        "${literal}",
                        arguments={"literal": f"type={literal_type}"},
                        start=statement.start_offset,
                        end=statement.end_offset,
                    ):
                        literal = source[start:end]
                        if (
                            literal_type == "__builtin__.str"
                            and (start, end) not in literal_regions
                        ) or (
                            literal_type == "__builtin__.int"
                            and not literal.isdecimal()
                        ):
                            continue
                        expression = (
                            f"${{frozen}}({{{literal}}})" if frozen else literal
                        )
                        pattern = (
                            f"${{target}}: ${{annotation}} = {expression}"
                            if statement.category
                            == c.Infra.StatementCategory.ANN_ASSIGN
                            else f"${{target}} = {expression}"
                        )
                        if not refactors.semantic_regions(
                            module,
                            pattern,
                            arguments=arguments,
                            start=statement.start_offset,
                            end=statement.end_offset,
                        ):
                            continue
                        canonical = cls._constant_reference(public, binding, path)
                        if canonical is not None:
                            found.append((expression, canonical))
        return tuple(found)

    @classmethod
    def _constant_terminal(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        qualified: str,
    ) -> p.Infra.RopePyName:
        """Prove import provenance, rejecting cycles, ambiguity and missing targets.

        Returns:
            The native declaration at the end of the import chain.

        Raises:
            ValueError: Import provenance is cyclic, ambiguous or unresolved.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        visited: set[t.Pair[Path, str]] = set()
        while isinstance(binding, p.Infra.RopeImportedName):
            resource = runtime.imported_module_resource(project, binding)
            path = Path(resource.real_path).resolve()
            key = path, binding.imported_name
            if key in visited:
                message = f"cyclic constant import chain: {qualified}"
                raise ValueError(message)
            visited.add(key)
            module = cls._constant_import_module(project, resource, qualified)
            imports = runtime.module_imports_for_pymodule(project, module)
            declarations = sum(
                alias == binding.imported_name
                or (alias is None and name == binding.imported_name)
                for statement in imports.imports
                for name, alias in statement.import_info.names_and_aliases
            )
            if declarations > 1:
                message = f"ambiguous constant import chain: {qualified}"
                raise ValueError(message)
            if binding.imported_name == "c" and module.source_code.startswith(
                c.Infra.AUTOGEN_HEADER
            ):
                owner = module.get_resource()
                if owner is None:
                    message = f"generated constants package has no source: {qualified}"
                    raise ValueError(message)
                declaration = owner.parent.get_child(c.Infra.CONSTANTS_PY)
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
                        declaration, declaration.path
                    ),
                )
            terminal = module.get_attributes().get(binding.imported_name)
            if terminal is None:
                message = f"unresolved constant import chain: {qualified}"
                raise ValueError(message)
            binding = terminal
        return binding

    @staticmethod
    def _constant_import_module(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        qualified: str,
    ) -> p.Infra.RopePyModule:
        """Inspect package declarations natively without evaluating their targets.

        Returns:
            The native source module declaring the import's bindings.

        Raises:
            TypeError: A package has no native folder resource.
            ValueError: A package has no source initializer.

        """
        if resource.is_folder():
            if not isinstance(resource, p.Infra.RopeRoot):
                message = f"constant import has no package resource: {qualified}"
                raise TypeError(message)
            if not resource.has_child(c.Infra.INIT_PY):
                message = f"constant import has no package declarations: {qualified}"
                raise ValueError(message)
            resource = resource.get_child(c.Infra.INIT_PY)
        return FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
                resource, qualified
            ),
        )

    @classmethod
    def _constant_reference(
        cls,
        paths: t.MappingKV[str, p.Infra.RopePyName],
        binding: p.Infra.RopePyName,
        path: Path,
    ) -> str | None:
        """Elect a unique published identity or proven class ancestry owner.

        Returns:
            The unique published reference, or no constant publication.

        Raises:
            ValueError: Several published owners have the same native identity.

        """
        references = tuple(
            reference
            for reference, candidate in paths.items()
            if cls._constant_owner_binding(candidate, binding)
        )
        if not references:
            return None
        if len(references) != 1:
            message = f"constant has ambiguous public owners in {path}: {references}"
            raise ValueError(message)
        return references[0]

    @classmethod
    def _constant_public_paths(
        cls,
        project: p.Infra.RopeProject,
        package: str,
    ) -> t.MappingKV[str, p.Infra.RopePyName]:
        """Enumerate native public facade members without importing the target.

        Returns:
            Public reference paths bound to their native declaration identities.

        """
        module = FlextInfraUtilitiesTypesRopeRuntime.require_semantic_module(
            project.get_module(f"{package}.{Path(c.Infra.CONSTANTS_PY).stem}")
        )
        facade = module.get_attributes().get("c")
        if facade is None:
            return {}
        found: t.MutableMappingKV[str, p.Infra.RopePyName] = {"c": facade}
        pending: t.MutableSequenceOf[
            t.Triple[str, p.Infra.RopePyObject, tuple[p.Infra.RopePyObject], ...]
        ] = [("c", facade.get_object(), ())]
        while pending:
            prefix, owner, ancestors = pending.pop()
            if owner in ancestors:
                continue
            if not FlextInfraUtilitiesTypesRopeRuntime.abstract_class(owner):
                continue
            for name, binding in owner.get_attributes().items():
                if name.startswith("_"):
                    continue
                reference = f"{prefix}.{name}"
                found[reference] = binding
                value = binding.get_object()
                if FlextInfraUtilitiesTypesRopeRuntime.abstract_class(value):
                    pending.append((reference, value, (*ancestors, owner)))
        return found

    @staticmethod
    def _constant_owner_binding(
        candidate: p.Infra.RopePyName, binding: p.Infra.RopePyName
    ) -> bool:
        """Prove a published identity or a native class ancestry owner.

        Returns:
            Whether publication directly names or inherits the native owner.

        """
        return FlextInfraUtilitiesRopeRuntimeModules.same_name(candidate, binding) or (
            FlextInfraUtilitiesTypesRopeRuntime.abstract_class(binding.get_object())
            and binding.get_object()
            in FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                candidate.get_object()
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantSources"]
