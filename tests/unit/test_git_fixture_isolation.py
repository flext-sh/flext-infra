"""Regression coverage for real Git fixture process isolation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, tm, u


class TestsFlextInfraGitFixtureIsolation:
    """Tests for ``FlextInfraGitFixtureIsolation``."""

    @u.Tests.fixture
    @staticmethod
    def locked_provider(tmp_path: Path) -> tuple[Path, str, Path]:
        """Give a standalone producer a real provider commit and native lock.

        Returns:
            The producer, declared requirement and private source storage.

        """
        producer = tmp_path / "producer"
        u.Tests.standalone_workspace(producer, "fixture-consumer")
        provider = tmp_path / "provider"
        u.Tests.write_native_resolution_project(provider, "fixture-provider")
        url = u.Tests.repository_ref("fixture-provider").url
        u.Tests.initialize_git_repo(provider, origin_url=url)
        identity = tm.ok(
            u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=provider))
        )
        sha = tm.not_none(identity.head_oid)
        branch = tm.not_none(identity.branch)
        u.Tests.git_bootstrap(
            producer,
            ("fetch", "--no-tags", provider.as_uri(), sha),
            overrides={"GIT_ALLOW_PROTOCOL": "file"},
        )
        metadata = tm.ok(u.Infra.read_project_metadata_result(provider))
        package = m.Infra.LockedPackage(
            name=metadata.project.name,
            version=tm.not_none(metadata.project.version),
            source=m.Infra.LockedPackageSource(git=f"{url}?rev={branch}#{sha}"),
        )
        tm.ok(
            u.Cli.toml_write_mapping(
                producer / c.Infra.UV_LOCK_FILENAME,
                {
                    "version": 1,
                    "package": [
                        package.model_dump(
                            mode="json", by_alias=True, exclude_none=True
                        )
                    ],
                },
            )
        )
        return producer, f"{package.name} @ git+{url}@{branch}", tmp_path / "storage"

    @staticmethod
    def test_locked_dependency_rejects_a_different_declared_ref(
        locked_provider: tuple[Path, str, Path],
    ) -> None:
        """A real locked commit cannot satisfy a different declared Git ref."""
        producer, requirement, storage = locked_provider
        with u.Tests.raises(ValueError, match="differs from its locked Git source"):
            u.Tests.locked_dependency_project(
                producer, storage, f"{requirement}-different"
            )
        tm.that(storage.exists(), eq=False)

    @staticmethod
    def test_locked_dependency_reuse_rejects_modified_source(
        locked_provider: tuple[Path, str, Path],
    ) -> None:
        """A real locked checkout is reusable only while its source stays intact."""
        producer, requirement, storage = locked_provider
        u.Tests.copy_tracked_mise_seeds(producer)
        project = u.Tests.locked_dependency_project(producer, storage, requirement)
        tm.that(
            u.Tests.locked_dependency_project(producer, storage, requirement),
            eq=project,
        )
        source = next((project / c.Infra.DEFAULT_SRC_DIR).glob("*/__init__.py"))
        source.write_text(
            "IDENTITY = 'modified-provider'\n", encoding=c.DEFAULT_ENCODING
        )
        with u.Tests.raises(ValueError, match="differs from its locked checkout"):
            u.Tests.locked_dependency_project(producer, storage, requirement)

    @staticmethod
    def test_initialize_git_repo_ignores_inherited_git_local_environment(
        tmp_path: Path,
    ) -> None:
        """Test initialize git repo ignores inherited git local environment."""
        poison = tmp_path / "poison"
        poison.mkdir()
        tm.ok(u.Cli.run_checked(["git", "init", "-b", "main"], cwd=poison))
        target = tmp_path / "target"
        target.mkdir()
        poisoned_environment = {
            "GIT_DIR": str(poison / c.GIT_DIR_NAME),
            "GIT_WORK_TREE": str(poison),
            "GIT_INDEX_FILE": str(poison / c.GIT_DIR_NAME / "index"),
            "GIT_COMMON_DIR": str(poison / c.GIT_DIR_NAME),
        }
        with tm.scope(env=poisoned_environment):
            u.Tests.initialize_git_repo(target)

        tm.ok((target / c.GIT_DIR_NAME).is_dir())
        resolved = tm.ok(
            u.Cli.capture(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=target,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.GIT_LOCAL_ENV_KEYS,
                ),
            ),
        )
        tm.that(Path(resolved).resolve(), eq=target.resolve())
