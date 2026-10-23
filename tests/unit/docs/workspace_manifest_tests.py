"""Legacy manifest validation stays separate from Git topology and codegen policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config
from tests import c, t, tm, u

_PROBE = "flext-probe"


class TestsFlextInfraWorkspaceManifest:
    """Classification of a checkout as a fleet umbrella."""

    @staticmethod
    @pytest.mark.parametrize(
        ("target_path", "valid"),
        [
            (".", True),
            ("nested/candidate", True),
            ("${HOME}", True),
            ("", False),
            (" ", False),
            ("/absolute/candidate", False),
        ],
    )
    def test_bootstrap_paths_public_manifest_loading(
        tmp_path: Path,
        target_path: str,
        *,
        valid: bool,
    ) -> None:
        """Keep relative paths unexpanded and reject empty or absolute paths."""
        manifest = u.Tests.write_standalone_workspace_manifest(tmp_path, _PROBE)
        tm.ok(
            u.Cli.yaml_dump(
                manifest,
                {
                    **tm.ok(u.Cli.yaml_safe_load(manifest)),
                    "candidate_bootstrap_targets": [
                        {
                            "path": target_path,
                            "what": c.Infra.CodegenConformSurface.MAKEFILE.value,
                        },
                    ],
                },
            ),
        )

        result = u.Infra.load_workspace_manifest(tmp_path)
        if not valid:
            tm.ok(result.failure)
            return
        loaded = tm.ok(result)[0]
        tm.that(loaded.candidate_bootstrap_targets[0].path, eq=Path(target_path))
        tm.that(
            loaded.candidate_bootstrap_targets[0].what
            is c.Infra.CodegenConformSurface.MAKEFILE,
            eq=True,
        )
        tm.that(u.Infra.repository_nonparticipant_paths(tmp_path), empty=True)
        tm.that(
            u.Infra.load_refactor_config(tmp_path).project_scan_dirs,
            eq=config.Infra.source_scan.roots,
        )

    @staticmethod
    @pytest.mark.parametrize("payload", ["version: invalid\n", "{}\n"])
    def test_invalid_legacy_manifest_does_not_own_discovery(
        tmp_path: Path,
        payload: str,
    ) -> None:
        """Legacy errors remain visible without supplying topology or policy."""
        manifest = u.Infra.workspace_manifest_path(tmp_path)
        manifest.parent.mkdir(parents=True)
        manifest.write_text(payload, encoding=c.DEFAULT_ENCODING)
        tm.ok(u.Infra.load_workspace_manifest(tmp_path).failure)
        tm.that(u.Infra.repository_nonparticipant_paths(tmp_path), empty=True)
        tm.fail(u.Infra.fleet_umbrella(tmp_path))
        tm.that(
            u.Infra.load_refactor_config(tmp_path).project_scan_dirs,
            eq=config.Infra.source_scan.roots,
        )

    @staticmethod
    def test_manifest_path_is_derived_from_the_declared_names(
        tmp_path: Path,
    ) -> None:
        """The path is built from the configured directory and filename."""
        resolved = u.Infra.workspace_manifest_path(tmp_path)

        tm.that(resolved.name, eq=c.Infra.WORKSPACE_MANIFEST_FILENAME)
        tm.that(resolved.parent.name, eq=c.CONFIG_DIR_NAME)
        tm.that(resolved.parent.parent, eq=tmp_path)

    @staticmethod
    def test_a_checkout_without_the_manifest_is_not_an_umbrella(
        tmp_path: Path,
    ) -> None:
        """Absence of the manifest is the ordinary case for a project."""
        tm.fail(u.Infra.fleet_umbrella(tmp_path))

    @staticmethod
    def test_a_standalone_manifest_does_not_make_an_umbrella(
        tmp_path: Path,
    ) -> None:
        """A governed standalone project keeps its project documentation shape."""
        written = u.Tests.write_standalone_workspace_manifest(tmp_path, _PROBE)

        tm.that(written, eq=u.Infra.workspace_manifest_path(tmp_path))
        tm.fail(u.Infra.fleet_umbrella(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_git_members_declare_a_fleet_umbrella(
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """Git composition, not a legacy role, selects aggregate documentation."""
        u.Tests.write_standalone_workspace_manifest(
            tmp_path,
            _PROBE,
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        if declared:
            u.Tests.WorktreeFixture.write_gitmodules(tmp_path, (_PROBE,))
        tm.that(u.Infra.fleet_umbrella(tmp_path), eq=declared)

    @staticmethod
    def test_a_beads_override_never_makes_a_checkout_an_umbrella(
        tmp_path: Path,
    ) -> None:
        """The exact regression: every project carries the Beads override.

        Reading it here classified every standalone project as a fleet
        umbrella, which is what silently dropped their README and project docs.
        """
        written = u.Tests.write_project_beads_config(tmp_path, _PROBE)

        tm.ok(written.is_file())
        tm.fail(u.Infra.fleet_umbrella(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("scan_dirs", [None, [""]])
    def test_invalid_codegen_cannot_supply_default_refactor_settings(
        tmp_path: Path,
        scan_dirs: t.JsonValue,
    ) -> None:
        """The compiled codegen owner rejects invalid declared refactor inputs."""
        directory = tmp_path / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                directory / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "refactor": {"project_scan_dirs": scan_dirs},
                            },
                        },
                    },
                },
            ),
        )
        loaded = u.Infra.load_codegen_inputs(tmp_path)
        tm.fail(loaded, has="project_scan_dirs")
        tm.ok(isinstance(loaded.exception, c.ValidationError))
        with pytest.raises(RuntimeError, match="project_scan_dirs") as raised:
            u.Infra.load_refactor_config(tmp_path)
        tm.ok(isinstance(raised.value.__cause__, c.ValidationError))
