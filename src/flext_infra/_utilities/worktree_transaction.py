"""Isolated command transactions built on the canonical ``u.Infra`` Git owner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from uuid import uuid4

from flext_cli import u
from flext_core import r
from flext_infra import c, config, m, p, t
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope


class FlextInfraUtilitiesWorktreeTransaction:
    """Execute fix and codegen mutations in complete detached worktrees."""

    @staticmethod
    def _repository_exclusions(
        repository_path: Path, submodule_paths: t.SequenceOf[Path]
    ) -> t.SequenceOf[Path]:
        """Resolve nested submodule exclusions relative to one repository."""
        exclusions: t.MutableSequenceOf[Path] = []
        for submodule_path in submodule_paths:
            if repository_path == Path():
                exclusions.append(submodule_path)
                continue
            try:
                relative_path = submodule_path.relative_to(repository_path)
            except ValueError:
                continue
            if relative_path != Path():
                exclusions.append(relative_path)
        return tuple(exclusions)

    @staticmethod
    def _submodule_in_scope(submodule: Path, scoped_paths: t.SequenceOf[Path]) -> bool:
        """Return whether a submodule falls under any scoped path."""
        if not scoped_paths:
            return True
        return any(
            submodule == scoped or submodule.is_relative_to(scoped)
            for scoped in scoped_paths
        )

    @classmethod
    def _create_complete_worktree(
        cls,
        workspace_root: Path,
        worktree_root: Path,
        transaction_id: str,
        selected_repositories: t.StrSequence,
    ) -> p.Result[t.SequenceOf[p.Infra.RepositoryWorktree]]:
        """Materialize every repository but snapshot dirty state only in scope."""
        submodules_result = FlextInfraUtilitiesGitScope.git_submodule_paths(
            workspace_root
        )
        if submodules_result.failure:
            return r[t.SequenceOf[p.Infra.RepositoryWorktree]].fail(
                submodules_result.error or "failed to discover workspace repositories"
            )
        submodule_paths = tuple(submodules_result.value)
        repository_paths = (Path(), *submodule_paths)
        selected_paths = (
            tuple(Path(path) for path in selected_repositories)
            if selected_repositories
            else repository_paths
        )
        invalid_paths = tuple(
            path
            for path in selected_paths
            if path.is_absolute() or ".." in path.parts or path not in repository_paths
        )
        if invalid_paths:
            invalid_text = ", ".join(path.as_posix() for path in invalid_paths)
            return r[t.SequenceOf[p.Infra.RepositoryWorktree]].fail(
                f"transaction selected unknown repositories: {invalid_text}"
            )
        created: t.MutableSequenceOf[p.Infra.RepositoryWorktree] = []
        for relative_path in repository_paths:
            source_root = (
                workspace_root
                if relative_path == Path()
                else workspace_root / relative_path
            )
            isolated_root = (
                worktree_root
                if relative_path == Path()
                else worktree_root / relative_path
            )
            add_result = FlextInfraUtilitiesGitScope.git_add_detached_worktree(
                source_root, isolated_root
            )
            if add_result.failure:
                cls._cleanup_worktrees(created, worktree_root)
                return r[t.SequenceOf[p.Infra.RepositoryWorktree]].fail(
                    add_result.error or f"failed to create worktree for {relative_path}"
                )
            repository = m.Infra.RepositoryWorktree(
                relative_path=relative_path.as_posix(),
                source_root=source_root,
                worktree_root=isolated_root,
                checkpoint_sha=add_result.value,
            )
            created.append(repository)
            if relative_path not in selected_paths:
                continue
            copy_result = FlextInfraUtilitiesGitScope.git_copy_worktree_state(
                source_root,
                isolated_root,
                excluded=cls._repository_exclusions(relative_path, submodule_paths),
            )
            if copy_result.failure:
                cls._cleanup_worktrees(created, worktree_root)
                return r[t.SequenceOf[p.Infra.RepositoryWorktree]].fail(
                    copy_result.error
                    or f"failed to reproduce dirty state for {relative_path}"
                )
        checkpointed: t.MutableSequenceOf[p.Infra.RepositoryWorktree] = []
        for repository in sorted(
            created, key=lambda item: len(Path(item.relative_path).parts), reverse=True
        ):
            checkpoint_result = FlextInfraUtilitiesGitScope.git_checkpoint_worktree(
                repository.worktree_root,
                message=(
                    "chore: isolated checkpoint "
                    f"{transaction_id} {repository.relative_path}"
                ),
            )
            if checkpoint_result.failure:
                cls._cleanup_worktrees(created, worktree_root)
                return r[t.SequenceOf[p.Infra.RepositoryWorktree]].fail(
                    checkpoint_result.error
                    or f"failed to checkpoint {repository.relative_path}"
                )
            checkpointed.append(
                m.Infra.RepositoryWorktree(
                    relative_path=repository.relative_path,
                    source_root=repository.source_root,
                    worktree_root=repository.worktree_root,
                    checkpoint_sha=checkpoint_result.value,
                )
            )
        return r[t.SequenceOf[p.Infra.RepositoryWorktree]].ok(
            tuple(
                sorted(
                    checkpointed,
                    key=lambda item: (
                        len(Path(item.relative_path).parts),
                        item.relative_path,
                    ),
                )
            )
        )

    @staticmethod
    def _source_roots(worktree_root: Path) -> t.SequenceOf[Path]:
        """Resolve productive source roots inside the isolated workspace."""
        roots: t.MutableSequenceOf[Path] = []
        root_source = worktree_root / c.Infra.DEFAULT_SRC_DIR
        if root_source.is_dir():
            roots.append(root_source)
        for child in sorted(worktree_root.iterdir()):
            source_root = child / c.Infra.DEFAULT_SRC_DIR
            if child.is_dir() and source_root.is_dir():
                roots.append(source_root)
        return tuple(roots)

    @classmethod
    def _selected_source_roots(
        cls, worktree_root: Path, selected_repositories: t.StrSequence
    ) -> t.SequenceOf[Path]:
        """Resolve source roots participating in selected validation phases."""
        if not selected_repositories:
            return cls._source_roots(worktree_root)
        roots: t.MutableSequenceOf[Path] = []
        for relative_path in selected_repositories:
            repository_root = (
                worktree_root
                if relative_path == Path().as_posix()
                else worktree_root / relative_path
            )
            source_root = repository_root / c.Infra.DEFAULT_SRC_DIR
            if source_root.is_dir():
                roots.append(source_root)
        return tuple(roots)

    @classmethod
    def _transaction_environment(cls, worktree_root: Path) -> t.StrMapping:
        """Build the isolated source and recursion-guard environment."""
        # mro-qz1m (codex): controller code/config owns generation policy while
        # detached consumer source roots remain importable for validation.
        controller_source = Path(__file__).resolve().parents[2]
        python_path = c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
            str(path)
            for path in dict.fromkeys((
                controller_source,
                *cls._source_roots(worktree_root),
            ))
        )
        return {
            config.Infra.worktree_transaction.environment_variable: (
                config.Infra.worktree_transaction.active_value
            ),
            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: python_path,
            c.Infra.ORCHESTRATOR_ENV_PYTHONDONTWRITEBYTECODE: "1",
        }

    @staticmethod
    def _lint_counts(tool: str, output: str) -> tuple[int, int]:
        """Extract comparable error and warning counts from lint output."""
        if tool == "ruff":
            errors = sum(
                int(match.group(1))
                for match in re.finditer(r"(?m)^\s*(\d+)\s+[A-Z][A-Z0-9]+\s+", output)
            )
            return (errors, 0)
        error_matches = tuple(
            int(match.group(1)) for match in re.finditer(r"\b(\d+)\s+errors?\b", output)
        )
        errors = error_matches[-1] if error_matches else 0
        warning_matches = tuple(
            int(match.group(1))
            for match in re.finditer(r"\b(\d+)\s+warnings?\b", output)
        )
        warnings = warning_matches[-1] if warning_matches else 0
        return (errors, warnings)

    @classmethod
    def _lint_snapshot(
        cls,
        worktree_root: Path,
        tool: str,
        command: t.StrSequence,
        environment: t.StrMapping,
        timeout_seconds: int,
    ) -> p.Infra.LintSnapshot:
        """Capture one lint command without hiding a non-zero exit status."""
        lint_command = cls._relocate_lint_command(command, worktree_root)
        if tool == c.Infra.RUFF:
            lint_command = cls.normalize_ruff_lint_command(
                lint_command, worktree_root / "pyproject.toml"
            )
        result = u.Cli.run_raw(
            lint_command, cwd=worktree_root, env=environment, timeout=timeout_seconds
        )
        if result.failure:
            return m.Infra.LintSnapshot(
                tool=tool,
                exit_code=1,
                errors=1,
                output=result.error or "lint command execution failed",
            )
        command_output = result.value
        combined_output = "\n".join(
            part for part in (command_output.stdout, command_output.stderr) if part
        )
        errors, warnings = cls._lint_counts(tool, combined_output)
        if command_output.exit_code != 0 and errors == 0:
            errors = 1
        return m.Infra.LintSnapshot(
            tool=tool,
            exit_code=command_output.exit_code,
            errors=errors,
            warnings=warnings,
            output=combined_output,
        )

    @staticmethod
    def _relocate_lint_command(
        command: t.StrSequence, worktree_root: Path
    ) -> t.StrSequence:
        """Resolve relative lint config paths against the isolated worktree."""
        relocated: t.MutableSequenceOf[str] = []
        config_option = False
        for argument in command:
            if config_option:
                candidate = Path(argument)
                relocated.append(
                    str(worktree_root / candidate)
                    if not candidate.is_absolute()
                    else argument
                )
                config_option = False
                continue
            relocated.append(argument)
            config_option = argument == "--config"
        return tuple(relocated)

    @staticmethod
    def normalize_ruff_lint_command(
        command: t.StrSequence, consumer_config: Path
    ) -> t.StrSequence:
        """Use the invoking Ruff module with exactly one consumer config option."""
        normalized: t.MutableSequenceOf[str] = [sys.executable, "-m", "ruff"]
        arguments = iter(command[1:])
        for argument in arguments:
            if argument == "--config":
                next(arguments, None)
                continue
            if argument.startswith("--config="):
                continue
            normalized.append(argument)
        normalized.append(f"--config={consumer_config}")
        return tuple(normalized)

    @classmethod
    def _lint_snapshots(
        cls,
        worktree_root: Path,
        environment: t.StrMapping,
        timeout_seconds: int,
        selected_repositories: t.StrSequence,
    ) -> t.VariadicTuple[p.Infra.LintSnapshot]:
        """Capture canonical lint commands for selected repositories only."""
        targets = selected_repositories or (Path().as_posix(),)
        return tuple(
            cls._lint_snapshot(
                worktree_root,
                lint_command.tool,
                # mro-wkii.17.26 (codex): the detached worktree deliberately has
                # no copied .venv; Pyrefly must query the caller interpreter.
                (
                    *lint_command.command,
                    *targets,
                    "--python-interpreter-path",
                    sys.executable,
                )
                if lint_command.tool == c.Infra.PYREFLY
                else tuple(
                    scoped_argument
                    for argument in lint_command.command
                    for scoped_argument in (
                        targets
                        if lint_command.tool == c.Infra.RUFF
                        and argument == Path().as_posix()
                        else (argument,)
                    )
                ),
                environment,
                timeout_seconds,
            )
            for lint_command in config.Infra.worktree_transaction.lint_commands
        )

    @classmethod
    def _import_probe(
        cls,
        worktree_root: Path,
        environment: t.StrMapping,
        timeout_seconds: int,
        selected_repositories: t.StrSequence,
    ) -> p.Cli.CommandOutput:
        """Fresh-import productive packages owned by the selected repositories."""
        packages = tuple(
            sorted({
                package_dir.name
                for source_root in cls._selected_source_roots(
                    worktree_root, selected_repositories
                )
                for package_dir in source_root.iterdir()
                if package_dir.is_dir()
                and package_dir.name.isidentifier()
                and (package_dir / c.Infra.INIT_PY).is_file()
            })
        )
        script = (
            "import importlib\n"
            f"packages = {packages!r}\n"
            "for package in packages:\n"
            "    importlib.import_module(package)\n"
            "print(f'imported {len(packages)} packages')\n"
        )
        result = u.Cli.run_raw(
            (sys.executable, "-c", script),
            cwd=worktree_root,
            env=environment,
            timeout=timeout_seconds,
        )
        if result.success:
            return result.value
        return m.Cli.CommandOutput(
            exit_code=1, stderr=result.error or "fresh import execution failed"
        )

    @staticmethod
    def _relocate_command(
        command: t.StrSequence, source_root: Path, worktree_root: Path
    ) -> t.StrSequence:
        """Relocate absolute workspace arguments into the isolated worktree."""
        source_text = str(source_root)
        target_text = str(worktree_root)
        return tuple(
            argument.replace(source_text, target_text, 1)
            if source_text in argument
            else argument
            for argument in command
        )

    @staticmethod
    def _lint_regressed(
        before: t.SequenceOf[p.Infra.LintSnapshot],
        after: t.SequenceOf[p.Infra.LintSnapshot],
    ) -> bool:
        """Return whether any lint tool gained diagnostics or newly failed."""
        return any(
            after_item.errors > before_item.errors
            or after_item.warnings > before_item.warnings
            or (after_item.exit_code != 0 and before_item.exit_code == 0)
            for before_item, after_item in zip(before, after, strict=True)
        )

    @staticmethod
    def _repository_deltas(
        repositories: t.SequenceOf[p.Infra.RepositoryWorktree],
    ) -> p.Result[t.SequenceOf[p.Infra.RepositoryDelta]]:
        """Capture operation-only deltas from every isolated repository."""
        deltas: t.MutableSequenceOf[p.Infra.RepositoryDelta] = []
        for repository in repositories:
            result = FlextInfraUtilitiesGitScope.git_repository_delta(repository)
            if result.failure:
                return r[t.SequenceOf[p.Infra.RepositoryDelta]].fail(
                    result.error
                    or f"failed to capture delta for {repository.relative_path}"
                )
            deltas.append(result.value)
        return r[t.SequenceOf[p.Infra.RepositoryDelta]].ok(tuple(deltas))

    @staticmethod
    def _check_patches(deltas: t.SequenceOf[p.Infra.RepositoryDelta]) -> p.Result[bool]:
        """Dry-run every patch before any source worktree mutation."""
        for delta in deltas:
            model_delta = m.Infra.RepositoryDelta.model_validate(delta)
            result = FlextInfraUtilitiesGitScope.git_check_isolated_patch(model_delta)
            if result.failure:
                return r[bool].fail(
                    f"{delta.relative_path}: {result.error or 'patch check failed'}"
                )
        return r[bool].ok(True)

    @staticmethod
    def _apply_patches(deltas: t.SequenceOf[p.Infra.RepositoryDelta]) -> p.Result[bool]:
        """Apply every previously checked patch, deepest repositories first."""
        ordered = sorted(
            deltas, key=lambda delta: len(Path(delta.relative_path).parts), reverse=True
        )
        for delta in ordered:
            model_delta = m.Infra.RepositoryDelta.model_validate(delta)
            result = FlextInfraUtilitiesGitScope.git_apply_patch(model_delta)
            if result.failure:
                return r[bool].fail(
                    f"{delta.relative_path}: {result.error or 'patch apply failed'}"
                )
        return r[bool].ok(True)

    @classmethod
    def _cleanup_worktrees(
        cls, repositories: t.SequenceOf[p.Infra.RepositoryWorktree], worktree_root: Path
    ) -> p.Result[bool]:
        """Remove only transaction-owned worktrees and their remaining directory."""
        failures: t.MutableSequenceOf[str] = []
        for repository in sorted(
            repositories,
            key=lambda item: len(Path(item.relative_path).parts),
            reverse=True,
        ):
            result = FlextInfraUtilitiesGitScope.git_remove_worktree(
                repository.source_root, repository.worktree_root
            )
            if result.failure:
                failures.append(
                    f"{repository.relative_path}: {result.error or 'cleanup failed'}"
                )
        if worktree_root.exists():
            remove_result = u.Cli.files_remove_directory(worktree_root)
            if remove_result.failure:
                failures.append(
                    remove_result.error or f"failed to remove {worktree_root}"
                )
        if failures:
            return r[bool].fail("; ".join(failures))
        return r[bool].ok(True)

    @classmethod
    def execute_worktree_transaction(
        cls, request: p.Infra.WorktreeTransactionRequest
    ) -> p.Result[p.Infra.WorktreeTransactionReport]:
        """Execute, validate, optionally apply, and always remove one worktree."""
        workspace_root = request.workspace_root.resolve()
        transaction_id = uuid4().hex
        worktree_root = (
            workspace_root
            / config.Infra.worktree_transaction.root
            / f"transaction-{transaction_id}"
        )
        selection_text = ",".join(request.selected_repositories) or "workspace"
        u.Cli.info(
            f"worktree transaction {transaction_id}: materializing {selection_text}"
        )
        create_result = cls._create_complete_worktree(
            workspace_root, worktree_root, transaction_id, request.selected_repositories
        )
        if create_result.failure:
            return r[p.Infra.WorktreeTransactionReport].fail(
                create_result.error or "failed to create complete worktree"
            )
        repositories = create_result.value
        report_result: p.Result[p.Infra.WorktreeTransactionReport]
        try:
            report_result = cls._execute_isolated(
                request,
                transaction_id=transaction_id,
                worktree_root=worktree_root,
                repositories=repositories,
            )
        finally:
            u.Cli.info(f"worktree transaction {transaction_id}: cleaning up")
            cleanup_result = cls._cleanup_worktrees(repositories, worktree_root)
        if cleanup_result.failure:
            return r[p.Infra.WorktreeTransactionReport].fail(
                cleanup_result.error or "failed to remove transaction worktree"
            )
        return report_result

    @classmethod
    def _execute_isolated(
        cls,
        request: p.Infra.WorktreeTransactionRequest,
        *,
        transaction_id: str,
        worktree_root: Path,
        repositories: t.SequenceOf[p.Infra.RepositoryWorktree],
    ) -> p.Result[p.Infra.WorktreeTransactionReport]:
        """Run and evaluate the command inside an already checkpointed worktree."""
        environment = cls._transaction_environment(worktree_root)
        u.Cli.info(f"worktree transaction {transaction_id}: lint before")
        lint_before = cls._lint_snapshots(
            worktree_root,
            environment,
            request.timeout_seconds,
            request.selected_repositories,
        )
        relocated = cls._relocate_command(
            request.command, request.workspace_root.resolve(), worktree_root
        )
        u.Cli.info(f"worktree transaction {transaction_id}: command")
        command_result = u.Cli.run_raw(
            (sys.executable, "-m", "flext_infra", *relocated),
            cwd=worktree_root,
            env=environment,
            timeout=request.timeout_seconds,
        )
        if command_result.failure:
            command_output = m.Cli.CommandOutput(
                exit_code=1,
                stderr=command_result.error or "isolated command execution failed",
            )
        else:
            command_output = command_result.value
        u.Cli.info(f"worktree transaction {transaction_id}: lint after")
        lint_after = cls._lint_snapshots(
            worktree_root,
            environment,
            request.timeout_seconds,
            request.selected_repositories,
        )
        u.Cli.info(f"worktree transaction {transaction_id}: import probe")
        import_probe = cls._import_probe(
            worktree_root,
            environment,
            request.timeout_seconds,
            request.selected_repositories,
        )
        u.Cli.info(f"worktree transaction {transaction_id}: repository deltas")
        deltas_result = cls._repository_deltas(repositories)
        if deltas_result.failure:
            return r[p.Infra.WorktreeTransactionReport].fail(
                deltas_result.error or "failed to capture repository deltas"
            )
        deltas = deltas_result.value
        selected_deltas = tuple(
            delta
            for delta in deltas
            if not request.selected_repositories
            or delta.relative_path in request.selected_repositories
        )
        out_of_scope = tuple(
            delta.relative_path
            for delta in deltas
            if request.selected_repositories
            and delta.relative_path not in request.selected_repositories
            and delta.patch
        )
        breakage = (
            command_output.exit_code != 0
            or import_probe.exit_code != 0
            or (
                not request.allow_lint_regression
                and cls._lint_regressed(lint_before, lint_after)
            )
            or bool(out_of_scope)
        )
        patch_check = cls._check_patches(selected_deltas)
        if patch_check.failure:
            breakage = True
        applied = False
        apply_error = ""
        if request.apply_patch and not breakage:
            apply_result = cls._apply_patches(selected_deltas)
            applied = apply_result.success
            apply_error = apply_result.error or "" if apply_result.failure else ""
            breakage = apply_result.failure
        summary = (
            f"breakage={'yes' if breakage else 'no'}; "
            f"patch-check={'ok' if patch_check.success else patch_check.error}; "
            f"applied={'yes' if applied else 'no'}"
        )
        if apply_error:
            summary = f"{summary}; apply-error={apply_error}"
        if out_of_scope:
            summary = f"{summary}; out-of-scope={','.join(out_of_scope)}"
        return r[p.Infra.WorktreeTransactionReport].ok(
            m.Infra.WorktreeTransactionReport(
                transaction_id=transaction_id,
                command=relocated,
                worktree_root=worktree_root,
                command_output=command_output,
                import_probe=import_probe,
                lint_before=lint_before,
                lint_after=lint_after,
                repositories=selected_deltas,
                breakage_detected=breakage,
                applied=applied,
                summary=summary,
            )
        )

    @staticmethod
    def render_worktree_transaction_report(
        report: p.Infra.WorktreeTransactionReport,
    ) -> str:
        """Render command evidence, lint deltas, and generated patches."""
        lines: t.MutableSequenceOf[str] = [
            f"transaction: {report.transaction_id}",
            f"command exit: {report.command_output.exit_code}",
            f"import exit: {report.import_probe.exit_code}",
            report.summary,
        ]
        # mro-45r9: a fail-closed transaction must expose its decisive output.
        for label, output in (
            ("command stdout", report.command_output.stdout),
            ("command stderr", report.command_output.stderr),
            ("import stdout", report.import_probe.stdout),
            ("import stderr", report.import_probe.stderr),
        ):
            if output.strip():
                lines.extend((f"{label}:", output.rstrip()))
        lines.append("lint delta:")
        for before, after in zip(report.lint_before, report.lint_after, strict=True):
            lines.append(
                f"  {before.tool}: errors {before.errors}->{after.errors} "
                f"({after.errors - before.errors:+d}), warnings "
                f"{before.warnings}->{after.warnings} "
                f"({after.warnings - before.warnings:+d})"
            )
            if (
                after.errors > before.errors
                or after.warnings > before.warnings
                or (after.exit_code != 0 and before.exit_code == 0)
            ):
                lines.extend((f"{after.tool} diagnostics after command:", after.output))
        for repository in report.repositories:
            if not repository.patch:
                continue
            # mro-wkii.17.26 (codex): decode verified patch bytes only at text egress.
            lines.extend((
                f"diff -- repository {repository.relative_path}",
                repository.patch.decode(c.Cli.ENCODING_DEFAULT),
            ))
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesWorktreeTransaction"]
