"""Source-proven own-method dispatch through the enclosing facade MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

import libcst as cst
from libcst.metadata import Assignment, ParentNodeProvider, Scope, ScopeProvider


class FlextInfraUtilitiesSemanticCutoverOwnMro:
    """Preserve lexical bindings while removing concrete own-method dispatch."""

    @classmethod
    def rewrite_own_method_mro_calls(cls, source: str) -> tuple[str, tuple[str, ...]]:
        """Bind own static/class helpers through the current facade receiver.

        Class declarations are authenticated by LibCST scope assignments. Local
        shadows and references to another class remain unchanged. Nested entity
        classes retain their own receiver; they never acquire the outer facade.

        Returns:
            Rewritten source and the actual methods whose dispatch changed.

        """
        visitor = cls._Dispatch()
        rewritten = cst.metadata.MetadataWrapper(cst.parse_module(source)).visit(
            visitor
        )
        return rewritten.code, tuple(visitor.messages)

    class _Dispatch(cst.CSTTransformer):
        """Resolve lexical ownership before choosing a method's MRO receiver."""

        METADATA_DEPENDENCIES = (ParentNodeProvider, ScopeProvider)

        def __init__(self) -> None:
            self.classes: list[cst.ClassDef] = []
            self.functions: list[tuple[cst.ClassDef, cst.FunctionDef] | None] = []
            self.changed: set[cst.FunctionDef] = set()
            self.messages: list[str] = []

        @staticmethod
        def _role(method: cst.FunctionDef) -> str:
            decorators = {
                item.decorator.value
                for item in method.decorators
                if isinstance(item.decorator, cst.Name)
            }
            return (
                "static"
                if "staticmethod" in decorators
                else ("class" if "classmethod" in decorators else "instance")
            )

        @override
        def visit_ClassDef(self, node: cst.ClassDef) -> None:
            self.classes.append(node)

        @override
        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            """Leave the exact declaration whose lexical context was entered.

            Returns:
                The transformed declaration.

            Raises:
                ValueError: The traversal lost the declaring class.

            """
            if self.classes.pop() is not original_node:
                message = "Own MRO rewrite lost its declaring class"
                raise ValueError(message)
            return updated_node

        @override
        def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
            parent = self.classes[-1] if self.classes else None
            direct = parent is not None and node in parent.body.body
            self.functions.append(
                (parent, node)
                if direct and parent is not None
                else (self.functions[-1] if self.functions else None)
            )

        def _in_body(self, node: cst.CSTNode, method: cst.FunctionDef) -> bool:
            """Distinguish executable bodies from decorators and defaults.

            Returns:
                Whether the node belongs to the declaring method's body.

            Raises:
                TypeError: Required parent metadata is not a CST node.

            """
            parent = node
            while parent is not method and parent is not method.body:
                enclosing = self.get_metadata(ParentNodeProvider, parent)
                if not isinstance(enclosing, cst.CSTNode):
                    message = "Own MRO rewrite requires parent-node metadata"
                    raise TypeError(message)
                parent = enclosing
            return parent is method.body

        def _scope(self, node: cst.Name) -> Scope:
            """Require the actual lexical scope supplied by LibCST.

            Returns:
                The resolved scope.

            Raises:
                TypeError: Required scope metadata is unavailable.

            """
            scope = self.get_metadata(ScopeProvider, node)
            if not isinstance(scope, Scope):
                message = "Own MRO rewrite requires lexical-scope metadata"
                raise TypeError(message)
            return scope

        @staticmethod
        def _target(owner: cst.ClassDef, attribute: str) -> cst.FunctionDef | None:
            return next(
                (
                    member
                    for member in owner.body.body
                    if isinstance(member, cst.FunctionDef)
                    and member.name.value == attribute
                ),
                None,
            )

        def _receiver(
            self, owner: cst.ClassDef, method: cst.FunctionDef, scope: Scope
        ) -> str:
            """Choose a receiver without capturing an existing local binding.

            Returns:
                The method's current or newly declared receiver.

            Raises:
                ValueError: A receiver is absent or would capture a binding.

            """
            parameters = (
                *method.params.posonly_params,
                *method.params.params,
                *method.params.kwonly_params,
            )
            if self._role(method) == "static":
                if any(p.name.value == "cls" for p in parameters) or scope["cls"]:
                    message = (
                        "Own MRO receiver would capture a parameter: "
                        f"{owner.name.value}.{method.name.value}"
                    )
                    raise ValueError(message)
                return "cls"
            if parameters:
                return parameters[0].name.value
            message = (
                "Own MRO method has no receiver: "
                f"{owner.name.value}.{method.name.value}"
            )
            raise ValueError(message)

        @override
        def leave_Attribute(
            self, original_node: cst.Attribute, updated_node: cst.Attribute
        ) -> cst.Attribute:
            """Rewrite a scope-proven own helper's executable reference.

            Returns:
                The original attribute or its inherited receiver reference.

            Raises:
                ValueError: An instance-method reference is unbound.

            """
            context = self.functions[-1] if self.functions else None
            if context is None or not isinstance(original_node.value, cst.Name):
                return updated_node
            owner, method = context
            if original_node.value.value != owner.name.value or not self._in_body(
                original_node, method
            ):
                return updated_node
            target = self._target(owner, original_node.attr.value)
            if target is None:
                return updated_node
            scope = self._scope(original_node.value)
            bindings = scope[owner.name.value]
            if len(bindings) != 1:
                return updated_node
            binding = next(iter(bindings))
            if not isinstance(binding, Assignment) or binding.node is not owner:
                return updated_node
            if self._role(target) == "instance":
                message = (
                    "Own instance method retains an unbound reference: "
                    f"{owner.name.value}.{target.name.value}"
                )
                raise ValueError(message)
            receiver = self._receiver(owner, method, scope)
            self.changed.add(method)
            return updated_node.with_changes(value=cst.Name(receiver))

        @override
        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            """Promote changed static methods while preserving their signatures.

            Returns:
                The transformed method and its inherited dispatch.

            Raises:
                ValueError: A changed method lost its declaring context.

            """
            context = self.functions.pop()
            if original_node not in self.changed:
                return updated_node
            if context is None:
                message = "Own MRO rewrite lost its declaring method"
                raise ValueError(message)
            self.messages.append(
                f"own-method-mro:{context[0].name.value}.{original_node.name.value}"
            )
            if self._role(original_node) != "static":
                return updated_node
            parameters = updated_node.params
            receiver = cst.Param(cst.Name("cls"))
            if parameters.posonly_params:
                parameters = parameters.with_changes(
                    posonly_params=(receiver, *parameters.posonly_params)
                )
            else:
                parameters = parameters.with_changes(
                    params=(receiver, *parameters.params)
                )
            return updated_node.with_changes(
                params=parameters,
                decorators=tuple(
                    item.with_changes(decorator=cst.Name("classmethod"))
                    if isinstance(item.decorator, cst.Name)
                    and item.decorator.value == "staticmethod"
                    else item
                    for item in updated_node.decorators
                ),
            )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverOwnMro"]
