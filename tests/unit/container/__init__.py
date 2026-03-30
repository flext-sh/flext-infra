# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Container package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.container import test_infra_container as test_infra_container
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions as TestInfraContainerFunctions,
        TestInfraMroPattern as TestInfraMroPattern,
        TestInfraServiceRetrieval as TestInfraServiceRetrieval,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestInfraContainerFunctions": [
        "tests.unit.container.test_infra_container",
        "TestInfraContainerFunctions",
    ],
    "TestInfraMroPattern": [
        "tests.unit.container.test_infra_container",
        "TestInfraMroPattern",
    ],
    "TestInfraServiceRetrieval": [
        "tests.unit.container.test_infra_container",
        "TestInfraServiceRetrieval",
    ],
    "test_infra_container": ["tests.unit.container.test_infra_container", ""],
}

_EXPORTS: Sequence[str] = [
    "TestInfraContainerFunctions",
    "TestInfraMroPattern",
    "TestInfraServiceRetrieval",
    "test_infra_container",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
