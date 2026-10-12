"""Layer-zero vocabulary shared by workspace declarations and constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from typing import ClassVar

from flext_cli import t


class FlextInfraConfigVocabulary:
    """Canonical closed contracts required before project facades initialize."""

    DEPENDENCY_GROUPS: ClassVar[str] = "dependency-groups"
    """PEP 735 dependency-groups table key."""

    WORKSPACE_MANIFEST_VERSION: ClassVar[int] = 3

    CODEGEN_CONFIG_DIR: ClassVar[str] = "config"
    """Directory name for flext-infra config files relative to the package root."""

    CODEGEN_LOCAL_OVERRIDES_FILENAME: ClassVar[str] = "codegen-overrides.local.yaml"
    """Local operator override file name, excluded from the tracked baseline."""

    CODEGEN_ORG_OVERRIDES_FILENAME: ClassVar[str] = "codegen-org.yaml"
    """Governed repository org overrides file name."""

    GIT_COMMIT_OID_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
    )

    @unique
    class CodegenConformSurface(StrEnum):
        """Managed file selection accepted by canonical conform declarations."""

        ALL = "all"
        DEPENDENCIES = "dependencies"
        DOCS_CONFIG = "docs-config"
        ENVRC = "envrc"
        FACADES = "facades"
        LAZY_INIT = "lazy-init"
        MAKEFILE = "makefile"
        MISE_CONFIG = "mise-config"
        PYPROJECT = "pyproject"
