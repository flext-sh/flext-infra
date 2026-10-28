"""Generated Make upgrade lifecycle and lock ownership contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, r, t, tm, u


class TestsFlextInfraCodegenMakeUpgrade:
    """Prove only ``upg`` resolves locks and setup preserves native lock inputs."""

    @staticmethod
    def test_help_parses_before_runtime_provisioning(
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """Public help parses bootstrap recipes without creating an environment."""
        _profile, root = generated_make_template
        environment = root / c.Infra.ENVIRONMENT_DIRECTORY
        tm.fail(environment.exists())
        output = tm.ok(u.Tests.run_isolated_make(["help"], cwd=root))
        tm.that(
            u.Cli.process_succeeded(output.outcome),
            eq=True,
            msg=output.stdout + output.stderr,
        )
        tm.fail(environment.exists())

    @staticmethod
    def test_setup_installs_dependencies_before_importing_infra(
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """Native config admission precedes sync; Python validation follows it."""
        _profile, project_root = generated_make_template
        makefile = (project_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8",
        )
        recipe = makefile.split("INSTALL_RUNTIME_RECIPE = ", 1)[1].split(
            "\n\n",
            1,
        )[0]
        admitted = recipe.index("config ls --json")
        installed = recipe.index("$(UV) sync")
        validated = recipe.index("codegen mise-artifacts")
        tm.ok(admitted < installed < validated)
        tm.that(recipe[:installed], lacks="$(PROJECT_FLEXT_INFRA)")

    @staticmethod
    def test_environment_prerequisites_resolve_without_running_recipes(
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """GNU Make resolves the complete environment guard dependency graph."""
        _profile, project_root = generated_make_template
        checked = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "--question", "_builtin_require_environment"],
                cwd=project_root,
            ),
        )
        # Question mode reports pending phony recipes as 1, unresolved rules as 2.
        tm.that(
            checked.outcome.raw_return_code,
            eq=1,
            msg=checked.stdout + checked.stderr,
        )

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    @pytest.mark.parametrize("verb", ["setup", "upg"])
    def test_setup_preserves_the_resolved_native_locks(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
        verb: str,
    ) -> None:
        """Both lifecycles use Mise's interpreter; setup preserves native locks."""
        profile = c.Infra.MakeProfile.STANDALONE
        project_root = u.Tests.resolved_make_checkout(
            resolved_make_templates[profile],
            tmp_path / "locked-setup",
            profile,
        )
        locks = (
            project_root / c.Infra.MISE_LOCK_FILENAME,
            project_root / c.Infra.UV_LOCK_FILENAME,
        )
        previous = tuple(lock.read_bytes() for lock in locks)

        provisioned = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", verb],
                cwd=project_root,
            ),
        )

        tm.that(
            u.Cli.process_succeeded(provisioned.outcome),
            eq=True,
            msg=provisioned.stdout + provisioned.stderr,
        )
        if verb == "setup":
            tm.that(tuple(lock.read_bytes() for lock in locks), eq=previous)
        tm.that(
            (u.Infra.runtime_environment_dir(project_root) / "pyvenv.cfg").is_file(),
            eq=True,
        )
        managed_python = tm.ok(
            u.Cli.capture(
                ["mise", "-C", str(project_root), "which", "python"],
                cwd=project_root,
            ),
        ).strip()
        base_prefix_command = ["-c", "import sys; print(sys.base_prefix)"]
        managed_prefix = tm.ok(
            u.Cli.capture([managed_python, *base_prefix_command], cwd=project_root),
        ).strip()
        environment_python = u.Infra.runtime_environment_dir(project_root) / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        environment_prefix = tm.ok(
            u.Cli.capture(
                [str(environment_python), *base_prefix_command], cwd=project_root
            ),
        ).strip()
        tm.that(environment_prefix, eq=managed_prefix)

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_native_upg_repairs_the_generated_self_source_before_resolution(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
    ) -> None:
        """A stale generated self override cannot block its own upgrade producer."""
        profile = c.Infra.MakeProfile.STANDALONE
        project_root = u.Tests.resolved_make_checkout(
            resolved_make_templates[profile],
            tmp_path / "stale-self-source",
            profile,
        )
        pyproject = project_root / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(pyproject.read_text(encoding="utf-8"))
        project = tm.not_none(u.Cli.toml_table_child(document, c.Infra.PROJECT))
        distribution = str(project[c.Infra.NAME])
        tool = tm.not_none(u.Cli.toml_table_child(document, c.Infra.TOOL))
        uv = tm.not_none(u.Cli.toml_table_child(tool, "uv"))
        u.Cli.toml_remove_key_if_present(uv, "sources")
        u.Cli.toml_sync_string_list(uv, "override-dependencies", (distribution,))
        tm.ok(u.Cli.atomic_write_text_file(pyproject, u.Cli.toml_dumps(document)))
        upgraded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=project_root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(upgraded.outcome),
            eq=True,
            msg=upgraded.stdout + upgraded.stderr,
        )
        source = u.Tests.toml_table_at(
            pyproject.read_text(encoding="utf-8"),
            "tool",
            "uv",
            "sources",
            distribution,
        )
        tm.that(source, eq={"workspace": True})

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_setup_rejects_invalid_lock_without_syncing_dependencies(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
    ) -> None:
        """The real setup refuses invalid lock input without changing packages."""
        profile = c.Infra.MakeProfile.STANDALONE
        project_root = u.Tests.resolved_make_checkout(
            resolved_make_templates[profile],
            tmp_path / "invalid-setup-lock",
            profile,
        )
        lock = project_root / c.Infra.UV_LOCK_FILENAME
        lock.write_text('version = "invalid"\n', encoding="utf-8")
        previous_lock = lock.read_bytes()
        environment = u.Infra.runtime_environment_dir(project_root)
        previous_packages = tuple(
            sorted(environment.glob("lib/python*/site-packages/*.dist-info")),
        )

        provisioned = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "setup"],
                cwd=project_root,
            ),
        )

        tm.fail(u.Cli.process_succeeded(provisioned.outcome))
        tm.that(provisioned.stderr, has=c.Infra.UV_LOCK_FILENAME)
        tm.that(lock.read_bytes(), eq=previous_lock)
        tm.that(
            tuple(sorted(environment.glob("lib/python*/site-packages/*.dist-info"))),
            eq=previous_packages,
        )

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_failed_native_upg_resolution_preserves_the_previous_lock(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
    ) -> None:
        """Invalid native manifest input fails without replacing the prior lock."""
        profile = c.Infra.MakeProfile.STANDALONE
        project_root = u.Tests.resolved_make_checkout(
            resolved_make_templates[profile],
            tmp_path / "lock-failure",
            profile,
        )
        lock = project_root / c.Infra.MISE_LOCK_FILENAME
        previous_lock = lock.read_bytes()
        (project_root / c.Infra.MISE_TOML_FILENAME).write_text(
            "[tools\n",
            encoding="utf-8",
        )

        upgraded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=project_root,
            ),
        )

        tm.fail(u.Cli.process_succeeded(upgraded.outcome))
        tm.ok(bool(upgraded.stderr.strip()))
        tm.that(lock.read_bytes(), eq=previous_lock)

    @pytest.mark.slow
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    def test_only_upg_resolves_and_cold_setup_preserves_immutable_sources(
        self,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Native upgrade resolves the candidate; cold hosted setup preserves locks."""
        root = resolved_make_templates[profile]
        parent = root.parent.parent
        checkout = (
            parent / c.Tests.MAKE_TEMPLATE_CI_CHECKOUT / profile.value / root.name
        )
        upgrade_source, setup_source = self._assert_cold_setup_receipts(parent)
        infra_url = u.Tests.repository_ref(
            config.Infra.codegen.infra_repository.distribution,
        ).url
        source = next(
            item
            for item in u.Tests.locked_git_sources(Path(__file__).resolve().parents[3])
            if item[0] == infra_url
        )
        self._assert_candidate_receipt_prefixes(
            parent,
            ((upgrade_source, root), (setup_source, checkout)),
            source,
        )
        self._assert_lock_floor_preserved(root, checkout, source)
        tm.that(
            (checkout / c.Infra.MISE_LOCK_FILENAME).read_bytes(),
            eq=(root / c.Infra.MISE_LOCK_FILENAME).read_bytes(),
        )
        foreign = parent / c.Tests.MAKE_TEMPLATE_HOSTILE_VENV
        tm.that((foreign / "sentinel").read_text(), eq="untouched\n")
        tm.that(tuple((foreign / "bin").iterdir()), eq=())

    @staticmethod
    def _assert_cold_setup_receipts(parent: Path) -> t.Pair[Path, Path]:
        """Require every cold-setup receipt to succeed and the hook to run.

        Returns:
            The upgrade and setup candidate-source receipt names.

        """
        upgrade_receipt = Path(c.Tests.MAKE_TEMPLATE_UPG_RECEIPT)
        setup_receipt = Path(c.Tests.MAKE_TEMPLATE_CI_RECEIPT)
        upgrade_source = upgrade_receipt.with_stem(f"{upgrade_receipt.stem}-source")
        setup_source = setup_receipt.with_stem(f"{setup_receipt.stem}-source")
        for receipt_name in (
            upgrade_receipt,
            upgrade_source,
            setup_receipt,
            setup_source,
        ):
            receipt = u.Tests.command_receipt(parent / receipt_name)
            tm.that(
                u.Cli.process_succeeded(receipt.outcome),
                eq=True,
                msg=receipt.stdout + receipt.stderr,
            )
        upgrade = u.Tests.command_receipt(parent / c.Tests.MAKE_TEMPLATE_UPG_RECEIPT)
        tm.that(upgrade.stdout, has="upg-hook-ran")
        return (upgrade_source, setup_source)

    @staticmethod
    def _assert_candidate_receipt_prefixes(
        parent: Path,
        observed: Sequence[t.Pair[Path, Path]],
        source: t.Triple[str, str, ...],
    ) -> None:
        """Require each receipt to record the locked source and its environment."""
        for name, project in observed:
            observation = u.Tests.command_receipt(parent / name)
            tm.that(observation.stdout, has=f"candidate-source={source[0]}#{source[2]}")
            environment = u.Infra.runtime_environment_dir(project)
            tm.fail(environment.is_symlink())
            tm.ok((environment / "pyvenv.cfg").is_file())
            tm.that(observation.stdout, has=f"candidate-prefix={environment.resolve()}")

    @staticmethod
    def _assert_lock_floor_preserved(
        root: Path, checkout: Path, source: t.Triple[str, str, ...]
    ) -> None:
        """Require the checkout's locks to match the resolved root exactly."""
        manifest = Path(c.PYPROJECT_FILENAME)
        lock = manifest.with_name(c.Infra.UV_LOCK_FILENAME)
        tm.ok((root / lock).is_file())
        tm.that((checkout / lock).read_bytes(), eq=(root / lock).read_bytes())
        packages = tuple(
            package
            for package in u.Tests.toml_tables_at(
                (root / lock).read_text(encoding="utf-8"),
                "package",
            )
            if package.get("name") == config.Infra.codegen.infra_repository.distribution
        )
        tm.that(len(packages), eq=1)
        locked_source = u.Tests.toml_mapping(packages[0].get("source"))
        tm.that(
            str(locked_source.get("git")).endswith(f"#{source[2]}"),
            eq=True,
        )
        tm.that(
            (checkout / manifest).read_bytes(),
            eq=(root / manifest).read_bytes(),
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    def test_setup_holds_no_lock_verdict_and_audit_owns_it(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
        profile: c.Infra.MakeProfile,
        hermetic_git_environment: Mapping[str, str],
    ) -> None:
        """Frozen setup provisions a stale native graph; audit reports the drift."""
        root = u.Tests.resolved_make_checkout(
            resolved_make_templates[profile],
            tmp_path / "drifted-consumer",
            profile,
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        view = root / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(view.read_text(encoding="utf-8"))
        groups = u.Cli.toml_ensure_table(document, "dependency-groups")
        project = u.Tests.toml_table_at(view.read_text(encoding="utf-8"), "project")
        groups["fixture-native-lock-drift"] = [str(project["name"])]
        tm.ok(u.Cli.atomic_write_text_file(view, u.Cli.toml_dumps(document)))
        locks = (
            root / c.Infra.MISE_LOCK_FILENAME,
            root / c.Infra.UV_LOCK_FILENAME,
        )
        before = {path: path.read_bytes() for path in locks}
        drifted_manifest = view.read_bytes()
        environment = u.Infra.runtime_environment_dir(root)
        tm.fail(environment.exists())
        native_environment = {
            **hermetic_git_environment,
            "UV_OFFLINE": c.ParserBooleanToken.ZERO,
            inputs.spec.make.ci.variable: inputs.spec.make.ci.value,
        }
        setup = tm.ok(
            u.Tests.run_isolated_make(["setup"], cwd=root, env=native_environment),
        )
        u.Tests.record_dependency_command_output(setup)
        tm.that(
            u.Cli.process_succeeded(setup.outcome),
            eq=True,
            msg=setup.stdout + setup.stderr,
        )
        tm.ok((environment / "pyvenv.cfg").is_file())
        audit = tm.ok(
            u.Tests.run_isolated_make(["audit"], cwd=root, env=native_environment),
        )
        u.Tests.record_dependency_command_output(audit)
        tm.fail(u.Cli.process_succeeded(audit.outcome))
        tm.that(audit.stdout + audit.stderr, has=["lock", "make upg"])
        tm.that({path: path.read_bytes() for path in locks}, eq=before)
        tm.that(view.read_bytes(), eq=drifted_manifest)

    @staticmethod
    @pytest.mark.parametrize(
        "generated_make_template",
        [c.Infra.MakeProfile.STANDALONE],
        indirect=True,
    )
    @pytest.mark.remote
    @pytest.mark.slow
    def test_native_shared_workspace_guard_stops_before_uv_lock(
        tmp_path: Path,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """A remaining native shared-lock declaration still fails before UV writes."""
        _profile, template = generated_make_template
        workspace = tmp_path / "workspace"
        member = workspace / "member"
        shutil.copytree(
            template,
            member,
            symlinks=True,
            ignore=shutil.ignore_patterns(".venv", c.GIT_DIR_NAME),
        )
        u.Tests.initialize_git_repo(member)
        workspace_lock = workspace / c.Infra.UV_LOCK_FILENAME
        u.Tests.initialize_git_repo(workspace)
        head = u.Tests.git_capture(member, "rev-parse", c.Infra.GIT_HEAD)
        u.Tests.git_run(
            workspace,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{head.strip()},member",
        )
        u.Tests.commit_git_changes(workspace, "attach member")
        (workspace / c.PYPROJECT_FILENAME).write_text(
            '[tool.uv.workspace]\nmembers = ["member"]\n',
            encoding="utf-8",
        )
        member_lock = member / c.Infra.UV_LOCK_FILENAME
        previous = member_lock.read_bytes() if member_lock.is_file() else None

        upgraded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=member,
            ),
        )

        tm.fail(u.Cli.process_succeeded(upgraded.outcome))
        tm.that(upgraded.stderr, has=["ERROR[upg]", str(workspace.resolve())])
        tm.that(
            member_lock.read_bytes() if member_lock.is_file() else None,
            eq=previous,
        )
        tm.fail(workspace_lock.exists())

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_failed_member_hook_prevents_containing_root_upgrade(
        tmp_path: Path,
        generated_make_templates: Mapping[c.Infra.MakeProfile, Path],
    ) -> None:
        """Actual public Make hooks propagate member failure without root effects."""
        workspace = tmp_path / "workspace"
        member = workspace / "member"
        for destination, profile in (
            (workspace, c.Infra.MakeProfile.WORKSPACE),
            (member, c.Infra.MakeProfile.STANDALONE),
        ):
            shutil.copytree(
                generated_make_templates[profile],
                destination,
                symlinks=True,
                ignore=shutil.ignore_patterns(".venv", c.GIT_DIR_NAME),
                dirs_exist_ok=True,
            )
            u.Tests.initialize_git_repo(destination)
        head = u.Tests.git_capture(member, "rev-parse", c.Infra.GIT_HEAD)
        u.Tests.git_run(
            workspace,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{head.strip()},member",
        )
        u.Tests.commit_git_changes(workspace, "attach member")
        marker = workspace / "root-upgrade-started"
        (workspace / c.Infra.MAKEFILE_CUSTOM_INCLUDE).write_text(
            'pre-upg:\n\t@touch "$(PROJECT_ROOT)/root-upgrade-started"\n',
            encoding="utf-8",
        )
        (member / c.Infra.MAKEFILE_CUSTOM_INCLUDE).write_text(
            "pre-upg:\n\t@printf 'member pre-upg failed\\n' >&2; exit 29\n",
            encoding="utf-8",
        )
        root_lock = workspace / c.Infra.UV_LOCK_FILENAME
        previous = root_lock.read_bytes() if root_lock.is_file() else None
        upgraded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=member,
            ),
        )
        tm.fail(u.Cli.process_succeeded(upgraded.outcome))
        tm.that(upgraded.stderr, has="member pre-upg failed")
        tm.fail(marker.is_file())
        tm.that(
            root_lock.read_bytes() if root_lock.is_file() else None,
            eq=previous,
        )

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_member_upgrade_reconciles_runtime_before_failing_hook(
        tmp_path: Path,
        resolved_make_templates: Mapping[c.Infra.MakeProfile, Path],
    ) -> None:
        """Native root satisfaction holds before the member observes shared runtime."""
        root = u.Tests.resolved_make_checkout(
            resolved_make_templates[c.Infra.MakeProfile.WORKSPACE],
            tmp_path / "runtime-owner",
            c.Infra.MakeProfile.WORKSPACE,
        )
        member = u.Tests.repository_ref("member", path=Path("member"))
        repository = u.Tests.repository_ref(member.distribution)
        source = tmp_path / "member-source"
        beads = u.Tests.beads_project(repository.name)
        u.Tests.WorktreeFixture.initialize_governed_project(
            source,
            repository.distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=beads.workspace,
                database=beads.database,
                issue_prefix=beads.issue_prefix,
            ),
        )
        plan = u.Tests.conform_plan(
            source,
            u.Tests.workspace_spec(
                repository,
                project=u.Tests.project_spec(repository.name),
            ),
        )
        tm.ok(
            u.Tests.materialize_codegen_plans(
                r[tuple[m.Infra.CodegenFilePlan, ...]].ok(plan.files),
            ),
        )
        u.Tests.commit_git_changes(source, "render independent upgrade consumer")
        branch = u.Tests.checkout_integration(source)
        u.Tests.git_bootstrap(
            root,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-b",
                branch,
                str(source),
                member.path.as_posix(),
            ),
        )
        u.Tests.git_bootstrap(
            root,
            (
                "config",
                "-f",
                c.Infra.GITMODULES,
                f"submodule.{member.path.as_posix()}.flext-managed",
                c.ParserBooleanToken.TRUE,
            ),
        )
        u.Tests.commit_git_changes(root, "attach upgrade consumer")
        pyproject = root / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(pyproject.read_text(encoding="utf-8"))
        project = tm.not_none(u.Cli.toml_table_child(document, "project"))
        version = str(project["version"]).partition("+")[0]
        project["version"] = f"{version}+upgradeprobe"
        tm.ok(u.Cli.atomic_write_text_file(pyproject, u.Cli.toml_dumps(document)))
        (root / c.Infra.MAKEFILE_CUSTOM_INCLUDE).write_text(
            "pre-upg:\n"
            '\t@touch "$(PROJECT_ROOT)/root-upgrade-started"\n'
            "post-setup:\n"
            '\t@$(UV) lock --check --project "$(RUNTIME_ROOT)"\n'
            "\t@$(UV_RUN) python -c 'import importlib.metadata; "
            "from pathlib import Path; import tomllib; "
            "project = tomllib.loads(Path( "
            'c.PYPROJECT_FILENAME).read_text())["project"]; '
            'assert importlib.metadata.version(project["name"]) == project["version"]'
            "'\n"
            "\t@printf '%s\\n' 'root-runtime-reconciled'\n",
            encoding="utf-8",
        )
        checkout = root / member.path
        (checkout / c.Infra.MAKEFILE_CUSTOM_INCLUDE).write_text(
            "post-upg:\n"
            '\t@$(UV) lock --check --project "$(RUNTIME_ROOT)"\n'
            '\t@$(UV) lock --check --project "$(PROJECT_ROOT)"\n'
            "\t@printf '%s\\n' 'member-runtime-reconciled'\n"
            "\t@printf '%s\\n' 'member-hook-stop' >&2; exit 29\n",
            encoding="utf-8",
        )
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=checkout,
                env={"GIT_ALLOW_PROTOCOL": "file:https:ssh"},
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=False,
            msg=process.stdout + process.stderr,
        )
        tm.that(
            process.stdout,
            has=["root-runtime-reconciled", "member-runtime-reconciled"],
        )
        tm.that(process.stderr, has="member-hook-stop")
        tm.ok((root / "root-upgrade-started").exists())
        tm.fail((checkout / ".venv").exists())
