"""Isolated command transactions built on the canonical ``u.Infra`` Git owner."""

from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from flext_cli import u
from flext_core import r
from flext_infra import c, m, t
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope

if TYPE_CHECKING:
    from flext_infra import p


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
        scoped_paths: t.SequenceOf[Path] = (),
    ) -> p.Result[t.SequenceOf[m.Infra.RepositoryWorktree]]:
        """Reproduce root plus in-scope submodule state, then checkpoint it.

        When ``scoped_paths`` is non-empty, only the root repository and the
        submodules under those paths are isolated; the full workspace is only
        snapshotted when scope is unknown (empty), so the whole monorepo is
        never checkpointed for an operation that touches one project.
        """
        submodules_result = FlextInfraUtilitiesGitScope.git_submodule_paths(
            workspace_root
        )
        if submodules_result.failure:
            return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                submodules_result.error or "failed to discover workspace repositories"
            )
        submodule_paths = tuple(
            submodule
            for submodule in submodules_result.value
            if cls._submodule_in_scope(submodule, scoped_paths)
        )
        repository_paths = (Path(), *submodule_paths)
        created: t.MutableSequenceOf[m.Infra.RepositoryWorktree] = []
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
                return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                    add_result.error or f"failed to create worktree for {relative_path}"
                )
            repository = m.Infra.RepositoryWorktree(
                relative_path=relative_path.as_posix(),
                source_root=source_root,
                worktree_root=isolated_root,
                checkpoint_sha=add_result.value,
            )
            created.append(repository)
            copy_result = FlextInfraUtilitiesGitScope.git_copy_worktree_state(
                source_root,
                isolated_root,
                excluded=cls._repository_exclusions(relative_path, submodule_paths),
            )
            if copy_result.failure:
                cls._cleanup_worktrees(created, worktree_root)
                return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                    copy_result.error
                    or f"failed to reproduce dirty state for {relative_path}"
                )
        checkpointed: t.MutableSequenceOf[m.Infra.RepositoryWorktree] = []
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
                return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
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
        return r[t.SequenceOf[m.Infra.RepositoryWorktree]].ok(
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
    def _transaction_environment(cls, worktree_root: Path) -> t.StrMapping:
        """Build the isolated source and recursion-guard environment."""
        python_path = c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
            str(path) for path in cls._source_roots(worktree_root)
        )
        return {
            c.Infra.WORKTREE_TRANSACTION_ENV: "1",
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
        warnings = (
            warning_matches[-1]
            if warning_matches
            else len(re.findall(r"(?im)^.*\bwarning:", output))
        )
        return (errors, warnings)

    @classmethod
    def _lint_snapshot(
        cls,
        worktree_root: Path,
        tool: str,
        command: t.StrSequence,
        environment: t.StrMapping,
        timeout_seconds: int,
    ) -> m.Infra.LintSnapshot:
        """Capture one lint command without hiding a non-zero exit status."""
        result = u.Cli.run_raw(
            command, cwd=worktree_root, env=environment, timeout=timeout_seconds
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

    @classmethod
    def _lint_commands(cls) -> p.Result[t.StrSequencePairTuple]:
        """Bind lint tools to the transaction interpreter before cwd mutation."""
        executable_root = Path(sys.executable).parent
        commands: t.MutableSequenceOf[t.StrSequencePair] = []
        for tool, command in c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS:
            executable = executable_root / command[0]
            if not executable.is_file():
                return r[t.StrSequencePairTuple].fail(
                    f"required transaction lint executable not found: {executable}"
                )
            commands.append((tool, (str(executable), *command[1:])))
        return r[t.StrSequencePairTuple].ok(tuple(commands))

    @classmethod
    def _lint_snapshots(
        cls,
        worktree_root: Path,
        environment: t.StrMapping,
        timeout_seconds: int,
        commands: t.StrSequencePairTuple,
    ) -> t.VariadicTuple[m.Infra.LintSnapshot]:
        """Capture every canonical transaction lint command in parallel."""
        with ThreadPoolExecutor(thread_name_prefix="lint_") as executor:
            return tuple(
                executor.map(
                    lambda item: cls._lint_snapshot(
                        worktree_root, item[0], item[1], environment, timeout_seconds
                    ),
                    commands,
                )
            )

    @classmethod
    def _import_probe(
        cls, worktree_root: Path, environment: t.StrMapping, timeout_seconds: int
    ) -> p.Cli.CommandOutput:
        """Fresh-import every productive package root in one isolated process."""
        packages = tuple(
            sorted({
                package_dir.name
                for source_root in cls._source_roots(worktree_root)
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
        before: t.SequenceOf[m.Infra.LintSnapshot],
        after: t.SequenceOf[m.Infra.LintSnapshot],
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
        repositories: t.SequenceOf[m.Infra.RepositoryWorktree],
    ) -> p.Result[t.SequenceOf[m.Infra.RepositoryDelta]]:
        """Capture operation-only deltas from every isolated repository."""
        deltas: t.MutableSequenceOf[m.Infra.RepositoryDelta] = []
        for repository in repositories:
            result = FlextInfraUtilitiesGitScope.git_repository_delta(repository)
            if result.failure:
                return r[t.SequenceOf[m.Infra.RepositoryDelta]].fail(
                    result.error
                    or f"failed to capture delta for {repository.relative_path}"
                )
            deltas.append(result.value)
        return r[t.SequenceOf[m.Infra.RepositoryDelta]].ok(tuple(deltas))

    @staticmethod
    def _check_patches(deltas: t.SequenceOf[m.Infra.RepositoryDelta]) -> p.Result[bool]:
        """Validate every patch from the isolated final state without source access."""
        for delta in deltas:
            result = FlextInfraUtilitiesGitScope.git_check_isolated_patch(delta)
            if result.failure:
                return r[bool].fail(
                    f"{delta.relative_path}: {result.error or 'patch check failed'}"
                )
        return r[bool].ok(True)

    @staticmethod
    def _apply_patches(deltas: t.SequenceOf[m.Infra.RepositoryDelta]) -> p.Result[bool]:
        """Forward-check and apply every patch, deepest repositories first."""
        ordered = sorted(
            deltas, key=lambda delta: len(Path(delta.relative_path).parts), reverse=True
        )
        for delta in ordered:
            result = FlextInfraUtilitiesGitScope.git_apply_patch(delta)
            if result.failure:
                return r[bool].fail(
                    f"{delta.relative_path}: {result.error or 'patch apply failed'}"
                )
        return r[bool].ok(True)

    @classmethod
    def _cleanup_worktrees(
        cls, repositories: t.SequenceOf[m.Infra.RepositoryWorktree], worktree_root: Path
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
        cls, request: m.Infra.WorktreeTransactionRequest
    ) -> p.Result[m.Infra.WorktreeTransactionReport]:
        """Execute, validate, optionally apply, and always remove one worktree."""
        workspace_root = request.workspace_root.resolve()
        transaction_id = uuid4().hex
        worktree_root = (
            workspace_root
            / c.Infra.WORKTREE_TRANSACTION_ROOT
            / f"transaction-{transaction_id}"
        )
        create_result = cls._create_complete_worktree(
            workspace_root,
            worktree_root,
            transaction_id,
            scoped_paths=tuple(request.scoped_paths),
        )
        if create_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                create_result.error or "failed to create complete worktree"
            )
        repositories = create_result.value
        report_result: p.Result[m.Infra.WorktreeTransactionReport]
        try:
            report_result = cls._execute_isolated(
                request,
                transaction_id=transaction_id,
                worktree_root=worktree_root,
                repositories=repositories,
            )
        finally:
            cleanup_result = cls._cleanup_worktrees(repositories, worktree_root)
        if cleanup_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                cleanup_result.error or "failed to remove transaction worktree"
            )
        return report_result

    @classmethod
    def _execute_isolated(
        cls,
        request: m.Infra.WorktreeTransactionRequest,
        *,
        transaction_id: str,
        worktree_root: Path,
        repositories: t.SequenceOf[m.Infra.RepositoryWorktree],
    ) -> p.Result[m.Infra.WorktreeTransactionReport]:
        """Run and evaluate the command inside an already checkpointed worktree."""
        lint_commands_result = cls._lint_commands()
        if lint_commands_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                lint_commands_result.error
                or "failed to resolve transaction lint executables"
            )
        lint_commands = lint_commands_result.value
        environment = cls._transaction_environment(worktree_root)
        lint_before = cls._lint_snapshots(
            worktree_root, environment, request.timeout_seconds, lint_commands
        )
        relocated = cls._relocate_command(
            request.command, request.workspace_root.resolve(), worktree_root
        )
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
        lint_after = cls._lint_snapshots(
            worktree_root, environment, request.timeout_seconds, lint_commands
        )

        def _run_import_probe() -> p.Cli.CommandOutput:
            return cls._import_probe(
                worktree_root, environment, request.timeout_seconds
            )

        def _run_deltas() -> p.Result[t.SequenceOf[m.Infra.RepositoryDelta]]:
            return cls._repository_deltas(repositories)

        with ThreadPoolExecutor(thread_name_prefix="post_") as executor:
            import_probe_future = executor.submit(_run_import_probe)
            deltas_future = executor.submit(_run_deltas)
            import_probe = import_probe_future.result()
            deltas_result = deltas_future.result()

        if deltas_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                deltas_result.error or "failed to capture repository deltas"
            )
        deltas = deltas_result.value
        breakage = (
            command_output.exit_code != 0
            or import_probe.exit_code != 0
            or cls._lint_regressed(lint_before, lint_after)
        )
        patch_check = cls._check_patches(deltas)
        if patch_check.failure:
            breakage = True
        applied = False
        apply_error = ""
        if request.apply_patch and not breakage:
            apply_result = cls._apply_patches(deltas)
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
        return r[m.Infra.WorktreeTransactionReport].ok(
            m.Infra.WorktreeTransactionReport(
                transaction_id=transaction_id,
                command=relocated,
                worktree_root=worktree_root,
                command_output=command_output,
                import_probe=import_probe,
                lint_before=lint_before,
                lint_after=lint_after,
                repositories=tuple(deltas),
                breakage_detected=breakage,
                applied=applied,
                summary=summary,
            )
        )

    @staticmethod
    def render_worktree_transaction_report(
        report: m.Infra.WorktreeTransactionReport,
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
        for repository in report.repositories:
            if not repository.patch:
                continue
            # mro-45r9: keep patches byte-exact internally; decode only at text egress.
            lines.extend((
                f"diff -- repository {repository.relative_path}",
                repository.patch.decode(c.Cli.ENCODING_DEFAULT, errors="replace"),
            ))
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesWorktreeTransaction"]
