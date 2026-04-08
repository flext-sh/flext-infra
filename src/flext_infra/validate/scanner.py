"""Text pattern scanning service.

Scans text files with regex patterns and reports violation counts,
supporting both present-match and absent-match violation modes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_infra import c, r, s, t


class FlextInfraTextPatternScanner(s[bool]):
    """Scans files for regex pattern matches and reports violations.

    Supports include/exclude glob filtering and configurable match
    modes (present = matches are violations, absent = no matches is a violation).
    """

    pattern: Annotated[str, Field(description="Regex pattern")]
    include: Annotated[
        t.StrSequence,
        Field(default_factory=list, description="Include glob"),
    ] = Field(default_factory=list, description="Include glob")
    exclude: Annotated[
        t.StrSequence,
        Field(default_factory=list, description="Exclude glob"),
    ] = Field(default_factory=list, description="Exclude glob")
    match: Annotated[
        str,
        Field(
            default=c.Infra.MatchModes.PRESENT,
            description="Violation mode (present or absent)",
        ),
    ] = c.Infra.MatchModes.PRESENT

    @staticmethod
    def _collect_files(
        scan_root: Path,
        includes: t.StrSequence,
        excludes: t.StrSequence,
    ) -> Sequence[Path]:
        """Collect files matching include/exclude globs."""
        return [
            path
            for path in scan_root.rglob("*")
            if path.is_file()
            and any(
                fnmatch.fnmatch(path.relative_to(scan_root).as_posix(), pat)
                for pat in includes
            )
            and not any(
                fnmatch.fnmatch(path.relative_to(scan_root).as_posix(), pat)
                for pat in excludes
            )
        ]

    @staticmethod
    def _count_matches(files: Sequence[Path], regex: t.Infra.RegexPattern) -> int:
        """Count regex matches across files."""
        total = 0
        for file_path in files:
            try:
                text = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                    errors=c.Infra.IGNORE,
                )
            except OSError:
                continue
            total += sum(1 for _ in regex.finditer(text))
        return total

    def scan(
        self,
        scan_root: Path,
        pattern: str,
        *,
        includes: t.StrSequence,
        excludes: t.StrSequence | None = None,
        match_mode: str = c.Infra.MatchModes.PRESENT,
    ) -> r[t.ConfigurationMapping]:
        """Scan files under scan_root for regex matches.

        Args:
            scan_root: Directory to scan.
            pattern: Regex pattern to search for.
            includes: Glob patterns for files to include.
            excludes: Glob patterns for files to exclude.
            match_mode: ``"present"`` (matches = violations) or
                ``"absent"`` (no matches = violation).

        Returns:
            r with violation count and match details.

        """
        error = self._validate_scan_inputs(scan_root, includes, match_mode)
        if error is not None:
            return r[t.ScalarMapping].fail(error)
        try:
            regex = re.compile(pattern, flags=re.MULTILINE)
            files = self._collect_files(scan_root, includes, excludes or [])
            matches = self._count_matches(files, regex)
            violation_count = (
                matches
                if match_mode == c.Infra.MatchModes.PRESENT
                else 0
                if matches > 0
                else 1
            )
            result: t.MutableConfigurationMapping = {
                "violation_count": violation_count,
                "match_count": matches,
                "files_scanned": len(files),
            }
            return r[t.ScalarMapping].ok(result)
        except re.error as exc:
            return r[t.ScalarMapping].fail(f"invalid regex pattern: {exc}")
        except (OSError, ValueError, TypeError) as exc:
            return r[t.ScalarMapping].fail(f"text pattern scan failed: {exc}")

    @override
    def execute(self) -> r[bool]:
        """Execute the text-pattern scan CLI flow."""
        result = self.scan(
            self.workspace_root,
            self.pattern,
            includes=self.include,
            excludes=self.exclude,
            match_mode=self.match,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "scan failed")
        count = result.value.get("violation_count", 0)
        if isinstance(count, int) and count > 0:
            return r[bool].fail(f"Scan found {count} violation(s)")
        return r[bool].ok(True)

    @staticmethod
    def _validate_scan_inputs(
        scan_root: Path,
        includes: t.StrSequence,
        match_mode: str,
    ) -> str | None:
        """Return an error message if scan inputs are invalid, else None."""
        if not scan_root.exists() or not scan_root.is_dir():
            return f"scan_root directory does not exist: {scan_root}"
        if not includes:
            return "at least one include glob required"
        if match_mode not in {c.Infra.MatchModes.PRESENT, c.Infra.MatchModes.ABSENT}:
            return f"invalid match_mode: {match_mode}"
        return None


__all__ = ["FlextInfraTextPatternScanner"]
