"""Exercise missing-pin recovery through native Mise and generated Make.

Release assets belong to the declared toolchain, not an application service
configured in a test ``.env``. Provisioning failures must reach these tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

from packaging.version import Version

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraMisePinBootstrap:
    """Setup stays frozen while upgrade can establish the first self pin."""

    class BootstrapRenderContext(m.Value):
        """Declared bootstrap inputs passed through the real template consumer."""

        toolchain: Annotated[
            m.Infra.ToolchainSpec,
            m.Field(description="Original declared toolchain"),
        ]
        make: Annotated[
            m.Infra.MakeSpec,
            m.Field(description="Original Make contract"),
        ]
        bootstrap_report_shell_literal: Annotated[
            str, m.Field(description="Elected operation report scalar transport")
        ]
        bootstrap_report_relative_path: Annotated[
            Path, m.Field(description="Canonical report destination")
        ]

    class WriterRenderContext(m.Value):
        """Declared inputs of the upgrade lock stage."""

        toolchain: Annotated[
            m.Infra.ToolchainSpec,
            m.Field(description="Original declared toolchain"),
        ]
        install_tools: Annotated[
            tuple[str, ...],
            m.Field(description="Declared tool keys the lock stage owns"),
        ]

    @staticmethod
    def environment(root: Path) -> Mapping[str, str]:
        """Confine native Mise configuration, installs, state and caches.

        Returns:
            The resulting ``Mapping[str, str]``.

        """
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
    def system_path_without_mise(root: Path) -> Path:
        """Expose real system executables with the host Mise deliberately absent.

        Returns:
            The resulting ``Path``.

        """
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
            "\"sh -ec 'command -v mise > runtime-mise-path.txt; "
            "mise --version > runtime-mise-version.txt; "
            "printf recovered > recovered.txt'\", make, "
            "bootstrap_report_shell_literal, bootstrap_report_relative_path) }}",
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
            "PROJECT_ROOT := $(CURDIR)\nsetup: bootstrap\n" + recipe,
            encoding="utf-8",
        )
        (tmp_path / ".mise.toml").write_text(
            f"[settings]\nlockfile = {str(toolchain.mise_lockfile).lower()}\n"
            "[tools]\n"
            f'"{toolchain.mise_selector}" = '
            f'"{mise_version or toolchain.mise_version}"\n',
            encoding="utf-8",
        )
        tm.ok(
            u.Cli.run_checked(
                ["mise", "trust", str(tmp_path / ".mise.toml")],
                options=m.Cli.ProcessOptions(
                    env=TestsFlextInfraMisePinBootstrap.environment(tmp_path),
                ),
            ),
        )

    @c.Tests.MARK.parametrize("git_metadata", [False, True])
    def test_setup_preserves_a_missing_self_pin(
        self, tmp_path: Path, *, git_metadata: bool
    ) -> None:
        """Frozen setup cannot resolve a missing lock or start its lifecycle."""
        self._project(tmp_path, git_metadata=git_metadata)
        setup = tm.ok(
            u.Tests.run_isolated_make(
                ["setup"], cwd=tmp_path, env=self.environment(tmp_path)
            )
        )
        tm.fail(u.Cli.process_succeeded(setup.outcome))
        tm.that(
            setup.stderr,
            has="pins no",
            msg=setup.stderr + "\n" + (tmp_path / "Makefile").read_text(),
        )
        tm.fail((tmp_path / "mise.lock").exists())
        tm.fail((tmp_path / "recovered.txt").exists())
        report = m.Infra.WorkspaceOperationReport.model_validate_json(
            (tmp_path / c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH).read_bytes()
        )
        tm.that(report.scope, eq=(Path(),))
        tm.that(len(report.receipts), eq=1)
        receipt = report.receipts[0]
        tm.that(receipt.root, eq=Path())
        tm.ok(receipt.executed)
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
            tm.ok(report.candidate_read_exit_code != 0)

    @staticmethod
    @c.Tests.MARK.parametrize("enabled", [False, True])
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
        tm.fail("locked" in settings)
        tm.that(
            settings["disable_update_warning"],
            eq=toolchain.mise_disable_update_warning,
        )
        tm.fail("tool_config" in document)

    @staticmethod
    def test_native_http_source_options_survive_the_public_toml_consumer() -> None:
        """Typed backend inputs round-trip without table scope swallowing tools."""
        toolchain = config.Infra.codegen.toolchain
        dependency = toolchain.tools[0]
        source = m.Infra.MiseToolEntry(
            name="source-contract-fixture",
            selector="http:source-contract-fixture",
            version="latest",
            http=m.Infra.MiseHttpToolOptions(
                url="https://example.invalid/source-{{version}}.tar.xz",
                version_list_url="https://example.invalid/releases",
                version_json_path=".[].tag_name",
                version_order="semver",
                checksum_url="https://example.invalid/checksums/{{version}}",
                checksum_expr="body",
                strip_components=1,
                bin_path="bin",
            ),
            depends=(dependency.selector or dependency.name,),
            install_env={"BUILD_INPUT_IDENTITY": "fixture-owned-input"},
            postinstall=m.Infra.MisePostinstallOptions(
                run='printf "%s\\n" "$MISE_TOOL_INSTALL_PATH"',
                when="always",
            ),
            version_probe=dependency.version_probe,
        )
        selected = m.Infra.ToolchainSpec.model_validate(
            toolchain.model_copy(
                update={"tools": (source, *toolchain.tools)},
            ).model_dump(round_trip=True),
        )
        rendered = tm.ok(
            u.Cli.template_render(
                u.Infra.codegen_templates_root(config.Infra.codegen)
                / "base"
                / ".mise.toml.j2",
                selected,
            ),
        )
        document = u.Tests.toml_payload(rendered)
        tools = u.Tests.toml_mapping(document["tools"])
        observed = u.Tests.toml_mapping(tools[source.selector or source.name])
        tm.that(observed["version"], eq=selected.tool_versions[source.name])
        for key, value in (
            tm.not_none(source.http).model_dump(exclude_none=True).items()
        ):
            tm.that(observed[key], eq=value)
        tm.that(observed["depends"], eq=list(source.depends))
        tm.that(observed["install_env"], eq=dict(source.install_env))
        tm.that(
            observed["postinstall"],
            eq=tm.not_none(source.postinstall).model_dump(exclude_none=True),
        )
        tm.that(
            set(tools),
            eq={"python", selected.mise_selector, *selected.tool_keys.values()},
        )

    @c.Tests.MARK.slow
    def test_setup_provisions_the_pinned_release_and_runs_it(
        self,
        tmp_path: Path,
    ) -> None:
        """The committed lock governs the release executing the lifecycle."""
        self._project(tmp_path)
        (tmp_path / "mise.lock").write_text(
            u.Tests.repo_mise_lock(), encoding=c.DEFAULT_ENCODING
        )
        setup = tm.ok(
            u.Tests.run_isolated_make(
                ["setup"], cwd=tmp_path, env=self.environment(tmp_path)
            )
        )
        tm.that(
            u.Cli.process_succeeded(setup.outcome),
            eq=True,
            msg=setup.stdout + setup.stderr,
        )
        tm.that((tmp_path / "recovered.txt").read_text(), eq="recovered")
        pin = u.Tests.pinned_mise_version(
            (tmp_path / "mise.lock").read_text(encoding=c.DEFAULT_ENCODING),
            config.Infra.codegen.toolchain.mise_selector,
        )
        tm.that(
            (tmp_path / "runtime-mise-version.txt").read_text().split()[0],
            eq=pin,
        )

    @c.Tests.MARK.slow
    def test_fresh_setup_provisions_before_the_native_workspace_reader(
        self,
        tmp_path: Path,
    ) -> None:
        """A fresh runner's setup rerun reaches provisioning, not the reader.

        Premise (aihub-0p2ee, ai-hub CI run 44970827653): the acquired Mise is
        present but the declared github:jdx/mise tool is not installed yet, and
        the _setup_provision rerun ran the native workspace reader first ("mise
        is not a mise bin", "Cannot resolve the physical workspace"). Offline
        Mise stops the locked install at its first download.
        """
        root, _ = u.Tests.render_make_environment(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        bootstrap_mise = tmp_path / "home/.local/bin/mise"
        bootstrap_mise.parent.mkdir(parents=True)
        bootstrap_mise.symlink_to(tm.not_none(shutil.which("mise")))
        environment = {
            **self.environment(tmp_path),
            "PATH": str(self.system_path_without_mise(tmp_path)),
            config.Infra.codegen.make.ci.variable: config.Infra.codegen.make.ci.value,
            "MISE_OFFLINE": "1",
        }

        setup = tm.ok(u.Tests.run_isolated_make(["setup"], cwd=root, env=environment))

        output = setup.stdout + setup.stderr
        tm.that(output, lacks="Cannot resolve the physical workspace")
        tm.that(
            output,
            has=f"Failed to install {config.Infra.codegen.toolchain.mise_selector}@",
        )

    @staticmethod
    def test_setup_provisions_the_pin_and_never_writes_a_lock(tmp_path: Path) -> None:
        """The rendered setup recipe installs the committed pin, never resolves."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        setup = rendered.split("_bootstrap_setup_tools:", 1)[1].split("\n\n", 1)[0]

        tm.that(setup, has="bootstrap_stage=lock-pin")
        tm.that(
            setup,
            has=(
                'MISE_LOCKED=1 "$(BOOTSTRAP_MISE)" -C "$(PROJECT_ROOT)" install --yes'
            ),
        )
        tm.that(
            setup,
            has=(
                'mise_pin="$$(MISE_LOCKED=1 "$(BOOTSTRAP_MISE)" -C '
                '"$(PROJECT_ROOT)" tool'
            ),
        )
        tm.that(setup, has='"$$mise_pin "*)')
        tm.that(setup, has='"$$mise_reader" -C "$(PROJECT_ROOT)" install --yes')
        tm.that(setup, has="bootstrap_stage=release-verification")
        tm.that(setup, has="re-provisioning the pinned release")
        tm.that(
            setup,
            has=(
                'MISE_LOCKED=1 "$(BOOTSTRAP_MISE)" -C "$(PROJECT_ROOT)" '
                "install --force --yes"
            ),
        )
        tm.that(
            setup,
            lacks=['MISE_LOCKFILE=0 "$(BOOTSTRAP_MISE)"', " lock"],
        )

    @staticmethod
    def test_upgrade_locks_only_through_the_declared_release(tmp_path: Path) -> None:
        """Every lock write of the upgrade names the declared self release."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        upgrade = rendered.split("_upg_toolchain:", 1)[1].split("\n\n", 1)[0]

        tm.that(upgrade, has='MISE_LOCKFILE=0 "$(BOOTSTRAP_MISE)"')
        tm.that(upgrade, has='"$$mise_reader" --version')
        tm.that(
            upgrade,
            has='"$$mise_reader" -C "$$lock_root" lock --bump --dry-run --json',
        )
        tm.that(upgrade, has='"$$mise_reader" -C "$$lock_root" lock')
        tm.that(upgrade, lacks='"$(BOOTSTRAP_MISE)" -C "$$lock_root"')

    @c.Tests.MARK.parametrize(
        ("pin", "acquires"),
        [("installed", False), ("2000.1.1", False), ("9999.1.1", True)],
    )
    def test_acquisition_raises_an_older_installed_mise_to_the_pin(
        self,
        tmp_path: Path,
        pin: str,
        *,
        acquires: bool,
    ) -> None:
        """An installed acquisition Mise older than the pin is re-acquired.

        The committed min_version makes an older Mise refuse every later
        command, so only absence or an older release runs the installer; a
        release at or above the pin is kept. The installer download is routed
        to a closed local port, so re-acquisition fails loudly at curl instead
        of reaching the network.
        """
        host_mise = Path(tm.not_none(shutil.which("mise"))).resolve()
        bin_dir = tmp_path / "home" / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "mise").symlink_to(host_mise)
        installed = tm.ok(
            u.Cli.run_raw(
                [str(host_mise), "--version"],
                options=m.Cli.ProcessOptions(env=self.environment(tmp_path)),
            ),
        ).stdout.split()[0]
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"mise_version": installed if pin == "installed" else pin},
        )
        shutil.copyfile(
            u.Infra.codegen_templates_root(config.Infra.codegen)
            / "base"
            / "tool_bootstrap_recipe.j2",
            tmp_path / "tool_bootstrap_recipe.j2",
        )
        template = tmp_path / "acquisition.j2"
        template.write_text(
            '{% from "tool_bootstrap_recipe.j2" import mise_acquisition, '
            "mise_staging_cleanup %}"
            "BOOTSTRAP_MISE := $(HOME)/.local/bin/mise\n"
            "PROJECT_ROOT := $(CURDIR)\n"
            "setup:\n"
            "\t+@set -eu; \\\n"
            "\tbootstrap_status=0; mise_stage=; \\\n"
            "\ttrap 'bootstrap_status=$$?; trap - EXIT; \\\n"
            "\t\t{{ mise_staging_cleanup() }} \\\n"
            '\t\texit "$${bootstrap_status}"\' EXIT; \\\n'
            '\t{{ mise_acquisition("$(PROJECT_ROOT)", toolchain) }}\n',
            encoding="utf-8",
        )
        (tmp_path / "Makefile").write_text(
            tm.ok(
                u.Cli.template_render(
                    template,
                    TestsFlextInfraMisePinBootstrap.WriterRenderContext(
                        toolchain=toolchain,
                        install_tools=(),
                    ),
                ),
            ),
            encoding="utf-8",
        )
        (tmp_path / c.Infra.MISE_TOML_FILENAME).write_text(
            "[tools]\n", encoding="utf-8"
        )

        setup = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "setup"],
                cwd=tmp_path,
                env={
                    **self.environment(tmp_path),
                    "https_proxy": "http://127.0.0.1:9",
                    "HTTPS_PROXY": "http://127.0.0.1:9",
                },
            ),
        )

        output = setup.stdout + setup.stderr
        tm.that(u.Cli.process_succeeded(setup.outcome), eq=not acquires, msg=output)
        tm.that("curl:" in output, eq=acquires, msg=output)
        tm.that((bin_dir / "mise").resolve(), eq=host_mise)

    @c.Tests.MARK.slow
    def test_lock_stage_rewrites_a_foreign_entry_to_the_declared_spec(
        self,
        tmp_path: Path,
    ) -> None:
        """The declared release writes the tool under the declared lock key."""
        self._writer_project(tmp_path)
        upgrade = tm.ok(
            u.Tests.run_isolated_make(
                ["upg"], cwd=tmp_path, env=self.environment(tmp_path)
            )
        )
        tm.that(
            u.Cli.process_succeeded(upgrade.outcome),
            eq=True,
            msg=upgrade.stdout + upgrade.stderr,
        )
        tools = u.Tests.toml_mapping(
            u.Tests.toml_payload(
                (tmp_path / "mise.lock").read_text(encoding=c.DEFAULT_ENCODING)
            )["tools"]
        )
        selector = config.Infra.codegen.toolchain.tool_keys["direnv"]
        tm.ok(selector in tools)
        entries = u.Tests.toml_list(tools[selector])
        entry = u.Tests.toml_mapping(entries[0])
        tm.that(entry["version"], is_=str)
        tm.that(entry["specifiers"], eq=["latest"])

    @staticmethod
    def _writer_project(tmp_path: Path) -> None:
        """Render only the upgrade lock stage over a committed tree."""
        u.Tests.initialize_git_repo(tmp_path)
        (tmp_path / "home").mkdir()
        toolchain = config.Infra.codegen.toolchain
        shutil.copyfile(
            Path(__file__).resolve().parents[3] / c.Infra.MISE_TOML_FILENAME,
            tmp_path / c.Infra.MISE_TOML_FILENAME,
        )
        selector = toolchain.tool_keys["direnv"]
        lock = u.Tests.repo_mise_lock()
        (tmp_path / c.Infra.MISE_LOCK_FILENAME).write_text(
            lock.replace(f'[[tools."{selector}"]]', "[[tools.direnv]]").replace(
                f'[tools."{selector}".', "[tools.direnv."
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        template_root = u.Infra.codegen_templates_root(config.Infra.codegen)
        shutil.copyfile(
            template_root / "base" / "tool_bootstrap_recipe.j2",
            tmp_path / "tool_bootstrap_recipe.j2",
        )
        template = tmp_path / "writer.j2"
        template.write_text(
            '{% from "tool_bootstrap_recipe.j2" import mise_acquisition, '
            "mise_declared_reader, mise_lock_changed, mise_staging_cleanup %}"
            "PROJECT_ROOT := $(CURDIR)\n"
            "upg:\n"
            "\t+@set -eu; \\\n"
            "\tbootstrap_status=0; mise_stage=; \\\n"
            "\ttrap 'bootstrap_status=$$?; trap - EXIT; \\\n"
            "\t\t{{ mise_staging_cleanup() }} \\\n"
            '\t\texit "$${bootstrap_status}"\' EXIT; \\\n'
            '\t{{ mise_acquisition("$(PROJECT_ROOT)", toolchain) }} \\\n'
            '\t{{ mise_declared_reader("$(PROJECT_ROOT)", toolchain) }} \\\n'
            "\t{{ mise_lock_changed('\"$$mise_reader\"', "
            "'\"$(PROJECT_ROOT)\"', install_tools) }}\n",
            encoding="utf-8",
        )
        recipe = tm.ok(
            u.Cli.template_render(
                template,
                TestsFlextInfraMisePinBootstrap.WriterRenderContext(
                    toolchain=toolchain,
                    install_tools=toolchain.mise_install_keys,
                ),
            ),
        )
        (tmp_path / "Makefile").write_text(recipe, encoding="utf-8")
        tm.ok(
            u.Cli.run_checked(
                ["mise", "trust", str(tmp_path / c.Infra.MISE_TOML_FILENAME)],
                options=m.Cli.ProcessOptions(
                    env=TestsFlextInfraMisePinBootstrap.environment(tmp_path),
                ),
            ),
        )

    @c.Tests.MARK.slow
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
            **self.environment(tmp_path),
            "PATH": str(self.system_path_without_mise(tmp_path)),
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
        tm.ok(executable.is_relative_to(tmp_path))
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

    @c.Tests.MARK.slow
    def test_hosted_setup_publishes_the_installed_tool_directories(
        self,
        tmp_path: Path,
    ) -> None:
        """Later hosted steps run the declared tools from any working directory.

        Premise (flext-cli CI run 42473521346): setup published its shim farm,
        and a shim resolves its version from the caller's working directory,
        so a formatter run in a test's temporary directory failed with
        "No version is set for shim: taplo".
        """
        self._project(tmp_path)
        lock = u.Tests.repo_mise_lock()
        (tmp_path / "mise.lock").write_text(lock, encoding=c.DEFAULT_ENCODING)
        github_path = tmp_path / "github-path.txt"
        github_path.touch()
        environment = {
            **self.environment(tmp_path),
            "PATH": str(self.system_path_without_mise(tmp_path)),
            "GITHUB_PATH": str(github_path),
        }

        setup = tm.ok(
            u.Tests.run_isolated_make(["setup"], cwd=tmp_path, env=environment)
        )

        tm.that(
            u.Cli.process_succeeded(setup.outcome),
            eq=True,
            msg=setup.stdout + setup.stderr,
        )
        published = github_path.read_text(encoding=c.DEFAULT_ENCODING).splitlines()
        installs = tmp_path / "data/mise/installs"
        tm.that(published, empty=False)
        tm.ok(all(Path(entry).is_relative_to(installs) for entry in published))
        mise = shutil.which("mise", path=os.pathsep.join(published))
        tm.that(mise, none=False)
        outside = tmp_path / "outside"
        outside.mkdir()
        version = tm.ok(
            u.Cli.capture(
                [str(mise), "--version"],
                cwd=outside,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )
        tm.that(
            version.split()[0],
            eq=u.Tests.pinned_mise_version(
                lock, config.Infra.codegen.toolchain.mise_selector
            ),
        )

    @c.Tests.MARK.slow
    def test_wrong_real_cached_release_is_replaced_before_lifecycle(
        self,
        tmp_path: Path,
    ) -> None:
        """A genuine release replacing the pinned install is repaired from the lock."""
        current = tmp_path / "current"
        current.mkdir()
        self._project(current)
        selector = config.Infra.codegen.toolchain.mise_selector
        lock = u.Tests.repo_mise_lock()
        (current / "mise.lock").write_text(lock, encoding=c.DEFAULT_ENCODING)
        pin = u.Tests.pinned_mise_version(lock, selector)
        environment = self.environment(current)
        installed = tm.ok(
            u.Tests.run_isolated_make(["setup"], cwd=current, env=environment),
        )
        tm.that(
            u.Cli.process_succeeded(installed.outcome),
            eq=True,
            msg=installed.stdout + installed.stderr,
        )
        current_executable = Path(
            (current / "runtime-mise-path.txt").read_text().strip(),
        )
        current_bytes = current_executable.read_bytes()
        # Another genuine release, provisioned natively beside the pin, replaces
        # the pinned executable: only the lock may decide what runs next.
        other = tmp_path / "other-release"
        other.mkdir()
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
        tm.ok(
            u.Cli.run_checked(
                ["mise", "install", f"{selector}@{older}"],
                cwd=other,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )
        replacement = tm.ok(
            u.Cli.capture(
                ["mise", "where", f"{selector}@{older}"],
                cwd=other,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        ).strip()
        shutil.copyfile(Path(replacement, "bin", "mise"), current_executable)
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
                    "PATH": str(self.system_path_without_mise(current)),
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
        mirrored = u.Tests.build_git_mirrors(project, tmp_path, sources)
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
