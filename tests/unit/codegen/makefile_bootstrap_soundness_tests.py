"""Soundness contracts for the rendered Makefile bootstrap recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config, settings, workspace
from tests import c, m, t, tm, u
from tests.unit.codegen import test_mise_pin_bootstrap


class TestsFlextInfraMakefileBootstrapSoundness:
    """Public Make preserves physical ownership and native tool configuration."""

    @staticmethod
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("supplier", [False, True])
    def test_install_recipe_survives_template_conditionals(
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
        editable_supplier: Callable[[Path | None], None],
        *,
        supplier: bool,
    ) -> None:
        """Public help parses both branches without truncating provisioning."""
        root, _ = u.Tests.render_make_environment(tmp_path, profile)
        if supplier:
            supplier_root = tmp_path / "supplier"
            supplier_root.mkdir()
            editable_supplier(supplier_root)
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        policy = inputs.spec.make.uv_resolution
        tm.that(settings.Infra.editable_supplier_root is not None, eq=supplier)
        spec = tm.ok(workspace.FlextInfraWorkspaceDetector.load_workspace_spec(root))
        rendered = u.Tests.conform_makefile_text(root, spec)
        tm.ok(u.Cli.atomic_write_text_file(root / c.Infra.MAKEFILE_FILENAME, rendered))
        (root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            "$(info install-runtime-recipe=$(value INSTALL_RUNTIME_RECIPE))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["help", "OPTIONS=Y"],
                cwd=root,
                env={
                    type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT: (
                        str(settings.Infra.editable_supplier_root) if supplier else ""
                    ),
                    policy.hosted_variable: "",
                    inputs.spec.make.ci.variable: inputs.spec.make.ci.local_value,
                },
            )
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        recipe = next(
            line
            for line in process.stdout.splitlines()
            if line.startswith("install-runtime-recipe=")
        )
        sync = '$$credential_env $(UV) sync --project "$(UV_PROJECT)"'
        tm.that(recipe, has=sync)
        tm.that(
            recipe,
            has='$(UV_SYNC_FLAGS) --frozen --link-mode "$(UV_LINK_MODE)"',
        )
        tm.ok(recipe.index("config ls --json") < recipe.index(sync))
        tm.that(recipe, has="$(UV) lock --check")
        tm.ok(recipe.index("$(UV) lock --check") < recipe.index(sync))
        tm.that(rendered, lacks=str(tmp_path / "supplier"))
        for verb in ("fmt", "fix"):
            body = rendered.split(
                f"_builtin_{verb}_all: _builtin_require_environment\n", 1
            )[1].split("\n\n", 1)[0]
            for gates in (
                inputs.spec.make.check_gates_default,
                inputs.spec.make.check_gates_ci,
                inputs.spec.make.check_gates_local,
            ):
                tm.that(body, has=f'gates="{",".join(gates)}"')
            capture = body.index('capture-gate --repository-root "$(PROJECT_ROOT)"')
            conform = body.index(
                'codegen conform --root "$(PROJECT_ROOT)" --scope self --mode check'
            )
            tm.ok(body.index("--apply") < capture < conform)
            tm.that(body[capture:conform], has='--gates "$$gates"')
            tm.that(body[capture:], lacks="--apply")

    @staticmethod
    @pytest.mark.parametrize("scenario", ["hosted", "missing-manifest"])
    def test_editable_upgrade_preflight_preserves_hooks_and_locks(
        tmp_path: Path,
        scenario: str,
        editable_supplier: Callable[[Path | None], None],
    ) -> None:
        """A selected dev supplier never changes hosted provisioning policy."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
        )
        spec = tm.ok(workspace.FlextInfraWorkspaceDetector.load_workspace_spec(root))
        supplier_root = tmp_path / "supplier"
        supplier_root.mkdir()
        editable_supplier(supplier_root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.MAKEFILE_FILENAME,
                u.Tests.conform_makefile_text(root, spec),
            )
        )
        marker = root / "pre-upg-ran"
        (root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            f".PHONY: pre-upg\npre-upg:\n\t@touch {quote(str(marker))}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec.make.uv_resolution
        paths = (
            root / c.Infra.UV_LOCK_FILENAME,
            root / c.Infra.MISE_LOCK_FILENAME,
            *(
                root / directory / c.Infra.UV_LOCK_FILENAME
                for directory in (
                    policy.local_directory,
                    policy.standalone_directory,
                    policy.editable_directory,
                )
            ),
        )
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in paths
        )
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["upg"],
                cwd=root,
                env={
                    type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT: str(
                        supplier_root
                    ),
                    policy.hosted_variable: policy.hosted_value
                    if scenario == "hosted"
                    else "",
                },
            )
        )
        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(
            process.stderr,
            has=(
                "Resolution and member propagation are forbidden in hosted CI"
                if scenario == "hosted"
                else "selected supplier has no native bootstrap lock"
            ),
        )
        tm.fail(marker.exists())
        tm.fail((root / c.Infra.ENVIRONMENT_DIRECTORY).exists())
        tm.that(
            tuple(tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in paths),
            eq=before,
        )

    @staticmethod
    def test_member_supplier_uses_the_physical_workspace_resolution(
        tmp_path: Path,
        editable_supplier: Callable[[Path | None], None],
    ) -> None:
        """The process setting selects only the physical owner's dev lock."""
        root, member, _, _ = (
            TestsFlextInfraMakefileBootstrapSoundness._reader_workspace_checkout(
                tmp_path,
                associated=True,
            )
        )
        u.Tests.initialize_git_repo(
            member,
            origin_url=u.Tests.WorktreeFixture.governed_repository_url(member.name),
        )
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution=member.name,
            relative_path=member.relative_to(root).as_posix(),
        )
        u.Tests.git_run(root, "submodule", "absorbgitdirs")
        spec = tm.ok(workspace.FlextInfraWorkspaceDetector.load_workspace_spec(member))
        supplier_root = tmp_path / "supplier"
        supplier_root.mkdir()
        editable_supplier(supplier_root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                member / c.Infra.MAKEFILE_FILENAME,
                u.Tests.conform_makefile_text(member, spec),
            )
        )
        policy = config.Infra.codegen.make.uv_resolution
        paths = tuple(
            root / directory / c.Infra.UV_LOCK_FILENAME
            for directory in (
                Path(),
                policy.local_directory,
                policy.standalone_directory,
            )
        )
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in paths
        )
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["upg"],
                cwd=member,
                env={
                    policy.hosted_variable: "",
                    type(settings.Infra).EDITABLE_SUPPLIER_ENVIRONMENT: str(
                        supplier_root
                    ),
                },
            )
        )
        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has="selected supplier has no native bootstrap lock")
        tm.that(
            tuple(tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in paths),
            eq=before,
        )

    @staticmethod
    def _reader_workspace_checkout(
        tmp_path: Path,
        *,
        associated: bool,
    ) -> tuple[Path, Path, Path, Path]:
        """Render a workspace root with one member copied from a standalone seed.

        Args:
            tmp_path: Test-scoped scratch root.
            associated: Whether the member joins the workspace instead of
                being excluded from it.

        Returns:
            The workspace root, the member checkout, the elected runtime
            owner, and the member environment directory.

        """
        root, _ = u.Tests.render_make_environment(
            tmp_path / "container",
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="reader-owner"),
        )
        seed, _ = u.Tests.render_make_environment(
            tmp_path / "seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="reader-member"),
        )
        member = root / "packages" / seed.name
        shutil.copytree(
            seed,
            member,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", c.Infra.ENVIRONMENT_DIRECTORY),
        )
        relative = member.relative_to(root).as_posix()
        document = u.Tests.toml_doc(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
        )
        tool = u.Cli.toml_ensure_table(document, "tool")
        uv = u.Cli.toml_ensure_table(tool, "uv")
        uv["workspace"] = (
            {"members": [relative]}
            if associated
            else {"members": [], "exclude": [relative]}
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.PYPROJECT_FILENAME,
                u.Cli.toml_dumps(document),
            ),
        )
        elected = root if associated else member
        return root, member, elected, elected / c.Infra.ENVIRONMENT_DIRECTORY

    @pytest.mark.slow
    @pytest.mark.parametrize("verb", ["setup", "upg"])
    @pytest.mark.parametrize("associated", [False, True])
    def test_cold_reader_elects_before_runtime_admission_without_resolving_locks(
        self,
        tmp_path: Path,
        verb: str,
        *,
        associated: bool,
    ) -> None:
        """Frozen UV establishes membership before the real environment guard."""
        root, member, elected, environment = self._reader_workspace_checkout(
            tmp_path,
            associated=associated,
        )
        foreign = tmp_path / "foreign-environment"
        foreign.mkdir()
        environment = elected / c.Infra.ENVIRONMENT_DIRECTORY
        environment.symlink_to(foreign, target_is_directory=True)
        (member / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            "$(info reader-elected-root=$(RUNTIME_ROOT))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        isolation = tmp_path / "native-tools"
        (isolation / "home").mkdir(parents=True)
        native_env = (
            test_mise_pin_bootstrap.TestsFlextInfraMisePinBootstrap.environment(
                isolation
            )
        )
        for project in (root, member):
            tm.ok(
                u.Cli.run_checked(
                    ["mise", "trust", str(project / c.Infra.MISE_TOML_FILENAME)],
                    options=m.Cli.ProcessOptions(env=native_env),
                ),
            )
        policy = config.Infra.codegen.make.uv_resolution
        lock_paths = tuple(
            project / relative
            for project in (root, member)
            for relative in (
                Path(c.Infra.MISE_LOCK_FILENAME),
                Path(c.Infra.UV_LOCK_FILENAME),
                policy.local_directory / c.Infra.UV_LOCK_FILENAME,
                policy.standalone_directory / c.Infra.UV_LOCK_FILENAME,
            )
        )
        locks = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in lock_paths
        )
        system_tools = (
            test_mise_pin_bootstrap.TestsFlextInfraMisePinBootstrap
        ).system_path_without_mise(isolation)
        optional_credential_provider = system_tools / "gh"
        if optional_credential_provider.is_symlink():
            optional_credential_provider.unlink()
        tm.that(shutil.which("gh", path=str(system_tools)), eq=None)
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["-f", str(member / c.Infra.MAKEFILE_FILENAME), verb],
                cwd=root,
                env={
                    **native_env,
                    "PATH": str(system_tools),
                    policy.hosted_variable: "",
                    config.Infra.codegen.make.ci.variable: (
                        config.Infra.codegen.make.ci.local_value
                    ),
                },
            ),
        )

        tm.that(
            process.outcome.raw_return_code,
            eq=2,
            msg=process.stdout + process.stderr,
        )
        tm.that(
            process.stderr,
            has="github-auth source=none extraction-exit=not-selected",
            msg=process.stdout + process.stderr,
        )
        tm.that(
            process.stdout,
            has=f"reader-elected-root={elected.resolve()}\n",
            msg=process.stdout + process.stderr,
        )
        tm.that(
            process.stderr,
            has=f"physical, not a symlink: {environment}",
            msg=process.stdout + process.stderr,
        )
        tm.that(
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in lock_paths
            ),
            eq=locks,
        )
        tm.ok(environment.is_symlink())
        tm.that(tuple(foreign.iterdir()), eq=())
        reader = tm.ok(
            u.Cli.capture(
                ["mise", "-C", str(root), "which", c.Infra.UV],
                options=m.Cli.ProcessOptions(env=native_env),
            ),
        )
        tm.ok(Path(reader).is_relative_to(isolation))

    @pytest.mark.parametrize(
        "entry",
        ["spaced", "symlink", "outside-spaced", "outside-symlink"],
    )
    @staticmethod
    def test_public_make_paths_keep_the_physical_runtime_owner(
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
                    (
                        "from pathlib import Path; import sys; "
                        "from flext_infra.workspace import "
                        "FlextInfraWorkspaceDetector; "
                        "context=FlextInfraWorkspaceDetector.resolution_context("
                        "Path(sys.argv[1])).unwrap(); print(context.model_dump_json())"
                    ),
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
            u.Cli.process_succeeded(observed.outcome),
            eq=True,
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
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"physical-runtime-root={physical}\n")
        tm.that(
            process.stdout,
            has=f"physical-runtime-environment={environment}\n",
        )
        tm.that(process.stdout, has=f"physical-runtime-resolution={resolution}\n")
        tm.fail(environment.exists())
        tm.fail((caller / c.Infra.ENVIRONMENT_DIRECTORY).exists())
        tm.fail((caller / c.Infra.UV_LOCK_FILENAME).exists())

    @staticmethod
    def _provisioned_native_venv(
        binary: Path,
        environment: Path,
        native_options: m.Cli.ProcessOptions,
    ) -> None:
        """Create a real native virtual environment with the managed binary.

        Args:
            binary: Managed mise binary used to create the environment.
            environment: Environment directory to provision.
            native_options: Isolation options for the native invocation.

        """
        created = tm.ok(
            u.Cli.run_raw(
                [str(binary), "venv", "--python", sys.executable, str(environment)],
                cwd=environment.parent,
                options=native_options,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(created.outcome),
            eq=True,
            msg=created.stdout + created.stderr,
        )

    @staticmethod
    def _runtime_context_probe(
        project: Path,
        env: t.StrMapping,
        *,
        cwd: Path,
    ) -> m.Infra.WorkspaceRuntimeContext:
        """Probe the native runtime context of one submitted project path.

        Args:
            project: Checkout whose resolution context is observed.
            env: Environment variables applied to the native invocation.
            cwd: Working directory of the native invocation.

        Returns:
            The validated runtime context reported by the detector.

        """
        observed = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "from pathlib import Path; import sys; "
                        "from flext_infra.workspace import "
                        "FlextInfraWorkspaceDetector; "
                        "context=FlextInfraWorkspaceDetector.resolution_context("
                        "Path(sys.argv[1])).unwrap(); print(context.model_dump_json())"
                    ),
                    str(project),
                ),
                cwd=cwd,
                options=m.Cli.ProcessOptions(
                    env=env,
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(observed.outcome),
            eq=True,
            msg=observed.stdout + observed.stderr,
        )
        return m.Infra.WorkspaceRuntimeContext.model_validate_json(observed.stdout)

    @pytest.mark.parametrize("invocation", ["root", "member"])
    @pytest.mark.parametrize("excluded", [False, True])
    @pytest.mark.parametrize("hosted", [False, True])
    def test_hosted_runtime_is_independent_of_local_ci_partition(
        self,
        tmp_path: Path,
        invocation: str,
        *,
        excluded: bool,
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
            tmp_path / "hosted-member-seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="hosted-owner-member"),
        )
        member = member.rename(root / member.name)
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution=member.name,
            relative_path=member.relative_to(root).as_posix(),
        )
        u.Tests.git_run(root, "submodule", "absorbgitdirs")
        if excluded:
            document = u.Tests.toml_doc(
                (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            )
            u.Cli.toml_ensure_table(u.Cli.toml_ensure_table(document, "tool"), "uv")[
                "workspace"
            ] = {
                "members": [],
                "exclude": [member.relative_to(root).as_posix()],
            }
            tm.ok(
                u.Cli.atomic_write_text_file(
                    root / c.PYPROJECT_FILENAME,
                    u.Cli.toml_dumps(document),
                ),
            )
        environment = root / c.Infra.ENVIRONMENT_DIRECTORY
        self._provisioned_native_venv(
            tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root)),
            environment,
            m.Cli.ProcessOptions(remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS),
        )
        tm.fail(environment.is_symlink())
        tm.ok((environment / "pyvenv.cfg").is_file())
        member_environment = member / c.Infra.ENVIRONMENT_DIRECTORY
        tm.fail(member_environment.exists())
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
        context = self._runtime_context_probe(project, context_env, cwd=project)
        u.Cli.emit_raw(
            f"native context runtime={context.runtime_root} "
            f"environment={context.environment_path} "
            f"resolution={context.resolution_root} hosted={context.standalone}\n",
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
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
        tm.fail(member_environment.exists())

    @staticmethod
    def test_python_project_without_python_ancestor_owns_its_runtime(
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
            u.Cli.process_succeeded(provisioned.outcome),
            eq=True,
            msg=provisioned.stdout + provisioned.stderr,
        )
        tm.fail(environment.is_symlink())
        tm.ok((environment / "pyvenv.cfg").is_file())
        (project / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            "\t@printf 'independent-root=%s\\n' '$(RUNTIME_ROOT)'\n"
            "\t@printf 'independent-environment=%s\\n' '$(RUNTIME_VENV)'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"independent-root={project.resolve()}\n")
        tm.that(
            process.stdout,
            has=f"independent-environment={environment.resolve()}\n",
        )
        context = tm.ok(
            workspace.FlextInfraWorkspaceDetector.resolution_context(project)
        )
        tm.that(context.runtime_root, eq=project.resolve())
        tm.that(context.environment_path, eq=environment.resolve())
        for path in (
            container / c.PYPROJECT_FILENAME,
            container / c.Infra.MISE_TOML_FILENAME,
            container / c.Infra.MISE_LOCK_FILENAME,
            container / c.Infra.ENVIRONMENT_DIRECTORY,
        ):
            tm.fail(path.exists())

    @staticmethod
    def test_dangling_git_marker_rejects_ancestor_discovery(
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
            ".PHONY: post-help\npost-help:\n\t@printf '%s\\n' 'nested-help-executed'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        baseline = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.that(
            u.Cli.process_succeeded(baseline.outcome),
            eq=True,
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
        tm.ok(native_error.outcome.raw_return_code != 0)
        tm.ok(bool(native_error.stderr.strip()))
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=project))
        tm.ok(process.outcome.raw_return_code != 0)
        tm.that(process.stderr, has=native_error.stderr.strip())
        tm.that(process.stdout, lacks="nested-help-executed")
        context = workspace.FlextInfraWorkspaceDetector.resolution_context(project)
        tm.ok(context.failure)
        tm.ok(marker.is_symlink())
        tm.fail(marker.exists())
        tm.fail((project / c.Infra.ENVIRONMENT_DIRECTORY).exists())

    @pytest.mark.parametrize("associated_clone", [False, True])
    @staticmethod
    def _native_owner_workspace_checkout(
        tmp_path: Path,
        *,
        associated_clone: bool,
    ) -> tuple[Path, Path]:
        """Copy a standalone seed member into a fresh workspace root.

        Args:
            tmp_path: Test-scoped scratch root.
            associated_clone: Whether the member gets its own Git origin.

        Returns:
            The workspace root and the member checkout.

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
        return root, member

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
        root, member = self._native_owner_workspace_checkout(
            tmp_path,
            associated_clone=associated_clone,
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
        tm.fail(environment.is_symlink())
        tm.ok((environment / "pyvenv.cfg").is_file())
        member_environment = member / c.Infra.ENVIRONMENT_DIRECTORY
        tm.fail(member_environment.exists())
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
            (project / c.PYPROJECT_FILENAME).read_bytes() for project in (root, member)
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
        tm.fail(member_environment.exists())
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

    @staticmethod
    def test_public_make_preserves_native_project_mise_lock_scope(
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
        tm.fail((project / ".mise" / "config.toml").exists())
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
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        native_paths: set[Path] = set()
        for row in u.Cli.json_as_sequence(
            tm.ok(
                u.Cli.json_loads(config_report.read_text(encoding=c.DEFAULT_ENCODING))
            ),
        ):
            path = u.Cli.json_as_mapping(row)["path"]
            tm.that(path, is_=str)
            if isinstance(path, str):
                native_paths.add(Path(path).resolve())
        tm.ok(project / c.Infra.MISE_TOML_FILENAME in native_paths)
        tm.fail(global_config in native_paths)
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
    @staticmethod
    def test_public_make_authenticates_file_aliases_without_replacing_the_invoker(
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
                u.Cli.process_succeeded(process.outcome),
                eq=True,
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
    @staticmethod
    def test_borrowed_environment_blocks_bootstrap_before_effects(
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
        tm.ok(environment.is_symlink())
        tm.that(foreign.exists(), eq=not broken)
        if not broken:
            tm.that(tuple(foreign.iterdir()), eq=(foreign / "owner.txt",))
            tm.that((foreign / "owner.txt").read_bytes(), eq=b"foreign-owned bytes")
