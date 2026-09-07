"""Offline contracts for generated Mise declarations and launchers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, m, u
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_tests import tm
from tests import u as test_u


class TestsCodegenMiseArtifacts:
    """Keep ordinary generation checks independent from remote resolution."""

    @staticmethod
    def _launcher_checksum() -> str:
        return "a" * 64

    @classmethod
    def _write_launchers(
        cls,
        root: Path,
        *,
        version: str = "2026.9.1",
        windows_version: str | None = None,
    ) -> None:
        resolved_windows = windows_version or version
        checksum = cls._launcher_checksum()
        launchers = root / "bin"
        launchers.mkdir(parents=True, exist_ok=True)
        (launchers / "mise").write_text(
            "\n".join((
                "#!/usr/bin/env bash",
                f'local mise_version="${{MISE_VERSION:-{version}}}"',
                f'checksum_linux_x86_64="{checksum}"',
                f'checksum_linux_x86_64_musl="{checksum}"',
                f'checksum_linux_arm64="{checksum}"',
                f'checksum_linux_arm64_musl="{checksum}"',
                f'checksum_linux_armv7="{checksum}"',
                f'checksum_linux_armv7_musl="{checksum}"',
                f'checksum_macos_x86_64="{checksum}"',
                f'checksum_macos_arm64="{checksum}"',
                f'checksum_linux_x86_64_zstd="{checksum}"',
                f'checksum_linux_x86_64_musl_zstd="{checksum}"',
                f'checksum_linux_arm64_zstd="{checksum}"',
                f'checksum_linux_arm64_musl_zstd="{checksum}"',
                f'checksum_linux_armv7_zstd="{checksum}"',
                f'checksum_linux_armv7_musl_zstd="{checksum}"',
                f'checksum_macos_x86_64_zstd="{checksum}"',
                f'checksum_macos_arm64_zstd="{checksum}"',
                "",
            )),
            encoding="utf-8",
        )
        (launchers / "mise").chmod(0o755)
        (launchers / "mise.cmd").write_text(
            "\n".join((
                "@echo off",
                f'set "pinned_version={resolved_windows}"',
                f'set "sum_x64={checksum}"',
                f'set "sum_arm64={checksum}"',
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

    def test_config_preflight_rejects_suspended_selector_before_publication(
        self, tmp_path: Path
    ) -> None:
        """A dormant capability cannot reach download or publication."""
        root = tmp_path / "project"
        root.mkdir()
        (root / ".mise.toml").write_text('[tools]\nbeads = "1.2.2"\n', encoding="utf-8")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "config_only": True,
        }).execute()

        tm.fail(result, has=["suspended toolchain", "beads"])
        tm.that((root / "bin").exists(), eq=False)

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

        tm.fail(result, has="Mise seed")

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

    def test_launcher_version_drift_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project")
        self._write_launchers(root, windows_version="2000.1.1")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="launcher version drift")

    def test_launcher_checksum_gap_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project")
        launcher = root / "bin" / "mise"
        launcher.write_text(
            launcher.read_text(encoding="utf-8").replace(
                f'checksum_macos_arm64="{self._launcher_checksum()}"\n', ""
            ),
            encoding="utf-8",
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="checksum missing")

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
