"""Offline contracts for generated Mise launchers and lock metadata."""

from __future__ import annotations

import socket
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from flext_infra import c, config, m, r, u
from flext_infra.codegen import FlextInfraCodegenConform
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
                'version = "latest"',
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
            'specifiers = ["latest"]',
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

    @staticmethod
    def _seed_offline_conform_repo(root: Path) -> None:
        """Seed a manifest-only tree whose Mise declaration matches this checkout.

        Rendering ``.mise.toml`` for a repository sharing this checkout's own
        distribution name reproduces the exact bytes ``copy_tracked_mise_seeds``
        copies in, so a real ``codegen conform`` apply finds nothing changed
        for the toolchain.
        """
        distribution = config.Infra.name
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "pyproject.toml",
                f'[project]\nname = "{distribution}"\nversion = "0.1.0"\n'
                'requires-python = ">=3.13,<3.14"\n',
            )
        )
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        tests_init = root / "tests" / "__init__.py"
        tests_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(tests_init, ""))
        test_u.Tests.write_project_beads_config(root, distribution)
        test_u.Tests.copy_tracked_mise_seeds(root)
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed Mise toolchain"],
                cwd=root,
            )
        )

    @staticmethod
    def _offline_apply_request(root: Path) -> m.Infra.CodegenConformRequest:
        """Pin offline resolution so the run never depends on the sandbox network."""
        return m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
            toolchain_resolution=c.Infra.MiseResolutionMode.OFFLINE,
        )

    @pytest.mark.slow
    def test_offline_apply_keeps_the_published_toolchain_byte_identical(
        self, infra_git_repo: Path
    ) -> None:
        """Offline resolution republishes the exact published launchers and lock.

        Nothing is resolved from the network, so the same sources produce the
        same bytes, and the transaction leaves no staging root or journal.
        """
        root = infra_git_repo
        self._seed_offline_conform_repo(root)
        tracked = (
            root / c.Infra.MISE_TOML_FILENAME,
            root / "mise.lock",
            root / "bin" / "mise",
            root / "bin" / "mise.cmd",
        )
        before = {path: path.read_bytes() for path in tracked}

        result = FlextInfraCodegenConform.execute_request(
            self._offline_apply_request(root)
        )

        tm.ok(result)
        for path, content in before.items():
            tm.that(path.read_bytes(), eq=content)
        transaction_root = (
            root / c.Infra.TRANSACTION_STATE_DIRNAME / "mise-artifacts" / "transaction"
        )
        journal_file = (
            root / c.Infra.TRANSACTION_STATE_DIRNAME / "mise-artifacts" / "journal.json"
        )
        tm.that(transaction_root.exists(), eq=False)
        tm.that(journal_file.exists(), eq=False)

    @pytest.mark.slow
    def test_offline_apply_cannot_stage_an_unpublished_launcher(
        self, infra_git_repo: Path
    ) -> None:
        """Offline resolution fails loud instead of inventing a missing artifact.

        A launcher that was never published can only come from the network, so
        the offline stage refuses before any effect and publishes nothing.
        """
        root = infra_git_repo
        self._seed_offline_conform_repo(root)
        windows_launcher = root / "bin" / "mise.cmd"
        windows_launcher.unlink()
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Drop windows launcher"],
                cwd=root,
            )
        )

        result = FlextInfraCodegenConform.execute_request(
            self._offline_apply_request(root)
        )

        tm.fail(result, has="offline Mise resolution")
        tm.that(windows_launcher.exists(), eq=False)
        transaction_root = (
            root / c.Infra.TRANSACTION_STATE_DIRNAME / "mise-artifacts" / "transaction"
        )
        tm.that(transaction_root.exists(), eq=False)

    def test_explicit_resolution_is_selected_without_probing(
        self, tmp_path: Path
    ) -> None:
        """An explicit online or offline request pins the path before effects."""
        root = self._project(tmp_path / "project")
        for requested in (
            c.Infra.MiseResolutionMode.ONLINE,
            c.Infra.MiseResolutionMode.OFFLINE,
        ):
            owner = FlextInfraCodegenMiseArtifacts.model_validate({
                "repository_root": root,
                "check_only": True,
                "toolchain_resolution": requested,
            })
            tm.that(owner.resolution_mode(), eq=requested)

    def test_unreachable_endpoint_is_offline(self) -> None:
        """A closed local port answers nothing, so the probe reports offline."""
        with socket.socket() as probe_socket:
            probe_socket.bind(("127.0.0.1", 0))
            port = probe_socket.getsockname()[1]
        tm.that(
            u.Infra.endpoint_reachable(
                f"http://127.0.0.1:{port}/", timeout_seconds=0.5
            ),
            eq=False,
        )

    def test_any_http_answer_is_online(self, tmp_path: Path) -> None:
        """A server that answers the HEAD request at all is reachable."""
        handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
        server = HTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        try:
            tm.that(
                u.Infra.endpoint_reachable(
                    f"http://127.0.0.1:{server.server_port}/", timeout_seconds=2
                ),
                eq=True,
            )
        finally:
            thread.join(timeout=2)
            server.server_close()

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

    def test_missing_platform_checksum_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="checksum")

    def test_explicit_apply_is_rejected_by_validation_service(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)
        lock_path = root / "mise.lock"
        before = lock_path.read_bytes()

        def reject_run_raw(*_args: object, **_kwargs: object) -> r[m.Cli.CommandOutput]:
            return r[m.Cli.CommandOutput].fail("validation service invoked a writer")

        monkeypatch.setattr(u.Cli, "run_raw", reject_run_raw)

        apply_result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "apply_changes": True,
        }).execute()

        tm.fail(apply_result, has="owned by codegen conform")
        tm.that(lock_path.read_bytes(), eq=before)

    def test_validation_rejects_unsafe_checksum_source(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project", include_checksum=False)
        lock_path = root / "mise.lock"
        lock_path.write_text(
            lock_path.read_text(encoding="utf-8").replace(
                "https://example.invalid", "http://example.invalid"
            ),
            encoding="utf-8",
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        # The typed lock contract is what validation reaches: a plaintext source
        # cannot describe an artifact, so the URL rule rejects it before any
        # download rule runs.
        error = tm.fail(result, has="invalid mise.lock metadata")
        tm.that(error, has="^https://")

    def test_missing_declared_platform_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project", platforms=("linux-x64",))

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="platform metadata mismatch")

    def test_lock_tool_set_must_equal_generated_config(self, tmp_path: Path) -> None:
        root = self._project(
            tmp_path / "project", extra_lock_selector="github:example/other"
        )

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.fail(result, has="tool set mismatch")

    def test_launcher_version_drift_is_rejected(self, tmp_path: Path) -> None:
        root = self._project(tmp_path / "project")
        self._write_launchers(root, windows_version="2000.1.1")

        result = FlextInfraCodegenMiseArtifacts.model_validate({
            "repository_root": root,
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
            "repository_root": root,
            "check_only": True,
        }).execute()

        tm.ok(result, eq=True)

    def test_project_filter_is_internal_to_make_propagation(self) -> None:
        """Keep project selection on the Make propagation boundary."""
        field = FlextInfraCodegenMiseArtifacts.model_fields["project_filter"]

        tm.that(field.alias, none=True)
        tm.that(field.exclude, eq=True)


__all__: tuple[str, ...] = ()
