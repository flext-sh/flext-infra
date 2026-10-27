"""Pytest entry-point plugin enforcing the runner's collection manifest.

The hook class only orchestrates: every hook delegates to the collection
utility of ``u.Infra``, which owns the manifest, Markdown and worker
accounting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import u

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from flext_infra import t


class FlextInfraPytestCollection:
    """Pytest entry-point plugin for the runner's explicit selection contract."""

    @staticmethod
    def pytest_collectstart(collector: t.Infra.Pytest.Collector) -> None:
        """Measure Markdown eligibility before the collector can omit an item."""
        u.Infra.markdown_collect_start(collector)

    @staticmethod
    def pytest_itemcollected(item: t.Infra.Pytest.Item) -> None:
        """Retain actual Markdown node identities before selector hooks run."""
        u.Infra.markdown_item_collected(item)

    @staticmethod
    def pytest_deselected(items: list[t.Infra.Pytest.Item]) -> None:
        """Account for selector effects through their public notification."""
        u.Infra.markdown_deselected(items)

    @staticmethod
    @u.Infra.Pytest.hookimpl(wrapper=True, specname="pytest_runtest_call")
    def pytest_markdown_module(item: t.Infra.Pytest.Item) -> Generator[None]:
        """Scope the Markdown SDK's execution module around one test call."""
        yield from u.Infra.markdown_module_scope(item)

    @staticmethod
    @u.Infra.Pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(item: t.Infra.Pytest.Item) -> Generator[None]:
        """Observe the real Markdown runner without replacing its execution."""
        yield from u.Infra.markdown_runtest_call(item)

    @staticmethod
    def pytest_addoption(parser: t.Infra.Pytest.Parser) -> None:
        """Require explicit activation by the canonical runner."""
        u.Infra.collection_add_options(parser)

    @staticmethod
    @u.Infra.Pytest.hookimpl(tryfirst=True)
    def pytest_configure(config: t.Infra.Pytest.Config) -> None:
        """Pin testmon outside the checkout and record warnings once."""
        u.Infra.collection_configure(config)

    @staticmethod
    @u.Infra.Pytest.hookimpl(optionalhook=True)
    def pytest_configure_node(node: t.Infra.Pytest.WorkerController) -> None:
        """Admit each actual native worker into this invocation's inventory."""
        u.Infra.collection_configure_node(node)

    @staticmethod
    @u.Infra.Pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(
        node: t.Infra.Pytest.WorkerController,
        ids: Sequence[str],
    ) -> None:
        """Retain the controller's native node order before test dispatch."""
        u.Infra.collection_node_finished(node, ids)

    @staticmethod
    @u.Infra.Pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(
        node: t.Infra.Pytest.WorkerController,
        error: object | None,
    ) -> None:
        """Publish one manifest after every admitted worker supplies its facts."""
        u.Infra.collection_node_down(node, error)

    @staticmethod
    @u.Infra.Pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection_finish(session: t.Infra.Pytest.Session) -> Generator[None]:
        """Validate the selection before xdist publishes worker IDs."""
        yield from u.Infra.collection_finish(session)


__all__: list[str] = ["FlextInfraPytestCollection"]
