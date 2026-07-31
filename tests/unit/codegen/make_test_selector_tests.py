"""Behavior contract for focused pytest selection through generated Make."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, p, u
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

        makefile: str = tm.ok(u.Cli.files_read_text(Path("Makefile")))
        (tmp_path / "Makefile").write_text(makefile, encoding="utf-8")
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python", "#!/bin/sh\nexit 0\n"
        )
        invocation_log = tmp_path / "uv-args.log"
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            uv, f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{invocation_log}"\n'
        )

        canonical: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "fmt", "WHAT=check", f"UV={uv}"], cwd=tmp_path
            )
        )
        tm.that(canonical.exit_code, eq=0, msg=canonical.stdout + canonical.stderr)
        invocations = invocation_log.read_text(encoding="utf-8")
        tm.that(invocations, has=["ruff check --no-fix", "ruff format --check"])
        calls_before_retired = invocations.splitlines()

        retired: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "format", f"UV={uv}"], cwd=tmp_path
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
        selected_makefile = engine_root / "canonical.mk"
        selected_makefile.write_text(
            tm.ok(u.Cli.files_read_text(Path("Makefile"))), encoding="utf-8"
        )
        (caller_root / "Makefile").write_text("all:\n\t@exit 99\n", encoding="utf-8")
        invocation_log = engine_root / "python-args.log"
        test_u.Tests.write_executable(
            engine_root / ".venv" / "bin" / "python",
            (f'#!/bin/sh\nprintf "%s\\n" "$PYTHONPATH" "$*" > "{invocation_log}"\n'),
        )
        uv = caller_root / "bin" / "uv"
        test_u.Tests.write_executable(uv, "#!/bin/sh\nexit 0\n")

        executed: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "-f",
                    str(selected_makefile),
                    "worktree",
                    "WHAT=list",
                    f"WORKSPACE={target_root}",
                    f"UV={uv}",
                ],
                cwd=caller_root,
            )
        )

        tm.that(executed.exit_code, eq=0, msg=executed.stdout + executed.stderr)
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=[
                str(engine_root / "src"),
                "-m flext_infra workspace worktree",
                f"--workspace {target_root}",
                "--operation list",
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
        selected_makefile = engine_root / "canonical.mk"
        selected_makefile.write_text(
            tm.ok(u.Cli.files_read_text(Path("Makefile"))), encoding="utf-8"
        )
        invocation_log = engine_root / "python-args.log"
        test_u.Tests.write_executable(
            engine_root / ".venv" / "bin" / "python",
            f'#!/bin/sh\nprintf "%s\\n" "$*" > "{invocation_log}"\n',
        )
        test_u.Tests.write_executable(
            caller_root / ".venv" / "bin" / "python", "#!/bin/sh\nexit 91\n"
        )
        uv = caller_root / "bin" / "uv"
        test_u.Tests.write_executable(uv, "#!/bin/sh\nexit 0\n")

        executed: p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "-f",
                    str(selected_makefile),
                    "test",
                    f"UV={uv}",
                ],
                cwd=caller_root,
            )
        )

        tm.that(executed.exit_code, eq=0, msg=executed.stdout + executed.stderr)
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=[
                "-m flext_infra workspace serialize-make",
                f"--workspace {caller_root}",
                f"--makefile {selected_makefile}",
                "--verb test",
            ],
        )

    def test_explicit_target_replaces_the_default_suite(self, tmp_path: Path) -> None:
        """A focused target is the pytest target, not an appendix to tests/."""
        makefile: str = tm.ok(u.Cli.files_read_text(Path("Makefile")))
        (tmp_path / "Makefile").write_text(makefile, encoding="utf-8")
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python",
            (
                "#!/bin/sh\n"
                "verb=''\n"
                "mode=''\n"
                "previous=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  if [ "$argument" = "validate" ]; then mode="validate"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then\n'
                '  exec make --no-print-directory "_serialized_${verb}"\n'
                "fi\n"
                'if [ "$mode" = "validate" ]; then\n'
                "  printf '%s\\n' failed_count=0 error_count=0 "
                "warning_count=0 skipped_count=0\n"
                "  exit 0\n"
                "fi\n"
                "exit 2\n"
            ),
        )
        invocation_log = tmp_path / "uv-args.log"
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            uv, f'#!/bin/sh\nprintf "%s\\n" "$@" > "{invocation_log}"\n'
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
                [
                    "--no-print-directory",
                    "test",
                    f"PYTEST_TARGETS={selected}",
                    f"UV={uv}",
                ],
                cwd=tmp_path,
            )
        )

        tm.that(
            executed.exit_code,
            eq=0,
            msg=f"stdout:\n{executed.stdout}\nstderr:\n{executed.stderr}",
        )
        arguments = invocation_log.read_text(encoding="utf-8")
        tm.that(arguments, has=selected)
        tm.that(str(tmp_path / "tests") not in arguments, where=bool)

    def test_generated_test_recipe_forwards_pytest_args(self) -> None:
        """Forward both supported pytest selectors through the local recipe.

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
        tm.that(template, has='"$(PYTEST_TARGETS)"')

    def test_generated_owners_use_distinct_canonical_verbs(self) -> None:
        """Gen (conform) and base.mk generation remain distinct operations."""
        template = _makefile_template().read_text(encoding="utf-8")
        repository = next(
            repository
            for repository in config.Infra.codegen.repositories
            if repository.name == "flext-infra"
        )
        extra_verbs = {verb.name: verb.default_what for verb in repository.extra_verbs}

        tm.that(template, has="_builtin_gen_apply")
        tm.that(extra_verbs, eq={"basemk": "generate"})
        tm.that(template, lacks="_builtin_build_gen")
