"""Domain test constants mixin for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final

from flext_infra import c


class TestsFlextInfraConstantsDomain:
    """Domain constants mixin for infra tests."""

    ALL_PHASES: tuple[str, ...] = (
        c.Infra.VERB_VALIDATE,
        c.Infra.VERSION,
        c.Infra.DIR_BUILD,
        c.Infra.VERB_PUBLISH,
    )

    class NamespaceSource:
        """Namespace-source detector constants for infra tests."""

        FAMILY_FILE_MAP: Final[dict[str, str]] = {
            "c": "constants.py",
            "t": "typings.py",
            "p": "protocols.py",
            "m": "models.py",
            "u": "utilities.py",
        }
        FAMILY_SUFFIX_MAP: Final[dict[str, str]] = {
            "c": "Constants",
            "t": "Types",
            "p": "Protocols",
            "m": "Models",
            "u": "Utilities",
        }

    class SsotEnforcement:
        """SSOT enforcement constants for infra tests."""

        WORKSPACE_ROOT_PARENT_DEPTH: Final[int] = 3
        SSOT_METHODS: Final[tuple[tuple[str, str], ...]] = (
            ("sha256_content", "flext_cli"),
            ("sha256_file", "flext_cli"),
            ("json_read", "flext_cli"),
            ("json_write", "flext_cli"),
            ("json_parse", "flext_cli"),
        )
        MRO_CHAIN: Final[tuple[tuple[str, str], ...]] = (
            ("flext_cli", "flext_core"),
            ("flext_infra", "flext_core"),
            ("flext_infra", "flext_cli"),
        )
        ALLOWED_OVERLAPS: Final[dict[tuple[str, str], frozenset[str]]] = {
            ("flext_cli", "flext_core"): frozenset({"run", "to_str"}),
        }

    class Projects:
        """Project names and identifiers for infra testing."""

        FLEXT_CORE: Final[str] = "flext-core"
        FLEXT_API: Final[str] = "flext-api"
        FLEXT_CLI: Final[str] = "flext-cli"
        FLEXT_MELTANO: Final[str] = "flext-meltano"
        FLEXT_LDAP: Final[str] = "flext-ldap"
        FLEXT_LDIF: Final[str] = "flext-ldif"
        FLEXT_OBSERVABILITY: Final[str] = "flext-observability"
        FLEXT_QUALITY: Final[str] = "flext-quality"

        ALL_PROJECTS: Final[tuple[str, ...]] = (
            FLEXT_CORE,
            FLEXT_API,
            FLEXT_CLI,
            FLEXT_MELTANO,
            FLEXT_LDAP,
            FLEXT_LDIF,
            FLEXT_OBSERVABILITY,
            FLEXT_QUALITY,
        )

    class Markers:
        """Test markers for infra test categorization."""

        INFRA: Final[str] = "infra"
        INTEGRATION: Final[str] = "integration"
        DOCKER: Final[str] = "docker"
        SLOW: Final[str] = "slow"
        REQUIRES_NETWORK: Final[str] = "requires_network"
        REQUIRES_DOCKER: Final[str] = "requires_docker"

    class Versions:
        """Version strings for infra components."""

        PYTHON_MIN: Final[str] = "3.13"
        PYTHON_RECOMMENDED: Final[str] = "3.13"
        POETRY_MIN: Final[str] = "1.8"
        RUFF_MIN: Final[str] = "0.1"
        MYPY_MIN: Final[str] = "1.0"

    class Paths:
        """Path constants for infra testing."""

        DOCKER_COMPOSE_DIR: Final[str] = "docker"
        TESTS_DIR: Final[str] = "tests"
        INFRA_TESTS_DIR: Final[str] = "tests/infra"
        FIXTURES_DIR: Final[str] = "tests/fixtures"
        INTEGRATION_DIR: Final[str] = "tests/integration"
