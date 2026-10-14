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
    def _class_ancestry(
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
    def _direct_bases(
        cls,
        value: p.Infra.RopePyObject,
    ) -> t.SequenceOf[p.Infra.RopePyObject]:
        """Resolve generic ancestry without erasing the source's specialization.

        Rope supplies lexical boundaries and bindings. A generic subscription
        contributes its owner only when it inherits the native Pydantic/typing
        subscription contract; custom class subscription behavior is not assumed.

        Returns:
            Native direct bases, including proven generic declaration owners.
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
        project = module.pycore.project
        headers = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                module.source_code,
            )
            if statement.line == scope.get_start()
            and statement.category == c.Infra.StatementCategory.CLASS_DEF
        )
        if len(headers) != 1:
            return bases
        header = headers[0]
        words = cls._worder(header.text)
        _keyword_begin, keyword_end = words.get_word_range(header.indent)
        name = header.text.index(value.get_name(), keyword_end)
        _begin, end = words.get_word_range(name)
        if header.text[end:].lstrip().startswith("["):
            _begin, end = words.get_word_parens_range(name, "[", "]")
        if not header.text[end:].lstrip().startswith("("):
            return bases
        first, last = words.get_word_parens_range(end - 1)
        arguments, _keywords = words.get_parameters(first, last - 1)
        parent = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
            module,
            header.start_offset,
            declaration_line=scope.get_start(),
        )
        subscriptions = tuple(
            binding
            for provider, owner in (
                ("pydantic", "BaseModel"),
                ("typing", "Protocol"),
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
        for argument in arguments:
            if "[" not in argument:
                continue
            argument_words = cls._worder(argument)
            first, _last = argument_words.get_word_parens_range(0, "[", "]")
            expression = argument_words.get_primary_at(first - 1)
            binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                parent,
                expression,
            )
            if binding is None:
                continue
            owner = binding.get_object()
            if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(owner):
                continue
            subscription = owner.get_attributes().get("__class_getitem__")
            if (
                subscription is not None
                and any(
                    FlextInfraUtilitiesRopeRuntimeModules.same_name(
                        known,
                        subscription,
                    )
                    for known in subscriptions
                )
                and owner not in bases
            ):
                bases.append(owner)
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
        scope = project.get_pymodule(resource).get_scope()
        if scope is None:
            return ()
        pending: list[t.Pair[p.Infra.RopeScope, str]] = [(scope, "")]
        names: list[str] = []
        while pending:
            parent, prefix = pending.pop()
            for child in parent.get_scopes():
                if child.get_kind() != c.Infra.RopeScopeKind.CLASS:
                    continue
                local_name = child.pyobject.get_name()
                qualified_name = f"{prefix}.{local_name}" if prefix else local_name
                if local_name == name:
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
        ancestry = cls._class_ancestry(value)
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
        if scope is None:
            return None
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
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
        for member in scope.get_defined_names().values():
            method = member.get_object()
            if FlextInfraUtilitiesRopeRuntimeTypes.py_function(
                method
            ) and not cls._payload_method(finder, method, statements):
                return None
        return binding

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
        protocol = project.get_module("typing").get_attribute("Protocol").get_object()
        return binding if protocol in cls._direct_bases(binding.get_object()) else None

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
            identities = tuple(
                identity
                for identity in (
                    *c.Infra.PYDANTIC_PAYLOAD_DECORATORS,
                    *c.Infra.PAYLOAD_DESCRIPTOR_DECORATORS,
                )
                if tuple(
                    finder.get_match_regions(
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
