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
        assert any(verb.name == "test" for verb in config.Infra.codegen.make.verbs)

    def test_generated_test_recipe_forwards_pytest_args(self) -> None:
        """The recipe must forward the knob `base.mk` documents.

        Without this, a targeted run is impossible through `make`, and the only
        way to filter is to call pytest directly -- exactly the loose command the
        canonical-command law forbids.
        """
        template = _makefile_template().read_text(encoding="utf-8")
        recipes = [
            block.split("\n\n", 1)[0]
            for block in template.split("_builtin_test_all:")[1:]
        ]
        assert recipes, "template declares no _builtin_test_all recipe"
        direct = [r for r in recipes if "pytest" in r]
        assert direct, "no _builtin_test_all recipe invokes pytest directly"
        assert all("PYTEST_ARGS" in recipe for recipe in direct)
