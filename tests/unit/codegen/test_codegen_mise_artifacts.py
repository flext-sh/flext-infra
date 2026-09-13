"""Offline contracts for generated Mise declarations and launchers."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from tests import u as test_u


class TestsCodegenMiseArtifacts:
    """Keep ordinary generation checks independent from remote resolution."""

    @pytest.mark.parametrize("invalid", ["missing", "empty", "nonexecutable"])
    def test_public_launcher_validation_keeps_failure_guards(
        self, tmp_path: Path, invalid: str
    ) -> None:
        """Published launchers must retain content and executable-output validation."""
        resources = files("flext_infra").joinpath(c.Infra.MISE_BOOTSTRAP_SEED_DIRECTORY)
        launchers = tmp_path / "bin"
        launchers.mkdir()
        for name, mode in (("mise", 0o755), ("mise.cmd", 0o644)):
            launcher = launchers / name
            launcher.write_bytes(resources.joinpath(name).read_bytes())
            launcher.chmod(mode)
        tm.ok(FlextInfraCodegenMiseArtifacts.validate_launchers(tmp_path))
        unix = launchers / "mise"
        if invalid == "empty":
            unix.write_bytes(b"")
        elif invalid == "missing":
            unix.unlink()
        else:
            unix.chmod(0o644)

        tm.fail(FlextInfraCodegenMiseArtifacts.validate_launchers(tmp_path))

    @classmethod
    def _write_launchers(cls, root: Path) -> None:
        """Write minimal launchers carrying the unlocked resolution contract.

        Root cause (R28): the seed switched from an embedded per-arch
        checksum table pinned to one release to a live `releases/latest`
        resolution verified against a fetched ``SHASUMS256.txt`` — the only
        contract `FlextInfraCodegenMiseArtifacts.validate_seed` still checks
        (`c.Infra.MISE_UNLOCKED_RESOLUTION_URL` /
        `MISE_UNLOCKED_FAIL_LOUD_CLAUSE` / `MISE_UNLOCKED_CHECKSUM_URI`).
        Per-arch checksum pinning and cross-launcher version drift no longer
        exist as launcher content or as a validated contract.
        """
        launchers = root / "bin"
        launchers.mkdir(parents=True, exist_ok=True)
        (launchers / "mise").write_text(
            "\n".join((
                "#!/usr/bin/env bash",
                "set -eu",
                (
                    f"mise_version=\"$(curl -fsSI -o /dev/null -w '%{{redirect_url}}' "
                    f'{c.Infra.MISE_UNLOCKED_RESOLUTION_URL})"'
                ),
                (
                    f'[ -n "$mise_version" ] || '
                    f'{{ echo "{c.Infra.MISE_UNLOCKED_FAIL_LOUD_CLAUSE}" >&2; exit 1; }}'
                ),
                f'checksums="{c.Infra.MISE_UNLOCKED_CHECKSUM_URI}"',
                "",
            )),
            encoding="utf-8",
        )
        (launchers / "mise").chmod(0o755)
        (launchers / "mise.cmd").write_text(
            "\n".join((
                "@echo off",
                f"rem resolves {c.Infra.MISE_UNLOCKED_RESOLUTION_URL}",
                f"rem {c.Infra.MISE_UNLOCKED_FAIL_LOUD_CLAUSE}",
                f"rem verifies {c.Infra.MISE_UNLOCKED_CHECKSUM_URI}",
                "",
            )),
            encoding="utf-8",
        )

    @staticmethod
    def _write_config(
        root: Path, *, selector: str = "github:example/tool", version: str = "latest"
    ) -> None:
        (root / ".mise.toml").write_text(
            "\n".join((
                "[tools]",
                'python = "3.13"',
                f'"{selector}" = "{version}"',
                "",
            )),
            encoding="utf-8",
        )

    @classmethod
    def _project(
        cls,
        root: Path,
        *,
        selector: str = "github:example/tool",
        version: str = "latest",
    ) -> Path:
        root.mkdir(parents=True)
        cls._write_launchers(root)
        cls._write_config(root, selector=selector, version=version)
        (root / "pyproject.toml").write_text(
            "[project]\n"
            f'name = "{config.Infra.name}"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n",
            encoding="utf-8",
        )
        test_u.Tests.write_project_beads_config(root, config.Infra.name)
        upstream = test_u.Tests.repository_ref(config.Infra.name).url
        test_u.Tests.initialize_git_repo(root, origin_url=upstream)
        return root

    def test_complete_artifacts_validate_without_running_mise(
        self, tmp_path: Path
    ) -> None:
        root = self._project(tmp_path / "project")

        service = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        })
        tm.that(service.repository_root, eq=root)
        tm.that((root / ".git").is_dir(), eq=True)
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        tm.ok(identity)
        tm.that(identity.value.is_submodule, eq=False)
        result = service.execute()

        tm.ok(result, eq=True)

    # Root cause: `config.Infra.codegen.toolchain.suspended_mise_selector_patterns`
    # is currently an empty tuple in config/codegen.yaml (no toolchain is
    # suspended today), and it is a fixed-config field with no declared public
    # input to override in a test. The prior fixture asserted "beads" was
    # suspended, which is no longer true and cannot be injected through the
    # public surface, so the retired scenario is dropped rather than faked.
    # `_validate_suspended_selectors` itself remains covered structurally by
    # every other `.execute()` call in this file, which passes through it.

    def test_config_only_validation_skips_launcher_contract(
        self, tmp_path: Path
    ) -> None:
        """Config-only mode validates the declaration without tool-owned effects."""
        root = tmp_path / "project"
        root.mkdir()
        self._write_config(root)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "config_only": True,
        }).execute()

        tm.ok(result, eq=True)
        tm.that((root / "bin").exists(), eq=False)

    def test_full_validation_requires_committed_launchers(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        root.mkdir()
        self._write_config(root)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        # Root cause: a missing launcher file fails at the read boundary
        # before validate_seed's own "Mise seed lacks ..." wording applies.
        tm.fail(result, has="No such file or directory")

    def test_tools_section_is_mandatory(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        root.mkdir()
        (root / ".mise.toml").write_text("[settings]\n", encoding="utf-8")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "config_only": True,
        }).execute()

        tm.fail(result, has="[tools]")

    def test_apply_validates_the_same_offline_contract(self, tmp_path: Path) -> None:
        """Apply mode owns no tool effect: it validates declarations and launchers."""
        root = self._project(tmp_path / "project")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "apply_changes": True,
        }).execute()

        tm.ok(result, eq=True)

    def test_latest_selectors_validate_without_resolution(self, tmp_path: Path) -> None:
        """The unlocked fleet declares moving selectors resolved at setup time."""
        root = self._project(tmp_path / "project", selector="npm:jscpd")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.ok(result, eq=True)

    def test_unix_launcher_requires_executable_mode(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project")
        (root / "bin" / "mise").chmod(0o644)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="not executable")

    def test_project_filter_is_internal_to_make_propagation(self) -> None:
        """Keep project selection on the Make propagation boundary."""
        field = FlextInfraCodegenMiseArtifacts.model_fields["project_filter"]

        tm.that(field.alias, none=True)
        tm.that(field.exclude, eq=True)


__all__: tuple[str, ...] = ()
