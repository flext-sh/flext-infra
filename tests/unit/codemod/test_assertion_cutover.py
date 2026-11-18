"""Behaviour tests for the automated bare-assert matcher cutover.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraCli, transformers
from tests import c, m, tm, u


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

    @staticmethod
    def test_comprehension_membership_is_not_top_level(tmp_path: Path) -> None:
        """An ``in`` inside a comprehension is not the assert's operator."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("comprehension"),
        )

        tm.that(
            updated,
            has=(
                'tm.that([d for d in docs if d.get("kind") == "ServiceAccount"],'
                " truth=False)"
            ),
        )
        tm.that(updated, has='tm.that([d for d in docs if d], has="x")')
        tm.that(updated, lacks="has=not [d for d")

    @staticmethod
    def test_hash_inside_string_is_not_a_comment(tmp_path: Path) -> None:
        """A ``#`` inside a string literal stays part of the operand."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("hash_in_string"),
        )

        tm.that(updated, has='tm.that(value, eq="a#b")')

    @staticmethod
    def test_compound_expressions_keep_their_meaning(tmp_path: Path) -> None:
        """Boolean, negated and chained comparisons stay whole predicates."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("compound"),
        )

        tm.that(updated, has="tm.that(value == 1 and other == 2, truth=True)")
        tm.that(updated, has="tm.that(value == expected, truth=False)")
        tm.that(updated, has="tm.that(low < value < high, truth=True)")

    @staticmethod
    def test_multiline_assert_is_rewritten(tmp_path: Path) -> None:
        """A multi-line assert becomes one matcher over its whole statement."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("multiline"),
        )

        tm.that(updated, has="tm.that(value, eq=(")
        tm.that(updated, has='tm.that(items, has=item, msg="message")')
        tm.that(updated, lacks="assert ")

    @staticmethod
    def test_tm_import_follows_a_parenthesized_import(tmp_path: Path) -> None:
        """The ``tm`` import lands after a multi-line import, never inside it."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("parenthesized_import"),
        )

        tm.that(updated, has="    Sequence,\n)\nfrom tests import tm\n")
        tm.that(updated, lacks="(\nfrom tests import tm")

    @staticmethod
    def test_unformattable_literal_is_split_to_fit(tmp_path: Path) -> None:
        """The public publisher splits a newly long literal before consumption."""
        source = u.Tests.semantic_cutover_assertion("unformattable")
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            source,
        )
        path = tmp_path / c.Tests.SEMANTIC_CUTOVER_RELATIVE
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        original = tmp_path / "original_case.py"
        original.write_text(source, encoding=c.DEFAULT_ENCODING)
        u.Tests.initialize_git_repo(tmp_path)
        u.Tests.provision_checkout(tmp_path)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
        tm.ok(
            transformers.FlextInfraTransformersSemantic.publish_semantic_artifact_plans(
                (
                    m.Infra.CodegenFilePlan(
                        project=tmp_path,
                        path=path,
                        before=before,
                        desired_content=updated.encode(c.DEFAULT_ENCODING),
                        desired_mode=before.mode,
                    ),
                ),
                repository_root=tmp_path,
            )
        )
        updated = path.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(updated, has="tm.that(value, eq=expected)")
        tm.that(updated, lacks="assert ")
        tm.that(
            FlextInfraCli.infra_main([
                "check",
                "run",
                "--repository-root",
                str(tmp_path),
                "--file",
                c.Tests.SEMANTIC_CUTOVER_RELATIVE,
                "--gates",
                c.Infra.LINT,
            ]),
            eq=0,
        )
        u.Tests.run_lazy_init_probe(
            "import runpy\n"
            f"for path in ({str(original)!r}, {str(path)!r}):\n"
            "    values = {'value': 1, 'expected': 1, 'text': 'word ' * 100}\n"
            "    module = runpy.run_path(path, init_globals=values)\n"
            "    module['test_probe']()\n"
            "    module['test_probe'].__globals__['text'] = ''\n"
            "    try:\n        module['test_probe']()\n"
            "    except AssertionError:\n        pass\n"
            "    else:\n        raise RuntimeError('missing text was accepted')\n",
            python_paths=(),
        )

    @staticmethod
    def test_local_names_keep_their_type_through_typed_helpers(
        tmp_path: Path,
    ) -> None:
        """A local name is rebound through ``tm.instance``/``tm.not_none``.

        The helpers return the checked value typed, so later uses keep ``T``
        without a narrowing guard; a name the function does not bind stays a
        matcher, since rebinding it would make it local.
        """
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("typed_locals"),
        )

        tm.that(updated, has="    rendered = tm.instance(rendered, dict)\n")
        tm.that(updated, has='    payload = tm.not_none(payload, msg="payload")\n')
        tm.that(updated, has="    tm.that(shared, is_=str)\n")
        tm.that(updated, has="        tm.that(rendered, is_=dict)\n")

    @staticmethod
    def test_non_string_message_stays_lazy_through_reject(tmp_path: Path) -> None:
        """A non-string assert message is raised lazily, never coerced."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("object_message"),
        )

        tm.that(
            updated, has="    if not (len(hosts) == 1):\n        tm.reject(route)\n"
        )
        tm.that(updated, has='    tm.that(value, eq=expected, msg=f"{value}")\n')

    @staticmethod
    def test_comments_are_never_lost(tmp_path: Path) -> None:
        """A trailing comment stays; an assert with an inner comment is kept."""
        updated = u.Tests.semantic_cutover_source(
            c.Infra.SemanticCutoverPhase.TEST_ASSERT_TO_MATCHER,
            tmp_path,
            c.Tests.SEMANTIC_CUTOVER_RELATIVE,
            u.Tests.semantic_cutover_assertion("comments"),
        )

        tm.that(updated, has="tm.that(value, eq=expected)  # why")
        tm.that(updated, has="assert other == (")
        tm.that(updated, has="# inner")


__all__: list[str] = ["TestsFlextInfraTestAssertionCutover"]
