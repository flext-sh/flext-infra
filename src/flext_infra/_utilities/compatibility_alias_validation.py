"""Strict validation for semantic compatibility-alias cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import c
from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeModules


class FlextInfraUtilitiesCompatibilityAliasValidation:
    """Reject ambiguous bindings, exports, and post-cutover residue."""

    @staticmethod
    def require_static_compatibility_alias_exports(
        source: str,
        file_path: Path,
        aliases: frozenset[str],
    ) -> None:
        """Reject dynamic export ownership before changing an alias owner.

        Raises:
            ValueError: If dynamic __all__ blocks alias cutover in.

        """
        if not aliases:
            return
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            None, source
        )
        sequence = module.get_source_binding_index().assignment_string_sequence(
            "__all__"
        )
        if sequence is None:
            return
        if sequence == () and "__all__" in source:
            msg = f"dynamic __all__ blocks alias cutover in {file_path}"
            raise ValueError(msg)

    @staticmethod
    def require_zero_compatibility_alias_residue(
        source: str,
        file_path: Path,
        *,
        qualified_aliases: Mapping[str, str],
        exported_aliases: frozenset[str],
    ) -> None:
        """Require removed identities and their literal exports to disappear.

        Raises:
            ValueError: If qualified alias residue; or if alias export residue in.

        """
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            None, source
        )
        sequence = module.get_source_binding_index().assignment_string_sequence(
            "__all__"
        )
        if sequence is not None and any(
            alias in sequence for alias in exported_aliases
        ):
            msg = f"alias export residue in {file_path}"
            raise ValueError(msg)
        residue = sorted(
            FlextInfraUtilitiesQualifiedNames.qualified_name_residue(
                source,
                qualified_aliases,
            ),
        )
        if residue:
            msg = f"qualified alias residue {residue[0]} in {file_path}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesCompatibilityAliasValidation"]