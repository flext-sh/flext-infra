"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, config, t, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_tests import tm

pytestmark = pytest.mark.slow


class TestCodegenCiMatrix:
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def _render_project(root: Path) -> Path:
        """Render a fresh EXTERNAL project into root and return the root."""
        service = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
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

    def test_ci_matrix_workflow_emitted(self, tmp_path: Path) -> None:
        """Generated project carries .github/workflows/ci-matrix.yml."""
        root = self._render_project(tmp_path / "external")
        tm.that((root / ".github" / "workflows" / "ci-matrix.yml").is_file(), eq=True)

    def test_ci_workflow_uses_immutable_action_catalog(self, tmp_path: Path) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = self._render_project(tmp_path / "external")
        workflows = "\n".join(
            (root / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            for filename in ("ci.yml", "ci-matrix.yml")
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
        tm.that(workflow, has="run: CI=Y make check")
        tm.that(workflow, lacks="run: CI=Y make test")
        tm.that(workflow, lacks="run: make test")
        tm.that(workflow, has="run: CI=Y make gen WHAT=apply APPLY=Y")
        tm.that(workflow, has="run: CI=Y make fmt WHAT=apply APPLY=Y")
        tm.that(workflow, has="run: CI=Y make fix WHAT=apply APPLY=Y")

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
            tm.that(hooks, has=f"id: {hook_id}")
            tm.that(hooks, has=f"'{commands}'")
        tm.that(hooks, has=f"{ci.variable}={ci.value} make check")
        tm.that(hooks, has="make test")
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
        dependabot = (root / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        cooldown = config.Infra.codegen.toolchain.dependency_cooldown_days

        tm.that(dependabot, has=f"default-days: {cooldown}")
        tm.that(dependabot.count(f"default-days: {cooldown}"), eq=3)
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
        tm.that(windows.count("shell: bash"), eq=2)

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

    def test_ci_matrix_template_defaults_dispatch_only(self) -> None:
        """SSOT template gates main-push auto-run behind ci_matrix_auto_run."""
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
        tm.that(triggers, has="{%- if ci_matrix_auto_run %}")
        tm.that(triggers, has="branches: [main]")
        tm.that(triggers, has="workflow_dispatch: {}")
        tm.that(triggers, lacks="pull_request:")
        tm.that(triggers, lacks="repository_branch")
        tm.that(triggers, lacks="0.12.0-dev")
        tm.that(triggers, lacks="develop")
        tm.that(triggers, lacks="branches: [dev]")
        tm.that(triggers, lacks="workspace-member")
        tm.that(content, lacks="{% if make_profile")

    def test_ci_matrix_overlay_enables_main_push_auto_run(self) -> None:
        """The explicit workflow flag enables push to main."""
        from flext_infra import m
        from flext_cli import u as cli_u

        codegen = config.Infra.codegen
        tpl = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows/ci-matrix.yml.j2"
        )
        disabled = m.Infra.GithubWorkflowRenderSpec(
            dist="flext-demo",
            repository_branch="develop",
            ci_trigger_branches=("dev", "develop", "0.12.0-dev", "develop", "main"),
            python_version=codegen.toolchain.python_version,
            dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
            github_actions=codegen.github_actions,
            make=codegen.make,
            workspace_repositories=(),
            checkout_submodules=codegen.checkout_submodules,
            ci_matrix_auto_run=False,
        )
        enabled = disabled.model_copy(update={"ci_matrix_auto_run": True})
        disabled_text = tm.ok(cli_u.Cli.template_render(tpl, disabled))
        enabled_text = tm.ok(cli_u.Cli.template_render(tpl, enabled))
        disabled_triggers = disabled_text.split('"on":', maxsplit=1)[1].split(
            "# End SECTION: triggers", maxsplit=1
        )[0]
        enabled_triggers = enabled_text.split('"on":', maxsplit=1)[1].split(
            "# End SECTION: triggers", maxsplit=1
        )[0]
        tm.that(disabled_triggers, has="workflow_dispatch: {}")
        tm.that(disabled_triggers, lacks="branches: [main]")
        tm.that(enabled_triggers, has="branches: [main]")
        tm.that(enabled_triggers, has="workflow_dispatch: {}")
        tm.that(enabled_triggers, lacks="pull_request:")

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

    @pytest.mark.parametrize(
        ("content", "expected_changed"),
        [
            pytest.param(
                "# [MANAGED] stale workflow\nname: stale\n", True, id="managed"
            ),
            pytest.param(
                "# Generated by a repository owner\nname: owned\n",
                False,
                id="repository-owned",
            ),
        ],
    )
    def test_existing_workflow_requires_managed_provenance_for_replacement(
        self, tmp_path: Path, content: str, *, expected_changed: bool
    ) -> None:
        """Replace only workflows carrying explicit [MANAGED] provenance."""
        from flext_infra import m
        from flext_infra.codegen.conform import FlextInfraCodegenConform
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        root = self._render_project(tmp_path / "external")
        workflow = root / ".github" / "workflows" / "ci.yml"
        workflow.write_text(content, encoding="utf-8")
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = tm.ok(
            FlextInfraCodegenConform(
                workspace_root=root, request=request, initial_workspace=workspace
            ).plan(request)
        )
        workflow_plan = next(item for item in planned.files if item.path == workflow)
        tm.that(workflow_plan.changed, eq=expected_changed)
        if expected_changed:
            tm.that(workflow_plan.rendered, has=c.Infra.WORKFLOW_MANAGED_PROVENANCE)
            tm.that(workflow_plan.rendered, lacks="name: stale")
        else:
            tm.that(workflow_plan.rendered, eq=content)
            tm.that(workflow_plan.reason, has="repository-owned workflow")

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
            "!.python-version",
            "!.default-python-packages",
            "!config/",
            "!scripts/dispatch.py",
            "!tests/fixtures/ci/docker/",
        ):
            tm.that(content, has=marker)


__all__: list[str] = []
