"""Rope-only object inventory helpers for workspace-wide census.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from json import dumps
from operator import itemgetter
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope_inventory_sites import (
    FlextInfraUtilitiesRopeInventorySitesMixin,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesRopeInventory(FlextInfraUtilitiesRopeInventorySitesMixin):
    """Generic Rope-only inventory helpers for Python objects."""

    @classmethod
    def objects(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        include_local_scopes: bool,
        include_references: bool = True,
    ) -> t.VariadicTuple[m.Infra.Object]:
        """Return all same-file defined objects for one workspace module.

        Returns:
            All same-file defined objects for one workspace module.

        Raises:
            ValueError: If path is outside the active rope workspace.

        """
        rope_project = rope_workspace.rope_project
        resource = rope_workspace.resource(file_path)
        if resource is None:
            msg = f"path is outside the active rope workspace: {file_path}"
            raise ValueError(msg)
        module_entry = rope_workspace.module(file_path)
        convention = rope_workspace.convention(file_path)
        pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project,
            resource,
        )
        # The text the module snapshot was parsed from: names and offsets must
        # come from one snapshot even when the file changed on disk since.
        source = pymodule.source_code
        parameter_lines = cls._parameter_lines(rope_project, pymodule)
        constant_bindings = cls._constant_bindings(pymodule)
        items: t.MutableSequenceOf[m.Infra.Object] = []
        module_scope = pymodule.get_scope()
        child_scopes = tuple(module_scope.get_scopes())
        for name, pyname in cls._sorted_module_names(pymodule, resource):
            record_options = m.Infra.RopeInventoryRecordInput(
                rope_project=rope_project,
                resource=resource,
                source=source,
                parameter_lines=parameter_lines,
                constant_bindings=constant_bindings,
                name=name,
                pyname=pyname,
                module_name=module_entry.module_name
                if module_entry is not None
                else "",
                project_name=convention.project_layout.project_name
                if convention.project_layout is not None
                else convention.file_path.parent.name,
                convention=convention,
                scope_chain=(),
                class_chain=(),
                child_scope=cls._child_scope_for(child_scopes, pyname),
                rope_workspace=rope_workspace,
            )
            items.extend(
                cls._recorded_objects(
                    record_options,
                    child_scope=record_options.child_scope,
                    include_local_scopes=include_local_scopes,
                    include_references=include_references,
                ),
            )
        return tuple(items)

    @classmethod
    def _scope_objects(
        cls,
        scope: p.Infra.RopeScopeDsl,
        *,
        parent_options: m.Infra.RopeInventoryRecordInput,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> t.VariadicTuple[m.Infra.Object]:
        """Scope objects.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.Object]``.

        """
        items: t.MutableSequenceOf[m.Infra.Object] = []
        child_scopes = tuple(scope.get_scopes())
        for name, pyname in cls._sorted_scope_names(scope, parent_options.resource):
            child_scope = cls._child_scope_for(child_scopes, pyname)
            record_options = parent_options.model_copy(
                update={"name": name, "pyname": pyname, "child_scope": child_scope},
            )
            items.extend(
                cls._recorded_objects(
                    record_options,
                    child_scope=child_scope,
                    include_local_scopes=include_local_scopes,
                    include_references=include_references,
                ),
            )
        return tuple(items)

    @classmethod
    def _recorded_objects(
        cls,
        record_options: m.Infra.RopeInventoryRecordInput,
        *,
        child_scope: p.Infra.RopeScopeDsl | None,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> t.VariadicTuple[m.Infra.Object]:
        """Return one recorded object followed by the objects of its child scope.

        An input that produces no record contributes nothing.

        Returns:
            One recorded object followed by the objects of its child scope.

        """
        record = cls._record(record_options, include_references=include_references)
        if record is None:
            return ()
        return (
            record,
            *cls._child_scope_objects(
                record=record,
                child_scope=child_scope,
                record_options=record_options,
                include_local_scopes=include_local_scopes,
                include_references=include_references,
            ),
        )

    @classmethod
    def _child_scope_objects(
        cls,
        *,
        record: m.Infra.Object,
        child_scope: p.Infra.RopeScopeDsl | None,
        record_options: m.Infra.RopeInventoryRecordInput,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> t.VariadicTuple[m.Infra.Object]:
        """Include nested class declarations while respecting function-local scope.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.Object]``.

        """
        if (
            record.kind not in {"class", "function", "method"}
            or child_scope is None
            or (
                not include_local_scopes
                and child_scope.get_kind() != c.Infra.RopeScopeKind.CLASS
            )
        ):
            return ()
        return cls._scope_objects(
            scope=child_scope,
            parent_options=cls._descend_options(record_options, record),
            include_local_scopes=include_local_scopes,
            include_references=include_references,
        )

    @staticmethod
    def _descend_options(
        parent_options: m.Infra.RopeInventoryRecordInput,
        record: m.Infra.Object,
    ) -> m.Infra.RopeInventoryRecordInput:
        """Descend options.

        Returns:
            The resulting ``m.Infra.RopeInventoryRecordInput``.

        """
        result: m.Infra.RopeInventoryRecordInput = parent_options.model_copy(
            update={
                "scope_chain": tuple(
                    part for part in record.scope_path.split(".") if part
                ),
                "class_chain": tuple(
                    part for part in record.class_path.split(".") if part
                ),
            },
        )
        return result

    @staticmethod
    def _sorted_module_names(
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]:
        """Sorted module names.

        Returns:
            The resulting ``t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]``.

        """
        return FlextInfraUtilitiesRopeInventory._sorted_names(
            pymodule.get_attributes(),
            resource,
        )

    @staticmethod
    def _sorted_scope_names(
        scope: p.Infra.RopeScopeDsl,
        resource: t.Infra.RopeResource,
    ) -> t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]:
        """Sorted scope names.

        Returns:
            The resulting ``t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]``.

        """
        return FlextInfraUtilitiesRopeInventory._sorted_names(
            scope.get_names(),
            resource,
        )

    @staticmethod
    def _sorted_names(
        names: t.MappingKV[str, t.Infra.RopePyName],
        resource: t.Infra.RopeResource,
    ) -> t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]:
        """Sorted names.

        Returns:
            The resulting ``t.VariadicTuple[t.Pair[str, t.Infra.RopePyName]]``.

        """
        candidates: list[t.Triple[int, str, t.Infra.RopePyName]] = []
        for name, pyname in names.items():
            if FlextInfraUtilitiesRopeRuntime.imported_name(pyname):
                continue
            line = FlextInfraUtilitiesRopeInventory._definition_line(pyname, resource)
            if line is None:
                continue
            candidates.append((line, name, pyname))
        return tuple(
            (name, pyname) for _, name, pyname in sorted(candidates, key=itemgetter(0))
        )

    @classmethod
    def _record(
        cls,
        options: m.Infra.RopeInventoryRecordInput,
        *,
        include_references: bool,
    ) -> m.Infra.Object | None:
        """Record.

        Returns:
            The resulting ``m.Infra.Object | None``.

        """
        line = cls._definition_line(options.pyname, options.resource)
        if line is None:
            return None
        expected_alias = options.convention.module_policy.expected_alias or ""
        kind = (
            "assignment"
            if not options.scope_chain and options.name == expected_alias
            else cls._kind_for(
                options.pyname,
                class_chain=options.class_chain,
                scope_chain=options.scope_chain,
                name=options.name,
            )
        )
        if kind == "parameter" and options.name in {"self", "cls"}:
            return None
        if kind == "parameter":
            # Rope reports a parameter at its function's ``def`` line; in a
            # multi-line signature the identifier lives on its own line.
            line = options.parameter_lines[line, options.name]
        elif (line, options.name) in options.constant_bindings and (
            options.scope_chain or options.name != expected_alias
        ):
            kind = "constant"
        is_facade_member = cls._is_facade_member(
            options.convention,
            name=options.name,
            scope_chain=options.scope_chain,
        )
        all_reference_sites: t.VariadicTuple[m.Infra.ReferenceSite] = ()
        runtime_reference_sites: t.VariadicTuple[m.Infra.ReferenceSite] = ()
        script_reference_sites: t.VariadicTuple[m.Infra.ReferenceSite] = ()
        reference_evidence_collected = False
        if include_references:
            (
                runtime_reference_sites,
                script_reference_sites,
                all_reference_sites,
                reference_evidence_collected,
            ) = cls._reference_sites(options, line=line)
        if is_facade_member or options.name.startswith("_"):
            runtime_reference_sites = ()
            script_reference_sites = ()
        references_count = len(runtime_reference_sites) + len(script_reference_sites)
        scope_path = ".".join((*options.scope_chain, options.name))
        class_path = (
            ".".join((*options.class_chain, options.name))
            if kind == "class"
            else ".".join(options.class_chain)
        )
        return m.Infra.Object(
            name=options.name,
            kind=kind,
            file_path=str(options.convention.file_path),
            line=line,
            project=options.project_name,
            class_path=class_path,
            module_name=options.module_name,
            scope_path=scope_path,
            actual_tier=cls._actual_tier(options.convention),
            expected_tier=cls._expected_tier(options.convention, kind=kind),
            is_facade_member=is_facade_member,
            references_count=references_count,
            runtime_references_count=len(runtime_reference_sites),
            script_references_count=len(script_reference_sites),
            runtime_reference_sites=runtime_reference_sites,
            script_reference_sites=script_reference_sites,
            all_reference_sites=all_reference_sites,
            reference_evidence_collected=reference_evidence_collected,
            fingerprint=cls._fingerprint(
                options.source,
                name=options.name,
                line=line,
                child_scope=options.child_scope,
            ),
            payload_fingerprint=(
                cls._payload_fingerprint(options, scope_path) if kind == "class" else ""
            ),
        )

    @classmethod
    def _payload_fingerprint(
        cls,
        options: m.Infra.RopeInventoryRecordInput,
        qualified_name: str,
    ) -> str:
        """Describe native Pydantic candidates without asserting substitutability.

        Literal values, native scope depth, declared bases, generics, fields,
        config and complete validator/serializer bodies remain part of the
        diagnostic. Only the declaration identifier and proven external alias
        spellings are normalized. The implicit class/schema identity is
        deliberately not treated as permission to merge declarations.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If native payload declaration has no class identifier.

        """
        payloads = FlextInfraUtilitiesDeclarationPayload
        binding = payloads.payload_declaration(
            options.rope_project,
            Path(options.resource.real_path),
            qualified_name,
        )
        if binding is None or options.child_scope is None:
            return ""
        bases = tuple(
            cls._native_object_identity(base)
            for base in payloads.direct_bases(binding.get_object())
        )
        if any(not base for base in bases):
            return ""
        scope = options.child_scope
        module = options.rope_project.get_pymodule(options.resource)
        statements = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                options.source
            )
            if scope.get_start() <= statement.line <= scope.get_end()
        )
        if not statements:
            return ""
        header = statements[0]
        references = cls._payload_references(options, module, scope, statements)
        definition_offset = header.start_offset + header.indent
        definition_offset = options.source.find(
            options.name,
            definition_offset + len("class"),
            header.end_offset,
        )
        if definition_offset < 0:
            msg = "native payload declaration has no class identifier"
            raise ValueError(msg)
        references.append((
            definition_offset,
            definition_offset + len(options.name),
            "<payload>",
        ))
        shapes = tuple(
            (
                statement.indent - header.indent,
                cls._payload_statement_fingerprint(
                    statement.text,
                    statement.start_offset,
                    references,
                ),
            )
            for statement in statements
        )
        return dumps((bases, shapes), ensure_ascii=True, separators=(",", ":"))

    @classmethod
    def _payload_references(
        cls,
        options: m.Infra.RopeInventoryRecordInput,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScopeDsl,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> list[t.Triple[int, int, str]]:
        references: list[t.Triple[int, int, str]] = []
        for statement in statements:
            for (
                begin,
                end,
            ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(
                statement.text
            ):
                start = statement.start_offset + begin
                stop = statement.start_offset + end
                lexical = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                    module,
                    start,
                    declaration_line=(
                        statement.line
                        if statement.category
                        in {
                            c.Infra.StatementCategory.CLASS_DEF,
                            c.Infra.StatementCategory.FUNC_DEF,
                        }
                        else None
                    ),
                )
                value = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                    lexical,
                    options.source[start:stop],
                )
                if value is None:
                    continue
                supplier, definition_line = value.get_definition_location()
                if (
                    supplier is module
                    and definition_line is not None
                    and (scope.get_start() <= definition_line <= scope.get_end())
                ):
                    continue
                identity = cls._native_binding_identity(value)
                if identity:
                    references.append((start, stop, f"<native:{identity}>"))
        return references

    @staticmethod
    def _native_object_identity(value: p.Infra.RopePyObject) -> str:
        runtime = FlextInfraUtilitiesRopeRuntime
        if runtime.py_class(value) or runtime.py_function(value):
            module = value.get_module()
            scope = value.get_scope()
            if module is None or scope is None:
                return ""
            names: list[str] = []
            while scope.parent is not None:
                names.append(scope.pyobject.get_name())
                scope = scope.parent
            return f"{module.get_name()}::{'.'.join(reversed(names))}"
        if runtime.abstract_class(value) and isinstance(
            value, p.Infra.RopeBuiltinClass
        ):
            return f"{value.builtin.__module__}::{value.builtin.__qualname__}"
        return ""

    @classmethod
    def _native_binding_identity(cls, value: p.Infra.RopePyName) -> str:
        identity = cls._native_object_identity(value.get_object())
        if identity:
            return identity
        supplier, line = value.get_definition_location()
        if supplier is None or line is None:
            return ""
        return f"{supplier.get_name()}::line:{line}"

    @staticmethod
    def _payload_statement_fingerprint(
        source: str,
        offset: int,
        references: t.SequenceOf[t.Triple[int, int, str]],
    ) -> str:
        """Keep literal bytes separate from normalized executable whitespace.

        Args:
            source: The source code of the statement.
            offset: Starting character offset of the statement in its source.
            references: Start/end offsets and identities of referenced objects.

        Returns:
            The statement fingerprint, retaining literal bytes separately from
            normalized executable whitespace.

        """
        edits: list[t.Triple[int, int, str]] = []
        cursor = -1
        for begin, end, identity in sorted(
            references, key=lambda item: (item[0], -item[1])
        ):
            if offset <= begin < end <= offset + len(source) and begin >= cursor:
                edits.append((begin - offset, end - offset, identity))
                cursor = end
        pieces: list[str] = []
        previous = 0
        literals = FlextInfraUtilitiesRopeRuntime.ignored_regions(source)
        spans = [
            (begin, end, dumps(("literal", source[begin:end]), ensure_ascii=True))
            for begin, end, _metadata in literals
            if source[begin] != "#"
        ]
        for begin, end, replacement in sorted((*edits, *spans)):
            if begin < previous:
                continue
            pieces.extend((" ".join(source[previous:begin].split()), replacement))
            previous = end
        pieces.append(" ".join(source[previous:].split()))
        return " ".join(piece for piece in pieces if piece)

    @staticmethod
    def _constant_bindings(
        pymodule: t.Infra.RopePyModule,
    ) -> frozenset[t.Pair[int, str]]:
        """Recognize immutable declarations by typing identity, independent of case.

        Returns:
            Definition line and name pairs proven by native Rope matches.

        """
        bindings: set[t.Pair[int, str]] = set()
        for pattern in (
            "${constant}: ${immutable}[${contract}] = ${value}",
            "${constant}: ${immutable} = ${value}",
        ):
            for start, _ in FlextInfraUtilitiesRopeRuntime.semantic_regions(
                pymodule,
                pattern,
                arguments={"immutable": "name=typing.Final"},
            ):
                first, last = FlextInfraUtilitiesRopeRuntime.word_primary_range(
                    pymodule.source_code,
                    start,
                )
                bindings.add((
                    pymodule.lines.get_line_number(start),
                    pymodule.source_code[first:last],
                ))
        return frozenset(bindings)

    @staticmethod
    def _parameter_lines(
        rope_project: t.Infra.RopeProject,
        pymodule: t.Infra.RopePyModule,
    ) -> t.MappingKV[t.Pair[int, str], int]:
        """Index parameter positions once for one immutable module snapshot.

        Returns:
            Parameter lines keyed by function definition line and parameter name.

        Raises:
            ValueError: If a declared parameter has no native source occurrence.

        """
        positions: t.MutableMappingKV[t.Pair[int, str], int] = {}
        module_scope = pymodule.get_scope()
        scopes = list(module_scope.get_scopes())
        while scopes:
            scope = scopes.pop()
            scopes.extend(scope.get_scopes())
            for name, pyname in scope.get_names().items():
                if not FlextInfraUtilitiesRopeRuntime.parameter_name(pyname):
                    continue
                finder = FlextInfraUtilitiesRopeRuntime.create_occurrence_finder(
                    rope_project,
                    name,
                    pyname,
                    imports=False,
                    in_hierarchy=False,
                )
                declaration = next(
                    iter(finder.find_occurrences(pymodule=pymodule)), None
                )
                if declaration is None:
                    message = f"Rope parameter declaration has no occurrence: {name}"
                    raise ValueError(message)
                _, definition_line = pyname.get_definition_location()
                if definition_line is None:
                    message = f"Rope parameter has no definition line: {name}"
                    raise ValueError(message)
                positions[definition_line, name] = declaration.lineno
        return positions

    @staticmethod
    def _definition_line(
        pyname: t.Infra.RopePyName,
        resource: t.Infra.RopeResource,
    ) -> int | None:
        """Definition line.

        Returns:
            The resulting ``int | None``.

        """
        location = pyname.get_definition_location()
        module, line = location
        origin = module.get_resource() if module is not None else None
        if line is None or origin is None or origin.path != resource.path:
            return None
        result: int = line
        return result

    @staticmethod
    def _child_scope_for(
        scopes: t.SequenceOf[p.Infra.RopeScopeDsl],
        pyname: t.Infra.RopePyName,
    ) -> p.Infra.RopeScopeDsl | None:
        """Child scope for.

        Returns:
            The resulting ``p.Infra.RopeScopeDsl | None``.

        """
        location = pyname.get_definition_location()
        _, line = location
        if line is None:
            return None
        scope = next((scope for scope in scopes if scope.get_start() == line), None)
        if scope is not None:
            validated_existing_scope: p.Infra.RopeScopeDsl = scope
            return validated_existing_scope
        if FlextInfraUtilitiesRopeRuntime.assigned_name(
            pyname,
        ) or FlextInfraUtilitiesRopeRuntime.parameter_name(pyname):
            return None
        getter = getattr(pyname.get_object(), "get_scope", None)
        candidate = getter() if callable(getter) else None
        if not isinstance(candidate, p.Infra.RopeScopeDsl):
            return None
        validated_scope: p.Infra.RopeScopeDsl = candidate
        return validated_scope

    @staticmethod
    def _in_class_scope(
        class_chain: t.StrSequence,
        scope_chain: t.StrSequence,
    ) -> bool:
        """Report whether the binding depth matches a class attribute position.

        Returns:
            The resulting ``bool``.

        """
        return bool(class_chain) and len(scope_chain) == len(class_chain)

    @staticmethod
    def _scoped_binding_kind(name: str) -> str:
        """Return the kind of a name bound inside a nested scope.

        Returns:
            The resulting ``str``.

        """
        return "local" if not name.isupper() else "constant"

    @staticmethod
    def _assigned_kind(
        *,
        class_chain: t.StrSequence,
        scope_chain: t.StrSequence,
        name: str,
    ) -> str:
        """Kind of a name Rope reports as assigned or bound as a parameter.

        Returns:
            The resulting ``str``.

        """
        if FlextInfraUtilitiesRopeInventory._in_class_scope(class_chain, scope_chain):
            # An UPPER name is a constant wherever it binds: the census owns
            # class-level constants too, not only module-level ones.
            return "constant" if name.isupper() else "attribute"
        if scope_chain:
            return FlextInfraUtilitiesRopeInventory._scoped_binding_kind(name)
        return "constant" if name.isupper() else "assignment"

    @staticmethod
    def _declared_kind(
        pyname: t.Infra.RopePyName,
        *,
        class_chain: t.StrSequence,
        scope_chain: t.StrSequence,
        name: str,
    ) -> str:
        """Kind of a name bound by a declaration instead of an assignment.

        Returns:
            The resulting ``str``.

        """
        obj = pyname.get_object()
        if FlextInfraUtilitiesRopeRuntime.abstract_class(obj):
            return "class"
        if FlextInfraUtilitiesRopeRuntime.py_function(obj):
            member = FlextInfraUtilitiesRopeInventory._in_class_scope(
                class_chain,
                scope_chain,
            )
            return "method" if member else "function"
        if FlextInfraUtilitiesRopeInventory._in_class_scope(class_chain, scope_chain):
            return "constant" if name.isupper() else "attribute"
        if scope_chain:
            return FlextInfraUtilitiesRopeInventory._scoped_binding_kind(name)
        if FlextInfraUtilitiesRopeRuntime.defined_name(pyname) and name.isupper():
            return "constant"
        return "assignment"

    @staticmethod
    def _kind_for(
        pyname: t.Infra.RopePyName,
        *,
        class_chain: t.StrSequence,
        scope_chain: t.StrSequence,
        name: str,
    ) -> str:
        """Kind for.

        Returns:
            The resulting ``str``.

        """
        if FlextInfraUtilitiesRopeRuntime.parameter_name(pyname):
            return "parameter"
        if FlextInfraUtilitiesRopeRuntime.assigned_name(pyname):
            return FlextInfraUtilitiesRopeInventory._assigned_kind(
                class_chain=class_chain,
                scope_chain=scope_chain,
                name=name,
            )
        return FlextInfraUtilitiesRopeInventory._declared_kind(
            pyname,
            class_chain=class_chain,
            scope_chain=scope_chain,
            name=name,
        )

    @staticmethod
    def _occurrence_search_resources(
        options: m.Infra.RopeInventoryRecordInput,
        definition_path: Path,
        name: str,
        *,
        all_surfaces: bool = False,
    ) -> t.VariadicTuple[t.Infra.RopeResource]:
        """Scope the occurrence search to the validated definition path.

        Returns:
            The resulting ``t.VariadicTuple[t.Infra.RopeResource]``.

        """
        if all_surfaces:
            return FlextInfraUtilitiesRopeImports.indexed_surface_search_resources(
                options.rope_workspace,
                resource=options.resource,
                name=name,
                definition_path=definition_path,
            )
        module_name = options.module_name
        dependent_import_targets = (
            (module_name, f"{module_name}.{name}")
            if module_name
            and FlextInfraUtilitiesRopeInventory._reference_surface(definition_path)
            != c.Infra.DEFAULT_SRC_DIR
            else ()
        )
        return FlextInfraUtilitiesRopeImports.indexed_search_resources(
            options.rope_workspace,
            resource=options.resource,
            name=name,
            definition_path=definition_path,
            dependent_import_targets=dependent_import_targets,
        )

    @staticmethod
    def _new_deduped_site(
        site: m.Infra.ReferenceSite,
        seen_sites: set[t.Triple[str, int, str]],
    ) -> bool:
        """Whether one site is new and outside ``__init__`` re-exports.

        Returns:
            The resulting ``bool``.

        """
        if Path(site.file_path).name == c.Infra.INIT_PY:
            return False
        site_key = (site.file_path, site.line, site.surface)
        if site_key in seen_sites:
            return False
        seen_sites.add(site_key)
        return True

    @staticmethod
    def _classified_occurrence_sites(
        hits: t.SequenceOf[t.Infra.RopeLocation],
        *,
        definition_path: Path | None,
        line: int,
        offset: int,
        reachability_paths: frozenset[str] | None,
    ) -> tuple[
        list[m.Infra.ReferenceSite],
        list[m.Infra.ReferenceSite],
        list[m.Infra.ReferenceSite],
        bool,
    ]:
        """Retain exact all-surface evidence separately from reachability sites.

        Returns:
            Runtime sites, script sites, all-surface sites, definition skipped.

        Raises:
            RuntimeError: If an occurrence lacks an absolute path or valid offset.

        """
        runtime_reference_sites: list[m.Infra.ReferenceSite] = []
        script_reference_sites: list[m.Infra.ReferenceSite] = []
        all_reference_sites: list[m.Infra.ReferenceSite] = []
        seen_sites: set[t.Triple[str, int, str]] = set()
        seen_occurrences: set[t.Pair[str, int]] = set()
        skipped_definition = False
        definition_key = (
            (
                FlextInfraUtilitiesRopeInventory._normalize_file_path(definition_path),
                offset,
            )
            if definition_path is not None
            else None
        )
        for hit in hits:
            reference_site = FlextInfraUtilitiesRopeInventory._reference_site(hit)
            occurrence_offset = getattr(hit, "offset", None)
            if (
                reference_site is None
                or not Path(reference_site.file_path).is_absolute()
                or not isinstance(occurrence_offset, int)
                or isinstance(occurrence_offset, bool)
                or occurrence_offset < 0
            ):
                msg = (
                    "rope census occurrence lacks an absolute file path "
                    "or nonnegative character offset"
                )
                raise RuntimeError(msg)
            occurrence_key = (reference_site.file_path, occurrence_offset)
            if (
                occurrence_key != definition_key
                and occurrence_key not in seen_occurrences
            ):
                seen_occurrences.add(occurrence_key)
                all_reference_sites.append(
                    reference_site.model_copy(update={"offset": occurrence_offset}),
                )
            # Only legacy counts use the existing line/path fallback semantics.
            if not skipped_definition and (
                FlextInfraUtilitiesRopeInventory._is_definition_occurrence(
                    hit,
                    definition_path=definition_path,
                    line=line,
                    offset=offset,
                )
            ):
                skipped_definition = True
                continue
            # Evidence must not widen the original reachability resource set.
            if (
                reachability_paths is not None
                and reference_site.file_path not in reachability_paths
            ):
                continue
            if not (
                FlextInfraUtilitiesRopeInventory._new_deduped_site(
                    reference_site,
                    seen_sites,
                )
            ):
                continue
            # Tests and examples are deliberately outside production reachability.
            if reference_site.surface in {c.Infra.DIR_TESTS, c.Infra.DIR_EXAMPLES}:
                continue
            if reference_site.surface == c.Infra.DIR_SCRIPTS:
                script_reference_sites.append(reference_site)
                continue
            runtime_reference_sites.append(reference_site)
        all_reference_sites.sort(key=lambda site: (site.file_path, site.offset))
        return (
            runtime_reference_sites,
            script_reference_sites,
            all_reference_sites,
            skipped_definition,
        )

    @staticmethod
    def _discard_unreferenced_definition(
        runtime_sites: list[m.Infra.ReferenceSite],
        script_sites: list[m.Infra.ReferenceSite],
        *,
        definition_path: Path,
        line: int,
    ) -> None:
        """Drop the definition's own site from the surface that owns it."""
        surface = FlextInfraUtilitiesRopeInventory._reference_surface(definition_path)
        if surface == c.Infra.DIR_SCRIPTS:
            FlextInfraUtilitiesRopeInventory._discard_definition_site(
                script_sites,
                definition_path=definition_path,
                line=line,
            )
        elif surface not in {c.Infra.DIR_TESTS, c.Infra.DIR_EXAMPLES}:
            FlextInfraUtilitiesRopeInventory._discard_definition_site(
                runtime_sites,
                definition_path=definition_path,
                line=line,
            )

    @staticmethod
    def _reference_sites(
        options: m.Infra.RopeInventoryRecordInput,
        *,
        line: int,
    ) -> t.Quad[
        t.VariadicTuple[m.Infra.ReferenceSite],
        t.VariadicTuple[m.Infra.ReferenceSite],
        t.VariadicTuple[m.Infra.ReferenceSite],
        bool,
    ]:
        """Collect the reference sites for the symbol one record describes.

        Returns:
            Runtime/source sites, script sites, exact all-surface evidence,
            and whether the occurrence search was anchored at all.

        Raises:
            RuntimeError: If the definition path cannot be located.

        """
        name = options.name
        lines = options.source.splitlines(keepends=True)
        try:
            offset = FlextInfraUtilitiesRopeCore.find_identifier_offset_in_lines(
                lines,
                line=line,
                symbol=name,
                pyname=options.pyname,
            )
        except RuntimeError as anchor_failure:
            offset = None
            anchor_diagnostic = str(anchor_failure)
        else:
            anchor_diagnostic = "identifier not found on its definition line"
        if offset is None:
            # A definition the binder cannot anchor (today: out-of-package
            # script modules whose Rope resource is not an indexed source
            # root, or an ambiguous same-line token) yields no reference
            # evidence. The record reports an uncollected search — never an
            # unused classification — instead of failing the whole census
            # for one unanchorable symbol.
            u.Cli.info(
                "rope census reference evidence unavailable: "
                f"{options.resource.path}:{line}:{name}: {anchor_diagnostic}",
            )
            return ((), (), (), False)
        definition_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            options.rope_project,
            options.resource,
        )
        if definition_path is None:
            msg = f"rope census definition path unavailable: {options.resource.path}"
            raise RuntimeError(msg)
        reachability_resources = (
            FlextInfraUtilitiesRopeInventory._occurrence_search_resources(
                options,
                definition_path,
                name,
            )
        )
        search_resources = (
            FlextInfraUtilitiesRopeInventory._occurrence_search_resources(
                options,
                definition_path,
                name,
                all_surfaces=True,
            )
        )
        hits = FlextInfraUtilitiesRopeImports.find_occurrences(
            options.rope_project,
            options.resource,
            offset,
            resources=search_resources,
        )
        runtime_sites, script_sites, all_sites, skipped_definition = (
            FlextInfraUtilitiesRopeInventory._classified_occurrence_sites(
                hits,
                definition_path=definition_path,
                line=line,
                offset=offset,
                reachability_paths=(
                    frozenset(
                        str(path)
                        for resource in reachability_resources
                        if (
                            path := FlextInfraUtilitiesRopeCore.resource_file_path(
                                options.rope_project,
                                resource,
                            )
                        )
                        is not None
                    )
                ),
            )
        )
        if not skipped_definition:
            FlextInfraUtilitiesRopeInventory._discard_unreferenced_definition(
                runtime_sites,
                script_sites,
                definition_path=definition_path,
                line=line,
            )
        return (
            tuple(runtime_sites),
            tuple(script_sites),
            tuple(all_sites),
            True,
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeInventory"]
