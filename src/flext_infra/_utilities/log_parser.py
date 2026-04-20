"""Extract error information from verb log files.

Provides utilities for reading the tail of orchestration log files
and extracting error-like lines for display in orchestrator output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path

from flext_infra import c, t


class FlextInfraUtilitiesLogParser:
    """Extract error information from verb log files."""

    # Inline patterns moved to c.Infra.LogParser

    @staticmethod
    def extract_errors(
        log_path: Path,
        *,
        max_lines: int = 5,
    ) -> t.Infra.Pair[int, t.StrSequence]:
        """Read log tail and extract error lines.

        Args:
            log_path: Path to the log file.
            max_lines: Maximum number of error lines to return.

        Returns:
            Tuple of (total_error_count, first_n_error_lines).

        """
        if not log_path.exists():
            return (0, [])
        try:
            text = log_path.read_text(
                encoding=c.Infra.ENCODING_DEFAULT, errors="replace"
            )
        except OSError:
            return (0, [])
        tail = text.splitlines()[-c.Infra.LOG_TAIL_LINES :]
        error_lines: MutableSequence[str] = []
        for line in tail:
            stripped = line.strip()
            if not stripped:
                continue
            if any(pattern.search(stripped) for pattern in c.Infra.LOG_NOISE_PATTERNS):
                continue
            if any(pattern.search(stripped) for pattern in c.Infra.LOG_ERROR_PATTERNS):
                error_lines.append(stripped)
        total = len(error_lines)
        return (total, error_lines[:max_lines])


__all__: list[str] = ["FlextInfraUtilitiesLogParser"]
