"""Project consumed model data contracts from authenticated native sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from itertools import chain
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesSemanticCutover,
)
from flext_infra._utilities._git import FlextInfraUtilitiesGitignore
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesModelsProtocol:
    """Restore the source projection removed in 7a76fa5a9c, without its CLI."""

    @classmethod
    def protocol_model_sources(
        cls, workspace: p.Infra.RopeWorkspaceDsl
    ) -> Mapping[Path, str]:
        """Return protocol sources without importing or publishing the target.

        Returns:
            Relative generated paths and their source-owned structural declarations.

        """
        return cls._ModelProtocolProjection(workspace).render()

    class _ModelProtocolProjection(
        FlextInfraUtilitiesSemanticCutover,
    ):
        """Bind the retired native inventory and renderer to one source candidate."""

        def __init__(self, workspace: p.Infra.RopeWorkspaceDsl) -> None:
            self.workspace = workspace
            self.project = workspace.rope_project
            self.models: dict[str, p.Infra.RopePyName] = {}
            self.facades: dict[str, p.Infra.RopePyName] = {}
            self.package: Path | None = None
            self.package_name = ""
            self.class_stem = ""
            self.imports: dict[str, str] = {}
            self.selected: set[str] = set()
            self.references: dict[str, str] = {}
            self.parameters: set[str] = set()
            self.type_parameters: dict[str, list[t.Infra.AstTypeParameter]] = {}
            self.dependencies: set[str] = set()
            self.member_cache: dict[str, p.Infra.RopePyName | None] = {}

        def render(self) -> Mapping[Path, str]:
            """Close consumed model identities and render their native namespaces.

            Returns:
                Generated data contracts grouped by their published namespace.

            Raises:
                ValueError: If native models compete for one protocol destination.

            """
            self._inventory()
            if self.package is None or not {"m", "p"}.issubset(self.facades):
                return {}
            self.selected.update(self._consumed())
            declarations: dict[str, list[t.Infra.AstStatement]] = {}
            imports: dict[str, dict[str, str]] = {}
            dependencies: dict[str, set[str]] = {}
            while pending := sorted(self.selected - declarations.keys()):
                for route in pending:
                    self.imports = {
                        "future": "from __future__ import annotations",
                        "protocol": "from typing import Protocol, runtime_checkable",
                    }
                    self.dependencies = set()
                    declarations[route] = self._fields(self.models[route])
                    self.type_parameters[route] = self._type_parameters(
                        self.models[route]
                    )
                    imports[route] = self.imports
                    dependencies[route] = self.dependencies
            rendered: dict[Path, str] = {}
            for route in sorted(declarations):
                path, source = self._render_route(
                    route, declarations[route], imports[route], dependencies[route]
                )
                previous = rendered.setdefault(path, source)
                if previous != source:
                    message = f"competing native model protocol destinations: {path}"
                    raise ValueError(message)
            return rendered

        def _render_route(
            self,
            route: str,
            declaration: list[t.Infra.AstStatement],
            imports: dict[str, str],
            dependencies: set[str],
        ) -> tuple[Path, str]:
            """Render one closed model under its generated protocol owner.

            Returns:
                The relative destination and generated source.

            Raises:
                ValueError: If no package was inventoried.

            """
            if self.package is None:
                message = "protocol projection has no inventoried package"
                raise ValueError(message)
            directory = self.package / (
                FlextInfraUtilitiesCodegenNamespace.facade_families()["p"].directory
            )
            owner = self.references[route].partition(".")[0]
            siblings = tuple(
                sorted(
                    {
                        self.references[dependency].partition(".")[0]
                        for dependency in dependencies
                    }
                    - {owner}
                )
            )
            token = route.replace(".", "_").lower()
            destination = directory / (
                f"generated_models_{token}.py" if token else "generated_models.py"
            )
            selected_imports = dict(imports)
            if siblings:
                selected_imports["protocol"] = (
                    "from typing import TYPE_CHECKING, Protocol, runtime_checkable"
                )
            # Field extraction still supplies legacy expression nodes. Convert
            # them once at this boundary; module structure is template-owned.
            context = m.Infra.ModelProtocolRenderContext(
                header=c.Infra.AUTOGEN_HEADER,
                copyright_notice=FlextInfraUtilitiesLintRecipes.copyright_notice(
                    self.package,
                    module=destination,
                    source_project=self.project,
                ),
                imports=tuple(sorted(set(selected_imports.values()))),
                sibling_import_lines=tuple(
                    FlextInfraUtilitiesLazyInitRender.source_import_lines(
                        "    ", f"{self.package_name}.{directory.name}", siblings
                    )
                )
                if siblings
                else (),
                owner=owner,
                name=route.rpartition(".")[2],
                type_parameters=tuple(
                    FlextInfraUtilitiesRopeAnalysis.Tree.unparse(
                        FlextInfraUtilitiesRopeAnalysis.Tree.fix_missing_locations(
                            parameter
                        )
                    )
                    for parameter in self.type_parameters[route]
                ),
                declarations=tuple(
                    FlextInfraUtilitiesRopeAnalysis.Tree.unparse(
                        FlextInfraUtilitiesRopeAnalysis.Tree.fix_missing_locations(
                            field
                        )
                    )
                    for field in declaration
                ),
            )
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL
            )
            content = u.Cli.template_render(template, context).unwrap()
            return (
                destination.relative_to(self.workspace.repository_root),
                content,
            )

        def _inventory(self) -> None:
            """Elect explicit facade exports and retain native model identities."""
            layout = FlextInfraUtilitiesCodegenNamespace.layout(
                self.workspace.repository_root, rope_project=self.project
            )
            if layout is None:
                return
            self.package_name = layout.package_name
            self.class_stem = layout.class_stem
            self.package = layout.package_dir
            self._inventory_facades()
            if not {"m", "p"}.issubset(self.facades):
                return
            self._inventory_models()
            for route in self.models:
                namespace, _, leaf = route.rpartition(".")
                owner = (
                    f"{self.class_stem}{namespace.replace('.', '')}"
                    f"ProtocolsGeneratedModels{leaf}"
                )
                self.references[route] = f"{owner}.{leaf}"

        def _inventory_facades(self) -> None:
            """Elect the native model and protocol exports in this package.

            Raises:
                TypeError: An indexed protocol file is not a native source module.
                ValueError: If an indexed source resource is unavailable.

            """
            for entry in self.workspace.modules():
                if entry.package_dir != self.package:
                    continue
                resource = self.workspace.resource(entry.file_path)
                if resource is None:
                    message = (
                        f"indexed protocol input is unavailable: {entry.file_path}"
                    )
                    raise ValueError(message)
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self.project, resource
                )
                if not self.source_module(module):
                    message = (
                        f"indexed protocol file is not a source module: "
                        f"{entry.file_path}"
                    )
                    raise TypeError(message)
                if not {"m", "p"}.intersection(
                    FlextInfraUtilitiesRopeAnalysis.public_export_names_source(module)
                ):
                    continue
                owner = (FlextInfraUtilitiesRopeAnalysis.published_facade_owner)(
                    self.project, resource
                )
                if owner is not None and owner[0] in {"m", "p"}:
                    self.facades[owner[0]] = module.get_attribute(owner[1])
                    self.package = entry.package_dir

        def _inventory_models(self) -> None:
            """Close native model identities through their published namespaces.

            Raises:
                ValueError: If a route names competing model identities.

            """
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            pending: list[
                tuple[
                    str,
                    p.Infra.RopePyName,
                    tuple[p.Infra.RopePyObject, ...],
                ]
            ] = [("", self.facades["m"], ())]
            while pending:
                prefix, binding, ancestors = pending.pop()
                value = binding.get_object()
                if not self.py_class(value) or value in ancestors:
                    continue
                for name in sorted(value.get_attributes()):
                    if name.startswith("_"):
                        continue
                    member = self._member(binding, name)
                    if member is None or not self.py_class(member.get_object()):
                        continue
                    child = member.get_object()
                    route = f"{prefix}{name}"
                    if model_base in self.class_ancestry(child):
                        previous = self.models.setdefault(route, member)
                        if not self.same_name(previous, member):
                            message = f"competing model identities for p.{route}"
                            raise ValueError(message)
                    pending.append((f"{route}.", member, (*ancestors, value)))

        def _consumed(self) -> set[str]:
            """Read protocol primaries through native scope identities, not names.

            Returns:
                Consumed models not already owned by an authored operational port.

            Raises:
                ValueError: If an indexed consumer resource is unavailable.

            """
            selected: set[str] = set()
            facade = self.facades["p"]
            for entry in self.workspace.modules():
                resource = self.workspace.resource(entry.file_path)
                if resource is None:
                    message = (
                        f"indexed protocol consumer is unavailable: {entry.file_path}"
                    )
                    raise ValueError(message)
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self.project, resource
                )
                source = module.source_code
                if source.startswith(c.Infra.AUTOGEN_HEADER):
                    continue
                references = FlextInfraUtilitiesSemanticFamilyTypeReferences
                primaries = (
                    (source[begin:end], self.scope_at(module, begin))
                    for begin, end in references.reference_regions(source)
                )
                quoted = (
                    (expression[begin:end], scope)
                    for expression, scope, _line in (
                        references.scoped_quoted_type_references(
                            source, self.project, module
                        )
                    )
                    for begin, end in references.reference_regions(expression)
                )
                for primary, scope in chain(primaries, quoted):
                    root, separator, route = primary.partition(".")
                    if not separator or route not in self.models:
                        continue
                    reference = self.expression_name(scope, root)
                    if not (
                        self.same_name(facade, reference)
                        or self.same_name(self.facades["m"], reference)
                    ):
                        continue
                    if route not in self.member_cache:
                        self.member_cache[route] = self._member(facade, route)
                    port = self.member_cache[route]
                    owner = port.get_object().get_module() if port is not None else None
                    if owner is None or (
                        self.source_module(owner)
                        and owner.source_code.startswith(c.Infra.AUTOGEN_HEADER)
                    ):
                        selected.add(route)
            return selected

        def _fields(self, binding: p.Infra.RopePyName) -> list[t.Infra.AstStatement]:
            """Retain inherited annotated data, never defaults or model methods.

            Returns:
                Annotated attributes in native C3 override order.

            Raises:
                TypeError: If a model declaration is absent.

            """
            fields: dict[str, t.Infra.AstStatement] = {}
            source = self._source_class(binding)
            definition = source.get_ast()
            if not isinstance(
                definition, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef
            ):
                message = "model has no authenticated class declaration"
                raise TypeError(message)
            self.parameters = {
                parameter.name
                for parameter in definition.type_params
                if isinstance(
                    parameter,
                    FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar
                    | FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                    | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple,
                )
            }
            for native_ancestor in reversed(source.get_mro()):
                ancestor = FlextInfraUtilitiesRopeRuntime.require_class_object(
                    native_ancestor, "model protocol ancestor"
                )
                if not self.py_class(ancestor):
                    continue
                node, lexical = ancestor.get_ast(), ancestor.get_scope()
                if not isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                    message = "model ancestor has no authenticated class declaration"
                    raise TypeError(message)
                self._collect_fields(node, lexical, fields)
            return list(fields.values())

        def _field_declaration(
            self, statement: t.Infra.AstStatement, scope: p.Infra.RopeScope
        ) -> tuple[str, t.Infra.AstExpression] | None:
            """Select annotated storage or a native computed field's return type.

            Returns:
                The declared field and annotation, or no data declaration.

            Raises:
                TypeError: If a computed field has no return annotation.

            """
            if isinstance(
                statement, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign
            ) and isinstance(
                statement.target, FlextInfraUtilitiesRopeAnalysis.Tree.Name
            ):
                return statement.target.id, statement.annotation
            if not isinstance(
                statement, FlextInfraUtilitiesRopeAnalysis.Tree.FunctionDef
            ) or not any(
                self._denotes(
                    decorator.func
                    if isinstance(decorator, FlextInfraUtilitiesRopeAnalysis.Tree.Call)
                    else decorator,
                    scope,
                    "pydantic",
                    "computed_field",
                )
                for decorator in statement.decorator_list
            ):
                return None
            if statement.returns is None:
                message = "computed model field has no return annotation"
                raise TypeError(message)
            return statement.name, statement.returns

        def _collect_fields(
            self,
            node: t.Infra.AstClassDefinition,
            scope: p.Infra.RopeScope,
            fields: dict[str, t.Infra.AstStatement],
        ) -> None:
            """Apply one native declaration's field overrides in C3 collection order."""
            for statement in node.body:
                declaration = self._field_declaration(statement, scope)
                if declaration is None:
                    continue
                name, annotation = declaration
                if name.startswith("_") or name == "model_config":
                    continue
                if isinstance(
                    statement, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign
                ) and self._declares_class_storage(self.project, scope, statement):
                    fields.pop(name, None)
                    continue
                if isinstance(
                    annotation, FlextInfraUtilitiesRopeAnalysis.Tree.Subscript
                ) and self._denotes(annotation.value, scope, "typing", "Final"):
                    annotation = annotation.slice
                fields[name] = FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign(
                    target=FlextInfraUtilitiesRopeAnalysis.Tree.Name(
                        id=name, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Store()
                    ),
                    annotation=self._annotation(annotation, scope, ()),
                    value=None,
                    simple=1,
                )

        def _type_parameters(
            self, binding: p.Infra.RopePyName
        ) -> list[t.Infra.AstTypeParameter]:
            """Rebind parameter bounds without mutating the engine's cached AST.

            Returns:
                Source-owned PEP 695 parameters in their original declaration order.

            Raises:
                TypeError: If a native class or supported parameter is absent.

            """
            source = self._source_class(binding)
            node = source.get_ast()
            if not isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                message = "model parameters have no native class declaration"
                raise TypeError(message)
            scope = source.get_scope()
            parameters: list[t.Infra.AstTypeParameter] = []
            for parameter in node.type_params:
                if not isinstance(
                    parameter,
                    FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar
                    | FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                    | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple,
                ):
                    message = "model has an unsupported native type parameter"
                    raise TypeError(message)
                default = (
                    self._annotation(parameter.default_value, scope, ())
                    if parameter.default_value is not None
                    else None
                )
                if isinstance(parameter, FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar):
                    bound = (
                        self._annotation(parameter.bound, scope, ())
                        if parameter.bound is not None
                        else None
                    )
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar(
                            name=parameter.name, bound=bound, default_value=default
                        )
                    )
                elif isinstance(
                    parameter, FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                ):
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec(
                            name=parameter.name, default_value=default
                        )
                    )
                else:
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple(
                            name=parameter.name, default_value=default
                        )
                    )
            return parameters

        def _annotation(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Restore source-bound annotation closure without target imports.

            Returns:
                A structural annotation with model dependencies projected to p.

            """
            if (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and node.id in self.parameters
            ):
                return node
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Constant):
                if isinstance(node.value, str):
                    return self._annotation(
                        FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                            node.value
                        ),
                        scope,
                        visiting,
                    )
                return node
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Subscript):
                return self._annotation_subscript(node, scope, visiting)
            if isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Name
                | FlextInfraUtilitiesRopeAnalysis.Tree.Attribute,
            ):
                return self._annotation_symbol(node, scope, visiting)
            return self._annotation_container(node, scope, visiting)

        def _annotation_subscript(
            self,
            node: t.Infra.AstSubscript,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Retain generic arguments without interpreting literal or metadata data.

            Returns:
                The projected generic or the structural Annotated payload.

            Raises:
                ValueError: If Annotated has no native payload.

            """
            if self._denotes(node.value, scope, "typing", "Annotated"):
                if not isinstance(
                    node.slice, FlextInfraUtilitiesRopeAnalysis.Tree.Tuple
                ):
                    message = "Annotated has no native payload"
                    raise ValueError(message)
                return self._annotation(node.slice.elts[0], scope, visiting)
            return FlextInfraUtilitiesRopeAnalysis.Tree.Subscript(
                value=self._annotation(node.value, scope, visiting),
                slice=(
                    node.slice
                    if self._denotes(node.value, scope, "typing", "Literal")
                    else self._annotation(node.slice, scope, visiting)
                ),
                ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load(),
            )

        def _annotation_container(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Project native union, sequence and unpacking annotation shapes.

            Returns:
                A container with its original structural kind.

            Raises:
                TypeError: If the native shape is unsupported.

            """
            if isinstance(
                node, FlextInfraUtilitiesRopeAnalysis.Tree.BinOp
            ) and isinstance(node.op, FlextInfraUtilitiesRopeAnalysis.Tree.BitOr):
                return FlextInfraUtilitiesRopeAnalysis.Tree.BinOp(
                    left=self._annotation(node.left, scope, visiting),
                    op=FlextInfraUtilitiesRopeAnalysis.Tree.BitOr(),
                    right=self._annotation(node.right, scope, visiting),
                )
            if isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Tuple
                | FlextInfraUtilitiesRopeAnalysis.Tree.List,
            ):
                values = [self._annotation(item, scope, visiting) for item in node.elts]
                return (
                    FlextInfraUtilitiesRopeAnalysis.Tree.Tuple(
                        elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                    )
                    if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Tuple)
                    else FlextInfraUtilitiesRopeAnalysis.Tree.List(
                        elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                    )
                )
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Starred):
                return FlextInfraUtilitiesRopeAnalysis.Tree.Starred(
                    value=self._annotation(node.value, scope, visiting),
                    ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load(),
                )
            message = (
                f"unsupported native model annotation: "
                f"{FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)}"
            )
            raise TypeError(message)

        def _annotation_symbol(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Resolve model, authored port and alias identities in the native scope.

            Returns:
                A source-bound annotation using its declaring import provider.

            Raises:
                TypeError: If a forbidden loose annotation is selected.
                ValueError: If a source annotation alias recurses.

            """
            binding = self.resolve_symbol(scope, node)
            if self._denotes(node, scope, "builtins", "object") or self._denotes(
                node, scope, "typing", "Any"
            ):
                message = (
                    f"forbidden generated protocol annotation: "
                    f"{FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)}"
                )
                raise TypeError(message)
            projected = self._model_annotation(node, scope, binding)
            if projected is not None:
                return projected
            alias = (
                self.annotation_alias_definition(binding)
                if binding is not None
                else None
            )
            if alias is not None:
                declaration, lexical = alias
                name = declaration.name.id
                if name in visiting:
                    message = f"recursive model annotation alias: {name}"
                    raise ValueError(message)
                if not declaration.type_params:
                    return self._annotation(
                        declaration.value, lexical, (*visiting, name)
                    )
            root = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node).partition(".")[0]
            if binding is not None and self.same_name(
                self.facades["p"], self.expression_name(scope, root)
            ):
                return self._declared_port(
                    binding,
                    FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node).partition(".")[
                        2
                    ],
                )
            source = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)
            aliases = self._imports(source, scope)
            renamed = aliases.get(root, root)
            return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                f"{renamed}{source[len(root) :]}"
            )

        def _model_annotation(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            binding: p.Infra.RopePyName | None,
        ) -> t.Infra.AstExpression | None:
            """Select a consumed model dependency or preserve its authored port.

            Returns:
                The projected dependency, or None for a non-model symbol.

            """
            for route, model in self.models.items():
                root, separator, tail = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(
                    node
                ).partition(".")
                future_port = (
                    separator
                    and tail == route
                    and self.same_name(
                        self.facades["p"], self.expression_name(scope, root)
                    )
                )
                if future_port or (
                    binding is not None and self.same_name(model, binding)
                ):
                    port = self._member(self.facades["p"], route)
                    owner = port.get_object().get_module() if port is not None else None
                    if (
                        port is not None
                        and self.source_module(owner)
                        and not owner.source_code.startswith(c.Infra.AUTOGEN_HEADER)
                    ):
                        return self._declared_port(port, route)
                    self.selected.add(route)
                    self.dependencies.add(route)
                    return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                        self.references[route]
                    )
            return None

        def _declared_port(
            self, binding: p.Infra.RopePyName, route: str
        ) -> t.Infra.AstExpression:
            """Retain an authored contract through its nearest family export.

            Returns:
                The declaring class path without reentering the facade under assembly.

            Raises:
                TypeError: If the authored port has no native source class.
                ValueError: If the authored port has no declaring resource.

            """
            inherited = self._inherited_port(binding, route)
            if inherited is not None:
                return inherited
            value = binding.get_object()
            if not self.py_class(value):
                message = "authored protocol annotation has no native source class"
                raise TypeError(message)
            module = value.get_module()
            resource = module.get_resource()
            if resource is None:
                message = "authored protocol annotation has no declaring resource"
                raise ValueError(message)
            if self.package is None or not Path(resource.real_path).is_relative_to(
                self.package
            ):
                message = (
                    f"inherited protocol has no native public facade owner: {route}"
                )
                raise ValueError(message)
            names = [value.get_name()]
            scope = value.get_scope()
            while scope.parent is not None:
                scope = scope.parent
                if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
                    names.append(scope.pyobject.get_name())
            names.reverse()
            package = (FlextInfraUtilitiesRopeAnalysis.package_name_for_module)(
                module.get_name(), resource
            )
            self.imports[names[0]] = f"from {package} import {names[0]}"
            return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                ".".join(names)
            )

        def _inherited_port(
            self, binding: p.Infra.RopePyName, route: str
        ) -> t.Infra.AstExpression | None:
            """Retain upstream namespaces through their native published p alias.

            Returns:
                The nearest inherited public reference, or no upstream owner.

            """
            facade = FlextInfraUtilitiesRopeRuntime.require_class_object(
                self.facades["p"].get_object(), "protocol facade"
            )
            for native_ancestor in facade.get_mro():
                ancestor = FlextInfraUtilitiesRopeRuntime.require_class_object(
                    native_ancestor, "protocol facade ancestor"
                )
                module = ancestor.get_module()
                if not self.source_module(module):
                    continue
                resource = module.get_resource()
                if resource is None or (
                    self.package is not None
                    and Path(resource.real_path).is_relative_to(self.package)
                ):
                    continue
                exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                    module
                )
                published = module.get_attributes().get("p")
                if (
                    "p" not in exports
                    or published is None
                    or published.get_object() is not ancestor
                ):
                    continue
                member = self._member(published, route)
                if member is None or not self.same_name(member, binding):
                    continue
                provider = module.get_name().rpartition(".")[0]
                alias = f"{provider.replace('.', '_')}_p"
                self.imports[alias] = f"from {provider} import p as {alias}"
                return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                    f"{alias}.{route}"
                )
            return None

        def _imports(self, source: str, scope: p.Infra.RopeScope) -> Mapping[str, str]:
            """Reuse native imports with provider-bound lexical aliases.

            Returns:
                Annotation roots rebound to their exact declaring import providers.

            Raises:
                ValueError: If source or import ownership is absent or competing.

            """
            module = scope.pyobject.get_module()
            if not self.source_module(module):
                message = "model annotation has no authenticated declaring module"
                raise ValueError(message)
            roots = {
                source[begin:end].partition(".")[0]
                for begin, end in (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(
                        source
                    )
                )
            }
            rebound: dict[str, str] = {}
            for (
                information
            ) in FlextInfraUtilitiesSemanticDeclarationRelocation.native_import_infos(
                self.project, module
            ):
                aliases = tuple(
                    (name, alias)
                    for name, alias in information.names_and_aliases
                    if (alias or name.partition(".")[0]) in roots
                )
                if not aliases:
                    continue
                if isinstance(information, p.Infra.RopeFromImport):
                    provider = self._import_provider(module, information)
                    projected = tuple(
                        (name, f"{provider.replace('.', '_')}_{alias or name}")
                        for name, alias in aliases
                    )
                    rebound.update(
                        (alias or name, projected_alias)
                        for (name, alias), (_name, projected_alias) in zip(
                            aliases, projected, strict=True
                        )
                    )
                    imported = FlextInfraUtilitiesRopeRuntime.from_import(
                        provider, 0, projected
                    )
                else:
                    imported = FlextInfraUtilitiesRopeRuntime.normal_import(aliases)
                    rebound.update(
                        (
                            alias or name.partition(".")[0],
                            alias or name.partition(".")[0],
                        )
                        for name, alias in aliases
                    )
                statement = imported.get_import_statement()
                for name, alias in aliases:
                    root = alias or name.partition(".")[0]
                    receiver = rebound[root]
                    previous = self.imports.setdefault(receiver, statement)
                    if previous != statement:
                        message = f"competing lexical annotation import: {receiver}"
                        raise ValueError(message)
            self._validate_builtins(roots - rebound.keys(), scope)
            return rebound

        def _validate_builtins(
            self,
            roots: set[str],
            scope: p.Infra.RopeScope,
        ) -> None:
            """Require exact native builtin identities for roots without imports.

            Raises:
                ValueError: If an annotation root has no authenticated owner.

            """
            builtins = self.require_semantic_module(
                self.project.get_module("builtins")
            ).get_attributes()
            for root in roots:
                builtin = builtins.get(root)
                if builtin is None or not self.same_name(
                    builtin, self.expression_name(scope, root)
                ):
                    message = f"annotation has no authenticated imported owner: {root}"
                    raise ValueError(message)

        @staticmethod
        def _import_provider(
            module: p.Infra.RopeSourceModule,
            information: p.Infra.RopeFromImport,
        ) -> str:
            """Resolve a relative native import in its declaring package.

            Returns:
                The absolute native import provider.

            Raises:
                ValueError: If the annotation import has no native resource.

            """
            resource = module.get_resource()
            if resource is None:
                message = "annotation import has no native resource"
                raise ValueError(message)
            return FlextInfraUtilitiesRopeAnalysis.resolve_import_module(
                current_package=(
                    FlextInfraUtilitiesRopeAnalysis.package_name_for_module(
                        module.get_name(), resource
                    )
                ),
                module_name=information.module_name,
                level=information.level,
            )

        def _denotes(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            module: str,
            name: str,
        ) -> bool:
            return self.same_name(
                self.qualified_name(self.project, name, module_name=module),
                self.resolve_symbol(scope, node),
            )

        def _member(
            self, binding: p.Infra.RopePyName, route: str
        ) -> p.Infra.RopePyName | None:
            value = binding.get_object()
            if not self.py_class(value):
                return None
            return self.resolve_symbol(value.get_scope(), route)

        def _source_class(self, binding: p.Infra.RopePyName) -> p.Infra.RopeSourceClass:
            """Require the source capability already proved by model admission.

            Returns:
                The authenticated model declaration, never a loaded target class.

            Raises:
                TypeError: If the model has no authenticated native source class.

            """
            value = binding.get_object()
            if not self.py_class(value):
                message = "model has no authenticated native source class"
                raise TypeError(message)
            return value


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocol"]
