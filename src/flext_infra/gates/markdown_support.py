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
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, config, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from flext_infra import m, p


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
        ctx: m.Infra.GateContext,
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

    @staticmethod
    def projected_block_view(path: Path, text: str) -> str:
        """Mask the inner lines of every declared foreign projected block.

        Marker lines stay verbatim and each inner line becomes the lint-neutral
        mask with its original ending, so line numbers and every line outside a
        block are unchanged. Only writers declared in
        ``tooling.tools.markdown.projected-blocks`` are masked.

        Returns:
            The lint view of ``text``.

        Raises:
            ValueError: If a marker is unbalanced, mismatched, nested, or
                left unclosed.

        """
        blocks = config.Infra.tooling.tools.markdown.projected_blocks
        view: list[str] = []
        opened: tuple[m.Infra.MarkdownProjectedBlock, Mapping[str, str], int] | None
        opened = None
        for number, line in enumerate(text.splitlines(keepends=True), start=1):
            marker = line.strip()
            if opened is None:
                opened = FlextInfraMarkdownGateBase._projected_block_open(
                    path, number, marker, blocks
                )
                view.append(line)
                continue
            block, captured, opened_at = opened
            closing = block.end.fullmatch(marker)
            if closing is not None and all(
                closing.group(name) == value for name, value in captured.items()
            ):
                opened = None
                view.append(line)
                continue
            if closing is not None or any(
                other.begin.fullmatch(marker) or other.end.fullmatch(marker)
                for other in blocks
            ):
                msg = (
                    f"{path}:{number}: marker {marker!r} inside the open "
                    f"{block.writer} projected block opened at line {opened_at}"
                )
                raise ValueError(msg)
            body = line.rstrip("\r\n")
            view.append(c.Infra.MARKDOWN_PROJECTED_BLOCK_MASK + line[len(body) :])
        if opened is not None:
            msg = (
                f"{path}:{opened[2]}: {opened[0].writer} projected block "
                "is never closed"
            )
            raise ValueError(msg)
        return "".join(view)

    @staticmethod
    def _projected_block_open(
        path: Path,
        number: int,
        marker: str,
        blocks: Sequence[m.Infra.MarkdownProjectedBlock],
    ) -> tuple[m.Infra.MarkdownProjectedBlock, Mapping[str, str], int] | None:
        """Open the declared block whose begin marker is ``marker``.

        Returns:
            The opened block, its pairing captures, and its line, or ``None``.

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
                return block, captured, number
        for block in blocks:
            if block.end.fullmatch(marker):
                msg = (
                    f"{path}:{number}: {block.writer} end marker {marker!r} "
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
    def selected_for(self, project_dir: Path, ctx: m.Infra.GateContext) -> bool:
        """Only a project with governed Markdown selects a Markdown gate.

        Returns:
            The resulting ``bool``.

        """
        return bool(self.collect_markdown_files(project_dir, ctx.scope_facts))

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
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
