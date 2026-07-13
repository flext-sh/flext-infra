"""Phase: Ensure a standardized hatch wheel build target plus force-include.

Every project's wheel gets an explicit ``[tool.hatch.build.targets.wheel]``
with ``packages = ["src/<pkg>"]``. Root data directories declared in
``config.Infra.tooling.tools.hatch.packaged_data_dirs`` (e.g. ``config``,
``templates``) are force-included into the wheel when they exist at the
project root, so they survive ``pip install`` (``<pkg>/<dir>``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraEnsurePackagingPhase:
    """Ensure the hatch wheel target and root data-dir force-include."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration providing the packaged data-dir policy."""
        self._tool_config = tool_config

    def _phase(
        self, *, package_name: str, data_dirs: t.StrSequence
    ) -> m.Infra.Deps.Toml.PhaseConfig:
        """Build the wheel-target phase for one resolved package name."""
        builder = (
            m.Infra.Deps.Toml.PhaseConfig
            .Builder("packaging")
            .table("hatch", "build", "targets", "wheel")
            .list(
                "packages",
                (f"{c.Infra.DEFAULT_SRC_DIR}/{package_name}",),
                strategy=c.Infra.TomlMergeMode.REPLACE,
            )
        )
        if data_dirs:
            builder = builder.nested(
                "force-include",
                values=tuple(
                    (data_dir, f"{package_name}/{data_dir}") for data_dir in data_dirs
                ),
            )
        return builder.build()

    def apply_payload(
        self, payload: t.MutableJsonMapping, *, path: Path, is_root: bool
    ) -> t.StrSequence:
        """Emit the wheel target for a distributable project.

        The workspace root is not a distributable package, so it is skipped.
        Only data directories that actually exist at the project root are
        force-included, keeping the wheel free of phantom paths.
        """
        if is_root:
            return ()
        project_dir = path.parent
        package_name = u.Infra.project_package_name(project_dir)
        if not package_name:
            return ()
        present_dirs = tuple(
            data_dir
            for data_dir in self._tool_config.tools.hatch.packaged_data_dirs
            if (project_dir / data_dir).is_dir()
        )
        return FlextInfraTomlPhaseService.apply_payload_phases(
            payload, self._phase(package_name=package_name, data_dirs=present_dirs)
        )


__all__: list[str] = ["FlextInfraEnsurePackagingPhase"]
