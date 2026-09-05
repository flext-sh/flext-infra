"""Gate measurement and ast-grep batch execution for the mod safety circuit."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from flext_infra.detectors.lsp_diagnostics import FlextInfraLspDiagnosticsDetector


class FlextInfraModGateEngine:
    """Execute ast-grep rewrites and strict static/LSP validation."""

    @classmethod
    def validate_rule_fixtures(cls, rules: t.SequenceOf[Path]) -> p.Result[bool]:
        """Require fixtures at every installed rule owner's config root."""
        rules_by_owner: dict[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        if not rules_by_owner:
            return r.fail("discovered ast-grep rules have no fixture owner")
        for config_root, owner_rules in sorted(rules_by_owner.items()):
            active_rule_ids: set[str] = set()
            for rule in owner_rules:
                rule_ids, _fixable_ids = cls._rule_ids(rule).unwrap()
                active_rule_ids.update(rule_ids)
            FlextInfraCodemodSnapshotReconciler.reconcile(
                config_root, frozenset(active_rule_ids)
            )
            cls._run_tool(
                config_root, (c.Infra.SG, c.Infra.TEST, c.Infra.SG_UPDATE_ALL)
            ).unwrap()
            cls._run_tool(config_root, (c.Infra.SG, c.Infra.TEST)).unwrap()
        return r.ok(True)

    @staticmethod
    def _run_tool(
        root: Path,
        command: t.StrSequence,
        *,
        env: t.StrMapping | None = None,
        remove_env_keys: t.StrSequence = (),
        finding_exit_code: int | None = None,
        accept_apply_receipt: bool = False,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run one AST tool and preserve its documented finding status."""
        sys.stderr.write(f"mod: start {' '.join(command)}\n")
        sys.stderr.flush()
        run = u.Cli.run_raw(
            command,
            cwd=root,
            timeout=c.Infra.TIMEOUT_SHORT,
            env=env,
            remove_env_keys=remove_env_keys,
        )
        if run.failure:
            return r[p.Cli.CommandOutput].fail(
                run.error or f"tool execution failed: {command[0]}"
            )
        output = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={output.exit_code} "
            f"duration={output.duration:.2f}s\n"
        )
        sys.stderr.flush()
        if output.exit_code != 0:
            if output.exit_code == finding_exit_code and output.stdout.strip():
                return r[p.Cli.CommandOutput].ok(output)
            detail = "\n".join(
                stream.strip()
                for stream in (output.stdout, output.stderr)
                if stream.strip()
            )
            return r[p.Cli.CommandOutput].fail(
                f"{command[0]} exited with code {output.exit_code}: {detail}"
            )
        stderr = output.stderr.strip()
        if stderr:
            if accept_apply_receipt and FlextInfraModGateEngine._is_apply_receipt(
                stderr
            ):
                return r[p.Cli.CommandOutput].ok(output)
            diagnostics = tuple(
                line for line in stderr.splitlines() if not line.startswith("INFO:")
            )
            if diagnostics:
                return r[p.Cli.CommandOutput].fail(stderr)
            sys.stderr.write(f"{stderr}\n")
            sys.stderr.flush()
        return r[p.Cli.CommandOutput].ok(output)

    @staticmethod
    def _is_apply_receipt(stderr: str) -> bool:
        """Recognize only ast-grep's successful update receipt."""
        words = stderr.split()
        return (
            len(words) == 3
            and words[0] == "Applied"
            and words[1].isdigit()
            and words[2] == "changes"
        )

    @staticmethod
    def _validate_finding_receipt(stderr: str, findings: int) -> p.Result[bool]:
        """Authenticate ast-grep's exact error-finding stderr receipt."""
        expected = "\n".join((
            c.Infra.AST_GREP_ERROR_FINDING_RECEIPT.format(count=findings),
            c.Infra.AST_GREP_ERROR_FINDING_HELP,
        ))
        if stderr.strip() != expected:
            return r[bool].fail(stderr)
        return r[bool].ok(True)

    @staticmethod
    def _rule_ids(rule: Path) -> p.Result[tuple[frozenset[str], frozenset[str]]]:
        """Parse every document and return all IDs plus the fixable subset."""
        documents = rule.read_text(encoding="utf-8").split("\n---")
        rule_ids: set[str] = set()
        fixable_ids: set[str] = set()
        for raw_document in documents:
            if not any(
                line.strip() and not line.lstrip().startswith("#")
                for line in raw_document.splitlines()
            ):
                continue
            parsed = u.Cli.yaml_parse(raw_document)
            if parsed.failure:
                return r[frozenset[str]].fail(
                    parsed.error or f"invalid ast-grep rule document in {rule}"
                )
            rule_id = parsed.value.get("id")
            if not isinstance(rule_id, str) or not rule_id:
                return r.fail(f"ast-grep rule document missing required id: {rule}")
            if rule_id in rule_ids:
                return r.fail(f"duplicate ast-grep rule id {rule_id!r}: {rule}")
            rule_ids.add(rule_id)
            if "fix" in parsed.value:
                fixable_ids.add(rule_id)
        return r.ok((frozenset(rule_ids), frozenset(fixable_ids)))

    @staticmethod
    def _parse_findings(
        stdout: str,
        root: Path,
        rule_file: Path,
        rule_ids: frozenset[str],
        fixable_ids: frozenset[str],
    ) -> p.Result[m.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output."""
        findings = 0
        nodes = 0
        files: set[Path] = set()
        entries: list[m.Infra.ModScanFinding] = []
        repository_roots = tuple(
            sorted(
                u.Infra.governed_project_roots(root),
                key=lambda candidate: len(candidate.parts),
                reverse=True,
            )
        )
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parsed = u.Cli.json_parse(line)
            if parsed.failure:
                return r.from_failure(parsed)
            if not isinstance(parsed.value, Mapping):
                return r.fail(f"ast-grep JSONL finding is not an object: {line}")
            finding = parsed.value
            rule_id = finding.get("ruleId")
            text = finding.get("text")
            file = finding.get("file")
            source_range = finding.get("range")
            raw_replacement = finding.get("replacement")
            if (
                not isinstance(rule_id, str)
                or rule_id not in rule_ids
                or not isinstance(text, str)
                or not isinstance(file, str)
                or not isinstance(source_range, Mapping)
                or (
                    raw_replacement is not None and not isinstance(raw_replacement, str)
                )
            ):
                return r.fail(f"invalid ast-grep finding contract: {line}")
            file_path = Path(file)
            files.add(file_path)
            replacement = raw_replacement if isinstance(raw_replacement, str) else None
            actionable = False
            if rule_id in fixable_ids:
                if not isinstance(replacement, str):
                    return r.fail(f"fixable ast-grep finding lacks replacement: {line}")
                actionable = text != replacement
                if actionable:
                    nodes += 1
            resolved_file = (root / file_path).resolve()
            repository = next(
                (
                    candidate.name
                    for candidate in repository_roots
                    if resolved_file.is_relative_to(candidate)
                ),
                root.resolve().name,
            )
            entries.append(
                m.Infra.ModScanFinding(
                    rule_file=str(rule_file.resolve()),
                    rule_id=rule_id,
                    repository=repository,
                    file=file_path,
                    range=t.Cli.JSON_MAPPING_ADAPTER.validate_python(source_range),
                    text=text,
                    replacement=replacement,
                    actionable=actionable,
                    payload=t.Cli.JSON_MAPPING_ADAPTER.validate_python(finding),
                )
            )
            findings += 1
        return r.ok(
            m.Infra.ModScanReport(
                findings=findings,
                nodes=nodes,
                files=frozenset(files),
                entries=tuple(entries),
            )
        )

    @staticmethod
    def _report_evidence(receipt: m.Infra.ModScanEvidenceReceipt) -> None:
        """Print bounded totals and the authenticated full-evidence identity."""
        evidence = receipt.evidence
        sys.stderr.write(
            "mod: findings "
            f"total={evidence.findings} actionable={evidence.actionable} "
            f"detection_only={evidence.detection_only}\n"
        )
        for repository, count in evidence.totals_by_repository.items():
            sys.stderr.write(f"mod: findings repository={repository} count={count}\n")
        for rule_id, count in evidence.totals_by_rule.items():
            sys.stderr.write(f"mod: findings rule={rule_id} count={count}\n")
        sys.stderr.write(
            f"mod: findings report={receipt.path} sha256={receipt.sha256}\n"
        )
        sys.stderr.flush()

    @classmethod
    def validate(cls, root: Path, changed_files: t.SequenceOf[Path]) -> p.Result[bool]:
        """Require zero Ruff, Pyrefly, LSP, and graph-analysis diagnostics."""
        resolved_root = root.resolve()
        project_roots = u.Infra.governed_project_roots(resolved_root)
        repository_changes = tuple(
            changed_path
            for project_root in project_roots
            for changed_path in u.Infra.git_changed_paths(
                m.Infra.GitRepoRequest(repo_root=project_root)
            ).unwrap()
        )
        python_files = tuple(
            sorted({
                resolved
                for path in (*changed_files, *repository_changes)
                if (
                    resolved := (
                        path if path.is_absolute() else resolved_root / path
                    ).resolve()
                ).is_file()
                and resolved.suffix == c.Infra.EXT_PYTHON
            })
        )
        deepest_first = tuple(
            sorted(project_roots, key=lambda owner: len(owner.parts), reverse=True)
        )
        files_by_root: dict[Path, list[Path]] = {owner: [] for owner in project_roots}
        for python_file in python_files:
            owner = next(
                candidate
                for candidate in deepest_first
                if python_file.is_relative_to(candidate)
            )
            files_by_root[owner].append(python_file)
        selected_groups = tuple(
            (owner, tuple(files)) for owner, files in files_by_root.items() if files
        )
        snapshots: dict[Path, t.Infra.LintSnapshot] = {}
        for index, (owner, files) in enumerate(selected_groups, start=1):
            sys.stderr.write(
                f"mod: validate project {index}/{len(selected_groups)} "
                f"{owner} files={len(files)}\n"
            )
            sys.stderr.flush()
            snapshots.update(
                u.Infra.lint_snapshots(
                    files, owner, gates=(c.Infra.RUFF, c.Infra.PYREFLY)
                )
            )
        diagnostics = tuple(
            f"{path.relative_to(resolved_root)}:{tool}: {message}"
            for path, snapshot in snapshots.items()
            for tool, messages in snapshot.items()
            for message in messages
        )
        if diagnostics:
            return r.fail("\n".join(diagnostics))
        for owner, files in selected_groups:
            FlextInfraLspDiagnosticsDetector.validate(owner, files).unwrap()
        return r[bool].ok(True)

    @classmethod
    def scan(
        cls, root: Path, rules: t.SequenceOf[Path], *, fix: bool
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply actionable rewrite documents."""
        findings = 0
        nodes = 0
        files: set[Path] = set()
        entries: list[m.Infra.ModScanFinding] = []
        known_rule_ids: set[str] = set()
        targets = u.Infra.ast_grep_scan_targets(root)
        total = len(rules)
        for index, rule in enumerate(rules, start=1):
            rule_contract = cls._rule_ids(rule).unwrap()
            rule_ids, fixable_ids = rule_contract
            duplicate_ids = known_rule_ids.intersection(rule_ids)
            if duplicate_ids:
                duplicates = ", ".join(sorted(duplicate_ids))
                return r.fail(f"duplicate inherited ast-grep rule id(s): {duplicates}")
            known_rule_ids.update(rule_ids)
            sys.stderr.write(
                f"mod: rule {index}/{total} {rule.name} {'apply' if fix else 'scan'}\n"
            )
            sys.stderr.flush()
            scan_command = u.Infra.ast_grep_scan_command(
                rule, targets=targets, json_stream=True
            )
            run = cls._run_tool(root, scan_command, finding_exit_code=1)
            if run.failure:
                return r[m.Infra.ModScanReport].from_failure(run)
            report = cls._parse_findings(
                run.value.stdout, root, rule, rule_ids, fixable_ids
            ).unwrap()
            if run.value.exit_code != 0:
                cls._validate_finding_receipt(
                    run.value.stderr, report.findings
                ).unwrap()
            findings += report.findings
            nodes += report.nodes
            files.update(report.files)
            entries.extend(report.entries)
            if fix and report.nodes:
                apply_command = u.Infra.ast_grep_scan_command(
                    rule, targets=targets, update_all=True
                )
                apply_run = cls._run_tool(
                    root, apply_command, accept_apply_receipt=True
                )
                if apply_run.failure:
                    return r[m.Infra.ModScanReport].from_failure(apply_run)
        complete_report = m.Infra.ModScanReport(
            findings=findings,
            nodes=nodes,
            files=frozenset(files),
            entries=tuple(entries),
        )
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            complete_report,
            command=(
                c.Infra.ModScanCommand.APPLY if fix else c.Infra.ModScanCommand.SCAN
            ),
            scope=targets,
        )
        if receipt.failure:
            return r[m.Infra.ModScanReport].from_failure(receipt)
        cls._report_evidence(receipt.value)
        if fix and findings > nodes:
            return r.fail(
                "detection-only findings require fix-forward after all automated "
                f"rewrites: report={receipt.value.path} sha256={receipt.value.sha256}"
            )
        return r[m.Infra.ModScanReport].ok(complete_report)


__all__: list[str] = ["FlextInfraModGateEngine"]
