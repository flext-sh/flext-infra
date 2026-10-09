"""Generated Make upgrade lifecycle and lock ownership contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Mapping
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config
from tests import c, t, u


class TestsFlextInfraCodegenMakeUpgrade:
    """Prove only ``upg`` resolves locks and setup preserves native lock inputs."""

    @staticmethod
    @pytest.mark.remote
    @pytest.mark.slow
    def test_setup_preserves_the_resolved_native_locks(
        tmp_path: Path,
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
    ) -> None:
        """Provision the real fixture without replacing its native lock payloads."""
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
                ["--no-print-directory", "setup"],
                cwd=project_root,
            ),
        )

        tm.that(
            u.Cli.process_succeeded(provisioned.outcome),
            eq=True,
            msg=provisioned.stdout + provisioned.stderr,
        )
        tm.that(tuple(lock.read_bytes() for lock in locks), eq=previous)
        tm.that(
            (u.Infra.runtime_environment_dir(project_root) / "pyvenv.cfg").is_file(),
            eq=True,
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

    def test_upg_is_the_only_resolver_and_setup_installs_frozen(
        self,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """Operator law 2026-09-24: only `upg` resolves and writes the locks.

        The generated Makefile confines every uv upgrade to the `upg`
        lifecycle and every `mise lock --bump` to that lifecycle or its shared
        bootstrap gated by a switch that only `upg` sets. `setup` installs
        what the committed locks pin (`--frozen`, `install --locked`) and
        never stops on a stale lock; `audit` holds the lock verdict.
        """
        _profile, project_root = generated_make_template
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
            eq={"_bootstrap_setup_tools", "_upg_lifecycle"},
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
        # Every `mise install` names only declared toolchain keys: a bare
        # install would also provision the operator's global registry. Setup
        # installs what the lock pins `--locked` and the rest unlocked, so an
        # incomplete or stale lock never stops it
        # (operator-ruling-2026-10-09-setup-resilient).
        declared = " ".join(f'"{key}"' for key in toolchain.mise_install_keys)
        tm.that(makefile, has=f"for mise_tool in {declared};")
        installs = re.findall(r"install --yes(.*?)(?:; \\|$)", makefile, re.MULTILINE)
        tm.that(
            {install.strip() for install in installs},
            eq={declared, "$$mise_without_lock"},
        )
        tm.that(makefile, has="install --locked --yes $$mise_from_lock")
        tm.that(
            makefile,
            has='MISE_LOCKFILE=false "$$mise_bootstrap_bin" -C "$(PROJECT_ROOT)" '
            "install --yes $$mise_without_lock",
        )
        # Setup holds no lock verdict: the toolchain proof runs in `audit`,
        # resolving uv through the mise installation (#1887), never PATH.
        activated = makefile.split("_setup_activated:\n", 1)[1].split("\n\n", 1)[0]
        tm.that(activated, lacks="mise-proof")
        audit = makefile.split("_builtin-audit:\n", 1)[1].split("\n_builtin-", 1)[0]
        tm.that(
            audit,
            has=[
                'codegen mise-proof --repository-root "$(PROJECT_ROOT)" '
                '--uv-executable "$$(mise which uv)"',
                '$(UV) lock --check --project "$(UV_PROJECT)"',
                "deps verify-locks",
                "make upg",
            ],
        )
        tm.that(makefile, has='if [ "$(TOOL_BOOTSTRAP_RESOLVE)" = "1" ]; then')
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
        # Setup never resolves, checks or writes uv.lock: a readable lock
        # installs --frozen, an unreadable one provisions straight from the
        # manifest, and nothing deletes or re-derives the committed lock.
        setup_recipe = makefile.split("SETUP_ENVIRONMENT_RECIPE = ", 1)[1].split(
            "\n\n",
            1,
        )[0]
        tm.that(re.findall(r"\$\(UV\) lock\b", setup_recipe), eq=[])
        tm.that(setup_recipe, has=["uv_lock_mode=--frozen", "$$uv_lock_mode"])
        tm.that(
            setup_recipe,
            has='--requirements "$(UV_PROJECT)/pyproject.toml" --all-extras',
        )
        tm.that(
            setup_recipe,
            lacks=[
                "uv_lock_mode=--locked",
                'rm -f "$(UV_PROJECT)/uv.lock"',
                ">/dev/null",
                "make upg",
            ],
        )

        mise_toml = u.Cli.toml_mapping_from_text(
            (project_root / c.Infra.MISE_TOML_FILENAME).read_text(encoding="utf-8"),
        )
        assert mise_toml is not None
        settings = mise_toml.get("settings")
        assert isinstance(settings, Mapping)
        tm.that(settings.get("lockfile"), eq=toolchain.mise_lockfile)
        tm.that(settings.get("disable_update_warning"), eq=True)
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
                '$(UV) lock --check --project "$(PROJECT_ROOT)"',
            ),
            eq={"_upg_lifecycle"},
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
        steps = (
            makefile
            .split("_upg_lifecycle: _builtin_setup_submodules\n", 1)[1]
            .split("\n\n", 1)[0]
            .splitlines()
        )

        def after(start: int, needle: str) -> int:
            return next(
                index
                for index, step in enumerate(steps)
                if index > start and needle in step
            )

        upgraded = after(-1, "lock --project")
        bumped = after(upgraded, "lock --bump")
        projected = after(bumped, "$(call RUN_PUBLIC_PRODUCE,gen)")
        relocked = after(projected, "lock --project")
        checked = after(relocked, "lock --check")
        installed = after(checked, "_builtin_setup_environment")
        activated = after(installed, "$(call RUN_PUBLIC_ACTIVATE,gen)")

        tm.that(steps[upgraded], has="--upgrade")
        tm.that(steps[relocked], lacks="--upgrade")
        tm.that(
            upgraded < bumped < projected < relocked < checked < installed,
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
            eq={"_upg_lifecycle", "_builtin-verify-clean"},
        )
        tm.that(
            "_upg_lifecycle"
            in self._recipe_targets_containing(makefile, "$(SELF_MAKE) check"),
            eq=False,
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
        steps = (
            makefile
            .split("_upg_lifecycle: _builtin_setup_submodules\n", 1)[1]
            .split("\n\n", 1)[0]
            .splitlines()
        )
        order = [
            next(i for i, step in enumerate(steps) if needle in step)
            for needle in (
                "--what mise-config --scope self --mode apply",
                "lock --bump",
                "install --yes",
                "deps modernize",
                "$(SELF_MAKE) _builtin_require_environment",
                "$(call RUN_PUBLIC_PRODUCE,gen)",
                "$(call RUN_PUBLIC_ACTIVATE,gen)",
                "$(SELF_MAKE) gen",
                'codegen conform --root "$(PROJECT_ROOT)" --mode check',
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
            has="_builtin_require_environment: _builtin_require_workspace\n",
        )
        tm.that(makefile, lacks="_builtin_require_mise")

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
            eq={"_upg_lifecycle", "_builtin-audit"},
        )
        tm.that(
            self._recipe_targets_containing(makefile, "codegen mise-proof"),
            eq={"_builtin-audit"},
        )
        tm.that(makefile, lacks=["_builtin_setup_lock_verdict", "ERROR[setup]"])
        audit = makefile.split("_builtin-audit:\n", 1)[1].split("\n_builtin-", 1)[0]
        tm.that(audit, has=["ERROR[audit]", "make upg", "exit 2"])

    @pytest.mark.parametrize(
        "generated_make_template",
        [c.Infra.MakeProfile.STANDALONE],
        indirect=True,
    )
    def test_attached_member_upg_stops_before_any_lock(
        self,
        tmp_path: Path,
        generated_make_template: t.Pair[c.Infra.MakeProfile, Path],
    ) -> None:
        """`make upg` in an attached member fails loud and writes no lock.

        Inside a workspace the member resolves the workspace runtime, where
        `uv lock` rewrites the workspace lock and never the member's own.
        """
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
        previous = {lock.name: lock.read_bytes() for lock in member.glob("*.lock")}

        upgraded = tm.ok(
            u.Tests.run_isolated_make(["--no-print-directory", "upg"], cwd=member),
        )

        tm.that(u.Cli.process_succeeded(upgraded.outcome), eq=False)
        tm.that(upgraded.stderr, has=["ERROR[upg]", str(workspace.resolve())])
        tm.that(
            {lock.name: lock.read_bytes() for lock in member.glob("*.lock")},
            eq=previous,
        )
        tm.that(workspace_lock.exists(), eq=False)
