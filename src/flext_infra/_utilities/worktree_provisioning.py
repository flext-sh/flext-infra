from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorktreeProvisioning:
    @staticmethod
    def _prepare_beads_directory(lane: Path) -> p.Result[bool]:
        beads_dir = lane / ".beads"
        if beads_dir.is_symlink():
            return r.fail(f"lane Beads path must not be a symlink: {beads_dir}")
        if beads_dir.exists() and not beads_dir.is_dir():
            return r.fail(f"lane Beads path must be a directory: {beads_dir}")
        if not beads_dir.exists():
            return r.ok(True)
        try:
            beads_dir.chmod(0o700, follow_symlinks=False)
        except OSError as exc:
            return r.fail(f"failed to secure lane Beads directory {beads_dir}: {exc}")
        return r.ok(True)

    @classmethod
    def setup_lane(cls, lane: Path) -> p.Result[bool]:
        secured = cls._prepare_beads_directory(lane)
        if secured.failure:
            return secured
        venv_name = config.Infra.tooling.tools.pyright.path_rules.venv_name
        lane_venv = lane / venv_name
        if lane_venv.is_symlink():
            try:
                lane_venv.unlink()
            except OSError as exc:
                return r.fail(f"failed to remove foreign lane environment link: {exc}")
        setup = u.Cli.run_live(
            (c.Infra.MAKE, "setup"),
            cwd=lane,
            remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
        )
        if setup.failure:
            return r.fail(setup.error or "make setup execution failed")
        interpreter = lane_venv / "bin" / "python"
        if not interpreter.is_file():
            return r.fail(f"lane setup did not create an interpreter: {interpreter}")
        return r.ok(True)


__all__: list[str] = ["FlextInfraWorktreeProvisioning"]
