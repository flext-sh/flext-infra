"""Offline contracts for generated Mise launchers and lock metadata."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import config, m, p, r, u
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_tests import tm


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
        self._write_launchers(root, windows_version="2000.1.1")

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

    @classmethod
    def _member(cls, root: Path, name: str, *, identical: bool) -> Path:
        member = root / name
        member.mkdir()
        root_config = (root / ".mise.toml").read_text(encoding="utf-8")
        member_config = (
            root_config
            if identical
            else root_config.replace("lockfile = true", "lockfile = false")
        )
        (member / ".mise.toml").write_text(member_config, encoding="utf-8")
        cls._write_launchers(member)
        (member / "mise.lock").write_text("lockfile_version = 0\n", encoding="utf-8")
        return member

    def test_from_root_applies_byte_identical_member_lock(
        self, tmp_path: Path
    ) -> None:
        root = self._project(tmp_path / "root")
        member = self._member(root, "member-identical", identical=True)
        expected_lock = (root / "mise.lock").read_text(encoding="utf-8")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "project_filter": "member-identical",
            "from_root": True,
            "apply_changes": True,
        }).execute()

        tm.ok(result, eq=True)
        tm.that((member / "mise.lock").read_text(encoding="utf-8"), eq=expected_lock)

    def test_from_root_rejects_materially_different_member(
        self, tmp_path: Path
    ) -> None:
        root = self._project(tmp_path / "root")
        member = self._member(root, "member-different", identical=False)
        unchanged_lock = (member / "mise.lock").read_text(encoding="utf-8")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "project_filter": "member-different",
            "from_root": True,
            "apply_changes": True,
        }).execute()

        tm.fail(result, has="not identical")
        tm.that(
            (member / "mise.lock").read_text(encoding="utf-8"),
            eq=unchanged_lock,
        )

    def test_from_root_requires_explicit_apply(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "root")
        _member = self._member(root, "member-identical", identical=True)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "project_filter": "member-identical",
            "from_root": True,
        }).execute()

        tm.fail(result, has="requires explicit --apply")

    def test_from_root_fails_causally_after_post_copy_divergence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = self._project(tmp_path / "root")
        _member = self._member(root, "member-identical", identical=True)
        original_write = u.Cli.atomic_write_text_file

        def write_divergent_lock(path: Path, content: str) -> p.Result[bool]:
            if path.name == "mise.lock":
                content = f"{content}# diverged\n"
            return original_write(path, content)

        monkeypatch.setattr(u.Cli, "atomic_write_text_file", write_divergent_lock)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "workspace_root": root,
            "project_filter": "member-identical",
            "from_root": True,
            "apply_changes": True,
        }).execute()

        tm.fail(result, has="mise.lock diverged after atomic propagation")

    def test_project_selector_is_cli_exposed(self) -> None:
        """The propagation selector reaches the schema-driven CLI as --project."""
        field = FlextInfraCodegenMiseArtifacts.model_fields["project_filter"]

        tm.that(field.alias, eq="project")
        tm.that(field.exclude, ne=True)


__all__: tuple[str, ...] = ()
