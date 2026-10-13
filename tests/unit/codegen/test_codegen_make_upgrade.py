"""Generated Make upgrade lifecycle and lock ownership contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import config, r
from tests import c, m, t, tm, u


class TestsFlextInfraCodegenMakeUpgrade:
    """Prove only ``upg`` resolves locks and setup preserves native lock inputs."""

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
        tm.that(admitted < installed < validated, eq=True)
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
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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

        tm.that(u.Cli.process_succeeded(provisioned.outcome), eq=False)
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
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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

        tm.that(u.Cli.process_succeeded(upgraded.outcome), eq=False)
        tm.that(bool(upgraded.stderr.strip()), eq=True)
        tm.that(lock.read_bytes(), eq=previous_lock)

    @staticmethod
    def _recipe_targets_containing(
        makefile: str,
        needle: str,
        *,
        regex: bool = False,
    ) -> set[str]:
        """Return every rule target whose recipe (not comments) carries *needle*.

        Returns:
            Every rule target whose recipe (not comments) carries *needle*.

        """
        targets: set[str] = set()
        current: str | None = None
        continued = False
        for line in makefile.splitlines():
            if line.startswith("\t") or continued:
                if (
                    current is not None
                    and not line.lstrip().startswith("#")
                    and (
                        re.search(needle, line) is not None if regex else needle in line
                    )
                ):
                    targets.add(current)
                continued = line.endswith("\\")
                continue
            continued = False
            # Make conditionals (ifeq/ifneq/ifdef/else/endif) sit inside a
            # recipe without ending it.
            if re.match(r"^(?:ifeq|ifneq|ifdef|ifndef|else|endif)\b", line):
                continue
            header = re.match(r"^([A-Za-z0-9_.$()%-]+)\s*:(?![=:])", line)
            current = header.group(1) if header else None
        return targets

    @staticmethod
    def _upg_steps(makefile: str) -> t.StrSequence:
        """Return the upgrade recipe lines: the lifecycle, then its convergence.

        Returns:
            The ``_upg_lifecycle`` lines followed by the ``_upg_converge`` lines.

        """
        lifecycle = makefile.split("_upg_lifecycle: _builtin_setup_submodules\n", 1)[1]
        converge = makefile.split("\n_upg_converge:\n", 1)[1]
        return [
            *lifecycle.split("\n\n", 1)[0].splitlines(),
            *converge.split("\n\n", 1)[0].splitlines(),
        ]

    @staticmethod
    def _assert_setup_recipe(
        makefile: str,
        profile: c.Infra.MakeProfile,
        sync_flags_value: str,
    ) -> None:
        """Assert the setup recipe verifies the committed lock and never relocks."""
        setup_recipe = makefile.split("INSTALL_RUNTIME_RECIPE = ", 1)[1].split(
            "\n\n",
            1,
        )[0]
        # Setup uses $(UV) sync --frozen to install from committed lock
        tm.that(re.findall(r"\$\(UV\) sync\b", setup_recipe), eq=["$(UV) sync"])
        tm.that(
            setup_recipe,
            has=[
                "--frozen",
                "ERROR[setup]",
                "make upg",
            ],
        )
        admission = "codegen mise-artifacts"
        tm.that(setup_recipe.count(admission), eq=1)
        tm.that(
            setup_recipe,
            has=[
                '--repository-root "$(PROJECT_ROOT)" --config-only',
            ],
        )
        # Single mise-artifacts call with --scope all handles root + members
        tm.that(
            setup_recipe,
            lacks=[
                "WARNING[setup]",
                "--requirements",
                'rm -f "$(UV_PROJECT)/uv.lock"',
                ">/dev/null",
            ],
        )
        tm.that(
            "--all-packages" in sync_flags_value,
            eq=profile is c.Infra.MakeProfile.WORKSPACE,
        )

    def test_upg_is_the_only_resolver_and_setup_requires_matching_lock(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """Operator law 2026-09-24: only `upg` resolves and writes the locks.

        The generated Makefile confines every uv upgrade to the `upg`
        lifecycle and every `mise lock --bump` to that lifecycle or its shared
        bootstrap gated by a switch that only `upg` sets. `setup` installs
        what the committed locks pin (`--locked`, `install --locked`) and
        rejects a stale UV lock before synchronization.
        """
        profile, project_root = generated_make_template
        makefile = (project_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8",
        )

        tm.that(
            self._recipe_targets_containing(
                makefile,
                r"\$\(UV\)\s+lock\b[^\n]*--upgrade\b",
                regex=True,
            ),
            eq={"_upg_lifecycle"},
        )
        tm.that(
            self._recipe_targets_containing(
                makefile,
                # The bootstrap runs the pinned binary it recovered
                # ($$mise_bootstrap_bin); the lifecycle runs the mise shim.
                r"(?:\bmise\b|\$\$mise_bootstrap_bin\b)[^\n]*\block\b[^\n]*--bump\b",
                regex=True,
            ),
            eq={"_bootstrap_setup_tools", "_upg_lifecycle", "_upg_converge"},
        )
        toolchain = config.Infra.codegen.toolchain
        # Setup never locks (operator 2026-10-02): no reconcile or relock path
        # survives, and a lock that no longer satisfies the manifest stops.
        tm.that(
            makefile,
            lacks=[
                "setup reconcile",
                ' reconcile "$$project_root"',
                'relock "$(PROJECT_ROOT)"',
            ],
        )
        # Every install names only the declared keys and keeps the committed
        # lock authoritative; no host tool list or unlocked install survives.
        declared = " ".join(f'"{key}"' for key in toolchain.mise_install_keys)
        installs = re.findall(
            r"install --locked --yes(.*?)(?:; \\|$)", makefile, re.MULTILINE
        )
        tm.that(
            {install.strip() for install in installs},
            eq={declared},
        )
        tm.that(
            makefile,
            lacks=["MISE_LOCKFILE=false", "$$mise_without_lock", "$$mise_from_lock"],
        )
        # Setup provisions; audit owns the toolchain lock verdict.
        audit = makefile.split("_builtin-audit:\n", 1)[1].split("\n_builtin-", 1)[0]
        tm.that(
            audit,
            has=[
                "$(UV) pip check",
                "workspace verify-environment",
                "codegen mise-proof",
            ],
        )
        tm.that(
            makefile,
            has='if [ "$(TOOL_BOOTSTRAP_RESOLVE)" = "1" ] && [ "$$mise_resolved" = "0" '
            "]; then",
        )
        resolve_assignments = re.findall(
            r"^(?:([\w-]+): )?TOOL_BOOTSTRAP_RESOLVE :=[ ]?(.*)$",
            makefile,
            flags=re.MULTILINE,
        )
        tm.that(sorted(resolve_assignments), eq=[("", ""), ("upg", "1")])
        tm.that(makefile, has="upg: TOOL_BOOTSTRAP_LIFECYCLE := _upg_lifecycle")
        sync_flags = re.search(r"^UV_SYNC_FLAGS := (.*)$", makefile, re.MULTILINE)
        assert sync_flags is not None
        tm.that(sync_flags.group(1), lacks="--upgrade")
        # Setup verifies the committed lock before any dependency sync;
        # only upg may resolve or write it.
        self._assert_setup_recipe(makefile, profile, sync_flags.group(1))
        tm.that(
            makefile, has="override UV_SYNC_FLAGS := $(UV_SYNC_FLAGS) --no-editable"
        )

        mise_toml = u.Cli.toml_mapping_from_text(
            (project_root / c.Infra.MISE_TOML_FILENAME).read_text(encoding="utf-8"),
        )
        assert mise_toml is not None
        settings = mise_toml.get("settings")
        assert isinstance(settings, Mapping)
        tm.that(settings.get("lockfile"), eq=toolchain.mise_lockfile)
        tm.that(
            settings.get("disable_update_warning"),
            eq=toolchain.mise_disable_update_warning,
        )
        tm.that(dict(settings), lacks="locked")
        tm.that(dict(mise_toml), lacks="tool_config")
        tm.that(
            settings.get("lockfile_platforms"),
            eq=list(toolchain.mise_lockfile_platforms),
        )

    def test_generated_dependency_upgrade_projects_lock_floors(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """`upg` owns lock upgrade, open-floor projection, and final resolution."""
        _profile, project_root = generated_make_template
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        for needle in (
            "deps modernize",
            "--rewrite-constraints",
            "--upgrade --refresh",
        ):
            tm.that(
                self._recipe_targets_containing(makefile, needle),
                eq={"_upg_lifecycle"},
            )
        tm.that(
            self._recipe_targets_containing(
                makefile,
                '$(UV) lock --check --project "$$project"',
            ),
            eq={"_upg_reconcile_locks"},
        )
        tm.that(makefile, lacks="--constraint-policy")

    def test_upg_relocks_the_manifest_gen_projected_before_installing(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """One `make upg` resolves the requirements its own `gen` projects.

        Premise (flext-5kqsx): the upgraded generator projected a declared
        runtime dependency into pyproject.toml after uv.lock was written, so
        the lock and the environment lacked it until a second `make upg`.
        """
        _profile, project_root = generated_make_template
        makefile = (project_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8",
        )
        steps = self._upg_steps(makefile)

        def after(start: int, needle: str) -> int:
            return next(
                index
                for index, step in enumerate(steps)
                if index > start and needle in step
            )

        upgraded = after(-1, "lock --project")
        bumped = after(upgraded, "lock --bump")
        projected = after(bumped, "$(call RUN_PUBLIC_PRODUCE,gen)")
        relocked = after(projected, "_upg_reconcile_locks")
        installed = after(relocked, "_builtin_setup_environment")
        activated = after(installed, "$(call RUN_PUBLIC_ACTIVATE,gen)")

        tm.that(steps[upgraded], has="--upgrade")
        tm.that(steps[relocked], lacks="--upgrade")
        tm.that(
            upgraded < bumped < projected < relocked < installed,
            eq=True,
        )
        tm.that(installed < activated, eq=True)

    @pytest.mark.parametrize(
        "generated_make_template",
        [c.Infra.MakeProfile.WORKSPACE],
        indirect=True,
    )
    def test_upg_converge_verifies_the_cycle_it_upgraded(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """An upgrade publishes after gen converges; gates stay with make check."""
        _profile, project_root = generated_make_template
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        tm.that(
            self._recipe_targets_containing(
                makefile,
                'codegen conform --root "$(PROJECT_ROOT)" --mode check',
            ),
            empty=True,
        )
        tm.that(
            {"_upg_lifecycle", "_upg_converge"}
            & self._recipe_targets_containing(makefile, "$(SELF_MAKE) check"),
            empty=True,
        )

    def test_upg_activates_gen_only_after_relocking_the_rendered_manifest(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """One `make upg` converges when the generator moves the Mise self-pin.

        The upgraded generator's `.mise.toml` is rendered, locked
        (`mise lock --bump`) and installed before any stage that resolves a
        managed tool (deps modernize, the gen producer and activation), so a
        consumer generated by an earlier generator, whose lock has no self pin
        yet, converges in one run (C19). No stage authenticates the Mise
        reader against the lock: that verdict lives in `audit`.
        """
        _profile, project_root = generated_make_template
        makefile = (project_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8",
        )
        steps = self._upg_steps(makefile)
        order = [
            next(i for i, step in enumerate(steps) if needle in step)
            for needle in (
                "--what mise-config --scope self --mode apply",
                "lock --bump",
                "install --locked --yes",
                "deps modernize",
                "$(call RUN_PUBLIC_PRODUCE,gen)",
                "$(call RUN_PUBLIC_ACTIVATE,gen)",
                "$(SELF_MAKE) gen",
                "deps verify-locks",
            )
        ]
        tm.that(order, eq=sorted(set(order)))
        # The upgrade writes files; staging belongs to the committer. No
        # generated recipe touches the Git index (a directory-scoped add would
        # also stage deletions of retired lock sidecars).
        tm.that(self._recipe_targets_containing(makefile, "git add"), eq=set[str]())
        tm.that(makefile, has="_activated-gen: _builtin_require_environment")
        tm.that(
            makefile,
            has="_builtin_require_environment: _builtin_require_interpreter\n",
        )

        # GNU Make itself expands the canned halves: the producer half never
        # re-enters the environment, the activation half does, and the public
        # verb is exactly the producer half followed by the activation half.
        probe = (
            "probe_upg_halves: ; @: "
            "$(info PRODUCE=$(strip $(call RUN_PUBLIC_PRODUCE,gen))) "
            "$(info ACTIVATE=$(strip $(call RUN_PUBLIC_ACTIVATE,gen))) "
            "$(info PUBLIC=$(strip $(call RUN_PUBLIC,gen,1)))"
        )
        expanded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", f"--eval={probe}", "probe_upg_halves"],
                cwd=project_root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(expanded.outcome),
            eq=True,
            msg=expanded.stdout + expanded.stderr,
        )
        halves = {
            name: value
            for name, _, value in (
                line.partition("=") for line in expanded.stdout.splitlines()
            )
            if name in {"PRODUCE", "ACTIVATE", "PUBLIC"}
        }
        tm.that(halves["PRODUCE"], has="_builtin-gen")
        tm.that(halves["PRODUCE"], lacks="_activated-gen")
        tm.that(halves["ACTIVATE"], has=["direnv exec", "_activated-gen"])
        tm.that(
            halves["PUBLIC"].split(),
            eq=[*halves["PRODUCE"].split(), *halves["ACTIVATE"].split()],
        )

    def test_setup_holds_no_lock_verdict_and_audit_owns_it(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """Setup provisions and ends green; ``audit`` judges the locks.

        Premise (operator-ruling-2026-10-09-setup-resilient): an invalid or
        stale lock never aborts installation or execution. No setup stage
        checks a lock or prints a lock verdict, in any context; ``audit``,
        which CI runs right after setup, ends RED with the ``make upg`` cure.
        """
        _profile, project_root = generated_make_template
        makefile = (project_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8",
        )
        tm.that(
            self._recipe_targets_containing(
                makefile,
                r"\$\(UV\) lock --check\b",
                regex=True,
            ),
            eq={"_upg_reconcile_locks"},
        )
        tm.that(
            self._recipe_targets_containing(makefile, "codegen mise-proof"),
            eq={"_builtin-audit"},
        )
        tm.that(makefile, lacks=["_builtin_setup_lock_verdict"])
        audit = makefile.split("_builtin-audit:\n", 1)[1].split("\n_builtin-", 1)[0]
        tm.that(
            audit,
            has=[
                "$(UV) pip check",
                "workspace verify-environment",
            ],
        )

    @pytest.mark.parametrize(
        "generated_make_template",
        [c.Infra.MakeProfile.STANDALONE],
        indirect=True,
    )
    @pytest.mark.remote
    @pytest.mark.slow
    def test_native_shared_workspace_guard_stops_before_uv_lock(
        self,
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
            ignore=shutil.ignore_patterns(".venv", ".git"),
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

        tm.that(u.Cli.process_succeeded(upgraded.outcome), eq=False)
        tm.that(upgraded.stderr, has=["ERROR[upg]", str(workspace.resolve())])
        tm.that(
            member_lock.read_bytes() if member_lock.is_file() else None,
            eq=previous,
        )
        tm.that(workspace_lock.exists(), eq=False)

    @pytest.mark.remote
    @pytest.mark.slow
    def test_failed_member_hook_prevents_containing_root_upgrade(
        self,
        tmp_path: Path,
        generated_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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
                ignore=shutil.ignore_patterns(".venv", ".git"),
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
        tm.that(u.Cli.process_succeeded(upgraded.outcome), eq=False)
        tm.that(upgraded.stderr, has="member pre-upg failed")
        tm.that(marker.is_file(), eq=False)
        tm.that(
            root_lock.read_bytes() if root_lock.is_file() else None,
            eq=previous,
        )

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_member_upgrade_reconciles_runtime_before_failing_hook(
        tmp_path: Path,
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
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
                "true",
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
            'project = tomllib.loads(Path("pyproject.toml").read_text())["project"]; '
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
        tm.that((root / "root-upgrade-started").exists(), eq=True)
        tm.that((checkout / ".venv").exists(), eq=False)
