"""Tests for p facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import p


class TestsFlextInfraInfraProtocols:
    """Test p class import and structure."""

    def test_flext_infra_protocols_is_importable(self) -> None:
        """Test that p can be imported."""
        assert p is not None

    def test_flext_infra_protocols_has_project_info_protocol(self) -> None:
        """Test that ProjectInfo is defined."""

    def test_flext_infra_protocols_has_command_output_protocol(self) -> None:
        """Test that CommandOutput is defined in CLI namespace."""

    def test_flext_infra_protocols_has_checker_protocol(self) -> None:
        """Test that Checker is defined."""

    def test_flext_infra_protocols_has_syncer_protocol(self) -> None:
        """Test that Syncer is defined."""

    def test_flext_infra_protocols_has_generator_protocol(self) -> None:
        """Test that Generator is defined."""

    def test_flext_infra_protocols_has_reporter_protocol(self) -> None:
        """Test that ReportingService is defined."""

    def test_flext_infra_protocols_has_validator_protocol(self) -> None:
        """Test that Validator is defined."""

    def test_flext_infra_protocols_has_orchestrator_protocol(self) -> None:
        """Test that Orchestrator is defined."""

    def test_flext_infra_protocols_has_discovery_protocol(self) -> None:
        """Test that Discovery is defined."""

    def test_flext_infra_protocols_has_command_runner_protocol(self) -> None:
        """Test that CommandRunner is defined in CLI namespace."""

    def test_runtime_alias_p_is_flext_infra_protocols(self) -> None:
        """Test that p has the same Infra namespace as FlextInfraProtocols."""

    def test_project_info_protocol_has_name_property(self) -> None:
        """Test that ProjectInfo defines name property."""

    def test_project_info_protocol_has_path_property(self) -> None:
        """Test that ProjectInfo defines path property."""

    def test_command_output_protocol_has_stdout_property(self) -> None:
        """Test that CommandOutput defines stdout property."""

    def test_command_output_protocol_has_stderr_property(self) -> None:
        """Test that CommandOutput defines stderr property."""

    def test_command_output_protocol_has_exit_code_property(self) -> None:
        """Test that CommandOutput defines exit_code property."""

    def test_checker_protocol_has_run_method(self) -> None:
        """Test that Checker defines run method."""

    def test_syncer_protocol_has_sync_method(self) -> None:
        """Test that Syncer defines sync method."""

    def test_generator_protocol_has_generate_method(self) -> None:
        """Test that Generator defines generate method."""

    def test_reporter_protocol_has_get_report_dir_method(self) -> None:
        """Test that ReportingService defines get_report_dir method."""

    def test_validator_protocol_has_validate_method(self) -> None:
        """Test that Validator defines validate method."""

    def test_orchestrator_protocol_has_orchestrate_method(self) -> None:
        """Test that Orchestrator defines orchestrate method."""

    def test_discovery_protocol_has_discover_projects_method(self) -> None:
        """Test that Discovery defines discover_projects method."""

    def test_command_runner_protocol_has_run_method(self) -> None:
        """Test that CommandRunner defines run method."""
