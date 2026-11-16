"""Alias and lazy-module resolution over the captured source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import p
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeModules


class FlextInfraUtilitiesRopeSourceBasesAliases:
    """Alias and lazy-module resolution part of the source-bases composite."""

    @classmethod
    def lazy_module_aliases(
        cls,
        module: str,
        path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> dict[str, str]:
        """Project the provider module of every declared lazy export binding.

        Returns:
            Alias name to absolute provider module path.

        """
        return {
            name: binding.target
            for name, binding in cls.lazy_export_bindings(
                module,
                path,
                source,
                project=project,
                pymodule=pymodule,
            ).items()
        }

    @classmethod
    def lazy_export_bindings(
        cls,
        module: str,
        path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> Mapping[str, p.Infra.SourceClassReference]:
        """Delegate lazy export bindings to the owner that parses them.

        Returns:
            The absolute provider and exact attribute of every declared export.

        """
        return FlextInfraUtilitiesRopeRuntimeModules.resolve_lazy_export_bindings(
            module,
            path,
            source,
            project=project,
            pymodule=pymodule,
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesAliases"]
