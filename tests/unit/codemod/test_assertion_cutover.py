"""Behaviour tests for the automated bare-assert matcher cutover.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraTestAssertionCutover:
    """Rewrite every bare assert through the public semantic planner."""

    @staticmethod
    def test_bare_truth_uses_truth_matcher_and_adds_tm_import(
        tmp_path: Path,
    ) -> None:
        """A bare predicate becomes ``tm.that(..., truth=True)``."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("truth"),
        )

        tm.that(updated, has="from tests import tm")
        tm.that(updated, has="tm.that(value, truth=True)")
        tm.that(updated, lacks="assert value")

    @staticmethod
    def test_equality_merges_into_existing_tests_import(tmp_path: Path) -> None:
        """Equality becomes ``eq`` and ``tm`` joins the canonical import."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("equality"),
        )

        tm.that(updated, has="from tests import c, tm")
        tm.that(updated, has="tm.that(value, eq=expected)")
        tm.that(updated, lacks="assert value")

    @staticmethod
    def test_inequality_uses_ne(tmp_path: Path) -> None:
        """Inequality becomes ``ne``."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("inequality"),
        )

        tm.that(updated, has="tm.that(value, ne=expected)")

    @staticmethod
    def test_none_identity_uses_none_matcher(tmp_path: Path) -> None:
        """``is None`` and ``is not None`` become the ``none`` matcher."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("none"),
        )

        tm.that(updated, has="tm.that(value, none=True)")
        tm.that(updated, has="tm.that(other, none=False)")

    @staticmethod
    def test_membership_uses_has_and_lacks(tmp_path: Path) -> None:
        """Membership becomes ``has`` and ``lacks`` on the container."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("membership"),
        )

        tm.that(updated, has="tm.that(items, has=item)")
        tm.that(updated, has="tm.that(items, lacks=other)")

    @staticmethod
    def test_isinstance_uses_type_matcher(tmp_path: Path) -> None:
        """Type checks become the ``is_``/``not_`` matcher, not narrowing."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("isinstance"),
        )

        tm.that(updated, has="tm.that(value, is_=str)")
        tm.that(updated, has="tm.that(other, not_=int)")
        tm.that(updated, lacks="isinstance(")

    @staticmethod
    def test_negation_uses_false_truth(tmp_path: Path) -> None:
        """A negated predicate becomes ``truth=False``."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("negation"),
        )

        tm.that(updated, has="tm.that(value, truth=False)")

    @staticmethod
    def test_assert_message_is_preserved(tmp_path: Path) -> None:
        """The assert message becomes the matcher's ``msg``."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("message"),
        )

        tm.that(updated, has='tm.that(value, truth=True, msg="message")')

    @staticmethod
    def test_module_without_assert_is_untouched(tmp_path: Path) -> None:
        """A module without asserts keeps its canonical imports."""
        planned = u.Tests.semantic_cutover_plan(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("untouched"),
        )

        tm.that(planned.value, eq=())


__all__: list[str] = ["TestsFlextInfraTestAssertionCutover"]
