"""Phase: Ensure bounded Hatch wheel and source-distribution targets.

Every project's wheel gets an explicit ``[tool.hatch.build.targets.wheel]``
with every manifest-declared source package. Root modules and data directories declared in
``config.Infra.tooling.tools.hatch.packaged_data_dirs`` (e.g. ``config``,
``templates``) are force-included into the wheel when they exist at the
project root, so they survive ``pip install`` (``<pkg>/<dir>``). The source
distribution is bounded to the package source and those validated data roots,
preventing caches and ignored workspace state from entering release artifacts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraEnsurePackagingPhase:
    """Ensure bounded Hatch wheel and source-distribution targets."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        """Store tool configuration providing the packaged data-dir policy."""
        self._tool_config = tool_config

    def _phase(
        self,
        *,
        package_name: str,
        root_modules: t.StrSequence,
        root_packages: t.StrSequence,
        data_dirs: t.StrSequence,
    ) -> m.Infra.Deps.Toml.PhaseConfig:
        """Build bounded distribution targets for one resolved package name."""
        package_path = f"{c.Infra.DEFAULT_SRC_DIR}/{package_name}"
        package_paths = (
            package_path,
            *(f"{c.Infra.DEFAULT_SRC_DIR}/{name}" for name in root_packages),
        )
        module_paths = tuple(
            f"{c.Infra.DEFAULT_SRC_DIR}/{name}.py" for name in root_modules
        )
        builder = (
            m.Infra.Deps.Toml.PhaseConfig
            .Builder("packaging")
            .table("hatch", "build", "targets")
            .nested("wheel", lists=(("packages", package_paths),))
            .nested(
                "sdist",
                lists=(("only-include", (*package_paths, *module_paths, *data_dirs)),),
            )
        )
        force_include = (
            *(
                (path, name + ".py")
                for path, name in zip(module_paths, root_modules, strict=True)
            ),
            *((data_dir, f"{package_name}/{data_dir}") for data_dir in data_dirs),
        )
        if force_include:
            builder = builder.nested("wheel", "force-include", values=force_include)
        return builder.build()

    @staticmethod
    def _additional_sources(project_dir: Path) -> tuple[t.StrSequence, t.StrSequence]:
        """Load additional Python distribution roots from the typed manifest owner."""
        manifest_path = project_dir / "config" / "workspace.yaml"
        if not manifest_path.is_file():
            return (), ()
        loaded = u.Cli.config_load(manifest_path, expand_env=False)
        if loaded.failure:
            message = loaded.error or f"workspace manifest load failed: {manifest_path}"
            raise ValueError(message)
        manifest = m.Infra.WorkspaceManifestSpec.model_validate(loaded.value.data)
        if manifest.project is None:
            return (), ()
        return manifest.project.root_modules, manifest.project.root_packages

    def apply_payload(
        self, payload: t.MutableJsonMapping, *, path: Path, is_root: bool
    ) -> t.StrSequence:
        """Emit bounded build targets for a distributable project.

        Projects whose distribution name resolves to ``src/<name>`` build via
        hatchling default file selection and need no explicit targets (the
        repository root is the canonical case). Standalone projects whose
        import package differs from the distribution name (for example a
        project shipping ``src/<other_name>``) must receive explicit bounded
        targets, or
        hatchling cannot determine the wheel contents. Only data directories
        that actually exist at the project root are force-included, keeping
        the wheel free of phantom paths.
        """
        project_dir = path.parent
        docs_meta = u.Infra.docs_meta_from_payload(payload)
        package_name = u.Infra.package_name_from_payload(
            project_dir, payload, docs_meta
        )
        if not package_name:
            return ()
        package_root = project_dir / c.Infra.DEFAULT_SRC_DIR / package_name
        root_modules, root_packages = self._additional_sources(project_dir)
        if is_root:
            project_name = u.Infra.project_name_from_payload(path, payload).replace(
                "-", "_"
            )
            if (project_dir / c.Infra.DEFAULT_SRC_DIR / project_name).is_dir():
                return ()
        tool = u.Cli.json_as_mapping(payload.get(c.Infra.TOOL))
        hatch = u.Cli.json_as_mapping(tool.get("hatch"))
        build = u.Cli.json_as_mapping(hatch.get("build"))
        targets = u.Cli.json_as_mapping(build.get("targets"))
        wheel = u.Cli.json_as_mapping(targets.get("wheel"))
        declared_force_include = u.Cli.json_as_mapping(wheel.get("force-include"))
        present_dirs = tuple(
            data_dir
            for data_dir in self._tool_config.tools.hatch.packaged_data_dirs
            # Force-include a root data dir only when it exists at the project
            # root AND is not already shipped from inside the package (which
            # would collide on the same wheel path).
            if data_dir in declared_force_include
            or (
                (project_dir / data_dir).is_dir()
                and not (package_root / data_dir).is_dir()
            )
        )
        return FlextInfraTomlPhaseService.apply_payload_phases(
            payload,
            self._phase(
                package_name=package_name,
                root_modules=root_modules,
                root_packages=root_packages,
                data_dirs=present_dirs,
            ),
        )


__all__: list[str] = ["FlextInfraEnsurePackagingPhase"]
