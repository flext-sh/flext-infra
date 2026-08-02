"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m, t, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm


class TestCodegenCiMatrix:
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def _render_project(root: Path, *, name: str = "flext-demo") -> Path:
        """Render a fresh EXTERNAL project into root and return the root."""
        service = FlextInfraCodegenProjectNew(
            name=name,
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

    def test_checkout_submodule_policy_is_typed_and_project_routed(
        self, tmp_path: Path
    ) -> None:
        """Render the configured default and override through typed workflow input."""
        codegen = config.Infra.codegen
        override_name, override_mode = next(
            (name, mode)
            for name, mode in codegen.checkout_submodules_overrides.items()
            if mode != codegen.checkout_submodules
        )
        payload = codegen.model_dump(mode="python")
        payload["checkout_submodules_overrides"] = {override_name: "invalid-mode"}
        with pytest.raises(c.ValidationError):
            m.Infra.CodegenConfigSpec.model_validate(payload)

        default_name = next(
            f"{override_name}-{suffix}"
            for suffix in ("default", "baseline")
            if f"{override_name}-{suffix}" not in codegen.checkout_submodules_overrides
        )
        cases = (
            (override_name, override_mode),
            (default_name, codegen.checkout_submodules),
        )
        checkout_action = codegen.github_actions["checkout"]
        checkout_reference = f"{checkout_action.repository}@{checkout_action.sha}"
        for index, (name, expected_mode) in enumerate(cases):
            root = self._render_project(tmp_path / f"project-{index}", name=name)
            workflow = u.Cli.yaml_load_mapping(
                root / ".github" / "workflows" / "ci-matrix.yml"
            )
            jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
            for raw_job in jobs.values():
                job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
                steps = t.Cli.JSON_LIST_ADAPTER.validate_python(job["steps"])
                checkout = next(
                    step
                    for raw_step in steps
                    if (
                        step := t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step)
                    ).get("uses")
                    == checkout_reference
                )
                checkout_with = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    checkout["with"]
                )
                tm.that(str(checkout_with["submodules"]).lower(), eq=expected_mode)

    def test_yamllint_policy_is_strict_typed_and_project_routed(
        self, tmp_path: Path
    ) -> None:
        """Derive strict defaults and only the configured real-syntax delta."""
        codegen = config.Infra.codegen
        default_name = next(
            candidate
            for index in range(len(codegen.yamllint.rule_ignore_overrides) + 1)
            if (candidate := f"yamllint-unconfigured-{index}")
            not in codegen.yamllint.rule_ignore_overrides
        )
        default_root = self._render_project(tmp_path / "default", name=default_name)
        default_content = (default_root / ".yamllint").read_text(encoding="utf-8")

        expected_line_length = config.Infra.tooling.tools.yamlfix.line_length
        tm.that(default_content, has=f"max: {expected_line_length}")
        tm.that(default_content, lacks="document-start:")
        tm.that(default_content, lacks="truthy:")
        global_paths = frozenset(
            path for paths in codegen.yamllint.rule_ignores.values() for path in paths
        )
        for index, (override_name, override) in enumerate(
            codegen.yamllint.rule_ignore_overrides.items()
        ):
            override_root = self._render_project(
                tmp_path / f"override-{index}", name=override_name
            )
            override_content = (override_root / ".yamllint").read_text(encoding="utf-8")
            tm.that(override_content, has=f"max: {expected_line_length}")
            tm.that(override_content, lacks="document-start:")
            tm.that(override_content, lacks="truthy:")
            for rule, paths in override.items():
                tm.that(override_content, has=f"  {rule}:")
                for path in paths:
                    tm.that(override_content, has=f"      {path}")
                    if path not in global_paths:
                        tm.that(default_content, lacks=path)

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
        payload = u.Cli.yaml_load_mapping(root / ".github" / "workflows" / "ci.yml")
        jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["jobs"])
        ci_job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["ci"])
        environment = t.Cli.JSON_MAPPING_ADAPTER.validate_python(ci_job["env"])
        steps = t.Cli.JSON_LIST_ADAPTER.validate_python(ci_job["steps"])
        commands = tuple(
            str(step["run"])
            for raw_step in steps
            if "run" in (step := t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step))
        )

        tm.that(commands, eq=config.Infra.codegen.make.workflow_commands["ci"])
        tm.that(
            environment,
            eq={
                config.Infra.codegen.make.ci.variable: config.Infra.codegen.make.ci.value
            },
        )

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

    def test_distro_dockerfiles_emitted(self, tmp_path: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            tm.that(
                (root / "ci" / "docker" / f"{distro}.Dockerfile").is_file(), eq=True
            )

    def test_distro_images_defer_the_single_lifecycle_to_the_workflow(
        self, tmp_path: Path
    ) -> None:
        """Images provision tools but never duplicate the workflow Make lifecycle."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            content = (root / "ci" / "docker" / f"{distro}.Dockerfile").read_text(
                encoding="utf-8"
            )
            tm.that(content, lacks="make setup")
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
        fedora = (root / "ci" / "docker" / "fedora.Dockerfile").read_text(
            encoding="utf-8"
        )
        tm.that(fedora, has="libatomic")
        for distro in ("ubuntu", "debian", "alpine", "arch"):
            content = (root / "ci" / "docker" / f"{distro}.Dockerfile").read_text(
                encoding="utf-8"
            )
            tm.that("libatomic" not in content, eq=True, msg=distro)

    def test_dockerfiles_render_byte_idempotently(self, tmp_path: Path) -> None:
        """Repeated project generation preserves the generated Dockerfiles."""
        root = self._render_project(tmp_path / "external")
        before = {
            distro: (root / "ci" / "docker" / f"{distro}.Dockerfile").read_bytes()
            for distro in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        self._render_project(root)
        after = {
            distro: (root / "ci" / "docker" / f"{distro}.Dockerfile").read_bytes()
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

    def test_ci_matrix_runs_configured_ci_workflow_once_per_job(
        self, tmp_path: Path
    ) -> None:
        """Every matrix job runs one ordered CI lifecycle from the Make SSOT."""
        root = self._render_project(tmp_path / "external")
        make = config.Infra.codegen.make
        expected_commands = make.workflow_commands["ci"]
        tm.that(expected_commands, empty=False)
        workflow = u.Cli.yaml_load_mapping(
            root / ".github" / "workflows" / "ci-matrix.yml"
        )
        jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])

        for name, raw_job in jobs.items():
            job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
            environment = t.Cli.JSON_MAPPING_ADAPTER.validate_python(job["env"])
            tm.that(environment, eq={make.ci.variable: make.ci.value})
            steps = t.Cli.JSON_LIST_ADAPTER.validate_python(job["steps"])
            run_steps = tuple(
                step
                for raw_step in steps
                if "run"
                in (step := t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step))
            )
            rendered_commands = "\n".join(str(step["run"]) for step in run_steps)
            tm.that(rendered_commands, lacks="make gen")
            tm.that(rendered_commands, lacks="conform")
            if name == "distro-matrix":
                tm.that(rendered_commands.count("docker run --rm"), eq=1)
                actual_commands = tuple(
                    line.strip().removesuffix(" &&")
                    for line in rendered_commands.splitlines()
                    if line.strip().startswith("make ")
                )
            else:
                actual_commands = tuple(
                    str(step["run"])
                    for step in run_steps
                    if str(step["run"]).startswith("make ")
                )
            tm.that(actual_commands, eq=expected_commands)
            for command in expected_commands:
                tm.that(actual_commands.count(command), eq=1)
            if name == "windows":
                for step in run_steps:
                    if str(step["run"]).startswith("make "):
                        tm.that(step["shell"], eq="bash")

    def test_ci_matrix_runs_only_configured_branch_promotions(
        self, tmp_path: Path
    ) -> None:
        """Accept only integration PRs into the configured promotion branch."""
        root = self._render_project(tmp_path / "external")
        manifest = u.Cli.yaml_load_mapping(root / "config" / "workspace.yaml")
        repository = t.Cli.JSON_MAPPING_ADAPTER.validate_python(manifest["repository"])
        provider_name = str(repository["provider"])
        provider = next(
            p for p in config.Infra.codegen.providers if p.name == provider_name
        )
        branch = provider.branch
        promotion_branch = config.Infra.codegen.branch_policy.promotion_branch
        workflow_path = root / ".github" / "workflows" / "ci-matrix.yml"
        workflow = u.Cli.yaml_load_mapping(workflow_path)
        events = t.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["on"])
        pull_request = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            events["pull_request"]
        )
        jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])

        tm.that(tuple(events), eq=("pull_request",))
        tm.that(pull_request["branches"], eq=[promotion_branch])
        for raw_job in jobs.values():
            job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
            condition = str(job["if"])
            tm.that(condition, has=f"github.base_ref == '{promotion_branch}'")
            tm.that(condition, has=f"github.head_ref == '{branch}'")

    def test_rendered_workflows_pass_strict_yaml_lint(self, tmp_path: Path) -> None:
        """All real workflow projections are resolved and strict-lint clean."""
        root = self._render_project(tmp_path / "external")
        codegen = config.Infra.codegen
        override_name, checkout_mode = next(
            (name, mode)
            for name, mode in codegen.checkout_submodules_overrides.items()
            if mode != codegen.checkout_submodules
        )
        provider = codegen.providers[0]
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        context = m.Infra.GithubWorkflowRenderSpec(
            dist=override_name,
            repository_branch=provider.branch,
            promotion_branch=codegen.branch_policy.promotion_branch,
            python_version=codegen.toolchain.python_version,
            github_actions=codegen.github_actions,
            make=codegen.make,
            workspace_repositories=workspace.members,
            checkout_submodules=checkout_mode,
        )
        template_root = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / ".github"
            / "workflows"
        )
        workflow_root = root / ".github" / "workflows"
        for filename in ("docs.yml", "release.yml"):
            rendered = tm.ok(
                u.Cli.template_render(template_root / f"{filename}.j2", context)
            )
            (workflow_root / filename).write_text(rendered, encoding="utf-8")

        release_path = workflow_root / "release.yml"
        release_text = release_path.read_text(encoding="utf-8")
        submodule_lines = tuple(
            line.strip()
            for line in release_text.splitlines()
            if line.strip().startswith("submodules:")
        )
        tm.that(len(submodule_lines), eq=2)
        for line in submodule_lines:
            tm.that(line, eq=f"submodules: {checkout_mode}")
            tm.that(line, lacks="{{")
            tm.that(line, lacks="}}")

        yamllint_config = root / ".yamllint"
        tm.that(yamllint_config.is_file(), eq=True)
        lint = u.Cli.run_checked(
            [
                "yamllint",
                "--strict",
                "-c",
                yamllint_config.as_posix(),
                ".github/workflows/ci.yml",
                ".github/workflows/ci-matrix.yml",
                ".github/workflows/docs.yml",
                ".github/workflows/release.yml",
            ],
            cwd=root,
        )
        tm.ok(lint)

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
            "!uv.lock",
            "!.mise.toml",
            "!.python-version",
            "!.default-python-packages",
            "!config/",
            "!scripts/dispatch.py",
            "!ci/docker/",
        ):
            tm.that(content, has=marker)


__all__: list[str] = []
