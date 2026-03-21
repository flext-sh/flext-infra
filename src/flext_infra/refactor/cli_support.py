"""CLI support routines for refactor execution and reporting."""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import re
import sys
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

import orjson

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.refactor.analysis import FlextInfraRefactorViolationAnalyzer
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra.refactor.engine import FlextInfraRefactorEngine


class FlextInfraRefactorCliSupport:
    @staticmethod
    def info(message: str) -> None:
        """Write informational output to stdout."""
        _ = sys.stdout.write(f"{message}\n")

    @staticmethod
    def error(message: str) -> None:
        """Write error output to stderr."""
        _ = sys.stderr.write(f"ERROR: {message}\n")

    @staticmethod
    def header(message: str) -> None:
        """Write a section header to stdout."""
        _ = sys.stdout.write(f"\n{message}\n")

    @staticmethod
    def debug(message: str) -> None:
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
        results: list[m.Infra.Result],
    ) -> list[dict[str, str]]:
        """Build normalized impact-map rows from refactor results."""
        impact_map: list[dict[str, str]] = []
        symbol_pattern = re.compile(r"^(.*):\s+(.+)\s+->\s+(.+?)(?:\s+\(|$)")
        added_pattern = re.compile(r"^\[(.+)\]\s+Added keyword:\s+(.+)$")
        removed_pattern = re.compile(r"^\[(.+)\]\s+Removed keyword:\s+(.+)$")
        for result in results:
            if not result.success:
                impact_map.append({
                    c.Infra.Toml.PROJECT: FlextInfraRefactorCliSupport.project_name_from_path(
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
            project_name = FlextInfraRefactorCliSupport.project_name_from_path(
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
        results: list[m.Infra.Result],
        output_path: Path,
    ) -> bool:
        """Persist impact-map JSON report to disk."""
        impact_map = FlextInfraRefactorCliSupport.build_impact_map(results)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            payload = (
                orjson.dumps(impact_map, option=orjson.OPT_INDENT_2).decode() + "\n"
            )
            _ = output_path.write_text(payload, encoding=c.Infra.Encoding.DEFAULT)
            FlextInfraRefactorCliSupport.info(f"Impact map written: {output_path}")
            FlextInfraRefactorCliSupport.info(f"Impact map entries: {len(impact_map)}")
            return True
        except OSError:
            FlextInfraRefactorCliSupport.error(
                f"Failed to write impact map {output_path}",
            )
            return False

    @staticmethod
    def print_diff(original: str, refactored: str, file_path: Path) -> None:
        """Print unified diff for one file."""
        FlextInfraRefactorCliSupport.header(f"Diff for {file_path.name}")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            refactored.splitlines(keepends=True),
            fromfile=f"{file_path.name} (original)",
            tofile=f"{file_path.name} (refactored)",
            lineterm="",
        )
        diff_text = "".join(diff)
        if diff_text:
            FlextInfraRefactorCliSupport.info(diff_text)
            return
        FlextInfraRefactorCliSupport.info("No changes")

    @staticmethod
    def print_rules_table(rules: list[dict[str, str | bool]]) -> None:
        """Print configured rule table for interactive CLI output."""
        FlextInfraRefactorCliSupport.header("Available Rules")
        if not rules:
            FlextInfraRefactorCliSupport.info("No rules loaded.")
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
        FlextInfraRefactorCliSupport.info(header)
        FlextInfraRefactorCliSupport.info("-" * len(header))
        for rule in rules:
            status = "✓" if rule[c.Infra.ReportKeys.ENABLED] else "✗"
            rid = f"{rule['id']:<{id_width}}"
            rname = f"{rule['name']:<{name_width}}"
            rsev = f"{rule['severity']:<10}"
            FlextInfraRefactorCliSupport.info(f"{rid} {rname} {rsev} {status}")
            if rule["description"]:
                FlextInfraRefactorCliSupport.info(f"  - {rule['description']}")

    @staticmethod
    def print_summary(results: list[m.Infra.Result], *, dry_run: bool) -> None:
        """Print execution summary for processed files."""
        modified = sum(1 for item in results if item.modified)
        failed = sum(1 for item in results if not item.success)
        unchanged = sum(1 for item in results if item.success and (not item.modified))
        FlextInfraRefactorCliSupport.header("Summary")
        FlextInfraRefactorCliSupport.info(f"Total files: {len(results)}")
        FlextInfraRefactorCliSupport.info(f"Modified: {modified}")
        FlextInfraRefactorCliSupport.debug(f"Unchanged: {unchanged}")
        FlextInfraRefactorCliSupport.info(f"Failed: {failed}")
        if dry_run:
            FlextInfraRefactorCliSupport.info("[DRY-RUN] No changes applied")
        elif failed == 0:
            FlextInfraRefactorCliSupport.info("All changes applied successfully")
        else:
            FlextInfraRefactorCliSupport.info(f"{failed} files failed")

    @staticmethod
    def print_violation_summary(
        analysis: m.Infra.ViolationAnalysisReport,
    ) -> None:
        """Print violation aggregate totals and hotspot files."""
        FlextInfraRefactorCliSupport.header("Violation Analysis")
        FlextInfraRefactorCliSupport.info(f"Files scanned: {analysis.files_scanned}")
        if not analysis.totals:
            FlextInfraRefactorCliSupport.info("No tracked violations found.")
            return
        totals_ranked = sorted(analysis.totals.items(), key=itemgetter(1), reverse=True)
        FlextInfraRefactorCliSupport.info("Top pattern counts:")
        for name, count in totals_ranked:
            FlextInfraRefactorCliSupport.info(f"  - {name}: {count}")
        if not analysis.top_files:
            return
        FlextInfraRefactorCliSupport.info("Hottest files:")
        for entry in analysis.top_files[:10]:
            FlextInfraRefactorCliSupport.info(f"  - {entry.file}: {entry.total}")

    @staticmethod
    def run_cli(engine_cls: type[FlextInfraRefactorEngine]) -> int:
        """Execute refactor CLI entry flow and return process exit code."""
        parser = argparse.ArgumentParser(
            description="Flext Refactor Engine - Declarative code transformation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        mode_group = parser.add_mutually_exclusive_group(required=True)
        _ = mode_group.add_argument("--project", "-p", type=Path)
        _ = mode_group.add_argument("--workspace", "-w", type=Path)
        _ = mode_group.add_argument("--file", "-f", type=Path)
        _ = mode_group.add_argument("--files", nargs="+", type=Path)
        _ = mode_group.add_argument("--list-rules", "-l", action="store_true")
        _ = parser.add_argument("--rules", "-r", type=str)
        _ = parser.add_argument("--pattern", default=c.Infra.Extensions.PYTHON_GLOB)
        _ = parser.add_argument("--dry-run", "-n", action="store_true")
        _ = parser.add_argument("--show-diff", "-d", action="store_true")
        _ = parser.add_argument("--impact-map-output", type=Path)
        _ = parser.add_argument("--analyze-violations", action="store_true")
        _ = parser.add_argument("--analysis-output", type=Path)
        _ = parser.add_argument("--config", "-c", type=Path)
        args = parser.parse_args()
        engine = engine_cls(config_path=args.config)
        config_result = engine.load_config()
        if not config_result.is_success:
            FlextInfraRefactorCliSupport.error(f"Config error: {config_result.error}")
            return 1
        if args.rules:
            rule_filters = [
                item.strip() for item in args.rules.split(",") if item.strip()
            ]
            engine.set_rule_filters(rule_filters)
        rules_result = engine.load_rules()
        if not rules_result.is_success:
            FlextInfraRefactorCliSupport.error(f"Rules error: {rules_result.error}")
            return 1
        if args.list_rules:
            FlextInfraRefactorCliSupport.print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            files_to_analyze: list[Path] = []
            if args.project:
                scan_dirs = frozenset(
                    engine.rule_loader.extract_project_scan_dirs(engine.config),
                )
                iter_result = u.Infra.iter_python_files(
                    workspace_root=args.project,
                    project_roots=[args.project],
                    include_tests=c.Infra.Directories.TESTS in scan_dirs,
                    include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                    include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                    src_dirs=scan_dirs or None,
                )
                if iter_result.is_failure:
                    FlextInfraRefactorCliSupport.error(
                        iter_result.error
                        or f"File iteration failed for project: {args.project}",
                    )
                    return 1
                ignore_items, extension_items = (
                    engine.rule_loader.extract_engine_file_filters(
                        engine.config,
                    )
                )
                ignore_patterns = {str(item) for item in ignore_items}
                allowed_extensions = {str(item) for item in extension_items}
                files_to_analyze = [
                    file_path
                    for file_path in iter_result.value
                    if (
                        fnmatch.fnmatch(
                            str(file_path.relative_to(args.project)),
                            args.pattern,
                        )
                        or fnmatch.fnmatch(file_path.name, args.pattern)
                    )
                    and (
                        not allowed_extensions or file_path.suffix in allowed_extensions
                    )
                    and file_path.name not in ignore_patterns
                    and not any(
                        part in ignore_patterns
                        for part in file_path.relative_to(args.project).parts
                    )
                    and not any(
                        fnmatch.fnmatch(
                            str(file_path.relative_to(args.project)),
                            ignore_pattern,
                        )
                        for ignore_pattern in ignore_patterns
                    )
                ]
            elif args.workspace:
                files_to_analyze = engine.collect_workspace_files(
                    args.workspace,
                    pattern=args.pattern,
                )
            elif args.file:
                if not args.file.exists():
                    FlextInfraRefactorCliSupport.error(f"File not found: {args.file}")
                    return 1
                files_to_analyze = [args.file]
            elif args.files:
                files_to_analyze = [item for item in args.files if item.exists()]
            analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(
                files_to_analyze,
            )
            FlextInfraRefactorCliSupport.print_violation_summary(analysis)
            if args.analysis_output is not None:
                _ = u.Infra.write_json(
                    args.analysis_output,
                    analysis.model_dump(mode="json"),
                    ensure_ascii=True,
                )
                FlextInfraRefactorCliSupport.info(
                    f"Analysis report written: {args.analysis_output}",
                )
            return 0
        results: list[m.Infra.Result] = []
        if args.project:
            results = engine.refactor_project(
                args.project,
                dry_run=args.dry_run,
                pattern=args.pattern,
            )
        elif args.workspace:
            results = engine.refactor_workspace(
                args.workspace,
                dry_run=args.dry_run,
                pattern=args.pattern,
            )
        elif args.file:
            if not args.file.exists():
                FlextInfraRefactorCliSupport.error(f"File not found: {args.file}")
                return 1
            original_code = args.file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            result_single = engine.refactor_file(args.file, dry_run=args.dry_run)
            results = [result_single]
            if args.show_diff and result_single.modified:
                refactored_code = result_single.refactored_code or original_code
                FlextInfraRefactorCliSupport.print_diff(
                    original_code,
                    refactored_code,
                    args.file,
                )
        elif args.files:
            existing_files = [item for item in args.files if item.exists()]
            missing_files = [item for item in args.files if not item.exists()]
            for file_path in missing_files:
                FlextInfraRefactorCliSupport.error(f"File not found: {file_path}")
            results = engine.refactor_files(existing_files, dry_run=args.dry_run)
        FlextInfraRefactorCliSupport.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = FlextInfraRefactorCliSupport.write_impact_map(
                results,
                args.impact_map_output,
            )
        failed = sum(1 for item in results if not item.success)
        return 0 if failed == 0 else 1


__all__ = ["FlextInfraRefactorCliSupport"]
