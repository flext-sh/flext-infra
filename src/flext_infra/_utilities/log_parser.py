"""Extract error information from verb log files.

Provides utilities for reading the tail of orchestration log files
and extracting error-like lines for display in orchestrator output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, t


class FlextInfraUtilitiesLogParser:
    """Extract error information from verb log files."""

    _ERROR_PATTERNS: ClassVar[Sequence[re.Pattern[str]]] = [
        re.compile(r"^\s*\S+\.py:\d+"),
        re.compile(r"^ERROR:", re.IGNORECASE),
        re.compile(r"^\s+\[B\d+\]"),
        re.compile(r"^FAIL:", re.IGNORECASE),
        re.compile(r"^error:", re.IGNORECASE),
        re.compile(r"^E\s+\w"),
        re.compile(r"^FAILED\s"),
    ]

    _NOISE_PATTERNS: ClassVar[Sequence[re.Pattern[str]]] = [
        re.compile(r"^make\["),
        re.compile(r"warning:\s+(overriding|ignoring)"),
        re.compile(r"^(Total|Success|Failed|Skipped):"),
        re.compile(r"^──\s"),
        re.compile(r"^INFO:"),
    ]

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
                encoding=c.Infra.Encoding.DEFAULT, errors="replace"
            )
        except OSError:
            return (0, [])
        tail = text.splitlines()[-c.Infra.LogParser.TAIL_LINES :]
        error_lines: MutableSequence[str] = []
        for line in tail:
            stripped = line.strip()
            if not stripped:
                continue
            if any(
                pattern.search(stripped)
                for pattern in FlextInfraUtilitiesLogParser._NOISE_PATTERNS
            ):
                continue
            if any(
                pattern.search(stripped)
                for pattern in FlextInfraUtilitiesLogParser._ERROR_PATTERNS
            ):
                error_lines.append(stripped)
        total = len(error_lines)
        return (total, error_lines[:max_lines])


__all__ = ["FlextInfraUtilitiesLogParser"]
