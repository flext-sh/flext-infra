"""CLI support utilities for refactor execution and reporting.

Centralizes CLI output, diff printing, rule table formatting, and
impact-map generation previously in ``FlextInfraRefactorCliSupport``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import re
import sys
from collections.abc import Mapping, Sequence
from operator import itemgetter
from pathlib import Path

import orjson

from flext_infra import c, m


class FlextInfraUtilitiesRefactorCli:
    """CLI output, diff, rule-table, and impact-map helpers.

    Usage via namespace::

        from flext_infra import u

        u.Infra.refactor_info("message")
        u.Infra.print_summary(results, dry_run=False)
    """

    @staticmethod
    def refactor_info(message: str) -> None:
        """Write informational output to stdout."""
        _ = sys.stdout.write(f"{message}\n")

    @staticmethod
    def refactor_error(message: str) -> None:
        """Write error output to stderr."""
        _ = sys.stderr.write(f"ERROR: {message}\n")

    @staticmethod
    def refactor_header(message: str) -> None:
        """Write a section header to stdout."""
        _ = sys.stdout.write(f"\n{message}\n")

    @staticmethod
    def refactor_debug(message: str) -> None:
        """Write debug output to stdout."""
        _ = sys.stdout.write(f"DEBUG: {message}\n")

    @staticmethod
    def project_name_from_path(file_path: Path) -> str:
        """Infer project directory name from a file path."""
        for parent in file_path.parents:
            if (parent / c.Infra.Files.PYPROJECT_FILENAME).exists() and (
                parent / c.Infra.Files.MAKEFILE_FILENAME
            ).exists():
                return parent.name
        return c.Infra.Defaults.UNKNOWN

    @staticmethod
    def build_impact_map(
        results: Sequence[m.Infra.Result],
    ) -> Sequence[Mapping[str, str]]:
        """Build normalized impact-map rows from refactor results."""
        impact_map: Sequence[Mapping[str, str]] = []
        symbol_pattern = re.compile(r"^(.*):\s+(.+)\s+->\s+(.+?)(?:\s+\(|$)")
        added_pattern = re.compile(r"^\[(.+)\]\s+Added keyword:\s+(.+)$")
        removed_pattern = re.compile(r"^\[(.+)\]\s+Removed keyword:\s+(.+)$")
        for result in results:
            if not result.success:
                impact_map.append({
                    c.Infra.Toml.PROJECT: FlextInfraUtilitiesRefactorCli.project_name_from_path(
                        result.file_path,
                    ),
                    c.Infra.ReportKeys.FILE: str(result.file_path),
                    "kind": "failure",
                    "old": "",
                    "new": "",
                    c.Infra.ReportKeys.STATUS: result.error or "failed",
                })
                continue
            if not result.changes:
                continue
            project_name = FlextInfraUtilitiesRefactorCli.project_name_from_path(
                result.file_path,
            )
            for change in result.changes:
                symbol_match = symbol_pattern.match(change)
                if symbol_match is not None:
                    _, old_symbol, new_symbol = symbol_match.groups()
                    impact_map.append({
                        c.Infra.Toml.PROJECT: project_name,
                        c.Infra.ReportKeys.FILE: str(result.file_path),
                        "kind": "rename",
                        "old": old_symbol.strip(),
                        "new": new_symbol.strip(),
                        c.Infra.ReportKeys.STATUS: "changed",
                    })
                    continue
                add_match = added_pattern.match(change)
                if add_match is not None:
                    migration_id, payload = add_match.groups()
                    impact_map.append({
                        c.Infra.Toml.PROJECT: project_name,
                        c.Infra.ReportKeys.FILE: str(result.file_path),
                        "kind": "signature_add",
                        "old": "",
                        "new": payload.strip(),
                        c.Infra.ReportKeys.STATUS: migration_id,
                    })
                    continue
                remove_match = removed_pattern.match(change)
                if remove_match is not None:
                    migration_id, payload = remove_match.groups()
                    impact_map.append({
                        c.Infra.Toml.PROJECT: project_name,
                        c.Infra.ReportKeys.FILE: str(result.file_path),
                        "kind": "signature_remove",
                        "old": payload.strip(),
                        "new": "",
                        c.Infra.ReportKeys.STATUS: migration_id,
                    })
        return impact_map

    @staticmethod
    def write_impact_map(
        results: Sequence[m.Infra.Result],
        output_path: Path,
    ) -> bool:
        """Persist impact-map JSON report to disk."""
        impact_map = FlextInfraUtilitiesRefactorCli.build_impact_map(results)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            payload = (
                orjson.dumps(impact_map, option=orjson.OPT_INDENT_2).decode() + "\n"
            )
            _ = output_path.write_text(payload, encoding=c.Infra.Encoding.DEFAULT)
            FlextInfraUtilitiesRefactorCli.refactor_info(
                f"Impact map written: {output_path}",
            )
            FlextInfraUtilitiesRefactorCli.refactor_info(
                f"Impact map entries: {len(impact_map)}",
            )
            return True
        except OSError:
            FlextInfraUtilitiesRefactorCli.refactor_error(
                f"Failed to write impact map {output_path}",
            )
            return False

    @staticmethod
    def print_diff(original: str, refactored: str, file_path: Path) -> None:
        """Print unified diff for one file."""
        FlextInfraUtilitiesRefactorCli.refactor_header(f"Diff for {file_path.name}")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            refactored.splitlines(keepends=True),
            fromfile=f"{file_path.name} (original)",
            tofile=f"{file_path.name} (refactored)",
            lineterm="",
        )
        diff_text = "".join(diff)
        if diff_text:
            FlextInfraUtilitiesRefactorCli.refactor_info(diff_text)
            return
        FlextInfraUtilitiesRefactorCli.refactor_info("No changes")

    @staticmethod
    def print_rules_table(rules: Sequence[Mapping[str, str | bool]]) -> None:
        """Print configured rule table for interactive CLI output."""
        FlextInfraUtilitiesRefactorCli.refactor_header("Available Rules")
        if not rules:
            FlextInfraUtilitiesRefactorCli.refactor_info("No rules loaded.")
            return
        id_width = (
            max(
                len(str(item.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN)))
                for item in rules
            )
            + 2
        )
        name_width = (
            max(
                len(str(item.get(c.Infra.Toml.NAME, c.Infra.Defaults.UNKNOWN)))
                for item in rules
            )
            + 2
        )
        header = (
            f"{'ID':<{id_width}} {'Name':<{name_width}} {'Severity':<10} {'Status'}"
        )
        FlextInfraUtilitiesRefactorCli.refactor_info(header)
        FlextInfraUtilitiesRefactorCli.refactor_info("-" * len(header))
        for rule in rules:
            status = "\u2713" if rule[c.Infra.ReportKeys.ENABLED] else "\u2717"
            rid = f"{rule['id']:<{id_width}}"
            rname = f"{rule['name']:<{name_width}}"
            rsev = f"{rule['severity']:<10}"
            FlextInfraUtilitiesRefactorCli.refactor_info(
                f"{rid} {rname} {rsev} {status}",
            )
            if rule["description"]:
                FlextInfraUtilitiesRefactorCli.refactor_info(
                    f"  - {rule['description']}",
                )

    @staticmethod
    def print_summary(results: Sequence[m.Infra.Result], *, dry_run: bool) -> None:
        """Print execution summary for processed files."""
        modified = sum(1 for item in results if item.modified)
        failed = sum(1 for item in results if not item.success)
        unchanged = sum(1 for item in results if item.success and (not item.modified))
        FlextInfraUtilitiesRefactorCli.refactor_header("Summary")
        FlextInfraUtilitiesRefactorCli.refactor_info(f"Total files: {len(results)}")
        FlextInfraUtilitiesRefactorCli.refactor_info(f"Modified: {modified}")
        FlextInfraUtilitiesRefactorCli.refactor_debug(f"Unchanged: {unchanged}")
        FlextInfraUtilitiesRefactorCli.refactor_info(f"Failed: {failed}")
        if dry_run:
            FlextInfraUtilitiesRefactorCli.refactor_info(
                "[DRY-RUN] No changes applied",
            )
        elif failed == 0:
            FlextInfraUtilitiesRefactorCli.refactor_info(
                "All changes applied successfully",
            )
        else:
            FlextInfraUtilitiesRefactorCli.refactor_info(f"{failed} files failed")

    @staticmethod
    def print_violation_summary(
        analysis: m.Infra.ViolationAnalysisReport,
    ) -> None:
        """Print violation aggregate totals and hotspot files."""
        FlextInfraUtilitiesRefactorCli.refactor_header("Violation Analysis")
        FlextInfraUtilitiesRefactorCli.refactor_info(
            f"Files scanned: {analysis.files_scanned}",
        )
        if not analysis.totals:
            FlextInfraUtilitiesRefactorCli.refactor_info(
                "No tracked violations found.",
            )
            return
        totals_ranked = sorted(
            analysis.totals.items(),
            key=itemgetter(1),
            reverse=True,
        )
        FlextInfraUtilitiesRefactorCli.refactor_info("Top pattern counts:")
        for name, count in totals_ranked:
            FlextInfraUtilitiesRefactorCli.refactor_info(f"  - {name}: {count}")
        if not analysis.top_files:
            return
        FlextInfraUtilitiesRefactorCli.refactor_info("Hottest files:")
        for entry in analysis.top_files[:10]:
            FlextInfraUtilitiesRefactorCli.refactor_info(
                f"  - {entry.file}: {entry.total}",
            )


__all__ = ["FlextInfraUtilitiesRefactorCli"]
