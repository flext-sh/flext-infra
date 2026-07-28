"""Contract test for the generated `test` verb argument surface.

`base.mk` advertises `PYTEST_ARGS="-k expr"` as a public knob, and the canonical
law is that validation runs through `make`, never through a loose `pytest`
invocation. Those two only hold together if the generated recipe actually
forwards the variable.

When it does not, `make test PYTEST_ARGS=...` silently runs the entire suite.
The selector appears to work, so the operator is pushed into calling pytest
directly to get a focused run -- which bypasses the guards, locks and evidence
that the Make surface exists to enforce.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import config


def _makefile_template() -> Path:
    """Locate the generated-Makefile template for the checkout in use."""
    marker = Path("src/flext_infra/templates/project/base/Makefile.j2")
    for candidate in Path(__file__).resolve().parents:
        if (candidate / marker).is_file():
            return candidate / marker
    msg = f"no ancestor of {Path(__file__).resolve()} provides {marker}"
    raise FileNotFoundError(msg)


class TestsMakeTestSelector:
    """The generated `test` recipe honours the documented argument knob."""

    def test_test_verb_is_canonical(self) -> None:
        """`test` is part of the canonical verb surface every project exposes."""
        tm.that(
            any(verb.name == "test" for verb in config.Infra.codegen.make.verbs),
            eq=True,
        )

    def test_generated_test_recipe_forwards_pytest_args(self) -> None:
        """The shared reporter recipe must forward every test selector.

        Without this, a targeted run is impossible through `make`, and the only
        way to filter is to call pytest directly -- exactly the loose command the
        canonical-command law forbids.
        """
        template_path = _makefile_template()
        template = template_path.read_text(encoding="utf-8")
        reporter = (template_path.parent / "base_test_report_recipe.j2").read_text(
            encoding="utf-8"
        )

        tm.that(template, has="test_report_recipe(")
        tm.that(reporter, has='_all_pytest_args="$(PYTEST_ARGS)"')
        tm.that(reporter, has='if [ -n "$(MATCH)" ]')
        tm.that(reporter, has='if [ -n "$(FILE)" ]')
        tm.that(reporter, has='if [ "$(FAIL_FAST)" = "1" ]')
