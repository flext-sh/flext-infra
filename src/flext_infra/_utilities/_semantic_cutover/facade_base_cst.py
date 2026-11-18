"""Concrete-syntax rewrite that extends a facade by its parent's class name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

import libcst as cst

from flext_infra import c, t
from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames


class FlextInfraUtilitiesSemanticCutoverFacadeBaseCst:
    """Preserve layout while a facade base moves from letter to class."""

    class _FacadeBaseTransformer(cst.CSTTransformer):
        """Swap the letter import and base for the parent's declared class."""

        def __init__(
            self,
            *,
            shape: tuple[str, str, str, str],
            owner: str,
            owner_bound: bool,
            local_rebound: bool,
        ) -> None:
            super().__init__()
            self.module, self.imported, self.local, self.facade = shape
            self.owner = owner
            self.owner_bound = owner_bound
            self.local_rebound = local_rebound
            self.depth = 0

        @override
        def visit_ClassDef(self, node: t.Infra.Cst.ClassDef) -> bool:
            del node
            self.depth += 1
            return True

        @override
        def leave_ClassDef(
            self,
            original_node: t.Infra.Cst.ClassDef,
            updated_node: t.Infra.Cst.ClassDef,
        ) -> t.Infra.Cst.ClassDef:
            self.depth -= 1
            if self.depth or original_node.name.value != self.facade:
                return updated_node
            return updated_node.with_changes(
                bases=[
                    base.with_changes(value=cst.Name(self.owner))
                    if isinstance(base.value, c.Infra.Cst.Name)
                    and base.value.value == self.local
                    else base
                    for base in updated_node.bases
                ],
            )

        @override
        def visit_FunctionDef(self, node: t.Infra.Cst.FunctionDef) -> bool:
            del node
            self.depth += 1
            return True

        @override
        def leave_FunctionDef(
            self,
            original_node: t.Infra.Cst.FunctionDef,
            updated_node: t.Infra.Cst.FunctionDef,
        ) -> t.Infra.Cst.FunctionDef:
            del original_node
            self.depth -= 1
            return updated_node

        @override
        def leave_Name(
            self,
            original_node: t.Infra.Cst.Name,
            updated_node: t.Infra.Cst.Name,
        ) -> t.Infra.Cst.Name:
            # A private import alias is never rebound, so every read of it is
            # the parent class; the letter itself keeps its deferred reads.
            if (
                not self.local_rebound
                and self.local != self.imported
                and original_node.value == self.local
            ):
                return updated_node.with_changes(value=self.owner)
            return updated_node

        @override
        def leave_ImportFrom(
            self,
            original_node: t.Infra.Cst.ImportFrom,
            updated_node: t.Infra.Cst.ImportFrom,
        ) -> t.Infra.Cst.ImportFrom | t.Infra.Cst.RemovalSentinel:

            if (
                self.depth
                or original_node.relative
                or isinstance(original_node.names, c.Infra.Cst.ImportStar)
                or isinstance(updated_node.names, c.Infra.Cst.ImportStar)
                or FlextInfraUtilitiesQualifiedNames.dotted_name(
                    original_node.module,
                )
                != self.module
            ):
                return updated_node
            retained = self._retained_aliases(original_node, updated_node)
            if not retained:
                return cst.RemoveFromParent()
            return updated_node.with_changes(
                names=[
                    *retained[:-1],
                    retained[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT),
                ],
            )

        def _retained_aliases(
            self,
            original_node: t.Infra.Cst.ImportFrom,
            updated_node: t.Infra.Cst.ImportFrom,
        ) -> list[t.Infra.Cst.ImportAlias]:
            """Keep unrelated aliases and the owner-bound replacement.

            Returns:
                The aliases retained in the rewritten ``from`` import.

            """
            retained: list[t.Infra.Cst.ImportAlias] = []
            if isinstance(
                original_node.names,
                c.Infra.Cst.ImportStar,
            ) or isinstance(updated_node.names, c.Infra.Cst.ImportStar):
                return []
            for original, updated in zip(
                original_node.names,
                updated_node.names,
                strict=True,
            ):
                name = FlextInfraUtilitiesQualifiedNames.dotted_name(original.name)
                bound = (
                    FlextInfraUtilitiesQualifiedNames.dotted_name(
                        original.asname.name,
                    )
                    if original.asname is not None
                    and isinstance(original.asname.name, c.Infra.Cst.Name)
                    else name
                )
                if name != self.imported or bound != self.local:
                    retained.append(updated)
                elif not self.owner_bound:
                    retained.append(
                        updated.with_changes(
                            name=cst.Name(self.owner),
                            asname=None,
                        ),
                    )
            return retained

        @override
        def leave_AnnAssign(
            self,
            original_node: t.Infra.Cst.AnnAssign,
            updated_node: t.Infra.Cst.AnnAssign,
        ) -> t.Infra.Cst.AnnAssign | t.Infra.Cst.Assign:
            # An annotated rebind declares a variable; the letter must stay the
            # implicit alias of its facade class for annotations to resolve.
            if (
                self.depth
                or not isinstance(original_node.target, c.Infra.Cst.Name)
                or original_node.target.value
                != (self.local if self.local_rebound else self.imported)
                or not isinstance(original_node.value, c.Infra.Cst.Name)
                or original_node.value.value != self.facade
            ):
                return updated_node
            return cst.Assign(
                targets=[cst.AssignTarget(target=original_node.target)],
                value=cst.Name(self.facade),
            )

    @classmethod
    def _rewrite_facade_base_source(
        cls,
        source: str,
        *,
        shape: tuple[str, str, str, str],
        owner: str,
        owner_bound: bool,
        local_rebound: bool,
    ) -> str:
        """Return the facade source extending ``owner`` with its layout kept.

        Returns:
            The facade source extending ``owner`` with its layout kept.

        """
        return (
            cst
            .parse_module(source)
            .visit(
                cls._FacadeBaseTransformer(
                    shape=shape,
                    owner=owner,
                    owner_bound=owner_bound,
                    local_rebound=local_rebound,
                ),
            )
            .code
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverFacadeBaseCst"]
