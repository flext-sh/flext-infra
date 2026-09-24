"""Enforce the runner's collection manifest through pytest's public hook API.

The runner resolves selected node IDs once and passes that ordered manifest as
pytest arguments. Testmon still records dependencies in every worker, but its
worker-local stable/unstable classification must not define xdist's index order.
Only ordering belongs here: missing, additional or duplicate tests fail loudly.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import ClassVar

import pytest


class FlextInfraPytestCollection:
    """Pytest entry-point plugin for the runner's explicit selection contract."""

    OPTION: ClassVar[str] = "--flext-selected-collection"

    @staticmethod
    def pytest_addoption(parser: pytest.Parser) -> None:
        """Require explicit activation by the canonical runner."""
        parser.addoption(
            FlextInfraPytestCollection.OPTION,
            action="store_true",
            help="Enforce the runner's ordered node-ID selection in every worker.",
        )

    @staticmethod
    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection_finish(session: pytest.Session) -> Generator[None]:
        """Validate before xdist publishes worker IDs, preserving raw failures."""
        if session.config.getoption(FlextInfraPytestCollection.OPTION):
            order = {
                node_id: index for index, node_id in enumerate(session.config.args)
            }
            collected = [item.nodeid for item in session.items]
            if len(order) != len(session.config.args) or len(set(collected)) != len(
                collected
            ):
                msg = "Runner collection manifest contains duplicate node IDs"
                raise ValueError(msg)
            if set(collected) != set(order):
                missing = sorted(set(order) - set(collected))
                unexpected = sorted(set(collected) - set(order))
                msg = f"Runner collection differs from selection: {missing=}, {unexpected=}"
                raise ValueError(msg)
            session.items.sort(key=lambda item: order[item.nodeid])
        yield


__all__: list[str] = ["FlextInfraPytestCollection"]
