"""FLEXT ruff_lint quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, config, deps, m, u
from flext_infra.gates import FlextInfraGate
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

    @staticmethod
    def _authorial_targets(project_dir: Path, targets: t.StrSequence) -> t.StrSequence:
        """Select authored sources without treating verified SDK stubs as our work.

        Returns:
            Original targets or exact authored files beside authenticated SDK stubs.

        """
        if not (project_dir / c.PYPROJECT_FILENAME).is_file():
            return targets
        producer = deps.FlextInfraDependencyDetectionService
        external = producer.authenticated_typing_sources(
            project_dir, producer().load_typing_generation_policy()
        )
        if not external:
            return targets
        selected = tuple((project_dir / target).resolve() for target in targets)
        return tuple(
            str(path.relative_to(project_dir))
            for path in u.Infra.discover_python_files(
                project_dir, workspace_excluded_top_dirs=frozenset()
            )
            if path not in external
            and any(
                path == target or path.is_relative_to(target) for target in selected
            )
        )

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

        Raises:
            ValueError: If the selected authorial scope has no source files.

        """
        targets = self._authorial_targets(project_dir, check_dirs)
        if not targets:
            msg = "Ruff authorial scope contains no source files"
            raise ValueError(msg)
        return self._lint_command(
            ctx,
            targets,
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

        Raises:
            ValueError: If the selected authorial scope has no source files.

        """
        authored = self._authorial_targets(project_dir, targets)
        if not authored:
            msg = "Ruff authorial scope contains no source files"
            raise ValueError(msg)
        return self._lint_command(
            ctx, authored, config.Infra.codegen.make.ruff.lint_fix
        )

    @override
    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
        started: float,
    ) -> m.Infra.GateExecution:
        executions = []
        for scope, targets in self._lint_scopes(project_dir, ctx, check_dirs):
            execution = super()._execute_check_command(
                project_dir, scope, targets, started
            )
            if execution.outcome is c.Infra.ToolOutcome.ERROR:
                return execution
            executions.append(execution)
        return self._build_check_gate_execution(
            project_dir,
            passed=all(item.result.passed for item in executions),
            issues=tuple(issue for item in executions for issue in item.issues),
            raw_output="\n".join(item.raw_output for item in executions),
            started=started,
        )

    def _lint_scopes(
        self, project_dir: Path, ctx: m.Infra.GateContext, targets: t.StrSequence
    ) -> tuple[tuple[m.Infra.GateContext, t.StrSequence], ...]:
        """Ask native Ruff for effective rules, then elect their proven source scope.

        No diagnostic is filtered: each native invocation checks every applicable
        rule. External signature names/imports are not local implementation choices.

        Returns:
            Native invocations retaining all rules except proven inapplicability.

        """
        if not (project_dir / c.PYPROJECT_FILENAME).is_file():
            return ((ctx, targets),)
        producer = deps.FlextInfraDependencyDetectionService
        contracts = producer.typing_contract_rules(
            project_dir, producer().load_typing_generation_policy()
        )
        if not contracts:
            return ((ctx, targets),)
        source_args: list[str] = []
        arguments = iter(ctx.ruff_args)
        for argument in arguments:
            if argument in {"--select", "--extend-select"}:
                next(arguments)
            elif not argument.startswith(("--select=", "--extend-select=")):
                source_args.append(argument)
        groups: dict[tuple[str, ...], list[str]] = {}
        for target in self._authorial_targets(project_dir, targets):
            path = (project_dir / target).resolve()
            inapplicable = contracts.get(path)
            if not inapplicable:
                groups.setdefault((), []).append(target)
                continue
            flags = self._contract_rule_args(project_dir, ctx, target, inapplicable)
            groups.setdefault(flags, []).append(target)
            u.Cli.info(
                f"lint: upstream contract {target}; implementation-only rules: "
                + ", ".join(sorted(inapplicable))
            )
        return tuple(
            (
                ctx.model_copy(
                    update={
                        "ruff_args": (
                            *(source_args if flags else ctx.ruff_args),
                            *flags,
                        ),
                        "selected_files": tuple(
                            project_dir / target for target in members
                        ),
                    }
                ),
                tuple(members),
            )
            for flags, members in groups.items()
        )

    def _contract_rule_args(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        target: str,
        inapplicable: frozenset[str],
    ) -> tuple[str, ...]:
        """Materialize effective native rules before electing source applicability.

        Returns:
            Explicit native selection without project per-file suppressions.

        Raises:
            RuntimeError: If Ruff cannot expose a nonempty effective rule selection.

        """
        clean_scope = ("--config", "lint.per-file-ignores={}")
        observed = self._run(
            (
                *self._lint_command(
                    ctx, (target,), config.Infra.codegen.make.ruff.lint_check
                ),
                *clean_scope,
                "--show-settings",
            ),
            project_dir,
        )
        _, marker, settings = observed.stdout.partition("linter.rules.enabled = [\n")
        rules, closed, _ = settings.partition("\n]")
        if not u.Cli.process_succeeded(observed.outcome) or not marker or not closed:
            msg = (
                f"Ruff effective rule scope is unavailable: {target}: {observed.stderr}"
            )
            raise RuntimeError(msg)
        applicable = tuple(
            name
            for line in rules.splitlines()
            if line.strip()
            and (name := line.strip().removesuffix(",").split(" (", maxsplit=1)[0])
            not in inapplicable
        )
        if not applicable:
            msg = f"Ruff effective rule scope is empty: {target}"
            raise RuntimeError(msg)
        return (*clean_scope, "--select", ",".join(applicable))

    @override
    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        started = time.monotonic()
        executions = []
        for scope, _ in self._lint_scopes(
            project_dir, ctx, self._get_fix_targets(project_dir, ctx)
        ):
            execution = self._fix_sources(project_dir, scope)
            if execution.outcome is c.Infra.ToolOutcome.ERROR:
                return execution
            executions.append(execution)
        return self._build_check_gate_execution(
            project_dir,
            passed=all(item.result.passed for item in executions),
            issues=tuple(issue for item in executions for issue in item.issues),
            raw_output="\n".join(item.raw_output for item in executions),
            started=started,
        )

    def _fix_sources(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
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
