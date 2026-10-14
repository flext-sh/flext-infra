"""Exercise missing-pin recovery through native Mise and generated Make.

Release assets belong to the declared toolchain, not an application service
configured in a test ``.env``. Provisioning failures must reach these tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import pytest
from packaging.version import Version

from flext_infra import c, config, m
from tests import t, tm, u


class TestsFlextInfraMisePinBootstrap:
    """Setup stays frozen while upgrade can establish the first self pin."""

    class BootstrapRenderContext(m.Value):
        """Declared bootstrap inputs passed through the real template consumer."""

        toolchain: Annotated[
            m.Infra.ToolchainSpec, m.Field(description="Original declared toolchain")
        ]
        make: Annotated[m.Infra.MakeSpec, m.Field(description="Original Make contract")]
        bootstrap_report_shell_literal: Annotated[
            str, m.Field(description="Elected operation report scalar transport")
        ]
        bootstrap_report_relative_path: Annotated[
            Path, m.Field(description="Canonical report destination")
        ]

    @staticmethod
    def _environment(root: Path) -> t.StrMapping:
        """Confine native Mise configuration, installs, state and caches."""
        return {
            "HOME": str(root / "home"),
            "XDG_CONFIG_HOME": str(root / "xdg-config"),
            "XDG_DATA_HOME": str(root / "data"),
            "XDG_STATE_HOME": str(root / "state"),
            "XDG_CACHE_HOME": str(root / "cache"),
            "MISE_CONFIG_DIR": str(root / "xdg-config/mise"),
            "MISE_DATA_DIR": str(root / "data/mise"),
            "MISE_STATE_DIR": str(root / "state/mise"),
            "MISE_CACHE_DIR": str(root / "cache/mise"),
            "MISE_TMP_DIR": str(root / "tmp/mise"),
            "MISE_INSTALLS_DIR": str(root / "data/mise/installs"),
            "MISE_DOWNLOADS_DIR": str(root / "data/mise/downloads"),
            "MISE_PLUGINS_DIR": str(root / "data/mise/plugins"),
            "MISE_SHIMS_DIR": str(root / "data/mise/shims"),
        }

    @staticmethod
    def _system_path_without_mise(root: Path) -> Path:
        """Expose real system executables with the host Mise deliberately absent."""
        destination = root / "system-bin"
        destination.mkdir()
        for directory in dict.fromkeys(os.defpath.split(os.pathsep)):
            for source in Path(directory).iterdir():
                target = destination / source.name
                if (
                    source.name != "mise"
                    and not target.exists()
                    and source.is_file()
                    and os.access(source, os.X_OK)
                ):
                    target.symlink_to(source.resolve())
        tm.that(shutil.which("mise", path=str(destination)), eq=None)
        return destination

    @staticmethod
    def _project(
        tmp_path: Path,
        *,
        git_metadata: bool = True,
        mise_version: str | None = None,
    ) -> None:
        """Render the real bootstrap macro with the declared self-managed tool."""
        if git_metadata:
            u.Tests.initialize_git_repo(tmp_path)
        (tmp_path / "home").mkdir()
        toolchain = config.Infra.codegen.toolchain
        template_root = u.Infra.codegen_templates_root(config.Infra.codegen)
        shutil.copyfile(
            template_root / "base" / "tool_bootstrap_recipe.j2",
            tmp_path / "tool_bootstrap_recipe.j2",
        )
        template = tmp_path / "bootstrap.j2"
        template.write_text(
            '{% from "tool_bootstrap_recipe.j2" import tool_bootstrap_recipe %}'
            '{{ tool_bootstrap_recipe("bootstrap", "$(PROJECT_ROOT)", '
            "toolchain, [toolchain.mise_selector], "
            '"sh -ec \'command -v mise > runtime-mise-path.txt; '
            "mise --version > runtime-mise-version.txt; "
            "printf recovered > recovered.txt'\", make, "
            "bootstrap_report_shell_literal, bootstrap_report_relative_path, false) }}",
            encoding="utf-8",
        )
        recipe = tm.ok(
            u.Cli.template_render(
                template,
                TestsFlextInfraMisePinBootstrap.BootstrapRenderContext(
                    toolchain=toolchain,
                    make=config.Infra.codegen.make,
                    bootstrap_report_shell_literal=(
                        u.Infra.bootstrap_operation_report_shell_literal()
                    ),
                    bootstrap_report_relative_path=(
                        c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH
                    ),
                ),
            ),
        )
        (tmp_path / "Makefile").write_text(
            "PROJECT_ROOT := $(CURDIR)\n"
            "setup: bootstrap\n"
            "upg: TOOL_BOOTSTRAP_RESOLVE := 1\n"
            "upg: bootstrap\n" + recipe,
            encoding="utf-8",
        )
        (tmp_path / ".mise.toml").write_text(
            f"[settings]\nlockfile = {str(toolchain.mise_lockfile).lower()}\n"
            "[tools]\n"
            f'"{toolchain.mise_selector}" = "{mise_version or toolchain.mise_version}"\n',
            encoding="utf-8",
        )
        tm.ok(
            u.Cli.run_checked(
                ["mise", "trust", str(tmp_path / ".mise.toml")],
                options=m.Cli.ProcessOptions(
                    env=TestsFlextInfraMisePinBootstrap._environment(tmp_path),
                ),
            ),
        )

    @pytest.mark.parametrize("git_metadata", [False, True])
    def test_setup_preserves_a_missing_self_pin(
        self, tmp_path: Path, *, git_metadata: bool
    ) -> None:
        """Frozen setup cannot resolve a missing lock or start its lifecycle."""
        self._project(tmp_path, git_metadata=git_metadata)
        setup = tm.ok(
            u.Tests.run_isolated_make(
                ["setup"], cwd=tmp_path, env=self._environment(tmp_path)
            )
        )
        tm.that(u.Cli.process_succeeded(setup.outcome), eq=False)
        tm.that(
            setup.stderr,
            has="pins no",
            msg=setup.stderr + "\n" + (tmp_path / "Makefile").read_text(),
        )
        tm.that((tmp_path / "mise.lock").exists(), eq=False)
        tm.that((tmp_path / "recovered.txt").exists(), eq=False)
        report = m.Infra.WorkspaceOperationReport.model_validate_json(
            (tmp_path / c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH).read_bytes()
        )
        tm.that(report.scope, eq=(Path(),))
        tm.that(len(report.receipts), eq=1)
        receipt = report.receipts[0]
        tm.that(receipt.root, eq=Path())
        tm.that(receipt.executed, eq=True)
        tm.that(receipt.completed, eq=False)
        tm.that(receipt.native_exit_code, eq=2)
        tm.that(receipt.stage, eq="lock-pin")
        tm.that(receipt.files, eq=())
        if git_metadata:
            tm.that(
                report.candidate_sha,
                eq=tm.ok(
                    u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=tmp_path)
                ).strip(),
            )
            tm.that(report.candidate_read_exit_code, eq=0)
        else:
            tm.that(report.candidate_sha, eq=None)
            tm.not_none(report.candidate_read_exit_code)
            tm.that(report.candidate_read_exit_code != 0, eq=True)

    @staticmethod
    @pytest.mark.parametrize("enabled", [False, True])
    def test_mise_settings_follow_typed_policy_without_global_locking(
        *, enabled: bool
    ) -> None:
        """Project valid policy changes without locking unrelated host tools."""
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={
                "mise_lockfile": enabled,
                "mise_disable_update_warning": enabled,
                "mise_provenance_api_failures_fatal": enabled,
                "mise_locked_verify_provenance": enabled,
            },
        )
        rendered = tm.ok(
            u.Cli.template_render(
                u.Infra.codegen_templates_root(config.Infra.codegen)
                / "base"
                / ".mise.toml.j2",
                toolchain,
            ),
        )
        document = u.Tests.toml_payload(rendered)
        settings = u.Tests.toml_mapping(document["settings"])
        tm.that(settings["lockfile"], eq=toolchain.mise_lockfile)
        tm.that(
            settings["provenance_api_failures_fatal"],
            eq=toolchain.mise_provenance_api_failures_fatal,
        )
        tm.that(
            settings["locked_verify_provenance"],
            eq=toolchain.mise_locked_verify_provenance,
        )
        tm.that("locked" in settings, eq=False)
        tm.that(
            settings["disable_update_warning"],
            eq=toolchain.mise_disable_update_warning,
        )
        tm.that("tool_config" in document, eq=False)

    @pytest.mark.slow
    @pytest.mark.parametrize("pin_present", [False, True])
    def test_upgrade_qualifies_the_final_self_pin(
        self, tmp_path: Path, *, pin_present: bool
    ) -> None:
        """The real upgraded lock governs the release executing the lifecycle."""
        self._project(tmp_path)
        if pin_present:
            (tmp_path / "mise.lock").write_text(
                u.Tests.repo_mise_lock(), encoding=c.DEFAULT_ENCODING
            )
        upgrade = tm.ok(
            u.Tests.run_isolated_make(
                ["upg"], cwd=tmp_path, env=self._environment(tmp_path)
            )
        )
        tm.that(
            u.Cli.process_succeeded(upgrade.outcome),
            eq=True,
            msg=upgrade.stdout + upgrade.stderr,
        )
        tm.that((tmp_path / "mise.lock").exists(), eq=True)
        tm.that((tmp_path / "recovered.txt").read_text(), eq="recovered")
        pin = u.Tests.pinned_mise_version(
            (tmp_path / "mise.lock").read_text(encoding=c.DEFAULT_ENCODING),
            config.Infra.codegen.toolchain.mise_selector,
        )
        tm.that(
            (tmp_path / "runtime-mise-version.txt").read_text().split()[0],
            eq=pin,
        )

    def test_cached_probe_failure_preserves_native_exit_and_artifact(
        self,
        tmp_path: Path,
    ) -> None:
        """A genuinely broken executable is a failed probe, never cache absence."""
        self._project(tmp_path)
        lock = u.Tests.repo_mise_lock()
        (tmp_path / "mise.lock").write_text(lock, encoding=c.DEFAULT_ENCODING)
        pin = u.Tests.pinned_mise_version(
            lock,
            config.Infra.codegen.toolchain.mise_selector,
        )
        cache = tmp_path / "cache"
        cached = cache / "flext/infra/mise-bootstrap" / pin / "mise"
        cached.parent.mkdir(parents=True)
        native = Path(tm.not_none(shutil.which("mise"))).resolve().read_bytes()
        damaged = native[:16]
        tm.that(b"\x00" in damaged, eq=True)
        cached.write_bytes(damaged)
        cached.chmod(0o755)
        probe = tm.ok(
            u.Cli.run_raw(
                ["/bin/sh", "-c", '"$1" --version', "probe", str(cached)],
                cwd=tmp_path,
            ),
        )
        tm.that(u.Cli.process_succeeded(probe.outcome), eq=False)

        setup = tm.ok(
            u.Tests.run_isolated_make(
                ["setup"],
                cwd=tmp_path,
                env=self._environment(tmp_path),
            ),
        )

        tm.that(u.Cli.process_succeeded(setup.outcome), eq=False)
        report = m.Infra.WorkspaceOperationReport.model_validate_json(
            (tmp_path / c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(
            report.receipts[0].native_exit_code,
            eq=probe.outcome.raw_return_code,
        )
        tm.that(report.receipts[0].stage, eq="release-verification")
        tm.that(setup.stderr, has=str(cached))
        tm.that(cached.read_bytes(), eq=damaged)
        tm.that((tmp_path / "recovered.txt").exists(), eq=False)

    @pytest.mark.slow
    def test_locked_setup_runs_without_host_mise_from_cold_and_warm_cache(
        self,
        tmp_path: Path,
    ) -> None:
        """A real pinned release bootstraps both cache states without host Mise."""
        self._project(tmp_path)
        lock = u.Tests.repo_mise_lock()
        lock_path = tmp_path / "mise.lock"
        lock_path.write_text(lock, encoding=c.DEFAULT_ENCODING)
        pin = u.Tests.pinned_mise_version(
            lock, config.Infra.codegen.toolchain.mise_selector
        )
        environment = {
            **self._environment(tmp_path),
            "PATH": str(self._system_path_without_mise(tmp_path)),
        }
        cold = tm.ok(
            u.Tests.run_isolated_make(["setup"], cwd=tmp_path, env=environment)
        )
        tm.that(
            u.Cli.process_succeeded(cold.outcome),
            eq=True,
            msg=cold.stdout + cold.stderr,
        )
        executable = Path((tmp_path / "runtime-mise-path.txt").read_text().strip())
        tm.that(executable.is_relative_to(tmp_path), eq=True)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(executable, required=True))

        warm = tm.ok(
            u.Tests.run_isolated_make(["setup"], cwd=tmp_path, env=environment)
        )

        tm.that(
            u.Cli.process_succeeded(warm.outcome),
            eq=True,
            msg=warm.stdout + warm.stderr,
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(executable, required=True)),
            eq=before,
        )
        tm.that(
            (tmp_path / "runtime-mise-version.txt").read_text().split()[0],
            eq=pin,
        )
        tm.that(lock_path.read_text(encoding=c.DEFAULT_ENCODING), eq=lock)
        tm.that((tmp_path / "recovered.txt").read_text(), eq="recovered")

    @pytest.mark.slow
    def test_wrong_real_cached_release_is_replaced_before_lifecycle(
        self,
        tmp_path: Path,
    ) -> None:
        """A successful probe of another genuine release triggers pinned recovery."""
        current = tmp_path / "current"
        current.mkdir()
        self._project(current)
        selector = config.Infra.codegen.toolchain.mise_selector
        lock = u.Tests.repo_mise_lock()
        (current / "mise.lock").write_text(lock, encoding=c.DEFAULT_ENCODING)
        pin = u.Tests.pinned_mise_version(lock, selector)
        environment = self._environment(current)
        available = tm.ok(
            u.Cli.capture(
                ["mise", "ls-remote", selector, pin.partition(".")[0]],
                cwd=current,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )
        older = str(
            max(
                version
                for item in available.splitlines()
                if (version := Version(item.removeprefix("v"))) < Version(pin)
                and not version.is_prerelease
                and not version.is_devrelease
            ),
        )
        previous = tmp_path / "previous"
        previous.mkdir()
        self._project(previous, mise_version=older)
        tm.ok(
            u.Cli.run_checked(
                ["mise", "-C", str(previous), "lock"],
                cwd=previous,
                options=m.Cli.ProcessOptions(env=self._environment(previous)),
            ),
        )
        previous_lock = (previous / "mise.lock").read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(u.Tests.pinned_mise_version(previous_lock, selector), eq=older)
        for project in (previous, current):
            installed = tm.ok(
                u.Tests.run_isolated_make(
                    ["setup"], cwd=project, env=self._environment(project)
                ),
            )
            tm.that(
                u.Cli.process_succeeded(installed.outcome),
                eq=True,
                msg=installed.stdout + installed.stderr,
            )
        previous_executable = Path(
            (previous / "runtime-mise-path.txt").read_text().strip(),
        )
        current_executable = Path(
            (current / "runtime-mise-path.txt").read_text().strip(),
        )
        current_bytes = current_executable.read_bytes()
        shutil.copyfile(previous_executable, current_executable)
        observed = tm.ok(
            u.Cli.capture(
                [str(current_executable), "--version"],
                cwd=current,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )
        tm.that(observed.split()[0], eq=older)

        recovered = tm.ok(
            u.Tests.run_isolated_make(
                ["setup"],
                cwd=current,
                env={
                    **environment,
                    "PATH": str(self._system_path_without_mise(current)),
                },
            ),
        )

        tm.that(
            u.Cli.process_succeeded(recovered.outcome),
            eq=True,
            msg=recovered.stdout + recovered.stderr,
        )
        tm.that(current_executable.read_bytes(), eq=current_bytes)
        tm.that(
            (current / "runtime-mise-version.txt").read_text().split()[0],
            eq=pin,
        )
        tm.that((current / "mise.lock").read_text(encoding=c.DEFAULT_ENCODING), eq=lock)

    @staticmethod
    def test_git_mirrors_use_native_uv_cache(tmp_path: Path) -> None:
        """Read each locked Git commit back from the locally provisioned mirror."""
        project = Path(__file__).resolve().parents[3]
        sources = u.Tests.locked_git_sources(project)
        mirrored = u.Tests.build_git_mirrors(project, tmp_path)
        tm.that(len(mirrored), eq=len(sources))
        for url, revision, commit in sources:
            parsed = urlsplit(url)
            mirror = tmp_path / parsed.netloc / parsed.path.lstrip("/")
            resolved = tm.ok(
                u.Cli.capture(
                    ["git", "rev-parse", f"refs/heads/{revision}"],
                    cwd=mirror,
                ),
            ).strip()
            tm.that(resolved, eq=commit)
