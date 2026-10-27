"""Captured-source inventory feeding base resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping

from flext_infra import m, t
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope.source_bases_inventory_collector import (
    FlextInfraUtilitiesRopeSourceBindingCollector,
)


class FlextInfraUtilitiesRopeSourceBasesInventory:
    """Captured-source inventory part of the source-bases composite."""

    @classmethod
    def inventory(
        cls,
        request: m.Infra.SourceBindingInventoryRequest,
        definitions: MutableMapping[str, m.Infra.SourceClassDefinition],
        *,
        provider: t.Infra.RopePyModule | None = None,
    ) -> t.MappingKV[str, m.Infra.SourceClassReference | None]:
        """Index lexical bindings without installing a cross-module Rope overlay.

        A provider class is indexed at its native declaration line. Unreferenced
        module-level provider classes remain qualified declarations, not fabricated
        lineages. A captured class owns its nested declaration identities.

        Returns:
            The module's explicit lexical bindings, including value shadowing.

        Raises:
            TypeError: If the elected provider is not a native source module or
                does not return a module AST.

        """
        provider = cls.source_provider(request, provider=provider)
        if not FlextInfraUtilitiesRopeRuntime.source_module(provider):
            message = f"Captured file has no native source module: {request.path}"
            raise TypeError(message)
        parsed = provider.get_ast()
        if not isinstance(parsed, ast.Module):
            message = f"Rope returned a non-module AST for {request.path}"
            raise TypeError(message)
        package = (
            request.module
            if request.path.name == "__init__.py"
            else request.module.rpartition(".")[0]
        )
        globals_: MutableMapping[str, m.Infra.SourceClassReference | None] = {}
        spec = m.Infra.SourceBindingCollectorSpec(
            module=request.module,
            provider=provider,
            package=package,
            required_line=request.required_line,
            allow_conditional=request.allow_conditional,
            definitions=definitions,
            lexical=globals_,
        )
        FlextInfraUtilitiesRopeSourceBindingCollector.collect(
            spec,
            parsed.body,
            globals_,
            "",
        )
        globals_.update(
            FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
                request.module,
                request.path,
                request.source,
                project=request.project,
                pymodule=provider,
            )
        )
        return globals_

    @staticmethod
    def source_provider(
        request: m.Infra.SourceBindingInventoryRequest,
        *,
        provider: t.Infra.RopePyModule | None = None,
    ) -> t.Infra.RopePyModule:
        """Elect one native provider for the exact captured source.

        An explicitly supplied mismatched provider raises ValueError with its
        captured-origin evidence.

        Returns:
            The matching cached module or a module built from the captured bytes.

        Raises:
            TypeError: If a captured resource has no native source module.

        """
        if provider is not None:
            resource = provider.get_resource()
            if (
                resource is None
                or resource.real_path != str(request.path)
                or provider.source_code != request.source
            ):
                message = f"Provider does not match captured source: {request.path}"
                failure = ValueError(message)
                failure.add_note(
                    f"provider_resource={resource.real_path if resource else None!r}; "
                    f"resource_matches={
                        resource is not None and resource.real_path == str(request.path)
                    }; "
                    f"provider_length={len(provider.source_code)}; "
                    f"captured_length={len(request.source)}; "
                    f"newline_normalization_matches={
                        provider.source_code
                        == request.source.replace(chr(13) + chr(10), chr(10)).replace(
                            chr(13), chr(10)
                        )
                    }"
                )
                raise failure
            return provider
        resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
            request.project,
            request.path,
        )
        if resource is not None and resource.read() == request.source:
            native = request.project.get_pymodule(resource, force_errors=True)
            if not FlextInfraUtilitiesRopeRuntime.source_module(native):
                message = f"Captured file has no native source module: {request.path}"
                raise TypeError(message)
            if native.source_code == request.source:
                return native
        return FlextInfraUtilitiesRopeRuntime.build_string_module(
            request.project,
            request.source,
            resource=resource,
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesInventory"]
