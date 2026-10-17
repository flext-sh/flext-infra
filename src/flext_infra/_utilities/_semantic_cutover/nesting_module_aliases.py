"""Module-alias consumers of modules whose members move under one owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import libcst as cst

from flext_infra import c, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesSemanticCutoverNestingModuleAliases:
    """Normalize import syntax while native Rope owns module binding identity.

    Module aliases remain module aliases: a proven moved member is emitted as
    ``alias.Owner.member`` without introducing a competing owner binding.
    """

    @staticmethod
    def _nesting_import_route(
        project: p.Infra.RopeProject,
        provider: p.Infra.RopePyModule,
        owner: str,
        origin: p.Infra.RopePyModule,
        sources: t.MappingKV[Path, str],
        *,
        consumer: str,
    ) -> t.Pair[str, str]:
        """Elect an existing public exposure, with native owner/MRO proof."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = provider.get_name()
        private = FlextInfraUtilitiesPrivateImportFacades.private_owner(module)
        cross_private = private is not None and consumer.partition(".")[0] != private
        if provider is origin and not cross_private:
            return module, owner
        original_owner = origin.get_attributes().get(owner)
        exposed = provider.get_attributes().get(owner)
        if (
            not cross_private
            and original_owner is not None
            and runtime.same_name(original_owner, exposed)
        ):
            return module, owner
        facades = FlextInfraUtilitiesPrivateImportFacades
        package = origin.get_name().partition(".")[0]
        native_package = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
            project.get_module(package),
        )
        resource = native_package.get_resource()
        if resource is None:
            msg = f"native public owner package has no source: {package}"
            raise ValueError(msg)
        package_root = Path(
            resource.real_path if resource.is_folder() else resource.parent.real_path,
        )
        inventory: t.MutableMappingKV[str, t.Pair[str, bool]] = {}
        for path, source in sources.items():
            if not path.is_relative_to(package_root):
                continue
            module_resource = project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            )
            parsed = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project, module_resource
            )
            name = parsed.get_name()
            if name in inventory:
                msg = f"ambiguous native public owner module: {name}"
                raise ValueError(msg)
            inventory[name] = source, module_resource.name == c.Infra.INIT_PY
        bindings, exports = facades.declared_exports(inventory)
        qualified = f"{origin.get_name()}.{owner}"
        declared = facades.declared_public_reference(qualified, bindings, exports)
        if declared is not None:
            public_module, public_name = declared
            native = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module(public_module),
            )
            if original_owner is not None and runtime.same_name(
                original_owner,
                native.get_attribute(public_name),
            ):
                return public_module, public_name
        reference = facades.public_reference(
            owners=facades.discover(inventory).get(package, ()),
            package=package,
            qualified=qualified,
            bindings=bindings,
            class_bases=FlextInfraUtilitiesPrivateImportAncestry.class_bases(inventory),
        )
        if reference is not None and original_owner is not None:
            public = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
                project.get_module(package),
            )
            exposed_owner = runtime.expression_name(public.get_scope(), reference)
            if exposed_owner is not None and original_owner.get_object() in (
                FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                    exposed_owner.get_object(),
                )
            ):
                return package, reference
        msg = f"no native public owner exposure for {module}: {qualified}"
        raise ValueError(msg)

    @staticmethod
    def _resolved_relative(
        level: int,
        suffix: str,
        *,
        module_name: str,
        is_package_init: bool,
    ) -> str:
        """Resolve one relative module reference against the importing module.

        Returns:
            The absolute dotted module name, or an empty string past the root.

        """
        package_parts = module_name.split(".")
        if not is_package_init:
            package_parts = package_parts[:-1]
        ascend = level - 1
        if ascend > len(package_parts):
            return ""
        prefix = package_parts[: len(package_parts) - ascend]
        return ".".join((*prefix, suffix) if suffix else prefix)

    @classmethod
    def _imported_module(
        cls,
        node: cst.ImportFrom,
        *,
        module_name: str,
        is_package_init: bool,
    ) -> str:
        """Return the absolute module one ``from`` import reads.

        Returns:
            The absolute dotted module name.

        """
        suffix = FlextInfraUtilitiesQualifiedNames.dotted_name(node.module) or ""
        if not node.relative:
            return suffix
        return cls._resolved_relative(
            len(node.relative),
            suffix,
            module_name=module_name,
            is_package_init=is_package_init,
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingModuleAliases"]
