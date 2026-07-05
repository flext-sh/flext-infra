"""Tests for the flext-infra pytest enforcement plugin.

The plugin is auto-registered via the ``flext_infra_enforcement`` pytest11
entry-point. These tests assert the entry-point exists and that loading the
module registers the expected detector contribution with the central
flext-tests dispatcher.
"""

from __future__ import annotations

from importlib.metadata import entry_points

import pytest
from flext_tests._fixtures._enforcement_parts.registry import (
    clear,
    get,
)

from flext_infra._fixtures import enforcement as flext_infra_enforcement_plugin


class TestsFlextInfraEnforcementPlugin:
    """Entry-point and registration contract for the flext-infra plugin."""

    @pytest.fixture
    def _clear_registry(self) -> None:
        """Keep the shared contribution registry isolated between cases."""
        clear()
        yield
        clear()

    def test_pytest11_entry_point_is_registered(self, _clear_registry: None) -> None:
        """The plugin is discoverable through the pytest11 entry-point group."""
        eps = entry_points(group="pytest11")
        names = {ep.name for ep in eps}

        assert "flext_infra_enforcement" in names

    def test_plugin_registers_infra_detector_contribution(
        self,
        _clear_registry: None,
    ) -> None:
        """Loading the module registers the flext-infra detector contribution."""
        flext_infra_enforcement_plugin._register()

        contribution = get("flext_infra_detector")
        assert contribution is not None
        assert contribution.source_kind == "flext_infra_detector"
        assert contribution.builder is not None
        assert contribution.warning_categories == ()
