"""Render the canonical focused pytest cProfile artifact.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from pathlib import Path

from flext_infra import c, config, u
from flext_infra.validate import FlextInfraCProfileReport


class FlextInfraCprofileEntry:
    """Thin transport for the canonical cProfile report service."""

    @staticmethod
    def main() -> int:
        """Dispatch focused or explicitly receipted profiles to the report owner.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If the profile manifest has no repository owner.

        """
        report_root = Path.cwd().resolve() / ".reports" / "cprofile"
        profile_path = (
            Path(sys.argv[1]) if len(sys.argv) > 1 else report_root / "pytest.pstats"
        ).resolve()
        repository_root = u.Infra.nearest_project_root(
            Path.cwd().resolve(),
            profile_path,
        )
        if repository_root is None:
            msg = f"cProfile manifest owner is unresolved: {profile_path}"
            raise ValueError(msg)
        output_path = profile_path.with_suffix(".txt")
        policy = config.Infra.tooling.tools.pytest
        FlextInfraCProfileReport(
            repository_root=repository_root,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
            run_receipt=(
                Path(sys.argv[2])
                if len(sys.argv) >= c.Infra.CPROFILE_RECEIPT_ARGUMENT_COUNT
                else None
            ),
        ).execute().unwrap()
        return 0


if __name__ == "__main__":
    raise SystemExit(FlextInfraCprofileEntry.main())
