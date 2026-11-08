"""Postconditions for semantic private-import rewrites.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import p
from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeModules


class FlextInfraUtilitiesPrivateImportValidation:
    """Reject old import residue or an incomplete public cutover."""

    @staticmethod
    def require_zero_private_import_residue(
        source: str,
        *,
        file_path: Path,
        plan: p.Infra.PrivateImportRewritePlan,
        removals: Mapping[str, set[str]],
    ) -> None:
        """Require old imports/bindings gone and public imports present.

        ``removals`` is every import binding that must disappear: the plan's
        private removals, its superseded public roots, and relocated exports.

        Raises:
            ValueError: If private binding residue; or if private import residue from;
                or if public facade import.

        """
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(None, source)
        layouts = module.get_source_binding_index().import_layouts()
        for module_name, symbols in removals.items():
            if any(
                layout.module_name == module_name
                and any(alias[0] in symbols for alias in layout.aliases)
                for layout in layouts
            ):
                msg = f"private import residue from {module_name} in {file_path}"
                raise ValueError(msg)
        for alias, package in plan.public_imports.items():
            present = any(
                layout.module_name == package
                and any(
                    imported[0] == alias and imported[1] is None
                    for imported in layout.aliases
                )
                for layout in layouts
            )
            if not present:
                msg = f"public facade import {package}.{alias} missing in {file_path}"
                raise ValueError(msg)
        residue = FlextInfraUtilitiesQualifiedNames.qualified_name_residue(
            source,
            plan.replacements,
        )
        if residue:
            msg = f"private binding residue {sorted(residue)} in {file_path}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesPrivateImportValidation"]
