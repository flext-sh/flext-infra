"""Process entrypoint for the canonical centralized flext-infra CLI."""

from __future__ import annotations

import sys

if __name__ == "__main__":
    cli_args = sys.argv[1:]
    if cli_args[:2] == ["validate", "pytest-diag"]:
        from flext_infra._pytest_diag_fast import main as pytest_diag_main

        raise SystemExit(pytest_diag_main(cli_args[2:]))

    from flext_cli import cli
    from flext_infra import main

    cli.exit(main(cli_args))
