# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Container package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.container import test_infra_container
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions,
        TestInfraMroPattern,
        TestInfraServiceRetrieval,
    )

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "TestInfraContainerFunctions": "tests.unit.container.test_infra_container",
    "TestInfraMroPattern": "tests.unit.container.test_infra_container",
    "TestInfraServiceRetrieval": "tests.unit.container.test_infra_container",
    "test_infra_container": "tests.unit.container.test_infra_container",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
