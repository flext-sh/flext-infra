"""Soundness contracts for the rendered Makefile bootstrap recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u

class TestsFlextInfraMakefileBootstrapSoundness:
    """Public Make preserves physical ownership and native tool configuration."""

    @pytest.mark.parametrize(
        "entry",
        ["spaced", "symlink", "outside-spaced", "outside-symlink"],
    )
    def test_public_make_paths_keep_the_physical_runtime_owner(
        self,
        tmp_path: Path,
        entry: str,
    ) -> None:
        """Spaces, symlinks and external callers retain the selected file's owner."""
        parent = (
            tmp_path / "checkout with spaces"
            if "spaced" in entry
            else tmp_path / "physical-checkout"
        )
        project, _ = u.Tests.render_make_environment(
            parent,
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="physical-runtime-owner"),
        )
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            "$(info physical-runtime-root=$(RUNTIME_ROOT))\n"
            "$(info physical-runtime-environment=$(RUNTIME_VENV))\n"
            "$(info physical-runtime-resolution=$(UV_PROJECT))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        invoked = project
        if "symlink" in entry:
            invoked = tmp_path / "invocation-link"
            invoked.symlink_to(project, target_is_directory=True)
        caller = invoked
        arguments = ["help"]
        if entry.startswith("outside-"):
            caller = tmp_path / "outside-caller"
            caller.mkdir()
            arguments = ["-f", str(invoked / c.Infra.MAKEFILE_FILENAME), "help"]
        policy = config.Infra.codegen.make.uv_resolution
        ci = config.Infra.codegen.make.ci
        context_env = {
            policy.hosted_variable: "",
            ci.variable: ci.local_value,
        }
        observed = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    "from pathlib import Path; import sys; "
                    "from flext_infra.workspace import FlextInfraWorkspaceDetector; "
                    "context=FlextInfraWorkspaceDetector.resolution_context("
                    "Path(sys.argv[1])).unwrap(); print(context.model_dump_json())",
                    str(invoked),
                ),
                cwd=caller,
                options=m.Cli.ProcessOptions(
                    env=context_env,
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        process = tm.ok(
            u.Tests.run_isolated_make(arguments, cwd=caller, env=context_env),
        )
        tm.that(
            observed.outcome.raw_return_code,
            eq=0,
            msg=observed.stdout + observed.stderr,
        )
        context = m.Infra.WorkspaceRuntimeContext.model_validate_json(observed.stdout)
        physical = project.resolve()
        environment = physical / c.Infra.ENVIRONMENT_DIRECTORY
        resolution = physical / policy.local_directory
        u.Cli.emit_raw(
            f"path context entry={entry} submitted={invoked} "
            f"caller={caller} runtime={context.runtime_root}\n",
        )
        tm.that(context.project_root, eq=physical)
        tm.that(context.runtime_root, eq=physical)
        tm.that(context.environment_path, eq=environment)
        tm.that(context.resolution_root, eq=resolution)
        tm.that(
            process.outcome.raw_return_code,
            eq=0,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"physical-runtime-root={physical}\n")
        tm.that(
            process.stdout,
            has=f"physical-runtime-environment={environment}\n",
        )
        tm.that(process.stdout, has=f"physical-runtime-resolution={resolution}\n")
        tm.that(environment.exists(), eq=False)
        tm.that((caller / c.Infra.ENVIRONMENT_DIRECTORY).exists(), eq=False)
        tm.that((caller / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)

    @pytest.mark.parametrize("invocation", ["root", "member"])
    @pytest.mark.parametrize("hosted", [False, True])
    def test_hosted_runtime_is_independent_of_local_ci_partition(
        self,
        tmp_path: Path,
        invocation: str,
        *,
        hosted: bool,
    ) -> None:
        """Make and the runtime API distinguish hosted isolation from local CI.

        This observes election before provisioning. The workspace owns a real
        environment; the associated member has no environment to borrow.
        """
        root, _ = u.Tests.render_make_environment(
            tmp_path / "hosted-container",
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="hosted-owner-root"),
        )
        member, _ = u.Tests.render_make_environment(
            root,
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="hosted-owner-member"),
        )
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution=member.name,
            relative_path=member.relative_to(root).as_posix(),
        )
        u.Tests.git_run(root, "submodule", "absorbgitdirs")
        binary = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        environment = root / c.Infra.ENVIRONMENT_DIRECTORY
        native_options = m.Cli.ProcessOptions(
            remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
        )
        created = tm.ok(
            u.Cli.run_raw(
                [str(binary), "venv", "--python", sys.executable, str(environment)],
                cwd=root,
                options=native_options,
            ),
        )
        tm.that(
            created.outcome.raw_return_code,
            eq=0,
            msg=created.stdout + created.stderr,
        )
        tm.that(environment.is_symlink(), eq=False)
        tm.that((environment / "pyvenv.cfg").is_file(), eq=True)
        member_environment = member / c.Infra.ENVIRONMENT_DIRECTORY
        tm.that(member_environment.exists(), eq=False)
        project = root if invocation == "root" else member
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            "$(info elected-root=$(RUNTIME_ROOT))\n"
            "$(info elected-environment=$(RUNTIME_VENV))\n"
            "$(info elected-resolution=$(UV_PROJECT))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        policy = config.Infra.codegen.make.uv_resolution
        ci = config.Infra.codegen.make.ci
        context_env = {
            ci.variable: ci.value,
            policy.hosted_variable: policy.hosted_value if hosted else "",
        }
        elected = project if hosted else root
        resolution = elected / (
            policy.standalone_directory if hosted else policy.local_directory
        )
        process = tm.ok(
            u.Tests.run_isolated_make(["help"], cwd=project, env=context_env),
        )
        observed = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    "from pathlib import Path; import sys; "
                    "from flext_infra.workspace import FlextInfraWorkspaceDetector; "
                    "context=FlextInfraWorkspaceDetector.resolution_context("
                    "Path(sys.argv[1])).unwrap(); print(context.model_dump_json())",
                    str(project),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env=context_env,
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        tm.that(
            observed.outcome.raw_return_code,
            eq=0,
            msg=observed.stdout + observed.stderr,
        )
        context = m.Infra.WorkspaceRuntimeContext.model_validate_json(observed.stdout)
        u.Cli.emit_raw(
            f"native context runtime={context.runtime_root} "
            f"environment={context.environment_path} "
            f"resolution={context.resolution_root} hosted={context.standalone}\n",
        )
        tm.that(
            process.outcome.raw_return_code,
            eq=0,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"elected-root={elected.resolve()}\n")
        tm.that(
            process.stdout,
            has=f"elected-environment={elected / c.Infra.ENVIRONMENT_DIRECTORY}\n",
        )
        tm.that(process.stdout, has=f"elected-resolution={resolution}\n")
        tm.that(context.project_root, eq=project.resolve())
        tm.that(context.runtime_root, eq=elected.resolve())
        tm.that(
            context.environment_path,
            eq=elected / c.Infra.ENVIRONMENT_DIRECTORY,
        )
        tm.that(context.resolution_root, eq=resolution)
        tm.that(context.standalone, eq=hosted)
        tm.that(member_environment.exists(), eq=False)

    def test_python_project_without_python_ancestor_owns_its_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        """A Git-only container supplies no Python composition or tool manifest."""
        container = tmp_path / "git-only-container"
        container.mkdir()
        u.Tests.initialize_git_repo(
            container,
            origin_url=u.Tests.repository_ref(container.name).url,
        )
        seed, _ = u.Tests.render_make_environment(
            tmp_path / "independent-seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="independent-python"),
        )
        project = container / "packages" / seed.name
        shutil.copytree(
            seed,
            project,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", c.Infra.ENVIRONMENT_DIRECTORY),
        )
        binary = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, seed))
        native_options = m.Cli.ProcessOptions(
            remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
        )
        owner = Path(
            tm.ok(
                u.Cli.capture(
                    [str(binary), "workspace", "dir", "--project", str(project)],
                    cwd=project,
                    options=native_options,
                ),
            ).strip(),
        ).resolve()
        tm.that(owner, eq=project.resolve())
        environment = project / c.Infra.ENVIRONMENT_DIRECTORY
        provisioned = tm.ok(
            u.Cli.run_raw(
                [str(binary), "venv", "--python", sys.executable, str(environment)],
                cwd=project,
                options=native_options,
            ),
        )
        tm.that(
            provisioned.outcome.raw_return_code,
            eq=0,
            msg=provisioned.stdout + provisioned.stderr,
        )
        tm.that(environment.is_symlink(), eq=False)
        tm.that((environment / "pyvenv.cfg").is_file(), eq=True)
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            "\t@printf 'independent-root=%s\\n' '$(RUNTIME_ROOT)'\n"
            "\t@printf 'independent-environment=%s\\n' '$(RUNTIME_VENV)'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.that(
            process.outcome.raw_return_code,
            eq=0,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"independent-root={project.resolve()}\n")
        tm.that(
            process.stdout,
            has=f"independent-environment={environment.resolve()}\n",
        )
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project))
        tm.that(context.runtime_root, eq=project.resolve())
        tm.that(context.environment_path, eq=environment.resolve())
        for path in (
            container / c.PYPROJECT_FILENAME,
            container / c.Infra.MISE_TOML_FILENAME,
            container / c.Infra.MISE_LOCK_FILENAME,
            container / c.Infra.ENVIRONMENT_DIRECTORY,
        ):
            tm.that(path.exists(), eq=False)

    def test_dangling_git_marker_rejects_ancestor_discovery(
        self,
        tmp_path: Path,
    ) -> None:
        """A malformed declared Git boundary cannot become an absent boundary."""
        outer, _ = u.Tests.render_make_environment(
            tmp_path / "outer",
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="outer-python-root"),
        )
        boundary = outer / "broken-python-boundary"
        u.Tests.write_native_resolution_project(boundary, boundary.name)
        seed, _ = u.Tests.render_make_environment(
            tmp_path / "nested-seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="nested-python-root"),
        )
        project = boundary / seed.name
        shutil.copytree(
            seed,
            project,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", c.Infra.ENVIRONMENT_DIRECTORY),
        )
        u.Tests.initialize_git_repo(
            project,
            origin_url=u.Tests.repository_ref(project.name).url,
        )
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            "\t@printf '%s\\n' 'nested-help-executed'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        baseline = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.that(
            baseline.outcome.raw_return_code,
            eq=0,
            msg=baseline.stdout + baseline.stderr,
        )
        tm.that(baseline.stdout, has="nested-help-executed")
        marker = boundary / c.Infra.GIT_DIR
        marker.symlink_to(tmp_path / "missing-git-directory", target_is_directory=True)
        native_error = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.GIT,
                    "-C",
                    str(boundary),
                    "rev-parse",
                    "--resolve-git-dir",
                    str(marker),
                ],
                cwd=boundary,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        tm.that(native_error.outcome.raw_return_code != 0, eq=True)
        tm.that(bool(native_error.stderr.strip()), eq=True)
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.that(process.outcome.raw_return_code != 0, eq=True)
        tm.that(process.stderr, has=native_error.stderr.strip())
        tm.that(process.stdout, lacks="nested-help-executed")
        context = FlextInfraWorkspaceDetector.resolution_context(project)
        tm.that(context.failure, eq=True)
        tm.that(marker.is_symlink(), eq=True)
        tm.that(marker.exists(), eq=False)
        tm.that((project / c.Infra.ENVIRONMENT_DIRECTORY).exists(), eq=False)

    @pytest.mark.parametrize("associated_clone", [False, True])
    def test_help_observes_native_workspace_owner_without_member_environment(
        self,
        tmp_path: Path,
        *,
        associated_clone: bool,
    ) -> None:
        """Make reports UV membership before a member environment exists.

        This proves owner election only. It does not qualify cold bootstrap,
        dependency provisioning or setup/upgrade delegation.
        """
        root, _ = u.Tests.render_make_environment(
            tmp_path / "container",
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="native-owner-root"),
        )
        seed, _ = u.Tests.render_make_environment(
            tmp_path / "member-seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="native-owner-member"),
        )
        member = root / "packages" / seed.name
        shutil.copytree(
            seed,
            member,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", c.Infra.ENVIRONMENT_DIRECTORY),
        )
        if associated_clone:
            u.Tests.initialize_git_repo(
                member,
                origin_url=u.Tests.repository_ref(member.name).url,
            )
        document = u.Tests.toml_doc(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
        )
        tool = u.Cli.toml_ensure_table(document, "tool")
        uv = u.Cli.toml_ensure_table(tool, "uv")
        uv["workspace"] = {"members": [member.relative_to(root).as_posix()]}
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.PYPROJECT_FILENAME,
                u.Cli.toml_dumps(document),
            ),
        )
        binary = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        native_options = m.Cli.ProcessOptions(
            remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
        )
        owner = Path(
            tm.ok(
                u.Cli.capture(
                    [str(binary), "workspace", "dir", "--project", str(member)],
                    cwd=member,
                    options=native_options,
                ),
            ).strip(),
        ).resolve()
        tm.that(owner, eq=root.resolve())
        environment = root / c.Infra.ENVIRONMENT_DIRECTORY
        created = tm.ok(
            u.Cli.run_raw(
                [
                    str(binary),
                    "venv",
                    "--python",
                    sys.executable,
                    str(environment),
                ],
                cwd=root,
                options=native_options,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(created.outcome),
            eq=True,
            msg=created.stdout + created.stderr,
        )
        tm.that(environment.is_symlink(), eq=False)
        tm.that((environment / "pyvenv.cfg").is_file(), eq=True)
        member_environment = member / c.Infra.ENVIRONMENT_DIRECTORY
        tm.that(member_environment.exists(), eq=False)
        (member / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            "\t@printf 'native-runtime-root=%s\\n' '$(RUNTIME_ROOT)'\n"
            "\t@printf 'native-runtime-environment=%s\\n' '$(RUNTIME_VENV)'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        parent_lock = root / c.Infra.MISE_LOCK_FILENAME
        member_lock = member / c.Infra.MISE_LOCK_FILENAME
        locks_before = (parent_lock.read_bytes(), member_lock.read_bytes())
        metadata_before = tuple(
            (project / c.PYPROJECT_FILENAME).read_bytes()
            for project in (root, member)
        )
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=member))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"native-runtime-root={owner}\n")
        tm.that(
            process.stdout,
            has=f"native-runtime-environment={environment.resolve()}\n",
        )
        tm.that(member_environment.exists(), eq=False)
        tm.that(
            (parent_lock.read_bytes(), member_lock.read_bytes()),
            eq=locks_before,
        )
        tm.that(
            tuple(
                (project / c.PYPROJECT_FILENAME).read_bytes()
                for project in (root, member)
            ),
            eq=metadata_before,
        )

    def test_public_make_preserves_native_project_mise_lock_scope(
        self,
        tmp_path: Path,
    ) -> None:
        """The complete Make environment cannot reclassify project tools as global."""
        project, _ = u.Tests.render_make_environment(
            tmp_path / "project",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="mise-project-scope"),
        )
        home = tmp_path / "host-home"
        home.mkdir()
        xdg = tmp_path / "host-config"
        global_config = xdg / "mise" / "config.toml"
        global_config.parent.mkdir(parents=True)
        global_config.write_text(
            '[env]\nNATIVE_SCOPE_HOST_SENTINEL = "fixture-owned-global"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that((project / ".mise" / "config.toml").exists(), eq=False)
        config_report = tmp_path / "mise-config-files.json"
        lock_report = tmp_path / "mise-project-locks.json"
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            '\t@mise -C "$(RUNTIME_ROOT)" config ls --json > '
            f"{quote(str(config_report))}\n"
            '\t@mise -C "$(RUNTIME_ROOT)" lock --sidecars --json > '
            f"{quote(str(lock_report))}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        paths = (
            project / c.Infra.MISE_TOML_FILENAME,
            project / c.Infra.MISE_LOCK_FILENAME,
            project / c.PYPROJECT_FILENAME,
            global_config,
        )
        before = tuple(path.read_bytes() for path in paths)
        environment = {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(xdg),
            "XDG_DATA_HOME": str(tmp_path / "host-data"),
            "XDG_STATE_HOME": str(tmp_path / "host-state"),
            "XDG_CACHE_HOME": str(tmp_path / "host-cache"),
            "MISE_DATA_DIR": str(tmp_path / "host-data" / "mise"),
            "MISE_STATE_DIR": str(tmp_path / "host-state" / "mise"),
            "MISE_CACHE_DIR": str(tmp_path / "host-cache" / "mise"),
            "MISE_TRUSTED_CONFIG_PATHS": str(project),
            "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_PARAMETERS": "",
            "GIT_CONFIG_COUNT": "0",
        }

        process = tm.ok(
            u.Tests.run_isolated_make(["help"], cwd=project, env=environment),
        )

        tm.that(
            process.outcome.raw_return_code,
            eq=0,
            msg=process.stdout + process.stderr,
        )
        native_paths: set[Path] = set()
        for row in u.Cli.json_as_sequence(
            tm.ok(u.Cli.json_loads(config_report.read_text(encoding=c.DEFAULT_ENCODING))),
        ):
            path = u.Cli.json_as_mapping(row)["path"]
            tm.that(path, is_=str)
            if isinstance(path, str):
                native_paths.add(Path(path).resolve())
        tm.that(project / c.Infra.MISE_TOML_FILENAME in native_paths, eq=True)
        tm.that(global_config in native_paths, eq=False)
        project_locks: set[Path] = set()
        # Mise's official SidecarListing reports default project-scope lock targets
        # without resolving tools, installing packages or changing the lock.
        for row in u.Cli.json_as_sequence(
            tm.ok(u.Cli.json_loads(lock_report.read_text(encoding=c.DEFAULT_ENCODING))),
        ):
            path = u.Cli.json_as_mapping(row)["lockfile"]
            tm.that(path, is_=str)
            if isinstance(path, str):
                project_locks.add((project / path).resolve())
        tm.that(project_locks, eq={project / c.Infra.MISE_LOCK_FILENAME})
        tm.that(tuple(path.read_bytes() for path in paths), eq=before)

    @pytest.mark.parametrize("scenario", ["relative-link", "link-cycle"])
    def test_public_make_authenticates_file_aliases_without_replacing_the_invoker(
        self,
        tmp_path: Path,
        scenario: str,
    ) -> None:
        """Native Make/file aliases resolve physically; a link cycle fails bounded."""
        project, _ = u.Tests.render_make_environment(
            tmp_path / "alias project",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="make-file-alias"),
        )
        binary = Path(tm.not_none(shutil.which(c.Infra.MAKE))).resolve()
        directory = project / "bin"
        directory.mkdir()
        entry = directory / "make-entry"
        target = directory / "make-target"
        entry.symlink_to(target.name)
        target.symlink_to(
            entry.name if scenario == "link-cycle" else binary,
        )
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            "$(info physical-invoker=$(SELF_MAKE_EXECUTABLE))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        arguments = ["help", f"MAKE_COMMAND={entry}"]
        if scenario == "relative-link":
            selected = project / "selected-Makefile"
            selected.symlink_to(c.Infra.MAKEFILE_FILENAME)
            arguments = [
                "-f",
                selected.name,
                "help",
                f"MAKE_COMMAND={entry.relative_to(project)}",
            ]
        process = tm.ok(
            u.Tests.run_isolated_make(arguments, cwd=project),
        )
        if scenario == "link-cycle":
            tm.that(process.outcome.raw_return_code, eq=2)
            tm.that(process.stderr, has="physical file link cycle")
            tm.that(process.stdout, lacks="physical-invoker=")
        else:
            tm.that(
                process.outcome.raw_return_code,
                eq=0,
                msg=process.stdout + process.stderr,
            )
            tm.that(process.stdout, has=f"physical-invoker={binary}\n")
        tm.that(entry.readlink(), eq=Path(target.name))
        tm.that(
            target.readlink(),
            eq=Path(entry.name) if scenario == "link-cycle" else binary,
        )

    @pytest.mark.parametrize("verb", ["setup", "upg"])
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("broken", [False, True])
    def test_borrowed_environment_blocks_bootstrap_before_effects(
        self,
        tmp_path: Path,
        verb: str,
        profile: c.Infra.MakeProfile,
        *,
        broken: bool,
    ) -> None:
        """Public provisioning rejects borrowed runtimes before bootstrap or hooks."""
        project, _ = u.Tests.render_make_environment(tmp_path, profile)
        environment = u.Infra.runtime_environment_dir(project)
        foreign = tmp_path / "foreign"
        if not broken:
            foreign.mkdir()
            (foreign / "owner.txt").write_bytes(b"foreign-owned bytes")
        environment.symlink_to(foreign, target_is_directory=True)
        (project / "custom.mk").write_text(
            "pre-setup pre-upg post-setup post-upg:\n\t@touch hook-effect\n",
            encoding=c.DEFAULT_ENCODING,
        )
        paths = set(project.rglob("*"))
        contents = {path: path.read_bytes() for path in paths if path.is_file()}
        process = tm.ok(u.Tests.run_isolated_make([verb], cwd=project))
        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has=f"physical, not a symlink: {environment}")
        tm.that(process.stdout, lacks="github-auth")
        tm.that(set(project.rglob("*")), eq=paths)
        for path, content in contents.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(environment.is_symlink(), eq=True)
        tm.that(foreign.exists(), eq=not broken)
        if not broken:
            tm.that(tuple(foreign.iterdir()), eq=(foreign / "owner.txt",))
            tm.that((foreign / "owner.txt").read_bytes(), eq=b"foreign-owned bytes")
