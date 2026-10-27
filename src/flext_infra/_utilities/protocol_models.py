"""Project consumed model data contracts from authenticated native sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from itertools import chain
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesProtocolModels:
    """Restore the source projection removed in 7a76fa5a9c, without its CLI."""

    @classmethod
    def protocol_model_sources(
        cls, workspace: p.Infra.RopeWorkspaceDsl
    ) -> t.MappingKV[Path, str]:
        """Return protocol sources without importing or publishing the target.

        Returns:
            Relative generated paths and their source-owned structural declarations.

        """
        return cls._ModelProtocolProjection(workspace).render()

    class _ModelProtocolProjection(FlextInfraUtilitiesDeclarationPayload):
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
            self.type_parameters: dict[str, list[ast.type_param]] = {}
            self.dependencies: set[str] = set()
            self.member_cache: dict[str, p.Infra.RopePyName | None] = {}

        def render(self) -> t.MappingKV[Path, str]:
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
            declarations: dict[str, list[ast.stmt]] = {}
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
            declaration: list[ast.stmt],
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
            body = ast.ClassDef(
                name=route.rpartition(".")[2],
                bases=[ast.Name(id="Protocol", ctx=ast.Load())],
                keywords=[],
                body=declaration or [ast.Pass()],
                decorator_list=[ast.Name(id="runtime_checkable", ctx=ast.Load())],
                type_params=self.type_parameters[route],
            )
            owner = self.references[route].partition(".")[0]
            wrapper = ast.ClassDef(
                name=owner,
                bases=[],
                keywords=[],
                body=[body],
                decorator_list=[],
                type_params=[],
            )
            exports = ast.Assign(
                targets=[ast.Name(id="__all__", ctx=ast.Store())],
                value=ast.List(elts=[ast.Constant(value=owner)], ctx=ast.Load()),
            )
            siblings = sorted(
                {
                    self.references[dependency].partition(".")[0]
                    for dependency in dependencies
                }
                - {owner}
            )
            statements = ast.parse("\n".join(sorted(set(imports.values())))).body
            if siblings:
                statements.extend((
                    ast.ImportFrom(
                        module="typing",
                        names=[ast.alias(name="TYPE_CHECKING")],
                        level=0,
                    ),
                    ast.If(
                        test=ast.Name(id="TYPE_CHECKING", ctx=ast.Load()),
                        body=[
                            ast.ImportFrom(
                                module=f"{self.package_name}.{directory.name}",
                                names=[ast.alias(name=name) for name in siblings],
                                level=0,
                            )
                        ],
                        orelse=[],
                    ),
                ))
            statements.extend((wrapper, exports))
            content = ast.unparse(
                ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[]))
            )
            token = route.replace(".", "_").lower()
            return (
                (
                    directory
                    / (
                        f"generated_models_{token}.py"
                        if token
                        else "generated_models.py"
                    )
                ).relative_to(self.workspace.repository_root),
                f"{c.Infra.AUTOGEN_HEADER}\n{content}\n",
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
                if not {"m", "p"}.intersection(
                    FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                        module.source_code
                    )
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
                t.Triple[
                    str,
                    p.Infra.RopePyName,
                    t.VariadicTuple[p.Infra.RopePyObject],
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

        def _fields(self, binding: p.Infra.RopePyName) -> list[ast.stmt]:
            """Retain inherited annotated data, never defaults or model methods.

            Returns:
                Annotated attributes in native C3 override order.

            Raises:
                TypeError: If a model declaration is absent.

            """
            fields: dict[str, ast.stmt] = {}
            definition = self._source_class(binding).get_ast()
            if not isinstance(definition, ast.ClassDef):
                message = "model has no authenticated class declaration"
                raise TypeError(message)
            self.parameters = {
                parameter.name
                for parameter in definition.type_params
                if isinstance(parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple)
            }
            for ancestor in reversed(self._lineage(binding.get_object(), ())):
                if not self.py_class(ancestor):
                    continue
                node, lexical = ancestor.get_ast(), ancestor.get_scope()
                if not isinstance(node, ast.ClassDef):
                    message = "model ancestor has no authenticated class declaration"
                    raise TypeError(message)
                self._collect_fields(node, lexical, fields)
            return list(fields.values())

        def _field_declaration(
            self, statement: ast.stmt, scope: p.Infra.RopeScope
        ) -> t.Pair[str, ast.expr] | None:
            """Select annotated storage or a native computed field's return type.

            Returns:
                The declared field and annotation, or no data declaration.

            Raises:
                TypeError: If a computed field has no return annotation.

            """
            if isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                return statement.target.id, statement.annotation
            if not isinstance(statement, ast.FunctionDef) or not any(
                self._denotes(
                    decorator.func if isinstance(decorator, ast.Call) else decorator,
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
            node: ast.ClassDef,
            scope: p.Infra.RopeScope,
            fields: dict[str, ast.stmt],
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
                    statement, ast.AnnAssign
                ) and self._declares_class_storage(self.project, scope, statement):
                    fields.pop(name, None)
                    continue
                if isinstance(annotation, ast.Subscript) and self._denotes(
                    annotation.value, scope, "typing", "Final"
                ):
                    annotation = annotation.slice
                fields[name] = ast.AnnAssign(
                    target=ast.Name(id=name, ctx=ast.Store()),
                    annotation=self._annotation(annotation, scope, ()),
                    value=None,
                    simple=1,
                )

        def _type_parameters(self, binding: p.Infra.RopePyName) -> list[ast.type_param]:
            """Rebind parameter bounds without mutating the engine's cached AST.

            Returns:
                Source-owned PEP 695 parameters in their original declaration order.

            Raises:
                TypeError: If a native class or supported parameter is absent.

            """
            source = self._source_class(binding)
            node = source.get_ast()
            if not isinstance(node, ast.ClassDef):
                message = "model parameters have no native class declaration"
                raise TypeError(message)
            scope = source.get_scope()
            parameters: list[ast.type_param] = []
            for parameter in node.type_params:
                if not isinstance(
                    parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple
                ):
                    message = "model has an unsupported native type parameter"
                    raise TypeError(message)
                default = (
                    self._annotation(parameter.default_value, scope, ())
                    if parameter.default_value is not None
                    else None
                )
                if isinstance(parameter, ast.TypeVar):
                    bound = (
                        self._annotation(parameter.bound, scope, ())
                        if parameter.bound is not None
                        else None
                    )
                    parameters.append(
                        ast.TypeVar(
                            name=parameter.name, bound=bound, default_value=default
                        )
                    )
                elif isinstance(parameter, ast.ParamSpec):
                    parameters.append(
                        ast.ParamSpec(name=parameter.name, default_value=default)
                    )
                else:
                    parameters.append(
                        ast.TypeVarTuple(name=parameter.name, default_value=default)
                    )
            return parameters

        def _lineage(
            self,
            value: p.Infra.RopePyObject,
            visiting: t.VariadicTuple[p.Infra.RopePyObject],
        ) -> t.VariadicTuple[p.Infra.RopePyObject]:
            """Use the canonical C3 merger for the native declared bases.

            Returns:
                The model's authenticated C3 declaration order.

            Raises:
                ValueError: If native model ancestry is cyclic.

            """
            if value in visiting:
                message = "cyclic native model ancestry"
                raise ValueError(message)
            bases = tuple(self.direct_bases(value))
            owners = {str(id(item)): item for item in self.class_ancestry(value)}
            merged = FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                (
                    *(
                        tuple(
                            str(id(item))
                            for item in self._lineage(base, (*visiting, value))
                        )
                        for base in bases
                    ),
                    tuple(str(id(base)) for base in bases),
                ),
                message="inconsistent native model ancestry",
            )
            return (value, *(owners[identity] for identity in merged))

        def _annotation(
            self, node: ast.expr, scope: p.Infra.RopeScope, visiting: t.StrTuple
        ) -> ast.expr:
            """Restore source-bound annotation closure without target imports.

            Returns:
                A structural annotation with model dependencies projected to p.

            """
            if isinstance(node, ast.Name) and node.id in self.parameters:
                return node
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    return self._annotation(
                        ast.parse(node.value, mode="eval").body, scope, visiting
                    )
                return node
            if isinstance(node, ast.Subscript):
                return self._annotation_subscript(node, scope, visiting)
            if isinstance(node, ast.Name | ast.Attribute):
                return self._annotation_symbol(node, scope, visiting)
            return self._annotation_container(node, scope, visiting)

        def _annotation_subscript(
            self,
            node: ast.Subscript,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> ast.expr:
            """Retain generic arguments without interpreting literal or metadata data.

            Returns:
                The projected generic or the structural Annotated payload.

            Raises:
                ValueError: If Annotated has no native payload.

            """
            if self._denotes(node.value, scope, "typing", "Annotated"):
                if not isinstance(node.slice, ast.Tuple):
                    message = "Annotated has no native payload"
                    raise ValueError(message)
                return self._annotation(node.slice.elts[0], scope, visiting)
            return ast.Subscript(
                value=self._annotation(node.value, scope, visiting),
                slice=(
                    node.slice
                    if self._denotes(node.value, scope, "typing", "Literal")
                    else self._annotation(node.slice, scope, visiting)
                ),
                ctx=ast.Load(),
            )

        def _annotation_container(
            self,
            node: ast.expr,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> ast.expr:
            """Project native union, sequence and unpacking annotation shapes.

            Returns:
                A container with its original structural kind.

            Raises:
                TypeError: If the native shape is unsupported.

            """
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                return ast.BinOp(
                    left=self._annotation(node.left, scope, visiting),
                    op=ast.BitOr(),
                    right=self._annotation(node.right, scope, visiting),
                )
            if isinstance(node, ast.Tuple | ast.List):
                values = [self._annotation(item, scope, visiting) for item in node.elts]
                return (
                    ast.Tuple(elts=values, ctx=ast.Load())
                    if isinstance(node, ast.Tuple)
                    else ast.List(elts=values, ctx=ast.Load())
                )
            if isinstance(node, ast.Starred):
                return ast.Starred(
                    value=self._annotation(node.value, scope, visiting),
                    ctx=ast.Load(),
                )
            message = f"unsupported native model annotation: {ast.unparse(node)}"
            raise TypeError(message)

        def _annotation_symbol(
            self,
            node: ast.Name | ast.Attribute,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> ast.expr:
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
                    f"forbidden generated protocol annotation: {ast.unparse(node)}"
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
            root = ast.unparse(node).partition(".")[0]
            if binding is not None and self.same_name(
                self.facades["p"], self.expression_name(scope, root)
            ):
                return self._declared_port(binding, ast.unparse(node).partition(".")[2])
            source = ast.unparse(node)
            aliases = self._imports(source, scope)
            renamed = aliases.get(root, root)
            return ast.parse(f"{renamed}{source[len(root) :]}", mode="eval").body

        def _model_annotation(
            self,
            node: ast.Name | ast.Attribute,
            scope: p.Infra.RopeScope,
            binding: p.Infra.RopePyName | None,
        ) -> ast.expr | None:
            """Select a consumed model dependency or preserve its authored port.

            Returns:
                The projected dependency, or None for a non-model symbol.

            """
            for route, model in self.models.items():
                root, separator, tail = ast.unparse(node).partition(".")
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
                    return ast.parse(self.references[route], mode="eval").body
            return None

        def _declared_port(self, binding: p.Infra.RopePyName, route: str) -> ast.expr:
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
            return ast.parse(".".join(names), mode="eval").body

        def _inherited_port(
            self, binding: p.Infra.RopePyName, route: str
        ) -> ast.expr | None:
            """Retain upstream namespaces through their native published p alias.

            Returns:
                The nearest inherited public reference, or no upstream owner.

            """
            for ancestor in self._lineage(self.facades["p"].get_object(), ()):
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
                    module.source_code
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
                return ast.parse(f"{alias}.{route}", mode="eval").body
            return None

        def _imports(
            self, source: str, scope: p.Infra.RopeScope
        ) -> t.MappingKV[str, str]:
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
            self, node: ast.expr, scope: p.Infra.RopeScope, module: str, name: str
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
            return self.resolve_symbol(
                value.get_scope(), ast.parse(route, mode="eval").body
            )

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


__all__: list[str] = ["FlextInfraUtilitiesProtocolModels"]
