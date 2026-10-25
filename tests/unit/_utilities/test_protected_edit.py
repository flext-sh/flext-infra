"""Test protected edit module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra, settings
from tests import c, m, t, tm, u


def _provision_edited_sample(
    tmp_path: Path,
) -> t.Quad[str, Path, str, str]:
    """Provision one lint-gated sample package and its edited source pair.

    Returns:
        The resulting ``t.Quad[str, Path, str, str]``.

    """
    project_config = (
        "[project]\nname = 'sample'\nversion = '1.0.0'\n"
        "[tool.ruff.lint]\nselect = ['F401']\n"
    )
    package = u.Tests.src_package(tmp_path, "sample", pyproject=project_config)
    py_file = package / "sample.py"
    original = "VALUE = 1\n"
    updated = "VALUE = 2\n"
    py_file.write_text(original, encoding=c.DEFAULT_ENCODING)
    return project_config, py_file, original, updated


@pytest.mark.usefixtures("provisioned_workspace")
class TestsFlextInfraUtilitiesProtectedEdit:
    @staticmethod
    @pytest.mark.parametrize(
        "mode", ["empty", "malformed", "signal", "timeout", "launch"]
    )
    def test_native_lint_failure_never_becomes_a_diagnostic_zero(
        tmp_path: Path,
        mode: str,
    ) -> None:
        """Process failures retain native receipts without invented findings."""
        programs = {
            "empty": f"raise SystemExit({c.Cli.EXIT_CODE_FAILURE})",
            "malformed": "print('{}')",
            "signal": "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
            "timeout": "import time; time.sleep(30)",
        }
        command = (
            (str(tmp_path / "absent-lint-executable"),)
            if mode == "launch"
            else (sys.executable, "-c", programs[mode])
        )
        executed = u.Cli.run_raw(command, cwd=tmp_path, timeout=1)
        receipt = u.Infra.lint_gate_result(c.Infra.RUFF, executed)
        tm.that(receipt.errors, eq=())
        tm.ok(receipt.execution_error is not None)
        tm.that(
            u.Infra.lint_execution_errors({receipt.tool_name: receipt}), empty=False
        )
        tm.that(
            u.Infra.lint_new_errors(
                {receipt.tool_name: receipt}, {receipt.tool_name: receipt}
            ),
            eq={},
        )
        if executed.failure:
            tm.that(receipt.output, eq=None)
            tm.that(receipt.execution_error, eq=executed.error)
            tm.that(receipt.error_code, eq=executed.error_code)
            tm.that(receipt.error_data, eq=executed.error_data)
            if executed.exception is not None:
                tm.that(receipt.error_traceback or "", has=str(executed.exception))
        else:
            tm.ok(receipt.output is not None)
            if receipt.output is not None:
                tm.that(
                    receipt.output.outcome.model_dump(),
                    eq={
                        "raw_return_code": executed.value.outcome.raw_return_code,
                        "timed_out": executed.value.outcome.timed_out,
                        "forwarded_signal": executed.value.outcome.forwarded_signal,
                    },
                )
                tm.that(receipt.output.stdout, eq=executed.value.stdout)
                tm.that(receipt.output.stderr, eq=executed.value.stderr)

    @staticmethod
    def test_configuration_failure_is_not_cached_as_clean_lint(
        tmp_path: Path,
    ) -> None:
        """Changing only the native configuration must recover a failed snapshot."""
        project_config, py_file, _, _ = _provision_edited_sample(tmp_path)
        configuration = tmp_path / c.PYPROJECT_FILENAME
        configuration.write_text(
            project_config + "[tool.ruff]\nline-length = 'invalid'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        failed = u.Infra.lint_snapshot(py_file, tmp_path, gates=(c.Infra.RUFF,))
        tm.that(u.Infra.lint_execution_errors(failed), empty=False)
        tm.that(failed[c.Infra.RUFF].errors, eq=())
        configuration.write_text(project_config, encoding=c.DEFAULT_ENCODING)
        recovered = u.Infra.lint_snapshot(py_file, tmp_path, gates=(c.Infra.RUFF,))
        tm.that(u.Infra.lint_execution_errors(recovered), eq=())
        tm.that(recovered[c.Infra.RUFF].errors, eq=())
        tm.ok(recovered[c.Infra.RUFF].output is not None)

    @staticmethod
    @pytest.mark.parametrize("inherited", [False, True])
    def test_valid_configuration_changes_reobserve_unchanged_source(
        tmp_path: Path,
        *,
        inherited: bool,
    ) -> None:
        """Native configuration changes invalidate observations, including extends."""
        project_config, py_file, _, _ = _provision_edited_sample(tmp_path)
        py_file.write_text("import os\n", encoding=c.DEFAULT_ENCODING)
        configuration = tmp_path / c.PYPROJECT_FILENAME
        if inherited:
            configuration = tmp_path / "policy.toml"
            (tmp_path / c.PYPROJECT_FILENAME).write_text(
                "[project]\nname = 'sample'\nversion = '1.0.0'\n"
                "[tool.ruff]\nextend = 'policy.toml'\n",
                encoding=c.DEFAULT_ENCODING,
            )
            project_config = "[lint]\nselect = ['F401']\n"
            configuration.write_text(project_config, encoding=c.DEFAULT_ENCODING)
        before = u.Infra.lint_snapshot(py_file, tmp_path, gates=(c.Infra.RUFF,))
        tm.that(u.Infra.lint_execution_errors(before), eq=())
        tm.that(before[c.Infra.RUFF].errors, empty=False)
        configuration.write_text(
            project_config.replace("F401", "F821"), encoding=c.DEFAULT_ENCODING
        )
        after = u.Infra.lint_snapshot(py_file, tmp_path, gates=(c.Infra.RUFF,))
        tm.that(u.Infra.lint_execution_errors(after), eq=())
        tm.that(after[c.Infra.RUFF].errors, eq=())
        configuration.write_text(project_config, encoding=c.DEFAULT_ENCODING)
        restored = u.Infra.lint_snapshot(py_file, tmp_path, gates=(c.Infra.RUFF,))
        tm.that(restored[c.Infra.RUFF].errors, eq=before[c.Infra.RUFF].errors)

    @staticmethod
    def test_native_ruff_findings_retain_violation_exit_separately(
        tmp_path: Path,
    ) -> None:
        """A validated native finding is not a launch or report failure."""
        _, py_file, _, _ = _provision_edited_sample(tmp_path)
        py_file.write_text("import os\n", encoding=c.DEFAULT_ENCODING)
        snapshot = u.Infra.lint_snapshot(
            py_file, tmp_path, gates=(c.Infra.RUFF,), source="import os\n"
        )
        receipt = snapshot[c.Infra.RUFF]
        tm.that(receipt.errors, empty=False)
        tm.that(receipt.execution_error, eq=None)
        tm.ok(receipt.output is not None)
        if receipt.output is not None:
            tm.fail(u.Cli.process_succeeded(receipt.output.outcome))
        tm.that(u.Infra.lint_new_errors(snapshot, snapshot), eq={})

    @staticmethod
    @pytest.fixture
    def provisioned_workspace(tmp_path: Path) -> None:
        """The edited workspace is a checkout whose environment owns the tools."""
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'sample'\nversion = '1.0.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.provision_checkout(tmp_path)

    @staticmethod
    @pytest.mark.parametrize(c.ProcessingMode.BATCH, [False, True])
    def test_callback_failure_preserves_written_source(
        tmp_path: Path,
        *,
        batch: bool,
    ) -> None:
        """The first callback exception escapes without undoing its writes."""
        _, py_file, original, updated = _provision_edited_sample(tmp_path)

        failure = RuntimeError("protected edit callback failed")

        def fail_after_write() -> None:
            """Surface the callback failure after the requested source is written."""
            raise failure

        def edit() -> None:
            py_file.write_text(updated, encoding=c.DEFAULT_ENCODING)
            fail_after_write()

        def protected_write() -> None:
            """Run the protected edit through the selected batch or file form."""
            if batch:
                u.Infra.protected_source_writes(
                    {py_file: updated},
                    request=m.Infra.ProtectedSourceWritesRequest(
                        workspace=tmp_path,
                        gates=("lint",),
                        expected_sources={py_file: original},
                        post_write=fail_after_write,
                    ),
                )
            else:
                u.Infra.protected_file_edit(
                    py_file,
                    request=m.Infra.ProtectedFileEditRequest(
                        workspace=tmp_path,
                        before_source=original,
                        edit_fn=edit,
                        gates=("lint",),
                    ),
                )

        with pytest.raises(
            RuntimeError, match="protected edit callback failed"
        ) as caught:
            protected_write()
        tm.ok(caught.value is failure)
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=updated)

    @staticmethod
    @pytest.mark.parametrize(c.ProcessingMode.BATCH, [False, True])
    def test_invalid_ruff_configuration_reports_failure_and_preserves_source(
        tmp_path: Path,
        *,
        batch: bool,
    ) -> None:
        """A native configuration error remains visible with the retained edit."""
        project_config, py_file, original, updated = _provision_edited_sample(tmp_path)

        def invalidate_configuration() -> None:
            (tmp_path / c.PYPROJECT_FILENAME).write_text(
                project_config + "[tool.ruff]\nline-length = 'invalid'\n",
                encoding=c.DEFAULT_ENCODING,
            )

        def edit() -> None:
            py_file.write_text(updated, encoding=c.DEFAULT_ENCODING)
            invalidate_configuration()

        result = (
            u.Infra.protected_source_writes(
                {py_file: updated},
                request=m.Infra.ProtectedSourceWritesRequest(
                    workspace=tmp_path,
                    gates=("lint",),
                    expected_sources={py_file: original},
                    post_write=invalidate_configuration,
                ),
            )
            if batch
            else u.Infra.protected_file_edit(
                py_file,
                request=m.Infra.ProtectedFileEditRequest(
                    workspace=tmp_path,
                    before_source=original,
                    edit_fn=edit,
                    gates=("lint",),
                ),
            )
        )
        tm.fail(result[0])
        tm.that(" ".join(result[1]), has="invalid")
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=updated)

    @staticmethod
    @pytest.mark.parametrize(c.ProcessingMode.BATCH, [False, True])
    @pytest.mark.parametrize(
        ("introduced", "nonfixable"),
        [(False, False), (True, False), (True, True)],
    )
    def test_validation_reports_new_findings_and_preserves_all_writes(
        tmp_path: Path,
        *,
        batch: bool,
        introduced: bool,
        nonfixable: bool,
    ) -> None:
        """Lint deltas report failure without repairing or reverting source."""
        package = u.Tests.src_package(
            tmp_path,
            "sample",
            pyproject=(
                "[project]\nname = 'sample'\nversion = '1.0.0'\n"
                "[tool.ruff.lint]\nselect = ['F401', 'F821']\n"
            ),
        )
        py_file = package / "sample.py"
        previous = "VALUE = 1\n"
        updated = "VALUE = 2\n"
        unused = "import os\n"
        original = previous if introduced else unused + previous
        requested = updated + unused if introduced else unused + updated
        if nonfixable:
            requested = "VALUE = missing_value\n"
        py_file.write_text(original, encoding=c.DEFAULT_ENCODING)
        if batch:
            peer = package / "peer.py"
            peer_before = unused + previous
            peer_requested = unused + updated
            peer.write_text(peer_before, encoding=c.DEFAULT_ENCODING)
            result = u.Infra.protected_source_writes(
                {py_file: requested, peer: peer_requested},
                request=m.Infra.ProtectedSourceWritesRequest(
                    workspace=tmp_path,
                    gates=("lint",),
                    expected_sources={py_file: original, peer: peer_before},
                ),
            )
            tm.that(
                peer.read_text(encoding=c.DEFAULT_ENCODING),
                eq=peer_requested,
            )
        else:
            result = u.Infra.protected_source_write(
                py_file,
                request=m.Infra.ProtectedSourceWriteRequest(
                    workspace=tmp_path,
                    updated_source=requested,
                    gates=("lint",),
                ),
            )
        tm.that(result[0], eq=not introduced)
        tm.that(result[1], empty=not introduced)
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=requested)

    @staticmethod
    def _assert_protected_source_write(py_file: Path, workspace: Path) -> None:
        original_source = "def helper() -> int:\n    return 1\n"
        updated_source = "def helper() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.DEFAULT_ENCODING)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=workspace,
                updated_source=updated_source,
                gates=("lint",),
            ),
        )

        tm.ok(result[0])
        tm.that(result[1], empty=True)
        tm.that(
            py_file.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    @staticmethod
    def test_pyrefly_snapshot_uses_the_edited_projects_config(
        tmp_path: Path,
    ) -> None:
        """Protected validation never inherits the orchestrator's Pyrefly config."""
        project = tmp_path / "project"
        source = project / "src" / "sample"
        source.mkdir(parents=True)
        config_path = project / c.PYPROJECT_FILENAME
        config_path.write_text(
            "[project]\nname = 'sample'\nversion = '1.0.0'\n",
            encoding="utf-8",
        )
        py_file = source / "module.py"
        py_file.write_text("VALUE = 1\n", encoding="utf-8")
        commands = dict(u.Infra.lint_commands(py_file, tmp_path, gates=("pyrefly",)))

        tm.that(commands["pyrefly"], has="--config")
        tm.that(commands["pyrefly"], has=str(config_path))

    @staticmethod
    @pytest.mark.parametrize("gate", [c.Infra.RUFF, c.Infra.MYPY])
    def test_preview_source_writes_preserves_live_sources(
        source_preview_workspace: t.Pair[Path, Path],
        gate: str,
    ) -> None:
        tmp_path, package = source_preview_workspace
        py_file = package / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.DEFAULT_ENCODING)
        before_modified_ns = py_file.stat().st_mtime_ns

        result = u.Infra.preview_source_writes(
            {py_file: updated_source},
            workspace=tmp_path,
            source_preview=infra.source_preview(tmp_path),
            gates=(gate,),
        )

        tm.ok(result[0])
        tm.that(result[1], empty=True)
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=original_source)
        tm.that(py_file.stat().st_mtime_ns, eq=before_modified_ns)

    @staticmethod
    def test_staged_source_consumer_reads_candidate_without_live_writes(
        source_preview_workspace: t.Pair[Path, Path],
    ) -> None:
        """Expose candidate bytes to the real consumer through public staging."""
        tmp_path, package = source_preview_workspace
        py_file = package / "sample.py"
        original = "VALUE = 1\n"
        updated = "VALUE = 2\n"
        py_file.write_text(original, encoding=c.DEFAULT_ENCODING)
        before_modified_ns = py_file.stat().st_mtime_ns
        transaction = infra.source_preview(tmp_path)

        def consume_candidate(
            view_root: Path,
            candidates: t.MappingKV[Path, Path],
        ) -> t.Triple[str, str, int]:
            candidate = candidates[py_file.resolve()]
            tm.ok(candidate.is_relative_to(view_root))
            return (
                candidate.read_text(encoding=c.DEFAULT_ENCODING),
                py_file.read_text(encoding=c.DEFAULT_ENCODING),
                py_file.stat().st_mtime_ns,
            )

        observed = transaction.preview_sources(
            tmp_path,
            {py_file.resolve(): updated},
            consume_candidate,
        )
        if observed.failure:
            state = tmp_path / c.Infra.TRANSACTION_STATE_DIRNAME
            u.Cli.info(f"native preview state effects: {tuple(state.rglob('*'))}")
        tm.ok(observed, eq=(updated, original, before_modified_ns))
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        tm.that(py_file.stat().st_mtime_ns, eq=before_modified_ns)

    @staticmethod
    def test_source_preview_preserves_parser_exception_and_cleans_staging(
        source_preview_workspace: t.Pair[Path, Path],
    ) -> None:
        """A real parser failure leaves live bytes untouched for a fresh view."""
        tmp_path, package = source_preview_workspace
        py_file = package / "sample.py"
        original = "VALUE = 1\n"
        invalid = "def value(:\n"
        py_file.write_text(original, encoding=c.DEFAULT_ENCODING)
        before_modified_ns = py_file.stat().st_mtime_ns
        preview = infra.source_preview(tmp_path)

        def parse_candidate(
            view_root: Path,
            candidates: t.MappingKV[Path, Path],
        ) -> str:
            candidate = candidates[py_file.resolve()]
            tm.ok(candidate.is_relative_to(view_root))
            content = candidate.read_text(encoding=c.DEFAULT_ENCODING)
            compile(content, str(candidate), "exec")
            return content

        with pytest.raises(SyntaxError) as raised:
            preview.preview_sources(
                tmp_path,
                {py_file.resolve(): invalid},
                parse_candidate,
            )
        # The staged parse failure is identified by the candidate path it
        # names: this interpreter sources SyntaxError.text from the on-disk
        # file named by ``filename``, so text always shows the live line.
        tm.that(raised.value.filename, eq=str(py_file.resolve()))
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        tm.that(py_file.stat().st_mtime_ns, eq=before_modified_ns)
        fresh = preview.preview_sources(
            tmp_path,
            {py_file.resolve(): "VALUE = 2\n"},
            parse_candidate,
        )
        tm.ok(fresh, eq="VALUE = 2\n")
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        tm.that(py_file.stat().st_mtime_ns, eq=before_modified_ns)

    def test_protected_source_write_skips_pytest_for_non_test_file(
        self,
        tmp_path: Path,
    ) -> None:
        self._assert_protected_source_write(tmp_path / "sample.py", tmp_path)

    def test_protected_source_write_compiles_supporting_test_module(
        self,
        tmp_path: Path,
    ) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        self._assert_protected_source_write(tests_dir / "test_placeholder.py", tmp_path)

    @staticmethod
    @pytest.mark.parametrize("collectable", [False, True])
    def test_protected_source_write_reports_failed_test_validation(
        tmp_path: Path,
        *,
        collectable: bool,
    ) -> None:
        """Failed compilation and zero collection retain their written candidate."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        py_file = tests_dir / "test_candidate.py"
        original = "def helper() -> int:\n    return 1\n"
        updated = (
            "__test__ = False\n\ndef test_candidate() -> None:\n    assert True\n"
            if collectable
            else "return 1\n"
        )
        py_file.write_text(original, encoding=c.DEFAULT_ENCODING)
        inherited = tmp_path / "orchestrator-imports"
        inherited.mkdir()
        marker = tmp_path / "inherited-startup.txt"
        (inherited / "sitecustomize.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('inherited', encoding='utf-8')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        selected_profile = settings.env_lookup(
            c.Infra.PYTEST_PROFILE_CHILD_ROOT_ENV,
        )
        profile_directory = (
            Path(selected_profile) if selected_profile is not None else None
        )
        previous_profiles: set[Path] = (
            set(profile_directory.glob("*.pstats"))
            if profile_directory is not None
            else set()
        )
        with u.Tests.env_vars_context({
            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(inherited),
        }):
            result = u.Infra.protected_source_write(
                py_file,
                request=m.Infra.ProtectedSourceWriteRequest(
                    workspace=tmp_path,
                    updated_source=updated,
                    gates=(),
                ),
            )
        tm.fail(result[0])
        tm.that(result[1], empty=False)
        tm.that(py_file.read_text(encoding=c.DEFAULT_ENCODING), eq=updated)
        tm.fail(marker.exists())
        if collectable and profile_directory is not None:
            tm.that(
                set(profile_directory.glob("*.pstats")) - previous_profiles,
                empty=False,
            )

    @staticmethod
    def test_protected_source_writes_applies_request_options(
        tmp_path: Path,
    ) -> None:
        left_file = tmp_path / "left.py"
        right_file = tmp_path / "right.py"
        left_file.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        right_file.write_text("VALUE = 10\n", encoding=c.DEFAULT_ENCODING)

        result = u.Infra.protected_source_writes(
            {left_file: "VALUE = 2\n", right_file: "VALUE = 20\n"},
            request=m.Infra.ProtectedSourceWritesRequest(
                workspace=tmp_path,
                expected_sources={left_file: "VALUE = 1\n", right_file: "VALUE = 10\n"},
                gates=("lint",),
                skip_pytest=True,
            ),
        )

        tm.ok(result[0])
        tm.that(result[1], empty=True)
        tm.that(
            (
                left_file.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n")
                == "VALUE = 2"
            ),
            eq=True,
        )
        tm.that(
            (
                right_file.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n")
                == "VALUE = 20"
            ),
            eq=True,
        )
