"""FLEXT ruff_lint quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, config, m, u
from flext_infra.gates import FlextInfraGate
from flext_infra.gates._readonly_namespace import FlextInfraReadonlyNamespace
from flext_infra.refactor import FlextInfraImportNormalization

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraRuffLintGate(FlextInfraGate):
    """Ruff Lint quality gate."""

    gate_id: ClassVar[str] = c.Infra.LINT
    gate_name: ClassVar[str] = "Ruff Lint"
    # Why: the gate implements _build_fix_command (ruff check --fix); declaring
    # can_fix=False made workspace_check_gates skip it, so `make fix`
    # never applied a single lint fix and the command below was dead code.
    can_fix: ClassVar[bool] = True

    def source_manifest(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        *,
        targets: t.StrSequence | None = None,
    ) -> tuple[Path, ...]:
        """Ask the native lint owner which files its actual invocation reads.

        This does not reuse codemod's transformation inventory: Ruff owns
        include/exclude, explicit targets, stubs, notebooks, and ignore files.
        An admission caller must reject unsupported formats rather than remove
        them from this manifest.

        Returns:
            Existing project-owned source paths selected by native Ruff.

        Raises:
            ValueError: If native discovery is incomplete or escapes the project.

        """
        selected = (
            self._get_check_dirs(project_dir, ctx) if targets is None else targets
        )
        result = self._run(
            self._lint_command(ctx, selected, ("--show-files", "--no-fix")),
            project_dir,
            timeout=self._check_timeout(project_dir, ctx),
            env=self._check_env(project_dir, ctx),
            remove_env_keys=self._check_remove_env_keys(project_dir, ctx),
        )
        if not u.Cli.process_succeeded(result.outcome) or result.stderr.strip():
            msg = (
                "Ruff source manifest is unavailable: "
                f"exit={result.outcome.raw_return_code}; {result.stderr.strip()}"
            )
            raise ValueError(msg)
        root = project_dir.resolve()
        paths: set[Path] = set()
        for line in result.stdout.splitlines():
            candidate = Path(line)
            path = (
                candidate if candidate.is_absolute() else root / candidate
            ).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                msg = f"Ruff source manifest has an invalid project source: {line!r}"
                raise ValueError(msg)
            paths.add(path)
        if not paths:
            msg = (
                "Ruff source manifest is empty; naming coverage cannot be authenticated"
            )
            raise ValueError(msg)
        return tuple(sorted(paths))

    def readonly_namespace_sources(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        *,
        targets: t.StrSequence | None = None,
    ) -> tuple[Path, ...]:
        """Require complete Python coverage before a per-name naming adaptation.

        Returns:
            The unchanged native manifest, including stub and generated inputs.

        Raises:
            ValueError: If any native input has no Python namespace authenticator.

        """
        manifest = self.source_manifest(project_dir, ctx, targets=targets)
        unsupported = tuple(
            path
            for path in manifest
            if path.suffix not in {".py", ".pyi"}
            and path.name not in {c.PYPROJECT_FILENAME, "ruff.toml", ".ruff.toml"}
        )
        if unsupported:
            msg = "Readonly namespace naming coverage is unavailable for: " + ", ".join(
                str(path.relative_to(project_dir.resolve())) for path in unsupported
            )
            raise ValueError(msg)
        return manifest

    def check_readonly_namespaces(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        occurrences: tuple[m.Infra.RuffReadonlyNamespaceOccurrence, ...],
        *,
        targets: t.StrSequence | None = None,
    ) -> m.Infra.GateExecution:
        """Run an auxiliary strict naming probe, never the primary lint verdict.

        Every registered getter must be present in the native scope. The source
        authenticator elects exactly one N802 per occurrence. All other native
        naming findings remain blocking, including argument, local, exception,
        stub, and future pep8-naming rules supported by the installed Ruff.
        Effective ignore patterns are read per file from native Ruff metadata;
        only the exact registered names are removed. A surviving wildcard that
        conceals a getter therefore fails the expected-diagnostic accounting.

        Returns:
            Complement findings with separate, explicitly named probe receipts.

        Raises:
            ValueError: If declarations, native metadata, or accounting fail closed.

        """
        started = time.monotonic()
        if not occurrences:
            msg = "Readonly namespace probe requires explicit occurrence identities"
            raise ValueError(msg)
        manifest = self.readonly_namespace_sources(project_dir, ctx, targets=targets)
        authenticator = FlextInfraReadonlyNamespace(manifest)
        expected = {
            authenticator.authenticate(project_dir, occurrence)
            for occurrence in occurrences
        }
        if len(expected) != len(occurrences):
            msg = "Readonly namespace registry contains duplicate occurrence identities"
            raise ValueError(msg)
        names = frozenset(item.qualname.rsplit(".", 1)[1] for item in occurrences)
        probe_ctx = ctx.model_copy(
            update={
                "reports_dir": ctx.reports_dir / "readonly-namespace-probe",
            }
        )
        issues: list[m.Infra.Issue] = []
        raw: list[str] = []
        for path in manifest:
            if path.suffix not in {".py", ".pyi"}:
                continue
            file_ctx = probe_ctx.model_copy(
                update={
                    "reports_dir": probe_ctx.reports_dir
                    / path.relative_to(project_dir.resolve()),
                }
            )
            ignores = self._readonly_namespace_ignore_names(project_dir, file_ctx, path)
            result = self._run(
                self._lint_command(
                    ctx,
                    (str(path),),
                    (
                        "--no-fix",
                        "--config",
                        "lint.pep8-naming.ignore-names="
                        + json.dumps([name for name in ignores if name not in names]),
                        "--config",
                        "lint.pep8-naming.extend-ignore-names=[]",
                    ),
                ),
                project_dir,
                timeout=self._check_timeout(project_dir, ctx),
                env=self._check_env(project_dir, ctx),
                remove_env_keys=self._check_remove_env_keys(project_dir, ctx),
            )
            evidence = self._publish_raw_receipt(file_ctx, self._raw_output(result))
            raw.append(evidence.raw_output)
            if (
                result.outcome.raw_return_code not in {0, *self._findings_exit_codes()}
                or result.stderr.strip()
            ):
                msg = f"Readonly namespace baseline is unavailable; receipt: {evidence.path}"
                raise ValueError(msg)
            report = u.Cli.json_parse(result.stdout).unwrap()
            if not isinstance(report, list):
                msg = "Readonly namespace baseline is not a native diagnostic list"
                raise ValueError(msg)
            for entry in report:
                if not isinstance(entry, Mapping):
                    msg = "Readonly namespace baseline contains malformed diagnostics"
                    raise ValueError(msg)
                code = u.Cli.json_pick_str(entry, "code")
                filename = u.Cli.json_pick_str(entry, "filename")
                line = u.Cli.json_nested_int(entry, "location", "row")
                column = u.Cli.json_nested_int(entry, "location", "column")
                identity = (filename, line, column)
                if code == "N802" and identity in expected:
                    expected.remove(identity)
                elif code.startswith("N"):
                    issues.append(
                        m.Infra.Issue(
                            file=filename,
                            line=line,
                            column=column,
                            code=u.Cli.json_pick_str(entry, "name"),
                            message=u.Cli.json_pick_str(entry, "message"),
                            severity=c.Infra.GateSeverity.ERROR.value,
                        )
                    )
        if expected:
            msg = f"Readonly namespace baseline did not report every authenticated getter: {sorted(expected)}"
            raise ValueError(msg)
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            evidence=self._publish_raw_receipt(probe_ctx, "\n".join(raw)),
            started=started,
        )

    def _readonly_namespace_ignore_names(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        path: Path,
    ) -> tuple[str, ...]:
        """Read merged native ignore-name metadata without guessing defaults."""
        result = self._run(
            self._lint_command(ctx, (str(path),), ("--show-settings", "--no-fix")),
            project_dir,
            timeout=self._check_timeout(project_dir, ctx),
            env=self._check_env(project_dir, ctx),
            remove_env_keys=self._check_remove_env_keys(project_dir, ctx),
        )
        metadata_ctx = ctx.model_copy(
            update={"reports_dir": ctx.reports_dir / "settings"}
        )
        receipt = self._publish_raw_receipt(metadata_ctx, self._raw_output(result))
        marker = "linter.pep8_naming.ignore_names = ["
        if (
            not u.Cli.process_succeeded(result.outcome)
            or result.stderr.strip()
            or result.stdout.count(marker) != 1
        ):
            msg = (
                f"Readonly naming metadata is unavailable or ambiguous: {receipt.path}"
            )
            raise ValueError(msg)
        _, _, tail = result.stdout.partition(marker)
        lines = tail.splitlines()
        if not lines or lines[0].strip() or "]" not in lines:
            msg = f"Unsupported native readonly naming metadata: {receipt.path}"
            raise ValueError(msg)
        values: list[str] = []
        for line in lines[1:]:
            if line == "]":
                return tuple(values)
            value = line.strip()
            if not value.endswith(",") or not value.removesuffix(","):
                msg = f"Malformed native readonly naming metadata: {receipt.path}"
                raise ValueError(msg)
            values.append(value.removesuffix(","))
        msg = f"Incomplete native readonly naming metadata: {receipt.path}"
        raise ValueError(msg)

    @override
    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrMapping:
        """Keep native cache writes outside authenticated source candidates.

        Returns:
            The resulting ``t.StrMapping``.

        """
        return {
            **(super()._check_env(project_dir, ctx) or {}),
            c.Infra.RUFF_CACHE_ENVIRONMENT_VARIABLE: str(
                u.Infra.ruff_cache_directory(project_dir)
            ),
        }

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Ruff always runs — never skip.

        Returns:
            The resulting ``t.StrSequence``.

        """
        del ctx
        return self._existing_check_dirs(project_dir) or ["."]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Lint read-only with the config-owned check flags.

        Returns:
            The Ruff lint invocation in check mode.

        """
        del project_dir
        return self._lint_command(
            ctx,
            check_dirs,
            config.Infra.codegen.make.ruff.lint_check,
        )

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> t.StrSequence:
        """Build the explicit Ruff fix command.

        Returns:
            The resulting ``t.StrSequence``.

        """
        del project_dir
        return self._lint_command(ctx, targets, config.Infra.codegen.make.ruff.lint_fix)

    @override
    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        """Apply Ruff's own fixes, then the declared recipe of each finding left.

        The recipe phases are tooling data (``fix-recipe-phases``) applied in
        order; Ruff re-reads the tree after each phase. Every remaining finding
        blocks the final verdict and retains Ruff's diagnostic, whether or not
        a recipe owns its repair.

        Returns:
            The gate execution of Ruff's final pass.

        """
        execution = super().fix(project_dir, ctx)
        if execution.outcome is c.Infra.ToolOutcome.ERROR:
            return execution
        tooling = u.Infra.load_tooling_inputs(project_dir).unwrap().document
        lint = tooling.tools.ruff.lint
        recipes = lint.fix_recipes
        overridden = self._project_overrides(project_dir, execution.issues, recipes)
        for phase in lint.fix_recipe_phases:
            hooks = self._overridden_hooks(execution.issues, recipes, overridden)
            by_file = self._phase_findings(
                execution.issues,
                recipes,
                frozenset(phase),
                hooks,
            )
            if by_file:
                self._apply_phase(project_dir, by_file, recipes, tooling=tooling)
                repaired = super().fix(project_dir, ctx)
                execution = repaired.model_copy(
                    update={
                        "raw_output": "\n".join(
                            output
                            for output in (execution.raw_output, repaired.raw_output)
                            if output
                        ),
                    },
                )
                if execution.outcome is c.Infra.ToolOutcome.ERROR:
                    return execution
        return execution

    def _project_overrides(
        self,
        project_dir: Path,
        issues: t.SequenceOf[p.Infra.Issue],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
    ) -> frozenset[t.Pair[str, str]]:
        """Index the methods on an override chain of this project.

        The index exists only for the static-method recipe, so a run without
        its findings builds none. A module Ruff reports as ``invalid-syntax``
        declares no class Ruff could judge and stays out of the index; its
        finding remains for its owner.

        Returns:
            The ``(class name, method name)`` pairs on an override chain.

        """
        if not any(
            recipes.get(issue.code) is c.Infra.LintFixRecipe.STATIC_METHOD
            for issue in issues
        ):
            return frozenset()
        unparsable = {
            Path(issue.file).resolve()
            for issue in issues
            if issue.code == c.Infra.RUFF_INVALID_SYNTAX
        }
        return u.Infra.overridden_methods(
            tuple(
                path.read_text(encoding=c.DEFAULT_ENCODING)
                for directory in self._existing_check_dirs(project_dir)
                for path in u.Infra.iter_directory_python_files(
                    project_dir / directory,
                )
                if path.resolve() not in unparsable
            ),
        )

    @staticmethod
    def _phase_findings(
        issues: t.SequenceOf[p.Infra.Issue],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
        phase: frozenset[c.Infra.LintFixRecipe],
        hooks: t.StrSequence,
    ) -> t.MappingKV[Path, t.SequenceOf[p.Infra.Issue]]:
        """Group by file the findings one recipe phase repairs.

        Returns:
            The phase's findings per module, overridden hooks excluded.

        """
        by_file: MutableMapping[Path, list[p.Infra.Issue]] = {}
        for issue in issues:
            if (
                recipes.get(issue.code) in phase
                and f"{issue.file}:{issue.line}:{issue.code}" not in hooks
            ):
                by_file.setdefault(Path(issue.file), []).append(issue)
        return by_file

    def _apply_phase(
        self,
        project_dir: Path,
        by_file: t.MappingKV[Path, t.SequenceOf[p.Infra.Issue]],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
        *,
        tooling: m.Infra.ToolConfigDocument,
    ) -> None:
        """Repair every module of one phase, computing all before any write."""
        with self._mutation_lease(project_dir):
            import_graph: t.MappingKV[str, frozenset[str]] = (
                u.Infra.project_import_graph(project_dir)[0]
                if any(
                    recipes.get(issue.code) is c.Infra.LintFixRecipe.NORMALIZE_IMPORTS
                    for issues in by_file.values()
                    for issue in issues
                )
                else {}
            )
            # A module the recipes cannot place stops the phase with nothing
            # written.
            planned: t.MutableSequenceOf[t.Pair[m.Cli.AtomicFileState, str]] = []
            for path, issues in sorted(by_file.items()):
                before = u.Cli.atomic_read_binary_file_state(
                    path,
                    required=True,
                ).unwrap()
                repaired = self._repaired_source(
                    project_dir,
                    before,
                    issues,
                    recipes,
                    import_graph=import_graph,
                    tooling=tooling,
                )
                if repaired.encode(c.DEFAULT_ENCODING) != before.content:
                    planned.append((before, repaired))
            for before, repaired in planned:
                u.Cli.atomic_write_text_file_guarded(before, repaired).unwrap()

    @staticmethod
    def _static_hook_keys(
        issues: t.SequenceOf[p.Infra.Issue],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
        resolver: Callable[..., t.VariadicTuple[p.Infra.Issue]],
        **extras: frozenset[t.Pair[str, str]],
    ) -> t.StrSequence:
        """Render the static-method findings one resolver leaves to their owner.

        Returns:
            ``file:line:code`` of each kept finding.

        """
        by_file: MutableMapping[Path, list[p.Infra.Issue]] = {}
        for issue in issues:
            if recipes.get(issue.code) is c.Infra.LintFixRecipe.STATIC_METHOD:
                by_file.setdefault(Path(issue.file), []).append(issue)
        return sorted(
            f"{issue.file}:{issue.line}:{issue.code}"
            for path, found in by_file.items()
            for issue in resolver(
                path.read_text(encoding=c.DEFAULT_ENCODING),
                found,
                path=path,
                recipes=recipes,
                **extras,
            )
        )

    @staticmethod
    def _repaired_source(
        project_dir: Path,
        before: m.Cli.AtomicFileState,
        issues: t.SequenceOf[p.Infra.Issue],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
        *,
        import_graph: t.MappingKV[str, frozenset[str]],
        tooling: m.Infra.ToolConfigDocument,
    ) -> str:
        """Apply one module's recipes: whole-module rewrites, then planned edits.

        ``normalize-imports`` runs the import-law engine over the module and
        ``wrap-long-line`` wraps the reported lines; every other recipe is an
        edit the lint-recipe planner places.

        Returns:
            The repaired module source.

        Raises:
            FileNotFoundError: If ``before.content is None``.

        """
        if before.content is None:
            raise FileNotFoundError(before.path)
        path = before.path
        source = before.content.decode(c.DEFAULT_ENCODING)
        owned = {issue.code: recipes[issue.code] for issue in issues}
        if c.Infra.LintFixRecipe.NORMALIZE_IMPORTS in owned.values():
            source = (
                FlextInfraImportNormalization.normalize_source(
                    project_root=project_dir,
                    file_path=path,
                    source=source,
                    import_graph=import_graph,
                )
                or source
            )
        wrapped = [
            issue.line
            for issue in issues
            if owned[issue.code] is c.Infra.LintFixRecipe.WRAP_LONG_LINE
        ]
        if wrapped:
            source = u.Infra.wrap_long_lines(
                source,
                wrapped,
                limit=u.Infra.native_tool_setting(tooling, "ruff", "line-length", int),
            )
        planned: t.SequenceOf[p.Infra.Issue] = [
            issue
            for issue in issues
            if owned[issue.code]
            not in {
                c.Infra.LintFixRecipe.NORMALIZE_IMPORTS,
                c.Infra.LintFixRecipe.WRAP_LONG_LINE,
            }
        ]
        if not planned:
            return source
        return u.Infra.apply_lint_recipes(source, planned, path=path, recipes=recipes)

    @staticmethod
    def _overridden_hooks(
        issues: t.SequenceOf[p.Infra.Issue],
        recipes: t.MappingKV[str, c.Infra.LintFixRecipe],
        overridden: frozenset[t.Pair[str, str]],
    ) -> t.StrSequence:
        """Retain instance-method contracts without suppressing their findings.

        Returns:
            ``file:line:code`` of each finding the static-method recipe keeps.

        """
        return (
            *FlextInfraRuffLintGate._static_hook_keys(
                issues,
                recipes,
                u.Infra.overridden_findings,
                overridden=overridden,
            ),
            *FlextInfraRuffLintGate._static_hook_keys(
                issues,
                recipes,
                u.Infra.service_operation_findings,
            ),
        )

    def _lint_command(
        self,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
        mode_args: t.StrSequence,
    ) -> t.StrSequence:
        """Keep check and fix on the same Ruff lint invocation contract.

        Returns:
            The resulting ``t.StrSequence``.

        """
        return self._python_module_command(
            c.Infra.RUFF,
            c.Infra.VERB_CHECK,
            *targets,
            *ctx.ruff_args,
            *mode_args,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "--quiet",
        )

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.Pair[bool, t.SequenceOf[p.Infra.Issue]]:
        """Parse Ruff's JSON report into findings named by their Ruff rule.

        Ruff names every finding by rule name (a syntax error included, as
        ``invalid-syntax``); a report that is not the declared JSON list is a
        tool error and raises with its cause.

        Returns:
            The run's verdict and the findings it reported.

        Raises:
            TypeError: If the report is not a list of finding objects.

        """
        del ctx
        report = u.Cli.json_parse(result.stdout or "[]").unwrap()
        if not isinstance(report, list):
            msg = f"Ruff JSON report is not a list: {type(report).__name__}"
            raise TypeError(msg)
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        for entry in report:
            if not isinstance(entry, Mapping):
                msg = f"Ruff JSON finding is not an object: {type(entry).__name__}"
                raise TypeError(msg)
            code = u.Cli.json_pick_str(entry, "name")
            issues.append(
                m.Infra.Issue(
                    file=u.Cli.json_pick_str(entry, "filename", "?"),
                    line=u.Cli.json_nested_int(entry, "location", "row"),
                    column=u.Cli.json_nested_int(entry, "location", "column"),
                    code=code,
                    message=u.Cli.json_pick_str(entry, "message"),
                    severity=c.Infra.GateSeverity.ERROR.value,
                ),
            )
        passed, parsed = self._finalize_parse_result(
            result,
            project_dir,
            issues,
            c.Infra.RUFF,
        )
        # Ruff's findings exit is a valid scanner result, but every reported
        # finding still blocks the lint gate under the current quality baseline.
        return passed and not parsed, parsed

    @staticmethod
    @override
    def _findings_exit_codes() -> t.VariadicTuple[int]:
        """Exit statuses with which Ruff reports its findings.

        Returns:
            The findings statuses declared for Ruff in the tooling config.

        """
        return config.Infra.tooling.tools.ruff.findings_exit_codes


__all__: list[str] = ["FlextInfraRuffLintGate"]
