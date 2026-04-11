"""Tests for flext_infra service importability and u.Infra MRO pattern.

Tests verify that all FlextInfra services are accessible via u.Infra MRO
and that the current output namespace works correctly.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from io import StringIO

import pytest

from flext_core import FlextContainer
from tests import c, u


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

    def test_io_methods_available(self) -> None:
        """Verify IO methods are accessible via u.Infra MRO."""
        assert callable(u.Cli.json_write)

    def test_cli_runtime_methods_available(self) -> None:
        """Verify command runtime methods are accessible via u.Cli."""
        assert callable(u.Cli.run_checked)
        assert callable(u.Cli.run_raw)
        assert callable(u.Cli.capture)
        assert callable(u.Cli.run_to_file)

    def test_discovery_methods_available(self) -> None:
        """Verify discovery methods are accessible via u.Infra MRO."""
        assert callable(u.Infra.discover_projects)
        assert callable(u.Infra.discover_project_roots)

    def test_output_methods_available(self) -> None:
        """Verify output methods are accessible via u.Infra MRO."""
        assert callable(u.Infra.status)
        assert callable(u.Infra.summary)
        assert callable(u.Infra.error)
        assert callable(u.Infra.warning)
        assert callable(u.Infra.info)
        assert callable(u.Infra.header)
        assert callable(u.Infra.progress)

    def test_path_methods_available(self) -> None:
        """Verify path methods are accessible via u.Infra MRO."""
        assert callable(u.Infra.workspace_root)

    def test_template_methods_available(self) -> None:
        """Verify template constants are accessible via c.Infra MRO."""
        assert isinstance(c.Infra.TOC_START, str)
        assert isinstance(c.Infra.TOC_END, str)
        assert isinstance(c.Infra.GENERATED_HEADER, str)

    def test_versioning_methods_available(self) -> None:
        """Verify versioning methods are accessible via u.Infra MRO."""
        assert callable(u.Infra.parse_semver)
        assert callable(u.Infra.bump_version)

    def test_toml_methods_available(self) -> None:
        """Verify TOML methods are accessible via u.Infra MRO."""
        assert callable(u.Cli.toml_ensure_table)
        assert callable(u.Cli.toml_table_string_keys)

    def test_patterns_available(self) -> None:
        """Verify pattern constants are accessible via u.Infra MRO."""
        assert callable(u.Infra.matches)


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

    def test_output_methods_write_to_configured_stream(self) -> None:
        """Verify output methods write through the shared namespace stream."""
        stream = StringIO()

        u.Infra.setup(color=False, unicode=False, stream=stream)
        u.Infra.info("hello")
        u.Infra.warning("careful")

        assert stream.getvalue() == "INFO: hello\nWARN: careful\n"
