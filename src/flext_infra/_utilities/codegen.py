"""Codegen utilities composition for the infrastructure namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from flext_cli import u

from flext_infra import c, config, e, m, p
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesGenerationInventory,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesManagedConflicts,
    FlextInfraUtilitiesMarkdownTooling,
    FlextInfraUtilitiesModelsProtocol,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRepository,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesWorkspaceInventory,
    FlextInfraUtilitiesWorkspaceManifest,
)
from flext_infra._utilities._git import FlextInfraUtilitiesGitignore
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra.make_contract import FlextInfraConfigMakeContract


class FlextInfraUtilitiesCodegen(
    FlextInfraConfigMakeContract,
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesGenerationInventory,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesMarkdownTooling,
    FlextInfraUtilitiesModelsProtocol,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesManagedConflicts,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRepository,
    FlextInfraUtilitiesGitignore,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesWorkspaceInventory,
    FlextInfraUtilitiesWorkspaceManifest,
    FlextInfraUtilitiesBase,
):
    """Compose the source helpers consumed by the generation operation."""

    @staticmethod
    def generation_root_members(
        workspace_root: Path,
        workspace: p.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Elect every declared member checkout that is its own generation root.

        A managed subproject is a member by declaration. An attached member the
        workspace declares as external is still a governed project once it
        carries its own ``pyproject.toml`` and committed ``mise.lock``: it owns
        its projections while sharing only the workspace runtime, so it is a
        legal generation root. A plain vendored fork carries no FLEXT lock and
        stays outside generation; a path the workspace never declares stays
        outside it as before.

        Returns:
            The absolute member checkouts generation may target.

        """
        return (
            *(
                (workspace_root / member.path).resolve()
                for member in workspace.subprojects
            ),
            *(
                (workspace_root / path).resolve()
                for path in workspace.external_dependency_paths
                if (workspace_root / path / c.PYPROJECT_FILENAME).is_file()
                and (workspace_root / path / c.Infra.MISE_LOCK_FILENAME).is_file()
            ),
        )

    @staticmethod
    def codegen_raise_failure(scope: Path, failure: p.FailureLike) -> NoReturn:
        """Stop codegen planning at its first failure instead of retaining it.

        A failure carrying its original exception re-raises it unchanged.

        Raises:
            e.OperationError: A typed refusal naming the failed scope when the
                failure carries no original exception.

        """
        if failure.exception is not None:
            raise failure.exception
        message = f"{failure.error}: {scope}"
        raise e.OperationError(
            message, context={c.Infra.MOD_FAILURE_MODULE_KEY: str(scope)}
        )

    @staticmethod
    def envrc_render_spec() -> p.Infra.EnvrcRenderSpec:
        """Return the sole typed context every generated ``.envrc`` renders from.

        Returns:
            The sole typed context every generated ``.envrc`` renders from.

        """
        return m.Infra.EnvrcRenderSpec(
            native_environment_unset=config.Infra.codegen.make.native_environment_unset,
            toolchain=config.Infra.codegen.toolchain,
            environment_path_prepends=(
                config.Infra.codegen.toolchain.environment_path_prepends
            ),
            bootstrap_bin_dir=config.Infra.codegen.make.bootstrap_bin_dir,
        )

    @staticmethod
    def generate_test_module_skeleton(
        *,
        context: p.Infra.TestModuleSkeletonRenderContext,
    ) -> str:
        """Render one canonical test facade skeleton from its validated context.

        Returns:
            The resulting ``str``.

        """
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_TEST_MODULE_SKELETON
        )
        rendered: p.Result[str] = u.Cli.template_render(template_path, context)
        return rendered.unwrap()

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return whether a package directory contains canonical Python files.

        Returns:
            Whether a package directory contains canonical Python files.

        """
        if not pkg_dir.is_dir():
            return False
        return any(
            child.is_file() and child.suffix == ".py" for child in pkg_dir.iterdir()
        )


__all__: list[str] = ["FlextInfraUtilitiesCodegen"]
