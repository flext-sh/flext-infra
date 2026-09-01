"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, config, t, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

pytestmark = pytest.mark.slow


class TestCodegenCiMatrix:
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def _render_project(root: Path) -> Path:
        """Render a fresh EXTERNAL project into root and return the root."""
        beads = tm.ok(
            FlextInfraWorkspaceDetector.load_beads_spec(
                Path(__file__).resolve().parents[3]
            )
        )
        service = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            beads_workspace=beads.workspace,
            beads_database=beads.database,
            beads_issue_prefix=beads.issue_prefix,
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        result = service.execute()
        tm.ok(result)
        return root

    def test_ci_matrix_profiles_are_topology_complete(self) -> None:
        """Matrix and distro Dockerfiles cover both repository-local profiles."""
        entries = config.Infra.codegen.templates.entries
        matrix = next(
            entry
            for entry in entries
            if entry.destination == ".github/workflows/ci-matrix.yml"
        )
        tm.that(set(matrix.profiles), eq={"workspace", "standalone"})
        docker_dests = {
            f"tests/fixtures/ci/docker/{name}.Dockerfile"
            for name in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        for entry in entries:
            if entry.destination not in docker_dests:
                continue
            tm.that(set(entry.profiles), eq={"workspace", "standalone"})

    def test_ci_matrix_workflow_emitted(self, tmp_path: Path) -> None:
        """Generated project carries .github/workflows/ci-matrix.yml."""
        root = self._render_project(tmp_path / "external")
        tm.that((root / ".github" / "workflows" / "ci-matrix.yml").is_file(), eq=True)

    def test_gate_attestation_is_generated_as_transparent_checkpoint(
        self, tmp_path: Path
    ) -> None:
        """Managed projects emit one automatic local-to-GitHub proof pipeline."""
        root = self._render_project(tmp_path / "attested")
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        script = (root / ".github/scripts/gate-attestation.sh").read_text(
            encoding="utf-8"
        )
        workflow = (root / ".github/workflows/gate-attestation.yml").read_text(
            encoding="utf-8"
        )

        tm.that(makefile, has="_builtin_checkpoint_wip:")
        tm.that(makefile, has="_builtin_checkpoint_merge:")
        tm.that(makefile, has="_builtin_checkpoint_review:")
        tm.that(makefile, has="_builtin_checkpoint_verify:")
        tm.that(script, has='git commit -m "[WIP] $MESSAGE ($BEAD)"')
        tm.that(script, lacks="[skip ci]")
        wip_case = script.split("  wip)", maxsplit=1)[1].split("  merge)", maxsplit=1)[0]
        merge_case = script.split("  merge)", maxsplit=1)[1].split("  review)", maxsplit=1)[0]
        review_case = script.split("  review)", maxsplit=1)[1].split("  verify)", maxsplit=1)[0]
        tm.that(wip_case, lacks="run_local_gates")
        tm.that(wip_case, lacks="publish_receipt")
        tm.that(wip_case, has="validation and attestation NOT SELECTED")
        tm.that(merge_case, has="aggregate_pull_requests")
        tm.that(merge_case, has="close_transferred_drafts")
        tm.that(script, has='gh pr close "$source_pr"')
        tm.that(script, has="Transferred automatically to maintained PR #$PR")
        tm.that(script, has="for source_pr in $SOURCE_PRS")
        tm.that(script, lacks="MAX_DRAFT")
        tm.that(review_case, has="run_local_gates")
        tm.that(review_case, has="publish_receipt")
        tm.that(
            review_case.index("run_local_gates"),
            lt(review_case.index("git commit --allow-empty")),
        )
        tm.that(
            review_case.index("run_local_gates"),
            lt(review_case.index("publish_receipt")),
        )
        tm.that(script, has='git merge --no-ff')
        tm.that(script, has="git tag -s")
        tm.that(script, has="bd update")
        tm.that(workflow, has="id-token: write")
        tm.that(workflow, has="attestations: write")
        action = config.Infra.codegen.github_actions["attest"]
        tm.that(workflow, has=f"uses: {action.repository}@{action.sha}")
        tm.that(workflow, has=".github/scripts/gate-attestation.sh verify")
        tm.that(workflow, lacks="make check")
        tm.that(workflow, lacks="make test")

    def test_github_apps_are_not_selected_for_draft_prs(self, tmp_path: Path) -> None:
        """Versioned app policy reserves external review for non-Draft PRs."""
        root = self._render_project(tmp_path / "apps-review-only")
        cubic = (root / "cubic.yaml").read_text(encoding="utf-8")
        tm.that(cubic, has="check_drafts: false")
        tm.that(cubic, has="- WIP")
        tm.that(cubic, has="generate: false")

    def test_ci_workflow_uses_immutable_action_catalog(self, tmp_path: Path) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = self._render_project(tmp_path / "external")
        workflows = "\n".join(
            (root / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            for filename in ("ci.yml", "ci-matrix.yml", "gate-attestation.yml")
        )
        catalog = {
            f"{action.repository}@{action.sha}": action.version
            for action in config.Infra.codegen.github_actions.values()
        }
        used_actions = tuple(
            line.split("uses:", maxsplit=1)[1].strip().split(maxsplit=1)[0]
            for line in workflows.splitlines()
            if "uses:" in line
        )
        tm.that(len(used_actions), gt=0)
        for action in used_actions:
            tm.that(catalog, has=action)
            # yamllint requires two spaces before an inline comment.
            tm.that(workflows, has=f"{action}  # {catalog[action]}")

        tm.that(workflows, lacks="continue-on-error")
        tm.that(workflows, lacks="set +e")
        tm.that(workflows, lacks="|| make")
        tm.that(workflows, lacks="soft-pass")

    def test_blocking_ci_bootstraps_only_through_make_setup(
        self, tmp_path: Path
    ) -> None:
        """Generated blocking CI provisions every binary via the Make surface."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        tm.that(workflow, has="run: CI=Y make setup")
        tm.that(workflow, has="run: CI=Y make gen WHAT=check")
        tm.that(workflow, has="run: CI=Y make check")
        tm.that(workflow, lacks="run: CI=Y make test")
        tm.that(workflow, lacks="run: make test")
        tm.that(workflow, lacks="WHAT=apply")
        tm.that(workflow, lacks="APPLY=Y")
        tm.that(
            workflow.index("run: CI=Y make setup"),
            lt=workflow.index("run: CI=Y make gen WHAT=check"),
        )
        header, jobs = workflow.split("\njobs:\n", maxsplit=1)
        tm.that(header, lacks="permissions:")
        ci_job = jobs.split("\n  merge-guard:", maxsplit=1)[0]
        tm.that(ci_job, has="permissions:\n      contents: read")

    def test_blocking_ci_configures_git_auth_through_gh(self, tmp_path: Path) -> None:
        """Provider baseline fetches use the runner token through the gh owner."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        tm.that(workflow, has="- name: Configure GitHub authentication")
        tm.that(workflow, has="GH_TOKEN: ${{ github.token }}")
        # The gh credential helper reads GH_TOKEN from the environment of the
        # step that runs git, so the token must be declared on the job, before
        # any step, not only on the setup-git step.
        tm.that(
            workflow.index("GH_TOKEN: ${{ github.token }}")
            < workflow.index("    steps:"),
            eq=True,
        )
        tm.that(workflow, has="run: gh auth setup-git")
        tm.that(
            workflow.index("run: gh auth setup-git")
            < workflow.index("run: CI=Y make gen WHAT=apply APPLY=Y"),
            eq=True,
        )

    def test_rendered_pre_commit_uses_typed_hook_contexts(self, tmp_path: Path) -> None:
        """The generated staged hooks render the configured workflow partitions."""
        root = self._render_project(tmp_path / "external")
        hooks = (root / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        workflow = config.Infra.codegen.make.workflow
        ci = config.Infra.codegen.make.ci

        for hook_id, context in (
            ("flext-pre-commit", "pre_commit"),
            ("flext-pre-push", "pre_push"),
        ):
            enabled = bool(getattr(config.Infra.codegen.make, context))
            commands = " && ".join(
                (
                    f"{ci.variable}={ci.value} make {step.verb}"
                    if step.verb == "check"
                    else f"make {step.verb}"
                )
                + (
                    f" {config.Infra.codegen.make.apply_variable}="
                    f"{config.Infra.codegen.make.apply_value}"
                    if step.apply
                    else ""
                )
                for step in workflow
                if context in step.contexts
            )
            if enabled:
                tm.that(hooks, has=f"id: {hook_id}")
                tm.that(hooks, has=f"'{commands}'")
            else:
                tm.that(hooks, lacks=f"id: {hook_id}")
        tm.that(hooks, lacks=f"export {ci.variable}={ci.value}")

    def test_ci_workflow_cancels_superseded_ref_runs(self, tmp_path: Path) -> None:
        """Generated CI groups competing runs by workflow and ref."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        tm.that(workflow, has="concurrency:")
        tm.that(workflow, has="group: ${{ github.workflow }}-${{ github.ref }}")
        tm.that(workflow, has="cancel-in-progress: true")

    def test_ci_workflow_stable_blank_line_without_private_submodules(
        self, tmp_path: Path
    ) -> None:
        """Empty private_submodules include must not accumulate blank lines."""
        root = self._render_project(tmp_path / "member")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        marker = (
            "fetch-depth: 0\n\n      # Codegen refreshes the declared provider baseline"
        )
        tm.that(workflow, has=marker)
        tm.that(
            workflow,
            lacks=(
                "fetch-depth: 0\n\n\n"
                "      # Codegen refreshes the declared provider baseline"
            ),
        )
        root2 = self._render_project(tmp_path / "member-again")
        workflow2 = (root2 / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        tm.that(workflow2, eq=workflow)

    def test_docs_workflow_inits_private_submodules_when_configured(self) -> None:
        """Docs jobs that run make setup must use the same deploy-key init as CI."""
        from flext_infra import config, m
        from flext_cli import u as cli_u

        codegen = config.Infra.codegen
        private = codegen.ci_private_submodules.get("cosmos-main")
        tm.that(private is not None, eq=True)
        assert private is not None
        tpl = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
        )
        spec = m.Infra.GithubWorkflowRenderSpec(
            dist="cosmos-main",
            make_profile=c.Infra.MakeProfile.WORKSPACE,
            repository_branch="develop",
            ci_trigger_branches=("dev", "develop", "0.12.0-dev", "develop", "main"),
            python_version=codegen.toolchain.python_version,
            mise_version=codegen.toolchain.mise_version,
            uv_version=codegen.toolchain.uv_version,
            dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
            github_actions=codegen.github_actions,
            gate_attestation=codegen.gate_attestation,
            make=codegen.make,
            workspace_repositories=(),
            checkout_submodules=codegen.checkout_submodules,
            private_submodules=private,
        )
        rendered = cli_u.Cli.template_render(tpl, spec)
        tm.ok(rendered)
        rendered_text: str = rendered.value
        tm.that(rendered_text, has="Init private workspace projects")
        tm.that(rendered_text.count("Init private workspace projects"), eq=2)

    def test_ci_uses_typed_action_catalog(self, tmp_path: Path) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        actions = config.Infra.codegen.github_actions
        for action in actions.values():
            if action.repository in workflow:
                # yamllint requires two spaces before an inline comment.
                tm.that(
                    workflow,
                    has=f"{action.repository}@{action.sha}  # {action.version}",
                )

    def test_dependabot_uses_uv_dependency_cooldown(self, tmp_path: Path) -> None:
        """Dependabot never raises floors newer than uv will resolve."""
        root = self._render_project(tmp_path / "external")
        cooldown = config.Infra.codegen.toolchain.dependency_cooldown_days

        document = u.Cli.yaml_load_mapping(root / ".github" / "dependabot.yml")
        updates = t.Cli.JSON_LIST_ADAPTER.validate_python(document["updates"])
        ecosystems = {
            str(t.Cli.JSON_MAPPING_ADAPTER.validate_python(item)["package-ecosystem"])
            for item in updates
        }
        tm.that(ecosystems, eq={"github-actions", "pip"})
        for item in updates:
            update = t.Cli.JSON_MAPPING_ADAPTER.validate_python(item)
            cooldown_config = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                update["cooldown"]
            )
            tm.that(cooldown_config["default-days"], eq=cooldown)
        tm.that(config.Infra.codegen.toolchain.uv_exclude_newer, eq=f"{cooldown} days")

    def test_distro_dockerfiles_emitted(self, tmp_path: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            tm.that(
                (
                    root
                    / "tests"
                    / "fixtures"
                    / "ci"
                    / "docker"
                    / f"{distro}.Dockerfile"
                ).is_file(),
                eq=True,
            )

    def test_distro_bootstrap_is_fail_closed_and_self_contained(
        self, tmp_path: Path
    ) -> None:
        """Every distro runs the canonical self-bootstrap fail-closed."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            content = (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_text(encoding="utf-8")
            tm.that(content, has="make setup")
            tm.that(content, has="ENV CI=Y")
            tm.that(content, lacks="UV_UNMANAGED_INSTALL")
            tm.that(content, lacks="uv python install")
            if distro == "alpine":
                tm.that(content, has="bash")
                tm.that(content, has="build-base")
            tm.that(content, has="USER runner")
            tm.that(content, has="./bin/mise install --locked --yes")
            tm.that(content, has="RUN --mount=type=bind,source=.,target=/source,ro")
            tm.that(content, has="cp -R /source/. /workspace/")
            tm.that(content, lacks="COPY")
            tm.that(content, lacks="chmod -R a+rwX")
            tm.that(content, lacks="GITHUB_TOKEN")

    def test_fedora_dockerfile_installs_libatomic_only_for_fedora(
        self, tmp_path: Path
    ) -> None:
        """Fedora's generated Node runtime has its required atomic library."""
        root = self._render_project(tmp_path / "external")
        fedora = (
            root / "tests" / "fixtures" / "ci" / "docker" / "fedora.Dockerfile"
        ).read_text(encoding="utf-8")
        tm.that(fedora, has="libatomic")
        for distro in ("ubuntu", "debian", "alpine", "arch"):
            content = (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_text(encoding="utf-8")
            tm.that("libatomic" not in content, eq=True, msg=distro)

    def test_dockerfiles_render_byte_idempotently(self, tmp_path: Path) -> None:
        """Repeated project generation preserves the generated Dockerfiles."""
        root = self._render_project(tmp_path / "external")
        before = {
            distro: (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_bytes()
            for distro in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        self._render_project(root)
        after = {
            distro: (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_bytes()
            for distro in before
        }
        tm.that(after, eq=before)

    def test_ci_matrix_has_only_supported_generic_legs(self, tmp_path: Path) -> None:
        """Generic Python CI emits only its complete cross-platform legs."""
        root = self._render_project(tmp_path / "external")
        workflow = root / ".github" / "workflows" / "ci-matrix.yml"
        tm.that(workflow.is_file(), eq=True)
        content = u.Cli.yaml_load_mapping(workflow)
        jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(content["jobs"])
        for leg in ("distro-matrix", "macos", "windows"):
            tm.that(jobs, has=leg)
        tm.that(jobs, lacks="wsl")
        tm.that(jobs, lacks="kind")

    def test_host_legs_bootstrap_only_through_make_setup(self, tmp_path: Path) -> None:
        """MacOS and Windows bootstrap through the same Make surface."""
        root = self._render_project(tmp_path / "external")
        content = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        macos = content.split("\n  macos:", maxsplit=1)[1].split(
            "\n  windows:", maxsplit=1
        )[0]
        windows = content.split("\n  windows:", maxsplit=1)[1]
        for host in (macos, windows):
            tm.that(host, has="run: CI=Y make setup")
            tm.that(host, has="run: CI=Y make help")
        tm.that(windows.count("shell: bash"), eq=3)

    def test_workflow_ci_policy_matrix_default_dispatch_only(
        self, tmp_path: Path
    ) -> None:
        """Blocking CI covers integration; matrix defaults to dispatch-only."""
        root = self._render_project(tmp_path / "external")
        provider = config.Infra.codegen.providers[0]
        branch = provider.branch
        blocking = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        integrations = ("dev", "develop", "0.12.0-dev", "main")
        tm.that(integrations, has=branch)
        for integration in integrations:
            tm.that(blocking, has=f"      - {integration}")
        tm.that(blocking, has="draft == false")
        tm.that(blocking, has="ready_for_review")
        triggers = matrix.split('"on":', maxsplit=1)[1].split(
            "# End SECTION: triggers", maxsplit=1
        )[0]
        tm.that(triggers, has="workflow_dispatch: {}")
        tm.that(triggers, lacks="branches: [main]")
        tm.that(triggers, lacks="pull_request:")
        tm.that(triggers, lacks="ready_for_review")
        tm.that(triggers, lacks="repository_branch")
        tm.that(triggers, lacks="0.12.0-dev")
        tm.that(triggers, lacks="develop")
        tm.that(triggers, lacks="branches: [dev]")

    def test_draft_wip_selects_no_jobs_and_review_blocks_wip_head(
        self, tmp_path: Path
    ) -> None:
        """Draft is remote durability; only a promoted non-WIP head may land."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        _, jobs = workflow.split("\njobs:\n", maxsplit=1)
        ci_job, merge_guard = jobs.split("\n  merge-guard:", maxsplit=1)

        tm.that(ci_job, has="github.event.pull_request.draft == false")
        tm.that(merge_guard, has="github.event.pull_request.draft == false")
        tm.that(merge_guard, has="subject=$(git log -1 --format=%s)")
        tm.that(merge_guard, has='[[ "$subject" == \\[WIP\\]* ]]')
        tm.that(merge_guard, has="WIP head cannot merge")
        tm.that(merge_guard, lacks="DRAFT PR cannot merge")

    def test_ci_matrix_template_defaults_dispatch_only(self) -> None:
        """The SSOT template is statically dispatch-only for every profile."""
        template = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / ".github"
            / "workflows"
            / "ci-matrix.yml.j2"
        )
        content = template.read_text(encoding="utf-8")
        triggers = content.split('"on":', maxsplit=1)[1].split(
            "# End SECTION: triggers", maxsplit=1
        )[0]
        tm.that(triggers, has="workflow_dispatch: {}")
        tm.that(triggers, lacks="branches: [main]")
        tm.that(triggers, lacks="pull_request:")
        tm.that(triggers, lacks="repository_branch")
        tm.that(triggers, lacks="0.12.0-dev")
        tm.that(triggers, lacks="develop")
        tm.that(triggers, lacks="branches: [dev]")
        tm.that(content, lacks="{% if make_profile")

    def test_docs_workflow_covers_every_blocking_ci_branch(
        self, tmp_path: Path
    ) -> None:
        """Docs validation follows the same governed branch lanes as CI."""
        root = self._render_project(tmp_path / "external")
        content = (root / ".github" / "workflows" / "docs.yml").read_text(
            encoding="utf-8"
        )

        for branch in ("dev", "develop", "0.12.0-dev", "main"):
            tm.that(content, has=f"      - {branch}")

    def test_ci_matrix_check_uses_ci_token_and_never_runs_test(
        self, tmp_path: Path
    ) -> None:
        """Matrix smoke is help+check under CI=Y; it must never run make test."""
        root = self._render_project(tmp_path / "external")
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        ci = config.Infra.codegen.make.ci
        smoke = matrix.split("Bootstrap + verb smoke", maxsplit=1)[1].split(
            "# End SECTION: distro-matrix", maxsplit=1
        )[0]
        tm.that(smoke, has=f"-e {ci.variable}={ci.value}")
        tm.that(smoke, has="make help")
        tm.that(smoke, has="make check")
        tm.that(smoke, lacks="} make test")
        tm.that(
            smoke,
            has="ci-matrix proves bootstrap + check across distros; it never runs make test",
        )
        dockerfiles = list(
            (root / "tests" / "fixtures" / "ci" / "docker").glob("*.Dockerfile")
        )
        tm.that(len(dockerfiles) > 0, eq=True)
        for dockerfile in dockerfiles:
            body = dockerfile.read_text(encoding="utf-8")
            tm.that(body, has="ENV CI=Y")
            tm.that(body, has="RUN make setup")

    def test_makefile_normalizes_windows_runtime_paths(self, tmp_path: Path) -> None:
        """Generated POSIX Make resolves Windows uv and virtualenv executables."""
        root = self._render_project(tmp_path / "external")
        content = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(content, has="ifeq ($(OS),Windows_NT)")
        tm.that(content, has='cygpath --path "$(CALLER_PATH)"')
        tm.that(content, has="RUNTIME_BIN := $(RUNTIME_VENV)/Scripts")
        tm.that(content, has="RUNTIME_PYTHON := $(RUNTIME_BIN)/python.exe")
        tm.that(content, has="override PATH := $(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)")
        tm.that(content, has="_builtin_help_usage:\n\t@printf")
        tm.that(content, has="'flext-demo [standalone]' '';")

    def test_root_dockerignore_reincludes_bootstrap_surface(self) -> None:
        """Root hand-maintained .dockerignore lets clean-machine bootstrap files into the context."""
        root = Path(__file__).resolve().parents[3]
        dockerignore = root / ".dockerignore"
        tm.that(dockerignore.is_file(), eq=True)
        content = dockerignore.read_text(encoding="utf-8")
        for marker in (
            "!Makefile",
            "!*.mk",
            "!pyproject.toml",
            "!README.md",
            "!uv.lock",
            "!.mise.toml",
            "!mise.lock",
            "!bin/",
            "!bin/mise",
            "!bin/mise.cmd",
            "!.python-version",
            "!.default-python-packages",
            "!config/",
            "!scripts/dispatch.py",
            "!tests/fixtures/ci/docker/",
        ):
            tm.that(content, has=marker)


__all__: list[str] = []
