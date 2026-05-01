"""Tests for flext_infra.workspace module initialization.

Tests lazy loading and __getattr__ fallthrough behavior.
"""

from __future__ import annotations

import pytest

from flext_infra import workspace as workspace_module
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.sync import FlextInfraSyncService


class TestsFlextInfraInfraWorkspaceInit:
    """Tests for flext_infra.workspace module."""

    def test_getattr_raises_attribute_error_for_unknown_symbol(self) -> None:
        """Test __getattr__ raises AttributeError for unknown attributes."""
        with pytest.raises(AttributeError):
            _ = getattr(workspace_module, "nonexistent_symbol_xyz")

    def test_lazy_import_orchestrator_service(self) -> None:
        """Test lazy import of FlextInfraOrchestratorService."""
        assert (
            workspace_module.FlextInfraOrchestratorService
            is FlextInfraOrchestratorService
        )

    def test_lazy_import_sync_service(self) -> None:
        """Test lazy import of FlextInfraSyncService."""
        assert workspace_module.FlextInfraSyncService is FlextInfraSyncService

    def test_lazy_import_migrator(self) -> None:
        """Test lazy import of FlextInfraProjectMigrator."""
        assert workspace_module.FlextInfraProjectMigrator is FlextInfraProjectMigrator

    def test_dir_returns_all_exports(self) -> None:
        """Test dir() returns all exported symbols."""
        exports = dir(workspace_module)
        assert "FlextInfraOrchestratorService" in exports
        assert "FlextInfraSyncService" in exports
        assert "FlextInfraProjectMigrator" in exports
