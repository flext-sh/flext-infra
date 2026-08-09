"""Real-process contract for per-checkout Make validation serialization.

Integration scope by nature: every case here spawns real ``flext_infra``
CLI processes (or a real outer ``make``) and proves that two independent
operating-system processes serialize through one native checkout lock. That
guarantee cannot be observed in-process, and a real CLI start-up exceeds the
unit case deadline, so these contracts live beside the other end-to-end
suites instead of being weakened or faked in the unit tier.

The in-process contracts for the same service (typed SSOT validation, lock
callback classification, fingerprint semantics, single-flight ordering) stay
in ``tests/unit/workspace/test_make_serialization.py``.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from filelock import FileLock, Timeout

from flext_infra import c, config, p, u
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_tests import tm
from tests import u as test_u

# Derived from the handler SSOT: a serialized mutation runs the verb's
# apply selector, then re-checks itself with the read-only default.
_MUTATION_CASES = tuple(
    (verb.name, verb.apply_what, verb.default_what)
    for verb in config.Infra.codegen.make.verbs
    if verb.name in config.Infra.codegen.make.serialization.mutation_verbs
)


@pytest.mark.xdist_group("make-single-flight")
class TestsFlextInfraMakeSerializationProcesses:
    """Prove configured Make verbs share one native lock across real processes."""

    _process_start_timeout_seconds = 30

    def test_serialized_validations_cannot_overlap_in_one_checkout(
        self, tmp_path: Path
    ) -> None:
        """Two public CLI processes serialize their nested Make executions."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "root = Path(sys.argv[1])\n"
                "state = root / '.reports' / 'serialization-test'\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "active = state / 'active'\n"
                "started = state / 'incumbent-started'\n"
                "contender = state / 'contender-entered'\n"
                "overlap = state / 'overlap'\n"
                "if not started.exists():\n"
                "    active.write_text('incumbent', encoding='utf-8')\n"
                "    started.write_text('', encoding='utf-8')\n"
                "    release = state / 'incumbent-release'\n"
                "    deadline = time.monotonic() + 30\n"
                "    while time.monotonic() < deadline and not release.exists():\n"
                "        time.sleep(0.01)\n"
                "    if not release.exists():\n"
                "        raise SystemExit(9)\n"
                "    active.unlink()\n"
                "else:\n"
                "    contender.write_text('', encoding='utf-8')\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write('contender')\n"
                "    except FileExistsError:\n"
                "        overlap.write_text('', encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@{sys.executable} {worker} {tmp_path}\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        command = [
            sys.executable,
            "-m",
            c.Infra.PACKAGE_IMPORT_NAME,
            c.Infra.CLI_GROUP_WORKSPACE,
            "serialize-make",
            "--workspace",
            str(tmp_path),
            "--makefile",
            str(makefile),
            "--verb",
        ]

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            incumbent_future = executor.submit(
                u.Cli.run_raw, [*command, validation_verb], tmp_path
            )
            contender_future = None
            release = tmp_path / ".reports" / "serialization-test" / "incumbent-release"
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (
                        tmp_path
                        / ".reports"
                        / "serialization-test"
                        / "incumbent-started"
                    ).exists()
                    and not incumbent_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that(
                    (
                        tmp_path
                        / ".reports"
                        / "serialization-test"
                        / "incumbent-started"
                    ).exists(),
                    where=bool,
                )
                contender_future = executor.submit(
                    u.Cli.run_raw, [*command, validation_verb], tmp_path
                )
                release.write_text("", encoding="utf-8")
                incumbent_process = tm.ok(
                    incumbent_future.result(timeout=self._process_start_timeout_seconds)
                )
                contender_process = tm.ok(
                    contender_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                release.touch()
                incumbent_future.cancel()
                if contender_future is not None:
                    contender_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        tm.that(incumbent_process.exit_code, eq=0)
        tm.that(contender_process.exit_code, eq=0)
        tm.that(
            not (tmp_path / ".reports" / "serialization-test" / "overlap").exists(),
            where=bool,
        )
        tm.that(
            (tmp_path / config.Infra.codegen.make.serialization.lock_path).is_file(),
            where=bool,
        )

    def test_external_callers_share_the_selected_make_engine_lock(
        self, tmp_path: Path
    ) -> None:
        """Different callers of one selected Make owner cannot overlap."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        state = engine_root / "state"
        worker = engine_root / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "state = Path(sys.argv[1])\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "active = state / 'active'\n"
                "started = state / 'started'\n"
                "release = state / 'release'\n"
                "overlap = state / 'overlap'\n"
                "if not started.exists():\n"
                "    active.write_text('incumbent', encoding='utf-8')\n"
                "    started.write_text('', encoding='utf-8')\n"
                "    deadline = time.monotonic() + 30\n"
                "    while time.monotonic() < deadline and not release.exists():\n"
                "        time.sleep(0.01)\n"
                "    if not release.exists():\n"
                "        raise SystemExit(9)\n"
                "    active.unlink()\n"
                "else:\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write('contender')\n"
                "    except FileExistsError:\n"
                "        overlap.write_text('', encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        selected_makefile = engine_root / "canonical.mk"
        selected_makefile.write_text(
            (
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@{sys.executable} {worker} {state}\n"
            ),
            encoding="utf-8",
        )
        callers = (tmp_path / "caller-a", tmp_path / "caller-b")
        for caller in callers:
            caller.mkdir()
            test_u.Tests.initialize_git_repo(caller)

        def command(caller: Path) -> p.Result[p.Cli.CommandOutput]:
            return u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(caller),
                    "--makefile",
                    str(selected_makefile),
                    "--verb",
                    validation_verb,
                ],
                cwd=caller,
            )

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            incumbent_future = executor.submit(command, callers[0])
            contender_future = None
            release = state / "release"
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "started").exists()
                    and not incumbent_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "started").exists(), where=bool)
                contender_future = executor.submit(command, callers[1])
                release.write_text("", encoding="utf-8")
                incumbent = tm.ok(
                    incumbent_future.result(timeout=self._process_start_timeout_seconds)
                )
                contender = tm.ok(
                    contender_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                release.touch()
                incumbent_future.cancel()
                if contender_future is not None:
                    contender_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        tm.that(incumbent.exit_code, eq=0)
        tm.that(contender.exit_code, eq=0)
        tm.that(not (state / "overlap").exists(), where=bool)
        tm.that(
            (engine_root / config.Infra.codegen.make.serialization.lock_path).is_file(),
            where=bool,
        )

    def test_private_failure_reaches_cli_and_outer_make(self, tmp_path: Path) -> None:
        """A private nonzero status is never coerced into public success."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        private_exit_code = 7
        make_failure_exit_code = 2
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        cli_command = (
            f"{sys.executable} -m {c.Infra.PACKAGE_IMPORT_NAME} "
            f"{c.Infra.CLI_GROUP_WORKSPACE} serialize-make "
            f"--workspace {tmp_path} --makefile {makefile} --verb {validation_verb}"
        )
        makefile.write_text(
            (
                f".PHONY: {validation_verb} _serialized_{validation_verb}\n"
                f"{validation_verb}:\n"
                f"\t@{cli_command}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@exit {private_exit_code}\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)

        outer_make = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", validation_verb], cwd=tmp_path
            )
        )

        tm.that(outer_make.exit_code, eq=make_failure_exit_code)
        tm.that(outer_make.stdout + outer_make.stderr, has=f"Error {private_exit_code}")
        tm.that(outer_make.exit_code, ne=0)

    def test_selected_makefile_is_required_at_the_cli_boundary(
        self, tmp_path: Path
    ) -> None:
        """A caller cannot silently fall back to a different Make owner."""
        process = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(tmp_path),
                    "--verb",
                    config.Infra.codegen.make.serialization.verbs[0],
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, ne=0)
        tm.that(process.stdout + process.stderr, has="makefile")

    def test_writer_ignoring_lock_invalidates_gate_snapshot(
        self, tmp_path: Path
    ) -> None:
        """A concurrent content writer makes a green private target invalid."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        writer = tmp_path / "writer.py"
        writer.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "time.sleep(0.1)\n"
                "Path(sys.argv[1]).write_text('changed', encoding='utf-8')\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@{sys.executable} {writer} {tmp_path / 'concurrent.txt'} & "
                "sleep 0.4\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)

        process = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(tmp_path),
                    "--makefile",
                    str(makefile),
                    "--verb",
                    validation_verb,
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, eq=int(c.Infra.ScriptExitCode.INFRA))
        tm.that(
            process.stdout + process.stderr,
            has=[
                f"workspace changed during serialized Make {validation_verb}",
                "concurrent.txt",
            ],
        )

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_declared_mutation_runs_fixed_point_without_rejecting_own_output(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """An authorized generator apply owns its projection and proves stability."""
        make_config = config.Infra.codegen.make
        tm.that(
            fixed_point_what,
            eq=next(
                verb.default_what
                for verb in make_config.verbs
                if verb.name == mutation_verb
            ),
        )
        projection = tmp_path / "generated.txt"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.apply_variable})" = '
                f'"{make_config.apply_value}" ]; then '
                f"printf 'generated\\n' > {projection}; "
                f"else "
                f'[ "$({make_config.apply_variable})" != '
                f'"{make_config.apply_value}" ] || exit 9; '
                "fi\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)

        process = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(tmp_path),
                    "--makefile",
                    str(makefile),
                    "--verb",
                    mutation_verb,
                    "--selector-value",
                    mutation_what,
                    "--apply-token",
                    make_config.apply_value,
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(projection.read_text(encoding="utf-8"), eq="generated\n")

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_transaction_owned_mutation_avoids_nested_lock_and_locks_fixed_point(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """The child owns apply serialization before Make locks the fixed point."""
        make_config = config.Infra.codegen.make
        tm.that(
            fixed_point_what,
            eq=next(
                verb.default_what
                for verb in make_config.verbs
                if verb.name == mutation_verb
            ),
        )
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "state = Path(sys.argv[1])\n"
                "phase = sys.argv[2]\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "events = state / 'events'\n"
                "with events.open('a', encoding='utf-8') as stream:\n"
                "    stream.write(f'{phase}-start\\n')\n"
                "(state / f'{phase}-started').write_text('', encoding='utf-8')\n"
                "release = state / f'{phase}-release'\n"
                "deadline = time.monotonic() + 30\n"
                "while not release.exists() and time.monotonic() < deadline:\n"
                "    time.sleep(0.01)\n"
                "if not release.exists():\n"
                "    raise SystemExit(9)\n"
                "with events.open('a', encoding='utf-8') as stream:\n"
                "    stream.write(f'{phase}-end\\n')\n"
            ),
            encoding="utf-8",
        )
        state = tmp_path / ".reports" / "serialization-fixed-point"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.apply_variable})" = '
                f'"{make_config.apply_value}" ]; then '
                f"{sys.executable} {worker} {state} mutation; "
                f"else "
                f"{sys.executable} {worker} {state} fixed-point; "
                "fi\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        command = [
            sys.executable,
            "-m",
            c.Infra.PACKAGE_IMPORT_NAME,
            c.Infra.CLI_GROUP_WORKSPACE,
            "serialize-make",
            "--workspace",
            str(tmp_path),
            "--makefile",
            str(makefile),
            "--verb",
        ]

        lock_path = tmp_path / make_config.serialization.lock_path
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            state.mkdir(parents=True, exist_ok=True)
            mutation_future = executor.submit(
                u.Cli.run_raw,
                [
                    *command,
                    mutation_verb,
                    "--selector-value",
                    mutation_what,
                    "--apply-token",
                    make_config.apply_value,
                ],
                tmp_path,
            )
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "mutation-started").exists()
                    and not mutation_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "mutation-started").exists(), where=bool)
                mutation_lock_available = False
                try:
                    with FileLock(lock_path, timeout=0):
                        mutation_lock_available = True
                except Timeout:
                    mutation_lock_available = False
                tm.that(mutation_lock_available, where=bool)
                (state / "mutation-release").write_text("", encoding="utf-8")

                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "fixed-point-started").exists()
                    and not mutation_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "fixed-point-started").exists(), where=bool)
                fixed_point_lock_held = False
                try:
                    with FileLock(lock_path, timeout=0):
                        pass
                except Timeout:
                    fixed_point_lock_held = True
                tm.that(fixed_point_lock_held, where=bool)
                (state / "fixed-point-release").write_text("", encoding="utf-8")
                mutation = tm.ok(
                    mutation_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                (state / "mutation-release").touch()
                (state / "fixed-point-release").touch()
                mutation_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        tm.that(mutation.exit_code, eq=0, msg=mutation.stdout + mutation.stderr)
        with FileLock(lock_path, timeout=0):
            pass
        tm.that(
            (state / "events").read_text(encoding="utf-8").splitlines(),
            eq=[
                "mutation-start",
                "mutation-end",
                "fixed-point-start",
                "fixed-point-end",
            ],
        )

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_transaction_to_fixed_point_lock_gap_fails_closed_on_drift(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """Reject drift landing after transaction apply and before the lock.

        The window is produced by real processes only: the apply recipe leaves a
        detached writer behind, and an incumbent holds the mutation lock so the
        service is genuinely parked between its post-transaction snapshot and
        the locked fixed point when that writer mutates the checkout.
        """
        make_config = config.Infra.codegen.make
        projection = tmp_path / "projection.txt"
        drift_writer = tmp_path / "drift_writer.py"
        drift_writer.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "time.sleep(0.5)\n"
                "Path(sys.argv[1]).write_text('drift\\n', encoding='utf-8')\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.selector})" = "{mutation_what}" ]; then '
                f"printf 'generated\\n' > {projection}; "
                f"{sys.executable} {drift_writer} {tmp_path / 'concurrent.txt'} "
                "</dev/null >/dev/null 2>&1 & "
                f'elif [ "$({make_config.selector})" = "{fixed_point_what}" ]; then '
                ":; else exit 8; fi\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        lock_path = tmp_path / make_config.serialization.lock_path
        service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": mutation_verb,
            "makefile": makefile,
            "selector_value": mutation_what,
            "apply_token": make_config.apply_value,
        })

        incumbent_lock = FileLock(
            lock_path, timeout=0, fallback_to_soft=False, preserve_lock_file=True
        )
        incumbent_lock.acquire()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                execution_future = executor.submit(service.execute)
                try:
                    drift_file = tmp_path / "concurrent.txt"
                    deadline = (
                        time.monotonic() + self._process_start_timeout_seconds
                    )
                    while (
                        not drift_file.exists()
                        and not execution_future.done()
                        and time.monotonic() < deadline
                    ):
                        time.sleep(0.01)
                    tm.that(drift_file.exists(), where=bool)
                    incumbent_lock.release()
                    result = execution_future.result(
                        timeout=self._process_start_timeout_seconds
                    )
                finally:
                    incumbent_lock.release()
                    execution_future.cancel()
        finally:
            incumbent_lock.release()

        tm.fail(
            result,
            has="workspace changed between transaction apply and fixed-point lock",
        )
