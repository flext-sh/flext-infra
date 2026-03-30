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
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.github import cli as cli
    from flext_infra.github.cli import FlextInfraCliGithub as FlextInfraCliGithub

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliGithub": ["flext_infra.github.cli", "FlextInfraCliGithub"],
    "cli": ["flext_infra.github.cli", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliGithub",
    "cli",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
