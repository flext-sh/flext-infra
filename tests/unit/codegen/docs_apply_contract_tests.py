"""Contract tests for the APPLY selector of the docs verb."""

from __future__ import annotations

import pathlib
import re

from flext_infra import config, m
from flext_tests import tm

_MAKEFILE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/flext_infra/templates/project/base/Makefile.j2"
)
_DOCS_WORKFLOW = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
)


def _docs_verb() -> m.Infra.MakeVerbSpec:
    """Return the declared docs verb from the SSOT."""
    for verb in config.Infra.codegen.make.verbs:
        if verb.name == "docs":
            return verb
    msg = "docs verb is not declared"
    raise AssertionError(msg)


class TestsDocsApplyContract:
    """`docs` mutates under APPLY, so the SSOT must declare it apply-guarded.

    The generated handler already branches on APPLY (``--apply`` vs
    ``--check``) and the generated workflow calls ``make docs WHAT=generate
    APPLY=Y``. With ``apply_guarded: false`` the dispatcher emits no
    ``_APPLY_WHAT_docs`` and rejects the call with "verb docs is read-only
    and does not accept APPLY", so the docs job can never materialize.
    """

    def test_the_generated_handler_consumes_apply(self) -> None:
        """The docs handler selects --apply or --check from APPLY."""
        makefile = _MAKEFILE.read_text(encoding="utf-8")

        tm.that("--apply,--check" in makefile.replace(" ", ""), eq=True)

    def test_the_generated_workflow_invokes_docs_with_apply(self) -> None:
        """The docs workflow materializes artifacts with APPLY=Y."""
        workflow = _DOCS_WORKFLOW.read_text(encoding="utf-8")

        tm.that("make docs WHAT=generate APPLY=Y" in workflow, eq=True)

    def test_the_ssot_declares_docs_apply_guarded(self) -> None:
        """A verb whose handler consumes APPLY is declared apply-guarded."""
        tm.that(_docs_verb().apply_guarded, eq=True)


_ = re

__all__: tuple[str, ...] = ()
