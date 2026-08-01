"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm


class TestCodegenCiMatrix:
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def render_project(root: Path) -> Path:
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

    def test_ci_matrix_workflow_emitted(self, rendered_project: Path) -> None:
        """Generated project carries .github/workflows/ci-matrix.yml."""
        root = rendered_project
        tm.that((root / ".github" / "workflows" / "ci-matrix.yml").is_file(), eq=True)

    def test_standalone_workflows_do_not_checkout_private_submodules(
        self, rendered_project: Path
    ) -> None:
        """Standalone CI reaches runtime without sibling-repository credentials."""
        root = rendered_project
        workflows = tuple(
            (root / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            for filename in ("ci.yml", "ci-matrix.yml")
        )
        for workflow in workflows:
            tm.that(workflow, has="submodules: false")
            tm.that(workflow, lacks="submodules: recursive")

        template_root = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows"
        )
        for template in template_root.glob("*.yml.j2"):
            content = template.read_text(encoding="utf-8")
            if "submodules:" in content:
                tm.that(content, has="checkout_submodules")
                tm.that(content, lacks="submodules: recursive")

    def test_ci_workflow_uses_immutable_action_catalog(
        self, rendered_project: Path
    ) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = rendered_project
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
        tm.that(
            workflows, has=f'version: "{config.Infra.codegen.toolchain.mise_version}"'
        )

    def test_blocking_ci_bootstraps_only_through_make_setup(
        self, rendered_project: Path
    ) -> None:
        """Generated blocking CI provisions every binary via the Make surface."""
        root = rendered_project
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        lifecycle = config.Infra.codegen.github_actions_workflows.lifecycle
        for step in lifecycle:
            command = f"make {step.verb}{' APPLY=Y' if step.apply else ''} CI=Y"
            tm.that(workflow.count(f"run: {command}"), eq=1)

    def test_docs_workflow_template_uses_default_all_make_contract(self) -> None:
        """Workspace docs CI delegates the complete lifecycle to Make."""
        root = Path(__file__).resolve().parents[3]
        workflow = (
            root
            / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
        ).read_text(encoding="utf-8")

        tm.that(workflow, has="github_actions_workflows.docs_verb")
        tm.that(workflow, lacks="WHAT=")
        tm.that(workflow, lacks="DOCS_PHASE=")

    def test_workflow_make_calls_explicitly_use_ci_mode(self) -> None:
        """Every generated workflow enters lifecycle verbs through CI=Y."""
        root = Path(__file__).resolve().parents[3]
        workflow_templates = (
            root / "src/flext_infra/templates/project/base/.github"
        ).glob("**/*.yml.j2")
        make_lines = tuple(
            line.strip()
            for template in workflow_templates
            for line in template.read_text(encoding="utf-8").splitlines()
            if "make " in line and not line.lstrip().startswith("#")
        )
        tm.that(make_lines, empty=False)
        for line in make_lines:
            tm.that(line, has="CI=Y")
            tm.that(line, lacks="WHAT=")
            tm.that(line, lacks="RELEASE_PHASE=")

    def test_rendered_ci_jobs_call_each_make_lifecycle_verb_once(
        self, rendered_workspace: Path
    ) -> None:
        """Each rendered CI job delegates once to every lifecycle Make verb."""
        lifecycle = tuple(
            f"make {step.verb}{' APPLY=Y' if step.apply else ''} CI=Y"
            for step in config.Infra.codegen.github_actions_workflows.lifecycle
        )
        forbidden_tools = (
            "mise exec",
            "uv ",
            "ruff ",
            "pytest ",
            "mypy ",
            "pyright ",
            "pyrefly ",
        )
        workflows = (
            rendered_workspace / ".github" / "ci-template" / "ci.yml",
            *(rendered_workspace / ".github" / "workflows").glob("*.yml"),
        )
        for workflow in workflows:
            payload = u.Cli.yaml_load_mapping(workflow)
            jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["jobs"])
            for job in jobs.values():
                job_payload = t.Cli.JSON_MAPPING_ADAPTER.validate_python(job)
                steps = t.Cli.JSON_LIST_ADAPTER.validate_python(job_payload["steps"])
                commands = "\n".join(
                    str(step_payload["run"])
                    for step in steps
                    if "run"
                    in (
                        step_payload := t.Cli.JSON_MAPPING_ADAPTER.validate_python(step)
                    )
                )
                for command in lifecycle:
                    tm.that(commands.count(command), eq=1, msg=str(workflow))
                for tool in forbidden_tools:
                    tm.that(commands, lacks=tool)

    def test_rendered_delivery_uses_owned_verbs_and_artifact_path_once(
        self, rendered_workspace: Path
    ) -> None:
        """Docs and release consume only their typed Make and artifact owners."""
        policy = config.Infra.codegen.github_actions_workflows
        docs_path = rendered_workspace / ".github" / "workflows" / "docs.yml"
        release_path = rendered_workspace / ".github" / "workflows" / "release.yml"
        docs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            u.Cli.yaml_load_mapping(docs_path)["jobs"]
        )
        release = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            u.Cli.yaml_load_mapping(release_path)["jobs"]
        )
        docs_job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(next(iter(docs.values())))
        release_job = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            next(iter(release.values()))
        )
        docs_steps = t.Cli.JSON_LIST_ADAPTER.validate_python(docs_job["steps"])
        release_steps = t.Cli.JSON_LIST_ADAPTER.validate_python(release_job["steps"])
        docs_commands = "\n".join(
            str(step["run"])
            for raw_step in docs_steps
            if "run" in (step := t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step))
        )
        release_commands = "\n".join(
            str(step["run"])
            for raw_step in release_steps
            if "run" in (step := t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step))
        )
        tm.that(docs_commands.count(f"make {policy.docs_verb} CI=Y"), eq=1)
        tm.that(release_commands.count(f"make {policy.release_verb} CI=Y"), eq=1)
        upload = next(
            t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step)
            for raw_step in docs_steps
            if config.Infra.codegen.github_actions["upload-pages-artifact"].repository
            in str(raw_step)
        )
        upload_with = t.Cli.JSON_MAPPING_ADAPTER.validate_python(upload["with"])
        tm.that(upload_with["path"], eq=policy.docs_artifact_path)

    def test_workflow_templates_only_allow_governed_promotions(self) -> None:
        """Every Actions template rejects push, manual, and scheduled execution."""
        root = Path(__file__).resolve().parents[3]
        github_templates = root / "src/flext_infra/templates/project/base/.github"
        templates = (
            github_templates / "ci-template" / "ci.yml.j2",
            *(github_templates / "workflows").glob("*.yml.j2"),
        )
        tm.that(templates, empty=False)
        for template in templates:
            content = template.read_text(encoding="utf-8")
            tm.that(content, has="github_actions_promotion.target")
            tm.that(content, has="github.head_ref")
            tm.that(content, lacks="workflow_dispatch")
            tm.that(content, lacks="\n  push:")
            tm.that(content, lacks="\n  schedule:")

        for name in ("docs.yml.j2", "release.yml.j2"):
            content = next(path for path in templates if path.name == name).read_text(
                encoding="utf-8"
            )
            tm.that(content, has="github_actions_workflows.delivery_event_types")
            tm.that(content, has="github.event.pull_request.merged == true")
        release = next(
            path for path in templates if path.name == "release.yml.j2"
        ).read_text(encoding="utf-8")
        tm.that(release, has="github_actions_workflows.release_verb")
        tm.that(release, lacks="run: make rel CI=Y")

    def test_ci_uses_typed_action_catalog(self, rendered_project: Path) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = rendered_project
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

    def test_distro_dockerfiles_emitted(self, rendered_project: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = rendered_project
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            tm.that(
                (root / "ci" / "docker" / f"{distro}.Dockerfile").is_file(), eq=True
            )

    def test_distro_images_defer_the_single_lifecycle_to_the_workflow(
        self, rendered_project: Path
    ) -> None:
        """Distro images never duplicate the workflow-owned Make lifecycle."""
        root = rendered_project
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            content = (root / "ci" / "docker" / f"{distro}.Dockerfile").read_text(
                encoding="utf-8"
            )
            tm.that(content, lacks="make setup")
            tm.that(content, lacks="UV_UNMANAGED_INSTALL")
            tm.that(content, lacks="uv python install")
            tm.that(content, lacks="set +e")
            tm.that(content, lacks="soft-pass")
            tm.that(content, lacks="go.dev/dl/")
            tm.that(content, lacks="rustup.rs")
            tm.that(
                content,
                has=f'MISE_VERSION="v{config.Infra.codegen.toolchain.mise_version}"',
            )
            if distro == "alpine":
                tm.that(content, has="bash")
                tm.that(content, has="build-base")

    def test_mise_toolchain_declares_portable_build_dependencies(
        self, rendered_project: Path
    ) -> None:
        """Generated mise config orders portable Python, Rust, Go, and CLIs."""
        root = rendered_project
        mapping = u.Cli.toml_mapping_from_text(
            (root / ".mise.toml").read_text(encoding="utf-8")
        )
        tm.that(mapping is not None, eq=True)
        tools = u.Cli.toml_mapping_child(mapping or {}, "tools")
        tm.that(tools is not None, eq=True)
        toolchain = config.Infra.codegen.toolchain
        tool_map = tools or {}
        python = t.Cli.JSON_MAPPING_ADAPTER.validate_python(tool_map["python"])
        ast_grep = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tool_map[toolchain.ast_grep_selector]
        )
        beads = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tool_map[toolchain.beads.selector]
        )

        tm.that(python["version"], eq=toolchain.python_version)
        tm.that(python["install_env"], has="MISE_PYTHON_COMPILE")
        tm.that(tool_map["go"], eq=toolchain.go_version)
        tm.that(tool_map["rust"], eq=toolchain.rust_version)
        tm.that(ast_grep["depends"], has="rust")
        tm.that(ast_grep["install_env"], has="CARGO_TERM_QUIET")
        tm.that(beads["depends"], has="go")
        tm.that(beads["install_env"], has="CGO_ENABLED")

    def test_fedora_dockerfile_installs_libatomic_only_for_fedora(
        self, rendered_project: Path
    ) -> None:
        """Fedora's generated Node runtime has its required atomic library."""
        root = rendered_project
        fedora = (root / "ci" / "docker" / "fedora.Dockerfile").read_text(
            encoding="utf-8"
        )
        tm.that(fedora, has="libatomic")
        for distro in ("ubuntu", "debian", "alpine", "arch"):
            content = (root / "ci" / "docker" / f"{distro}.Dockerfile").read_text(
                encoding="utf-8"
            )
            tm.that("libatomic" not in content, eq=True, msg=distro)

    def test_dockerfiles_render_byte_idempotently(self, rendered_project: Path) -> None:
        """Repeated project generation preserves the generated Dockerfiles."""
        root = rendered_project
        before = {
            distro: (root / "ci" / "docker" / f"{distro}.Dockerfile").read_bytes()
            for distro in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        self.render_project(root)
        after = {
            distro: (root / "ci" / "docker" / f"{distro}.Dockerfile").read_bytes()
            for distro in before
        }
        tm.that(after, eq=before)

    def test_ci_matrix_has_only_supported_generic_legs(
        self, rendered_project: Path
    ) -> None:
        """Generic Python CI emits only its complete cross-platform legs."""
        root = rendered_project
        workflow = root / ".github" / "workflows" / "ci-matrix.yml"
        tm.that(workflow.is_file(), eq=True)
        content = u.Cli.yaml_load_mapping(workflow)
        jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(content["jobs"])
        for leg in ("distro-matrix", "macos", "windows"):
            tm.that(jobs, has=leg)
        tm.that(jobs, lacks="wsl")
        tm.that(jobs, lacks="kind")

    def test_generated_workflows_pass_strict_yamllint(
        self, rendered_workspace: Path
    ) -> None:
        """Rendered workflows satisfy YAML indentation with warnings as errors."""
        root = rendered_workspace
        lint = u.Cli.run_checked(
            [
                "yamllint",
                "--strict",
                "--config-data",
                (
                    "{extends: default, rules: {document-start: disable, "
                    "line-length: disable}}"
                ),
                ".github",
            ],
            cwd=root,
        )
        tm.ok(lint)

    def test_host_legs_bootstrap_only_through_make_setup(
        self, rendered_project: Path
    ) -> None:
        """MacOS and Windows bootstrap through the same Make surface."""
        root = rendered_project
        content = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        macos = content.split("\n  macos:", maxsplit=1)[1].split(
            "\n  windows:", maxsplit=1
        )[0]
        windows = content.split("\n  windows:", maxsplit=1)[1]
        lifecycle = tuple(
            f"make {step.verb}{' APPLY=Y' if step.apply else ''} CI=Y"
            for step in config.Infra.codegen.github_actions_workflows.lifecycle
        )
        for host in (macos, windows):
            positions = tuple(host.index(f"run: {command}") for command in lifecycle)
            tm.that(positions, eq=tuple(sorted(positions)))
            tm.that(host, lacks="mise exec")
        distro = content.split("\n  distro-matrix:", maxsplit=1)[1].split(
            "\n  macos:", maxsplit=1
        )[0]
        for command in lifecycle:
            tm.that(distro, has=command)
        tm.that(windows.count("shell: bash"), eq=windows.count("\n        run:"))

    def test_rendered_workflows_only_trigger_governed_promotion(
        self, rendered_project: Path
    ) -> None:
        """Rendered CI accepts only configured source branches into main."""
        root = rendered_project
        promotion = config.Infra.codegen.github_actions_promotion
        for filename in ("ci.yml", "ci-matrix.yml"):
            workflow = root / ".github" / "workflows" / filename
            content = workflow.read_text(encoding="utf-8")
            payload = u.Cli.yaml_load_mapping(workflow)
            events = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["on"])
            pull_request = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                events["pull_request"]
            )
            jobs = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["jobs"])

            tm.that(tuple(events), eq=("pull_request",))
            tm.that(pull_request["branches"], eq=[promotion.target])
            tm.that(
                pull_request["types"],
                eq=list(
                    config.Infra.codegen.github_actions_workflows.validation_event_types
                ),
            )
            tm.that(content, lacks="workflow_dispatch")
            tm.that(content, lacks="\n  push:")
            for job in jobs.values():
                job_payload = t.Cli.JSON_MAPPING_ADAPTER.validate_python(job)
                condition = str(job_payload["if"])
                tm.that(condition, has=promotion.target)
                for source in promotion.sources:
                    tm.that(condition, has=source)

    def test_makefile_normalizes_windows_runtime_paths(
        self, rendered_project: Path
    ) -> None:
        """Generated POSIX Make resolves Windows uv and virtualenv executables."""
        root = rendered_project
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
            "!README.md",
            "!config/",
            "!scripts/dispatch.py",
            "!ci/docker/",
        ):
            tm.that(content, has=marker)


@pytest.fixture(scope="module")
def rendered_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Render the immutable project fixture once for this contract module."""
    return TestCodegenCiMatrix.render_project(
        tmp_path_factory.mktemp("ci-matrix") / "external"
    )


@pytest.fixture(scope="module")
def rendered_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Render all workspace-root workflows through the production planner."""
    root = TestCodegenCiMatrix.render_project(
        tmp_path_factory.mktemp("ci-workspace") / "workspace"
    )
    workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
    repository = workspace.repository.model_copy(
        update={
            "role": c.Infra.RepositoryRole.WORKSPACE_ROOT,
            "profile": c.Infra.MakeProfile.WORKSPACE_ROOT,
            "checkout": c.Infra.CheckoutKind.ROOT,
            "path": Path(),
            "package": False,
            "editable": False,
        }
    )
    workspace = workspace.model_copy(update={"repository": repository})
    request = m.Infra.CodegenConformRequest(
        root=root,
        scope=c.Infra.CodegenConformScope.SELF,
        mode=c.Infra.CodegenConformMode.CHECK,
    )
    plan = tm.ok(
        FlextInfraCodegenConform(
            workspace_root=root, request=request, initial_workspace=workspace
        ).plan(request)
    )
    for planned in plan.files:
        if planned.path.parts[:1] != (".github",) or planned.path.suffix != ".yml":
            continue
        destination = root / planned.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(planned.rendered, encoding="utf-8")
    return root


__all__: list[str] = []
