"""Detect missing or duplicate runtime alias assignments via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, u

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraRuntimeAliasDetector:
    """Detect missing/duplicate runtime aliases (e.g. m = FlextFooModels) via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
        *,
        policy: m.Infra.NamespaceModulePolicy,
    ) -> t.SequenceOf[m.Infra.RuntimeAliasViolation]:
        """Detect missing/duplicate runtime alias assignments in a facade file."""
        file_path = ctx.file_path
        family = policy.expected_alias
        if family is None:
            return []
        resource = u.Infra.fetch_python_resource(
            ctx.rope_project, file_path
        )
        if resource is None:
            message = f"facade source is unavailable to Rope: {file_path}"
            raise ValueError(message)
        source = resource.read()
        matches = u.Infra.runtime_alias_bindings(source, alias=family)
        if not matches or family not in u.Infra.public_export_names_source(source):
            return [
                m.Infra.RuntimeAliasViolation(
                    file=str(file_path),
                    kind="missing",
                    alias=family,
                    detail=f"Facade {family!r} must be bound and published in __all__",
                )
            ]
        if len(matches) > 1:
            return [
                m.Infra.RuntimeAliasViolation(
                    file=str(file_path),
                    kind="duplicate",
                    alias=family,
                    detail=f"Found {len(matches)} '{family} = ...' assignments",
                )
            ]
        module = u.Infra.get_pymodule(ctx.rope_project, resource)
        attributes = module.get_attributes()
        target = attributes.get(policy.expected_family or "")
        binding = attributes.get(family)
        if target is None or binding is None or binding.get_object() is not target.get_object():
            return [
                m.Infra.RuntimeAliasViolation(
                    file=str(file_path),
                    kind="missing",
                    alias=family,
                    detail=f"Facade {family!r} must reference {policy.expected_family!r}",
                )
            ]
        return []


__all__: list[str] = ["FlextInfraRuntimeAliasDetector"]
