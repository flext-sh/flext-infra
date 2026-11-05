"""Behaviour tests for the automated test-namespace import cutover.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraTestNamespaceImportCutover:
    """Rewrites every import-law violation through the public planner."""

    @staticmethod
    def test_direct_first_party_import_moves_to_tests_namespace(
        tmp_path: Path,
    ) -> None:
        """A direct package import becomes a canonical tests import."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("direct"),
        )

        tm.that(updated, has="from tests import FlextCore")
        tm.that(updated, lacks="from flext_core import")

    @staticmethod
    def test_deep_first_party_import_moves_to_tests_namespace(
        tmp_path: Path,
    ) -> None:
        """A deep module import becomes a canonical tests import."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("deep"),
        )

        tm.that(updated, has="from tests import install_lazy_exports")
        tm.that(updated, lacks="from flext_core.lazy import")

    @staticmethod
    def test_tests_submodule_import_moves_to_tests_root(tmp_path: Path) -> None:
        """A direct tests submodule import moves to the namespace root."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("tests_submodule"),
        )

        tm.that(updated, has="from tests import c")
        tm.that(updated, lacks="from tests.constants import")

    @staticmethod
    def test_relative_import_moves_to_tests_namespace(tmp_path: Path) -> None:
        """A relative import becomes an absolute tests import."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("relative"),
        )

        tm.that(updated, has="from tests import helper")
        tm.that(updated, lacks="from . import")

    @staticmethod
    def test_non_canonical_alias_is_stripped_and_references_renamed(
        tmp_path: Path,
    ) -> None:
        """A local alias becomes the canonical tests name everywhere."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("alias"),
        )

        tm.that(updated, has="from tests import c")
        tm.that(updated, has="value = c.Tests.VALUE")
        tm.that(updated, lacks="as tc")
        tm.that(updated, lacks="tc.Tests")

    @staticmethod
    def test_plain_import_moves_to_canonical_namespace_alias(
        tmp_path: Path,
    ) -> None:
        """A plain package import binds the canonical namespace alias."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("plain"),
        )

        tm.that(updated, has="from tests import core")
        tm.that(updated, has="value = core.VALUE")
        tm.that(updated, lacks="from flext_core import c,t,p,m,u,x,h,d")
        tm.that(updated, lacks="core_module")

    @staticmethod
    def test_imports_merge_into_one_canonical_statement(tmp_path: Path) -> None:
        """Every targeted import merges into one sorted tests import."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_import("merged"),
        )

        tm.that(updated, has="import pytest")
        tm.that(updated, has="from tests import FlextCore, c")
        tm.that(updated.count("from tests import"), eq=1)

    @staticmethod
    def test_meta_import_machinery_is_never_rewritten(tmp_path: Path) -> None:
        """The declared import-machinery area keeps its probes."""
        planned = u.Tests.semantic_cutover_plan(
            c.Infra.SemanticCutoverPhase.TEST_NAMESPACE_IMPORT,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_META_RELATIVE,
            u.Tests.semantic_cutover_import("meta"),
        )

        tm.that(planned.value, eq=())


__all__: list[str] = ["TestsFlextInfraTestNamespaceImportCutover"]
