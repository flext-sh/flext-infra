"""Extracted facade class for docs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsAudit,
    FlextInfraUtilitiesDocsBuild,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsFix,
    FlextInfraUtilitiesDocsGenerate,
    FlextInfraUtilitiesDocsGithubLinks,
    FlextInfraUtilitiesDocsRender,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsScopeBuild,
    FlextInfraUtilitiesDocsValidate,
)
from flext_infra._utilities._docs.base import FlextInfraUtilitiesDocsBase


class FlextInfraUtilitiesDocs(
    FlextInfraUtilitiesDocsBase,
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsAudit,
    FlextInfraUtilitiesDocsBuild,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsFix,
    FlextInfraUtilitiesDocsGenerate,
    FlextInfraUtilitiesDocsGithubLinks,
    FlextInfraUtilitiesDocsRender,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsScopeBuild,
    FlextInfraUtilitiesDocsValidate,
):
    """Facade for docs."""


__all__: list[str] = ["FlextInfraUtilitiesDocs"]
