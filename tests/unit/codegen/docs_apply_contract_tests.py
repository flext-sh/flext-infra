"""Contract tests for documentation as a standard Make scope."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsDocsApplyContract:
    """Documentation is a WHAT scope of standard verbs, never its own verb."""

    def test_the_ssot_has_no_docs_verb(self) -> None:
        names = tuple(verb.name for verb in config.Infra.codegen.make.verbs)

        tm.that(names, lacks="docs")


__all__: tuple[str, ...] = ()
