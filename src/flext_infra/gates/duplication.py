"""Fail-closed jscpd duplicate-code detector (R2 consumer+family scope).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, config, m, r, t, u
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from flext_infra.gates import FlextInfraGate
from flext_infra.gates.duplication_evidence import FlextInfraDuplicationEvidence
from flext_infra.gates.duplication_report import FlextInfraDuplicationReportMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDuplicationGate(FlextInfraDuplicationReportMixin, FlextInfraGate):
    """Report every clone owned by one project from a fresh scan of that project.

    R2 extension: consumer+family scope via [tool.flext.project] config keys;
    thresholds in config SSOT. Structural ban forms only for mechanisms with
    a published canonical owner (derived from primitives set) — never per-site lists.
    """

    gate_id: ClassVar[str] = "duplication"
    gate_name: ClassVar[str] = "Code Duplication"
    can_fix: ClassVar[bool] = False
    scanner_binary: ClassVar[str] = c.Infra.JSCPD_BINARY
    check_timeout: ClassVar[int] = c.Infra.TIMEOUT_LONG

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run and validate jscpd, then expose every owned clone as an error.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        overrides = self._read_project_config(project_dir)
        scan = self._scan_project(
            project_dir,
            ctx,
            fleet_enabled=overrides.success and overrides.value.fleet,
        )
        if (
            scan.outcome.timed_out
            or scan.outcome.forwarded_signal is not None
            or scan.outcome.raw_return_code < 0
        ):
            return self._parsed_gate_execution(project_dir, ctx, scan, started)
        report, issues, tool_failed = self._report_issues(scan, project_dir)
        not_executed = (
            "jscpd semantic pass NOT EXECUTED: the CI context has no embeddings host"
            if self.semantic_not_executed()
            else ""
        )
        evidence = self._publish_raw_receipt(
            ctx,
            "\n".join(
                part for part in (scan.stdout, scan.stderr, not_executed) if part
            ),
        )
        if report is not None and overrides.success:
            issues = (
                *issues,
                *self._assessment_issues(
                    (report, overrides.value),
                    project_dir,
                    evidence,
                    (
                        f"return_code={scan.outcome.raw_return_code}; "
                        f"timed_out={scan.outcome.timed_out}; "
                        f"signal={scan.outcome.forwarded_signal}; {not_executed}"
                    ),
                ),
            )
        outcome = (
            c.Infra.ToolOutcome.ERROR
            if tool_failed
            or any(issue.code == c.Infra.ToolOutcome.ERROR for issue in issues)
            else u.Infra.tool_outcome(
                scan.outcome,
                findings=len(issues),
                findings_exit_codes=(1,),
            )
        )
        return self._gate_execution_from(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=not issues,
                outcome=outcome,
                issues=tuple(issues),
                raw_output=evidence.raw_output,
                started=started,
            ),
            evidence,
        ).model_copy(
            update={
                "process": m.Cli.ProcessOutcome.model_validate(
                    scan.outcome, from_attributes=True
                ),
            }
        )

    def _report_issues(
        self,
        scan: p.Cli.CommandOutput,
        project_dir: Path,
    ) -> t.Triple[m.Infra.JscpdReport | None, t.VariadicTuple[m.Infra.Issue], bool]:
        """Parse the native report into owned clones plus any tool failure.

        A non-findings exit, or a findings exit whose report holds no clone,
        is a tool failure reported beside the parsed clones.

        Returns:
            The parsed report, its issues, and whether the tool itself failed.

        """
        report: m.Infra.JscpdReport | None = None
        try:
            if scan.stdout.strip():
                report = FlextInfraDuplicationEvidence.parse(scan.stdout)
            parsed = self._issues_from_report(project_dir, report)
        except ValueError as exc:
            parsed = r[tuple[m.Infra.Issue, ...]].fail(str(exc), exception=exc)
        issues: t.VariadicTuple[m.Infra.Issue] = (
            parsed.value if parsed.success else (self._failure_issue(parsed.error),)
        )
        empty_failure = (
            scan.outcome.raw_return_code == 1
            and report is not None
            and report.statistics.total.clones == 0
        )
        tool_failed = scan.outcome.raw_return_code not in {0, 1} or empty_failure
        if tool_failed:
            issues = (*issues, self._tool_failure_issue(scan))
        return report, issues, tool_failed

    def _assessment_issues(
        self,
        assessed: t.Pair[m.Infra.JscpdReport, m.Infra.ProjectDuplicationOverrides],
        project_dir: Path,
        evidence: m.Infra.GateOutputReceipt,
        execution: str,
    ) -> t.VariadicTuple[m.Infra.Issue]:
        """Publish the duplication assessment beside its receipt.

        Returns:
            The assessment's own failures; none when it is clean.

        """
        report, overrides = assessed
        try:
            assessment = FlextInfraDuplicationEvidence().assess(
                report,
                project_dir,
                overrides,
                raw_receipt=evidence.raw_output,
                execution=execution,
            )
        except (OSError, ValueError) as exc:
            return (self._failure_issue(f"duplication assessment: {exc}"),)
        u.Cli.atomic_write_text_file(
            evidence.path.with_suffix(".assessment.json"),
            assessment.model_dump_json(indent=2),
        ).unwrap()
        if assessment.counts.get("analysis_error", 0):
            return (
                self._failure_issue(
                    "duplication assessment contains source analysis errors; "
                    "see assessment receipt",
                ),
            )
        return ()

    def _scan_project(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        *,
        fleet_enabled: bool = False,
    ) -> p.Cli.CommandOutput:
        """Create one fresh report; tool, scope, and report failures escape.

        Returns:
            The resulting ``p.Cli.CommandOutput``.

        Raises:
            ValueError: If jscpd report target is not a physical file.

        """
        binary = self.resolve_binary()
        if binary is None:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=(
                    f"{c.Infra.JSCPD_BINARY} not found on PATH; `make setup` "
                    "provisions it from codegen.toolchain.tools entry 'jscpd'"
                ),
                # jscpd itself exits 1 when it finds clones, so an absent binary
                # must not borrow that code or the gate would read it as a scan.
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=c.Infra.PROCESS_COMMAND_NOT_FOUND_EXIT_CODE,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            )
        scope = (
            self._render_fleet_scope_dirs(project_dir)
            if fleet_enabled
            else self._render_scope_dirs(project_dir)
        )
        if scope.failure:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=scope.error or "project scope resolution failed",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=1,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            )
        if not scope.value:
            return m.Cli.CommandOutput(
                stdout="",
                stderr="jscpd scope resolved no source or test directories",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=1,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            )
        rendered_config = self._render_config(project_dir)
        if rendered_config.failure:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=rendered_config.error or "project duplication config invalid",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=1,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            )
        config_path = rendered_config.value
        report_dir = self._repository_root / c.Infra.JSCPD_REPORT_DIRNAME
        report_path = report_dir / c.Infra.JSCPD_REPORT_FILENAME
        if report_path.is_symlink() or (
            report_path.exists() and not report_path.is_file()
        ):
            msg = f"jscpd report target is not a physical file: {report_path}"
            raise ValueError(msg)
        if report_path.is_file():
            report_path.unlink()
        cmd = (
            binary,
            "--config",
            str(config_path),
            "--reporters",
            "json",
            "--output",
            str(report_dir),
            *scope.value,
        )
        result = self._run(
            cmd,
            self._repository_root,
            ctx,
        )
        return self._load_report(report_dir, result)

    def _render_scope_dirs(self, project_dir: Path) -> p.Result[t.StrSequence]:
        """The invoking project's canonical scope plus its declared extra trees.

        Every repository evaluates only itself, locally exactly as in CI: the
        scan covers this project's check directories, the governed manifest's
        ``repository.duplication_trees`` (e.g. Helm charts) and the
        ``[tool.flext.project]`` scope keys that exist on disk. Other projects
        are libraries, never scanned from here.

        Each resolved directory appears exactly once. The check directories
        (``source_scan.roots``) and the declared scope keys overlap, so the
        union must be de-duplicated: handing jscpd the same directory twice
        makes it clone every file against itself, which is the double-scan
        artifact (a false 50%-duplication report), never real duplication.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        project_config = self._read_project_config(project_dir)
        if project_config.failure:
            return r[t.StrSequence].from_failure(project_config)
        scope_dirnames = project_config.value.scope
        declared_trees = self._declared_duplication_trees()
        if declared_trees.failure:
            return r[t.StrSequence].from_failure(declared_trees)
        candidates: t.MutableSequenceOf[str] = []
        seen: set[str] = set()
        for candidate in (
            *self._existing_check_dirs(project_dir),
            *(tree for tree in declared_trees.value if (project_dir / tree).is_dir()),
            *(
                dirname
                for dirname in scope_dirnames
                if (project_dir / dirname).is_dir()
            ),
        ):
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
        return r[t.StrSequence].ok(
            tuple(str(project_dir / candidate) for candidate in candidates),
        )

    def _render_fleet_scope_dirs(self, project_dir: Path) -> p.Result[t.StrSequence]:
        """Union this project's scope with every declared member's scope.

        The cross-project view scans every member this workspace declares (the
        canonical member enumerator, derived from the workspace composition —
        never a hand-listed set) in ONE jscpd run, so a clone shared between two
        projects is reported instead of hidden behind per-project scoping.
        Ownership stays path containment under the invoking project, which is
        the governed workspace root.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        base = self._render_scope_dirs(project_dir)
        if base.failure:
            return r[t.StrSequence].from_failure(base)
        candidates: t.MutableSequenceOf[str] = list(base.value)
        seen: set[str] = set(candidates)
        for member in u.Infra.discover_project_roots(project_dir):
            if member == project_dir:
                continue
            member_scope = self._render_scope_dirs(member)
            if member_scope.failure:
                return r[t.StrSequence].from_failure(member_scope)
            for candidate in member_scope.value:
                if candidate in seen:
                    continue
                seen.add(candidate)
                candidates.append(candidate)
        return r[t.StrSequence].ok(tuple(candidates))

    @staticmethod
    def _read_project_config(
        project_dir: Path,
    ) -> p.Result[m.Infra.ProjectDuplicationOverrides]:
        """Read ``[tool.flext.project.duplication]`` from pyproject.toml.

        Why: a malformed manifest is a declared error, never an empty config —
        silently returning the default model for a broken manifest would
        disable the operator's overrides without a trace (silent-failure law).
        An absent manifest or absent ``duplication`` table is not malformed;
        it legitimately yields the default overrides.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectDuplicationOverrides]``.

        """
        pyproject_path = project_dir / c.PYPROJECT_FILENAME
        if not pyproject_path.is_file():
            return r[m.Infra.ProjectDuplicationOverrides].ok(
                m.Infra.ProjectDuplicationOverrides(),
            )
        loaded = u.Cli.config_load(pyproject_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.ProjectDuplicationOverrides].fail(
                f"invalid project manifest ({pyproject_path}): {loaded.error}",
            )
        tool = u.Cli.json_as_mapping(loaded.value.data).get("tool", {})
        flext = u.Cli.json_as_mapping(tool).get("flext", {})
        project = u.Cli.json_as_mapping(flext).get("project", {})
        duplication = u.Cli.json_as_mapping(project).get("duplication", {})
        validated: p.Result[m.Infra.ProjectDuplicationOverrides] = u.validate_value(
            m.Infra.ProjectDuplicationOverrides,
            u.Cli.json_as_mapping(duplication),
        )
        if validated.failure:
            return r[m.Infra.ProjectDuplicationOverrides].fail_op(
                f"[tool.flext.project.duplication] validation ({pyproject_path})",
                validated.error,
            )
        return r[m.Infra.ProjectDuplicationOverrides].ok(validated.value)

    def _declared_duplication_trees(self) -> p.Result[t.StrSequence]:
        """Read duplication scope from the target's selected repository delta.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        loaded = u.Infra.load_codegen_inputs(self._repository_root)
        if loaded.failure:
            return r[t.StrSequence].from_failure(loaded)
        repository = loaded.value.spec.repository
        return r[t.StrSequence].ok(repository.duplication_trees)

    def _render_config(self, project_dir: Path) -> p.Result[Path]:
        """Materialize the jscpd config from this gate's typed SSOT.

        R2: Reads thresholds from [tool.flext.project] config SSOT.
        A generated-at-scan-time projection, never a second hand-edited
        source; regenerating with unchanged constants produces byte-identical
        content (idempotent).

        Returns:
            The resulting ``p.Result[Path]``.

        """
        project_config = self._read_project_config(project_dir)
        if project_config.failure:
            return r[Path].from_failure(project_config)
        overrides = project_config.value
        passes = config.Infra.tooling.tools.jscpd
        jscpd_config = m.Infra.JscpdConfig(
            absolute=True,
            formatsExts={
                name: tuple(extensions)
                for name, extensions in c.Infra.JSCPD_FORMAT_EXTENSIONS.items()
            },
            ignore=self._derived_ignore_patterns(),
            ignorePattern=passes.ignore_patterns,
            minLines=overrides.min_lines,
            minTokens=overrides.min_tokens,
            mode=overrides.mode,
            noColors=True,
            noTips=True,
            reporters=(c.Infra.OUTPUT_JSON,),
            threshold=overrides.threshold_percent,
            similarity=passes.similarity,
            semantic=None if self.semantic_not_executed() else passes.semantic,
        )
        config_path = (
            self._repository_root
            / c.Infra.JSCPD_REPORT_DIRNAME
            / c.Infra.JSCPD_CONFIG_FILENAME
        )
        u.Cli.ensure_dir(config_path.parent).unwrap()
        rendered = jscpd_config.model_dump_json(by_alias=True, exclude_none=True)
        u.Cli.atomic_write_text_file(config_path, rendered).unwrap()
        return r[Path].ok(config_path)

    @staticmethod
    def semantic_not_executed() -> bool:
        """Whether the embedding pass is NOT EXECUTED in this context.

        The CI context has no embeddings host, so the pass is typed NOT
        EXECUTED there with its reason in the gate output; it is never a
        green result and never replaced by another classifier.

        Returns:
            Whether the invocation runs in the declared CI context.

        """
        ci = config.Infra.codegen.make.ci
        return (u.Infra.env_lookup(ci.variable) or "").strip() == ci.value

    def _derived_ignore_patterns(self) -> t.StrSequence:
        """Derive the complete jscpd ignore list from declared owners.

        Every pattern names a declared semantic fact, never a hand-maintained
        exception: the ast-grep corpus topology read from the declared
        sgconfig fixtures (provider resource and the repository-local delta
        when declared), the declared ast-grep snapshot directory,
        and resolver-owned lockfile emission. Case directories, part
        directories and helper filenames do not establish ownership exemptions.
        Owned generated sources remain subject to clone analysis.

        Returns:
            The resulting ``t.StrSequence``.

        """
        globs: list[str] = []
        corpus_root_rel = c.Infra.CODEMOD_CONFIG_RELPATH.parent.as_posix()
        # The same relative corpus path names the governed checkout's
        # catalog and the copy the distribution ships as <pkg>/config, so
        # the packaged provider root resolves beside its packaged config
        # directory.
        provider_root = type(config).ssot_config_dir().parent / corpus_root_rel
        if (provider_root / c.Infra.CODEMOD_CONFIG_FILENAME).is_file():
            globs.extend(
                self._sgconfig_fixture_globs(corpus_root_rel, provider_root),
            )
        local_root = self._repository_root / corpus_root_rel
        if (local_root / c.Infra.CODEMOD_CONFIG_FILENAME).is_file():
            globs.extend(self._sgconfig_fixture_globs(corpus_root_rel, local_root))
        globs.append(f"**/{c.Infra.CODEMOD_SNAPSHOT_DIRNAME}/**")
        globs.extend(f"**/{name}" for name in config.Infra.codegen.resolver_owned_files)
        return tuple(dict.fromkeys(globs))

    @staticmethod
    def _sgconfig_fixture_globs(
        corpus_root_rel: str,
        config_root: Path,
    ) -> t.StrSequence:
        """Derive corpus globs from one declared sgconfig's fixture topology.

        Returns:
            The resulting ``t.StrSequence``.

        """
        fixtures = FlextInfraCodemodSnapshotReconciler.fixture_directories(config_root)
        return tuple(
            f"**/{corpus_root_rel}/{directory.name}/**"
            for directory in sorted({*fixtures.rule_dirs, *fixtures.test_dirs})
        )

    @staticmethod
    def _load_report(
        report_dir: Path,
        result: p.Cli.CommandOutput,
    ) -> p.Cli.CommandOutput:
        """Load the JSON report jscpd writes to disk; stdout carries console noise only.

        Returns:
            The resulting ``p.Cli.CommandOutput``.

        """
        if (
            result.outcome.timed_out
            or result.outcome.forwarded_signal is not None
            or result.outcome.raw_return_code < 0
        ):
            return result
        report_path = report_dir / c.Infra.JSCPD_REPORT_FILENAME
        if not report_path.is_file():
            return result
        return m.Cli.CommandOutput(
            stdout=report_path.read_text(encoding="utf-8"),
            stderr=result.stderr,
            outcome=m.Cli.ProcessOutcome(
                raw_return_code=result.outcome.raw_return_code,
                timed_out=result.outcome.timed_out,
                forwarded_signal=result.outcome.forwarded_signal,
            ),
        )


__all__: list[str] = ["FlextInfraDuplicationGate"]
