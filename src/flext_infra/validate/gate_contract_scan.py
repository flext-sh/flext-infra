"""Gate contract script discovery."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import u
from flext_infra.validate.gate_contract_errors import GateContractInfraError

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraGateContractScanMixin:
    """Discover tracked workspace scripts."""

    @staticmethod
    def _tracked_scripts(root: Path) -> t.SequenceOf[Path]:
        scripts_root = root / "scripts"
        if not scripts_root.exists() or not scripts_root.is_dir():
            return ()

        scripts = u.Infra.git_tracked_scope_paths(scripts_root)
        if scripts is None:
            msg = f"tracked script discovery requires a Git worktree: {root}"
            raise GateContractInfraError(msg)
        return tuple(
            path.relative_to(root)
            for path in scripts
            if path.name != "__init__.py" and path.suffix in {".py", ".sh"}
        )
        if result.failure:
            raise GateContractInfraError(result.error or "git ls-files failed")
        output = result.value
        if not u.Cli.process_succeeded(output.outcome):
            stderr = (output.stderr or "").strip()
            raise GateContractInfraError(stderr or "git ls-files failed")

        scripts = (
            Path(line.strip())
            for line in sorted(set(output.stdout.splitlines()))
            if line.strip()
        )
        return tuple(path for path in scripts if path.name != "__init__.py")


__all__: list[str] = ["FlextInfraGateContractScanMixin"]
