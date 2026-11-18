"""FLEXT markdown quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, MutableSequence, Sequence
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates import FlextInfraMarkdownGateBase, FlextInfraMarkdownListIndent

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraGatesMarkdown(FlextInfraMarkdownGateBase):
    """Markdown quality gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN
    gate_name: ClassVar[str] = "Markdown"
    # Fixable findings are repaired by the native linter. The findings that
    # remain after repair come back under rumdl's declared findings status:
    # the repair verb completes and reports them, and the read-only gate
    # enforces them.
    can_fix: ClassVar[bool] = True

    @override
    def _execute_fix_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
        started: float,
        lock_owners: Sequence[Path],
    ) -> p.Infra.GateExecution:
        """Repair natively, then move the MkDocs list blocks rumdl withholds.

        Each phase re-indents the blocks its rule still reports in MkDocs
        documents and runs the native repair again, so the verdict reads the
        repaired files. Nested items move first: their new column sets the
        column their content needs.

        Returns:
            The native repair's execution over the re-indented files.

        """
        execution = super()._execute_fix_command(
            project_dir, ctx, targets, started, lock_owners
        )
        for rule in c.Infra.MARKDOWN_MKDOCS_LIST_RULES:
            if execution.outcome is c.Infra.ToolOutcome.ERROR:
                break
            if self._reindent_mkdocs_lists(
                project_dir, execution.issues, rule, lock_owners
            ):
                execution = super()._execute_fix_command(
                    project_dir, ctx, targets, started, lock_owners
                )
        return execution

    def _reindent_mkdocs_lists(
        self,
        project_dir: Path,
        issues: Sequence[p.Infra.Issue],
        rule: str,
        lock_owners: Sequence[Path],
    ) -> bool:
        """Publish the re-indent of every MkDocs document ``rule`` reports.

        Returns:
            Whether any document changed.

        Raises:
            RuntimeError: If the publisher rejects the re-indented documents.

        """
        reported: dict[Path, set[int]] = {}
        for issue in issues:
            if issue.code == rule:
                path = (project_dir / issue.file).resolve()
                reported.setdefault(path, set()).add(issue.line)
        owners = {path: self._projected_owner(path, lock_owners) for path in reported}
        patterns = {
            owner: self._mkdocs_patterns(owner) for owner in set(owners.values())
        }
        plans: dict[Path, list[p.Infra.CodegenFilePlan]] = {}
        for path, lines in reported.items():
            owner = owners[path]
            relative = PurePosixPath(path.relative_to(owner).as_posix())
            if not any(relative.full_match(glob) for glob in patterns[owner]):
                continue
            plan = self._reindent_plan(owner, path, rule, lines)
            if plan is not None:
                plans.setdefault(owner, []).append(plan)
        for owner, owned in plans.items():
            published = u.Infra.publish_codegen_plans(owner, owned)
            if published.failure:
                msg = published.error or f"{owner}: list re-indent publication failed"
                raise RuntimeError(msg)
        return bool(plans)

    def _reindent_plan(
        self,
        owner: Path,
        path: Path,
        rule: str,
        lines: Collection[int],
    ) -> p.Infra.CodegenFilePlan | None:
        """Plan one document's re-indent; projected blocks stay byte for byte.

        Returns:
            The document's publication plan, or ``None`` when nothing moved.

        Raises:
            RuntimeError: If the document cannot be observed.

        """
        captured = u.Infra.codegen_target_snapshot(path)
        if captured.failure:
            msg = captured.error or f"{path}: reported document is unreadable"
            raise RuntimeError(msg)
        state = captured.value
        content = state.content
        if content is None:
            msg = f"{path}: reported document has no content"
            raise RuntimeError(msg)
        original = content.decode(c.DEFAULT_ENCODING)
        repaired = self.projected_block_splice(
            path,
            original,
            FlextInfraMarkdownListIndent.reindent(
                self.projected_block_view(path, original), rule, lines
            ),
        )
        if repaired == original:
            return None
        return m.Infra.CodegenFilePlan(
            project=owner,
            path=state.path,
            before=state,
            desired_content=repaired.encode(c.DEFAULT_ENCODING),
            desired_mode=state.mode,
        )

    @staticmethod
    def _mkdocs_patterns(project_root: Path) -> Collection[str]:
        """Read the path globs the project's rumdl policy renders as MkDocs.

        Returns:
            The ``per-file-flavor`` globs whose flavor is MkDocs.

        """
        document = u.Infra.load_tooling_inputs(project_root).unwrap().document
        flavors = u.Infra.configuration_pairs(
            document.tools.markdown.native_settings
        ).get(c.Infra.MARKDOWN_PER_FILE_FLAVOR_TABLE)
        if not isinstance(flavors, Mapping):
            return ()
        return tuple(
            glob
            for glob, flavor in flavors.items()
            if flavor == c.Infra.MARKDOWN_MKDOCS_FLAVOR
        )

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Lint the collected Markdown files read-only, through their lint view.

        rumdl has no configuration that excludes a region of a file, so the
        check reads every target from ``--stdin-batch`` (see
        ``_execute_check_command``) under its own path, with declared foreign
        projected blocks masked.

        Returns:
            The rumdl check invocation.

        """
        del ctx, check_dirs
        return self._rumdl_command(project_dir, "check", (), "--stdin-batch")

    @override
    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
        started: float,
    ) -> p.Infra.GateExecution:
        """Run the read-only lint over every target's projected-block view.

        The check command reads its targets from stdin, so the invocation
        carries the rumdl ``--stdin-batch`` payload of every target.

        Returns:
            The parsed lint execution.

        """
        result = self._run(
            self._build_check_command(project_dir, ctx, targets),
            project_dir,
            ctx,
            input_data=self.projected_block_stdin_batch(project_dir, targets),
        )
        return self._parsed_gate_execution(project_dir, ctx, result, started)

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
    ) -> Sequence[str]:
        """Repair fixable findings and return the linter's residual verdict.

        Returns:
            The resulting ``Sequence[str]``.

        """
        del ctx
        return self._rumdl_command(project_dir, "check", targets, "--fix")

    @override
    def _projected_command(self, project_dir: Path, target: str) -> Sequence[str]:
        """Repair one projected file's lint view read from stdin.

        Returns:
            The rumdl ``check --fix --stdin`` invocation named after ``target``.

        """
        return self._rumdl_command(
            project_dir, "check", (), "--fix", "--stdin", "--stdin-filename", target
        )

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
        """Parse rumdl output, discarding lines marking already-applied fixes.

        Returns:
            The resulting ``tuple[bool, Sequence[p.Infra.Issue]]``.

        """
        del ctx
        issues: MutableSequence[p.Infra.Issue] = []
        for line in (result.stdout + "\n" + result.stderr).splitlines():
            match = c.Infra.MARKDOWN_RE.match(line.strip())
            if not match:
                continue
            if match.group("msg").strip().endswith(c.Infra.MARKDOWN_FIXED_SUFFIX):
                continue
            issues.append(
                m.Infra.Issue(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    column=int(match.group("col") or 1),
                    code=match.group("code"),
                    message=match.group("msg"),
                ),
            )
        return self._finalize_parse_result(result, project_dir, issues, c.Infra.RUMDL)


__all__: list[str] = ["FlextInfraGatesMarkdown"]
