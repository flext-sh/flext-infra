"""Behavior contract for focused pytest selection through generated Make."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, p, u
from flext_tests import tm
from tests import u as test_u


class TestsMakeTestSelector:
    """The generated `test` recipe honours the documented argument knob."""

    @staticmethod
    def _write_generated_make(root: Path) -> Path:
        """Copy the config-owned wrapper and engine into an isolated checkout."""
        checkout_root = Path(__file__).resolve().parents[3]
        surfaces = config.Infra.codegen.surfaces
        wrapper_source = checkout_root / surfaces.make_wrapper_path
        engine_source = checkout_root / surfaces.make_engine_path
        wrapper = root / surfaces.make_wrapper_path
        engine = root / surfaces.make_engine_path
        engine.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(wrapper_source.read_text(encoding="utf-8"), encoding="utf-8")
        engine.write_text(engine_source.read_text(encoding="utf-8"), encoding="utf-8")
        return wrapper

    def test_test_verb_is_canonical(self) -> None:
        """`test` is part of the canonical verb surface every project exposes."""
        matches = tuple(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == "test"
        )
        tm.that(matches, len=1)

    def test_fmt_is_the_only_public_formatting_verb(self, tmp_path: Path) -> None:
        """The generated Makefile runs canonical fmt and rejects its retired name."""
        public_verbs = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that("fmt" in public_verbs, where=bool)
        tm.that("format" not in public_verbs, where=bool)

        self._write_generated_make(tmp_path)
        invocation_log = tmp_path / "python-args.log"
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python",
            f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{invocation_log}"\n',
        )

        canonical: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "fmt", "WHAT=check"], cwd=tmp_path
            )
        )
        tm.that(canonical.exit_code, eq=0, msg=canonical.stdout + canonical.stderr)
        invocations = invocation_log.read_text(encoding="utf-8")
        tm.that(
            invocations,
            has=["workspace serialize-make", "--verb fmt", "--selector-value check"],
        )
        calls_before_retired = invocations.splitlines()

        retired: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "format"], cwd=tmp_path
            )
        )
        tm.that(retired.exit_code, ne=0)
        tm.that(
            invocation_log.read_text(encoding="utf-8").splitlines(),
            eq=calls_before_retired,
        )

    def test_recursive_dispatch_preserves_explicit_makefile(
        self, tmp_path: Path
    ) -> None:
        """An external -f invocation keeps the selected Make owner and runtime."""
        caller_root = tmp_path / "consumer"
        caller_root.mkdir()
        target_root = tmp_path / "target"
        target_root.mkdir()
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        self._write_generated_make(engine_root)
        selected_makefile = engine_root / config.Infra.codegen.surfaces.make_engine_path
        (caller_root / "Makefile").write_text("all:\n\t@exit 99\n", encoding="utf-8")
        invocation_log = engine_root / "python-args.log"
        test_u.Tests.write_executable(
            engine_root / ".venv" / "bin" / "python",
            (
                "#!/bin/sh\n"
                f'printf "workspace=%s\\nargs=%s\\n" '
                f'"$FLEXT_MAKE_INPUT_WORKSPACE" "$*" > "{invocation_log}"\n'
            ),
        )

        executed: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "-f",
                    str(selected_makefile),
                    "worktree",
                    "WHAT=list",
                    f"WORKSPACE={target_root}",
                ],
                cwd=caller_root,
            )
        )

        tm.that(executed.exit_code, eq=0, msg=executed.stdout + executed.stderr)
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=[
                f"workspace={target_root}",
                "-m flext_infra workspace serialize-make",
                f"--workspace {engine_root}",
                f"--makefile {selected_makefile}",
                "--verb worktree",
                "--selector-value list",
            ],
        )

    def test_external_makefile_owns_the_serialization_engine(
        self, tmp_path: Path
    ) -> None:
        """A selected Make owner, not its caller, owns runtime and lock routing."""
        caller_root = tmp_path / "consumer"
        caller_root.mkdir()
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        self._write_generated_make(engine_root)
        selected_makefile = engine_root / config.Infra.codegen.surfaces.make_engine_path
        invocation_log = engine_root / "python-args.log"
        test_u.Tests.write_executable(
            engine_root / ".venv" / "bin" / "python",
            f'#!/bin/sh\nprintf "%s\\n" "$*" > "{invocation_log}"\n',
        )
        test_u.Tests.write_executable(
            caller_root / ".venv" / "bin" / "python", "#!/bin/sh\nexit 91\n"
        )
        executed: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "-f", str(selected_makefile), "test"],
                cwd=caller_root,
            )
        )

        tm.that(executed.exit_code, eq=0, msg=executed.stdout + executed.stderr)
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=[
                "-m flext_infra workspace serialize-make",
                f"--workspace {engine_root}",
                f"--makefile {selected_makefile}",
                "--verb test",
            ],
        )

    def test_explicit_target_replaces_the_default_suite(self, tmp_path: Path) -> None:
        """A focused target is the pytest target, not an appendix to tests/."""
        self._write_generated_make(tmp_path)
        invocation_log = tmp_path / "python-args.log"
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python",
            (
                "#!/bin/sh\n"
                f'printf "file=%s\\nargs=%s\\n" "$FLEXT_MAKE_INPUT_FILE" "$*" '
                f'> "{invocation_log}"\n'
            ),
        )
        selected = "tests/unit/selected_test.py"
        selected_path = tmp_path / selected
        selected_path.parent.mkdir(parents=True)
        selected_path.write_text(
            "from flext_tests import tm\n\n"
            "def test_selected() -> None:\n"
            "    tm.that(True, eq=True)\n",
            encoding="utf-8",
        )

        executed: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "test", f"FILE={selected}"], cwd=tmp_path
            )
        )

        tm.that(
            executed.exit_code,
            eq=0,
            msg=f"stdout:\n{executed.stdout}\nstderr:\n{executed.stderr}",
        )
        arguments = invocation_log.read_text(encoding="utf-8")
        tm.that(arguments, has=f"file={selected}")
        tm.that(arguments, has=["workspace serialize-make", "--verb test"])

    def test_generated_test_recipe_uses_one_typed_runner_boundary(self) -> None:
        """Forward supported selectors without reconstructing pytest in shell.

        Without this, a targeted run is impossible through `make`, and the only
        way to filter is to call pytest directly -- exactly the loose command the
        canonical-command law forbids.
        """
        make = config.Infra.codegen.make
        test_verb = next(verb for verb in make.verbs if verb.name == "test")
        operation = next(
            operation
            for operation in make.operations
            if operation.name == test_verb.operation
        )
        input_by_variable = {
            variable: item.name for item in make.inputs for variable in item.variables
        }
        selector_variables = ("FILE", "MATCH", "FAIL_FAST")
        selector_inputs = tuple(input_by_variable[name] for name in selector_variables)
        checkout_root = Path(__file__).resolve().parents[3]
        engine = (
            checkout_root / config.Infra.codegen.surfaces.make_engine_path
        ).read_text(encoding="utf-8")

        tm.that(operation.executor, eq="runtime")
        tm.that(operation.inputs, has=selector_inputs)
        tm.that(engine.count("workspace serialize-make"), eq=1)
        tm.that(
            engine, lacks=["pytest", "_pytest_entry", "grep ", "awk ", "PYTEST_TARGETS"]
        )

    def test_generated_make_owners_derive_from_the_typed_ssot(self) -> None:
        """The wrapper and engine expose the one config-owned operation graph."""
        codegen = config.Infra.codegen
        make = codegen.make
        generation_operations = tuple(
            operation
            for operation in make.operations
            if operation.executor == "generation"
        )
        generation_verbs = tuple(
            verb
            for verb in make.verbs
            if any(
                operation.name == verb.operation for operation in generation_operations
            )
        )
        tm.that(generation_operations, len=1)
        tm.that(generation_verbs, len=1)

        wrapper_path = Path(codegen.surfaces.make_wrapper_path)
        engine_path = Path(codegen.surfaces.make_engine_path)
        wrapper: str = tm.ok(u.Cli.files_read_text(wrapper_path))
        engine: str = tm.ok(u.Cli.files_read_text(engine_path))
        public_verbs = " ".join(verb.name for verb in make.verbs)

        tm.that(wrapper, has=f"include {engine_path.as_posix()}")
        tm.that(engine, has=f"PUBLIC_VERBS := {public_verbs}")
        tm.that(
            f"{wrapper}\n{engine}",
            lacks=["custom.mk", "_custom_", "_builtin_gen_apply"],
        )
