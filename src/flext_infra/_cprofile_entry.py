"""Source-live cProfile target imported before the flext-infra CLI can load.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import os
import runpy
import shlex
import sys
from enum import StrEnum
from typing import Final

_ENV_ACTION: Final[str] = "FLEXT_CPROFILE_ACTION"
_ENV_ARGS: Final[str] = "FLEXT_CPROFILE_ARGS"
_ENV_TARGET: Final[str] = "FLEXT_CPROFILE_TARGET"


class ProfileTarget(StrEnum):
    """Cold import targets whose costs block the canonical command surface."""

    CODEGEN = "codegen"
    CLI = "cli"
    PIPELINE_TEST = "pipeline-test"
    UTILITIES = "utilities"

    @property
    def module(self) -> str:
        """Exact module imported for this profiling target."""
        return {
            ProfileTarget.CODEGEN: "flext_infra.services.cli_routes_codegen",
            ProfileTarget.CLI: "flext_infra",
            ProfileTarget.PIPELINE_TEST: "pytest",
            ProfileTarget.UTILITIES: "flext_infra.utilities",
        }[self]


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        msg = f"required cProfile environment variable is empty: {name}"
        raise ValueError(msg)
    return value


def _execute_target() -> None:
    target = ProfileTarget(_required_environment(_ENV_TARGET))
    if target is ProfileTarget.CLI:
        previous_argv = sys.argv
        sys.argv = [target.module, *shlex.split(os.environ.get(_ENV_ARGS, "--help"))]
        try:
            _ = runpy.run_module(target.module, run_name="__main__")
        except SystemExit as exc:
            if exc.code not in {None, 0}:
                raise
        finally:
            sys.argv = previous_argv
        return
    if target is ProfileTarget.PIPELINE_TEST:
        import pytest

        test_args = shlex.split(
            os.environ.get(
                _ENV_ARGS,
                "tests/unit/codegen/pipeline_tests.py"
                "::test_codegen_pipeline_end_to_end -q",
            )
        )
        exit_code = int(pytest.main(test_args))
        if exit_code != 0:
            raise SystemExit(exit_code)
        return
    _ = importlib.import_module(target.module)


def main() -> int:
    """Execute the selected source-live cProfile target."""
    action = _required_environment(_ENV_ACTION)
    if action == "import":
        _execute_target()
        return 0
    msg = f"invalid cProfile action: {action}"
    raise ValueError(msg)


if __name__ == "__main__":
    raise SystemExit(main())
