"""Public release utilities and artifact-boundary behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests import c
from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraReleaseHelpers:
    """Behavior contract for public release helpers and strict boundaries."""

    class TestsPhaseResolution:
        """Release phase alias behavior."""

        @staticmethod
        @pytest.mark.parametrize(
            ("phase", "expected"),
            [
                (c.Infra.RELEASE_PHASE_ALL, c.Tests.ALL_PHASES),
                (c.Tests.RELEASE_PHASE_VALIDATE, (c.Tests.RELEASE_PHASE_VALIDATE,)),
            ],
        )
        def test_resolve_phase_names(phase: str, expected: t.StrSequence) -> None:
            """Resolve aliases and explicit phases through the public utility."""
            tm.that(tuple(u.Infra.resolve_phase_names(phase)), eq=expected)

    class TestsReleaseNotes:
        """Release-note behavior."""

        @staticmethod
        def test_generate_notes_writes_release_document(tmp_path: Path) -> None:
            """Generate notes containing projects and verification lines."""
            notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
            project = u.Tests.create_project_info(tmp_path / "flext-a", name="flext-a")

            result = u.Infra.generate_notes(
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                [project],
                c.Tests.RELEASE_NOTES_CHANGE_LINE,
                notes_path,
            )

            notes = notes_path.read_text(encoding="utf-8")
            tm.ok(result)
            tm.that(notes, has=c.Tests.RELEASE_NOTES_HEADING)
            tm.that(notes, has="- root")
            tm.that(notes, has="- flext-a")
            tm.that(notes, has=c.Tests.RELEASE_NOTES_CHANGE_LINE)
            for verification_line in c.Tests.RELEASE_VERIFICATION_LINES[:2]:
                tm.that(notes, has=verification_line)

        @staticmethod
        def test_generate_notes_failure_returns_result_error(tmp_path: Path) -> None:
            """Return a typed failure when the note path is a directory."""
            notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
            notes_path.mkdir(parents=True, exist_ok=True)

            result = u.Infra.generate_notes(
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                [],
                "",
                notes_path,
            )

            tm.fail(result)
            tm.that(result.error or "", has="failed to write release notes")

    class TestsChangelog:
        """Changelog behavior."""

        @staticmethod
        def test_update_changelog_creates_expected_files(tmp_path: Path) -> None:
            """Create changelog, latest and versioned release documents."""
            workspace = tmp_path / "workspace"
            notes_path = workspace / "notes.md"
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(
                c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8"
            )

            result = u.Infra.update_changelog(
                workspace,
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                notes_path,
            )

            tm.ok(result)
            tm.that((workspace / "docs" / "CHANGELOG.md").is_file(), eq=True)
            tm.that((workspace / "docs" / "releases" / "latest.md").is_file(), eq=True)
            tm.that(
                (
                    workspace / "docs" / "releases" / f"{c.Tests.RELEASE_TAG_TARGET}.md"
                ).is_file(),
                eq=True,
            )

        @staticmethod
        def test_update_changelog_is_idempotent(tmp_path: Path) -> None:
            """Keep one release heading across repeated public updates."""
            workspace = tmp_path / "workspace"
            notes_path = workspace / "notes.md"
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(
                c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8"
            )

            first_result = u.Infra.update_changelog(
                workspace,
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                notes_path,
            )
            second_result = u.Infra.update_changelog(
                workspace,
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                notes_path,
            )

            changelog = (workspace / "docs" / "CHANGELOG.md").read_text(
                encoding="utf-8"
            )
            tm.ok(first_result)
            tm.ok(second_result)
            tm.that(changelog.count(f"## {c.Tests.RELEASE_VERSION_TARGET} - "), eq=1)

        @staticmethod
        def test_update_changelog_adds_default_header(tmp_path: Path) -> None:
            """Add the canonical header when an existing file lacks it."""
            workspace = tmp_path / "workspace"
            docs_dir = workspace / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "CHANGELOG.md").write_text(
                "Existing notes only\n", encoding="utf-8"
            )
            notes_path = workspace / "notes.md"
            notes_path.write_text(
                c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8"
            )

            result = u.Infra.update_changelog(
                workspace,
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                notes_path,
            )

            changelog = (docs_dir / "CHANGELOG.md").read_text(encoding="utf-8")
            tm.ok(result)
            tm.that(changelog, starts=c.Tests.RELEASE_CHANGELOG_HEADER)

        @staticmethod
        def test_update_changelog_missing_notes_returns_failure(tmp_path: Path) -> None:
            """Return a typed failure when source release notes are absent."""
            workspace = tmp_path / "workspace"

            result = u.Infra.update_changelog(
                workspace,
                c.Tests.RELEASE_VERSION_TARGET,
                c.Tests.RELEASE_TAG_TARGET,
                workspace / "missing-notes.md",
            )

            tm.fail(result)
            tm.that(result.error or "", has="changelog update failed")

    class TestsBuildArtifacts:
        """Successful artifact behavior."""

        @staticmethod
        def test_duplicate_project_selectors_build_once(tmp_path: Path) -> None:
            """Build each selected project once with strict modeled artifacts."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                project_name,
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
            tm.that(result, eq=0)
            tm.that(report.total, eq=1)
            tm.that([record.project for record in report.records], eq=[project_name])
            record = report.records[0]
            tm.that(
                sorted(artifact.kind for artifact in record.artifacts),
                eq=["sdist", "wheel"],
            )
            for artifact in record.artifacts:
                artifact_path = Path(artifact.path)
                tm.that(artifact_path.is_file(), eq=True)
                tm.that(len(artifact.sha256), eq=64)
                tm.that(
                    hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
                    eq=artifact.sha256,
                )
            staged_metadata = (
                report_path.parent / "metadata" / f"{project_name}-pyproject.toml"
            ).read_text(encoding="utf-8")
            tm.that(
                staged_metadata, has=f"flext-core=={c.Tests.RELEASE_VERSION_TARGET}"
            )
            tm.that(
                staged_metadata, has=f"flext-tests=={c.Tests.RELEASE_VERSION_TARGET}"
            )
            tm.that(staged_metadata, lacks="git+")
            tm.that(staged_metadata, lacks="[tool.uv")

    class TestsStrictModels:
        """Release report model boundary behavior."""

        @staticmethod
        def test_artifact_rejects_relative_path() -> None:
            """Reject a relative artifact path at the public model boundary."""
            with pytest.raises(c.ValidationError) as exc_info:
                m.Infra.BuildArtifact(
                    path="dist/flext_a-1.0.0-py3-none-any.whl",
                    kind="wheel",
                    sha256="a" * 64,
                )
            tm.that(exc_info.value.errors()[0]["type"], eq="string_pattern_mismatch")
            tm.that(exc_info.value.errors()[0]["loc"], eq=("path",))

        @staticmethod
        def test_build_record_accepts_negative_exit_and_rejects_string(
            tmp_path: Path,
        ) -> None:
            """Retain signal exits as strict integers without coercing strings."""
            record = m.Infra.BuildRecord(
                project="flext-a",
                path=str(tmp_path.resolve()),
                exit_code=-9,
                log=str((tmp_path / "build.log").resolve()),
                artifacts=(),
            )

            tm.that(record.exit_code, eq=-9)
            with pytest.raises(c.ValidationError):
                m.Infra.BuildRecord.model_validate({
                    "project": "flext-a",
                    "path": str(tmp_path.resolve()),
                    "exit_code": "-9",
                    "log": str((tmp_path / "build.log").resolve()),
                })

    class TestsArtifactPersistence:
        """Atomic immutable artifact-set behavior."""

        @staticmethod
        def test_collision_preserves_complete_existing_set(tmp_path: Path) -> None:
            """Fail on immutable collision without partial or temporary output."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            arguments = (
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
            first_result = u.Tests.run_release_main(workspace, *arguments)
            artifact_dir = u.Tests.release_artifact_dir(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            )
            original_names = tuple(path.name for path in sorted(artifact_dir.iterdir()))
            collided_artifact = min(artifact_dir.iterdir())
            collided_artifact.write_bytes(b"immutable collision\n")

            second_result = u.Tests.run_release_main(workspace, *arguments)

            current_names = tuple(path.name for path in sorted(artifact_dir.iterdir()))
            build_log = u.Tests.release_build_log(
                workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
            ).read_text(encoding="utf-8")
            temporary_sets = tuple(
                path.name
                for path in artifact_dir.parent.iterdir()
                if path.name.startswith(f".{project_name}-")
            )
            report_dir = u.Tests.release_report_dir(
                workspace, c.Tests.RELEASE_VERSION_TARGET
            )
            temporary_builds = tuple(report_dir.glob(f"{project_name}-*"))
            tm.that(first_result, eq=0)
            tm.that(second_result, eq=1)
            tm.that(current_names, eq=original_names)
            tm.that(collided_artifact.read_bytes(), eq=b"immutable collision\n")
            tm.that(temporary_sets, eq=())
            tm.that(temporary_builds, eq=())
            tm.that(build_log, has="immutable artifact collision")

        @staticmethod
        def test_unexpected_uv_output_is_rejected_without_artifacts(
            tmp_path: Path,
        ) -> None:
            """Reject a real Hatch build that emits a third output entry."""
            project_name = "flext-a"
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )
            project = workspace / project_name
            pyproject = project / "pyproject.toml"
            wheel_target = "[tool.hatch.build.targets.sdist]"
            pyproject.write_text(
                pyproject.read_text(encoding="utf-8").replace(
                    wheel_target,
                    "[tool.hatch.build.hooks.custom]\n"
                    'path = "src/flext_a/build_hook.py"\n\n'
                    f"{wheel_target}",
                ),
                encoding="utf-8",
            )
            (project / "src" / "flext_a" / "build_hook.py").write_text(
                "from pathlib import Path\n"
                "from hatchling.builders.hooks.plugin.interface import "
                "BuildHookInterface\n\n"
                "class CustomBuildHook(BuildHookInterface):\n"
                '    PLUGIN_NAME = "custom"\n\n'
                "    def finalize(self, version, build_data, artifact_path):\n"
                "        Path(self.directory, 'unexpected.txt').write_text("
                "'unexpected\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            u.Tests.commit_git_changes(project, "emit unexpected build output")

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
            tm.that(build_log, has="uv build emitted unexpected output")
            tm.that(build_log, has="unexpected.txt")
            tm.that(
                u.Tests.release_artifact_dir(
                    workspace, c.Tests.RELEASE_VERSION_TARGET, project_name
                ).exists(),
                eq=False,
            )
