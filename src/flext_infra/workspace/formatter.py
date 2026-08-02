"""Git-scoped multi-language formatting owned by flext-infra config."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import config, m, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraWorkspaceFormatter:
    """Run ordered configured formatters over tracked and nonignored dirty files."""

    @staticmethod
    def select_files(
        root: Path,
        step: m.Infra.FormatterStepSpec,
        *,
        requested: t.SequenceOf[Path] = (),
    ) -> tuple[Path, ...]:
        """Resolve one step through the canonical Git-aware inventory."""
        matching = tuple(u.Infra.iter_matching_files(root, includes=step.includes))
        if not requested:
            return matching
        requested_resolved = frozenset(path.resolve() for path in requested)
        return tuple(path for path in matching if path.resolve() in requested_resolved)

    @classmethod
    def execute_request(cls, request: m.Infra.WorkspaceFormatRequest) -> p.Result[int]:
        """Format the selected managed repositories and return processed file count."""
        workspace_root = request.workspace_path
        roots = cls._managed_roots(workspace_root, request.project_names)
        if not roots:
            return r[int].fail("workspace formatter selected no managed projects")
        requested_result = cls._requested_paths(workspace_root, request.files, roots)
        if requested_result.failure:
            return r[int].fail(requested_result.error or "invalid formatter files")
        requested = requested_result.value
        processed: set[Path] = set()
        for root in roots:
            root_requested = tuple(
                path for path in requested if path.is_relative_to(root)
            )
            for step in config.Infra.codegen.formatters:
                files = cls.select_files(
                    root, step, requested=root_requested if requested else ()
                )
                if not files:
                    continue
                run_result = cls._run_step(root, step, files, apply=request.apply)
                if run_result.failure:
                    return r[int].fail(
                        run_result.error or f"formatter failed: {step.name}"
                    )
                processed.update(files)
        return r[int].ok(len(processed))

    @staticmethod
    def _managed_roots(
        workspace_root: Path, project_names: t.StrSequence | None
    ) -> tuple[Path, ...]:
        resolved = workspace_root.resolve()
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(resolved)
        entries: list[tuple[str, Path]] = [(".", resolved)]
        if workspace.success:
            entries.extend(
                (repository.distribution, (resolved / repository.path).resolve())
                for repository in workspace.value.members
                if not repository.read_only
            )
        selected = frozenset(project_names or ())
        return tuple(
            root
            for name, root in entries
            if root.is_dir()
            and (
                not selected
                or name in selected
                or root.name in selected
                or ("." in selected and root == resolved)
            )
        )

    @staticmethod
    def _requested_paths(
        workspace_root: Path, values: t.StrSequence, roots: tuple[Path, ...]
    ) -> p.Result[tuple[Path, ...]]:
        requested: list[Path] = []
        for raw in values:
            candidate = (workspace_root / raw).resolve()
            if not any(candidate.is_relative_to(root) for root in roots):
                return r[tuple[Path, ...]].fail(
                    f"formatter file is outside managed repositories: {raw}"
                )
            if not candidate.is_file():
                return r[tuple[Path, ...]].fail(f"formatter file does not exist: {raw}")
            requested.append(candidate)
        return r[tuple[Path, ...]].ok(tuple(requested))

    @staticmethod
    def _run_step(
        root: Path,
        step: m.Infra.FormatterStepSpec,
        files: tuple[Path, ...],
        *,
        apply: bool,
    ) -> p.Result[int]:
        command = cls.command_for_step(step, files, apply=apply)
        if not command:
            return r[int].fail(
                f"managed formatter executable not found: {step.executable}"
            )
        output = u.Cli.run_raw(
            command, cwd=root, capture=step.reject_stdout and not apply
        )
        if output.failure:
            return r[int].fail(
                output.error or f"failed to start formatter: {step.name}"
            )
        if output.value.exit_code != 0:
            return r[int].fail(
                f"formatter {step.name} failed with exit {output.value.exit_code}"
            )
        if step.reject_stdout and not apply and output.value.stdout.strip():
            return r[int].fail(f"formatter {step.name} reported format drift")
        return r[int].ok(len(files))

    @staticmethod
    def command_for_step(
        step: m.Infra.FormatterStepSpec, files: tuple[Path, ...], *, apply: bool
    ) -> tuple[str, ...]:
        """Build one formatter command from the governed venv or Mise binary."""
        mode_arguments = step.apply_arguments if apply else step.check_arguments
        arguments = (*step.arguments, *mode_arguments, *(str(path) for path in files))
        if step.python_tool:
            executable = Path(sys.executable).parent / step.executable
            return (str(executable), *arguments) if executable.is_file() else ()
        mise = os.environ.get("FLEXT_INFRA_MISE", "")
        if not mise or not Path(mise).is_file():
            return ()
        return (mise, "exec", "--", step.executable, *arguments)


__all__: list[str] = ["FlextInfraWorkspaceFormatter"]
