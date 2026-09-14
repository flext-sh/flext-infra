"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, u

pytestmark = [pytest.mark.slow]


class TestsFlextInfraScriptDispatchMakefile:
    """Prove per-repo extra verbs and script-dispatch WHAT normalization."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verbs: tuple[m.Infra.MakeVerbSpec, ...],
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> str:
        # The engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = u.Tests.provider()
        root_repository = m.Infra.RepositoryRef(
            name="demo-root",
            distribution="demo-root",
            url=f"{provider.base_url}/demo-root.git",
            path=Path(),
            # Script dispatch is a generic capability: exercise it on standalone.
            role=c.Infra.MakeProfile.STANDALONE,
            provider=provider.name,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
            extra_verbs=extra_verbs,
            script_dispatch=script_dispatch,
        )
        workspace = m.Infra.WorkspaceSpec(
            name="demo-root",
            beads=u.Tests.beads_project("demo-root"),
            repository=root_repository,
            project=u.Tests.project_spec("demo-root"),
            subprojects=(),
        )
        root = tmp_path / "demo-root"
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            repository_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        plan = tm.ok(planned)
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        rendered: str = u.Tests.codegen_file_text(makefile)
        return rendered

    def test_script_dispatch_repo_routes_extra_verbs_and_normalizes_what(
        self, tmp_path: Path
    ) -> None:
        """Extra verbs join PUBLIC_VERBS and dispatch through the declared dispatcher."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="incidente",
                    description="Dispatch incidente through the declared script dispatcher.",
                ),
                m.Infra.MakeVerbSpec(
                    name="charts",
                    description="Dispatch charts through the declared script dispatcher.",
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
        )
        # Extra verbs are public targets the dispatcher can reach.
        tm.that("incidente" in rendered, eq=True)
        tm.that("charts" in rendered, eq=True)
        # Each extra verb gets a _builtin-<verb> target that dispatches through
        # the repo's declared dispatcher.
        tm.that("_builtin-incidente:" in rendered, eq=True)
        tm.that("_builtin-charts:" in rendered, eq=True)
        # It forwards to the declared dispatcher through uv, not a raw builtin.
        tm.that("scripts/dispatch.py" in rendered, eq=True)
        # Script dispatch roots are recorded for operator visibility.
        tm.that("apps/demo-app/scripts" in rendered, eq=True)

    def test_extra_verb_dispatch_target_is_emitted_exactly_once(
        self, tmp_path: Path
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
        tm.that(rendered.count("\ndeploy: _builtin_require_environment\n"), eq=1)

    def test_dispatch_routes_custom_what_before_allowlist(self, tmp_path: Path) -> None:
        """Custom ``_custom_<verb>`` handlers bypass the builtin allowlist.

        ai-hub and other projects extend ``run`` / ``check`` via custom.mk. The
        continuous Makefile RUN_PUBLIC macro discovers those handlers and
        dispatches them instead of falling through to _builtin-<verb>.
        """
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        # RUN_PUBLIC checks CUSTOM_DECLARED_TARGETS first and calls _custom-$(1)
        # when it exists, falling back to _builtin-$(1).
        tm.that("define RUN_PUBLIC" in rendered, eq=True)
        tm.that("_custom-$(1)" in rendered, eq=True)
        tm.that("_builtin-$(1)" in rendered, eq=True)

    def test_repo_without_script_dispatch_omits_script_routing(
        self, tmp_path: Path
    ) -> None:
        """A repo with no script dispatch omits every script-routing projection."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        # No script routing leaks into non-opted-in repositories.
        tm.that("tr '-' '_'" in rendered, eq=False)
        tm.that("scripts/dispatch.py" in rendered, eq=False)

    def test_gen_replaces_codegen_as_the_single_conform_verb(
        self, tmp_path: Path
    ) -> None:
        """``make gen`` is THE conform verb; ``codegen`` no longer exists.

        The convergence spine fuses codegen+conform under the
        single short ``gen`` verb: one verb, one meaning. The old ``codegen``
        Make verb is fully replaced across config, rendered handlers, and the
        regeneration header.
        """
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.that("gen" in verb_names, eq=True)
        tm.that("codegen" in verb_names, eq=False)
        gen = next(verb for verb in make_config.verbs if verb.name == "gen")
        # WHAT selectors were exterminated: one verb, one meaning, declared once.
        tm.that(hasattr(gen, "default_what"), eq=False)
        tm.that(hasattr(gen, "_apply_flag_exterminated"), eq=False)
        tm.that("initialize" in verb_names, eq=True)
        tm.that(hasattr(make_config, "serialization"), eq=False)
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(" gen" in public_line, eq=True)
        tm.that(" codegen" in public_line, eq=False)
        tm.that("_DEFAULT_gen" in rendered, eq=False)
        # S1 (operator law 2026-09-14): gen dispatches unconditionally to
        # _builtin_gen_all; there is no CHECK_ONLY selector, no separate
        # check-mode recipe, and no `conform` verb left at all.
        tm.that("_builtin-gen: _builtin_gen_all" in rendered, eq=True)
        tm.that("_builtin-conform" in rendered, eq=False)
        tm.that("_builtin_gen_check" in rendered, eq=False)
        tm.that("_builtin_gen_apply" in rendered, eq=False)
        tm.that("_builtin_gen_init:" in rendered, eq=True)
        tm.that("_builtin_gen_all:" in rendered, eq=True)
        tm.that("_builtin_codegen_check" in rendered, eq=False)
        tm.that("_builtin_codegen_apply" in rendered, eq=False)
        builtin_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith("BUILTIN_VERBS :=")
        )
        tm.that(" gen" in builtin_line, eq=True)
        tm.that(" codegen" in builtin_line, eq=False)
        phony_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith(".PHONY:") and "_builtin_" in line
        )
        tm.that(phony_line, eq=".PHONY: _builtin_gen_init _builtin_gen_all")
        # The one handler drives the conform engine (CLI namespace is unchanged).
        gen_all_body = rendered.split("_builtin_gen_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(gen_all_body.count("codegen conform"), eq=1)
        tm.that("--mode apply" in gen_all_body, eq=True)
        tm.that("--mode check" in gen_all_body, eq=False)
        tm.that(gen_all_body, has="$(PROJECT_FLEXT_INFRA)")
        tm.that(
            gen_all_body,
            lacks=[
                "_builtin_require_environment",
                "$(FLEXT_INFRA_BOOTSTRAP)",
                "codegen init",
                "deps modernize",
            ],
        )
        tm.that(gen_all_body, lacks="MISE_GITHUB_CREDENTIAL_COMMAND")
        tm.that(
            gen_all_body,
            lacks=["codegen lazy-init", "docs generate", "_generated_docs"],
        )
        tm.that("define _generated_docs" in rendered, eq=False)
        gen_init_body = rendered.split("_builtin_gen_init:", 1)[1].split("\n\n", 1)[0]
        tm.that(gen_init_body.count("codegen init"), eq=2)
        tm.that(gen_init_body, lacks=["codegen conform", "REPOSITORY_ROOT", "bd"])
        # The regeneration contract published on every projection speaks gen.
        tm.that("# @flext-regenerate: make gen" in rendered, eq=True)
        # The custom-surface policy names gen (not codegen) for hooks/handlers.
        handler_policies: dict[str, m.Infra.CustomHandlerPolicy] = dict(
            config.Infra.codegen.make.custom_handler_policies
        )
        for policy in handler_policies.values():
            tm.that("|gen|" in policy.target_pattern, eq=True)
            tm.that("|codegen|" in policy.target_pattern, eq=False)

    def test_make_initialize_bypasses_runtime_and_topology_discovery(
        self, tmp_path: Path
    ) -> None:
        """Execute the public selector with process sentinels around its owner."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        root = tmp_path / "declared-target"
        package = root / "src" / "demo_root"
        package.mkdir(parents=True)
        makefile = root / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(rendered, encoding="utf-8")
        (root / "custom.mk").write_text(
            "$(error init selector evaluated custom.mk)\n", encoding="utf-8"
        )

        calls = root / "init.calls"
        forbidden = root / "forbidden.calls"
        sentinel_bin = root / "sentinel-bin"
        for command in ("git", "bd", "mise", "uv", "sed", "sort", "tr"):
            u.Tests.write_executable(
                sentinel_bin / command,
                f"#!/bin/sh\nprintf '%s\\n' '{command}' >> '{forbidden}'\nexit 97\n",
            )
        # The interpreter the generated Makefile derives for the infra owner,
        # and the owner package reached through the declared public input.
        venv_bin = root / ".venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python").symlink_to(sys.executable)
        owner_root = root / "init-owner"
        owner_package = owner_root / "flext_infra"
        owner_package.mkdir(parents=True)
        (owner_package / "__init__.py").write_text("", encoding="utf-8")
        (owner_package / "__main__.py").write_text(
            "import sys\n"
            "from pathlib import Path\n"
            f"calls = Path({str(calls)!r})\n"
            f"marker = Path({str(package / '__init__.py')!r})\n"
            "argv = sys.argv[1:]\n"
            "with calls.open('a', encoding='utf-8') as handle:\n"
            "    handle.write(' '.join(argv) + '\\n')\n"
            "if argv[:2] != ['codegen', 'init']:\n"
            "    sys.exit(98)\n"
            "if '--apply' in argv:\n"
            "    marker.write_text('# generated\\n', encoding='utf-8')\n"
            "elif '--check' in argv:\n"
            "    sys.exit(0 if marker.is_file() else 1)\n"
            "else:\n"
            "    sys.exit(98)\n",
            encoding="utf-8",
        )
        environment = dict(os.environ)
        environment["PATH"] = f"{sentinel_bin}:{environment['PATH']}"

        invoked = u.Cli.run_raw(
            [
                "make",
                "--no-print-directory",
                "-f",
                str(makefile),
                "initialize",
                f"PROJECT_INFRA_PYTHONPATH={owner_root}",
            ],
            cwd=root,
            env=environment,
        )

        tm.ok(invoked)
        tm.that(u.Cli.process_succeeded(invoked.value.outcome), eq=True)
        tm.that(forbidden.exists(), eq=False)
        tm.that(
            calls.read_text(encoding="utf-8").splitlines(),
            eq=[
                f"codegen init --repository-root {root} --apply",
                f"codegen init --repository-root {root} --check",
            ],
        )

    def test_work_lifecycle_is_not_projected(self, tmp_path: Path) -> None:
        """Gas City owns lanes; generated repositories expose no second lifecycle."""
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.that("work" in verb_names, eq=False)
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(" work" in public_line, eq=False)
        tm.that(rendered, lacks="_builtin_work_")
        tm.that(rendered, lacks="workspace work")

    # A test asserting a downstream consumer's verbs from this
    # engine's catalog was removed. The engine is consumer-agnostic: a consumer
    # declares extra_verbs/script_dispatch in its own typed repository input. The
    # generic capability stays covered by the fixture-driven cases below.
    def test_script_dispatch_adds_scripts_to_lint_and_type_paths(
        self, tmp_path: Path
    ) -> None:
        """Opted-in repos scan scripts alongside src and tests."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="charts",
                    description="Dispatch charts through the declared script dispatcher.",
                ),
                m.Infra.MakeVerbSpec(
                    name="chart-release",
                    description="Dispatch chart-release through the declared script dispatcher.",
                ),
                m.Infra.MakeVerbSpec(
                    name="bead",
                    description="Dispatch bead through the declared script dispatcher.",
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py", roots=("scripts",)
            ),
        )
        tm.that(
            "RUFF_PATHS := $(strip $(foreach d,src tests examples scripts,"
            "$(if $(wildcard $(PROJECT_ROOT)/$(d)/.),$(PROJECT_ROOT)/$(d),)))"
            in rendered,
            eq=True,
        )
        tm.that(
            "MYPY_PATHS := $(strip $(foreach d,src tests examples scripts,"
            "$(if $(wildcard $(PROJECT_ROOT)/$(d)/.),$(PROJECT_ROOT)/$(d),)))"
            in rendered,
            eq=True,
        )

    def test_repo_without_script_dispatch_retains_canonical_lint_and_type_paths(
        self, tmp_path: Path
    ) -> None:
        """A repo without script dispatch keeps src/tests/scripts paths and excludes scripts."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        tm.that(
            "RUFF_PATHS := $(strip $(foreach d,src tests examples,"
            "$(if $(wildcard $(PROJECT_ROOT)/$(d)/.),$(PROJECT_ROOT)/$(d),)))"
            in rendered,
            eq=True,
        )
        tm.that(
            "MYPY_PATHS := $(strip $(foreach d,src tests examples,"
            "$(if $(wildcard $(PROJECT_ROOT)/$(d)/.),$(PROJECT_ROOT)/$(d),)))"
            in rendered,
            eq=True,
        )
        tm.that("$(PROJECT_ROOT)/scripts" in rendered, eq=False)
