"""Public release build-policy tests using real workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from flext_tests import tm

from tests import c, m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleaseDag:
    """Behavior contract for fail-closed release build policy."""

    class TestsDryRun:
        """Metadata-only build behavior."""

        @staticmethod
        def test_release_succeeds_in_dry_run_mode(tmp_path: Path) -> None:
            """Create strict reports without persisting package artifacts."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--dry-run",
            )

            report_dir = u.Tests.release_report_dir(
                workspace, c.Tests.RELEASE_VERSION_BASE
            )
            report = m.Infra.BuildReport.model_validate_json(
                (report_dir / "build-report.json").read_text(encoding="utf-8")
            )
            tm.that(result, eq=0)
            tm.that(report.total, eq=1)
            tm.that(report.records[0].project, eq=project_name)
            tm.that(report.records[0].artifacts, eq=())

        @staticmethod
        def test_validate_only_skips_release_artifacts(tmp_path: Path) -> None:
            """Skip release reports when only validation is selected."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VALIDATE,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--dry-run",
            )

            tm.that(result, eq=0)
            tm.that((workspace / ".reports" / "release").exists(), eq=False)

    class TestsBuildConstraints:
        """Hashed build-toolchain policy behavior."""

        @staticmethod
        def test_complete_hashed_constraints_build_and_are_attested(
            tmp_path: Path,
        ) -> None:
            """Build only with the complete hashed toolchain and attest its digest."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            constraints_path = workspace / c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            report_path = (
                u.Tests.release_report_dir(workspace, c.Tests.RELEASE_VERSION_TARGET)
                / "build-report.json"
            )
            report = m.Infra.BuildReport.model_validate_json(
                report_path.read_text(encoding="utf-8")
            )
            expected_digest = hashlib.sha256(constraints_path.read_bytes()).hexdigest()
            gitleaks_path = workspace / c.Infra.RELEASE_GITLEAKS_CONFIG_PATH
            expected_gitleaks_digest = hashlib.sha256(
                gitleaks_path.read_bytes()
            ).hexdigest()
            tm.that(result, eq=0)
            tm.that(report.build_constraints_sha256, eq=expected_digest)
            tm.that(report.gitleaks_policy_sha256, eq=expected_gitleaks_digest)
            tm.that(report.records[0].exit_code, eq=0)

        @staticmethod
        def test_incomplete_hashed_constraints_fail_before_build(
            tmp_path: Path,
        ) -> None:
            """Reject a valid hash record that omits required toolchain members."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            constraints_path = workspace / c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH
            first_record = "\n".join(
                constraints_path.read_text(encoding="utf-8").splitlines()[:3]
            )
            constraints_path.write_text(first_record + "\n", encoding="utf-8")

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            tm.that(result, eq=1)
            tm.that(build_log, has="release build toolchain mismatch")
            tm.that(build_log, has="packaging")

    class TestsMetadata:
        """Publishable metadata policy behavior."""

        @staticmethod
        def test_missing_hatch_config_fails_before_artifact_build(
            tmp_path: Path,
        ) -> None:
            """Reject committed metadata without the required Hatch boundary."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            project = workspace / project_name
            pyproject = project / "pyproject.toml"
            content = pyproject.read_text(encoding="utf-8")
            pyproject.write_text(
                content.split("[tool.hatch.build.targets.sdist]", maxsplit=1)[0],
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "remove Hatch release metadata")

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            tm.that(result, eq=1)
            tm.that(build_log, has="release pyproject must define [tool.hatch]")
            tm.that(
                u.Tests.release_artifact_dir(
                    workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
                ).exists(),
                eq=False,
            )

    class TestsGitleaksPolicy:
        """Trusted secret-scanning policy behavior."""

        @staticmethod
        def test_ambient_gitleaks_override_cannot_replace_trusted_policy(
            tmp_path: Path,
        ) -> None:
            """Detect committed secret material despite permissive ambient config."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            project = workspace / project_name
            synthetic_token = "AKIA" + "Q7Z9X2W4V6B8N3M5"
            (project / "credential.txt").write_text(
                f"AWS_ACCESS_KEY_ID={synthetic_token}\n", encoding="utf-8"
            )
            u.Tests.commit_git_changes(project, "add synthetic secret fixture")
            ambient_policy = tmp_path / "ambient-gitleaks.toml"
            ambient_policy.write_text(
                'title = "permissive ambient policy"\n', encoding="utf-8"
            )

            with tm.scope(env={"GITLEAKS_CONFIG": str(ambient_policy)}):
                result = u.Tests.run_release_main(
                    workspace,
                    "--phase",
                    c.Tests.RELEASE_PHASE_BUILD,
                    "--version",
                    c.Tests.RELEASE_VERSION_TARGET,
                    "--projects",
                    project_name,
                    "--interactive",
                    "0",
                    "--create-branches",
                    "0",
                    "--apply",
                )

            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            tm.that(result, eq=1)
            tm.that(build_log, has="gitleaks detected a secret")

        @staticmethod
        def test_committed_gitleaks_policy_file_is_rejected(tmp_path: Path) -> None:
            """Reject project-owned scanner policy from the committed source set."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            project = workspace / project_name
            (project / ".gitleaks.toml").write_text(
                'title = "project override"\n', encoding="utf-8"
            )
            u.Tests.commit_git_changes(project, "add forbidden scanner policy")

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            tm.that(result, eq=1)
            tm.that(build_log, has="sensitive staged source path: .gitleaks.toml")

    class TestsCommittedSource:
        """Immutable committed-source behavior."""

        @staticmethod
        def test_dirty_committed_member_is_rejected(tmp_path: Path) -> None:
            """Reject a project whose committed source has working-tree changes."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            package_file = workspace / project_name / "src" / "flext_a" / "__init__.py"
            package_file.write_text("# uncommitted release change\n", encoding="utf-8")

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            tm.that(result, eq=1)
            tm.that(build_log, has="release project is dirty")
            tm.that(
                u.Tests.release_artifact_dir(
                    workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
                ).exists(),
                eq=False,
            )

        @staticmethod
        def test_member_without_git_repository_is_rejected(tmp_path: Path) -> None:
            """Reject a project that lacks a committed Git source identity."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,)
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)
