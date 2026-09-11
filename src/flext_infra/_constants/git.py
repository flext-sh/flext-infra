"""Git constants for flext-infra project.

Centralizes git mode/stage/remote/sha constants consumed by the
``_utilities/_git/`` facet so the GitPython-backed operations never
hardcode magic numbers or strings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final


class FlextInfraConstantsGit:
    """Git-specific constants for the GitPython-backed facet."""

    @unique
    class GateAttestationSchema(StrEnum):
        """Supported signed gate-attestation schema identities."""

        V1 = "https://flext.sh/attestations/gates/v1"

    # --- Index entry modes (git mode field, not POSIX st_mode) ---

    GIT_MODE_FILE: Final[int] = 0o100644
    "Normal tracked file index mode."
    GIT_MODE_EXECUTABLE: Final[int] = 0o100755
    "Executable tracked file index mode."
    GIT_MODE_SYMLINK: Final[int] = 0o120000
    "Symbolic link index mode."
    GIT_MODE_GITLINK: Final[int] = 0o160000
    "Submodule gitlink index mode (used by BaseIndexEntry)."
    GIT_CACHEINFO_GITLINK: Final[str] = "160000"
    "Submodule gitlink mode string for ``git update-index --cacheinfo``."

    # --- Index stage values ---

    GIT_STAGE_NORMAL: Final[int] = 0
    "Normal (non-conflict) index stage."

    # --- SHA lengths ---

    GIT_OID_HEX_LENGTH_SHA1: Final[int] = 40
    "Hex length of a SHA-1 Git object id."
    GIT_OID_HEX_LENGTH_SHA256: Final[int] = 64
    "Hex length of a SHA-256 Git object id."

    # --- Remote defaults ---

    GIT_DEFAULT_REMOTE: Final[str] = "origin"
    "Canonical upstream remote name."
    GIT_REMOTE_SSH_SCHEMES: Final[frozenset[str]] = frozenset({"ssh", "git+ssh"})
    "Remote URL schemes treated as SSH-style remote identifiers."
    GIT_REMOTE_SENSITIVE_QUERY_KEYS: Final[frozenset[str]] = frozenset({
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "client_secret",
        "id_token",
        "jwt",
        "key",
        "oauth_token",
        "password",
        "passwd",
        "private_key",
        "private_token",
        "refresh_token",
        "secret",
        "token",
    })
    "Remote query keys whose values are redacted from identity output."

    # --- Ref prefixes ---

    GIT_REFS_HEADS: Final[str] = "refs/heads/"
    "Local branch ref prefix."


__all__: list[str] = ["FlextInfraConstantsGit"]
