# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Import Law. Policy package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._import_law._policy.namespace import (
        FlextInfraUtilitiesImportLawPolicyNamespace,
    )
    from flext_infra._utilities._import_law._policy.publication import (
        FlextInfraUtilitiesImportLawPolicyPublication,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawPolicyNamespace",
    "FlextInfraUtilitiesImportLawPolicyPublication",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesImportLawPolicyNamespace": ".namespace",
        "FlextInfraUtilitiesImportLawPolicyPublication": ".publication",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesImportLawPolicyNamespace": (
            "_module_bindings",
            "_declared_binding",
            "snapshot_import_namespace",
            "import_namespace",
            "_layer_alias_modules",
            "module_import_layer",
            "pytest_plugin_modules",
            "import_module_role",
            "import_source_role",
            "import_direct_module",
            "import_lazy_exports",
            "import_package_dir",
            "import_bootstrap_dependency",
            "import_facade_dependencies",
            "_declared_binding_source",
            "resolve_declared_binding",
        ),
        "FlextInfraUtilitiesImportLawPolicyPublication": (
            "_scan_due",
            "_scan_consumers",
            "_scan_lookups",
            "_scan_files",
            "_scan_providers",
            "codemod_progress",
            "_publication_scan_summary",
            "family_letter",
            "lazy_source",
            "_declared_subpackage_source",
            "_declared_ancestors",
            "_declaration_identity",
            "model_utility_target",
            "import_contract_routes",
            "_import_contract_rule",
            "_family_contract_rule",
            "_family_binding_route",
            "_family_provider_admitted",
            "_family_owner_spelling",
            "import_contract_bindings",
            "_module_bindings",
            "_declared_binding",
            "snapshot_import_namespace",
            "import_namespace",
            "_layer_alias_modules",
            "module_import_layer",
            "pytest_plugin_modules",
            "import_module_role",
            "import_source_role",
            "import_direct_module",
            "import_lazy_exports",
            "import_package_dir",
            "import_bootstrap_dependency",
            "import_facade_dependencies",
            "_declared_binding_source",
            "resolve_declared_binding",
        ),
    },
)
