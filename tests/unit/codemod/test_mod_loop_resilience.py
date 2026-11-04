"""The mod loop survives external drift and quarantines one failing module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import config, e, infra, m, r
from flext_infra.codemod import FlextInfraApplyRenames, FlextInfraCodemodBatchApply
from tests import c, p, t, tm, u


class _RecordingProgress:
    """Real ModProgress transport that records emissions for asserts."""

    def __init__(self) -> None:
        """Initialize an empty emission log."""
        self.messages: list[str] = []

    def emit(self, message: str) -> None:
        """Record one progress line."""
        self.messages.append(message)

    def emit_rename(self, report: p.Infra.ApplyRenamesReport) -> None:
        """Record one rename campaign summary."""
        self.messages.append(f"rename occurrences={report.occurrences}")


class _ExternalWriterPhase:
    """Loop phase whose first plan races a real write by another actor."""

    name = "external-writer"

    def __init__(self, target: Path, content: str) -> None:
        """Bind the source the concurrent actor rewrites once."""
        self.target = target
        self.content = content
        self.calls = 0

    def plan(
        self,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Rewrite the target on disk during the first plan only.

        Returns:
            No effects of its own.

        """
        del root, preflight, rope_workspace, sources
        self.calls += 1
        if self.calls == 1:
            _ = self.target.write_text(self.content, encoding="utf-8")
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(())

    @staticmethod
    def apply(
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Publish nothing standalone.

        Returns:
            ``False``: the phase owns no standalone effect.

        """
        del root, preflight, rope_workspace
        return r[bool].ok(value=False)


def _rewrite(path: Path, desired: str) -> p.Infra.CodegenFilePlan:
    """Plan one real rewrite against the module's current physical state.

    Returns:
        The rewrite plan bound to the observed state.

    """
    state = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
    return m.Infra.CodegenFilePlan(
        project=path.parents[2],
        path=path,
        before=state,
        desired_content=desired.encode(c.DEFAULT_ENCODING),
        desired_mode=state.mode,
    )


class _OneModuleFailsPhase:
    """Fails attributed to one module; otherwise plans a change spanning it."""

    name = "one-module-fails"

    def __init__(self, bad: Path, partner: Path) -> None:
        """Bind the failing module and the partner of its cross-module change."""
        self.bad = bad
        self.partner = partner

    def plan(
        self,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Fail on the bad module while in scope, else span bad and partner.

        Returns:
            The attributed failure, or one coherent two-module change.

        """
        del root, preflight, rope_workspace
        result = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if self.bad in sources:
            failure = e.OperationError(
                f"cannot plan {self.bad.name}",
                context={c.Infra.MOD_FAILURE_MODULE_KEY: str(self.bad)},
            )
            return result.fail(str(failure), exception=failure)
        return result.ok(
            tuple(
                _rewrite(path, path.read_text(encoding="utf-8") + "SHARED = 1\n")
                for path in (self.bad, self.partner)
            )
        )

    @staticmethod
    def apply(
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Publish nothing standalone.

        Returns:
            ``False``: the phase owns no standalone effect.

        """
        del root, preflight, rope_workspace
        return r[bool].ok(value=False)


class _IndependentFixPhase:
    """Loop phase repairing one module unrelated to the quarantined one."""

    name = "independent-fix"

    def __init__(self, target: Path, desired: str) -> None:
        """Bind the module this phase repairs."""
        self.target = target
        self.desired = desired

    def plan(
        self,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Repair the target until it carries the desired source.

        Returns:
            The target's repair plan, or nothing at its fixed point.

        """
        del root, preflight, rope_workspace
        result = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if sources.get(self.target) == self.desired:
            return result.ok(())
        return result.ok((_rewrite(self.target, self.desired),))

    @staticmethod
    def apply(
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Publish nothing standalone.

        Returns:
            ``False``: the phase owns no standalone effect.

        """
        del root, preflight, rope_workspace
        return r[bool].ok(value=False)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Build one governed project with three clean modules.

    Returns:
        ``(project, alpha, beta, gamma)`` with resolved module paths.

    """
    names = ("alpha", "beta", "gamma")
    project = u.Tests.create_codegen_project(
        tmp_path=tmp_path,
        name="sample-proj",
        pkg_name="sample_pkg",
        files={
            f"{name}.py": (
                f'"""Module {name}."""\n\nfrom __future__ import annotations\n\n'
                f"{name.upper()}_VALUE = 1\n"
            )
            for name in names
        },
    )
    pkg = project / "src" / "sample_pkg"
    for extra in pkg.iterdir():
        if extra.name not in {c.Infra.INIT_PY, *(f"{name}.py" for name in names)}:
            extra.unlink()
    _ = (project / c.PYPROJECT_FILENAME).write_text(
        "[project]\nname='sample-proj'\n"
        f"version='{config.Infra.initial_project_version}'\n"
        'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
        'license = "MIT"\ndependencies=[]\n',
        encoding="utf-8",
    )
    u.Tests.copy_tracked_mise_seeds(project)
    declared = project / c.Infra.CODEGEN_CONFIG_DIR / c.Infra.CODEGEN_CONFIG_FILENAME
    declared.parent.mkdir(parents=True, exist_ok=True)
    _ = declared.write_text(
        "Infra:\n  codegen:\n    repository:\n"
        f"      kind: {c.Infra.ProjectKind.INTERNAL_FLEXT.value}\n",
        encoding="utf-8",
    )
    u.Tests.provision_checkout(project)
    alpha, beta, gamma = ((pkg / f"{name}.py").resolve() for name in names)
    return project, alpha, beta, gamma


def _run(
    project: Path,
    *phases: p.Infra.ModLoopPhase,
) -> tuple[p.Result[t.Cli.ResultValue], _RecordingProgress]:
    """Drive the public batch apply with injected loop phases.

    Returns:
        The real mod verdict and the recorded progress.

    """
    progress = _RecordingProgress()
    with infra.rope_workspace(project) as rope:
        result = FlextInfraCodemodBatchApply(
            workspace_factory=infra.rope_workspace,
            source_preview=infra.source_preview(project),
            repository_root=project,
            apply_changes=True,
            check_only=False,
            dry_run=False,
            rename_runner=FlextInfraApplyRenames(),
            progress=progress,
            rope=rope,
            rename_inputs=(),
            phase_callbacks=phases,
        ).execute()
    return result, progress


class TestsFlextInfraModLoopResilience:
    """External drift and one module's failure never abort the mod loop."""

    @staticmethod
    @pytest.mark.slow
    def test_external_drift_discards_iteration_and_adopts_disk(
        tmp_path: Path,
    ) -> None:
        """A source rewritten mid-iteration is re-captured, never an abort."""
        project, alpha, _beta, _gamma = _fixture(tmp_path)
        adopted = alpha.read_text(encoding="utf-8").replace("= 1", "= 2")
        phase = _ExternalWriterPhase(alpha, adopted)

        result, progress = _run(project, phase)

        tm.ok(result)
        tm.that(alpha.read_text(encoding="utf-8"), eq=adopted)
        tm.that(phase.calls, gte=2)
        tm.that(
            [
                message
                for message in progress.messages
                if "observed external change" in message and str(alpha) in message
            ],
            empty=False,
        )

    @staticmethod
    @pytest.mark.slow
    def test_module_failure_quarantines_only_that_module(
        tmp_path: Path,
    ) -> None:
        """Unrelated fixes publish; a change spanning the module drops whole."""
        project, alpha, beta, gamma = _fixture(tmp_path)
        before = {path: path.read_bytes() for path in (alpha, beta)}
        desired = gamma.read_text(encoding="utf-8").replace("= 1", "= 3")

        result, progress = _run(
            project,
            _OneModuleFailsPhase(alpha, beta),
            _IndependentFixPhase(gamma, desired),
        )

        tm.ok(result.failure)
        tm.that(result.error, has="quarantined module(s)")
        tm.that(result.error, has=f"{alpha}: ")
        tm.that(result.error, has="cannot plan alpha.py")
        tm.that(
            result.error,
            has=(
                f"phase one-module-fails change over {alpha}, {beta} dropped "
                f"whole because of {alpha}"
            ),
        )
        tm.that(gamma.read_text(encoding="utf-8"), eq=desired)
        for path, content in before.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(
            [
                message
                for message in progress.messages
                if message.startswith(f"mod: quarantine {alpha}")
            ],
            empty=False,
        )
