"""Rope refactor change-set boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import types as python_types
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import cast

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeMatching,
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesRopeRuntimeRefactors(FlextInfraUtilitiesRopeRuntimeMatching):
    """Load Rope refactor helpers behind protocols."""

    @classmethod
    def reindent_source(cls, source: str, amount: int) -> str:
        """Move source indentation while retaining every multiline literal value.

        Args:
            source: The source code whose indentation is to be adjusted.
            amount: Spaces to add or remove from each line's indentation.

        Returns:
            The source code with adjusted indentation.

        Raises:
            ValueError: If a source line has less indentation than the removal.

        """
        literals = tuple(
            (begin, end)
            for begin, end, _metadata in cls.ignored_regions(source)
            if source[begin] != "#"
        )
        result: list[str] = []
        offset = 0
        for line in source.splitlines(keepends=True):
            inside_literal = any(begin < offset < end for begin, end in literals)
            if not inside_literal and line.strip():
                if amount >= 0:
                    changed = " " * amount + line
                else:
                    removable = len(line) - len(line.lstrip(" \t"))
                    if removable < -amount:
                        msg = "source indentation is smaller than its native move"
                        raise ValueError(msg)
                    changed = line[-amount:]
            else:
                changed = line
            result.append(changed)
            offset += len(line)
        return "".join(result)

    @staticmethod
    def compiled_constant(source: str) -> p.Result[p.AttributeProbe]:
        """Read a primitive compiler constant without executing authored source.

        Returns:
            The resulting ``p.Result[p.AttributeProbe]``.

        """
        code = compile(source, "<native constant>", "eval", dont_inherit=True)
        if code.co_names or code.co_freevars or len(code.co_consts) != 1:
            return r[p.AttributeProbe].fail("expression has no sole native constant")
        value = code.co_consts[0]
        if (
            type(value) not in {str, bytes, int, float, complex, bool, type(None)}
            and value is not Ellipsis
        ):
            return r[p.AttributeProbe].fail(
                "expression has no primitive native constant"
            )
        return r[p.AttributeProbe].ok(value)

    @classmethod
    def literal_string(cls, source: str) -> str | None:
        """Decode native string escapes without evaluating source callbacks.

        Returns:
            The resulting ``str | None``.

        """
        observed = cls.compiled_constant(source)
        if observed.failure:
            return None
        value = observed.value
        return value if type(value) is str else None

    @classmethod
    def attribute_read_proofs(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        function: p.Infra.RopeSourceFunction,
        resolver: p.Infra.RopeSourceMemberResolver,
    ) -> tuple[p.Infra.RopeAttributeReadProof, ...]:
        """Prove attribute reads in declarations against one elected source view.

        Imports use Rope's native identities, lazy exports use their literal
        installer route, class members use the captured C3 resolver, and the
        effective getter must be a builtin. Arbitrary descriptors refuse.

        Returns:
            Snapshot-bound evidence for every executed declaration attribute.

        Raises:
            TypeError: The native function has no function declaration AST.
            ValueError: Any module, member, getter, descriptor, or source span is
                unresolved or has non-builtin access behavior.

        """
        source = project.source_text(Path(resource.real_path))
        if function.get_module().source_code != source:
            message = "attribute proof source differs from the Rope snapshot"
            raise ValueError(message)
        method = function.get_ast()
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            message = "attribute proof requires a native function declaration"
            raise TypeError(message)
        expressions: list[ast.expr] = [*method.decorator_list]
        expressions.extend(method.args.defaults)
        expressions.extend(
            default for default in method.args.kw_defaults if default is not None
        )
        module = function.get_module()
        future_annotations = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in module.get_ast().body
        )
        if not future_annotations:
            parameters = [
                *method.args.posonlyargs,
                *method.args.args,
                *method.args.kwonlyargs,
            ]
            parameters.extend(
                parameter
                for parameter in (method.args.vararg, method.args.kwarg)
                if parameter is not None
            )
            expressions.extend(
                parameter.annotation
                for parameter in parameters
                if parameter.annotation is not None
            )
            if method.returns is not None:
                expressions.append(method.returns)

        scope = function.get_scope().parent
        if scope is None:
            message = "attribute proof requires the declaration's lexical scope"
            raise ValueError(message)
        proofs = []
        seen: set[tuple[int, int, int | None, int | None]] = set()
        for expression in expressions:
            for node in ast.walk(expression):
                if not isinstance(node, ast.Attribute):
                    continue
                span = (
                    node.lineno,
                    node.col_offset,
                    node.end_lineno,
                    node.end_col_offset,
                )
                if span in seen:
                    continue
                seen.add(span)
                proofs.append(
                    cls._attribute_read_proof(project, resolver, scope, resource, node)
                )
        return tuple(proofs)

    @classmethod
    def _attribute_read_proof(
        cls,
        project: p.Infra.RopeProject,
        resolver: p.Infra.RopeSourceMemberResolver,
        scope: p.Infra.RopeScope,
        resource: p.Infra.RopeResource,
        node: ast.Attribute,
    ) -> p.Infra.RopeAttributeReadProof:
        """Authenticate one member fetch and its effective access mechanism.

        Returns:
            The resulting ``m.Infra.RopeAttributeReadProof``.

        Raises:
            ValueError: If attribute read has no native Rope identity; or if attribute
                access resolves to a non-builtin getter; or if class MRO and Rope
                attribute bindings disagree; or if attribute receiver has no native
                class identity; or if class access has an unresolved metaclass.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        base_name = cls._native_expression_binding(project, scope, node.value, resolver)
        member_name = cls._native_expression_binding(project, scope, node, resolver)
        if base_name is None or member_name is None:
            msg = (
                "attribute read has no native Rope identity: "
                f"{ast.dump(node, include_attributes=False)}"
            )
            raise ValueError(msg)
        base = base_name.get_object()

        if types.pymodule(base):
            access = "module"
            base_reference = cls._attribute_reference(project, base)
            native_base = base_name
            member = runtime.qualified_name(
                project, node.attr, module_name=base.get_name()
            )
        else:
            owner = base.get_type() if types.instance_object(base) else base
            if not types.abstract_class(owner):
                msg = "attribute receiver has no native class identity"
                raise ValueError(msg)
            base_reference = cls._attribute_reference(project, owner)
            native_base = (
                runtime.qualified_name(
                    project,
                    ".".join(base_reference.attributes),
                    module_name=base_reference.target,
                )
                if types.instance_object(base)
                else base_name
            )
            member = resolver(f"{base_reference.qualified_base}.{node.attr}")
            access = "instance" if types.instance_object(base) else "class"
        accessor = cls._attribute_accessor(project, resolver, base)
        if not runtime.same_name(member, member_name):
            msg = "class MRO and Rope attribute bindings disagree"
            raise ValueError(msg)
        descriptor = cls._attribute_descriptor(member)
        source = project.source_text(Path(resource.real_path))
        span = cls._source_byte_range(source, node)
        return m.Infra.RopeAttributeReadProof.model_validate({
            "project": (project),
            "source_path": (Path(resource.real_path)),
            "source_sha256": (hashlib.sha256(source.encode("utf-8")).hexdigest()),
            "start_byte": (span[0]),
            "end_byte": (span[1]),
            "expression": (ast.dump(node, include_attributes=False)),
            "access": (access),
            "base": (base_reference),
            "accessor": (cls._binding_reference(project, accessor, "__getattribute__")),
            "member": (cls._binding_reference(project, member, node.attr)),
            "descriptor": (descriptor),
            "native_base": (native_base),
            "native_accessor": (accessor),
            "native_member": (member),
            "native_descriptor": (
                runtime.qualified_name(project, "staticmethod", module_name="builtins")
                if descriptor is not None
                else None
            ),
        })

    @classmethod
    def _attribute_accessor(
        cls,
        project: p.Infra.RopeProject,
        resolver: p.Infra.RopeSourceMemberResolver,
        base: p.Infra.RopePyObject,
    ) -> p.Infra.RopePyName:
        """Authenticate the exact builtin getter used by a native receiver.

        Returns:
            The captured binding of the effective builtin attribute getter.

        Raises:
            ValueError: A receiver or metaclass is unresolved, or its getter has
                arbitrary execution behavior.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if types.pymodule(base):
            expression = "types.ModuleType.__getattribute__"
            expected = python_types.ModuleType.__getattribute__
        else:
            instance = types.instance_object(base)
            owner = base.get_type() if instance else base
            if not types.abstract_class(owner):
                message = "attribute receiver has no native class identity"
                raise ValueError(message)
            getter_owner = owner if instance else owner.get_metaclass()
            if getter_owner is None or not types.abstract_class(getter_owner):
                message = "class access has an unresolved metaclass"
                raise ValueError(message)
            expression = (
                f"{cls._attribute_reference(project, getter_owner).qualified_base}"
                ".__getattribute__"
            )
            expected = (
                builtins.object.__getattribute__
                if instance
                else builtins.type.__getattribute__
            )
        accessor = resolver(expression)
        if getattr(accessor.get_object(), "builtin", None) is not expected:
            message = "attribute access resolves to a non-builtin getter"
            raise ValueError(message)
        return accessor

    @classmethod
    def _native_expression_binding(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        expression: ast.expr,
        resolver: p.Infra.RopeSourceMemberResolver,
    ) -> p.Infra.RopePyName | None:
        """Resolve source imports, lazy aliases, and C3 members without execution.

        Returns:
            The resulting ``p.Infra.RopePyName | None``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        evaluate = cls.runtime_callable("rope.base.evaluate", "eval_node")
        observed = evaluate(scope, expression)
        binding = observed if isinstance(observed, p.Infra.RopePyName) else None
        if isinstance(expression, ast.Name) and types.imported_name(binding):
            imported = binding.imported_module
            if imported.module_name is not None and binding.imported_name:
                try:
                    return runtime.qualified_name(
                        project,
                        binding.imported_name,
                        module_name=imported.module_name,
                    )
                except runtime.rope_unresolved_error_types():
                    pass
        if isinstance(expression, ast.Attribute):
            base_binding = cls._native_expression_binding(
                project, scope, expression.value, resolver
            )
            if base_binding is None:
                return None
            base = base_binding.get_object()
            if types.pymodule(base):
                try:
                    return runtime.qualified_name(
                        project, expression.attr, module_name=base.get_name()
                    )
                except runtime.rope_unresolved_error_types():
                    return None
            instance = types.instance_object(base)
            owner = base.get_type() if instance else base
            return (
                resolver(
                    f"{cls._attribute_reference(project, owner).qualified_base}."
                    f"{expression.attr}"
                )
                if types.abstract_class(owner)
                else None
            )
        return binding

    @classmethod
    def _attribute_reference(
        cls, project: p.Infra.RopeProject, value: p.Infra.RopePyObject
    ) -> p.Infra.SourceClassReference:
        """Resolve a Rope class or module to its native fully qualified identity.

        Returns:
            The resulting ``m.Infra.SourceClassReference``.

        Raises:
            ValueError: If attribute receiver has no source class identity; or if
                attribute receiver class has no source module; or if Rope class identity
                differs from its source path; or if builtin Rope identity changed during
                lookup.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if types.instance_object(value):
            value = value.get_type()
        if types.pymodule(value):
            name = value.get_name()
            return m.Infra.SourceClassReference(
                target=name, attributes=(), qualified_base=name
            )
        builtin = getattr(value, "builtin", None)
        if builtin is not None:
            module = getattr(builtin, "__module__", "builtins")
            name = builtin.__qualname__
            attributes = tuple(name.split("."))
            identity = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project, ".".join(attributes), module_name=module
            )
            if getattr(identity.get_object(), "builtin", None) is not builtin:
                msg = "builtin Rope identity changed during lookup"
                raise ValueError(msg)
            return m.Infra.SourceClassReference(
                target=module,
                attributes=attributes,
                qualified_base=".".join((module, *attributes)),
            )
        if not types.py_class(value):
            msg = "attribute receiver has no source class identity"
            raise ValueError(msg)
        module = value.get_module()
        attributes = []
        scope = value.get_scope()
        while scope is not None and scope.get_kind() == "Class":
            attributes.insert(0, scope.pyobject.get_name())
            scope = scope.parent
        if not attributes:
            attributes.append(value.get_name())
        identity = runtime.qualified_name(
            project,
            ".".join(attributes),
            module_name=module.get_name(),
        )
        if identity.get_object() is not value:
            msg = "Rope class identity differs from its source path"
            raise ValueError(msg)
        qualified = ".".join((module.get_name(), *attributes))
        return m.Infra.SourceClassReference(
            target=module.get_name(),
            attributes=tuple(attributes),
            qualified_base=qualified,
        )

    @classmethod
    def _binding_reference(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        fallback_member: str,
    ) -> p.Infra.SourceClassReference:
        """Identify one resolved binding by its source owner or builtin path.

        Returns:
            The resulting ``m.Infra.SourceClassReference``.

        Raises:
            ValueError: If attribute binding has no native source definition.

        """
        supplier = FlextInfraUtilitiesRopeRuntimeModuleQueries.source_import_binding(
            binding
        )
        if supplier is not None:
            binding = supplier
        value = binding.get_object()
        if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value):
            return cls._attribute_reference(project, value)
        builtin = getattr(value, "builtin", None)
        if builtin is not None:
            module = getattr(builtin, "__module__", "builtins")
            name = getattr(builtin, "__qualname__", fallback_member)
            attributes = tuple(name.split("."))
            return m.Infra.SourceClassReference(
                target=module,
                attributes=attributes,
                qualified_base=".".join((module, *attributes)),
            )
        module, line = FlextInfraUtilitiesRopeRuntimeModuleQueries.definition_location(
            binding
        )
        if (
            not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module)
            or line is None
        ):
            msg = "attribute binding has no native source definition"
            raise ValueError(msg)
        scope = module.get_scope().get_inner_scope_for_line(line)
        owner = scope
        while owner is not None and owner.get_kind() != "Class":
            owner = owner.parent
        if owner is None:
            qualified = f"{module.get_name()}.{fallback_member}"
            return m.Infra.SourceClassReference(
                target=module.get_name(),
                attributes=(fallback_member,),
                qualified_base=qualified,
            )
        class_reference = cls._attribute_reference(project, owner.pyobject)
        attributes = (*class_reference.attributes, fallback_member)
        return m.Infra.SourceClassReference(
            target=class_reference.target,
            attributes=attributes,
            qualified_base=".".join((class_reference.target, *attributes)),
        )

    @staticmethod
    def _attribute_descriptor(
        binding: p.Infra.RopePyName,
    ) -> p.Infra.SourceClassReference | None:
        """Admit source classes, plain constants, or builtin staticmethod only.

        Returns:
            The resulting ``m.Infra.SourceClassReference | None``.

        Raises:
            ValueError: If attribute value may invoke a custom descriptor.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        value = binding.get_object()
        if types.pymodule(value) or types.abstract_class(value):
            return None
        if types.py_function(value) and value.get_kind() == "staticmethod":
            return m.Infra.SourceClassReference(
                target="builtins",
                attributes=("staticmethod",),
                qualified_base="builtins.staticmethod",
            )
        supplier = FlextInfraUtilitiesRopeRuntimeModuleQueries.source_import_binding(
            binding
        )
        if types.assigned_name(supplier) and len(supplier.assignments) == 1:
            assignment = supplier.assignments[0]
            if isinstance(assignment.ast_node, ast.Constant):
                return None
        msg = "attribute value may invoke a custom descriptor"
        raise ValueError(msg)

    @staticmethod
    def _source_byte_range(source: str, node: ast.Attribute) -> tuple[int, int]:
        """Return the source-owned byte span, refusing absent AST endpoints.

        Returns:
            The inclusive start and exclusive end byte offsets.

        Raises:
            ValueError: The native attribute has no complete source span.

        """
        if node.end_lineno is None or node.end_col_offset is None:
            message = "attribute read has no complete native source span"
            raise ValueError(message)
        lines = source.splitlines(keepends=True)
        start = sum(len(line.encode("utf-8")) for line in lines[: node.lineno - 1])
        end = sum(len(line.encode("utf-8")) for line in lines[: node.end_lineno - 1])
        return start + node.col_offset, end + node.end_col_offset

    @classmethod
    def ignored_regions(
        cls,
        source: str,
    ) -> tuple[tuple[int, int, Mapping[str, str | None]], ...]:
        """Read complete literal and comment ranges from Rope's native lexer.

        Returns:
            The resulting ``tuple[tuple[int, int, Mapping[str, str |
                None]], ...]``.

        """
        adapter: t.ValueAdapter[Sequence[tuple[int, int, Mapping[str, str | None]]]] = (
            u.type_adapter(
                Sequence[tuple[int, int, dict[str, str | None]]],
            )
        )
        return tuple(
            adapter.validate_python(
                cls.runtime_callable("rope.base.simplify", "ignored_regions")(source),
                strict=True,
            ),
        )

    @staticmethod
    def change_set_members(
        value: p.AttributeProbe,
        invalid_result: str,
    ) -> p.Result[Sequence[p.Infra.RopeChangeContents]]:
        """Validate a native content-change list once at the Rope SDK boundary.

        Returns:
            Typed content changes, or a failure for malformed lists or members.

        """
        if not isinstance(value, list):
            return r[Sequence[p.Infra.RopeChangeContents]].fail(invalid_result)
        members = cast("list[p.AttributeProbe]", value)
        validated: list[p.Infra.RopeChangeContents] = []
        for member in members:
            if not isinstance(member, p.Infra.RopeChangeContents):
                return r[Sequence[p.Infra.RopeChangeContents]].fail(invalid_result)
            validated.append(member)
        return r[Sequence[p.Infra.RopeChangeContents]].ok(tuple(validated))

    @classmethod
    def unwrap_class_rewrites(
        cls,
        source: str,
        layout: p.Infra.ClassBlockLayout,
    ) -> tuple[p.Infra.SourceRewrite, ...]:
        """Remove one Rope-resolved header without changing literal payloads.

        The body statements own the dedent width and the wrapper docstring, so
        both derive from the logical facts instead of being passed alongside.

        Returns:
            The resulting ``tuple[p.Infra.SourceRewrite, ...],``.

        Raises:
            TypeError: If Rope's source lines do not satisfy their public contract.
            ValueError: If Rope wrapper body has inconsistent indentation.

        """
        lines = cls.runtime_callable("rope.base.codeanalyze", "SourceLinesAdapter")(
            source,
        )
        if not isinstance(lines, p.Infra.RopeSourceLines):
            msg = "Rope SourceLinesAdapter does not satisfy its public contract"
            raise TypeError(msg)
        regions = cls.ignored_regions(source)
        start = lines.get_line_start(layout.header_start)
        end = min(lines.get_line_end(layout.header_end) + 1, len(source))
        comments = "".join(
            source[begin:finish] + "\n"
            for begin, finish, _metadata in regions
            if start <= begin < end and source[begin:finish].startswith("#")
        )
        prefix = lines.get_line(layout.header_start)
        prefix = prefix[: len(prefix) - len(prefix.lstrip())]
        edits = [
            FlextInfraModelsTransformers.SourceRewrite(
                start=start,
                end=end,
                text="".join(
                    prefix + line for line in comments.splitlines(keepends=True)
                ),
            ),
        ]
        for number in range(layout.header_end + 1, layout.body_end + 1):
            offset = lines.get_line_start(number)
            line = lines.get_line(number)
            if layout.docstring_span is not None and (
                layout.docstring_span[0] <= number <= layout.docstring_span[1]
            ):
                continue
            if not line.strip() or any(
                begin < offset < finish
                for begin, finish, _metadata in regions
                if not source[begin:finish].startswith("#")
            ):
                continue
            if len(line) - len(line.lstrip()) < layout.indentation:
                msg = "Rope wrapper body has inconsistent indentation"
                raise ValueError(msg)
            edits.append(
                FlextInfraModelsTransformers.SourceRewrite(
                    start=offset,
                    end=offset + layout.indentation,
                    text="",
                ),
            )
        if layout.docstring_span is not None:
            edits.append(
                FlextInfraModelsTransformers.SourceRewrite(
                    start=lines.get_line_start(layout.docstring_span[0]),
                    end=min(
                        lines.get_line_end(layout.docstring_span[1]) + 1,
                        len(source),
                    ),
                    text="",
                ),
            )
        return tuple(edits)

    @classmethod
    def content_change(
        cls,
        resource: p.Infra.RopeResource,
        source: str,
        rewrites: Sequence[p.Infra.SourceRewrite],
    ) -> p.Infra.RopeChangeContents:
        """Preview checked, disjoint edits through Rope's change machinery.

        Returns:
            The resulting ``p.Infra.RopeChangeContents``.

        Raises:
            TypeError: If Rope ChangeCollector has an invalid contract; or if Rope
                ChangeCollector returned a non-source result; or if Rope ChangeContents
                returned an invalid content plan.
            ValueError: If Rope source edits overlap or escape their snapshot.

        """
        collector = cls.runtime_callable("rope.base.codeanalyze", "ChangeCollector")(
            source,
        )
        add = getattr(collector, "add_change", None)
        changed = getattr(collector, "get_changed", None)
        if not callable(add) or not callable(changed):
            msg = "Rope ChangeCollector has an invalid contract"
            raise TypeError(msg)
        end = 0
        for rewrite in sorted(rewrites, key=lambda item: (item.start, item.end)):
            if rewrite.start < end or not 0 <= rewrite.start <= rewrite.end <= len(
                source,
            ):
                msg = "Rope source edits overlap or escape their snapshot"
                raise ValueError(msg)
            add(rewrite.start, rewrite.end, rewrite.text)
            end = rewrite.end
        updated = changed()
        if updated is None:
            updated = source
        if not isinstance(updated, str):
            msg = "Rope ChangeCollector returned a non-source result"
            raise TypeError(msg)
        change = cls.runtime_callable("rope.base.change", "ChangeContents")(
            resource,
            updated,
        )
        if not isinstance(change, p.Infra.RopeChangeContents):
            msg = "Rope ChangeContents returned an invalid content plan"
            raise TypeError(msg)
        return change

    @classmethod
    def inline_variable_changes(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        offset: int,
        *,
        resources: Sequence[p.Infra.RopeResource],
        remove: bool = True,
    ) -> p.Infra.RopeChangeSet:
        """Plan assigned-name inlining with native occurrence and import handling.

        Returns:
            The SDK's unapplied content changes, with literal payloads untouched.

        Raises:
            TypeError: If the installed SDK violates the inlining contract.

        """
        inline = cls.runtime_callable("rope.refactor.inline", "InlineVariable")(
            project,
            resource,
            offset,
        )
        if not isinstance(inline, p.Infra.RopeInlineVariable):
            message = "Rope InlineVariable does not satisfy its native contract"
            raise TypeError(message)
        return inline.get_changes(remove=remove, resources=list(resources), docs=False)

    @classmethod
    def signature_addition_changes(
        cls,
        project: p.Infra.RopeProject,
        addition: p.Infra.RopeSignatureAddition,
        paths: Sequence[Path],
    ) -> p.Infra.RopeChangeSet:
        """Propagate one required keyword through native declaration identities.

        Returns:
            Unapplied native changes over the captured consumer resources.

        Raises:
            TypeError: If the SDK exposes no valid signature planning contract.
            ValueError: If a declaration or caller has no exact native owner.

        """
        binding = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, addition.target
        )
        target = binding.get_object()
        module, _line = binding.get_definition_location()
        resource = None if module is None else module.get_resource()
        if (
            not FlextInfraUtilitiesRopeRuntimeTypes.py_function(target)
            or resource is None
        ):
            message = f"{addition.id}: signature target has no function source"
            raise ValueError(message)
        resource, offset = cls._declaration_position(
            project, binding, paths, f"{addition.id}: signature declaration"
        )

        callers = {
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project, name
            ).get_object(): value
            for name, value in addition.call_values.items()
        }

        def call_value(
            caller: p.Infra.RopePyModule, occurrence: p.Infra.RopeOccurrence
        ) -> str | None:
            scope = caller.get_scope().get_inner_scope_for_line(occurrence.lineno)
            while scope is not None:
                if scope.pyobject in callers:
                    return callers[scope.pyobject]
                scope = scope.parent
            if addition.default is not None:
                return None
            message = (
                f"{addition.id}: no native caller value for "
                f"{caller.get_name()}:{occurrence.lineno}"
            )
            raise ValueError(message)

        change = cls.runtime_callable(
            "rope.refactor.change_signature", "ArgumentAdder"
        )(
            0,
            addition.parameter,
            default=addition.default,
            value=call_value,
            keyword_only=True,
            annotation=addition.annotation,
        )
        planner = cls.runtime_callable(
            "rope.refactor.change_signature", "ChangeSignature"
        )(project, resource, offset)
        get_changes = getattr(planner, "get_changes", None)
        if not callable(get_changes):
            message = "Rope ChangeSignature exposes no native planning contract"
            raise TypeError(message)
        changes = get_changes(
            [change],
            resources=[
                FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
                for path in paths
            ],
        )
        if not isinstance(changes, p.Infra.RopeChangeSet):
            message = "Rope ChangeSignature returned an invalid change set"
            raise TypeError(message)
        return changes

    @classmethod
    def signature_replacement_changes(
        cls,
        project: p.Infra.RopeProject,
        removal: p.Infra.RopeSignatureRemoval,
        paths: Sequence[Path],
    ) -> p.Infra.RopeChangeSet | None:
        """Replace exact parameter reads through native semantic restructuring.

        Returns:
            Unapplied native changes, or None when the parameter is retired.

        Raises:
            ValueError: The target or its lexical scope cannot be resolved.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        target = runtime.qualified_name(project, removal.target).get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(target):
            message = f"{removal.id}: signature target has no function source"
            raise ValueError(message)
        parameter = target.get_parameters().get(removal.parameter)
        if parameter is None:
            return None

        def admitted(
            module: p.Infra.RopePyModule, match: p.Infra.RopeContractMatch
        ) -> bool:
            node = match.get_ast(removal.parameter)
            if not isinstance(node, ast.Name):
                return False
            scope = module.get_scope().get_inner_scope_for_line(node.lineno)
            if not runtime.same_name(
                parameter, runtime.expression_name(scope, node.id)
            ):
                return False
            if not isinstance(node.ctx, ast.Load):
                message = f"{removal.id}: parameter writes cannot be replaced"
                raise TypeError(message)
            if scope is not target.get_scope():
                message = (
                    f"{removal.id}: replacement escapes its declared lexical scope"
                )
                raise ValueError(message)
            return True

        return cls.restructure_changes(
            project,
            m.Infra.RopeRestructureRequest(
                pattern=f"${{{removal.parameter}}}",
                goal=removal.replacement,
                arguments={removal.parameter: "exact"},
                resources=tuple(
                    runtime.file_resource_at(project, path) for path in paths
                ),
                match_filter=admitted,
            ),
        )

    @classmethod
    def signature_removal_changes(
        cls,
        project: p.Infra.RopeProject,
        removal: p.Infra.RopeSignatureRemoval,
        paths: Sequence[Path],
    ) -> p.Infra.RopeChangeSet | None:
        """Retire a body-free parameter through native signature propagation.

        Returns:
            Unapplied native changes, or None when the parameter is retired.

        Raises:
            ValueError: The target is not a function or still reads its parameter.
            TypeError: The SDK returns an invalid native change set.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.qualified_name(project, removal.target)
        target = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(target):
            message = f"{removal.id}: signature target has no function source"
            raise ValueError(message)
        parameters = tuple(target.get_param_names())
        if removal.parameter not in parameters:
            return None
        resource, offset = cls._declaration_position(
            project, binding, paths, f"{removal.id}: signature declaration"
        )
        finder = cls.create_occurrence_finder(
            project,
            removal.parameter,
            target.get_parameters()[removal.parameter],
            imports=False,
            in_hierarchy=False,
        )
        if any(
            occurrence.lineno >= target.get_scope().get_body_start()
            for occurrence in finder.find_occurrences(resource=resource)
        ):
            message = f"{removal.id}: parameter still has native body references"
            raise ValueError(message)
        change = cls.runtime_callable(
            "rope.refactor.change_signature", "ArgumentRemover"
        )(parameters.index(removal.parameter))
        planner = cls.runtime_callable(
            "rope.refactor.change_signature", "ChangeSignature"
        )(project, resource, offset)
        get_changes = getattr(planner, "get_changes", None)
        if not callable(get_changes):
            message = "Rope ChangeSignature exposes no native planning contract"
            raise TypeError(message)
        changes = get_changes(
            [change],
            resources=[runtime.file_resource_at(project, path) for path in paths],
        )
        if not isinstance(changes, p.Infra.RopeChangeSet):
            message = "Rope ChangeSignature returned an invalid change set"
            raise TypeError(message)
        return changes

    @classmethod
    def _declaration_position(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        paths: Sequence[Path],
        label: str,
    ) -> tuple[p.Infra.RopeResource, int]:
        """Retain a unique native declaration occurrence inside captured sources.

        Returns:
            The source resource and its native declaration-name offset.

        Raises:
            ValueError: A declaration lacks captured source or a unique occurrence.

        """
        target = cls.require_named_object(binding.get_object(), label)
        module, _line = binding.get_definition_location()
        resource = None if module is None else module.get_resource()
        if resource is None:
            message = f"{label} has no source"
            raise ValueError(message)
        if Path(resource.real_path).resolve() not in paths:
            message = f"{label} is outside captured sources"
            raise ValueError(message)
        definitions = tuple(
            occurrence.get_word_range()[0]
            for occurrence in cls.create_occurrence_finder(
                project, target.get_name(), binding, imports=False, in_hierarchy=False
            ).find_occurrences(resource=resource)
            if occurrence.is_defined()
        )
        if len(definitions) != 1:
            message = f"{label} is ambiguous"
            raise ValueError(message)
        return resource, definitions[0]

    @classmethod
    def method_transfer_changes(
        cls,
        project: p.Infra.RopeProject,
        transfer: p.Infra.RopeMethodTransfer,
        paths: Sequence[Path],
        resolver: p.Infra.RopeSourceMemberResolver,
    ) -> p.Infra.RopeChangeSet | None:
        """Delegate existing-class method ownership to the native SDK batch.

        Returns:
            Native unapplied changes, or None for an already completed transfer.

        Raises:
            TypeError: A native owner or SDK result violates its typed contract.
            ValueError: If ``len(moves) != 1``; or if ``transfer.receiver_rewrites``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        destination = runtime.qualified_name(
            project, transfer.destination[1], module_name=transfer.destination[0]
        )
        owner = destination.get_object()
        if not types.py_class(owner):
            message = f"{transfer.id}: destination is not a native source class"
            raise TypeError(message)
        destination_resource, destination_offset = cls._declaration_position(
            project, destination, paths, f"{transfer.id}: destination"
        )
        moves = cls._method_transfer_moves(project, transfer, paths, owner)
        if not moves:
            return None
        source_binding = cls.runtime_callable("rope.base.evaluate", "eval_location")(
            project.get_pymodule(moves[0][0]), moves[0][1]
        )
        source_method = (
            source_binding.get_object()
            if isinstance(source_binding, p.Infra.RopePyName)
            else None
        )
        if types.py_function(source_method) and source_method.get_kind() == "method":
            if len(moves) != 1:
                msg = (
                    f"{transfer.id}: instance methods transfer one declaration at a "
                    f"time"
                )
                raise ValueError(msg)
            cls.attribute_read_proofs(
                project,
                moves[0][0],
                source_method,
                resolver,
            )
            planner_name = "get_instance_class_changes"
        else:
            if transfer.receiver_rewrites:
                msg = f"{transfer.id}: receiver rewrites require an instance method"
                raise ValueError(msg)
            planner_name = "get_class_changes"
        planner = getattr(
            cls.runtime_type("rope.refactor.move", "MoveMethod"),
            planner_name,
            None,
        )
        if not callable(planner):
            message = "Rope MoveMethod exposes no native class-transfer contract"
            raise TypeError(message)
        arguments = {
            "resources": [runtime.file_resource_at(project, path) for path in paths]
        }
        if planner_name == "get_instance_class_changes":
            changes = planner(
                project,
                moves,
                destination_resource,
                destination_offset,
                receiver_rewrites=dict(transfer.receiver_rewrites),
                resolve_binding=lambda scope, node: cls._native_expression_binding(
                    project, scope, node, resolver
                ),
                **arguments,
            )
        else:
            changes = planner(
                project,
                moves,
                destination_resource,
                destination_offset,
                **arguments,
            )
        if not isinstance(changes, p.Infra.RopeChangeSet):
            message = "Rope MoveMethod returned an invalid change set"
            raise TypeError(message)
        return changes

    @classmethod
    def _method_transfer_moves(
        cls,
        project: p.Infra.RopeProject,
        transfer: p.Infra.RopeMethodTransfer,
        paths: Sequence[Path],
        owner: p.Infra.RopeSourceClass,
    ) -> list[tuple[p.Infra.RopeResource, int, str]]:
        """Collect source-owned methods, retaining completed destination transfers.

        Returns:
            Source resource, declaration offset, and method-name triples.

        Raises:
            TypeError: A declared source owner is not a native source class.
            ValueError: A source method is malformed or has no valid owner.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        moves: list[tuple[p.Infra.RopeResource, int, str]] = []
        for module, qualified in transfer.methods:
            class_name, separator, name = qualified.rpartition(".")
            if not separator:
                message = f"{transfer.id}: source must name a class method: {qualified}"
                raise ValueError(message)
            source = runtime.qualified_name(
                project, class_name, module_name=module
            ).get_object()
            if not types.py_class(source):
                message = f"{transfer.id}: source is not a native source class"
                raise TypeError(message)
            binding = source.get_attributes().get(name)
            function = None if binding is None else binding.get_object()
            if (
                binding is not None
                and types.py_function(function)
                and function.get_name() == name
                and (enclosing := function.get_scope().parent) is not None
                and enclosing.pyobject is source
            ):
                resource, offset = cls._declaration_position(
                    project, binding, paths, f"{transfer.id}: {qualified}"
                )
                moves.append((resource, offset, name))
                continue
            published = owner.get_attributes().get(name)
            settled = None if published is None else published.get_object()
            enclosing = (
                settled.get_scope().parent
                if types.py_function(settled) and settled.get_name() == name
                else None
            )
            if (
                enclosing is None
                or enclosing.pyobject is not owner
                or (binding is not None and function is not settled)
            ):
                message = f"{transfer.id}: source method is not owned: {qualified}"
                raise ValueError(message)
        return moves

    @classmethod
    def restructure_changes(
        cls,
        rope_project: p.Infra.RopeProject,
        request: p.Infra.RopeRestructureRequest,
    ) -> p.Infra.RopeChangeSet:
        """Plan Rope 1.14 semantic changes without invoking Project.do.

        Args:
            rope_project: Native Rope project owning the restructured sources.
            request: Immutable native pattern, admission, and import policies.

        Returns:
            The resulting ``p.Infra.RopeChangeSet``.

        Raises:
            TypeError: If rope Restructure does not satisfy its public planning
                contract.

        """
        factory = cls.runtime_callable(
            "flext_infra._utilities._rope.restructure", "FlextInfraRopeRestructure"
        )
        restructuring = factory(
            rope_project,
            request,
        )
        if not isinstance(restructuring, p.Infra.RopeRestructure):
            msg = "rope Restructure does not satisfy its public planning contract"
            raise TypeError(msg)
        changes = restructuring.get_changes(resources=list(request.resources))
        u.Cli.info(
            "Rope restructuring "
            f"matched={restructuring.matched_count} "
            f"admitted={restructuring.admitted_count} pattern={request.pattern}"
        )
        return changes

    @classmethod
    def create_move(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int | None,
    ) -> t.Infra.RopeMoveGlobal:
        create = cls.runtime_callable("rope.refactor.move", "create_move")
        mover = create(rope_project, resource, offset)
        if not isinstance(mover, p.Infra.RopeMoveGlobal):
            msg = "rope create_move did not return MoveGlobal-compatible object"
            raise TypeError(msg)
        return mover

    @classmethod
    def move_class_changes(
        cls,
        project: p.Infra.RopeProject,
        origin: p.Infra.RopeResource,
        origin_offset: int,
        destination: p.Infra.RopeResource,
        *,
        options: p.Infra.RopeMoveOptions,
    ) -> p.Infra.RopeChangeSet:
        """Delegate nested-class transfer to its native SDK owner without effects.

        Returns:
            The native unapplied changes, preserving its first refusal.

        Raises:
            TypeError: The installed native mover lacks the class-transfer contract.

        """
        mover = cls.create_move(project, origin, origin_offset)
        if not isinstance(
            mover, cls.runtime_type("rope.refactor.move", "MoveClass")
        ) or not isinstance(mover, p.Infra.RopeMoveClass):
            message = "native Rope class transfer requires MoveClass"
            raise TypeError(message)
        return mover.get_changes(
            destination,
            resources=options.resources,
            destination_offset=options.destination_offset,
            match_filter=options.match_filter,
        )

    @classmethod
    def preserved_receiver_reference_filter(
        cls,
        project: p.Infra.RopeProject,
        public_routes: Sequence[tuple[str, str]],
    ) -> Callable[[p.Infra.RopeOccurrence], bool]:
        """Retain explicitly observed public receivers during native relocation.

        Returns:
            The occurrence predicate for references that may be rewritten.

        """
        receivers = tuple(
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                project, route.rpartition(".")[0], module_name=module
            ).get_object()
            for module, route in public_routes
        )

        def selected(occurrence: p.Infra.RopeOccurrence) -> bool:
            names = occurrence.get_primary_and_pyname()
            if names is None or names[0] is None:
                return True
            receiver = names[0].get_object()
            return all(receiver is not public for public in receivers)

        return selected

    @classmethod
    def move_binding_changes(
        cls,
        project: p.Infra.RopeProject,
        origin: p.Infra.RopeResource,
        origin_offset: int,
        destination: p.Infra.RopeResource,
        *,
        options: p.Infra.RopeMoveOptions,
    ) -> p.Infra.RopeChangeSet:
        """Delegate a resolved declaration to its native class or global mover.

        Returns:
            Native unapplied changes retaining the source binding's kind.

        Raises:
            TypeError: The native source or mover does not satisfy its contract.

        """
        source_binding = cls.runtime_callable("rope.base.evaluate", "eval_location")(
            project.get_pymodule(origin), origin_offset
        )
        if not isinstance(source_binding, p.Infra.RopePyName):
            message = "native move source has no declaration binding"
            raise TypeError(message)
        if FlextInfraUtilitiesRopeRuntimeTypes.py_class(source_binding.get_object()):
            mover = cls.runtime_callable("rope.refactor.move", "MoveClass")(
                project, origin, origin_offset
            )
            if not isinstance(mover, p.Infra.RopeMoveClass):
                message = "native Rope class mover violates its planning contract"
                raise TypeError(message)
            return mover.get_changes(
                destination,
                resources=options.resources,
                destination_offset=options.destination_offset,
                match_filter=options.match_filter,
            )
        mover = cls.create_move(project, origin, origin_offset)
        return mover.get_changes(destination, resources=options.resources)

    @classmethod
    def rename_changes(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int | None,
        new_name: str,
        *,
        options: p.Infra.RopeRenameOptions,
    ) -> t.Infra.RopeChangeSet:
        renamer_factory = cls.runtime_callable("rope.refactor.rename", "Rename")
        renamer = renamer_factory(rope_project, resource, offset)
        get_changes = getattr(renamer, "get_changes", None)
        if not callable(get_changes):
            msg = "rope Rename does not expose callable get_changes"
            raise TypeError(msg)
        changes = get_changes(
            new_name,
            resources=list(options.resources),
            in_hierarchy=options.in_hierarchy,
            docs=options.docs,
        )
        if not isinstance(changes, p.Infra.RopeChangeSet):
            msg = "rope Rename returned invalid ChangeSet"
            raise TypeError(msg)
        return changes

    @staticmethod
    def _identifier_at(source: str, offset: int) -> str:
        """Return the identifier that starts at a source offset.

        Returns:
            The maximal identifier text beginning at ``offset``.

        """
        end = offset
        while end < len(source) and (source[end].isalnum() or source[end] == "_"):
            end += 1
        return source[offset:end]

    @classmethod
    def rename_all_changes(
        cls,
        projects: Sequence[p.Infra.RopeProject],
        resource: p.Infra.RopeResource,
        offset: int | None,
        new_name: str,
        *,
        sources: Mapping[Path, str],
    ) -> tuple[tuple[p.Infra.RopeProject, p.Infra.RopeChangeSet], ...]:
        """Preview every elected project before any publication or Project.do.

        Returns:
            Native per-project changes, including module resource moves.

        Raises:
            ValueError: If no producer is elected or native module ownership changes.

        """
        if not projects:
            msg = "native rename requires a producer project"
            raise ValueError(msg)
        producer = cls.require_semantic_module(projects[0].get_pymodule(resource))
        module_name = producer.get_name()
        # Each project edits only its own sources that carry the identifier.
        retired = (
            module_name.rpartition(".")[2]
            if offset is None
            else cls._identifier_at(sources[Path(resource.real_path)], offset)
        )
        changes: list[tuple[p.Infra.RopeProject, p.Infra.RopeChangeSet]] = []
        resource_path = Path(resource.real_path)
        for project in projects:
            # Foreign declarations must use the same authenticated resource owner
            # as imports, not MultiProjectRefactoring's global NoProject resolver.
            elected = project.find_module(module_name)
            if elected is None or Path(elected.real_path) != resource_path:
                # A multi-root workspace names the same file from each root; the
                # producer name is not resolvable verbatim in a consumer project.
                project_root = Path(project.root.real_path)
                if resource_path.is_relative_to(project_root):
                    relative = resource_path.relative_to(project_root).with_suffix("")
                    parts = list(relative.parts)
                    if parts and parts[-1] == c.Infra.INIT_PY:
                        parts.pop()
                    elected = project.find_module(".".join(parts))
            if elected is None or Path(elected.real_path) != resource_path:
                msg = f"native rename lost its elected module: {module_name}"
                raise ValueError(msg)
            changes.append((
                project,
                cls.rename_changes(
                    project,
                    elected,
                    offset,
                    new_name,
                    options=m.Infra.RopeRenameOptions(
                        resources=tuple(
                            candidate
                            for candidate in project.get_python_files()
                            if Path(candidate.real_path) in sources
                            and project.source_owned(Path(candidate.real_path))
                            and (
                                candidate.real_path == resource.real_path
                                or (
                                    offset is None
                                    and resource.is_folder()
                                    and Path(candidate.real_path).is_relative_to(
                                        Path(resource.real_path)
                                    )
                                )
                                or retired in sources[Path(candidate.real_path)]
                            )
                        ),
                        in_hierarchy=True,
                        docs=True,
                    ),
                ),
            ))
        return tuple(changes)


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeRefactors"]
