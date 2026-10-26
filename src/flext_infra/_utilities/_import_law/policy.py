"""Import policy facade over publication and namespace facts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._import_law._policy.namespace import (
    FlextInfraUtilitiesImportLawPolicyNamespace,
)
from flext_infra._utilities._import_law._policy.publication import (
    FlextInfraUtilitiesImportLawPolicyPublication,
)


class FlextInfraUtilitiesImportLawPolicy(
    FlextInfraUtilitiesImportLawPolicyPublication,
    FlextInfraUtilitiesImportLawPolicyNamespace,
):
    """Compose source publication and namespace policy through MRO."""


__all__: list[str] = ["FlextInfraUtilitiesImportLawPolicy"]
