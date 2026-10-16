"""Public accessor warning detection for semantic migration review.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t
    from flext_infra.refactor._accessor_origin import FlextInfraAccessorOriginResolver


class FlextInfraAccessorMigrationWarningsMixin:
    """Identify loose public accessors needing manual contract review."""

    _AUTOMATED_RULES: ClassVar[t.VariadicTuple[m.Infra.AccessorMigrationRule]] = tuple(
        m.Infra.AccessorMigrationRule(
            source_name=src,
            replacement_name=repl,
            reason=reason,
            origin="flext_core",
        )
        for src, (repl, reason) in c.ENFORCEMENT_ACCESSOR_RENAMES.items()
    )

    def _collect_manual_warnings(
        self,
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
        *,
        resolver: FlextInfraAccessorOriginResolver,
    ) -> t.SequenceOf[m.Infra.AccessorMigrationChange]:
        """Report introducing methods through the canonical Core prefix predicate.

        Returns:
            The resulting ``t.SequenceOf[m.Infra.AccessorMigrationChange]``.

        Raises:
            ValueError: If the source/project differs from the original Rope snapshot.

        """
        if (
            resolver.rope_project is not rope_project
            or source != resolver.module(py_file).source_code
        ):
            msg = f"accessor discovery source differs from Rope snapshot: {py_file}"
            raise ValueError(msg)
        policy = m.MethodShapeParams.model_validate(
            c.ENFORCEMENT_PREDICATE_SPECS["no_accessor_methods"]["params"]
        )
        warnings: list[m.Infra.AccessorMigrationChange] = []
        for declaration in resolver.introduced_methods(py_file):
            name = declaration.name
            prefix = next(
                (
                    prefix
                    for prefix in policy.forbidden_prefixes
                    if name.startswith(prefix)
                ),
                None,
            )
            if prefix is None or name.startswith("_"):
                continue
            rule = next(
                (rule for rule in self._AUTOMATED_RULES if rule.source_name == name),
                None,
            )
            if rule is not None and resolver.within_origin(
                str(py_file), origin=rule.origin
            ):
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=declaration.line,
                    original_name=name,
                    replacement_name="",
                    automated=False,
                    reason=(
                        "Owned introducing method "
                        f"{declaration.module_name}.{declaration.scope_path} "
                        "violates no_accessor_methods; "
                        f"{policy.forbidden_prefixes[prefix]}; "
                        "an explicit domain rename decision is required."
                    ),
                ),
            )
        return tuple(warnings)


__all__: list[str] = ["FlextInfraAccessorMigrationWarningsMixin"]
