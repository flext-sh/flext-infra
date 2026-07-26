"""Tests that the codegen engine carries no downstream-consumer knowledge.

``flext-infra`` is a generalized engine. Its configuration SSOT declares only
the provider and repositories it owns; every downstream consumer declares its
own topology in its own ``config/workspace.yaml``. Embedding a consumer's
repositories here couples the engine to projects it must not know about.

The owning identity is never hardcoded: it is derived from the engine's own
distribution name (``pyproject.toml`` metadata SSOT) resolved against the
repository catalog the engine publishes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config, u


@pytest.fixture(scope="module")
def owned_provider() -> str:
    """Resolve the engine's own provider from its own catalog entry."""
    engine_root = Path(__file__).resolve().parents[2]
    metadata = tm.ok(u.read_project_metadata(engine_root))
    distribution = metadata.project.name
    entry = next(
        (
            repository
            for repository in config.Infra.codegen.repositories
            if repository.distribution == distribution
        ),
        None,
    )
    if entry is None:
        msg = f"engine absent from its own catalog: {distribution}"
        raise AssertionError(msg)
    return entry.provider


class TestsFlextInfraEngineIsConsumerAgnostic:
    def test_repository_catalog_declares_only_owned_provider(
        self, owned_provider: str
    ) -> None:
        foreign = sorted({
            repository.provider
            for repository in config.Infra.codegen.repositories
            if repository.provider != owned_provider
        })

        tm.that(foreign, eq=[])

    def test_provider_catalog_declares_only_owned_provider(
        self, owned_provider: str
    ) -> None:
        foreign = sorted(
            provider.name
            for provider in config.Infra.codegen.providers
            if provider.name != owned_provider
        )

        tm.that(foreign, eq=[])

    def test_workspace_catalog_declares_only_owned_workspaces(
        self, owned_provider: str
    ) -> None:
        owned = {
            repository.name
            for repository in config.Infra.codegen.repositories
            if repository.provider == owned_provider
        }
        foreign = sorted(
            workspace.name
            for workspace in config.Infra.codegen.workspaces
            if workspace.repository not in owned
        )

        tm.that(foreign, eq=[])

    def test_engine_declares_no_directory_name_of_a_foreign_workspace(self) -> None:
        """Sibling discovery is declarative, never a directory name in the engine.

        A neighbour joins discovery by declaring ``[tool.flext.workspace]
        attached = true`` in its own pyproject. The engine therefore ships no
        directory-name list, glob, or pattern for a workspace it does not own.
        """
        engine_root = Path(__file__).resolve().parents[2]
        discovery_source = (
            engine_root
            / "src"
            / "flext_infra"
            / "_utilities"
            / "_project_discovery_candidates.py"
        ).read_text(encoding="utf-8")

        tm.that(discovery_source, has="attached")
        tm.that(discovery_source, lacks=".glob(pattern)")
