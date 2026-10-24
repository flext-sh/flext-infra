"""Declared remote validation contract for native project initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from flext_infra import FlextInfraConfig, config
from flext_infra.codegen.make_bootstrap import FlextInfraCodegenMakeBootstrap
from tests import c, m, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenProjectNewValidation:
    """Prove declared bootstrap remotes are validated before any effect."""

    @staticmethod
    def _service(
        root: Path,
        *,
        source: str | None = None,
        origin_url: str | None = None,
    ) -> FlextInfraCodegenMakeBootstrap:
        """Prepare declared Git inputs before invoking the native init service.

        Returns:
            The apply-mode initializer bound to the prepared repository.

        """
        root.mkdir()
        repository = u.Tests.repository_ref(
            root.name,
            role=c.Infra.MakeProfile.STANDALONE,
        )
        integration = u.Tests.integration()
        u.Tests.initialize_unborn_git_repo(
            root,
            origin_url=origin_url or repository.url,
            branch=integration.branch,
        )
        beads = u.Tests.beads_project(repository.name)
        u.Tests.write_beads_project(
            root,
            workspace=beads.workspace,
            database=beads.database,
            issue_prefix=beads.issue_prefix,
        )
        project = u.Tests.project_spec(repository.name)
        if source is not None:
            project = project.model_copy(update={"flext_source": source})
        declaration = m.Infra.RepositoryDeltaSpec(
            project=project,
            integration=integration,
            kind=repository.kind,
        )
        _, own, _ = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        own.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                own,
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json", exclude_unset=True
                            ),
                        },
                    },
                },
            )
        )
        return FlextInfraCodegenMakeBootstrap(
            repository_root=root,
            kind=repository.kind,
            apply_changes=True,
        )

    def test_whitespace_flext_ref_is_rejected_without_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """A whitespace-only dependency ref fails before publication."""
        root = tmp_path / "project"
        dependency = u.Tests.repository_ref(config.Infra.name)
        service = self._service(
            root,
            source=f"{dependency.distribution} @ git+{dependency.url}@   ",
        )
        before = TestsFlextInfraConformSupport.project_tree(root)
        tm.fail(service.execute(), has="must declare a branch or ref")
        tm.that(TestsFlextInfraConformSupport.project_tree(root), eq=before)

    def test_hostless_flext_url_is_rejected_without_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """A dependency URL without a host fails before publication."""
        root = tmp_path / "project"
        dependency = u.Tests.repository_ref(config.Infra.name)
        service = self._service(
            root,
            source=(
                f"{dependency.distribution} @ git+https:///{dependency.name}.git@"
                f"{u.Tests.provider_branch()}"
            ),
        )
        before = TestsFlextInfraConformSupport.project_tree(root)
        tm.fail(service.execute(), has="must name a host and repository path")
        tm.that(TestsFlextInfraConformSupport.project_tree(root), eq=before)

    def test_unparseable_origin_is_rejected_without_effects(
        self,
        tmp_path: Path,
    ) -> None:
        """A project origin that is not a Git URL fails before any effect."""
        root = tmp_path / "project"
        service = self._service(root, origin_url="not-a-url")
        before = TestsFlextInfraConformSupport.project_tree(root)
        tm.fail(service.execute(), has="Git origin must name an owner and repository")
        tm.that(TestsFlextInfraConformSupport.project_tree(root), eq=before)

    @staticmethod
    def test_ssh_origin_canonicalizes_to_https() -> None:
        """The declared origin is stored in its canonical HTTPS form."""
        repository = u.Tests.repository_ref(config.Infra.name)
        origin = urlsplit(repository.url)
        canonical = u.Infra.validate_git_remote_url(
            f"git@{origin.netloc}:{origin.path.lstrip('/')}",
        )
        tm.ok(canonical)
        tm.that(canonical.value, eq=repository.url)

    @staticmethod
    def test_surrounding_whitespace_is_stripped_before_validation() -> None:
        """A padded but valid URL validates to the same canonical form."""
        padded = f"  {u.Tests.repository_ref(config.Infra.name).url}  "
        canonical = u.Infra.validate_git_remote_url(padded)
        tm.ok(canonical)
        tm.that(canonical.value, eq=u.Tests.repository_ref(config.Infra.name).url)

    @staticmethod
    def test_pathless_url_is_rejected() -> None:
        """A URL naming only a host carries no repository identity."""
        origin = urlsplit(u.Tests.repository_ref(config.Infra.name).url)
        result = u.Infra.validate_git_remote_url(f"{origin.scheme}://{origin.netloc}")
        tm.fail(result, has="must name a host and repository path")
