"""Elect the project-owned private pytest fixture after test admission.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING

from flext_infra import c, m, u
from flext_infra.workspace.native_setup import FlextInfraNativeSetup

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPytestFixtureElection:
    """Capture one declared fixture from its existing physical owners."""

    @classmethod
    def elect(
        cls,
        context: p.Infra.WorkspaceProjectContext,
        declaration: m.Infra.PytestFixtureConfig,
    ) -> m.Infra.PytestFixture:
        """Bind the original setup qualification to the prepared checkout.

        Returns:
            Authenticated inputs and the elected persistent checkout.

        Raises:
            ValueError: If the declared fixture topology cannot be admitted.

        """
        root = context.cwd
        checkout = declaration.checkout_root
        if (
            sys.platform != "linux"
            or checkout.resolve(strict=True) != checkout
            or not checkout.is_dir()
            or checkout.is_relative_to(root)
            or root.is_relative_to(checkout)
        ):
            msg = "pytest fixture requires a disjoint physical Linux checkout"
            raise ValueError(msg)
        source_paths = cls._sources(context, declaration)
        cls._validate_environment(declaration)
        launcher, compiler = FlextInfraNativeSetup.fixture_tools(declaration.setup_root)
        tool_declaration = cls._capture(
            declaration.setup_root / c.Infra.MISE_TOML_FILENAME
        )
        return m.Infra.PytestFixture(
            checkout_root=checkout,
            isolation=m.Cli.ProcessReadOnlyIsolation(
                platform="linux",
                architecture=launcher.architecture,
                launcher=launcher,
                launcher_declaration=tool_declaration,
                policy_compiler=compiler,
                compiler_declaration=tool_declaration,
                sources=tuple(cls._capture(path) for path in source_paths),
                runtime_trees=(),
                runtime_files=tuple(
                    cls._capture(path) for path in declaration.runtime_files
                ),
                environment=tuple(declaration.environment.items()),
            ),
        )

    @staticmethod
    def capture_runtime_trees(
        roots: tuple[Path, ...],
    ) -> tuple[m.Cli.AtomicPhysicalTreeManifest, ...]:
        """Capture the shared interpreter version for one fixture operation.

        Returns:
            Physical tree manifests that each launched phase must verify.

        """
        started = monotonic()
        trees = tuple(
            m.Cli.AtomicPhysicalTreeManifest.model_validate(
                u.Cli.atomic_inventory_physical_tree(path).unwrap(),
                from_attributes=True,
            )
            for path in roots
        )
        u.Cli.info(
            f"pytest fixture: runtime trees={len(trees)} "
            f"capture_seconds={monotonic() - started:.3f}"
        )
        return trees

    @staticmethod
    def _sources(
        context: p.Infra.WorkspaceProjectContext,
        declaration: m.Infra.PytestFixtureConfig,
    ) -> tuple[Path, ...]:
        root = context.cwd
        git_root = root / c.GIT_DIR_NAME
        if (
            context.identity.repo_root != root
            or context.identity.git_dir != git_root
            or context.identity.common_dir != context.identity.git_dir
            or any(
                path.exists() or path.is_symlink()
                for path in (
                    git_root / "commondir",
                    git_root / "objects" / "info" / "alternates",
                    git_root / "objects" / "info" / "http-alternates",
                )
            )
        ):
            msg = "declared pytest fixture requires independently prepared Git metadata"
            raise ValueError(msg)
        for relative in declaration.git_inputs:
            if not FlextInfraPytestFixtureElection._git_metadata_leaf(relative):
                msg = f"invalid repository-relative fixture Git input: {relative}"
                raise ValueError(msg)
        tracked = u.Infra.git_source_scope_paths(root)
        if tracked is None:
            msg = f"fixture source has no native Git inventory: {root}"
            raise ValueError(msg)
        return (*tracked, *(root / relative for relative in declaration.git_inputs))

    @staticmethod
    def _git_metadata_leaf(relative: Path) -> bool:
        git = Path(c.GIT_DIR_NAME)
        if relative.is_absolute() or ".." in relative.parts:
            return False
        if relative.parent == git:
            return relative.name in {"HEAD", "index", "packed-refs"}
        if relative.is_relative_to(git / "refs"):
            return True
        objects = git / "objects"
        return (
            relative.is_relative_to(objects)
            and relative.parent != objects
            and not relative.is_relative_to(objects / "info")
        )

    @staticmethod
    def _capture(path: Path) -> m.Cli.AtomicFileState:
        if not path.is_absolute() or path.resolve(strict=True) != path:
            msg = f"pytest fixture input is outside its physical declaration: {path}"
            raise ValueError(msg)
        return m.Cli.AtomicFileState.model_validate(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap(),
            from_attributes=True,
        )

    @staticmethod
    def _validate_environment(declaration: m.Infra.PytestFixtureConfig) -> None:
        for name in ("PATH", "LD_LIBRARY_PATH", "TERMINFO"):
            value = declaration.environment.get(name)
            if value is None:
                continue
            for entry in value.split(os.pathsep):
                path = Path(entry)
                if (
                    not path.is_absolute()
                    or path.resolve(strict=True) != path
                    or not (
                        any(
                            path.is_relative_to(root)
                            for root in declaration.runtime_trees
                        )
                        or any(
                            file.is_relative_to(path)
                            for file in declaration.runtime_files
                        )
                    )
                ):
                    msg = f"unqualified fixture environment path for {name}: {path}"
                    raise ValueError(msg)


__all__: list[str] = ["FlextInfraPytestFixtureElection"]
