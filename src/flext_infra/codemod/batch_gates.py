"""Gate measurement and ast-grep batch execution for the mod safety circuit."""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from flext_infra.detectors.lsp_diagnostics import FlextInfraLspDiagnosticsDetector
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate


class FlextInfraModGateEngine:
    """Execute ast-grep rewrites and strict static/LSP validation."""

    @classmethod
    def validate_rule_fixtures(
        cls, root: Path, rules: t.SequenceOf[Path]
    ) -> p.Result[bool]:
        """Validate inherited fixtures and update only rule owners in scope."""
        governed_roots = frozenset(
            project.resolve() for project in u.Infra.governed_project_roots(root)
        )
        rules_by_owner: dict[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        if not rules_by_owner:
            return r.fail("discovered ast-grep rules have no fixture owner")
        for config_root, owner_rules in sorted(rules_by_owner.items()):
            owner_root = u.Infra.project_root(config_root)
            owner_is_governed = (
                owner_root is not None and owner_root.resolve() in governed_roots
            )
            active_rule_ids: set[str] = set()
            for rule in owner_rules:
                rule_ids, _fixable_ids = u.Infra.ast_grep_rule_contract(rule)
                active_rule_ids.update(rule_ids)
            if owner_is_governed:
                FlextInfraCodemodSnapshotReconciler.reconcile(
                    config_root, frozenset(active_rule_ids)
                )
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-fixtures-", dir=config_root.parent
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                shutil.copytree(config_root, temp_root)
                split_rules = cls._materialize_split_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                if owner_is_governed:
                    cls._run_tool(
                        temp_root, (c.Infra.SG, c.Infra.TEST, c.Infra.SG_UPDATE_ALL)
                    ).unwrap()
                cls._run_tool(temp_root, (c.Infra.SG, c.Infra.TEST)).unwrap()
                if owner_is_governed:
                    cls._sync_rule_fixture_root(
                        config_root=config_root,
                        temp_root=temp_root,
                        split_rules=split_rules,
                    )
        return r.ok(True)

    @staticmethod
    def _rule_documents(rule: Path) -> tuple[str, ...]:
        """Return every non-empty YAML document in one rule file."""
        documents = tuple(rule.read_text(encoding="utf-8").split("\n---"))
        return tuple(
            document.strip("\n")
            for document in documents
            if any(
                line.strip() and not line.lstrip().startswith("#")
                for line in document.splitlines()
            )
        )

    @classmethod
    def _materialize_split_rule_files(
        cls, *, config_root: Path, temp_root: Path, owner_rules: t.SequenceOf[Path]
    ) -> dict[Path, tuple[Path, ...]]:
        """Replace multi-document rule files with single-document temp copies."""
        split_rules: dict[Path, tuple[Path, ...]] = {}
        source_rules = set(owner_rules)
        config_path = config_root / c.Infra.CODEMOD_CONFIG_FILENAME
        config = u.Cli.yaml_safe_load(config_path).unwrap()
        for key in (c.Infra.CODEMOD_RULE_DIRS_KEY, c.Infra.CODEMOD_UTIL_DIRS_KEY):
            raw_directories = config.get(key)
            if not isinstance(raw_directories, Sequence) or isinstance(
                raw_directories, str
            ):
                msg = f"invalid ast-grep {key} contract: {config_path}"
                raise TypeError(msg)
            for raw_directory in raw_directories:
                if not isinstance(raw_directory, str) or not raw_directory.strip():
                    msg = f"invalid ast-grep {key} entry: {config_path}"
                    raise ValueError(msg)
                directory = Path(raw_directory)
                if directory.is_absolute() or ".." in directory.parts:
                    msg = f"ast-grep {key} escapes its owner: {raw_directory}"
                    raise ValueError(msg)
                source_rules.update(
                    (config_root / directory).rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")
                )
        for rule in sorted(source_rules):
            documents = cls._rule_documents(rule)
            if len(documents) <= 1:
                continue
            temp_rule = temp_root / rule.relative_to(config_root)
            temp_rule.unlink()
            split_paths: list[Path] = []
            for document in documents:
                parsed = u.Cli.yaml_parse(document)
                if parsed.failure:
                    raise RuntimeError(parsed.error or str(rule))
                rule_id = parsed.value.get("id")
                if not isinstance(rule_id, str) or not rule_id:
                    msg = f"ast-grep rule document missing required id: {rule}"
                    raise RuntimeError(msg)
                split_path = temp_rule.with_name(f"{rule_id}.yml")
                split_path.write_text(document, encoding="utf-8")
                split_paths.append(split_path)
            split_rules[rule] = tuple(split_paths)
        return split_rules

    @staticmethod
    def _sync_rule_fixture_root(
        *, config_root: Path, temp_root: Path, split_rules: dict[Path, tuple[Path, ...]]
    ) -> None:
        """Mirror validated fixture updates from the temp copy back to source."""
        split_temp_paths = {
            path.relative_to(temp_root)
            for paths in split_rules.values()
            for path in paths
        }
        for temp_path in temp_root.rglob("*"):
            if not temp_path.is_file():
                continue
            relative = temp_path.relative_to(temp_root)
            if relative in split_temp_paths:
                continue
            source_path = config_root / relative
            if source_path.is_file():
                if source_path.read_text(encoding="utf-8") == temp_path.read_text(
                    encoding="utf-8"
                ):
                    continue
            else:
                source_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_path, source_path)
        for source_rule, split_paths in split_rules.items():
            reconstructed = "\n---\n".join(
                split_path.read_text(encoding="utf-8").rstrip("\n")
                for split_path in split_paths
            )
            if reconstructed and not reconstructed.endswith("\n"):
                reconstructed += "\n"
            source_rule.write_text(reconstructed, encoding="utf-8")

    @staticmethod
    def _run_tool(
        root: Path,
        command: t.StrSequence,
        *,
        env: t.StrMapping | None = None,
        remove_env_keys: t.StrSequence = (),
        finding_exit_code: int | None = None,
        accept_source_apply_receipt: bool = False,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run one AST tool and preserve its documented finding status."""
        sys.stderr.write(
            f"mod: start {' '.join(command[:2])} arguments={max(0, len(command) - 2)}\n"
        )
        sys.stderr.flush()
        run = u.Cli.run_raw(
            command,
            cwd=root,
            timeout=c.Infra.TIMEOUT_SHORT,
            env=env,
            remove_env_keys=remove_env_keys,
        )
        if run.failure:
            return r[p.Cli.CommandOutput].from_failure(run)
        output = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={output.outcome.raw_return_code} "
            f"duration={output.duration:.2f}s\n"
        )
        sys.stderr.flush()
        if output.outcome.raw_return_code != 0:
            if (
                output.outcome.raw_return_code == finding_exit_code
                and output.stdout.strip()
            ):
                return r[p.Cli.CommandOutput].ok(output)
            detail = "\n".join(
                stream.strip()
                for stream in (output.stdout, output.stderr)
                if stream.strip()
            )
            return r[p.Cli.CommandOutput].fail(
                f"{command[0]} exited with code "
                f"{output.outcome.raw_return_code}: {detail}"
            )
        stderr = output.stderr.strip()
        if stderr:
            if (
                accept_source_apply_receipt
                and FlextInfraModGateEngine._is_apply_receipt(stderr)
            ):
                return r[p.Cli.CommandOutput].ok(output)
            return r[p.Cli.CommandOutput].fail(stderr)
        return r[p.Cli.CommandOutput].ok(output)

    @staticmethod
    def _is_apply_receipt(stderr: str) -> bool:
        """Recognize only ast-grep's successful source-apply receipt."""
        return re.fullmatch(r"Applied [0-9]+ changes", stderr.strip()) is not None

    @staticmethod
    def _path_depth(path: Path) -> int:
        """Return path depth for deterministic deepest-owner selection."""
        return len(path.parts)

    @staticmethod
    def _validate_finding_receipt(stderr: str, errors: int) -> p.Result[bool]:
        """Authenticate ast-grep's exact error-finding stderr receipt."""
        expected = "\n".join((
            c.Infra.AST_GREP_ERROR_FINDING_RECEIPT.format(count=errors),
            c.Infra.AST_GREP_ERROR_FINDING_HELP,
        ))
        if stderr.strip() != expected:
            return r[bool].fail(
                f"ast-grep finding receipt mismatch: parsed_errors={errors} "
                f"expected={expected!r} actual={stderr.strip()!r}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _parse_findings(
        stdout: str,
        root: Path,
        rule_files_by_id: Mapping[str, Path],
        fixable_ids: frozenset[str],
    ) -> p.Result[m.Infra.ModScanReport]:
        """Validate every JSONL finding without dropping malformed output."""
        findings = 0
        actionable_findings = 0
        detection_only_findings = 0
        non_actionable_with_fix_findings = 0
        files: set[Path] = set()
        entries: list[m.Infra.ModScanFinding] = []
        repository_roots = tuple(
            sorted(
                u.Infra.governed_project_roots(root),
                key=FlextInfraModGateEngine._path_depth,
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
            severity = finding.get("severity")
            if not isinstance(rule_id, str) or rule_id not in rule_files_by_id:
                return r.fail(f"invalid ast-grep finding contract: {line}")
            if not isinstance(text, str) or not isinstance(file, str):
                return r.fail(f"invalid ast-grep finding contract: {line}")
            if not isinstance(source_range, Mapping):
                return r.fail(f"invalid ast-grep finding contract: {line}")
            if raw_replacement is not None and not isinstance(raw_replacement, str):
                return r.fail(f"invalid ast-grep finding contract: {line}")
            if severity not in {"error", "warning", "info", "hint"}:
                return r.fail(f"invalid ast-grep finding severity: {line}")
            file_path = Path(file)
            files.add(file_path)
            replacement = raw_replacement if isinstance(raw_replacement, str) else None
            actionable = False
            if rule_id in fixable_ids:
                if not isinstance(replacement, str):
                    return r.fail(f"fixable ast-grep finding lacks replacement: {line}")
                actionable = text != replacement
                if actionable:
                    actionable_findings += 1
                    classification = c.Infra.ModScanFindingClass.ACTIONABLE
                else:
                    non_actionable_with_fix_findings += 1
                    classification = c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX
            else:
                if replacement is not None:
                    return r.fail(
                        f"detection-only ast-grep finding has replacement: {line}"
                    )
                detection_only_findings += 1
                classification = c.Infra.ModScanFindingClass.DETECTION_ONLY
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
                    rule_file=str(rule_files_by_id[rule_id].resolve()),
                    rule_id=rule_id,
                    repository=repository,
                    file=file_path,
                    range=t.Cli.JSON_MAPPING_ADAPTER.validate_python(source_range),
                    text=text,
                    replacement=replacement,
                    actionable=actionable,
                    classification=classification,
                    payload=t.Cli.JSON_MAPPING_ADAPTER.validate_python(finding),
                )
            )
            findings += 1
        return r.ok(
            m.Infra.ModScanReport(
                findings=findings,
                actionable=actionable_findings,
                detection_only=detection_only_findings,
                non_actionable_with_fix=non_actionable_with_fix_findings,
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
            f"detection_only={evidence.detection_only} "
            f"non_actionable_with_fix={evidence.non_actionable_with_fix}\n"
        )
        for finding_class, count in evidence.totals_by_class.items():
            sys.stderr.write(
                f"mod: findings class={finding_class.value} count={count}\n"
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
    def validate(cls, root: Path) -> p.Result[bool]:
        """Require full-scope canonical formatting, Ruff, Pyrefly, and LSP health."""
        resolved_root = root.resolve()
        project_roots = u.Infra.governed_project_roots(resolved_root)
        for index, owner in enumerate(project_roots, start=1):
            sys.stderr.write(
                f"mod: validate project {index}/{len(project_roots)} {owner}\n"
            )
            sys.stderr.flush()
            context = m.Infra.GateContext(
                workspace=owner,
                reports_dir=owner / c.Infra.REPORTS_DIR_NAME,
                check_only=True,
            )
            for gate_type in (
                FlextInfraRuffFormatGate,
                FlextInfraRuffLintGate,
                FlextInfraPyreflyGate,
            ):
                execution = gate_type(owner).check(owner, context)
                if not execution.result.passed:
                    return r.fail(
                        execution.raw_output or "\n".join(execution.result.errors)
                    )
            files = u.Infra.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(owner,))
            ).unwrap()
            FlextInfraLspDiagnosticsDetector.validate(owner, files).unwrap()
        return r[bool].ok(True)

    @classmethod
    def scan(cls, root: Path, *, fix: bool) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply every ruleset elected by the composed rule-plan SSOT."""
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return r[m.Infra.ModScanReport].from_failure(planned)
        plan = planned.value
        findings = 0
        actionable_findings = 0
        detection_only_findings = 0
        non_actionable_with_fix_findings = 0
        files: set[Path] = set()
        entries: list[m.Infra.ModScanFinding] = []
        rule_files_by_id = {rule.id: rule.resource for rule in plan.rules}
        targets = u.Infra.ast_grep_scan_targets(root)
        sys.stderr.write(
            f"mod: ast-grep {'apply' if fix else 'scan'} "
            f"providers={len(plan.rulesets)} rules={len(plan.rules)}\n"
        )
        sys.stderr.flush()
        for ruleset in plan.rulesets:
            ruleset_files = {
                rule_id: rule_files_by_id[rule_id] for rule_id in ruleset.rule_ids
            }
            scan_command = u.Infra.ast_grep_scan_command(
                ruleset.config,
                rule_ids=ruleset.rule_ids,
                targets=targets,
                json_stream=True,
            )
            run = cls._run_tool(root, scan_command, finding_exit_code=1)
            if run.failure:
                return r[m.Infra.ModScanReport].from_failure(run)
            report = cls._parse_findings(
                run.value.stdout,
                root,
                ruleset_files,
                frozenset(ruleset.fixable_rule_ids),
            ).unwrap()
            if run.value.outcome.raw_return_code != 0:
                error_findings = sum(
                    entry.payload.get("severity") == "error" for entry in report.entries
                )
                cls._validate_finding_receipt(run.value.stderr, error_findings).unwrap()
            findings += report.findings
            actionable_findings += report.actionable
            detection_only_findings += report.detection_only
            non_actionable_with_fix_findings += report.non_actionable_with_fix
            files.update(report.files)
            entries.extend(report.entries)
            if not (fix and report.actionable and ruleset.fixable_rule_ids):
                continue
            apply_command = u.Infra.ast_grep_scan_command(
                ruleset.config,
                rule_ids=ruleset.fixable_rule_ids,
                targets=targets,
                update_all=True,
            )
            apply_run = cls._run_tool(
                root, apply_command, accept_source_apply_receipt=True
            )
            if apply_run.failure:
                return r[m.Infra.ModScanReport].from_failure(apply_run)
        complete_report = m.Infra.ModScanReport(
            findings=findings,
            actionable=actionable_findings,
            detection_only=detection_only_findings,
            non_actionable_with_fix=non_actionable_with_fix_findings,
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
        return r[m.Infra.ModScanReport].ok(complete_report)


__all__: list[str] = ["FlextInfraModGateEngine"]
