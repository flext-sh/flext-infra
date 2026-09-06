"""Project identity and spec fixture test utilities for flext-infra."""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import config, u
from flext_tests import tm
from tests import c, m, t


class TestsFlextInfraUtilitiesProjectFixtureMixin:
    """Typed project identity, spec, and manifest-seed fixture helpers."""

    @staticmethod
    def provider(name: str = "flext-sh") -> m.Infra.ProviderSpec:
        """Resolve one explicitly named provider for repository fixtures."""
        providers = tuple(
            provider
            for provider in config.Infra.codegen.providers
            if provider.name == name
        )
        tm.that(len(providers), eq=1, msg="fixture provider must resolve once")
        (provider,) = providers
        return provider

    @staticmethod
    def repository_ref(
        name: str,
        *,
        role: c.Infra.MakeProfile | None = None,
        path: Path | None = None,
    ) -> m.Infra.RepositoryRef:
        """Build a repository reference from the provider contract.

        flext-infra owns no catalog of projects, so a test that needs a
        repository declares the one it means instead of borrowing a row
        from a registry. Only the provider contract (generic policy) is
        read from config, which keeps the fixture valid for any provider.

        A non-empty path denotes the root's view of one subproject. The
        subproject still classifies itself as standalone; only its checkout
        relationship is ``submodule``.
        """
        provider = TestsFlextInfraUtilitiesProjectFixtureMixin.provider()
        resolved_path = Path() if path is None else path
        is_subproject = bool(resolved_path.parts)
        resolved_role = role or (
            c.Infra.MakeProfile.STANDALONE
            if is_subproject
            else c.Infra.MakeProfile.WORKSPACE
        )
        return m.Infra.RepositoryRef(
            name=name,
            distribution=name,
            url=f"{provider.base_url.rstrip('/')}/{name}.git",
            path=resolved_path,
            role=resolved_role,
            provider=provider.name,
            checkout=(
                c.Infra.CheckoutKind.SUBMODULE
                if is_subproject
                else c.Infra.CheckoutKind.ROOT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=is_subproject,
            read_only=False,
        )

    @staticmethod
    def beads_project(name: str) -> m.Infra.BeadsProjectSpec:
        """Build portable Beads identity for one repository fixture."""
        return m.Infra.BeadsProjectSpec(
            version=c.Infra.BEADS_CONFIG_VERSION,
            workspace=name,
            database=name.replace("-", "_"),
            issue_prefix=name,
        )

    @staticmethod
    def project_spec(name: str) -> m.Infra.ProjectSpec:
        """Build deterministic scaffold metadata for one project fixture."""
        package_name = name.replace("-", "_")
        class_stem = u.derive_class_stem(name)
        homepage = (
            f"{TestsFlextInfraUtilitiesProjectFixtureMixin.provider().base_url.rstrip('/')}/"
            f"{name}"
        )
        return m.Infra.ProjectSpec(
            package_name=package_name,
            class_stem=class_stem,
            namespace=class_stem.removeprefix("Flext") or class_stem,
            constant_name=name,
            namespace_attribute=package_name,
            alias=u.Infra.package_alias(package_name=package_name),
            environment_prefix=f"{package_name.upper()}_",
            description=f"{class_stem} test project",
            license=config.Infra.codegen.scaffold.project.supported_licenses[0],
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream=(
                config.Infra.codegen.scaffold.project.dependency_profiles[
                    0
                ].upstream
            ),
            homepage=homepage,
            documentation=homepage,
            workspace_root_rel=".",
            year=2026,
        )

    @staticmethod
    def write_beads_project(
        repository: Path, *, workspace: str, database: str, issue_prefix: str
    ) -> Path:
        """Write the typed repository-local Beads identity fixture.

        The bytes mirror the managed ``config/beads.yaml.j2`` render for
        the same spec, so a planned regeneration of an existing fixture
        file is never reported as drift.
        """
        path = repository / "config" / "beads.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        spec = m.Infra.BeadsProjectSpec(
            version=c.Infra.BEADS_CONFIG_VERSION,
            workspace=workspace,
            database=database,
            issue_prefix=issue_prefix,
        )
        path.write_text(
            f"version: {spec.version}\n"
            f"workspace: {json.dumps(spec.workspace)}\n"
            f"database: {json.dumps(spec.database)}\n"
            f"issue_prefix: {json.dumps(spec.issue_prefix)}\n\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def declare_workspace_projects(
        repository: Path, projects: t.StrSequence
    ) -> Path:
        """Declare the exact governed projects in this root's ``.gitmodules``."""
        provider = config.Infra.codegen.providers[0]
        path = repository / c.Infra.GITMODULES
        path.write_text(
            "".join(
                f'[submodule "{project}"]\n'
                f"\tpath = {project}\n"
                f"\turl = {provider.base_url.rstrip('/')}/{Path(project).name}.git\n"
                f"\tbranch = {provider.branch}\n"
                for project in projects
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def write_project_beads_config(project_dir: Path, name: str) -> Path:
        """Write a standalone project's required local topology input."""
        return TestsFlextInfraUtilitiesProjectFixtureMixin.write_beads_project(
            project_dir, workspace=name, database=name, issue_prefix=name
        )

    @staticmethod
    def is_project_valid(project_name: str) -> bool:
        """Validate the lightweight project-name fixture contract."""
        return (
            bool(project_name)
            and project_name.replace("-", "").replace("_", "").isalnum()
        )


__all__: list[str] = ["TestsFlextInfraUtilitiesProjectFixtureMixin"]
