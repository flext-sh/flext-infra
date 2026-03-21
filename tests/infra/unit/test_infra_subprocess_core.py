"""Tests for FlextInfraUtilitiesSubprocess — core run/capture operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import m, u

from flext_infra import FlextInfraUtilitiesSubprocess, m


@pytest.fixture
def runner() -> FlextInfraUtilitiesSubprocess:
    return FlextInfraUtilitiesSubprocess()


@pytest.mark.parametrize(
    (
        "command",
        "timeout",
        "env",
        "use_tmp_path",
        "expect_success",
        "stdout_has",
        "stderr_has",
        "exit_code",
        "error_has",
    ),
    [
        (["echo", "hello"], None, None, False, True, "hello", "", 0, ""),
        (["sh", "-c", "echo error >&2"], None, None, False, True, "", "error", 0, ""),
        (["sh", "-c", "exit 42"], None, None, False, True, "", "", 42, ""),
        (["pwd"], None, None, True, True, "", "", 0, ""),
        (
            ["sh", "-c", "echo $TEST_VAR"],
            None,
            {"TEST_VAR": "raw_value"},
            False,
            True,
            "raw_value",
            "",
            0,
            "",
        ),
        (["sleep", "10"], 1, None, False, False, "", "", None, "timeout"),
        (["nonexistent_command_xyz"], None, None, False, False, "", "", None, ""),
    ],
    ids=["echo", "stderr", "nonzero-exit", "cwd", "env", "timeout", "invalid-command"],
)
def test_run_raw_cases(
    runner: FlextInfraUtilitiesSubprocess,
    tmp_path: Path,
    command: list[str],
    timeout: int | None,
    env: dict[str, str] | None,
    use_tmp_path: bool,
    expect_success: bool,
    stdout_has: str,
    stderr_has: str,
    exit_code: int | None,
    error_has: str,
) -> None:
    cwd = tmp_path if use_tmp_path else None
    result = runner.run_raw(command, cwd=cwd, timeout=timeout, env=env)
    if expect_success:
        output = u.Tests.Matchers.ok(result)
        assert isinstance(output, m.Infra.CommandOutput)
        if stdout_has:
            u.Tests.Matchers.that(output.stdout, has=stdout_has)
        if stderr_has:
            u.Tests.Matchers.that(output.stderr, has=stderr_has)
        if use_tmp_path:
            u.Tests.Matchers.that(output.stdout.strip(), eq=str(tmp_path))
        if exit_code is not None:
            u.Tests.Matchers.that(output.exit_code, eq=exit_code)
        return
    if error_has:
        u.Tests.Matchers.fail(result, has=error_has)
        return
    u.Tests.Matchers.fail(result)


@pytest.mark.parametrize(
    (
        "command",
        "timeout",
        "env",
        "use_tmp_path",
        "expect_success",
        "stdout_has",
        "error_has",
    ),
    [
        (["echo", "hello"], None, None, False, True, "hello", ""),
        (["pwd"], None, None, True, True, "", ""),
        (
            ["sh", "-c", "echo $TEST_VAR"],
            None,
            {"TEST_VAR": "test_value"},
            False,
            True,
            "test_value",
            "",
        ),
        (["sh", "-c", "exit 1"], None, None, False, False, "", "command failed"),
        (["sleep", "10"], 1, None, False, False, "", "timeout"),
    ],
    ids=["success", "cwd", "env", "nonzero-failure", "timeout"],
)
def test_run_cases(
    runner: FlextInfraUtilitiesSubprocess,
    tmp_path: Path,
    command: list[str],
    timeout: int | None,
    env: dict[str, str] | None,
    use_tmp_path: bool,
    expect_success: bool,
    stdout_has: str,
    error_has: str,
) -> None:
    cwd = tmp_path if use_tmp_path else None
    result = runner.run(command, cwd=cwd, timeout=timeout, env=env)
    if expect_success:
        output = u.Tests.Matchers.ok(result)
        if stdout_has:
            u.Tests.Matchers.that(output.stdout, has=stdout_has)
        if use_tmp_path:
            u.Tests.Matchers.that(output.stdout.strip(), eq=str(tmp_path))
        return
    u.Tests.Matchers.fail(result, has=error_has)


@pytest.mark.parametrize(
    (
        "command",
        "timeout",
        "env",
        "use_tmp_path",
        "expect_success",
        "expected",
        "error_has",
    ),
    [
        (["echo", "captured"], None, None, False, True, "captured", ""),
        (["echo", "text"], None, None, False, True, "text", ""),
        (["pwd"], None, None, True, True, "", ""),
        (
            ["sh", "-c", "echo $TEST_VAR"],
            None,
            {"TEST_VAR": "captured_value"},
            False,
            True,
            "captured_value",
            "",
        ),
        (["sh", "-c", "exit 1"], None, None, False, False, "", ""),
        (["sleep", "10"], 1, None, False, False, "", ""),
    ],
    ids=["success", "strip-whitespace", "cwd", "env", "nonzero-failure", "timeout"],
)
def test_capture_cases(
    runner: FlextInfraUtilitiesSubprocess,
    tmp_path: Path,
    command: list[str],
    timeout: int | None,
    env: dict[str, str] | None,
    use_tmp_path: bool,
    expect_success: bool,
    expected: str,
    error_has: str,
) -> None:
    cwd = tmp_path if use_tmp_path else None
    result = runner.capture(command, cwd=cwd, timeout=timeout, env=env)
    if expect_success:
        output = u.Tests.Matchers.ok(result)
        if use_tmp_path:
            u.Tests.Matchers.that(output, eq=str(tmp_path))
            return
        u.Tests.Matchers.that(output, eq=expected)
        return
    if error_has:
        u.Tests.Matchers.fail(result, has=error_has)
        return
    u.Tests.Matchers.fail(result)
