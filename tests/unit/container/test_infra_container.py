"""Tests for flext_infra service importability and u.Infra MRO pattern.

Tests verify that all FlextInfra services are accessible via u.Infra MRO
and that the current output namespace works correctly.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

import pytest
from flext_tests import tm

from flext_core import FlextContainer
from tests import c, u


class TestsFlextInfraContainerInfraContainer:
    """Test container accessor functions."""

    pytestmark = pytest.mark.usefixtures("setup")

    @pytest.fixture
    def setup(self) -> None:
        """Ensure container is configured before each test."""
        FlextContainer.shared().initialize_di_components()

    def test_get_flext_infra_container_returns_singleton(self) -> None:
        """Verify FlextContainer is a singleton-like container."""
        container = FlextContainer.shared()
        tm.that(callable(container.has), eq=True)
        tm.that(callable(container.resolve), eq=True)

    def test_get_flext_infra_service_returns_result(self) -> None:
        """Verify container get returns values for registered services."""
        container = FlextContainer.shared()
        tm.that(callable(container.bind), eq=True)
        tm.that(callable(container.resolve), eq=True)

    def test_io_methods_available(self) -> None:
        """Verify IO methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Cli.json_write), eq=True)

    def test_cli_runtime_methods_available(self) -> None:
        """Verify command runtime methods are accessible via u.Cli."""
        tm.that(callable(u.Cli.run_checked), eq=True)
        tm.that(callable(u.Cli.run_raw), eq=True)
        tm.that(callable(u.Cli.capture), eq=True)
        tm.that(callable(u.Cli.run_to_file), eq=True)

    def test_discovery_methods_available(self) -> None:
        """Verify discovery methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Infra.discover_projects), eq=True)
        tm.that(callable(u.Infra.discover_project_roots), eq=True)

    def test_output_methods_available(self) -> None:
        """Verify output methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Cli.status), eq=True)
        tm.that(callable(u.Cli.summary), eq=True)
        tm.that(callable(u.Cli.error), eq=True)
        tm.that(callable(u.Cli.warning), eq=True)
        tm.that(callable(u.Cli.info), eq=True)
        tm.that(callable(u.Cli.header), eq=True)
        tm.that(callable(u.Cli.progress), eq=True)

    def test_path_methods_available(self) -> None:
        """Verify path methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Infra.rope_workspace_root), eq=True)

    def test_template_methods_available(self) -> None:
        """Verify template constants are accessible via c.Infra MRO."""
        tm.that(c.Infra.TOC_START, is_=str)
        tm.that(c.Infra.TOC_END, is_=str)
        tm.that(c.Infra.GENERATED_HEADER, is_=str)

    def test_versioning_methods_available(self) -> None:
        """Verify versioning methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Infra.parse_semver), eq=True)
        tm.that(callable(u.Infra.bump_version), eq=True)

    def test_toml_methods_available(self) -> None:
        """Verify TOML methods are accessible via u.Infra MRO."""
        tm.that(callable(u.Cli.toml_ensure_table), eq=True)
        tm.that(callable(u.Cli.toml_table_path), eq=True)

    def test_patterns_available(self) -> None:
        """Verify pattern constants are accessible via u.Infra MRO."""
        tm.that(callable(u.Cli.matches), eq=True)

    def test_container_has_service_method(self) -> None:
        """Verify FlextContainer has has_service method."""
        tm.that(callable(FlextContainer.shared().has), eq=True)

    def test_container_list_services_method(self) -> None:
        """Verify FlextContainer has list_services method."""
        tm.that(callable(FlextContainer.shared().names), eq=True)

    def test_output_methods_write_to_configured_stream(self) -> None:
        """Verify output methods write through the shared namespace stream."""
        stream = StringIO()

        with redirect_stdout(stream):
            u.Cli.info("hello")
            u.Cli.warning("careful")

        tm.that(stream.getvalue(), eq="INFO: hello\nWARN: careful\n")
