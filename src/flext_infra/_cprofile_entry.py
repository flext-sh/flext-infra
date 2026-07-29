"""Source-live cProfile target imported before the flext-infra CLI can load.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import io
import os
import pstats
from enum import StrEnum
from pathlib import Path
from typing import Final

_ENV_ACTION: Final[str] = "FLEXT_CPROFILE_ACTION"
_ENV_LIMIT: Final[str] = "FLEXT_CPROFILE_LIMIT"
_ENV_SORT: Final[str] = "FLEXT_CPROFILE_SORT"
_ENV_TARGET: Final[str] = "FLEXT_CPROFILE_TARGET"
_ENV_WORKSPACE: Final[str] = "FLEXT_CPROFILE_WORKSPACE"
_MAX_PROFILE_LIMIT: Final[int] = 1000
_SORT_KEYS: Final[frozenset[str]] = frozenset({
    "calls",
    "cumulative",
    "filename",
    "line",
    "name",
    "nfl",
    "pcalls",
    "stdname",
    "time",
})


class ProfileTarget(StrEnum):
    """Cold import targets whose costs block the canonical command surface."""

    CODEGEN = "codegen"
    UTILITIES = "utilities"

    @property
    def module(self) -> str:
        """Exact module imported for this profiling target."""
        return {
            ProfileTarget.CODEGEN: "flext_infra.services.cli_routes_codegen",
            ProfileTarget.UTILITIES: "flext_infra.utilities",
        }[self]


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        msg = f"required cProfile environment variable is empty: {name}"
        raise ValueError(msg)
    return value


def _artifact_paths() -> tuple[Path, Path]:
    workspace = Path(_required_environment(_ENV_WORKSPACE)).resolve()
    target = ProfileTarget(_required_environment(_ENV_TARGET))
    report_root = workspace / ".reports" / "cprofile-import"
    return report_root / f"{target.value}.pstats", report_root / f"{target.value}.txt"


def _import_target() -> None:
    target = ProfileTarget(_required_environment(_ENV_TARGET))
    _ = importlib.import_module(target.module)


def _render_report() -> None:
    profile_path, output_path = _artifact_paths()
    sort = _required_environment(_ENV_SORT)
    if sort not in _SORT_KEYS:
        msg = f"invalid cProfile sort key: {sort}"
        raise ValueError(msg)
    limit = int(_required_environment(_ENV_LIMIT))
    if limit <= 0 or limit > _MAX_PROFILE_LIMIT:
        msg = "cProfile limit must be between 1 and 1000"
        raise ValueError(msg)
    if not profile_path.is_file():
        msg = f"cProfile artifact does not exist: {profile_path}"
        raise FileNotFoundError(msg)
    stream = io.StringIO()
    stats = pstats.Stats(str(profile_path), stream=stream)
    stats.strip_dirs().sort_stats(sort).print_stats(limit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    temporary.write_text(stream.getvalue(), encoding="utf-8")
    temporary.replace(output_path)


def main() -> int:
    """Execute the selected source-live cProfile action."""
    action = _required_environment(_ENV_ACTION)
    if action == "import":
        _import_target()
        return 0
    if action == "report":
        _render_report()
        return 0
    msg = f"invalid cProfile action: {action}"
    raise ValueError(msg)


if __name__ == "__main__":
    raise SystemExit(main())
