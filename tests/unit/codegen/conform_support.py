"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from difflib import unified_diff
from fnmatch import fnmatchcase
from pathlib import Path

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, tm, u


class TestsFlextInfraConformSupport:
    """Shared project fixtures for conformance and Make runtime contracts."""

    @staticmethod
    def conform_target(
        root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        make_profile: c.Infra.MakeProfile,
    ) -> m.Infra.RepositoryConformTarget:
        """Build the current public target without retired branch-policy fields.

        Returns:
            The resulting ``m.Infra.RepositoryConformTarget``.

        """
        return m.Infra.RepositoryConformTarget(
            repository=repository,
            root=root,
            toolchain_root=root,
            make_profile=make_profile,
            beads=u.Tests.beads_project(repository.name),
            canonical_project_name=repository.distribution,
            ci_enabled=True,
        )

    @staticmethod
    def standalone_workspace(root: Path) -> m.Infra.WorkspaceSpec:
        """Load the smallest repository-local topology for conform tests.

        Returns:
            The resulting ``m.Infra.WorkspaceSpec``.

        """
        return u.Tests.standalone_workspace(root)

    @staticmethod
    def conform_in_workspace(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Execute one conform request against a pre-declared workspace topology.

        Returns:
            The conformance outcome of the bound executor.

        """
        return FlextInfraCodegenConform.Generate(
            state=m.Infra.CodegenConformState(
                repository_root=request.root,
                request=request,
                initial_workspace=workspace,
                ports=infra.codegen_conform_collaborators(),
            ),
            runtime_settings=infra.settings,
            initial_context=infra.context,
        ).execute()

    @staticmethod
    def apply_conform_surface(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        surface: c.Infra.CodegenConformSurface,
    ) -> None:
        """Materialize one exact public conform surface for a focused test."""
        request = u.Tests.conform_request(
            root,
            what=surface,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(
            TestsFlextInfraConformSupport.conform_in_workspace(request, workspace),
        )

    @staticmethod
    def project_tree(root: Path) -> tuple[tuple[str, bytes], ...]:
        """Return the versionable project tree independently of Git test fixtures.

        Returns:
            The versionable project tree independently of Git test fixtures.

        """
        ignored_directories = tuple(
            artifact.name
            for artifact in config.Infra.codegen.artifacts
            if artifact.ignore and not artifact.generated_source and artifact.is_dir
        )
        ignored_files = tuple(
            artifact.name
            for artifact in config.Infra.codegen.artifacts
            if artifact.ignore and not artifact.generated_source and not artifact.is_dir
        )
        return tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
                and c.GIT_DIR_NAME not in path.relative_to(root).parts
                and ".infra-baseline" not in path.relative_to(root).parts
                and c.Infra.TRANSACTION_STATE_DIRNAME
                not in path.relative_to(root).parts
                and not any(
                    fnmatchcase(part, pattern)
                    for part in path.relative_to(root).parts[:-1]
                    for pattern in ignored_directories
                )
                and not any(
                    fnmatchcase(path.name, pattern) for pattern in ignored_files
                )
            ),
        )

    @staticmethod
    def project_tree_diff(
        expected: tuple[tuple[str, bytes], ...],
        actual: tuple[tuple[str, bytes], ...],
    ) -> str:
        """Render only differing generated files when a fixed-point contract fails.

        Returns:
            The resulting ``str``.

        """
        expected_files = dict(expected)
        actual_files = dict(actual)
        return "\n".join(
            line
            for path in sorted(expected_files.keys() | actual_files.keys())
            if expected_files.get(path) != actual_files.get(path)
            for line in unified_diff(
                expected_files
                .get(path, b"")
                .decode(errors=c.MergeStrategy.REPLACE)
                .splitlines(),
                actual_files
                .get(path, b"")
                .decode(errors=c.MergeStrategy.REPLACE)
                .splitlines(),
                fromfile=f"created/{path}",
                tofile=f"conformed/{path}",
                lineterm="",
            )
        )

    @staticmethod
    def seed_infra_package_tree(root: Path) -> None:
        """Seed the minimal flext-infra tree (pyproject, src, tests, Mise seeds).

        The conform templates materialize tests/fixtures/ci/docker/*, and the
        existing-tree tooling render discovers python roots from directories that
        exist on disk (env_dirs). Seeding tests/ makes the first render match the
        post-apply fixed point.
        """
        dist = u.Tests.repository_ref(config.Infra.name).distribution
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.PYPROJECT_FILENAME,
                f'[project]\nname = "{dist}"\nversion = "0.12.0.dev0"\n'
                'description = "Existing repository fixture"\n'
                f"requires-python = "
                f'"{config.Infra.codegen.toolchain.python_required_version}"\n'
                'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
                f'license = "{u.Tests.project_spec(dist).license}"\n'
                'dependencies = ["flext-cli"]\n',
            ),
        )
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        tests_init = root / "tests" / "__init__.py"
        tests_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(tests_init, ""))
        # Native formatting authenticates the committed declaration and its lock
        # together before conform can render a replacement declaration.
        u.Tests.copy_tracked_mise_seeds(root)

    @staticmethod
    def self_check_conform_service(
        root: Path,
    ) -> tuple[FlextInfraCodegenConform.Generate, m.Infra.CodegenConformRequest]:
        """Materialize the standalone root fixture and its CHECK-mode conform service.

        Returns:
            The resulting ``tuple[FlextInfraCodegenConform.Generate,
                m.Infra.CodegenConformRequest]``.

        """
        repository = u.Tests.repository_ref("flext-infra").model_copy(
            update={"path": Path()},
        )
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        (root / c.PYPROJECT_FILENAME).write_text(
            f"[project]\nname = '{repository.distribution}'\nversion = '0.1.0'\n",
            encoding="utf-8",
        )
        package = root / "src" / repository.distribution.replace("-", "_")
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        return TestsFlextInfraConformSupport.check_conform_service(root, workspace)

    @staticmethod
    def check_conform_service(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        *,
        what: c.Infra.CodegenConformSurface = c.Infra.CodegenConformSurface.ALL,
    ) -> tuple[FlextInfraCodegenConform.Generate, m.Infra.CodegenConformRequest]:
        """Build the CHECK-mode conform service bound to one declared workspace.

        Returns:
            The resulting ``tuple[FlextInfraCodegenConform.Generate,
                m.Infra.CodegenConformRequest]``.

        """
        request = u.Tests.conform_request(
            root,
            what=what,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform.Generate(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root,
                request=request,
                initial_workspace=workspace,
            ),
        )
        return service, request
