"""Codegen utilities composition for the infrastructure namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesManagedConflicts,
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
    FlextInfraUtilitiesBase,
    FlextInfraConfigMakeContract,
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesGitignore,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesModelsProtocol,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesManagedConflicts,
    FlextInfraUtilitiesRefactor,
    FlextInfraUtilitiesRepository,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesVersioning,
    FlextInfraUtilitiesWorkspaceInventory,
    FlextInfraUtilitiesWorkspaceManifest,
):
    """Compose the source helpers consumed by the generation operation."""

    @staticmethod
    def envrc_render_spec() -> m.Infra.EnvrcRenderSpec:
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
        )

    @staticmethod
    def generate_test_module_skeleton(
        *,
        context: m.Infra.TestModuleSkeletonRenderContext,
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

    @staticmethod
    def parse_final_constant_definitions(
        source_lines: Sequence[str],
    ) -> Sequence[tuple[str, str, str, str, int]]:
        """Parse ``NAME: Final[...] = VALUE`` definitions with class-path context.

        Returns:
            The resulting ``Sequence[tuple[str, str, str, str, int]]``.

        """
        class_stack: MutableSequence[tuple[str, int]] = []
        parsed: MutableSequence[tuple[str, str, str, str, int]] = []
        for line_number, line in enumerate(source_lines, 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            FlextInfraUtilitiesCodegen.update_class_stack(class_stack, stripped, indent)
            match = c.Infra.DETECTION_FINAL_DECL_RE.match(line)
            if match is None:
                continue
            parsed.append((
                match.group("name"),
                match.group("ann"),
                match.group("value").strip(),
                ".".join(name for name, _ in class_stack),
                line_number,
            ))
        return tuple(parsed)

    @staticmethod
    def update_class_stack(
        class_stack: MutableSequence[tuple[str, int]],
        stripped_line: str,
        indent: int,
    ) -> None:
        """Keep class-path stack in sync while iterating constant source lines."""
        class_match = (
            c.Infra.DETECTION_CLASS_DECL_RE.match(stripped_line)
            if stripped_line.startswith("class ") and stripped_line.endswith(":")
            else None
        )
        if class_match is not None:
            while class_stack and class_stack[-1][1] >= indent:
                class_stack.pop()
            class_stack.append((class_match.group(1), indent))
            return
        while class_stack and indent <= class_stack[-1][1]:
            class_stack.pop()


__all__: list[str] = ["FlextInfraUtilitiesCodegen"]
