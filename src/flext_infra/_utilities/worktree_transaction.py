"""Isolated command transactions built on the canonical ``u.Infra`` Git owner."""

from __future__ import annotations

import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from flext_cli import u
from flext_core import r
from flext_infra import c, config, m, t
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.serialization_lock import (
    FlextInfraUtilitiesSerializationLock,
)

if TYPE_CHECKING:
    from flext_infra.protocols import p


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
    def _declared_nested_repository_paths(
        cls, workspace_root: Path
    ) -> p.Result[t.SequenceOf[Path]]:
        """Resolve existing manifest-declared nested Git repositories.

        The typed workspace manifest is the topology SSOT: a declared member
        may already be an initialized checkout without yet being recorded in
        ``.gitmodules``, so discovery reads the manifest rather than Git's
        submodule index alone.
        """
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
            workspace_root
        )
        if workspace_result.failure:
            return r[t.SequenceOf[Path]].fail(
                workspace_result.error or "failed to load workspace topology"
            )
        paths = tuple(
            repository.path
            for repository in workspace_result.value.members
            if repository.checkout is c.Infra.CheckoutKind.SUBMODULE
            and (workspace_root / repository.path / c.Infra.GIT_DIR).exists()
        )
        return r[t.SequenceOf[Path]].ok(paths)

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
        declared_result = cls._declared_nested_repository_paths(workspace_root)
        if declared_result.failure:
            return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                declared_result.error or "failed to discover declared repositories"
            )
        discovered = (*submodules_result.value, *declared_result.value)
        submodule_paths = tuple(
            submodule
            for submodule in dict.fromkeys(discovered)
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
            if repository.relative_path == ".":
                # The isolated root must describe the member commits this
                # transaction actually contains: members are checkpointed
                # first (deepest-first ordering), so seed the root index from
                # those checkpoints instead of the pre-transaction source HEAD.
                checkpoints = {
                    nested.relative_path: nested.checkpoint_sha
                    for nested in checkpointed
                }
                for nested in created:
                    if nested.relative_path == ".":
                        continue
                    nested_head = checkpoints.get(nested.relative_path)
                    if nested_head is None:
                        cls._cleanup_worktrees(created, worktree_root)
                        return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                            f"missing isolated checkpoint for {nested.relative_path}"
                        )
                    update_result = FlextInfraUtilitiesGitScope.git_capture(
                        repository.worktree_root,
                        (
                            "update-index",
                            "--add",
                            "--cacheinfo",
                            "160000",
                            nested_head,
                            nested.relative_path,
                        ),
                    )
                    if update_result.failure:
                        cls._cleanup_worktrees(created, worktree_root)
                        return r[t.SequenceOf[m.Infra.RepositoryWorktree]].fail(
                            update_result.error
                            or "failed to seed isolated gitlink for "
                            f"{nested.relative_path}"
                        )
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

    @classmethod
    def _source_roots(
        cls, worktree_root: Path, scoped_paths: t.SequenceOf[Path] = ()
    ) -> t.SequenceOf[Path]:
        """Resolve the productive source roots the transaction actually owns.

        A member outside the requested scope is never a source root: importing
        it would assert a dependency the scoped project does not declare and
        would fail closed on any sibling that is merely present on disk.
        """
        roots: t.MutableSequenceOf[Path] = []
        root_source = worktree_root / c.Infra.DEFAULT_SRC_DIR
        if root_source.is_dir():
            roots.append(root_source)
        for child in sorted(worktree_root.iterdir()):
            source_root = child / c.Infra.DEFAULT_SRC_DIR
            if not (child.is_dir() and source_root.is_dir()):
                continue
            if cls._submodule_in_scope(child.relative_to(worktree_root), scoped_paths):
                roots.append(source_root)
        return tuple(roots)

    @classmethod
    def _transaction_environment(
        cls, worktree_root: Path, scoped_paths: t.SequenceOf[Path] = ()
    ) -> t.StrMapping:
        """Build the isolated source and recursion-guard environment."""
        source_roots = cls._source_roots(worktree_root, scoped_paths)
        python_path = c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
            str(path) for path in source_roots
        )
        return {
            c.Infra.WORKTREE_TRANSACTION_ENV: "1",
            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: python_path,
            c.Infra.ORCHESTRATOR_ENV_PYTHONDONTWRITEBYTECODE: "1",
        }

    @staticmethod
    def _materialize_runtime_environment(worktree_root: Path) -> p.Result[bool]:
        """Expose the active managed environment at its configured project path."""
        executable = Path(sys.executable).expanduser().absolute()
        runtime_root = executable.parent.parent
        venv_name = config.Infra.tooling.tools.pyright.path_rules.venv_name
        return u.Cli.ensure_symlink(worktree_root / venv_name, runtime_root)

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
        lint_environment = {
            key: value
            for key, value in environment.items()
            if key != c.Infra.ORCHESTRATOR_ENV_PYTHONPATH
        }
        result = u.Cli.run_raw(
            command,
            cwd=worktree_root,
            env=lint_environment,
            remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            timeout=timeout_seconds,
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
    def _project_interpreter(project_root: Path) -> str:
        """Resolve the interpreter that owns one project's dependencies.

        ``sys.executable`` may point at the flext-infra bootstrap interpreter
        (from ``FLEXT_INFRA_BOOTSTRAP`` / ``uv run --project ...``); it resolves
        flext-infra's dependencies and may not include the checked project's dev
        dependencies (pytest, PyYAML, ...). Type checking against it reports each as a
        missing import. The project virtualenv is the only interpreter that can
        resolve the imports the project actually declares.
        """
        candidate = project_root / c.Infra.VENV_BIN_REL / c.Infra.PYTHON
        if candidate.is_file():
            return str(candidate.resolve())
        return sys.executable

    @classmethod
    def _lint_commands(cls, worktree_root: Path) -> p.Result[t.StrSequencePairTuple]:
        """Bind lint tools from the managed process environment before mutation."""
        managed_path = u.Cli.process_env().get(c.Infra.ORCHESTRATOR_ENV_PATH, "")
        commands: t.MutableSequenceOf[t.StrSequencePair] = []
        for tool, command in c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS:
            resolved = shutil.which(command[0], path=managed_path)
            if resolved is None:
                return r[t.StrSequencePairTuple].fail(
                    "required transaction lint executable not found on managed PATH: "
                    f"{command[0]}"
                )
            executable = Path(resolved).resolve()
            if not executable.is_file():
                return r[t.StrSequencePairTuple].fail(
                    f"resolved transaction lint executable is not a file: {executable}"
                )
            bound_command: t.StrSequence = (str(executable), *command[1:])
            if tool == c.Infra.PYREFLY:
                bound_command = (
                    *bound_command,
                    "--config",
                    c.Infra.PYPROJECT_FILENAME,
                    "--python-interpreter-path",
                    cls._project_interpreter(worktree_root),
                )
            commands.append((tool, bound_command))
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
        cls,
        worktree_root: Path,
        runtime_root: Path,
        environment: t.StrMapping,
        timeout_seconds: int,
        scoped_paths: t.SequenceOf[Path] = (),
    ) -> p.Cli.CommandOutput:
        """Fresh-import scoped sources with their real runtime metadata."""
        packages = tuple(
            sorted({
                package_dir.name
                for source_root in cls._source_roots(worktree_root, scoped_paths)
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
            (cls._project_interpreter(runtime_root), "-c", script),
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
        """Return whether a command introduced or increased diagnostics."""
        return any(
            after_item.errors > before_item.errors
            or after_item.warnings > before_item.warnings
            or (after_item.exit_code != 0 and before_item.exit_code == 0)
            for before_item, after_item in zip(before, after, strict=True)
        )

    @classmethod
    def _repository_deltas(
        cls, repositories: t.SequenceOf[m.Infra.RepositoryWorktree]
    ) -> p.Result[t.SequenceOf[m.Infra.RepositoryDelta]]:
        """Capture operation-only deltas from every isolated repository.

        The sandbox seeds each nested gitlink with the member's ISOLATED
        checkpoint so the isolated tree is self-consistent. That SHA exists
        only inside the sandbox, so the root patch must carry the SOURCE head
        instead; otherwise applying the transaction would point the real
        superproject at a commit no source checkout has.
        """
        source_gitlinks = {
            repository.relative_path: repository.source_root
            for repository in repositories
            if repository.relative_path != "."
        }
        resolved_gitlinks: dict[str, str] = {}
        for path, source_root in source_gitlinks.items():
            head_result = FlextInfraUtilitiesGitScope.git_repository_head(source_root)
            if head_result.failure:
                return r[t.SequenceOf[m.Infra.RepositoryDelta]].fail(
                    head_result.error or f"failed to resolve source head for {path}"
                )
            resolved_gitlinks[path] = head_result.value
        deltas: t.MutableSequenceOf[m.Infra.RepositoryDelta] = []
        for repository in repositories:
            result = FlextInfraUtilitiesGitScope.git_repository_delta(
                repository,
                source_gitlinks=resolved_gitlinks
                if repository.relative_path == "."
                else None,
            )
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
    def _preflight_source_heads(
        deltas: t.SequenceOf[m.Infra.RepositoryDelta],
    ) -> p.Result[bool]:
        """Reject every transaction when any source HEAD moved after checkpoint."""
        for delta in deltas:
            checkpoint_parent = FlextInfraUtilitiesGitScope.git_capture(
                delta.worktree_root, ("rev-parse", f"{delta.checkpoint_sha}^")
            )
            if checkpoint_parent.failure:
                return r[bool].fail(
                    checkpoint_parent.error
                    or f"{delta.relative_path}: failed to resolve checkpoint parent"
                )
            source_head = FlextInfraUtilitiesGitScope.git_repository_head(
                delta.source_root
            )
            if source_head.failure:
                return r[bool].fail(
                    source_head.error
                    or f"{delta.relative_path}: failed to resolve source HEAD"
                )
            expected = checkpoint_parent.value.strip()
            actual = source_head.value.strip()
            if actual != expected:
                return r[bool].fail(
                    f"{delta.relative_path}: source HEAD changed during isolated "
                    f"transaction: expected {expected}, found {actual}"
                )
        return r[bool].ok(True)

    @staticmethod
    def _transaction_lock_paths(
        deltas: t.SequenceOf[m.Infra.RepositoryDelta],
    ) -> p.Result[t.SequenceOf[Path]]:
        """Resolve the configured Make lock for every participating workspace."""
        relative_lock_path = config.Infra.codegen.make.serialization.lock_path
        lock_paths: set[Path] = set()
        for delta in deltas:
            for repository_root in (delta.source_root, delta.worktree_root):
                workspace_result = FlextInfraUtilitiesGitScope.git_workspace_root(
                    repository_root
                )
                if workspace_result.failure:
                    return r[t.SequenceOf[Path]].fail(
                        workspace_result.error
                        or f"failed to resolve lock owner for {repository_root}"
                    )
                workspace_root = workspace_result.value.resolve()
                lock_path = (workspace_root / relative_lock_path).resolve()
                try:
                    lock_path.relative_to(workspace_root)
                except ValueError:
                    return r[t.SequenceOf[Path]].fail(
                        f"transaction lock escapes workspace owner: {lock_path}"
                    )
                lock_paths.add(lock_path)
        return r[t.SequenceOf[Path]].ok(
            tuple(sorted(lock_paths, key=lambda path: path.as_posix()))
        )

    @classmethod
    def _apply_transaction_patches_locked(
        cls, deltas: t.SequenceOf[m.Infra.RepositoryDelta]
    ) -> p.Result[bool]:
        """Preflight all source HEADs and apply every patch under acquired locks."""
        head_preflight = cls._preflight_source_heads(deltas)
        if head_preflight.failure:
            return head_preflight
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
    def git_apply_transaction_patches(
        cls, deltas: t.SequenceOf[m.Infra.RepositoryDelta]
    ) -> p.Result[bool]:
        """Lock every workspace across source-HEAD preflight and patch apply."""
        lock_paths_result = cls._transaction_lock_paths(deltas)
        if lock_paths_result.failure:
            return r[bool].fail(
                lock_paths_result.error or "failed to resolve transaction locks"
            )
        serialization = config.Infra.codegen.make.serialization

        def timeout_failure(lock_path: Path, timeout_seconds: int) -> p.Result[bool]:
            return r[bool].fail(
                "timed out waiting for transaction lock "
                f"'{lock_path}' after {timeout_seconds}s"
            )

        def acquisition_failure(error: str) -> p.Result[bool]:
            return r[bool].fail(f"transaction lock acquisition failed: {error}")

        return FlextInfraUtilitiesSerializationLock.serialization_lock_execute(
            lock_paths_result.value,
            serialization.timeout_seconds,
            lambda: cls._apply_transaction_patches_locked(deltas),
            timeout_failure=timeout_failure,
            acquisition_failure=acquisition_failure,
            # The transaction owns its sandbox for exactly one operation, so its
            # lock is ephemeral: leaving the artifact behind would mutate the
            # source checkout the transaction promised to leave untouched.
            ephemeral=True,
        )

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
        primary_result = FlextInfraUtilitiesGitScope.git_primary_worktree_root(
            workspace_root
        )
        if primary_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                primary_result.error or "failed to resolve primary worktree"
            )
        primary_root = primary_result.value
        worktree_root = primary_root.parent / (
            c.Infra.WORKTREE_TRANSACTION_NAME_TEMPLATE.format(
                repository=primary_root.name, transaction_id=transaction_id
            )
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
        environment_result = cls._materialize_runtime_environment(worktree_root)
        if environment_result.failure:
            cls._cleanup_worktrees(repositories, worktree_root)
            return r[m.Infra.WorktreeTransactionReport].fail(
                environment_result.error
                or "failed to materialize transaction runtime environment"
            )
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
        lint_commands_result = cls._lint_commands(worktree_root)
        if lint_commands_result.failure:
            return r[m.Infra.WorktreeTransactionReport].fail(
                lint_commands_result.error
                or "failed to resolve transaction lint executables"
            )
        lint_commands = lint_commands_result.value
        environment = cls._transaction_environment(worktree_root, request.scoped_paths)
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
                worktree_root,
                request.workspace_root,
                environment,
                request.timeout_seconds,
                request.scoped_paths,
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
        lint_regressed = cls._lint_regressed(lint_before, lint_after)
        breakage = (
            command_output.exit_code != 0
            or import_probe.exit_code != 0
            or lint_regressed
        )
        patch_check = cls._check_patches(deltas)
        if patch_check.failure:
            breakage = True
        applied = False
        apply_error = ""
        if request.apply_patch and not breakage:
            apply_result = cls.git_apply_transaction_patches(deltas)
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
            if before.exit_code != 0 or before.errors or before.warnings:
                lines.extend((
                    f"  {before.tool} before output:",
                    before.output.rstrip(),
                ))
            if after.exit_code != 0 or after.errors or after.warnings:
                lines.extend((f"  {after.tool} after output:", after.output.rstrip()))
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
