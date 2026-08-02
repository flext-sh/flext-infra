"""Contract tests for the canonical Make grammar and worktree selector."""

from __future__ import annotations

from flext_infra import config, m
from flext_tests import tm


class TestsCodegenMakeGrammar:
    """The generated Make grammar is a faithful typed-SSOT projection."""

    def test_public_grammar_round_trips_through_the_typed_ssot(self) -> None:
        """Every configured verb remains unique and lossless after validation."""
        verbs = config.Infra.codegen.make.verbs
        names = tuple(verb.name for verb in verbs)
        round_tripped = tuple(
            m.Infra.MakeVerbSpec.model_validate(verb.model_dump()) for verb in verbs
        )

        tm.that(verbs, where=bool)
        tm.that(names, len=len(set(names)))
        tm.that(round_tripped, eq=verbs)

    def test_public_grammar_defaults_are_typed_nonempty_selectors(self) -> None:
        """Defaults come from config and remain valid selector values."""
        for verb in config.Infra.codegen.make.verbs:
            tm.that(verb.default_what, where=bool)
