# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""GitHub integration services.

Provides services for GitHub API interactions, workflow management, and
repository operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.github._constants import *
    from flext_infra.github._models import *
    from flext_infra.github.cli import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliGithub": "flext_infra.github.cli",
    "FlextInfraGithubConstants": "flext_infra.github._constants",
    "FlextInfraGithubModels": "flext_infra.github._models",
    "_constants": "flext_infra.github._constants",
    "_models": "flext_infra.github._models",
    "cli": "flext_infra.github.cli",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
