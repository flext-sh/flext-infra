"""Declared project queries and immutable dependency payload boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack, nullcontext
from pathlib import Path
from re import escape

import pytest

from tests import c, tm, u


class TestsFlextInfraSourceOwnership:
    """Exercise the native source reader through its public planning facade."""

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    def test_dependency_membership_is_not_project_ownership(
        tmp_path: Path, *, nested: bool
    ) -> None:
        """The elected runtime has the same query boundary inside or outside root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        runtime = (root if nested else tmp_path) / "dependency_runtime"
        runtime.mkdir()
        source = runtime / "provider.py"
        source.write_text("class Provider:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        candidate = runtime / "new_package" / "__init__.py"
        with (
            tm.scope(python_paths=(str(runtime),)),
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            with project.source_consumption() as scope:
                tm.fail(project.source_query(candidate, "isfile"))
                tm.that(project.source_children(runtime), has=source)
                tm.fail(project.source_query(candidate, "isfile"))
            tm.that(scope.receipt().source_query_topology, eq=())
            tm.that(scope.receipt().source_directories, eq=())
            candidate.parent.mkdir()
            candidate.write_text("", encoding=c.DEFAULT_ENCODING)
            tm.that(project.source_text(source), eq="class Provider:\n    pass\n")
            tm.that(
                {state.path for state in project.consumed_source_states()}, has=source
            )
            tm.that(project.source_query(package / "absent.py", "isfile"), eq=False)

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("payload", ["provider.py", "provider.dist-info/METADATA"])
    def test_dependency_payload_attestation_remains_immutable(
        tmp_path: Path, payload: str, *, nested: bool
    ) -> None:
        """Dependency source and metadata reads reject byte changes in either layout."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        runtime = (root if nested else tmp_path) / "dependency_runtime"
        source = runtime / payload
        source.parent.mkdir(parents=True)
        source.write_text("original\n", encoding=c.DEFAULT_ENCODING)
        with tm.scope(python_paths=(str(runtime),)), ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            tm.that(project.source_text(source), eq="original\n")
            source.write_text("changed\n", encoding=c.DEFAULT_ENCODING)
            with pytest.raises(RuntimeError, match=escape(str(source))):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize("replace", [False, True])
    def test_declared_source_ancestry_remains_authenticated(
        tmp_path: Path, *, replace: bool
    ) -> None:
        """A runtime import root cannot demote a more specific declared source root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        candidate = package / "absent" / "provider.py"
        expectation = (
            pytest.raises(ValueError, match="source directory ancestry changed")
            if replace
            else nullcontext()
        )
        with (
            tm.scope(python_paths=(str(root),)),
            expectation,
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            with project.source_consumption() as scope:
                tm.fail(project.source_query(candidate, "isfile"))
            tm.that(
                any(
                    item.target == candidate.parent
                    for item in scope.receipt().source_query_topology
                ),
                eq=True,
            )
            if replace:
                candidate.parent.mkdir()
