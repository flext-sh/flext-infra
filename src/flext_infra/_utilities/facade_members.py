"""Single owner of every facade member, derived from the object it binds.

A facade letter (``c``, ``t``, ``p``, ``m``, ``u`` ...) may re-export a name a
lower layer already owns. The owner of a member is selected by the kind of the
source binding of the name, through the declarative ``facade-members``
policy; every other facade binding the same object is a duplicate that
``make mod`` retires, and its consumers are relocated to the owner. No member
or letter is listed here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from rope.base import exceptions as rope_exceptions

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodNative
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesFacadeMembers:
    """Derive facade member kinds and their single owner letter."""

    @classmethod
    def facade_member_kind(
        cls,
        value: p.Infra.RopePyName,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        source_project: p.Infra.RopeProject,
    ) -> c.Infra.FacadeMemberKind:
        """Classify a proven native declaration, never an unknown inference.

        Returns:
            The configured declaration kind of the native binding.

        Raises:
            ValueError: The native binding has no proven declaration kind.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        binding = value
        while True:
            annotation_kind = cls._annotation_kind(
                binding, source_project=source_project
            )
            if (
                annotation_kind is None
                and binding.get_object()
                is runtime.runtime_callable("rope.base.pyobjects", "get_unknown")()
            ):
                annotation_kind = cls._stub_kind(binding, source_project=source_project)
            if annotation_kind is not None:
                return annotation_kind
            if binding is not value:
                break
            resolved = cls._typing_origin(value, source_project=source_project)
            if resolved is binding:
                break
            binding = resolved
        origin = binding.get_object()
        if origin is runtime.runtime_callable("rope.base.pyobjects", "get_unknown")():
            message = (
                f"unknown facade member kind: {binding.get_definition_location()}; "
                f"original_type={type(value).__qualname__}; "
                f"original_definition={value.get_definition_location()}; "
                f"resolved_type={type(binding).__qualname__}; "
                f"same_binding={binding is value}; "
                f"project={source_project.root.real_path}"
            )
            raise ValueError(message)
        kind = c.Infra.FacadeMemberKind
        policy = config.Infra.tooling.facade_members
        module = origin.get_module()
        module_name = "" if module is None else module.get_name()
        if types.abstract_class(origin):
            return cls.class_kind(
                origin,
                resolver_factory=resolver_factory,
                source_project=source_project,
            )
        if types.py_function(origin) or isinstance(
            origin, runtime.runtime_type("rope.base.builtins", "BuiltinFunction")
        ):
            return (
                kind.TYPE
                if module_name in policy.type_constructor_modules
                else kind.MODEL_DECLARATION
                if module_name in policy.model_declaration_modules
                else kind.FUNCTION
            )
        origin_type = origin.get_type().get_module()
        return (
            kind.TYPE
            if origin_type is not None
            and origin_type.get_name() in c.Infra.FACADE_MEMBER_TYPING_MODULES
            else kind.CONSTANT
        )

    @staticmethod
    def _stub_kind(
        value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> c.Infra.FacadeMemberKind | None:
        """Classify a binary export from its installed class or value declaration.

        Returns:
            The source-declared kind, or None without a proven declaration.

        Raises:
            ValueError: If the binary export has ambiguous or cyclic declarations.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        imported = runtime.class_assignment_binding(value, classes_only=False)
        visited: set[int] = set()
        while imported is not None:
            if id(imported) in visited:
                message = f"cyclic binary export: {imported.get_definition_location()}"
                raise ValueError(message)
            visited.add(id(imported))
            if types.assigned_name(imported):
                if len(imported.assignments) != 1:
                    return None
                assigned = imported.assignments[0].ast_node
                module, _line = runtime.definition_location(imported)
                if not isinstance(
                    assigned, ast.Name | ast.Attribute
                ) or not types.source_module(module):
                    return None
                scope = runtime.scope_at(
                    module, runtime.source_offset(module.source_code, assigned)
                )
                imported = runtime.resolve_symbol(scope, assigned)
                continue
            if not types.imported_name(imported):
                return None
            resource = runtime.imported_module_resource(source_project, imported)
            path = Path(resource.real_path).resolve()
            stub = path / "__init__.pyi" if path.is_dir() else path.with_suffix(".pyi")
            if stub.is_file():
                statements = ast.parse(stub.read_text(encoding="utf-8")).body
                declarations = [
                    node
                    for node in statements
                    if isinstance(node, ast.ClassDef)
                    and node.name == imported.imported_name
                ]
                values = [
                    node
                    for node in statements
                    if isinstance(node, ast.AnnAssign)
                    and node.value is None
                    and isinstance(node.target, ast.Name)
                    and node.target.id == imported.imported_name
                ]
                if len(declarations) + len(values) > 1:
                    message = (
                        "ambiguous binary declaration: "
                        f"{(path, imported.imported_name)}"
                    )
                    raise ValueError(message)
                if values or declarations:
                    return (
                        c.Infra.FacadeMemberKind.CONSTANT
                        if values
                        else c.Infra.FacadeMemberKind.EXCEPTION
                        if any(
                            isinstance(base, ast.Name)
                            and isinstance(
                                base_type := vars(builtins).get(base.id), type
                            )
                            and issubclass(base_type, BaseException)
                            for base in declarations[0].bases
                        )
                        else c.Infra.FacadeMemberKind.TYPE
                    )
            imported = (
                FlextInfraUtilitiesRopeCore
                .resolve_pymodule(source_project, resource)
                .get_attributes()
                .get(imported.imported_name)
            )
        return None

    @classmethod
    def _annotation_kind(
        cls, value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> c.Infra.FacadeMemberKind | None:
        """Identify explicit annotation declarations before resolving their value.

        Args:
            value: The annotation to inspect.
            source_project: The native project providing the annotation's context.

        Returns:
            The declared annotation kind, or no applicable annotation declaration.

        Raises:
            ValueError: If a cyclic annotation is detected.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        alias = runtime.annotation_alias_definition(value)
        visited: set[int] = set()
        declared_alias = False
        while alias is not None:
            declaration, scope = alias
            if id(declaration) in visited:
                message = f"cyclic facade annotation: {declaration.name.id}"
                raise ValueError(message)
            visited.add(id(declaration))
            expression = declaration.value
            while isinstance(expression, ast.Subscript) and runtime.same_name(
                runtime.qualified_name(source_project, "typing.Annotated"),
                runtime.resolve_symbol(scope, expression.value),
            ):
                if (
                    not isinstance(expression.slice, ast.Tuple)
                    or not expression.slice.elts
                ):
                    return None
                expression = expression.slice.elts[0]
            if isinstance(expression, ast.BinOp) and isinstance(
                expression.op, ast.BitOr
            ):
                return c.Infra.FacadeMemberKind.TYPE
            origin = runtime.resolve_symbol(
                scope,
                expression.value
                if isinstance(expression, ast.Subscript)
                else expression,
            )
            if origin is None:
                return None
            declared_alias = True
            alias = runtime.annotation_alias_definition(origin)
        if declared_alias:
            return c.Infra.FacadeMemberKind.TYPE
        return cls._annotation_assignment_kind(value, source_project=source_project)

    @classmethod
    def _annotation_assignment_kind(
        cls, value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> c.Infra.FacadeMemberKind | None:
        """Classify an assignment from its native annotation or value provenance.

        Returns:
            The declared assignment kind, or no applicable annotation declaration.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        assigned = runtime.annotation_assignment_outer_type(source_project, value)
        if assigned is not None:
            origin, from_value = assigned
            if not from_value:
                return c.Infra.FacadeMemberKind.CONSTANT
            if runtime.same_name(
                runtime.qualified_name(source_project, "typing.Literal"), origin
            ) or runtime.same_name(
                runtime.qualified_name(source_project, "collections.abc.Callable"),
                origin,
            ):
                return c.Infra.FacadeMemberKind.TYPE
            if cls._annotated_class_value(value, source_project=source_project):
                return c.Infra.FacadeMemberKind.TYPE
        if (
            cls._typing_assigned_value(value, source_project=source_project)
            # A prova Annotated estrita (operando classe + metadata) vale
            # também quando a resolução por anotação não se aplica.
            or cls._annotated_class_value(value, source_project=source_project)
        ):
            return c.Infra.FacadeMemberKind.TYPE
        return None

    @staticmethod
    def _typing_assigned_value(
        value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> bool:
        """Prove a plain assignment subscribes a native ``typing`` constructor.

        Atribuições simples de fornecedores externos ao snapshot (sem
        ``AnnAssign``) carregam o subscrito no valor declarado; a identidade
        do construtor contra ``typing``/``typing_extensions`` nativos prova a
        classificação TYPE sem mapa de nomes nem inferência.

        Returns:
            Whether the declared subscrito constructor is proven native.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        supplier = runtime.class_assignment_binding(
            runtime.source_import_binding(value), classes_only=False
        )
        if (
            supplier is None
            or not types.assigned_name(supplier)
            or len(supplier.assignments) != 1
        ):
            return False
        expression = supplier.assignments[0].ast_node
        if not isinstance(expression, ast.Subscript):
            return False
        module, _line = runtime.definition_location(supplier)
        if not types.source_module(module):
            return False
        scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, expression)
        )
        constructor = runtime.resolve_symbol(scope, expression.value)
        return any(
            runtime.same_name(
                runtime.qualified_name(source_project, identity), constructor
            )
            for identity in ("typing.Literal", "typing_extensions.Literal")
        )

    @staticmethod
    def _annotated_class_value(
        value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> bool:
        """Prove an Annotated value wraps a native class and includes metadata.

        Returns:
            Whether the native constructor and its class operand are proven.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        supplier = runtime.class_assignment_binding(
            runtime.source_import_binding(value), classes_only=False
        )
        if (
            supplier is None
            or not types.assigned_name(supplier)
            or len(supplier.assignments) != 1
        ):
            return False
        expression = supplier.assignments[0].ast_node
        if (
            not isinstance(expression, ast.Subscript)
            or not isinstance(expression.slice, ast.Tuple)
            or not expression.slice.elts[1:]
        ):
            return False
        module, _line = runtime.definition_location(supplier)
        if not types.source_module(module):
            return False
        scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, expression)
        )
        constructor = runtime.resolve_symbol(scope, expression.value)
        if not any(
            runtime.same_name(
                runtime.qualified_name(source_project, identity), constructor
            )
            for identity in ("typing.Annotated", "typing_extensions.Annotated")
        ):
            return False
        operand = runtime.annotation_origin(
            source_project, expression.slice.elts[0], scope
        )
        return operand is not None and types.abstract_class(operand.get_object())

    @staticmethod
    def class_kind(
        origin: p.Infra.RopeClassObject,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        source_project: p.Infra.RopeProject,
    ) -> c.Infra.FacadeMemberKind:
        """Classify native class ancestry and its declared structural contract.

        Returns:
            The class's owner kind, preserving direct protocol declarations.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(origin):
            # A typing form (pydantic's ConfigDict and siblings) is not a
            # class: it has no C3 ancestry to linearize and publishes as TYPE.
            return c.Infra.FacadeMemberKind.TYPE
        direct = FlextInfraUtilitiesDeclarationPayload.direct_bases(origin)
        if any(
            runtime.qualified_name(source_project, identity).get_object() in direct
            for identity in (
                "typing.TypedDict",
                "typing_extensions.TypedDict",
            )
        ):
            # TypedDict subclasses are typing forms by declaration; rope
            # cannot linearize their synthetic MRO and none is needed.
            return c.Infra.FacadeMemberKind.TYPE
        ancestry = FlextInfraUtilitiesDeclarationPayload.class_ancestry(origin)
        return FlextInfraUtilitiesFacadeMembers._class_kind_classified(
            origin,
            ancestry,
            resolver_factory=resolver_factory,
            source_project=source_project,
        )

    @classmethod
    def _class_kind_classified(
        cls,
        origin: p.Infra.RopePyObject,
        ancestry: Sequence[p.Infra.RopePyObject],
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        source_project: p.Infra.RopeProject,
    ) -> c.Infra.FacadeMemberKind:
        """Classify from the already-linearized native ancestry.

        Returns:
            The facade member kind for the native member.

        """
        kind = c.Infra.FacadeMemberKind
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if any(
            isinstance(ancestor, p.Infra.RopeBuiltinClass)
            and isinstance(ancestor.builtin, type)
            and issubclass(ancestor.builtin, BaseException)
            for ancestor in ancestry
        ):
            return kind.EXCEPTION
        if runtime.qualified_name(source_project, "enum.Enum").get_object() in ancestry:
            return kind.ENUM
        direct = FlextInfraUtilitiesDeclarationPayload.direct_bases(origin)
        if any(
            runtime.qualified_name(source_project, identity).get_object() in direct
            for identity in ("typing.Protocol", "typing_extensions.Protocol")
        ):
            return kind.PROTOCOL
        if FlextInfraUtilitiesFacadeMembers._model_class(
            origin,
            ancestry,
            resolver_factory=resolver_factory,
            source_project=source_project,
        ):
            return kind.MODEL
        own = (
            origin.get_scope().get_defined_names()
            if types.py_class(origin)
            else origin.get_attributes()
        )
        module = origin.get_module()
        return (
            kind.MODEL_DECLARATION
            if "__class_getitem__" not in own
            and module is not None
            and module.get_name()
            in config.Infra.tooling.facade_members.model_declaration_modules
            else kind.TYPE
        )

    @staticmethod
    def _model_class(
        origin: p.Infra.RopePyObject,
        ancestry: Sequence[p.Infra.RopePyObject],
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        source_project: p.Infra.RopeProject,
    ) -> bool:
        """Recognize the canonical structural model contract and native TypedDict.

        Returns:
            Whether the native declaration satisfies a model contract.

        Raises:
            ValueError: The canonical model protocol declares no public members.

        """
        model = resolver_factory()(
            f"{c.Infra.PKG_CORE_UNDERSCORE}.p.ModelType"
        ).get_object()
        required = frozenset(
            name for name in model.get_attributes() if not name.startswith("_")
        )
        if not required:
            message = "native model-type contract has no declared members"
            raise ValueError(message)
        return required.issubset(origin.get_attributes()) or any(
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                source_project, identity
            ).get_object()
            in ancestry
            for identity in ("typing.TypedDict", "typing_extensions.TypedDict")
        )

    @staticmethod
    def _typing_origin(
        value: p.Infra.RopePyName, *, source_project: p.Infra.RopeProject
    ) -> p.Infra.RopePyName:
        """Resolve alias origins for kind classification, never for value identity.

        Returns:
            The native alias origin, or the original non-alias declaration.

        Raises:
            ValueError: The declared alias origin cannot be proven.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.class_assignment_binding(value, classes_only=False)
        if binding is None:
            message = f"ambiguous facade declaration: {value.get_definition_location()}"
            raise ValueError(message)
        if (
            isinstance(binding, p.Infra.RopeImportedName)
            and binding.get_object()
            is runtime.runtime_callable("rope.base.pyobjects", "get_unknown")()
        ):
            resource = runtime.imported_module_resource(source_project, binding)
            provider = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                source_project, resource
            )
            resolved = FlextInfraUtilitiesImportLaw.resolve_declared_binding(
                source_project,
                provider.get_name(),
                binding.imported_name,
                Path(source_project.root.real_path),
                {},
            )
            if resolved is None:
                message = (
                    f"unproven lazy facade origin: "
                    f"{provider.get_name()}.{binding.imported_name}"
                )
                raise ValueError(message)
            binding = resolved
        alias = runtime.annotation_alias_definition(binding)
        if alias is None:
            return binding
        declaration, scope = alias
        origin = runtime.annotation_origin(source_project, declaration.value, scope)
        if origin is None:
            message = f"unproven facade alias origin: {declaration.name.id}"
            raise ValueError(message)
        return origin

    @classmethod
    def facade_member_owner(
        cls,
        value: p.Infra.RopePyName,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        source_project: p.Infra.RopeProject,
    ) -> str:
        """Return the configured owner of the member's native declaration.

        Returns:
            The owner letter declared for the member's kind.

        """
        return config.Infra.tooling.facade_members.owners[
            cls.facade_member_kind(
                value,
                resolver_factory=resolver_factory,
                source_project=source_project,
            )
        ]

    @classmethod
    def library_members_owned_by(
        cls,
        library: str,
        letters: Sequence[str],
        *,
        source_project: p.Infra.RopeProject,
    ) -> Mapping[str, t.StrTuple]:
        """Classify a library's public bindings once for the selected letters.

        Returns:
            Each selected letter's sorted public member names.

        Raises:
            ValueError: If the member's owner cannot be determined.

        """
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                source_project,
                sources=FlextInfraUtilitiesWorkspaceSnapshot.project_captured_sources(
                    source_project
                ),
            )
        )
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
            source_project.get_module(library)
        )
        # One native classification serves every requested owner letter.
        owned: dict[str, list[str]] = {letter: [] for letter in letters}
        for name, binding in module.get_attributes().items():
            if name.startswith("_"):
                continue
            try:
                owner = cls.facade_member_owner(
                    binding,
                    resolver_factory=resolver_factory,
                    source_project=source_project,
                )
            except ValueError as failure:
                failure.add_note(f"library-member-owner: {library}.{name}")
                raise
            if owner in owned:
                owned[owner].append(name)
        return {letter: tuple(sorted(names)) for letter, names in owned.items()}

    @staticmethod
    def specialized_aliases(
        package: str, *, source_project: p.Infra.RopeProject
    ) -> t.StrTuple:
        """Name the ``p`` aliases that specialize the same-named ``t`` generic.

        Read the injected source engine, never import the pre-migration package
        or evaluate an alias value. Native lazy routes and published class
        identities establish the receivers; PEP 695 declarations establish aliases.

        Returns:
            The sorted, statically proven specialization names.

        """
        facades = FlextInfraUtilitiesFacadeMembers.facade_source_classes(
            package,
            (c.Infra.FacadeFamily.P, c.Infra.FacadeFamily.T),
            source_project=source_project,
        )
        if not {c.Infra.FacadeFamily.P, c.Infra.FacadeFamily.T}.issubset(facades):
            return ()
        typings = facades[c.Infra.FacadeFamily.T].get_attributes()
        return tuple(
            sorted(
                name
                for name, binding in facades[c.Infra.FacadeFamily.P]
                .get_attributes()
                .items()
                if not name.startswith("_")
                and name in typings
                and FlextInfraUtilitiesFacadeMembers._specialization_alias_matches(
                    package, name, binding, typings[name]
                )
            )
        )

    @staticmethod
    def facade_source_classes(
        package: str,
        letters: Sequence[str],
        *,
        source_project: p.Infra.RopeProject,
    ) -> Mapping[str, p.Infra.RopeClassObject]:
        """Resolve exactly the requested published facade receivers from native source.

        Returns:
            Authenticated facades keyed by their published letters.

        Raises:
            ValueError: A receiver is a module or lacks a proven class publication.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        module = types.require_parsed_module(source_project.get_module(package))
        resource = module.get_resource()
        if isinstance(resource, p.Infra.RopeRoot):
            if not resource.has_child(c.Infra.INIT_PY):
                return {}
            resource = resource.get_child(c.Infra.INIT_PY)
        initializer = types.require_file_resource(resource, package)
        parsed = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            source_project, initializer
        )
        if not types.source_module(parsed):
            message = f"facade publisher has no native source tree: {package}"
            raise ValueError(message)
        routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
            package,
            Path(initializer.real_path),
            parsed.source_code,
            project=source_project,
            pymodule=parsed,
        )
        exports = frozenset(
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(parsed)
        )
        facades: dict[str, p.Infra.RopeClassObject] = {}
        view = (source_project, package, module, parsed, routes, exports)
        for letter in letters:
            target = FlextInfraUtilitiesFacadeMembers._published_letter_facade(
                view, letter
            )
            if target is not None:
                facades[letter] = target
        return facades

    @staticmethod
    def _published_letter_facade(
        view: tuple[
            p.Infra.RopeProject,
            str,
            p.Infra.RopeParsedModule,
            p.Infra.RopeSourceModule,
            Mapping[str, m.Infra.SourceClassReference],
            frozenset[str],
        ],
        letter: str,
    ) -> p.Infra.RopeClassObject | None:
        """Authenticate one letter's specialization facade publication.

        Returns:
            The published native facade class, or an unpublished letter.

        Raises:
            ValueError: A receiver is a module or lacks a proven publication.

        """
        source_project, package, module, _parsed, routes, _exports = view
        route = routes.get(letter)
        if route is not None and not route.attributes:
            message = f"specialization facade publishes a module: {package}.{letter}"
            raise ValueError(message)
        try:
            binding = (
                FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                    source_project,
                    ".".join(route.attributes),
                    module_name=route.target,
                )
                if route is not None
                else module.get_attributes().get(letter)
            )
        except rope_exceptions.AttributeNotFoundError:
            # A rota aponta para um destino stageado cuja publicação ainda
            # não existe na fonte: a letra segue não publicada nesta vista.
            return None
        target = None if binding is None else binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(target):
            # Um binding que não é classe (módulo stageado, parcial) não é
            # publicação: a letra segue não publicada nesta vista.
            return None
        owner = target.get_module()
        observed_owner = (
            FlextInfraUtilitiesRopeAnalysisImportState.published_facade_owner(
                source_project,
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    None if owner is None else owner.get_resource(),
                    f"{package}.{letter}",
                ),
            )
        )
        expected_owner = (letter, target.get_name())
        if observed_owner != expected_owner:
            message = f"unproven specialization publication: {package}.{letter}"
            failure = ValueError(message)
            failure.add_note(
                f"route_target={None if route is None else route.target}; "
                f"route_attributes={None if route is None else route.attributes}; "
                f"binding_type={type(binding).__qualname__}; "
                f"expected_owner={expected_owner}; observed_owner={observed_owner}"
            )
            raise failure
        return target

    @staticmethod
    def _specialization_alias_matches(
        package: str,
        name: str,
        binding: p.Infra.RopePyName,
        typing: p.Infra.RopePyName,
    ) -> bool:
        """Compare one protocol alias's immediate origin with its typing binding.

        Returns:
            Whether both declarations identify the same native generic.

        Raises:
            ValueError: A candidate alias or its origin has no static identity.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        alias = runtime.annotation_alias_definition(binding)
        if alias is None:
            value = binding.get_object()
            if not (types.abstract_class(value) or types.py_function(value)):
                message = f"unproven specialization alias: {package}.p.{name}"
                raise ValueError(message)
            return False
        declaration, scope = alias
        if not isinstance(declaration.value, ast.Subscript):
            return False
        origin = runtime.resolve_symbol(scope, declaration.value.value)
        if origin is None:
            message = f"unresolved specialization origin: {package}.p.{name}"
            raise ValueError(message)
        generic = runtime.annotation_alias_definition(typing)
        actual = runtime.annotation_alias_definition(origin)
        if (generic is None and not types.abstract_class(typing.get_object())) or (
            actual is None and not types.abstract_class(origin.get_object())
        ):
            message = f"unproven specialization identity: {package}.p.{name}"
            raise ValueError(message)
        if generic is not None and actual is not None:
            return generic[0] is actual[0]
        return runtime.same_name(typing, origin)

    @classmethod
    def facade_source_members(
        cls, facade: p.Infra.RopeClassObject, *, source_project: p.Infra.RopeProject
    ) -> Mapping[str, p.Infra.RopePyName]:
        """Read the inherited bindings selected by the native class object.

        Returns:
            Public native member bindings selected by the source MRO.

        """
        del cls, source_project
        attributes = facade.get_attributes()
        return {
            name: binding
            for name, binding in attributes.items()
            if not name.startswith("_")
        }

    @classmethod
    def facade_member_placement(
        cls,
        reference: tuple[str, str, str],
        *,
        facades: Mapping[str, p.Infra.RopeClassObject],
        bindings: Mapping[str, Mapping[str, p.Infra.RopePyName]],
        scope: t.Infra.FacadeMemberScope,
    ) -> c.Infra.FacadeMemberPlacement | None:
        """Classify a foreign member's actual placement through native bindings.

        ``reference`` identifies the package, facade letter and member name.
        ``EXPOSED`` holds when the owner already binds the identical object,
        so the duplicate is retired automatically. ``MISSING`` holds when the
        owner binds nothing under that name yet: the declaration moves to the
        owner family before consumers relocate.

        Returns:
            The proven foreign placement, or no foreign member at this receiver.

        Raises:
            ValueError: A facade member has no proven native declaration kind.

        """
        resolver_factory, source_project, declarations = scope
        package, letter, member = reference
        if member.startswith("_"):
            return None
        facade = facades.get(letter)
        if facade is None or not cls.declared_by_package(
            facade,
            member,
            package,
            source_project=source_project,
            declarations=None if declarations is None else declarations[letter],
        ):
            return None
        value = bindings[letter][member]
        try:
            owner = cls.facade_member_owner(
                value,
                resolver_factory=resolver_factory,
                source_project=source_project,
            )
        except ValueError as failure:
            failure.add_note(f"Facade census reference: {package}.{letter}.{member}")
            raise
        members: Mapping[str, p.Infra.RopePyName] = bindings.get(owner, {})
        bound = member in members
        if owner != letter and bound and cls._same_binding(members[member], value):
            return c.Infra.FacadeMemberPlacement.EXPOSED
        kind = cls.facade_member_kind(
            value,
            resolver_factory=resolver_factory,
            source_project=source_project,
        )
        # A ``type`` alias is a type declaration by construction (t), except an
        # alias of a structural contract, which p owns; only a strongly typed
        # object whose owner binds nothing yet must move.
        alias_kind = (
            c.Infra.FacadeMemberKind.PROTOCOL
            if kind is c.Infra.FacadeMemberKind.PROTOCOL
            else c.Infra.FacadeMemberKind.TYPE
        )
        declared_owner = (
            config.Infra.tooling.facade_members.owners[alias_kind]
            if FlextInfraUtilitiesRopeRuntimeModules.annotation_alias_definition(value)
            is not None
            else owner
        )
        return (
            c.Infra.FacadeMemberPlacement.MISSING
            if declared_owner != letter and not bound
            else None
        )

    @classmethod
    def facade_member_census(
        cls, project: Path, *, source_project: p.Infra.RopeProject
    ) -> tuple[
        Sequence[str],
        Mapping[str, frozenset[str]],
        Mapping[str, frozenset[str]],
    ]:
        """Derive every foreign facade reference over the project's lineage.

        A member a non-owner facade letter re-exports while its owner binds
        the identical object yields one exact ``letter.member`` reference
        under its owner letter; the project's own duplicates also yield their
        name under the non-owner letter that declares them. A member the
        owner letter declares for its own kind also yields the reference of
        every other letter that binds no object, or the identical object,
        under that name: the consumer still spelling the retired receiver
        moves to the owner. References are derived over the core facade
        package, the project's package and every package its facades inherit
        from, so a consumer relocates inherited duplicates too. A facade whose
        ancestry cannot be proven from source fails here, loudly.

        Returns:
            The lineage packages, the references by owner letter and the
            project's duplicate names by declaring letter.

        """
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                source_project,
                sources=FlextInfraUtilitiesWorkspaceSnapshot.project_captured_sources(
                    source_project
                ),
            )
        )
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        lineage = cls.facade_member_lineage(
            package, letters, source_project=source_project
        )
        references: dict[str, set[str]] = {}
        names: dict[str, set[str]] = {}
        for root in lineage:
            facades = cls.facade_source_classes(
                root, letters, source_project=source_project
            )
            bindings = {
                letter: cls.facade_source_members(facade, source_project=source_project)
                for letter, facade in facades.items()
            }
            declarations = {
                letter: cls.facade_member_declarations(facade)
                for letter, facade in facades.items()
            }
            for letter, members in bindings.items():
                for member, value in members.items():
                    if (
                        cls.facade_member_placement(
                            (root, letter, member),
                            facades=facades,
                            bindings=bindings,
                            scope=(resolver_factory, source_project, declarations),
                        )
                        is not c.Infra.FacadeMemberPlacement.EXPOSED
                    ):
                        continue
                    owner = cls.facade_member_owner(
                        value,
                        resolver_factory=resolver_factory,
                        source_project=source_project,
                    )
                    references.setdefault(owner, set()).add(f"{letter}.{member}")
                    if root == package:
                        names.setdefault(letter, set()).add(member)
            for owner, reference in cls._owned_references(
                root,
                facades,
                bindings,
                scope=(resolver_factory, source_project, declarations),
            ):
                references.setdefault(owner, set()).add(reference)
        return (
            lineage,
            {owner: frozenset(found) for owner, found in sorted(references.items())},
            {letter: frozenset(found) for letter, found in sorted(names.items())},
        )

    @classmethod
    def facade_member_lineage(
        cls,
        package: str,
        letters: Sequence[str],
        *,
        source_project: p.Infra.RopeProject,
    ) -> t.StrTuple:
        """Name the core package, ``package`` and every package its facades extend.

        Publisher identities retain their complete qualified package path.
        Missing native declarations fail instead of importing the target.

        Returns:
            The facade-publishing root packages of the composition lineage.

        """
        publishers = {c.Infra.PKG_CORE_UNDERSCORE, package}
        for facade in cls.facade_source_classes(
            package, letters, source_project=source_project
        ).values():
            ancestry = FlextInfraUtilitiesDeclarationPayload.class_ancestry(facade)
            for ancestor in ancestry:
                module = ancestor.get_module()
                if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
                    continue
                exports = FlextInfraUtilitiesRopeAnalysisExports
                exported = exports.public_export_names_source(module)
                if not frozenset(letters).intersection(exported):
                    continue
                state = FlextInfraUtilitiesRopeAnalysisImportState
                published = state.published_facade_owner(
                    source_project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        module.get_resource(), module.get_name()
                    ),
                )
                if published is not None and published[0] in letters:
                    publishers.add(
                        FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                            module, source_project=source_project
                        ).rpartition(".")[0]
                    )
        return tuple(
            publisher
            for publisher in sorted(publishers)
            if cls.facade_source_classes(
                publisher, letters, source_project=source_project
            )
        )

    @staticmethod
    def facade_member_family_files(root: Path) -> Mapping[str, Sequence[str]]:
        """Group the project's facade-family files by the letter they produce.

        Returns:
            Native globs of each letter's family files.

        """
        families: dict[str, list[str]] = {}
        for path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
            root, workspace_excluded_top_dirs=frozenset()
        ):
            relative = path.relative_to(root)
            letter = FlextInfraUtilitiesCodegenNamespace.facade_family_of_source(
                relative
            )
            if letter is not None:
                families.setdefault(letter, []).append(f"**/{relative.as_posix()}")
        return {letter: tuple(sorted(found)) for letter, found in families.items()}

    @classmethod
    def _owned_references(
        cls,
        root: str,
        facades: Mapping[str, p.Infra.RopeClassObject],
        bindings: Mapping[str, Mapping[str, p.Infra.RopePyName]],
        *,
        scope: t.Infra.FacadeMemberScope,
    ) -> Sequence[tuple[str, str]]:
        """Reference every owned member through each other letter of ``root``.

        A letter that binds no object, or the owner's identical object, under
        the member's name is a receiver the consumer relocates to the owner.

        Returns:
            Each owner letter with one foreign ``letter.member`` reference.

        """
        return tuple(
            (owner, f"{letter}.{member}")
            for owner, value, member in cls._owned_members(
                root,
                facades,
                bindings,
                scope=scope,
            )
            for letter, members in bindings.items()
            if letter != owner
            and (member not in members or cls._same_binding(members[member], value))
        )

    @classmethod
    def _owned_members(
        cls,
        root: str,
        facades: Mapping[str, p.Infra.RopeClassObject],
        bindings: Mapping[str, Mapping[str, p.Infra.RopePyName]],
        *,
        scope: t.Infra.FacadeMemberScope,
    ) -> Sequence[tuple[str, p.Infra.RopePyName, str]]:
        """Collect each public member a letter of ``root`` declares as owner.

        Returns:
            The owner letter, the bound object and the member name.

        """
        resolver_factory, source_project, declarations = scope
        owned: list[tuple[str, p.Infra.RopePyName, str]] = []
        for owner, facade in facades.items():
            for member, value in bindings[owner].items():
                if not cls.declared_by_package(
                    facade,
                    member,
                    root,
                    source_project=source_project,
                    declarations=None if declarations is None else declarations[owner],
                ):
                    continue
                if (
                    cls.facade_member_owner(
                        value,
                        resolver_factory=resolver_factory,
                        source_project=source_project,
                    )
                    == owner
                ):
                    owned.append((owner, value, member))
        return tuple(owned)

    @classmethod
    def codemod_facade_member_ownership_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Render the retirement and wrong-layer rules, one document per letter.

        A family module of letter ``L`` declaring a member another letter owns
        is a duplicate to retire when the owner already binds the identical
        object, and a misplaced declaration while the owner binds nothing
        under that name; both name sets come from the project's native source
        facades, and each document is scoped to the exact family files of
        its letter.

        Returns:
            The rendered rule documents keyed by rule id.

        """
        root = project.absolute()
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        _lineage, _references, exposed = cls.facade_member_census(
            root, source_project=snapshot.engine
        )
        missing = cls._misplaced_members(package, source_project=snapshot.engine)
        families = cls.facade_member_family_files(root)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        documents: dict[str, t.JsonMapping] = {}
        shapes = (
            (
                c.Infra.FACADE_MEMBER_RETIRE_SHAPE,
                exposed,
                {"severity": "error", "fix": ""},
                (
                    "`$NAME` is re-exported by a facade that does not own it: "
                    "`make mod` deletes this duplicate and relocates every consumer "
                    "to the owner."
                ),
            ),
            (
                c.Infra.FACADE_MEMBER_WRONG_LAYER_SHAPE,
                missing,
                {"severity": "warning"},
                (
                    "`$NAME` is declared in a facade layer that does not own its "
                    "kind: move this declaration into the owner family's module."
                ),
            ),
        )
        for shape, names, effect, message in shapes:
            for letter, found in sorted(names.items()):
                files = list[t.JsonValue](sorted(families.get(letter, ())))
                if not files or not found:
                    continue
                rule_id = f"{shape}{separator}{package}{separator}{letter}"
                documents[rule_id] = {
                    "id": rule_id,
                    "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                    **effect,
                    "files": files,
                    "constraints": {
                        c.Infra.FACADE_MEMBER_NAME_VAR: {
                            "regex": cls.exact_alternation(sorted(found))
                        }
                    },
                    "utils": {
                        "class-member": {
                            "kind": "block",
                            "inside": {"kind": "class_definition"},
                        }
                    },
                    "rule": cls._class_member_declaration(),
                    "message": message,
                }
        return documents

    @staticmethod
    def _class_member_declaration() -> t.JsonDict:
        """Match an assignment or type alias statement in a class body.

        Returns:
            The native rule capturing the declared name as ``$NAME``.

        """
        name = f"${c.Infra.FACADE_MEMBER_NAME_VAR}"
        return {
            "any": [
                {
                    "kind": "expression_statement",
                    "has": {
                        "kind": "assignment",
                        "has": {"field": "left", "kind": "identifier", "pattern": name},
                    },
                    "inside": {"matches": "class-member"},
                },
                {
                    "kind": "type_alias_statement",
                    "has": {
                        "field": "left",
                        "has": {"kind": "identifier", "pattern": name},
                    },
                    "inside": {"matches": "class-member"},
                },
            ]
        }

    @classmethod
    def _misplaced_members(
        cls, package: str, *, source_project: p.Infra.RopeProject
    ) -> Mapping[str, frozenset[str]]:
        """Collect each letter's members whose owner binds nothing under the name.

        Returns:
            The misplaced member names by declaring letter; empty for a
            package that declares no facade receivers.

        """
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                source_project,
                sources=FlextInfraUtilitiesWorkspaceSnapshot.project_captured_sources(
                    source_project
                ),
            )
        )
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        facades = cls.facade_source_classes(
            package, letters, source_project=source_project
        )
        bindings = {
            letter: cls.facade_source_members(facade, source_project=source_project)
            for letter, facade in facades.items()
        }
        found: dict[str, frozenset[str]] = {}
        for letter, members in bindings.items():
            names = frozenset(
                member
                for member in members
                if cls.facade_member_placement(
                    (package, letter, member),
                    facades=facades,
                    bindings=bindings,
                    scope=(resolver_factory, source_project, None),
                )
                is c.Infra.FacadeMemberPlacement.MISSING
            )
            if names:
                found[letter] = names
        return found

    @classmethod
    def codemod_facade_member_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Render the one rule relocating every foreign facade reference.

        A reference matches only as one of the exact foreign ``letter.member``
        texts of the census, through a receiver letter and an owner letter a
        module-level import from the lineage or the project's own packages
        binds, neither rebound at module level nor shadowed by an enclosing
        function's parameters, and never assigned through. Inside ``Literal``
        type data it never moves; inside ``Annotated`` only the callable of a
        complete metadata call does. One rewriter per owner letter emits the
        owner reference.

        Returns:
            The single native rule document keyed by its rule id, or nothing
            when the lineage re-exports no foreign member.

        """
        lineage, references, _names = cls.facade_member_census(
            project, source_project=snapshot.engine
        )
        if not references:
            return {}
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(project)
        sources = sorted({
            *lineage,
            *FlextInfraUtilitiesCodemodNative.codemod_own_package_names(project),
        })
        rule_id = (
            f"{c.Infra.FACADE_MEMBER_RELOCATE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        variable = c.Infra.FACADE_MEMBER_REFERENCE_VAR
        owners = {
            owner: cls.exact_alternation(sorted(found))
            for owner, found in references.items()
        }
        return {
            rule_id: {
                "id": rule_id,
                "language": "python",
                "severity": "error",
                "rule": {
                    "all": [
                        {"kind": "attribute"},
                        {"pattern": f"${variable}"},
                        {"pattern": "$RECEIVER.$MEMBER"},
                        {
                            "has": {
                                "field": "object",
                                "all": [
                                    {"pattern": "$RECEIVER"},
                                    cls.facade_letter_bound_rule(
                                        {"pattern": "$RECEIVER"}, sources
                                    ),
                                ],
                            }
                        },
                        {
                            "any": [
                                {
                                    "regex": pattern,
                                    "all": [
                                        cls.facade_letter_bound_rule(
                                            {"regex": f"^{re.escape(owner)}$"},
                                            sources,
                                        ),
                                        {
                                            "not": {
                                                "inside": {
                                                    "kind": "module",
                                                    "stopBy": "end",
                                                    "has": {
                                                        "kind": "assignment",
                                                        "stopBy": "end",
                                                        "has": {
                                                            "field": "left",
                                                            "pattern": (
                                                                f"{owner}.$MEMBER"
                                                            ),
                                                        },
                                                    },
                                                }
                                            }
                                        },
                                    ],
                                }
                                for owner, pattern in owners.items()
                            ]
                        },
                        {
                            "not": {
                                "inside": {
                                    "kind": "module",
                                    "stopBy": "end",
                                    "has": {
                                        "kind": "assignment",
                                        "stopBy": "end",
                                        "has": {
                                            "field": "left",
                                            "pattern": f"${variable}",
                                        },
                                    },
                                }
                            }
                        },
                        {
                            "not": {
                                "inside": {
                                    "kind": "subscript",
                                    "stopBy": "end",
                                    "has": {
                                        "field": "value",
                                        "regex": r"^(?:typing\.)?Literal$",
                                    },
                                }
                            }
                        },
                        {
                            "any": [
                                {
                                    "not": {
                                        "inside": {
                                            "kind": "subscript",
                                            "stopBy": "end",
                                            "has": {
                                                "field": "value",
                                                "regex": r"^(?:typing\.)?Annotated$",
                                            },
                                        }
                                    }
                                },
                                {
                                    "inside": {
                                        "kind": "call",
                                        "field": "function",
                                        "nthChild": {"position": "n+3"},
                                        "inside": {
                                            "kind": "subscript",
                                            "has": {
                                                "field": "value",
                                                "regex": r"^(?:typing\.)?Annotated$",
                                            },
                                        },
                                    }
                                },
                            ]
                        },
                    ]
                },
                "rewriters": [
                    {
                        "id": f"to-{owner}",
                        "rule": {"regex": pattern, "pattern": "$LETTER.$MEMBER"},
                        "fix": f"{owner}.$MEMBER",
                    }
                    for owner, pattern in owners.items()
                ],
                "transform": {
                    "OWNED": {
                        "rewrite": {
                            "source": f"${variable}",
                            "rewriters": [f"to-{owner}" for owner in owners],
                        }
                    }
                },
                "fix": "$OWNED",
                "message": (
                    f"Consume `${variable}` through its owner facade: `$OWNED`."
                ),
            }
        }

    @staticmethod
    def facade_letter_bound_rule(
        name: t.JsonMapping, sources: Sequence[str]
    ) -> t.JsonDict:
        """Match where a module-level facade import binds a letter unshadowed.

        ``name`` is the native rule of the letter's spelling: an exact regex
        or the pattern of a captured metavariable. The import comes from one
        of ``sources`` or is package-relative; the module never rebinds the
        letter at its top level and no enclosing function declares it as a
        parameter.

        Returns:
            The native rule of a stable module-level facade letter binding.

        """
        packages = "|".join(re.escape(source) for source in sources)
        return {
            "all": [
                {
                    "inside": {
                        "kind": "module",
                        "stopBy": "end",
                        "all": [
                            {
                                "has": {
                                    "kind": "import_from_statement",
                                    "all": [
                                        {
                                            "any": [
                                                {
                                                    "has": {
                                                        "field": "module_name",
                                                        "kind": "dotted_name",
                                                        "regex": (
                                                            rf"^(?:{packages})(?:\.|$)"
                                                        ),
                                                    }
                                                },
                                                {
                                                    "has": {
                                                        "field": "module_name",
                                                        "kind": "relative_import",
                                                    }
                                                },
                                            ]
                                        },
                                        {
                                            "any": [
                                                {
                                                    "has": {
                                                        "kind": "dotted_name",
                                                        "not": {
                                                            "inside": {
                                                                "kind": (
                                                                    "aliased_import"
                                                                )
                                                            }
                                                        },
                                                        **name,
                                                    }
                                                },
                                                {
                                                    "has": {
                                                        "kind": "aliased_import",
                                                        "has": {
                                                            "field": "alias",
                                                            **name,
                                                        },
                                                    }
                                                },
                                            ]
                                        },
                                    ],
                                }
                            },
                            {
                                "not": {
                                    "has": {
                                        "any": [
                                            {
                                                "kind": "expression_statement",
                                                "has": {
                                                    "kind": "assignment",
                                                    "has": {"field": "left", **name},
                                                },
                                            },
                                            {
                                                "kind": "class_definition",
                                                "has": {"field": "name", **name},
                                            },
                                            {
                                                "kind": "function_definition",
                                                "has": {"field": "name", **name},
                                            },
                                        ]
                                    }
                                }
                            },
                        ],
                    }
                },
                {
                    "not": {
                        "inside": {
                            "kind": "function_definition",
                            "stopBy": "end",
                            "has": {
                                "field": "parameters",
                                "has": {
                                    "any": [
                                        {"kind": "identifier", **name},
                                        {
                                            "any": [
                                                {"kind": "typed_parameter"},
                                                {"kind": "list_splat_pattern"},
                                                {"kind": "dictionary_splat_pattern"},
                                            ],
                                            "has": {
                                                "kind": "identifier",
                                                "nthChild": 1,
                                                **name,
                                            },
                                        },
                                        {
                                            "any": [
                                                {"kind": "default_parameter"},
                                                {"kind": "typed_default_parameter"},
                                            ],
                                            "has": {"field": "name", **name},
                                        },
                                    ]
                                },
                            },
                        }
                    }
                },
            ]
        }

    @staticmethod
    def exact_alternation(texts: Sequence[str]) -> str:
        """Anchor an exact, sorted alternation of literal texts.

        Returns:
            A regex matching exactly one of ``texts``.

        """
        return "^(?:" + "|".join(re.escape(text) for text in texts) + ")$"

    @staticmethod
    def facade_member_declarations(
        facade: p.Infra.RopeClassObject,
    ) -> Mapping[str, Sequence[p.Infra.RopePyObject]]:
        """Collect each member's declaring ancestors in the current source view.

        Returns:
            The shared declaration inventory, retaining native object identities.

        """
        declared: dict[str, list[p.Infra.RopePyObject]] = {}
        for ancestor in FlextInfraUtilitiesDeclarationPayload.class_ancestry(facade):
            members = (
                ancestor.get_scope().get_defined_names()
                if FlextInfraUtilitiesRopeRuntimeTypes.py_class(ancestor)
                else ancestor.get_attributes()
            )
            for member in members:
                declared.setdefault(member, []).append(ancestor)
        return declared

    @staticmethod
    def declared_by_package(
        facade: p.Infra.RopeClassObject,
        member: str,
        package: str,
        *,
        source_project: p.Infra.RopeProject,
        declarations: Mapping[str, Sequence[p.Infra.RopePyObject]] | None = None,
    ) -> bool:
        """Whether a class of ``package`` declares ``member`` in the facade MRO.

        Members a facade inherits from a third-party base (``model_dump`` from
        the model library) are that library's surface, not a re-export, and so
        are overrides of such members (``model_config``).

        Returns:
            Whether only classes of the package bind ``member`` in the MRO.

        """
        holders = (
            FlextInfraUtilitiesFacadeMembers.facade_member_declarations(facade)
            if declarations is None
            else declarations
        ).get(member, ())
        return bool(holders) and all(
            (module := ancestor.get_module()) is not None
            and (
                (
                    name
                    := FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                        module, source_project=source_project
                    )
                )
                == package
                or name.startswith(f"{package}.")
            )
            for ancestor in holders
        )

    @staticmethod
    def _same_binding(
        left: p.Infra.RopePyName,
        right: p.Infra.RopePyName,
    ) -> bool:
        """Prove declaration or nominal identity without erasing generic arguments.

        Returns:
            Whether both names have the exact same proven source identity.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        aliases = tuple(
            runtime.annotation_alias_definition(value) for value in (left, right)
        )
        if aliases[0] is not None or aliases[1] is not None:
            return (
                aliases[0] is not None
                and aliases[1] is not None
                and aliases[0][0] is aliases[1][0]
            )
        if runtime.same_name(left, right):
            return True
        values = (left.get_object(), right.get_object())
        if all(
            types.abstract_class(value) or types.py_function(value) for value in values
        ):
            return values[0] is values[1]
        return False


__all__: list[str] = ["FlextInfraUtilitiesFacadeMembers"]
