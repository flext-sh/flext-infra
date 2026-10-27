"""Public release build-policy tests using real workspaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import tarfile
import zipfile
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraReleaseDag:
    """Behavior contract for fail-closed release build policy."""

    @staticmethod
    def test_rendered_plan_selects_member_version_from_workspace_cwd(
        tmp_path: Path,
    ) -> None:
        """The generated recipe selects each repository, not the caller's version."""
        root_version = tm.ok(
            u.Infra.bump_version(
                c.Tests.RELEASE_VERSION_BASE, c.Infra.VersionBump.PATCH
            ),
        )
        member_name = "flext-member"
        workspace = u.Tests.create_release_workspace(
            tmp_path / "release",
            project_names=(member_name,),
            version=root_version,
            initialize_project_git=True,
        )
        rendered_root, _ = u.Tests.render_make_environment(
            tmp_path / "render",
            c.Infra.MakeProfile.STANDALONE,
        )
        rendered = (rendered_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        recipe = rendered.split("_builtin_release_plan:", 1)[1].splitlines()[1]
        command = recipe.strip().removeprefix("@").partition(" $(if ")[0]
        command = command.replace("$(PROJECT_FLEXT_INFRA)", "flext-infra")
        for selected in (workspace, workspace / member_name):
            tm.ok(
                u.Cli.run_checked(
                    [
                        "bash",
                        "-eu",
                        "-c",
                        command.replace("$(PROJECT_ROOT)", str(selected)),
                    ],
                    cwd=workspace,
                ),
            )
            plan = m.Infra.ReleasePlan.model_validate_json(
                (
                    selected / ".reports" / "release" / c.Infra.RELEASE_PLAN_FILENAME
                ).read_text(encoding=c.DEFAULT_ENCODING),
            )
            tm.that(
                plan.current,
                eq=tm.ok(u.Infra.current_workspace_version(selected)),
            )
            tm.that(plan.next, eq=plan.current)
        tm.that(
            tm.ok(u.Infra.current_workspace_version(workspace / member_name)),
            ne=root_version,
        )

    class TestsDryRun:
        """Metadata-only build behavior."""

        @staticmethod
        def test_release_succeeds_in_dry_run_mode(tmp_path: Path) -> None:
            """Create strict reports without persisting package artifacts."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)

            result = u.Tests.run_release_build(workspace, project_name, dry_run=True)

            report = u.Tests.release_build_report(workspace)
            tm.that(result, eq=0)
            tm.that(report.total, eq=1)
            tm.that(report.records[0].project, eq=project_name)
            tm.that(report.records[0].artifacts, eq=())

    class TestsBuildConstraints:
        """Hashed build-toolchain policy behavior."""

        @staticmethod
        def policy_snapshot(workspace: Path, name: str) -> bytes:
            """Read one immutable policy file a build phase snapshotted.

            Returns:
                The resulting ``bytes``.

            """
            return (
                u.Tests.release_report_dir(workspace, c.Tests.RELEASE_VERSION_BASE)
                / "policy"
                / name
            ).read_bytes()

        @staticmethod
        def test_complete_hashed_constraints_build_and_are_attested(
            tmp_path: Path,
        ) -> None:
            """Build only with the complete hashed toolchain and attest its digests."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)

            result = u.Tests.run_release_build(workspace, project_name)

            report = u.Tests.release_build_report(workspace)
            snapshot = TestsFlextInfraReleaseDag.TestsBuildConstraints.policy_snapshot
            gitleaks_path = workspace / c.Infra.RELEASE_GITLEAKS_CONFIG_PATH
            tm.that(result, eq=0)
            tm.that(
                report.build_constraints_sha256,
                eq=hashlib.sha256(
                    snapshot(workspace, "build-constraints.txt"),
                ).hexdigest(),
            )
            tm.that(
                report.gitleaks_policy_sha256,
                eq=hashlib.sha256(gitleaks_path.read_bytes()).hexdigest(),
            )
            tm.that(report.records[0].exit_code, eq=0)

        @staticmethod
        def test_policy_snapshot_pins_every_configured_backend(tmp_path: Path) -> None:
            """The snapshot carries each configured pin with exactly its digests.

            ``uv build --require-hashes`` then accepts precisely the declared
            backend; the typed config is the only owner of those bytes, and a
            second build renders them identically.
            """
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            snapshot = TestsFlextInfraReleaseDag.TestsBuildConstraints.policy_snapshot

            first = u.Tests.run_release_build(workspace, project_name, dry_run=True)
            rendered = snapshot(workspace, "build-constraints.txt").decode("utf-8")
            second = u.Tests.run_release_build(workspace, project_name, dry_run=True)

            pins = config.Infra.release.build_constraints
            tm.that((first, second), eq=(0, 0))
            for pin in pins:
                tm.that(rendered, has=f"{pin.name}=={pin.version} \\")
                for digest in pin.hashes:
                    tm.that(rendered, has=f"--hash=sha256:{digest}")
            tm.that(
                rendered.count("--hash=sha256:"),
                eq=sum(len(pin.hashes) for pin in pins),
            )
            tm.that(rendered, lacks="\\\n\n")
            tm.that(
                snapshot(workspace, "build-constraints.txt").decode("utf-8"),
                eq=rendered,
            )

        @staticmethod
        def test_only_the_gitleaks_policy_is_projected_into_repositories() -> None:
            """Codegen owns the Gitleaks policy everywhere and no constraints file.

            Build constraints render from the typed config at release time; a
            repository ``config/build-constraints.txt`` would be a second owner.
            """
            entries = {
                entry.destination: entry
                for entry in config.Infra.codegen.templates.entries
            }
            gitleaks = entries[c.Infra.RELEASE_GITLEAKS_CONFIG_PATH]
            tm.fail("config/build-constraints.txt" in entries)
            tm.that(set(gitleaks.profiles), eq=set(c.Infra.MakeProfile))
            tm.that(tm.not_none(gitleaks.ownership).policy, eq="full")

    class TestsArchiveBoundary:
        """Publishable archive content policy."""

        @staticmethod
        def test_package_data_may_carry_an_operational_looking_tree(
            tmp_path: Path,
        ) -> None:
            """A `.github` tree inside the package is data, not repository operations.

            flext-infra ships the fleet's `.github` workflow templates as package
            data; only the archive root is an operational boundary.
            """
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            templates = project / "src" / "flext_a" / "templates" / ".github"
            templates.mkdir(parents=True)
            (templates / "ci.yml.j2").write_text("name: CI\n", encoding="utf-8")
            u.Tests.commit_git_changes(project, "package the workflow templates")

            result = u.Tests.run_release_build(workspace, project_name)

            build_log = u.Tests.release_build_log_text(workspace, project_name)
            tm.that(result, eq=0, msg=build_log)
            wheel = next(
                u.Tests.release_artifact_dir(
                    workspace,
                    c.Tests.RELEASE_VERSION_BASE,
                    project_name,
                ).glob("*.whl"),
            )
            with zipfile.ZipFile(wheel) as archive:
                tm.that(archive.namelist(), has="flext_a/templates/.github/ci.yml.j2")

    class TestsMetadata:
        """Publishable metadata policy behavior."""

        @staticmethod
        def test_unavailable_sibling_manifest_fails_release(tmp_path: Path) -> None:
            """Never substitute installed versions for an unavailable release source."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                project_names=(project_name,),
                initialize_project_git=True,
            )
            result = u.Tests.run_release_build(workspace, project_name)
            tm.that(result, ne=0)
            tm.that(
                u.Tests.release_build_log_text(workspace, project_name),
                has="internal dependency version unknown",
            )

        @staticmethod
        def test_missing_hatch_config_fails_before_artifact_build(
            tmp_path: Path,
        ) -> None:
            """Reject committed metadata without the required Hatch boundary."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            pyproject = project / c.PYPROJECT_FILENAME
            content = pyproject.read_text(encoding="utf-8")
            pyproject.write_text(
                content.split("[tool.hatch.build.targets.sdist]", maxsplit=1)[0],
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "remove Hatch release metadata")

            result = u.Tests.run_release_build(workspace, project_name)

            build_log = u.Tests.release_build_log_text(workspace, project_name)
            tm.that(result, eq=1)
            tm.that(build_log, has="release pyproject must define [tool.hatch]")
            tm.that(
                u.Tests.release_artifact_dir(
                    workspace,
                    c.Tests.RELEASE_VERSION_BASE,
                    project_name,
                ).exists(),
                eq=False,
            )

        @staticmethod
        @pytest.mark.parametrize("target", ["build", "wheel", "sdist"])
        def test_hatch_exclusion_cannot_cancel_declared_source(
            tmp_path: Path,
            target: str,
        ) -> None:
            """Reject an archive target that excludes its declared package."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            pyproject = project / c.PYPROJECT_FILENAME
            content = pyproject.read_text(encoding="utf-8")
            header = f"[tool.hatch.build.targets.{target}]\n"
            replacement = header + 'exclude = ["/src/flext_a/**"]\n'
            expected = "Hatch wheel and sdist exclusions must match"
            if target == "build":
                header = "[tool.hatch.build.targets.sdist]\n"
                replacement = (
                    '[tool.hatch.build]\nexclude = ["/src/flext_a/**"]\n\n' + header
                )
                expected = (
                    "Hatch build must use target source patterns without exclusions"
                )
            pyproject.write_text(content.replace(header, replacement), encoding="utf-8")
            u.Tests.commit_git_changes(project, "add conflicting Hatch exclusion")

            result = u.Tests.run_release_build(workspace, project_name, dry_run=True)

            tm.that(result, eq=1)
            tm.that(
                u.Tests.release_build_log_text(workspace, project_name),
                has=expected,
            )

        @staticmethod
        def test_hatch_force_include_rejects_absolute_host_source(
            tmp_path: Path,
        ) -> None:
            """Keep a host path outside the release staging boundary."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            pyproject = project / c.PYPROJECT_FILENAME
            content = pyproject.read_text(encoding="utf-8")
            header = "[tool.hatch.metadata]\n"
            forced = (
                "[tool.hatch.build.targets.wheel.force-include]\n"
                '"/src/host.py" = "host.py"\n\n'
                "[tool.hatch.build.targets.sdist.force-include]\n"
                '"/src/host.py" = "/src/host.py"\n\n'
            )
            pyproject.write_text(
                content.replace(header, forced + header),
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "add absolute Hatch source")

            result = u.Tests.run_release_build(workspace, project_name, dry_run=True)

            tm.that(result, eq=1)
            tm.that(
                u.Tests.release_build_log_text(workspace, project_name),
                has="Hatch source path is outside the release boundary",
            )

        @staticmethod
        def test_hatch_extra_metadata_source_must_ride_in_sdist(
            tmp_path: Path,
        ) -> None:
            """A wheel rebuilt from the sdist needs every extra-metadata source."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            pyproject = project / c.PYPROJECT_FILENAME
            content = pyproject.read_text(encoding="utf-8")
            header = "[tool.hatch.metadata]\n"
            declared = (
                "[tool.hatch.build.targets.wheel.extra-metadata]\n"
                '"NOTICE.md" = "NOTICE.md"\n\n'
            )
            pyproject.write_text(
                content.replace(header, declared + header),
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "add unretained extra metadata")

            result = u.Tests.run_release_build(workspace, project_name, dry_run=True)

            tm.that(result, eq=1)
            tm.that(
                u.Tests.release_build_log_text(workspace, project_name),
                has="Hatch sdist must retain every forced and extra-metadata wheel",
            )

    class TestsGitleaksPolicy:
        """Trusted secret-scanning policy behavior."""

        @staticmethod
        def test_ambient_gitleaks_override_cannot_replace_trusted_policy(
            tmp_path: Path,
        ) -> None:
            """Detect committed secret material despite permissive ambient config."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            synthetic_token = hashlib.sha256(project_name.encode()).hexdigest()
            (project / "credential.txt").write_text(
                # Split literal: fixture writes a synthetic secret for the
                # gitleaks detection path and must not self-match scans.
                "api_" + f'key = "{synthetic_token}"\n',
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "add synthetic secret fixture")
            ambient_policy = tmp_path / "ambient-gitleaks.toml"
            ambient_policy.write_text(
                'title = "permissive ambient policy"\n',
                encoding="utf-8",
            )

            with tm.scope(env={"GITLEAKS_CONFIG": str(ambient_policy)}):
                result = u.Tests.run_release_build(workspace, project_name)

            build_log = u.Tests.release_build_log_text(workspace, project_name)
            tm.that(result, eq=1)
            tm.that(build_log, has="gitleaks detected a secret")

        @staticmethod
        def test_committed_gitleaks_policy_file_is_rejected(tmp_path: Path) -> None:
            """Reject project-owned scanner policy from the committed source set."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            (project / ".gitleaks.toml").write_text(
                'title = "project override"\n',
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "add forbidden scanner policy")

            result = u.Tests.run_release_build(workspace, project_name)

            build_log = u.Tests.release_build_log_text(workspace, project_name)
            tm.that(result, eq=1)
            tm.that(build_log, has="sensitive staged source path: .gitleaks.toml")

        @staticmethod
        def test_codegen_owned_env_example_is_accepted(tmp_path: Path) -> None:
            """A file codegen owns is a projection, never a secret, whatever its name.

            Every generated repository carries `.env.example`; rejecting it by
            its `.env.` prefix blocked the build phase fleet-wide.
            """
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            (project / ".env.example").write_text(
                "FLEXT_A_LOG_LEVEL=INFO\n",
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "add the generated environment example")

            _ = u.Tests.run_release_build(workspace, project_name)

            build_log = u.Tests.release_build_log_text(workspace, project_name)
            tm.that(build_log, lacks="sensitive staged source path")

    class TestsCommittedSource:
        """Immutable committed-source behavior."""

        @staticmethod
        def test_shared_wip_is_preserved_and_only_committed_bytes_ship(
            tmp_path: Path,
        ) -> None:
            """Build the committed SHA, not staged, modified, or untracked bytes."""
            project_name = "flext-a"
            workspace = u.Tests.release_internal_workspace(tmp_path, project_name)
            project = workspace / project_name
            package_file = project / "src" / "flext_a" / "__init__.py"
            committed = package_file.read_bytes()
            oid = u.Tests.git_capture(project, "rev-parse", "HEAD^{commit}").strip()
            package_file.write_bytes(b"# staged release change\n")
            u.Tests.git_bootstrap(project, ("add", "src/flext_a/__init__.py"))
            package_file.write_bytes(b"# uncommitted release change\n")
            added = package_file.parent / "uncommitted.py"
            added.write_bytes(b"# untracked release addition\n")
            prepared = project / "dist" / "nested" / "source-receipt.json"
            prepared.parent.mkdir(parents=True)
            prepared.write_bytes(b'{"uncommitted": true}\n')
            status = u.Tests.git_capture(project, "status", "--porcelain")
            index = u.Tests.git_capture(project, "show", ":src/flext_a/__init__.py")

            tm.that(
                u.Tests.run_release_build(workspace, project_name),
                eq=0,
                msg=u.Tests.release_build_log_text(workspace, project_name),
            )
            report = u.Tests.release_build_report(workspace)
            tm.that(report.records[0].commit_oid, eq=oid)
            tm.that(package_file.read_bytes(), eq=b"# uncommitted release change\n")
            tm.that(added.read_bytes(), eq=b"# untracked release addition\n")
            tm.that(prepared.read_bytes(), eq=b'{"uncommitted": true}\n')
            tm.that(
                u.Tests.git_capture(project, "status", "--porcelain"),
                eq=status,
            )
            tm.that(
                u.Tests.git_capture(project, "show", ":src/flext_a/__init__.py"),
                eq=index,
            )
            artifacts = u.Tests.release_artifact_dir(
                workspace,
                c.Tests.RELEASE_VERSION_BASE,
                project_name,
            )
            with zipfile.ZipFile(next(artifacts.glob("*.whl"))) as archive:
                tm.that(archive.read("flext_a/__init__.py"), eq=committed)
                tm.that(archive.namelist(), lacks="flext_a/uncommitted.py")
                tm.that(
                    any("source-receipt.json" in name for name in archive.namelist()),
                    eq=False,
                )
            with tarfile.open(next(artifacts.glob("*.tar.gz"))) as archive:
                member = next(
                    item
                    for item in archive.getmembers()
                    if item.name.endswith("/src/flext_a/__init__.py")
                )
                with tm.not_none(archive.extractfile(member)) as source:
                    tm.that(source.read(), eq=committed)
                tm.that(
                    any(
                        name.endswith("/uncommitted.py") for name in archive.getnames()
                    ),
                    eq=False,
                )
                tm.that(
                    any("source-receipt.json" in name for name in archive.getnames()),
                    eq=False,
                )
