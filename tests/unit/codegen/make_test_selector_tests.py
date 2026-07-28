"""Behavior contract for focused pytest selection through generated Make."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import config, u
from tests import u as test_u


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
        matches = tuple(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == "test"
        )
        tm.that(matches, len=1)

    def test_explicit_target_replaces_the_default_suite(self, tmp_path: Path) -> None:
        """A focused target is the pytest target, not an appendix to tests/."""
        makefile = tm.ok(u.Cli.files_read_text(Path("Makefile")))
        (tmp_path / "Makefile").write_text(makefile, encoding="utf-8")
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python", "#!/bin/sh\nexit 0\n"
        )
        invocation_log = tmp_path / "uv-args.log"
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            uv, f'#!/bin/sh\nprintf "%s\\n" "$@" > "{invocation_log}"\n'
        )
        selected = "tests/unit/selected_test.py"

        executed = tm.ok(
            u.Cli.run_raw(
                [
                    "make",
                    "--no-print-directory",
                    "test",
                    f"PYTEST_ARGS={selected}",
                    f"UV={uv}",
                ],
                cwd=tmp_path,
            )
        )

        tm.that(executed.exit_code, eq=0)
        arguments = invocation_log.read_text(encoding="utf-8")
        tm.that(arguments, has=selected)
        tm.that(str(tmp_path / "tests") in arguments, eq=False)

    def test_generated_test_recipe_forwards_pytest_args(self) -> None:
        """Forward both supported pytest selectors through the local recipe.

        Without this, a targeted run is impossible through `make`, and the only
        way to filter is to call pytest directly -- exactly the loose command the
        canonical-command law forbids.
        """
        template = _makefile_template().read_text(encoding="utf-8")
        recipes = [
            block.split("\n\n", 1)[0]
            for block in template.split("_builtin_test_all:")[1:]
        ]
        tm.that(
            recipes,
            len=2,
            msg="template must define workspace-root and local test handlers",
        )
        direct = [r for r in recipes if "pytest" in r]
        tm.that(direct, len=1, msg="_builtin_test_all must invoke pytest directly")
        tm.that(all("PYTEST_ARGS" in recipe for recipe in direct), eq=True)
        tm.that(template, has="PYTEST_TARGETS ?=\n")
        tm.that(direct[0], has="$(if $(strip $(PYTEST_TARGETS))")
