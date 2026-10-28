"""Rope DSL declaration models — semantic operations as catalog data.

One typed document per law (ADR-028 Decision 18): the declarative surface for
semantic engine operations, interpreted against the single rope index per
repository invocation (ADR-028 Decision 17 amendment 2026-10-28; campaign
`flext-pipol` / `flext-u9h2i`). The vocabulary is closed: extending it is a
model evolution, never per-rule code.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field as MField

from flext_infra import m, t


class FlextInfraModelsConfigRopeDsl:
    """Declarative rope-operation documents (engine-map section 8)."""

    class Operation(StrEnum):
        """Closed vocabulary of native rope operations the DSL admits."""

        ORGANIZE_IMPORTS = "organize-imports"
        RENAME = "rename"
        MOVE = "move"
        RESTRUCTURE = "restructure"
        TRANSFORM = "transform"

    class TransformVerb(StrEnum):
        """Closed vocabulary of first-class semantic rewrites."""

        ELECT_BARE_LETTER = "elect-bare-letter"
        DROP_ALIAS_BINDING = "drop-alias-binding"

    class Selector(m.ArbitraryTypesModel):
        """One typed query over the single rope index.

        Attributes:
            module_pattern: Module-name pattern the rule applies to
                (`fnmatch` vocabulary over dotted names, e.g. ``flext_*``).
            symbol_pattern: Optional symbol-name pattern (``fnmatch``).
            import_shape: Optional import-statement shape; `$MODULE`,
                `$NAME` and `$ALIAS` are the interpolated captures.

        """

        module_pattern: Annotated[
            t.NonEmptyStr,
            MField(description="fnmatch pattern over dotted module names"),
        ]
        symbol_pattern: Annotated[
            str,
            MField(default="", description="fnmatch pattern over symbol names"),
        ]
        import_shape: Annotated[
            str,
            MField(
                default="",
                description=(
                    "Import shape with $MODULE/$NAME/$ALIAS captures, e.g. "
                    "'from $MODULE import $NAME as $ALIAS'"
                ),
            ),
        ]

    class Constraint(m.ArbitraryTypesModel):
        """Declared limits a match must respect.

        Attributes:
            letters: Facade letters admitted when the rule reasons about
                letters (subset of c/t/p/m/u; empty means unconstrained).
            max_occurrences: Upper bound of matched sites per application.

        """

        letters: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            MField(
                default=(),
                description="Admitted facade letters (c/t/p/m/u subset)",
            ),
        ]
        max_occurrences: Annotated[
            int,
            MField(default=0, ge=0, description="Match cap; 0 means uncapped"),
        ]

    class Rewrite(m.ArbitraryTypesModel):
        """The declared outcome of one rule application.

        Attributes:
            verb: The transform verb (transform operations).
            target_module: Destination dotted module (move operations).
            new_name: Destination symbol name (rename operations).

        """

        verb: Annotated[
            FlextInfraModelsConfigRopeDsl.TransformVerb | None,
            MField(default=None, description="Transform verb to apply"),
        ]
        target_module: Annotated[
            str,
            MField(default="", description="Destination module (move)"),
        ]
        new_name: Annotated[
            str,
            MField(default="", description="Destination name (rename)"),
        ]

    class Rule(m.ArbitraryTypesModel):
        """One rope DSL rule: id, operation, selector, constraint, rewrite.

        Attributes:
            id: Stable rule identity (one rule per law).
            operation: The native rope operation.
            selector: Where the rule applies.
            constraint: Declared limits.
            rewrite: The declared outcome.

        """

        id: Annotated[t.NonEmptyStr, MField(description="Stable rule identity")]
        operation: FlextInfraModelsConfigRopeDsl.Operation
        selector: FlextInfraModelsConfigRopeDsl.Selector
        constraint: Annotated[
            FlextInfraModelsConfigRopeDsl.Constraint,
            MField(
                default_factory=FlextInfraModelsConfigRopeDsl.Constraint,
            ),
        ]
        rewrite: Annotated[
            FlextInfraModelsConfigRopeDsl.Rewrite,
            MField(
                default_factory=FlextInfraModelsConfigRopeDsl.Rewrite,
            ),
        ]

        @m.model_validator(mode="after")
        def _require_rewrite_shape(self) -> Self:
            """Keep every operation's rewrite fields lawful.

            Returns:
                The validated rule.

            Raises:
                ValueError: When the operation lacks its required rewrite.

            """
            if (
                self.operation is FlextInfraModelsConfigRopeDsl.Operation.TRANSFORM
                and self.rewrite.verb is None
            ):
                msg = f"rope rule {self.id}: transform requires a rewrite verb"
                raise ValueError(msg)
            if (
                self.operation is FlextInfraModelsConfigRopeDsl.Operation.MOVE
                and not self.rewrite.target_module
            ):
                msg = f"rope rule {self.id}: move requires target_module"
                raise ValueError(msg)
            if (
                self.operation is FlextInfraModelsConfigRopeDsl.Operation.RENAME
                and not self.rewrite.new_name
            ):
                msg = f"rope rule {self.id}: rename requires new_name"
                raise ValueError(msg)
            return self

    class Catalog(m.ArbitraryTypesModel):
        """The declared rope rule set (`Infra.codegen.rope`)."""

        rules: Annotated[
            t.VariadicTuple[FlextInfraModelsConfigRopeDsl.Rule],
            MField(default=(), description="Declared semantic rules"),
        ]

        @m.model_validator(mode="after")
        def _require_unique_ids(self) -> Self:
            """Reject duplicate rule identities.

            Returns:
                The validated catalog.

            Raises:
                ValueError: When two rules share one identity.

            """
            ids = [rule.id for rule in self.rules]
            if len(set(ids)) != len(ids):
                msg = f"rope catalog rule ids must be unique: {sorted(ids)}"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsConfigRopeDsl"]
