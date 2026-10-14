"""Resolve declaration roles through Rope scopes, ancestry and native matching.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)


class FlextInfraUtilitiesDeclarationPayload:
    """Identify inherited declarations without parsing or spelling heuristics."""

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
            if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(current):
                pending.extend(cls._direct_bases(current))
        return found

    @classmethod
    def _header_argument_span(
        cls,
        value: p.Infra.RopePyObject,
        scope: p.Infra.RopeScope,
        module: p.Infra.RopePyModule,
    ) -> (
        t.Pair[m.Infra.LogicalStatement, t.Triple[p.Infra.RopeWorder, int, int]] | None
    ):
        """Locate the class header base list through Rope's native reader.

        Args:
            value: The class whose header is resolved.
            scope: The class scope marking the header line.
            module: The source module declaring the class.

        Returns:
            The header statement with its native worder and base-list span,
            or ``None`` when the header has no parenthesized base list.
        """
        headers = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                module.source_code,
            )
            if statement.line == scope.get_start()
            and statement.category == c.Infra.StatementCategory.CLASS_DEF
        )
        if len(headers) != 1:
            return None
        header = headers[0]
        words = cls._worder(header.text)
        _keyword_begin, keyword_end = words.get_word_range(header.indent)
        name = header.text.index(value.get_name(), keyword_end)
        _begin, end = words.get_word_range(name)
        if header.text[end:].lstrip().startswith("["):
            _begin, end = words.code_finder.get_word_parens_range(name, "[", "]")
        if not header.text[end:].lstrip().startswith("("):
            return None
        first, last = words.get_word_parens_range(end - 1)
        return header, (words, first, last)

    @staticmethod
    def _native_subscription_bindings(
        project: p.Infra.RopeProject,
    ) -> t.SequenceOf[p.Infra.RopePyName]:
        """Collect the native subscription contracts of declared generic owners.

        Args:
            project: The Rope project supplying the declaration providers.

        Returns:
            Native ``__class_getitem__`` bindings of Pydantic and Protocol.
        """
        return tuple(
            binding
            for provider, owner in (
                ("pydantic", "BaseModel"),
                ("typing", "Protocol"),
                ("typing_extensions", "Protocol"),
            )
            if (
                binding := project
                .get_module(provider)
                .get_attribute(owner)
                .get_object()
                .get_attributes()
                .get("__class_getitem__")
            )
            is not None
        )

    @classmethod
    def _generic_subscription_context(
        cls,
        module: p.Infra.RopeSourceModule,
        header: m.Infra.LogicalStatement,
        scope: p.Infra.RopeScope,
    ) -> t.Triple[
        t.SequenceOf[t.Pair[int, int]],
        p.Infra.RopeScope,
        t.SequenceOf[p.Infra.RopePyName],
    ]:
        """Resolve header subscription matches, scope, and native bindings.

        Args:
            module: The source module declaring the class header.
            header: The resolved class header statement.
            scope: The class scope used as the declaration boundary.

        Returns:
            Header subscription match regions, the header's enclosing scope,
            and the native subscription bindings of declared generic owners.
        """
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
        parent = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
            module,
            header.start_offset,
            declaration_line=scope.get_start(),
        )
        try:
            subscriptions_in_header = tuple(
                finder.get_match_regions(
                    "${generic_owner}[${generic_arguments}]",
                    {},
                    start=header.start_offset,
                    end=header.end_offset,
                )
            )
        except AttributeError:
            # Rope's similarfinder cannot region every header shape (a
            # Subscript node inside the matched span carries no region): a
            # header it cannot region simply has no matchable subscription.
            return (), parent, ()
        subscriptions = cls._native_subscription_bindings(module.pycore.project)
        return subscriptions_in_header, parent, subscriptions

    @staticmethod
    def _native_subscription_at(
        text: str,
        offset: int,
        argument_start: int,
        argument_end: int,
        subscriptions_in_header: t.SequenceOf[t.Pair[int, int]],
    ) -> t.Pair[int, int] | None:
        """Resolve the single native subscription region covering the argument.

        Args:
            text: The class header text holding the argument.
            offset: The header start offset making regions header-relative.
            argument_start: Header-relative start offset of the argument.
            argument_end: Header-relative end offset of the argument.
            subscriptions_in_header: Native subscription regions in the header.

        Returns:
            The argument-relative subscription span, or ``None`` when the
            argument does not carry exactly one enclosing native subscription.
        """
        native_subscriptions = tuple(
            (start - offset, stop - offset)
            for start, stop in subscriptions_in_header
            if argument_start <= start - offset
            and stop - offset <= argument_end
            and not text[argument_start : start - offset].strip("() \t\r\n")
            and not text[stop - offset : argument_end].strip("() \t\r\n")
        )
        if len(native_subscriptions) != 1:
            return None
        return native_subscriptions[0]

    @classmethod
    def _specialization_owner(
        cls,
        parent: p.Infra.RopeScope,
        subscriptions: t.SequenceOf[p.Infra.RopePyName],
        bases: t.SequenceOf[p.Infra.RopePyObject],
        specialization: str,
    ) -> p.Infra.RopePyObject | None:
        """Resolve the abstract owner admitted by one specialization argument.

        Args:
            parent: The scope enclosing the class header declaration.
            subscriptions: Native subscription contracts of generic owners.
            bases: Already admitted direct bases used for identity exclusion.
            specialization: The subscription argument text being resolved.

        Returns:
            The proven generic declaration owner, or ``None`` when the
            specialization binds no new admitted generic owner.
        """
        argument_words = cls._worder(specialization)
        owner_first, _last = argument_words.code_finder.get_word_parens_range(
            0,
            "[",
            "]",
        )
        expression = argument_words.get_primary_at(owner_first - 1)
        binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            parent,
            expression,
        )
        if binding is None:
            return None
        owner = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(owner):
            return None
        subscription = owner.get_attributes().get("__class_getitem__")
        if subscription is None or not any(
            FlextInfraUtilitiesRopeRuntimeModules.same_name(known, subscription)
            for known in subscriptions
        ):
            return None
        return None if owner in bases else owner

    @classmethod
    def _admitted_generic_owner(
        cls,
        header: m.Infra.LogicalStatement,
        first: int,
        argument: str,
        context: t.Triple[
            t.SequenceOf[t.Pair[int, int]],
            p.Infra.RopeScope,
            t.SequenceOf[p.Infra.RopePyName],
        ],
        bases: t.SequenceOf[p.Infra.RopePyObject],
    ) -> p.Infra.RopePyObject | None:
        """Resolve one specialized header argument's declaration owner.

        Args:
            header: The resolved class header statement.
            first: Offset of the header base list opening parenthesis.
            argument: The specialized header argument being resolved.
            context: Header subscription matches, enclosing scope, and native
                subscription bindings of declared generic owners.
            bases: Already admitted direct bases used for identity exclusion.

        Returns:
            The abstract declaration owner proven to specialize the argument,
            or ``None`` when the argument carries no admitted owner.
        """
        subscriptions_in_header, parent, subscriptions = context
        text = header.text
        offset = header.start_offset
        argument_start = text.index(argument, first + 1)
        argument_end = argument_start + len(argument)
        region = cls._native_subscription_at(
            text,
            offset,
            argument_start,
            argument_end,
            subscriptions_in_header,
        )
        if region is None:
            return None
        start, stop = region
        return cls._specialization_owner(
            parent,
            subscriptions,
            bases,
            text[start:stop],
        )

    @classmethod
    def _extend_generic_owners(
        cls,
        bases: list[p.Infra.RopePyObject],
        header: m.Infra.LogicalStatement,
        first: int,
        specialized_arguments: t.SequenceOf[str],
        context: t.Triple[
            t.SequenceOf[t.Pair[int, int]],
            p.Infra.RopeScope,
            t.SequenceOf[p.Infra.RopePyName],
        ],
    ) -> None:
        """Extend direct bases with proven generic declaration owners.

        Args:
            bases: Native direct bases, extended in place in header order.
            header: The resolved class header statement.
            first: Offset of the header base list opening parenthesis.
            specialized_arguments: Header arguments carrying a subscription.
            context: Header subscription matches, enclosing scope, and native
                subscription bindings of declared generic owners.
        """
        for argument in specialized_arguments:
            owner = cls._admitted_generic_owner(
                header,
                first,
                argument,
                context,
                bases,
            )
            if owner is not None:
                bases.append(owner)

    @classmethod
    def _direct_bases(
        cls,
        value: p.Infra.RopePyObject,
    ) -> t.SequenceOf[p.Infra.RopePyObject]:
        """Resolve generic ancestry without erasing the source's specialization.

        Rope supplies lexical boundaries and bindings. A generic subscription
        contributes its owner only when it inherits the native Pydantic/typing
        subscription contract; custom class subscription behavior is not assumed.

        Args:
            value: The class whose direct bases are to be resolved.

        Returns:
            Native direct bases, including proven generic declaration owners.

        Raises:
            TypeError: If the class module has no native project owner.
        """
        bases = list(value.get_superclasses())
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
            return bases
        scope = value.get_scope()
        module = value.get_module()
        if scope is None or module is None:
            return bases
        if not isinstance(module, p.Infra.RopeSourceModule):
            msg = "Rope class module has no native project owner"
            raise TypeError(msg)
        resolved = cls._header_argument_span(value, scope, module)
        if resolved is None:
            return bases
        header, span = resolved
        words, first, last = span
        arguments, _keywords = words.get_parameters(first, last - 1)
        specialized_arguments = tuple(
            argument for argument in arguments if "[" in argument
        )
        if not specialized_arguments:
            return bases
        context = cls._generic_subscription_context(module, header, scope)
        cls._extend_generic_owners(
            bases,
            header,
            first,
            specialized_arguments,
            context,
        )
        return bases

    @staticmethod
    def _worder(source: str) -> p.Infra.RopeWorder:
        """Bind Rope's native header and parameter reader.

        Returns:
            The native lexical reader.

        Raises:
            TypeError: If the reader does not satisfy the declared Rope contract.
        """
        words = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
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
    ) -> t.VariadicTuple[str]:
        """Discover module and nested class paths from the native scope graph.

        Function-local declarations have no durable family owner and are excluded.

        Returns:
            Every qualified class declaration matching the supplied short name.
        """
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            path,
        )
        module = project.get_pymodule(resource)
        scope = module.get_scope()
        if scope is None:
            return ()
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
        resolved = cls._class_binding(project, path, qualified_name)
        if resolved is None:
            return None
        module, binding = resolved
        value = binding.get_object()
        ancestry = cls.class_ancestry(value)
        base = project.get_module("pydantic").get_attribute("BaseModel").get_object()
        settings = (
            project
            .get_module("pydantic_settings")
            .get_attribute("BaseSettings")
            .get_object()
        )
        if base not in ancestry or settings in ancestry:
            return None
        scope = value.get_scope()
        statements = (
            None
            if scope is None
            else cls._admitted_payload_statements(module, value, scope)
        )
        if statements is None:
            return None
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
        for member_scope in scope.get_scopes():
            if (
                member_scope.get_kind() == c.Infra.RopeScopeKind.FUNCTION
                and not cls._payload_method(finder, member_scope.pyobject, statements)
            ):
                return None
        return binding

    @classmethod
    def _admitted_payload_statements(
        cls,
        module: p.Infra.RopePyModule,
        value: p.Infra.RopePyObject,
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
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            path,
        )
        module = project.get_pymodule(resource)
        owner = module.get_attributes()
        binding: p.Infra.RopePyName | None = None
        for name in qualified_name.split("."):
            binding = owner.get(name)
            if binding is None:
                return None
            owner = binding.get_object().get_attributes()
        if binding is None:
            return None
        value = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value):
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
        bases = cls._direct_bases(binding.get_object())
        return (
            binding
            if any(
                project.get_module(provider).get_attribute("Protocol").get_object()
                in bases
                for provider in ("typing", "typing_extensions")
            )
            else None
        )

    @staticmethod
    def _payload_body(
        value: p.Infra.RopePyObject,
        scope: p.Infra.RopeScope,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Reject class-body behavior using the existing Rope statement boundary.

        Returns:
            Whether the class body contains only declaration statements.
        """
        return all(
            statement.category
            in {
                c.Infra.StatementCategory.ANN_ASSIGN,
                c.Infra.StatementCategory.ASSIGN,
                c.Infra.StatementCategory.FUNC_DEF,
            }
            or statement.text.strip() == "pass"
            or statement.text.lstrip().startswith("@")
            or (
                statement.line == scope.get_body_start() and value.get_doc() is not None
            )
            for statement in statements
            if scope.get_start() < statement.line <= scope.get_end()
            and statement.enclosing_kind == c.Infra.RopeScopeKind.CLASS
            and statement.enclosing_name == value.get_name()
        )

    @staticmethod
    def _payload_method(
        finder: p.Infra.RopeSimilarFinder,
        method: p.Infra.RopePyObject,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Admit only native declaration decorators in Rope's header region.

        Returns:
            Whether every decorator is allowed and one belongs to Pydantic.
        """
        scope = method.get_scope()
        if scope is None:
            return False
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
            expression = decorator[1:]
            callee_start = (
                statement.start_offset
                + len(statement.text)
                - len(decorator)
                + 1
                + len(expression)
                - len(expression.lstrip())
            )
            identities = tuple(
                identity
                for identity in (
                    *c.Infra.PYDANTIC_PAYLOAD_DECORATORS,
                    *c.Infra.PAYLOAD_DESCRIPTOR_DECORATORS,
                )
                if any(
                    start == callee_start
                    for start, _end in finder.get_match_regions(
                        f"${{{identity.rsplit('.', 1)[-1]}}}",
                        {identity.rsplit(".", 1)[-1]: f"object={identity}"},
                        start=statement.start_offset,
                        end=statement.end_offset,
                    )
                )
            )
            if not identities:
                return False
            known |= any(
                identity in c.Infra.PYDANTIC_PAYLOAD_DECORATORS
                for identity in identities
            )
        return known


__all__: list[str] = ["FlextInfraUtilitiesDeclarationPayload"]
