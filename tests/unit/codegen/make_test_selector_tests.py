"""Behavior contract for focused pytest selection through generated Make."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, u
from flext_tests import tm
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
        """Expose test through the canonical verb surface."""
        tm.that(
            any(verb.name == "test" for verb in config.Infra.codegen.make.verbs),
            eq=True,
        )

    def test_generated_test_recipe_forwards_pytest_args(self) -> None:
        """Forward explicit pytest selectors without forcing the full suite."""
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
        direct = [recipe for recipe in recipes if "pytest" in recipe]
        tm.that(direct, len=1, msg="_builtin_test_all must invoke pytest directly")
        tm.that(all("PYTEST_ARGS" in recipe for recipe in direct), eq=True)
        tm.that(template, has="PYTEST_TARGETS ?=\n")
        tm.that(direct[0], has="$(if $(strip $(PYTEST_TARGETS))")

    def test_explicit_target_replaces_the_default_suite(self, tmp_path: Path) -> None:
        """Use an explicit target instead of appending it to the default suite."""
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
