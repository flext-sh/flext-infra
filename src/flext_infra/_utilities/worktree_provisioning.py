from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, m, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorktreeProvisioning:
    @staticmethod
    def _initialize_primary_gitlinks(primary_root: Path) -> p.Result[bool]:
        declared = u.Infra.git_declared_submodule_paths(primary_root)
        if declared.failure:
            return r.fail(declared.error or "failed to read primary Git declarations")
        for relative in declared.value:
            if (primary_root / relative / ".git").exists():
                continue
            initialized = u.Infra.git_submodule_init(
                m.Infra.GitRefRequest(
                    repo_root=primary_root, reference=relative.as_posix()
                )
            )
            if initialized.failure:
                return r.fail(
                    initialized.error
                    or f"failed to initialize primary gitlink {relative}"
                )
        return r.ok(True)

    @classmethod
    def setup_lane(cls, primary_root: Path, lane: Path) -> p.Result[bool]:
        beads_dir = lane / ".beads"
        if beads_dir.is_dir():
            beads_dir.chmod(0o700)
        initialized = cls._initialize_primary_gitlinks(primary_root)
        if initialized.failure:
            return initialized
        venv_name = config.Infra.tooling.tools.pyright.path_rules.venv_name
        primary_venv = primary_root / venv_name
        lane_venv = lane / venv_name
        if lane_venv.is_symlink():
            if lane_venv.resolve() != primary_venv.resolve():
                return r.fail(
                    f"lane environment points outside the primary environment: {lane_venv}"
                )
        elif lane_venv.exists():
            return r.fail(f"refusing to replace existing lane environment: {lane_venv}")
        setup = u.Cli.run_live(
            (c.Infra.MAKE, "setup", "WHAT=", f"WORKSPACE={primary_root}"),
            cwd=primary_root,
            remove_env_keys=(
                "MAKEFLAGS",
                "MAKELEVEL",
                "MAKEOVERRIDES",
                "MFLAGS",
                "UV_PROJECT",
                "UV_PROJECT_ENVIRONMENT",
                "VIRTUAL_ENV",
            ),
        )
        if setup.failure:
            return r.fail(setup.error or "make setup execution failed")
        interpreter = primary_venv / "bin" / "python"
        if not interpreter.is_file():
            return r.fail(f"primary setup did not create an interpreter: {interpreter}")
        if not lane_venv.is_symlink():
            try:
                lane_venv.symlink_to(primary_venv, target_is_directory=True)
            except OSError as exc:
                return r.fail(f"failed to bind lane environment {lane_venv}: {exc}")
        return r.ok(True)


__all__: list[str] = ["FlextInfraWorktreeProvisioning"]
