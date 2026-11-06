"""Service base for flext-infra tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsServiceBase

from flext_infra import FlextInfraServiceBase
from tests import p


class TestsFlextInfraServiceBase[TDomainResult: p.Base = p.Base](
    FlextTestsServiceBase[TDomainResult],
    FlextInfraServiceBase[TDomainResult],
):
    """Infra test service base: flext-tests runtime over the infra service contract."""

    # NOTE (multi-agent, flext-wkii.17.14): flext-tests is the sole owner of
    # settings bootstrap behavior; this project adds no forwarding override.


s = TestsFlextInfraServiceBase

__all__: list[str] = ["TestsFlextInfraServiceBase", "s"]
