"""Resolve declaration roles through Rope scopes, ancestry and native matching.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
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
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesDeclarationPayload(
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesTypesRopeRuntime,
):
    """Identify inherited declarations without parsing or spelling heuristics."""

    @staticmethod
    def identity_name(
        project: p.Infra.RopeProject,
        identity: str,
    ) -> p.Infra.RopePyName:
        """Resolve one qualified ``module.attribute`` identity in the graph.

        Returns:
            The native name the identity's module binds.

        """
        module, _, name = identity.rpartition(".")
        return FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, name, module_name=module
        )

    @classmethod
    def class_ancestry(
        cls,
        value: p.Infra.RopePyObject,
    ) -> t.SequenceOf[p.Infra.RopePyObject]:
        pending = [value]
        found: list[p.Infra.RopePyObject] = []
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.append(current)
            if FlextInfraUtilitiesTypesRopeRuntime.abstract_class(current):
                pending.extend(cls.direct_bases(current))
        return found

    @classmethod
    def utility_behavior_provider(
        cls, project: p.Infra.RopeProject, owner: p.Infra.RopePyObject
    ) -> bool:
        """Prove stateless utility behavior without reclassifying class entities.

        Returns:
            Whether native ancestry, descriptors and storage establish behavior.

        """
        if not cls.py_class(owner):
            return False
        ancestry = cls.class_ancestry(owner)
        entities = tuple(
            cls.identity_name(project, identity).get_object()
            for identity in ("enum.Enum", "typing.Protocol", "pydantic.BaseModel")
        )
        if any(ancestor in entities for ancestor in ancestry):
            return False
        methods = tuple(
            value
            for attribute in owner.get_attributes().values()
            if cls.py_function(value := attribute.get_object())
        )
        return (
            bool(methods)
            and all(
                method.get_kind() in {"classmethod", "staticmethod"}
                for method in methods
            )
            and all(
                not cls.py_class(ancestor)
                or cls.utility_namespace_declaration(project, ancestor)
                for ancestor in ancestry
            )
        )

    @classmethod
    def utility_namespace_declaration(
        cls, project: p.Infra.RopeProject, owner: p.Infra.RopeSourceClass
    ) -> bool:
        """Validate native utility storage for rendering and semantic migration.

        Returns:
            Whether the declaration contains only admissible class storage.

        Raises:
            TypeError: The native utility declaration is not a class syntax tree.

        """
        node = owner.get_ast()
        if not isinstance(node, ast.ClassDef):
            message = "utility provider has no native class syntax tree"
            raise TypeError(message)
        return not node.decorator_list and not any(
            isinstance(member, ast.AnnAssign)
            and not cls._declares_class_storage(project, owner.get_scope(), member)
            for member in node.body
        )

    @classmethod
    def _declares_class_storage(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        member: ast.AnnAssign,
    ) -> bool:
        """Authenticate ClassVar and initialized Final through native identities.

        Returns:
            Whether the annotation proves class storage for this declaration.

        """
        annotation = member.annotation
        qualifier = cls.resolve_symbol(
            scope,
            annotation.value if isinstance(annotation, ast.Subscript) else annotation,
        )
        return cls.same_name(
            cls.qualified_name(project, "ClassVar", module_name="typing"), qualifier
        ) or (
            member.value is not None
            and cls.same_name(
                cls.qualified_name(project, "Final", module_name="typing"), qualifier
            )
        )

    @classmethod
    def _header_argument_span(
        cls,
        value: p.Infra.RopeNamedObject,
        scope: p.Infra.RopeScope,
        module: p.Infra.RopePyModule,
    ) -> t.Pair[str, t.Triple[p.Infra.RopeWorder, int, int]] | None:
        """Locate the class header base list through Rope's native reader.

        Args:
            value: The class whose header is resolved.
            scope: The class scope marking the header line.
            module: The source module declaring the class.

        Returns:
            The original header text with its native worder and base-list span,
            or ``None`` when the header has no parenthesized base list.

        """
        first_line, last_line = module.logical_lines.logical_line_in(scope.get_start())
        lines = module.lines
        header = module.source_code[
            lines.get_line_start(first_line) : lines.get_line_end(last_line)
        ]
        words = cls._worder(header)
        indent = len(header) - len(header.lstrip())
        _keyword_begin, keyword_end = words.get_word_range(indent)
        name = header.index(value.get_name(), keyword_end)
        _begin, end = words.get_word_range(name)
        if header[end:].lstrip().startswith("["):
            _begin, end = words.code_finder.get_word_parens_range(name, "[", "]")
        if not header[end:].lstrip().startswith("("):
            return None
        first, last = words.get_word_parens_range(end - 1)
        return header, (words, first, last)

    @classmethod
    def direct_bases(
        cls, value: p.Infra.RopePyObject
    ) -> t.SequenceOf[p.Infra.RopePyObject]:
        """Return native bases and proven generic owners in their original scope.

        Returns:
            Direct bases without erasing specialization or guessing subscriptions.

        Raises:
            TypeError: If a source class lacks its native project owner.

        """
        bases = list(
            FlextInfraUtilitiesTypesRopeRuntime.require_class_object(
                value, "declaration ancestry"
            ).get_superclasses()
        )
        if not FlextInfraUtilitiesTypesRopeRuntime.py_class(value):
            return bases
        scope, module = value.get_scope(), value.get_module()
        if not isinstance(module, p.Infra.RopeSourceModule):
            msg = "Rope class module has no native project owner"
            raise TypeError(msg)
        resolved = cls._header_argument_span(value, scope, module)
        if resolved is None:
            return bases
        header, (_words, first, last) = resolved
        arguments = cls._specialized_arguments(header, first, last)
        if not arguments:
            return bases
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        parent = runtime.scope_at(
            module,
            module.lines.get_line_start(scope.get_start()),
            declaration_line=scope.get_start(),
        )
        subscriptions = tuple(
            item
            for provider, name in (
                ("pydantic", "BaseModel"),
                ("typing", "Protocol"),
                ("typing_extensions", "Protocol"),
            )
            if (resource := module.pycore.project.find_module(provider)) is not None
            if FlextInfraUtilitiesRopeCore.resolvable_module_resource(resource)
            if (
                binding := FlextInfraUtilitiesRopeCore
                .resolve_pymodule(
                    module.pycore.project,
                    resource,
                )
                .get_attributes()
                .get(name)
            )
            is not None
            if (item := binding.get_object().get_attributes().get("__class_getitem__"))
            is not None
        )
        for argument in arguments:
            owner = cls._specialized_base(argument, parent)
            if owner is None:
                continue
            subscription = owner.get_attributes().get("__class_getitem__")
            if (
                subscription is not None
                and owner not in bases
                and any(
                    runtime.same_name(known, subscription) for known in subscriptions
                )
            ):
                bases.append(owner)
        return bases

    @staticmethod
    def _specialized_arguments(source: str, first: int, last: int) -> t.StrSequence:
        """Select the original subscribed class-header arguments.

        Returns:
            Native header argument text in source order.

        """
        segments = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
            source,
            first + 1,
            last - 1,
            ",",
        )
        return tuple(
            source[begin:end] for begin, end in segments if "[" in source[begin:end]
        )

    @classmethod
    def _specialized_base(
        cls,
        argument: str,
        parent: p.Infra.RopeScope,
    ) -> p.Infra.RopePyObject | None:
        """Resolve one complete subscription through its original native scope.

        Returns:
            The actual class owner, when the entire argument is one subscription.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        regions = tuple(
            (left, right)
            for left, right in FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
                runtime.build_string_module(None, argument),
                "${generic_owner}[${generic_arguments}]",
                arguments={},
            )
            if not argument[:left].strip("() \t\r\n")
            and not argument[right:].strip("() \t\r\n")
        )
        if len(regions) != 1:
            return None
        left, right = regions[0]
        words = cls._worder(argument[left:right])
        opening, _closing = words.code_finder.get_word_parens_range(0, "[", "]")
        binding = runtime.expression_name(parent, words.get_primary_at(opening - 1))
        if binding is None:
            return None
        owner = binding.get_object()
        return (
            owner if FlextInfraUtilitiesTypesRopeRuntime.abstract_class(owner) else None
        )

    @staticmethod
    def _worder(source: str) -> p.Infra.RopeWorder:
        """Bind Rope's native header and parameter reader.

        Returns:
            The native lexical reader.

        Raises:
            TypeError: If the reader does not satisfy the declared Rope contract.

        """
        words = FlextInfraUtilitiesTypesRopeRuntime.runtime_callable(
            "rope.base.worder",
            "Worder",
        )(source, handle_ignores=True)
        if not isinstance(words, p.Infra.RopeWorder):
            msg = "Rope Worder does not expose its native header contract"
            raise TypeError(msg)
        return words

    @staticmethod
    def declaration_names(
        project: p.Infra.RopeProject,
        path: Path,
        name: str,
        *,
        offset: int | None = None,
    ) -> tuple[str, ...]:
        """Discover module and nested class paths from the native scope graph.

        Function-local declarations have no durable family owner and are excluded.

        Returns:
            Every qualified class declaration matching the supplied short name.

        """
        resource = FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        scope = module.get_scope()
        declaration_lines = (
            frozenset(
                statement.line
                for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                    module.source_code,
                )
                if statement.category == c.Infra.StatementCategory.CLASS_DEF
                and statement.start_offset <= offset < statement.end_offset
            )
            if offset is not None
            else None
        )
        pending: list[t.Pair[p.Infra.RopeScope, str]] = [(scope, "")]
        names: list[str] = []
        while pending:
            parent, prefix = pending.pop()
            for child in parent.get_scopes():
                if child.get_kind() != c.Infra.RopeScopeKind.CLASS:
                    continue
                local_name = child.pyobject.get_name()
                qualified_name = f"{prefix}.{local_name}" if prefix else local_name
                if local_name == name and (
                    declaration_lines is None or child.get_start() in declaration_lines
                ):
                    names.append(qualified_name)
                pending.append((child, qualified_name))
        return tuple(names)

    @classmethod
    def payload_declaration(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> p.Infra.RopePyName | None:
        """Resolve a data declaration, including fields inherited from a preset.

        Recognition follows the actual BaseModel identity. Relocation admission
        additionally rejects settings, class decorators and behavioral methods.
        Validators, serializers and computed fields retain their native identity.

        Args:
            project: The Rope project context for the resolution.
            path: The file path containing the declaration.
            qualified_name: The fully qualified name of the declaration.

        Returns:
            The bound model declaration, or ``None`` for a different contract.

        """
        binding = cls.payload_body(project, path, qualified_name)
        if binding is None:
            return None
        ancestry = cls.class_ancestry(binding.get_object())
        base = cls.identity_name(project, c.Infra.PYDANTIC_MODEL_IDENTITY).get_object()
        settings = cls.identity_name(
            project, c.Infra.PYDANTIC_SETTINGS_IDENTITY
        ).get_object()
        if base not in ancestry or settings in ancestry:
            return None
        return binding

    @classmethod
    def payload_body(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> p.Infra.RopePyName | None:
        """Admit a class whose body declares only data, ancestry aside.

        Settings, class decorators and behavioral methods reject it;
        validators, serializers and computed fields keep their identity.

        Returns:
            The class binding, or ``None`` when its body holds behavior.

        """
        resolved = cls._class_binding(project, path, qualified_name)
        if resolved is None:
            return None
        module, binding = resolved
        value = FlextInfraUtilitiesTypesRopeRuntime.require_source_object(
            binding.get_object(), qualified_name
        )
        scope = value.get_scope()
        statements = cls._admitted_payload_statements(module, value, scope)
        if statements is None:
            return None
        for member_scope in scope.get_scopes():
            if (
                member_scope.get_kind() == c.Infra.RopeScopeKind.FUNCTION
                and not cls._payload_method(
                    project,
                    member_scope.pyobject,
                    statements,
                )
            ):
                return None
        return binding

    @classmethod
    def _admitted_payload_statements(
        cls,
        module: p.Infra.RopePyModule,
        value: p.Infra.RopeNamedObject,
        scope: p.Infra.RopeScope,
    ) -> t.SequenceOf[m.Infra.LogicalStatement] | None:
        """Return the logical statements of one admitted payload body.

        Args:
            module: The native module declaring the payload.
            value: The resolved payload class object.
            scope: The native class scope of the payload.

        Returns:
            The class logical statements when the scope leads with no
            statements and the body holds only declarations, else ``None``.

        """
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(
            module.source_code,
        )
        begin, _end = scope.get_region()
        if any(
            begin < statement.end_offset and statement.line < scope.get_start()
            for statement in statements
        ):
            return None
        located = cls._header_argument_span(value, scope, module)
        if located is not None:
            header, (_words, _first, last) = located
            inline = header[last:].lstrip()
            if (
                inline.startswith(":")
                and inline[1:].strip()
                and not cls._payload_statement_sequence(
                    inline[1:].strip(), docstring=value.get_doc() is not None
                )
            ):
                return None
        if not cls._payload_body(value, scope, statements):
            return None
        return statements

    @staticmethod
    def _class_binding(
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> t.Pair[p.Infra.RopePyModule, p.Infra.RopePyName] | None:
        """Resolve one lexical class identity through its native module.

        Returns:
            The native module and class binding, or ``None`` for a non-class.

        """
        resource = FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        *enclosing, name = qualified_name.split(".")
        owner = module.get_attributes()
        # Only an enclosing class's members are read: concluding the inherited
        # attributes of the resolved class itself is the costliest Rope step
        # and nothing below needs it.
        for segment in enclosing:
            enclosing_binding = owner.get(segment)
            if enclosing_binding is None:
                return None
            owner = enclosing_binding.get_object().get_attributes()
        binding = owner.get(name)
        if binding is None:
            return None
        value = binding.get_object()
        if not FlextInfraUtilitiesTypesRopeRuntime.abstract_class(value):
            return None
        return module, binding

    @classmethod
    def protocol_declaration(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> p.Infra.RopePyName | None:
        """Identify a declared protocol rather than a concrete implementation.

        Python subprotocols explicitly include Protocol among their direct bases.
        Merely implementing an inherited protocol does not declare a new protocol.

        Returns:
            The native protocol binding, or ``None`` for a different contract.

        """
        resolved = cls._class_binding(project, path, qualified_name)
        if resolved is None:
            return None
        _module, binding = resolved
        bases = cls.direct_bases(binding.get_object())
        defining = frozenset(
            declared for base in bases if (declared := base.get_module()) is not None
        )
        return (
            binding
            if any(
                (resource := project.find_module(provider)) is not None
                and FlextInfraUtilitiesRopeCore.resolvable_module_resource(resource)
                and FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
                in defining
                for provider in ("typing", "typing_extensions")
            )
            else None
        )

    @classmethod
    def model_ancestry_declaration(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> p.Infra.RopePyName | None:
        """Identify a class whose native ancestry reaches the model base.

        Unlike ``payload_declaration`` any class body qualifies: a namespace
        that inherits a model in any position of its ancestry is itself a model.

        Returns:
            The native class binding, or ``None`` when no ancestor is the model base.

        """
        resolved = cls._class_binding(project, path, qualified_name)
        if resolved is None:
            return None
        _module, binding = resolved
        value = FlextInfraUtilitiesTypesRopeRuntime.require_source_object(
            binding.get_object(), qualified_name
        )
        base = cls.identity_name(project, c.Infra.PYDANTIC_MODEL_IDENTITY).get_object()
        return binding if base in cls.class_ancestry(value) else None

    @classmethod
    def _payload_body(
        cls,
        value: p.Infra.RopeNamedObject,
        scope: p.Infra.RopeScope,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Reject class-body behavior using the existing Rope statement boundary.

        Returns:
            Whether the class body contains only declaration statements.

        """
        return all(
            statement.category == c.Infra.StatementCategory.FUNC_DEF
            or statement.text.lstrip().startswith("@")
            or cls._payload_statement_sequence(
                statement.text,
                docstring=(
                    statement.line == scope.get_body_start()
                    and value.get_doc() is not None
                ),
            )
            for statement in statements
            if scope.get_start() < statement.line <= scope.get_end()
            and statement.enclosing_kind == c.Infra.RopeScopeKind.CLASS
            and statement.enclosing_name == value.get_name()
        )

    @staticmethod
    def _payload_statement_sequence(source: str, *, docstring: bool) -> bool:
        """Admit each simple statement through the shared native region splitter.

        Returns:
            Whether every semicolon-delimited statement remains declaration data.

        """
        regions = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments(
            source, 0, len(source), ";"
        )
        return bool(regions) and all(
            statement.category
            in {
                c.Infra.StatementCategory.ANN_ASSIGN,
                c.Infra.StatementCategory.ASSIGN,
            }
            or statement.text.strip() == "pass"
            or (
                index == 0
                and docstring
                and FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(
                    statement.text
                )
                is not None
            )
            for index, (begin, end) in enumerate(regions)
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                source[begin:end]
            )
        )

    @classmethod
    def _payload_method(
        cls,
        project: p.Infra.RopeProject,
        method: p.Infra.RopeScopedObject,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Admit only native declaration decorators in Rope's header region.

        Returns:
            Whether every decorator is allowed and one belongs to Pydantic.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        owning_module = method.get_module()
        module_scope = owning_module.get_scope()
        known_targets = {
            identity: cls.identity_name(project, identity)
            for identity in (
                *c.Infra.PYDANTIC_PAYLOAD_DECORATORS,
                *c.Infra.PAYLOAD_DESCRIPTOR_DECORATORS,
            )
        }
        scope = method.get_scope()
        begin, _end = scope.get_region()
        known = False
        for statement in statements:
            if not (
                begin < statement.end_offset and statement.line < scope.get_start()
            ):
                continue
            decorator = statement.text.lstrip()
            if not decorator.startswith("@"):
                return False
            callee = decorator[1:].strip()
            expression = ast.parse(callee, mode="eval").body
            callee_name = getattr(expression, "func", expression)
            resolved = runtime.resolve_symbol(module_scope, callee_name)
            if resolved is None:
                return False
            identity = next(
                (
                    candidate
                    for candidate, target in known_targets.items()
                    if runtime.same_name(target, resolved)
                ),
                None,
            )
            if identity is None:
                return False
            known |= identity in c.Infra.PYDANTIC_PAYLOAD_DECORATORS
        return known


__all__: list[str] = ["FlextInfraUtilitiesDeclarationPayload"]
