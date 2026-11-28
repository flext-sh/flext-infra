"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableMapping
from pathlib import Path

from flext_infra import config
from tests import c, m, p, t, tm, u


@c.Tests.MARK.slow
class TestsFlextInfraScriptDispatchMakefile:
    """Prove per-repo extra verbs and script-dispatch WHAT normalization."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verbs: tuple[p.Infra.MakeVerbSpec, ...],
        script_dispatch: p.Infra.ScriptDispatchSpec | None,
        commands: tuple[tuple[str, t.JsonMapping], ...] = (),
    ) -> str:
        # The engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = u.Tests.provider()
        root_repository = m.Infra.RepositoryRef.model_validate({
            "name": ("demo-root"),
            "distribution": ("demo-root"),
            "url": (f"{provider.base_url}/demo-root.git"),
            "path": (Path()),
            "role": (c.Infra.MakeProfile.STANDALONE),
            "provider": (provider.name),
            "kind": (c.Infra.ProjectKind.INTERNAL_FLEXT),
            "codegen": (c.Infra.CodegenKind.CONFORM),
            "package": (False),
            "editable": (False),
            "read_only": (False),
            "extra_verbs": (extra_verbs),
            "script_dispatch": (script_dispatch),
        })
        workspace = u.Tests.workspace_spec(
            root_repository,
            project=u.Tests.project_spec("demo-root"),
        )
        root = tmp_path / root_repository.name
        u.Tests.standalone_workspace(root, name=root_repository.name)
        for relative, command in commands:
            u.Tests.write_promoted_command(root / relative, command)
        u.Tests.initialize_git_repo(root, origin_url=root_repository.url)
        rendered: str = u.Tests.conform_makefile_text(
            root,
            workspace,
        )
        return rendered

    @staticmethod
    def _command(
        verb: str,
        what: str,
        aliases: tuple[str, ...] = (),
    ) -> t.JsonMapping:
        """Return one promoted command header table.

        Returns:
            The ``[tool.flext.command]`` table of one read-only command.

        """
        return {
            "verb": verb,
            "what": what,
            "domain": verb,
            "summary": f"Run {verb} {what}",
            "description": f"Run the {verb} {what} action.",
            "example": f"make {verb} WHAT={what}",
            "mutates": False,
            "aliases": [*aliases],
        }

    def test_header_declared_verbs_and_aliases_get_public_targets(
        self,
        tmp_path: Path,
    ) -> None:
        """Every verb and alias a command header declares is a public target.

        No ``all.sh`` entrypoint and no ``extra_verbs`` entry declares them:
        the promoted registry the dispatcher builds, over every declared
        root, is the only source of the script verbs.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
            commands=(
                ("scripts/finops/krr_sizing.py", self._command("finops", "krr-sizing")),
                (
                    "scripts/incidente/all.sh",
                    self._command("incidente", "all", ("breakglass",)),
                ),
                (
                    "apps/demo-app/scripts/charts/adopt.py",
                    self._command("charts", "adopt"),
                ),
            ),
        )
        script_verbs = next(
            line for line in rendered.splitlines() if line.startswith("SCRIPT_VERBS :=")
        )
        tm.that(
            script_verbs.split()[2:],
            eq=["breakglass", "charts", "finops", "incidente"],
        )
        tm.that(
            rendered,
            has=[
                f"_builtin-{verb}: _builtin_require_environment\n"
                f"\t$(call _dispatch,{verb})"
                for verb in ("breakglass", "charts", "finops", "incidente")
            ],
        )

    def test_script_dispatch_repo_routes_extra_verbs_and_normalizes_what(
        self,
        tmp_path: Path,
    ) -> None:
        """Extra verbs join PUBLIC_VERBS and dispatch through the dispatcher."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="incidente",
                    description="Dispatch incidente through the dispatcher.",
                ),
                m.Infra.MakeVerbSpec(
                    name="charts",
                    description="Dispatch charts through the dispatcher.",
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
            commands=(("scripts/incidente/all.sh", self._command("incidente", "all")),),
        )
        # Extra verbs are public targets the dispatcher can reach.
        tm.ok("incidente" in rendered)
        tm.ok("charts" in rendered)
        # Each extra verb gets a _builtin-<verb> target that dispatches through
        # the repo's declared dispatcher.
        tm.ok("_builtin-incidente:" in rendered)
        tm.ok("_builtin-charts:" in rendered)
        # It forwards to the declared dispatcher through uv, not a raw builtin.
        tm.ok("python -m scripts.dispatch " in rendered)
        # Selectors reach the dispatcher as literal environment data.
        tm.that(rendered, has="override export WHAT := $(value WHAT)")

    def test_extra_verb_dispatch_target_is_emitted_exactly_once(
        self,
        tmp_path: Path,
    ) -> None:
        """Every extra verb owns one public recipe; a second one is a Make warning.

        Two integrations of the same dispatch block once rendered every extra
        verb twice, and GNU Make reported ``overriding recipe for target`` on
        each parse of the consumer's Makefile.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(name="deploy", description="Publish the runtime."),
            ),
            script_dispatch=None,
        )
        makefile = tmp_path / "demo-root" / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        observed = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "help"],
                cwd=makefile.parent,
            ),
        )
        tm.that(u.Cli.process_succeeded(observed.outcome), eq=True, msg=observed.stderr)
        deploy_entries = [
            line
            for line in observed.stdout.splitlines()
            if line.split(maxsplit=1)[:1] == ["deploy"]
        ]
        tm.that(len(deploy_entries), eq=1)
        tm.that(observed.stderr, lacks="overriding recipe for target")

    def test_dispatch_routes_custom_what_before_allowlist(self, tmp_path: Path) -> None:
        """Custom ``_custom_<verb>`` handlers bypass the builtin allowlist.

        ai-hub and other projects extend ``run`` / ``check`` via custom.mk. The
        continuous Makefile RUN_PUBLIC macro discovers those handlers and
        dispatches them instead of falling through to _builtin-<verb>.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        # RUN_PUBLIC checks CUSTOM_DECLARED_TARGETS first and calls _custom-$(1)
        # when it exists, falling back to _builtin-$(1).
        tm.ok("define RUN_PUBLIC" in rendered)
        tm.ok("_custom-$(1)" in rendered)
        tm.ok("_builtin-$(1)" in rendered)

    def test_repo_without_script_dispatch_omits_script_routing(
        self,
        tmp_path: Path,
    ) -> None:
        """A repo with no script dispatch omits every script-routing projection."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        # No script routing leaks into non-opted-in repositories.
        tm.fail("tr '-' '_'" in rendered)
        tm.fail("scripts.dispatch" in rendered)

    def test_check_owns_generation_without_retired_public_verbs(
        self,
        tmp_path: Path,
    ) -> None:
        """Check owns convergence; its private phases are not public verbs."""
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        retired = {"gen", "gen-scope", "fmt", "fix", "codegen"}
        tm.ok(c.Infra.VERB_CHECK in verb_names)
        tm.fail(bool(retired & verb_names))
        check = next(
            verb for verb in make_config.verbs if verb.name == c.Infra.VERB_CHECK
        )
        check_fields = type(check).model_fields
        tm.fail("default_what" in check_fields)
        tm.fail("_apply_flag_exterminated" in check_fields)
        tm.fail("serialization" in type(make_config).model_fields)
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        public_verbs = set(public_line.split(":=", 1)[1].split())
        tm.ok(c.Infra.VERB_CHECK in public_verbs)
        tm.fail(bool(retired & public_verbs))
        tm.that(rendered, has="_builtin-check: _builtin_check_all")
        tm.that(rendered, has="$(SELF_MAKE) _builtin_converge_all")
        for retired_verb in retired:
            tm.that(rendered, lacks=f"_builtin-{retired_verb}:")
        for phase in ("gen", "fix", "fmt"):
            tm.that(rendered, has=f"$(SELF_MAKE) _builtin_{phase}_all")
        gen_all_body = rendered.split("_builtin_gen_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(gen_all_body, has="$(PROJECT_FLEXT_INFRA) codegen generate")
        tm.that(gen_all_body, has='$(DIRENV) allow "$$allow_root"')
        tm.that(
            gen_all_body,
            lacks=[
                "$(FLEXT_INFRA_BOOTSTRAP)",
                "codegen conform",
                "codegen init",
                "deps modernize",
                "--mode apply",
                "--mode check",
                "codegen lazy-init",
                "docs generate",
            ],
        )
        tm.ok("# @flext-regenerate: make check" in rendered)
        handler_policies: MutableMapping[str, p.Infra.CustomHandlerPolicy] = dict(
            make_config.custom_handler_policies,
        )
        for policy in handler_policies.values():
            for retired_verb in retired:
                tm.fail(re.fullmatch(policy.target_pattern, retired_verb) is not None)
            for target in ("pre-check", "_custom-check", "post-check"):
                tm.ok(re.fullmatch(policy.target_pattern, target) is not None)

    def test_check_convergence_preserves_gitlinks_and_staging(
        self,
        tmp_path: Path,
    ) -> None:
        """Check convergence with a tracked checkout and staged edits."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        root = tmp_path / "workspace"
        member = root / "member"
        member.mkdir(parents=True)
        u.Tests.initialize_git_repo(root)
        u.Tests.initialize_git_repo(member)
        member_head = u.Tests.git_capture(member, "rev-parse", c.Infra.GIT_HEAD).strip()
        u.Tests.git_run(
            root,
            "update-index",
            "--add",
            "--cacheinfo",
            f"{c.Infra.GIT_GITLINK_MODE_TEXT},{member_head},{member.name}",
        )
        u.Tests.commit_git_changes(root, "attach member")
        document = root / "README.md"
        document.write_text("staged\n", encoding="utf-8")
        u.Tests.git_run(root, "add", "--", document.name)
        document.write_text("working tree\n", encoding="utf-8")
        member_document = member / document.name
        member_document.write_text("staged in member\n", encoding="utf-8")
        u.Tests.git_run(member, "add", "--", member_document.name)
        member_document.write_text("working tree in member\n", encoding="utf-8")
        staged = u.Tests.git_capture(root, "ls-files", "--stage")
        member_staged = u.Tests.git_capture(member, "ls-files", "--stage")
        convergence = rendered.split("_builtin_converge_all:", 1)[1].split(
            "\n\n",
            1,
        )[0]
        pass_limit = next(
            line
            for line in rendered.splitlines()
            if line.startswith("override CHECK_CONVERGE_MAX_PASSES :=")
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            "PROJECT_ROOT := .\n"
            f"WORKSPACE_SUBPROJECTS := {member.name}\n"
            'SELF_MAKE := $(MAKE) --no-print-directory -f "$(firstword '
            '$(MAKEFILE_LIST))"\n'
            f"{pass_limit}\n"
            "_builtin_require_environment: ;\n"
            f"_builtin_converge_all:{convergence}\n\n"
            "_builtin_gen_all: ;\n"
            "_builtin_fix_all: ;\n"
            f"_builtin_fmt_all:\n\t@printf 'projected\\n' > "
            f"{member.name}/projected.txt\n",
            encoding="utf-8",
        )

        command = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "-f", str(makefile), "_builtin_converge_all"],
                cwd=root,
            ),
        )

        tm.ok(u.Cli.process_succeeded(command.outcome))
        tm.that(command.stdout, has="fixed point after 2 pass(es)")
        tm.that(command.stderr, lacks="embedded git repository")
        tm.that(u.Tests.git_capture(root, "ls-files", "--stage"), eq=staged)
        tm.that(u.Tests.git_capture(member, "ls-files", "--stage"), eq=member_staged)

    def test_work_lifecycle_is_not_projected(self, tmp_path: Path) -> None:
        """Gas City owns lanes; generated repositories expose no second lifecycle."""
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.fail("work" in verb_names)
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.fail(" work" in public_line)
        tm.that(rendered, lacks="_builtin_work_")
        tm.that(rendered, lacks="workspace work")

    def test_mod_profile_is_bound_to_the_selected_project(self, tmp_path: Path) -> None:
        """The public mod route passes its configured profile path to Infra."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        profile = config.Infra.codegen.make.modification_profile_path
        tm.that(
            rendered,
            has=[
                f'FLEXT_INFRA_PROFILE_OUTPUT="$(PROJECT_ROOT)/{profile}"',
                (
                    "$(PROJECT_FLEXT_INFRA) refactor mod --repository-root "
                    '"$(PROJECT_ROOT)"'
                ),
            ],
            lacks="_builtin-profile-mod-report:",
        )

    def test_test_verbs_share_the_persistent_testmon_database(
        self,
        tmp_path: Path,
    ) -> None:
        """Each test verb uses the native workspace runner and its checkout state."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        make = config.Infra.codegen.make
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(
            public_line.split(":=", 1)[1].split(),
            eq=[
                verb.name
                for verb in make.verbs
                if c.Infra.MakeProfile.STANDALONE in verb.profiles
            ],
        )
        tm.that(
            rendered,
            has=f'FLEXT_INFRA_PROFILE_OUTPUT="$(PROJECT_ROOT)/{make.tests_profile_path}"',
            lacks=[
                c.Infra.PYTEST_ENV_TESTMON_DATAFILE,
                "_builtin-test:",
                "_builtin-test-full:",
                "_builtin-profile-test:",
            ],
        )
        for verb in (c.Infra.VERB_TEST, "tests-full", "tests-harness"):
            handler = verb.replace("-", "_")
            tm.that(rendered, has=f"_builtin-{verb}: _builtin_{handler}_all\n")
            body = rendered.split(f"_builtin_{handler}_all:", 1)[1].split(
                "\n\n",
                1,
            )[0]
            tm.that(
                body,
                has=f'workspace {verb} --repository-root "$(PROJECT_ROOT)"',
            )

    # A test asserting a downstream consumer's verbs from this
    # engine's catalog was removed. The engine is consumer-agnostic: a consumer
    # declares extra_verbs/script_dispatch in its own typed repository input. The
    # generic capability stays covered by the fixture-driven cases below.
    @c.Tests.MARK.parametrize(
        "script_dispatch",
        [
            None,
            m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts",),
            ),
        ],
    )
    def test_lint_and_type_paths_scan_every_configured_analyzer_dir(
        self,
        tmp_path: Path,
        script_dispatch: p.Infra.ScriptDispatchSpec | None,
    ) -> None:
        """Every repo scans the configured analyzer dirs present in its checkout.

        examples/ and scripts/ are first-class code under the same gates as
        src/, so the scanned set is the tooling SSOT, independent of script
        dispatch; the Makefile keeps only the directories that exist.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=script_dispatch,
            commands=()
            if script_dispatch is None
            else (("scripts/sync/all.sh", self._command("sync", "all")),),
        )
        env_dirs = " ".join(config.Infra.tooling.tools.pyrefly.path_rules.env_dirs)
        tm.ok(f"for directory in {env_dirs}; do" in rendered)

    def test_pytest_verbs_leave_basetemp_to_pytest(
        self,
        tmp_path: Path,
    ) -> None:
        """Pytest owns its basetemp: no verb injects a basetemp or temp root."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        tm.that(
            rendered, lacks=["--basetemp", "export TMPDIR TMP TEMP", "scratch_root"]
        )
