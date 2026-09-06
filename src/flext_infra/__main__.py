"""Process entrypoint for the canonical centralized flext-infra CLI."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import main


def _run() -> None:
    """Run only the facade-backed CLI; managed writes belong to its transaction."""
    cli.exit(main())


if __name__ == "__main__":
    _run()
