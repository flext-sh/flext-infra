"""Offline contracts for generated Mise launchers and lock metadata."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_core import r
from flext_infra import config, m, u
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_tests import tm


class TestsCodegenMiseArtifacts:
    """Keep ordinary generation checks independent from remote resolution."""

    @staticmethod
    def _launcher_checksum() -> str:
        return "a" * 64

    @classmethod
    def _write_launchers(cls, root: Path, *, version: str | None = None) -> None:
        resolved = version or config.Infra.codegen.toolchain.mise_version
        checksum = cls._launcher_checksum()
        launchers = root / "bin"
        launchers.mkdir(parents=True, exist_ok=True)
        (launchers / "mise").write_text(
            "\n".join((
                "#!/usr/bin/env bash",
                f'local mise_version="${{MISE_VERSION:-{resolved}}}"',
                f'checksum_linux_x86_64="{checksum}"',
                f'checksum_linux_x86_64_musl="{checksum}"',
                f'checksum_linux_arm64="{checksum}"',
                f'checksum_linux_arm64_musl="{checksum}"',
                f'checksum_macos_x86_64="{checksum}"',
                f'checksum_macos_arm64="{checksum}"',
                "",
            )),
            encoding="utf-8",
        )
        (launchers / "mise").chmod(0o755)
        (launchers / "mise.cmd").write_text(
            "\n".join((
                "@echo off",
                f'set "pinned_version={resolved}"',
                f'set "sum_x64={checksum}"',
                "",
            )),
            encoding="utf-8",
        )

    @staticmethod
    def _write_lock(
        root: Path,
        *,
        selector: str = "github:example/tool",
        platforms: tuple[str, ...] | None = None,
        include_checksum: bool = True,
        extra_lock_selector: str | None = None,
    ) -> None:
        selected_platforms = (
            platforms or config.Infra.codegen.toolchain.mise_lock_platforms
        )
        (root / ".mise.toml").write_text(
            "\n".join((
                "[settings]",
                "lockfile = true",
                "[tool_config]",
                "locked = true",
                f'[tools."{selector}"]',
                'version = "1.2.3"',
                "",
            )),
            encoding="utf-8",
        )
        lines = [
            "lockfile_version = 1",
            "",
            f'[[tools."{selector}"]]',
            'version = "1.2.3"',
            f'backend = "{selector}"',
            'specifiers = ["1.2.3"]',
        ]
        checksum = "b" * 64
        for platform in selected_platforms:
            lines.extend((
                "",
                f'[tools."{selector}"."platforms.{platform}"]',
                *((f'checksum = "sha256:{checksum}"',) if include_checksum else ()),
                f'url = "https://example.invalid/{platform}/tool"',
            ))
        if extra_lock_selector is not None:
            lines.extend((
                "",
                f'[[tools."{extra_lock_selector}"]]',
                'version = "9.9.9"',
                f'backend = "{extra_lock_selector}"',
                'specifiers = ["9.9"]',
            ))
        (root / "mise.lock").write_text("\n".join((*lines, "")), encoding="utf-8")

    @classmethod
    def _project(
        cls,
        root: Path,
        *,
        selector: str = "github:example/tool",
        platforms: tuple[str, ...] | None = None,
        include_checksum: bool = True,
        extra_lock_selector: str | None = None,
    ) -> Path:
        root.mkdir(parents=True)
        cls._write_launchers(root)
        cls._write_lock(
            root,
            selector=selector,
            platforms=platforms,
            include_checksum=include_checksum,
            extra_lock_selector=extra_lock_selector,
        )
        return root

    def test_complete_artifacts_validate_without_running_mise(
        self, tmp_path: Path
    ) -> None:
        root = self._project(tmp_path / "project")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.ok(result, eq=True)

    def test_missing_platform_checksum_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="checksum")

    def test_explicit_apply_hydrates_missing_checksums_before_offline_validation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)
        commands: list[tuple[str, ...]] = []

        def run_raw(command: tuple[str, ...], *, cwd: Path) -> r[m.Cli.CommandOutput]:
            commands.append(command)
            output_index = command.index("--output") + 1
            artifact = Path(command[output_index])
            tm.that(artifact.parent, eq=cwd)
            artifact.write_bytes(b"resolved immutable artifact")
            return r[m.Cli.CommandOutput].ok(
                m.Cli.CommandOutput(stdout="", stderr="", exit_code=0)
            )

        monkeypatch.setattr(u.Cli, "run_raw", run_raw)

        apply_result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "apply_changes": True,
        }).execute()
        check_result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.ok(apply_result, eq=True)
        tm.ok(check_result, eq=True)
        tm.that(commands, len=len(config.Infra.codegen.toolchain.mise_lock_platforms))
        tm.that(
            (root / "mise.lock").read_text(encoding="utf-8"), has='checksum = "sha256:'
        )

    def test_explicit_apply_rejects_unsafe_checksum_source(
        self, tmp_path: Path
    ) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)
        lock_path = root / "mise.lock"
        lock_path.write_text(
            lock_path.read_text(encoding="utf-8").replace(
                "https://example.invalid", "http://example.invalid"
            ),
            encoding="utf-8",
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "apply_changes": True,
        }).execute()

        tm.fail(result, has="not safe")

    def test_missing_declared_platform_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project", platforms=("linux-x64",))

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="platform metadata mismatch")

    def test_lock_tool_set_must_equal_generated_config(self, tmp_path: Path) -> None:
        root = self._project(
            tmp_path / "project", extra_lock_selector="github:example/other"
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="tool set mismatch")

    def test_launcher_version_drift_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project")
        self._write_launchers(root, version="2000.1.1")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="launcher version drift")

    def test_declared_platform_exclusions_are_exact(self, tmp_path: Path) -> None:
        excluded = config.Infra.codegen.toolchain.mise_lock_platform_exclusions[
            "ast-grep"
        ]
        platforms = tuple(
            platform
            for platform in config.Infra.codegen.toolchain.mise_lock_platforms
            if platform not in excluded
        )
        root = self._project(
            tmp_path / "project", selector="ast-grep", platforms=platforms
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "check_only": True,
        }).execute()

        tm.ok(result, eq=True)


__all__: tuple[str, ...] = ()
