"""Tests for the flext-infra pytest enforcement plugin.

The plugin is auto-registered via the ``flext_infra_enforcement`` pytest11
entry-point. These tests assert the entry-point exists and that loading the
module registers the expected detector contribution with the central
flext-tests dispatcher.
"""

from __future__ import annotations

from collections.abc import Iterator
from importlib.metadata import entry_points

import pytest
from flext_tests.enforcement import clear, get

from flext_infra._fixtures import enforcement as flext_infra_enforcement_plugin
from flext_tests import tm


class TestsFlextInfraEnforcementPlugin:
    """Entry-point and registration contract for the flext-infra plugin."""

    @pytest.fixture
    def _clear_registry(self) -> Iterator[None]:
        """Keep the shared contribution registry isolated between cases."""
        clear()
        yield
        clear()

    def test_pytest11_entry_point_is_registered(self, _clear_registry: None) -> None:
        """The plugin is discoverable through the pytest11 entry-point group."""
        eps = entry_points(group="pytest11")
        names = {ep.name for ep in eps}

        tm.that(names, has="flext_infra_enforcement")

    def test_plugin_registers_infra_detector_contribution(
        self, _clear_registry: None
    ) -> None:
        """Loading the module registers the flext-infra detector contribution."""
        flext_infra_enforcement_plugin.FlextInfraEnforcementPytestPlugin.register()

        contribution = get("flext_infra_detector")
        tm.that(contribution, none=False)
        tm.that(contribution.source_kind, eq="flext_infra_detector")
        tm.that(contribution.builder, none=False)
        tm.that(contribution.warning_categories, eq=())
