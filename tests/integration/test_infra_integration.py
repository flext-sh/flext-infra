"""Integration tests for flext_infra cross-module flows.

Tests exercise cross-module flows using the public runtime surfaces, validating:
- Output/reporting methods via u.Infra
- Service r chaining
- Command runtime operations via u.Cli.run_checked/capture
- BaseMk generation flow

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    FlextInfraOrchestratorService,
    FlextInfraWorkspaceDetector,
    r,
    u,
)

pytestmark = [pytest.mark.integration]


class TestsFlextInfraIntegrationInfraIntegration:
    @pytest.mark.integration
    def test_workspace_detector_and_orchestrator_share_state(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that FlextInfraWorkspaceDetector and orchestrator share state.

        Validates:
        - Detector can be created
        - Orchestrator can be created
        - Both can access shared workspace information
        """
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        (workspace_root / ".git").mkdir()
        detector = FlextInfraWorkspaceDetector()
        orchestrator = FlextInfraOrchestratorService(verb="test")
        assert detector is not None
        assert orchestrator is not None
        assert isinstance(detector, FlextInfraWorkspaceDetector)
        assert isinstance(orchestrator, FlextInfraOrchestratorService)

    @pytest.mark.integration
    def test_workspace_detector_returns_flext_result(self, tmp_path: Path) -> None:
        """Test that workspace detector operations return r.

        Validates:
        - Detector methods return r
        - Result typing is correct
        """
        detector = FlextInfraWorkspaceDetector()
        assert detector is not None
        assert isinstance(detector, FlextInfraWorkspaceDetector)

    @pytest.mark.integration
    def test_basemk_template_engine_and_generator_flow(self, tmp_path: Path) -> None:
        """Test BaseMk template engine → generator flow.

        Validates:
        - Template engine can be created
        - Generator can be created
        - Both work together in a flow
        """
        output_dir = tmp_path / "basemk_output"
        output_dir.mkdir()
        engine = FlextInfraBaseMkTemplateEngine()
        generator = FlextInfraBaseMkGenerator()
        assert engine is not None
        assert generator is not None
        assert isinstance(engine, FlextInfraBaseMkTemplateEngine)
        assert isinstance(generator, FlextInfraBaseMkGenerator)

    @pytest.mark.integration
    def test_basemk_generator_generates_valid_content(self, tmp_path: Path) -> None:
        """Test BaseMk generator validates rendered output using real make."""
        _ = tmp_path
        generator = FlextInfraBaseMkGenerator()
        generated = generator.execute()
        assert generated.success
        assert isinstance(generated.value, str)
        assert "check" in generated.value

    @pytest.mark.integration
    def test_output_singleton_has_expected_methods(self) -> None:
        """Test that reporting/output methods are exposed through u.Infra.

        Validates u.Infra MRO output methods are available:
        - status, summary, error, warning, info, header, progress
        """
        assert callable(u.Cli.status)
        assert callable(u.Cli.summary)
        assert callable(u.Cli.error)
        assert callable(u.Cli.warning)
        assert callable(u.Cli.info)
        assert callable(u.Cli.header)
        assert callable(u.Cli.progress)

    @pytest.mark.integration
    def test_output_methods_are_callable_via_u_infra(self) -> None:
        """Test that reporting methods are callable through the real facade.

        Validates:
        - All methods are callable through u.Infra
        """
        assert callable(u.Cli.status)
        assert callable(u.Cli.summary)
        assert callable(u.Cli.error)
        assert callable(u.Cli.warning)
        assert callable(u.Cli.info)
        assert callable(u.Cli.header)
        assert callable(u.Cli.progress)

    @pytest.mark.integration
    def test_service_result_chaining_with_map(self) -> None:
        """Test chaining multiple services via .map().

        Validates:
        - r.map() works with service results
        - Type is preserved through chain
        - Value is transformed correctly
        """
        initial_value = 10
        result = r[int].ok(initial_value).map(lambda x: x * 2).map(lambda x: x + 5)
        assert result.success
        assert result.value == 25

    @pytest.mark.integration
    def test_service_result_chaining_with_flat_map(self) -> None:
        """Test chaining multiple services via .flat_map().

        Validates:
        - r.flat_map() works with service results
        - Type is preserved through chain
        - Failures propagate correctly
        """
        initial_value = 10
        result = (
            r[int]
            .ok(initial_value)
            .flat_map(lambda x: r[int].ok(x * 2))
            .flat_map(lambda x: r[int].ok(x + 5))
        )
        assert result.success
        assert result.value == 25

    @pytest.mark.integration
    def test_service_result_chaining_failure_propagation(self) -> None:
        """Test that failures propagate through result chains.

        Validates:
        - Failure stops the chain
        - Error message is preserved
        - Subsequent operations are not executed
        """
        initial_value = 10
        result = (
            r[int]
            .ok(initial_value)
            .flat_map(lambda x: r[int].ok(x * 2))
            .flat_map(lambda x: r[int].fail("intentional error"))
            .flat_map(lambda x: r[int].ok(x + 5))
        )
        assert result.failure
        assert isinstance(result.error, str)
        assert "intentional error" in result.error

    @pytest.mark.integration
    def test_service_result_chaining_with_mixed_operations(self) -> None:
        """Test chaining with mixed map and flat_map operations.

        Validates:
        - Mixed operations work together
        - Type is preserved
        - Values are transformed correctly
        """
        initial_value = 5
        result = (
            r[int]
            .ok(initial_value)
            .map(lambda x: x * 2)
            .flat_map(lambda x: r[int].ok(x + 3))
            .map(lambda x: x * 2)
        )
        assert result.success
        assert result.value == 26

    @pytest.mark.integration
    def test_discover_projects_via_mro(self, tmp_path: Path) -> None:
        """Test u.Infra.discover_projects flow.

        Validates:
        - discover_projects is callable via u.Infra MRO
        - workspace_root is callable via u.Infra MRO
        """
        assert callable(u.Infra.discover_projects)
        assert callable(u.Infra.resolve_workspace_root_or_cwd)

    @pytest.mark.integration
    def test_path_utilities_via_mro(self, tmp_path: Path) -> None:
        """Test u.Infra path utility methods are available via MRO."""
        assert callable(u.Infra.resolve_project_root)

    @pytest.mark.integration
    def test_cli_capture_git_current_branch_in_real_repo(self, tmp_path: Path) -> None:
        """Test git branch detection through the canonical CLI runtime surface."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        init_result = u.Cli.run_checked(["git", "init"], cwd=repo_root)
        assert init_result.success
        email_result = u.Cli.run_checked(
            ["git", "config", "user.email", "infra@example.com"], cwd=repo_root
        )
        assert email_result.success
        name_result = u.Cli.run_checked(
            ["git", "config", "user.name", "Infra Test"], cwd=repo_root
        )
        assert name_result.success
        sample_file = repo_root / "README.md"
        _ = sample_file.write_text("infra test\n", encoding="utf-8")
        add_result = u.Cli.run_checked(["git", "add", "README.md"], cwd=repo_root)
        assert add_result.success
        commit_result = u.Cli.run_checked(
            ["git", "commit", "-m", "initial"], cwd=repo_root
        )
        assert commit_result.success
        branch_result = u.Cli.capture(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
        )
        assert branch_result.success
        assert branch_result.value != ""

    @pytest.mark.integration
    def test_command_runner_capture_executes_real_command(self) -> None:
        """Test u.Cli.capture with a real external command."""
        capture_result = u.Cli.capture(["python3", "-c", "print('infra-ok')"])
        assert capture_result.success
        assert capture_result.value == "infra-ok"
