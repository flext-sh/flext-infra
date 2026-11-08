"""Shared markdown-gate surface: collection, config, and the rumdl invocation.

``markdown`` (``rumdl check``) and ``markdown-format`` (``rumdl fmt``) drive
the same tool over the same governed markdown surface with the same generated
configuration, so typed file eligibility and the rumdl invocation contract live
here exactly once. Generated ignore files are outputs, never policy inputs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, config, m, p, u
from flext_infra.gates import FlextInfraGates


class FlextInfraMarkdownGateBase(FlextInfraGates):
    """Share file selection, configuration, and the rumdl invocation."""

    # Relative flavor and exclusion patterns belong to each configuration root.
    # Union dispatch remains available, but distinct roots cannot share a run.
    union_capable: ClassVar[bool] = True

    @staticmethod
    @override
    def union_group_key(project_dir: Path) -> str:
        """Keep native relative-pattern semantics rooted in each repository.

        A project without the generated configuration runs alone, so its own
        failure stays attributed to it.

        Returns:
            The configuration fingerprint shared by one union group.

        """
        config_path = project_dir / c.Infra.MARKDOWN_CONFIG_FILENAME
        if not config_path.is_file():
            return f"absent:{project_dir.resolve()}"
        return "\0".join((
            project_dir.resolve().as_posix(),
            config_path.read_text(c.DEFAULT_ENCODING),
        ))

    @override
    def _union_targets(
        self,
        project_dirs: Sequence[Path],
        ctx: p.Infra.GateContext,
        *,
        repair: bool,
    ) -> Sequence[str]:
        """Collect each project's files through its effective typed scope.

        Returns:
            Every project's governed Markdown files as absolute paths.

        """
        del repair
        return tuple(
            path.resolve().as_posix()
            for project_dir in project_dirs
            for path in self.collect_markdown_files(project_dir, ctx.scope_facts)
        )

    @staticmethod
    def collect_markdown_files(
        project_dir: Path,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> list[Path]:
        """Collect the governed markdown surface shared by both markdown gates.

        The walker is git-scope aware, so generated/untracked trees (``.venv``,
        ``target``, ``dist``, ``build``) never enter the surface; provider and
        agent projections (``.agents``, ``.claude``, ``.gemini``, ``.beads``,
        ``.github`` agent directories) are excluded with the check vocabulary.

        Returns:
            The resulting ``list[Path]``.

        """
        inputs = u.Infra.load_codegen_inputs(project_dir).unwrap()
        return list(
            u.Infra.scope_excluded_paths(
                project_dir.resolve(),
                u.Infra.governed_scope_files(project_dir, ["*.md"], scope_facts),
                inputs.spec.markdown_exclude_globs,
            )
        )

    @classmethod
    def untracked_markdown_files(
        cls,
        project_dir: Path,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> Sequence[Path]:
        """Collect worktree Markdown that Git neither tracks nor ignores.

        Repair widens to these files so a new document is formatted before it
        is ever committed; findings stay on ``collect_markdown_files``.

        Returns:
            The untracked governed Markdown, empty outside a Git worktree.

        Raises:
            RuntimeError: If Git cannot list the worktree's changed paths.

        """
        root = project_dir.resolve()
        request = m.Infra.GitRepoRequest(repo_root=root)
        if u.Infra.git_repository_root(request).failure:
            return ()
        changed = u.Infra.git_changed_paths(request)
        if changed.failure:
            msg = changed.error or f"{root}: git changed paths failed"
            raise RuntimeError(msg)
        tracked = set(cls.collect_markdown_files(project_dir, scope_facts))
        return u.Infra.scope_excluded_paths(
            root,
            tuple(
                path
                for path in changed.value
                if path.suffix == ".md"
                and not path.is_symlink()
                and path not in tracked
            ),
            u.Infra.load_codegen_inputs(root).unwrap().spec.markdown_exclude_globs,
        )

    @staticmethod
    def projected_block_spans(
        path: Path,
        lines: Sequence[str],
    ) -> tuple[tuple[int, int], ...]:
        """Locate every declared foreign projected block in ``lines``.

        Only writers declared in ``tooling.tools.markdown.projected-blocks``
        are located; FLEXT-owned blocks are never declared there.

        Returns:
            The ``(begin, end)`` zero-based indices of each block's marker lines.

        Raises:
            ValueError: If a marker is unbalanced, mismatched, nested, or
                left unclosed.

        """
        blocks = config.Infra.tooling.tools.markdown.projected_blocks
        spans: list[tuple[int, int]] = []
        opened: tuple[p.Infra.MarkdownProjectedBlock, Mapping[str, str], int] | None
        opened = None
        for index, line in enumerate(lines):
            marker = line.strip()
            if opened is None:
                opened = FlextInfraMarkdownGateBase._projected_block_open(
                    path, index, marker, blocks
                )
                continue
            block, captured, opened_at = opened
            closing = block.end.fullmatch(marker)
            if closing is not None and all(
                closing.group(name) == value for name, value in captured.items()
            ):
                spans.append((opened_at, index))
                opened = None
                continue
            if closing is not None or any(
                other.begin.fullmatch(marker) or other.end.fullmatch(marker)
                for other in blocks
            ):
                msg = (
                    f"{path}:{index + 1}: marker {marker!r} inside the open "
                    f"{block.writer} projected block opened at line {opened_at + 1}"
                )
                raise ValueError(msg)
        if opened is not None:
            msg = (
                f"{path}:{opened[2] + 1}: {opened[0].writer} projected block "
                "is never closed"
            )
            raise ValueError(msg)
        return tuple(spans)

    @staticmethod
    def _projected_block_mask(line: str) -> str:
        """Replace one inner block line by the mask, keeping its line ending.

        Returns:
            The lint-neutral line.

        """
        body = line.rstrip("\r\n")
        return c.Infra.MARKDOWN_PROJECTED_BLOCK_MASK + line[len(body) :]

    @staticmethod
    def projected_block_view(path: Path, text: str) -> str:
        """Mask the inner lines of every declared foreign projected block.

        Marker lines stay verbatim and each inner line becomes the lint-neutral
        mask with its original ending, so line numbers and every line outside a
        block are unchanged.

        Returns:
            The lint view of ``text``.

        """
        lines = text.splitlines(keepends=True)
        view = list(lines)
        for begin, end in FlextInfraMarkdownGateBase.projected_block_spans(path, lines):
            for index in range(begin + 1, end):
                view[index] = FlextInfraMarkdownGateBase._projected_block_mask(
                    lines[index]
                )
        return "".join(view)

    @staticmethod
    def projected_block_splice(path: Path, original: str, repaired: str) -> str:
        """Restore every projected block's original lines into a repaired view.

        The repaired view is the tool's output for ``projected_block_view`` of
        ``original``. Each block must come back with its marker lines and its
        masked lines byte-identical; only lines outside the blocks may change.

        Returns:
            ``repaired`` with every block's original inner lines spliced back.

        Raises:
            ValueError: If the tool added, removed, or touched a block, its
                markers, or its masked lines.

        """
        source = original.splitlines(keepends=True)
        result = repaired.splitlines(keepends=True)
        before = FlextInfraMarkdownGateBase.projected_block_spans(path, source)
        after = FlextInfraMarkdownGateBase.projected_block_spans(path, result)
        if len(before) != len(after):
            msg = (
                f"{path}: repair changed the projected block count "
                f"from {len(before)} to {len(after)}"
            )
            raise ValueError(msg)
        rebuilt = list(result)
        for (begin, end), (new_begin, new_end) in reversed(
            tuple(zip(before, after, strict=True))
        ):
            masked = [
                FlextInfraMarkdownGateBase._projected_block_mask(line)
                for line in source[begin + 1 : end]
            ]
            if (
                result[new_begin] != source[begin]
                or result[new_end] != source[end]
                or result[new_begin + 1 : new_end] != masked
            ):
                msg = (
                    f"{path}:{begin + 1}: repair touched the projected block "
                    f"at lines {begin + 1}-{end + 1}; it cannot be spliced back"
                )
                raise ValueError(msg)
            rebuilt[new_begin + 1 : new_end] = source[begin + 1 : end]
        return "".join(rebuilt)

    @staticmethod
    def _projected_block_open(
        path: Path,
        index: int,
        marker: str,
        blocks: Sequence[p.Infra.MarkdownProjectedBlock],
    ) -> tuple[p.Infra.MarkdownProjectedBlock, Mapping[str, str], int] | None:
        """Open the declared block whose begin marker is ``marker``.

        Returns:
            The opened block, its pairing captures, and its zero-based line
            index, or ``None``.

        Raises:
            ValueError: If ``marker`` ends a block that was never opened.

        """
        for block in blocks:
            beginning = block.begin.fullmatch(marker)
            if beginning is not None:
                captured: Mapping[str, str] = {
                    name: value
                    for name, value in beginning.groupdict().items()
                    if name in block.end.groupindex and value is not None
                }
                return block, captured, index
        for block in blocks:
            if block.end.fullmatch(marker):
                msg = (
                    f"{path}:{index + 1}: {block.writer} end marker {marker!r} "
                    "closes no open projected block"
                )
                raise ValueError(msg)
        return None

    @staticmethod
    def projected_block_stdin_batch(
        project_dir: Path,
        targets: Sequence[str],
    ) -> str:
        """Encode every target's lint view as rumdl ``--stdin-batch`` input.

        Each target keeps its own path, so diagnostics name the real file and
        line; its content is the projected-block view of the file on disk.

        Returns:
            NUL-delimited path/content pairs for every target.

        Raises:
            ValueError: If a target's content carries the batch delimiter.

        """
        separator = c.Infra.MARKDOWN_STDIN_BATCH_SEPARATOR
        pairs: list[str] = []
        for target in targets:
            path = project_dir / target
            text = path.read_text(c.DEFAULT_ENCODING)
            if separator in text:
                msg = f"{path}: content carries the rumdl stdin-batch delimiter"
                raise ValueError(msg)
            view = FlextInfraMarkdownGateBase.projected_block_view(path, text)
            pairs.extend((target, separator, view, separator))
        return "".join(pairs)

    @staticmethod
    def _projected_targets(
        project_dir: Path,
        targets: Sequence[str],
    ) -> frozenset[str]:
        """Select the targets that carry at least one declared projected block.

        Returns:
            The targets routed through the per-file projected round trip.

        """
        selected: set[str] = set()
        for target in targets:
            path = project_dir / target
            lines = path.read_text(c.DEFAULT_ENCODING).splitlines(keepends=True)
            if FlextInfraMarkdownGateBase.projected_block_spans(path, lines):
                selected.add(target)
        return frozenset(selected)

    def _projected_command(self, project_dir: Path, target: str) -> Sequence[str]:
        """Build the single-file rumdl ``--stdin`` pass for a projected file.

        Raises:
            NotImplementedError: If the concrete gate declares no stdin pass.

        """
        del project_dir, target
        msg = f"{type(self).__name__}._projected_command() must be implemented"
        raise NotImplementedError(msg)

    def _projected_completed(self, result: p.Cli.CommandOutput) -> bool:
        """Tell whether rumdl completed the stdin pass with a usable output.

        Returns:
            ``True`` for a success or a declared findings status.

        """
        outcome = result.outcome
        return (
            not outcome.timed_out
            and outcome.forwarded_signal is None
            and (
                u.Cli.process_succeeded(outcome)
                or outcome.raw_return_code in self._findings_exit_codes()
            )
        )

    def _projected_round_trip(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        target: str,
    ) -> tuple[p.Cli.AtomicFileState, str, p.Cli.CommandOutput, str]:
        """Run the stdin pass over one file's lint view and splice its blocks.

        The file is observed once through the atomic reader, so its state is
        the witness a later publication guards. Only the tool's diagnostics are
        kept as the command output; its stdout is the repaired view.

        Returns:
            The observed state, its text, the diagnostics-only output, and the
            spliced text (the original text when the pass did not complete).

        Raises:
            RuntimeError: If the file cannot be observed.

        """
        path = project_dir / target
        captured = u.Cli.atomic_read_binary_file_state(path, required=True)
        if captured.failure:
            msg = captured.error or f"{path}: projected file is unreadable"
            raise RuntimeError(msg)
        state = captured.value
        content = state.content
        if content is None:
            msg = f"{path}: projected file has no content"
            raise RuntimeError(msg)
        original = content.decode(c.DEFAULT_ENCODING)
        result = self._run(
            self._projected_command(project_dir, target),
            project_dir,
            ctx,
            input_data=self.projected_block_view(path, original),
        )
        diagnostics = m.Cli.CommandOutput(
            outcome=m.Cli.ProcessOutcome.model_validate(
                result.outcome, from_attributes=True
            ),
            duration=result.duration,
            stderr=result.stderr,
        )
        if not self._projected_completed(result):
            return state, original, diagnostics, original
        spliced = self.projected_block_splice(path, original, result.stdout)
        return state, original, diagnostics, spliced

    @staticmethod
    def _projected_owner(path: Path, owners: Sequence[Path]) -> Path:
        """Return the innermost project root that contains ``path``.

        Returns:
            The owning project root.

        Raises:
            ValueError: If no owner contains ``path``.

        """
        physical = path.resolve()
        containing = [
            owner.resolve()
            for owner in owners
            if physical.is_relative_to(owner.resolve())
        ]
        if not containing:
            msg = f"{path}: projected file is outside every repaired project"
            raise ValueError(msg)
        return max(containing, key=lambda owner: len(owner.parts))

    @override
    def _execute_fix_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
        started: float,
        lock_owners: Sequence[Path],
    ) -> p.Infra.GateExecution:
        """Repair projected files through their view; the rest in one disk pass.

        A file without a declared projected block keeps the single native
        disk invocation. A file with one is repaired from its lint view on
        stdin, its blocks are spliced back byte-identical, and the result is
        published through the codegen file publisher against the observed
        file state, so no foreign block is ever rewritten.

        Returns:
            One execution covering every target.

        Raises:
            RuntimeError: If the publisher rejects the repaired files.

        """
        failed = self._repair_untracked(ctx, started, lock_owners)
        if failed is not None:
            return failed
        projected = self._projected_targets(project_dir, targets)
        if not projected:
            return super()._execute_fix_command(
                project_dir, ctx, targets, started, lock_owners
            )
        executions: list[p.Infra.GateExecution] = []
        plain = tuple(target for target in targets if target not in projected)
        if plain:
            executions.append(
                super()._execute_fix_command(
                    project_dir, ctx, plain, started, lock_owners
                )
            )
        plans: dict[Path, list[p.Infra.CodegenFilePlan]] = {}
        for target in targets:
            if target not in projected:
                continue
            state, original, diagnostics, spliced = self._projected_round_trip(
                project_dir, ctx, target
            )
            executions.append(
                self._parsed_gate_execution(project_dir, ctx, diagnostics, started)
            )
            if spliced == original:
                continue
            owner = self._projected_owner(state.path, lock_owners)
            plans.setdefault(owner, []).append(
                m.Infra.CodegenFilePlan(
                    project=owner,
                    path=state.path,
                    before=state,
                    desired_content=spliced.encode(c.DEFAULT_ENCODING),
                    desired_mode=state.mode,
                )
            )
        for owner, owned in plans.items():
            published = u.Infra.publish_codegen_plans(owner, owned)
            if published.failure:
                msg = published.error or f"{owner}: projected repair publication failed"
                raise RuntimeError(msg)
        return self._merged_execution(project_dir, ctx, started, executions)

    def _repair_untracked(
        self,
        ctx: p.Infra.GateContext,
        started: float,
        lock_owners: Sequence[Path],
    ) -> p.Infra.GateExecution | None:
        """Repair each owner's untracked Markdown without reporting it.

        Residual findings stay with ``check`` over tracked files; only a native
        tool error fails the repair.

        Returns:
            The failed native execution, or ``None`` when every pass completed.

        """
        for owner in lock_owners:
            untracked = self.untracked_markdown_files(owner, ctx.scope_facts)
            if not untracked:
                continue
            widened = super()._execute_fix_command(
                owner,
                ctx,
                tuple(path.as_posix() for path in untracked),
                started,
                (owner,),
            )
            if widened.outcome is c.Infra.ToolOutcome.ERROR:
                return widened
        return None

    def _merged_execution(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        started: float,
        executions: Sequence[p.Infra.GateExecution],
    ) -> p.Infra.GateExecution:
        """Join the disk pass and the projected passes into one execution.

        Returns:
            The single execution, or one carrying every pass's findings, the
            most severe outcome, and an interrupted pass's process if any.

        """
        if len(executions) == 1:
            return executions[0]
        outcomes = {execution.outcome for execution in executions}
        outcome = next(
            candidate
            for candidate in (
                c.Infra.ToolOutcome.ERROR,
                c.Infra.ToolOutcome.FINDINGS,
                c.Infra.ToolOutcome.CLEAN,
            )
            if candidate in outcomes
        )
        merged = self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=all(execution.result.passed for execution in executions),
                outcome=outcome,
                issues=tuple(
                    issue for execution in executions for issue in execution.issues
                ),
                raw_output="\n".join(
                    execution.raw_output
                    for execution in executions
                    if execution.raw_output
                ),
                started=started,
            ),
            ctx,
        )
        return merged.model_copy(
            update={
                "process": next(
                    (
                        execution.process
                        for execution in executions
                        if execution.interrupted
                    ),
                    executions[0].process,
                )
            }
        )

    @staticmethod
    @override
    def _findings_exit_codes() -> tuple[int, ...]:
        """Exit statuses with which rumdl reports its findings.

        Returns:
            The findings statuses declared for rumdl in the tooling config.

        """
        return config.Infra.tooling.tools.markdown.findings_exit_codes

    @staticmethod
    def _resolve_config_args(project_dir: Path) -> Sequence[str]:
        """Resolve only the repository-local markdown settings owner.

        Returns:
            The resulting ``Sequence[str]``.

        """
        config_path = project_dir / c.Infra.MARKDOWN_CONFIG_FILENAME
        # An absent explicit config is a native tool error, never a request for
        # defaults. Keeping it native preserves attributed check/repair reports.
        return ["--config", str(config_path.resolve())]

    def _rumdl_command(
        self,
        project_dir: Path,
        subcommand: str,
        targets: Sequence[str],
        *mode_args: str,
    ) -> Sequence[str]:
        """Keep every markdown gate on the same rumdl invocation contract.

        Returns:
            The rumdl ``subcommand`` invocation over ``targets``.

        """
        return self._python_console_script_command(
            c.Infra.RUMDL,
            subcommand,
            *mode_args,
            "--no-cache",
            "--color",
            "never",
            "--output-format",
            "text",
            "--deny-config-warnings",
            *self._resolve_config_args(project_dir),
            *targets,
        )

    @override
    def selected_for(self, project_dir: Path, ctx: p.Infra.GateContext) -> bool:
        """Only a project with governed Markdown selects a Markdown gate.

        Returns:
            The resulting ``bool``.

        """
        return bool(self.collect_markdown_files(project_dir, ctx.scope_facts))

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> Sequence[str]:
        """Return the governed Markdown paths relative to their repository.

        Returns:
            The governed Markdown paths relative to their repository.

        """
        return [
            str(path.relative_to(project_dir))
            for path in self.collect_markdown_files(project_dir, ctx.scope_facts)
        ]


__all__: list[str] = ["FlextInfraMarkdownGateBase"]
