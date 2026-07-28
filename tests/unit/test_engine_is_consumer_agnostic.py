"""Tests that the codegen engine keeps catalog topology declarative.

``flext-infra`` is a generalized engine. Its configuration SSOT may catalog
multiple providers and workspaces, but the implementation must not hardcode
consumer directory names or leave catalog references dangling.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, t, u
from flext_tests import tm


@pytest.fixture(scope="module")
def engine_provider() -> str:
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
    provider: str = t.Infra.STR_ADAPTER.validate_python(entry.provider)
    return provider


class TestsFlextInfraEngineIsConsumerAgnostic:
    def test_repository_catalog_uses_declared_providers(self) -> None:
        declared = {provider.name for provider in config.Infra.codegen.providers}
        referenced = {
            repository.provider for repository in config.Infra.codegen.repositories
        }

        tm.that(referenced - declared, eq=set())

    def test_workspace_catalog_declares_only_owned_workspaces(
        self, owned_provider: str
    ) -> None:
        owned = {
            repository.name
            for repository in config.Infra.codegen.repositories
            if repository.provider == owned_provider
        }
        tm.that(sorted(referenced - declared), eq=[])

    def test_every_workspace_repository_is_declared(self) -> None:
        declared = {repository.name for repository in config.Infra.codegen.repositories}
        referenced = {
            workspace.repository for workspace in config.Infra.codegen.workspaces
        }
        tm.that(sorted(referenced - declared), eq=[])

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
