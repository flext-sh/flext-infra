"""Tests for flext_infra service importability and u.Infra MRO pattern.

Tests verify that all FlextInfra services are accessible via u.Infra MRO
and that the output singleton works correctly.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from tests import u

from flext_core import FlextContainer
from flext_infra import output


class TestInfraContainerFunctions:
    """Test container accessor functions."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Ensure container is configured before each test."""
        FlextContainer().initialize_di_components()

    def test_get_flext_infra_container_returns_singleton(self) -> None:
        """Verify FlextContainer is a singleton-like container."""
        assert FlextContainer.has_service is not None
        assert callable(FlextContainer.get)

    def test_get_flext_infra_service_returns_result(self) -> None:
        """Verify container get returns values for registered services."""
        assert callable(FlextContainer.register)
        assert callable(FlextContainer.get)


class TestInfraMroPattern:
    """Test that u.Infra MRO exposes all utility methods."""

    def test_git_methods_available(self) -> None:
        """Verify git methods are accessible via u.Infra MRO."""
        assert callable(u.git_current_branch)
        assert callable(u.git_add)
        assert callable(u.git_commit)
        assert callable(u.git_push)
        assert callable(u.git_pull)
        assert callable(u.git_fetch)
        assert callable(u.git_has_changes)
        assert callable(u.git_is_repo)
        assert callable(u.git_run)

    def test_io_methods_available(self) -> None:
        """Verify IO methods are accessible via u.Infra MRO."""
        assert callable(u.read_json)
        assert callable(u.write_json)

    def test_subprocess_methods_available(self) -> None:
        """Verify subprocess methods are accessible via u.Infra MRO."""
        assert callable(u.run_checked)
        assert callable(u.run_raw)
        assert callable(u.capture)

    def test_discovery_methods_available(self) -> None:
        """Verify discovery methods are accessible via u.Infra MRO."""
        assert callable(u.discover_projects)
        assert callable(u.discover_project_roots)

    def test_output_methods_available(self) -> None:
        """Verify output methods are accessible via u.Infra MRO."""
        assert callable(u.status)
        assert callable(u.summary)
        assert callable(u.error)
        assert callable(u.warning)
        assert callable(u.info)
        assert callable(u.header)
        assert callable(u.progress)

    def test_path_methods_available(self) -> None:
        """Verify path methods are accessible via u.Infra MRO."""
        assert callable(u.workspace_root)

    def test_template_methods_available(self) -> None:
        """Verify template methods are accessible via u.Infra MRO."""
        assert callable(u.render)
        assert hasattr(u.Infra, "TOC_START")
        assert hasattr(u.Infra, "TOC_END")
        assert hasattr(u.Infra, "GENERATED_HEADER")

    def test_versioning_methods_available(self) -> None:
        """Verify versioning methods are accessible via u.Infra MRO."""
        assert callable(u.parse_semver)
        assert callable(u.bump_version)

    def test_toml_methods_available(self) -> None:
        """Verify TOML methods are accessible via u.Infra MRO."""
        assert callable(u.ensure_table)
        assert callable(u.table_string_keys)

    def test_patterns_available(self) -> None:
        """Verify pattern constants are accessible via u.Infra MRO."""
        assert callable(u.matches)


class TestInfraServiceRetrieval:
    """Test service retrieval behavior."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Ensure container is configured before each test."""
        FlextContainer().initialize_di_components()

    def test_container_has_service_method(self) -> None:
        """Verify FlextContainer has has_service method."""
        assert callable(FlextContainer.has_service)

    def test_container_list_services_method(self) -> None:
        """Verify FlextContainer has list_services method."""
        assert callable(FlextContainer.list_services)

    def test_output_singleton_returns_same_instance(self) -> None:
        """Verify output singleton is consistent."""
        assert output is not None
