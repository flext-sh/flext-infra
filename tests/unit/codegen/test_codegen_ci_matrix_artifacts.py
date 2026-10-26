"""Public contract for generated CI dependency, distro and host workflow artifacts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, tm, u
from tests.unit.codegen.ci_matrix_support import TestsFlextInfraCodegenCiMatrixSupport


@pytest.mark.slow
class TestsFlextInfraCodegenCiMatrixArtifacts(TestsFlextInfraCodegenCiMatrixSupport):
    """Prove generated dependency, distro and host workflow artifacts."""

    @staticmethod
    def _assert_dispatch_only(triggers: str) -> None:
        """Assert a workflow trigger section selects only manual dispatch."""
        tm.that(triggers, has="workflow_dispatch: {}")
        for forbidden in (
            "branches: [main]",
            "pull_request:",
            "ready_for_review",
            "repository_branch",
            "0.12.0-dev",
            "develop",
            "branches: [dev]",
        ):
            tm.that(triggers, lacks=forbidden)

    @staticmethod
    def test_fresh_render_projects_no_generated_ast_grep_rules(
        rendered_project: Path,
    ) -> None:
        """Generated ast-grep utilities and rules live only in memory.

        ``make mod`` renders them for its cascade, so a fresh render publishes
        none of them, while the same project still renders them in memory.
        """
        root = rendered_project.absolute()
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            rendered = u.Infra.codemod_native_generated(
                snapshot, root, config.Infra.codegen.ast_grep
            )
        tm.that(len(rendered.utilities), gt=0)
        for retired in config.Infra.codegen.retired_projections:
            if isinstance(retired, str) and retired.startswith("config/rules/ast-grep"):
                tm.that((root / retired).exists(), eq=False)

    @staticmethod
    def test_dependabot_applies_the_fleet_cooldown_everywhere(
        rendered_project: Path,
    ) -> None:
        """Every ecosystem entry carries the one configured cooldown."""
        root = rendered_project
        days = config.Infra.codegen.toolchain.dependency_cooldown_days

        document = u.Cli.yaml_load_mapping(root / ".github" / "dependabot.yml")
        updates = u.Cli.JSON_LIST_ADAPTER.validate_python(document["updates"])
        ecosystems = {
            str(u.Cli.JSON_MAPPING_ADAPTER.validate_python(item)["package-ecosystem"])
            for item in updates
        }
        tm.that(ecosystems, eq={"github-actions", "pip"})
        for item in updates:
            update = u.Cli.JSON_MAPPING_ADAPTER.validate_python(item)
            cooldown = u.Cli.JSON_MAPPING_ADAPTER.validate_python(update["cooldown"])
            tm.that(cooldown["default-days"], eq=days)

    @staticmethod
    def test_cooldown_exclusion_is_the_direct_git_requirement_set(
        tmp_path: Path,
    ) -> None:
        """Only requirements taken by direct reference are excluded."""
        pyproject = tmp_path / c.PYPROJECT_FILENAME
        pyproject.write_text(
            "[project]\n"
            'name = "example"\n'
            'version = "0.1.0"\n'
            "dependencies = [\n"
            '  "registry-package>=1.0",\n'
            '  "example-local @ git+https://example.invalid/local.git@main",\n'
            "]\n"
            "[dependency-groups]\n"
            'dev = ["example-fork @ git+https://example.invalid/fork.git@main"]\n',
            encoding="utf-8",
        )
        document = tm.ok(u.Cli.toml_read_document(pyproject))

        names = tm.ok(u.Infra.direct_source_names(document))

        tm.that(names, eq=("example-fork", "example-local"))

    @staticmethod
    def test_dependabot_cooldown_skips_forks_and_local_projects() -> None:
        """Git-referenced requirements are excluded from pip cooldowns only.

        Forks and local projects never enter the supply-chain cooldown; the
        exclusion rides the pip entries, while every entry keeps the one
        configured default-days.
        """
        excluded = ("example-fork", "example-local")
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-dist",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=u.CodegenTestSupport.Ci.ci_trigger_branches(
                "develop",
            ),
            overrides=u.CodegenTestSupport.Ci.WorkflowRenderOverrides(
                has_devcontainer=True,
                cooldown_excluded_dependencies=excluded,
            ),
        )
        days = config.Infra.codegen.toolchain.dependency_cooldown_days
        template = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/dependabot.yml.j2"
        )
        rendered = u.Cli.template_render(template, spec)
        tm.ok(rendered)
        rendered_text: str = rendered.value
        document = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.yaml_parse(rendered_text)),
        )
        updates = u.Cli.JSON_LIST_ADAPTER.validate_python(document["updates"])
        tm.that(len(updates), eq=3)
        for item in updates:
            update = u.Cli.JSON_MAPPING_ADAPTER.validate_python(item)
            cooldown = u.Cli.JSON_MAPPING_ADAPTER.validate_python(update["cooldown"])
            tm.that(cooldown["default-days"], eq=days)
            if update["package-ecosystem"] == "pip":
                tm.that(list(excluded), eq=cooldown["exclude"])
            else:
                tm.that(cooldown, lacks="exclude")

    @staticmethod
    def test_distro_dockerfiles_emitted(rendered_project: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = rendered_project
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

    @staticmethod
    def test_distro_bootstrap_is_fail_closed_and_self_contained(
        rendered_project: Path,
    ) -> None:
        """Every distro runs the canonical self-bootstrap fail-closed."""
        root = rendered_project
        # The matrix build declares the checkout's Git metadata as a named
        # build context; the Dockerfiles consume only that context by COPY.
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8",
        )
        tm.that(matrix, has="--build-context git=.git")
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
            tm.that(content, lacks="./bin/mise install --locked --yes")
            tm.that(content, has="RUN --mount=type=bind,source=.,target=/source,ro")
            tm.that(content, has="cp -R /source/. /workspace/")
            # The source tree arrives only through the read-only bind mount;
            # the one COPY brings .git from the named build context.
            copies = [line for line in content.splitlines() if line.startswith("COPY")]
            tm.that(len(copies), eq=1)
            tm.that(copies[0], has="--from=git")
            tm.that(copies[0], has="/workspace/.git/")
            tm.that(content, lacks="chmod -R a+rwX")
            # BuildKit exposes the credential only for the setup instruction.
            tm.that(content, lacks="ARG GITHUB_TOKEN")
            tm.that(content, lacks="ENV MISE_GITHUB_TOKEN=")
            tm.that(
                content,
                has="--mount=type=secret,id=github_token,env=GITHUB_TOKEN,required=true",
            )
            tm.that(content, lacks='GITHUB_TOKEN="')

    @staticmethod
    def test_dockerfiles_install_the_node_atomic_library_on_seed_bases(
        rendered_project: Path,
    ) -> None:
        """The apt and dnf seeds carry the atomic library the Node runtime needs."""
        root = rendered_project
        docker_dir = root / "tests" / "fixtures" / "ci" / "docker"
        for distro in ("ubuntu", "debian", "fedora"):
            content = (docker_dir / f"{distro}.Dockerfile").read_text(encoding="utf-8")
            tm.that(content, has="libatomic", msg=distro)
        for distro in ("alpine", "arch"):
            content = (docker_dir / f"{distro}.Dockerfile").read_text(encoding="utf-8")
            tm.that("libatomic" not in content, eq=True, msg=distro)

    @staticmethod
    def test_dockerfiles_render_byte_idempotently(rendered_project: Path) -> None:
        """Repeated project generation preserves the generated Dockerfiles."""
        root = rendered_project
        before = {
            distro: (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_bytes()
            for distro in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        TestsFlextInfraCodegenCiMatrixSupport.render_project(root)
        after = {
            distro: (
                root / "tests" / "fixtures" / "ci" / "docker" / f"{distro}.Dockerfile"
            ).read_bytes()
            for distro in before
        }
        tm.that(after, eq=before)

    @staticmethod
    def test_ci_matrix_has_only_supported_generic_legs(
        rendered_project: Path,
    ) -> None:
        """Generic Python CI emits only its complete cross-platform legs."""
        root = rendered_project
        workflow = root / ".github" / "workflows" / "ci-matrix.yml"
        tm.ok(workflow.is_file())
        content = u.Cli.yaml_load_mapping(workflow)
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(content["jobs"])
        for leg in ("distro-matrix", "macos", "windows"):
            tm.that(jobs, has=leg)
        tm.that(jobs, lacks="wsl")
        tm.that(jobs, lacks="kind")

    @staticmethod
    def test_host_legs_bootstrap_only_through_make_setup(
        rendered_project: Path,
    ) -> None:
        """MacOS and Windows bootstrap and run one lifecycle through Make."""
        root = rendered_project
        content = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8",
        )
        macos = content.split("\n  macos:", maxsplit=1)[1].split(
            "\n  windows:",
            maxsplit=1,
        )[0]
        windows = content.split("\n  windows:", maxsplit=1)[1]
        for host in (macos, windows):
            tm.that(host, has="run: CI=Y make setup")
        verbs = [re.findall(r"CI=Y make (\S+)", host) for host in (macos, windows)]
        tm.that(verbs[0], eq=verbs[1])
        tm.that(windows.count("shell: bash"), eq=windows.count("run:"))

    @staticmethod
    def test_runtime_jobs_supply_the_native_github_credential(
        rendered_project: Path,
    ) -> None:
        """Each Make job inherits a token; pure Git jobs require no extra input."""
        root = rendered_project
        for filename in ("ci.yml", "ci-matrix.yml"):
            workflow = u.Cli.yaml_load_mapping(
                root / ".github" / "workflows" / filename,
            )
            jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
            for value in jobs.values():
                job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(value)
                steps = u.Cli.JSON_LIST_ADAPTER.validate_python(job["steps"])
                commands = tuple(
                    step["run"]
                    for raw in steps
                    if (step := u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw)).get(
                        "run",
                    )
                )
                invokes_make = any(
                    isinstance(command, str) and re.search(r"\bmake\s", command)
                    for command in commands
                )
                if invokes_make:
                    environment = u.Cli.JSON_MAPPING_ADAPTER.validate_python(job["env"])
                    tm.that(environment["GITHUB_TOKEN"], eq="${{ github.token }}")
                elif "env" in job:
                    environment = u.Cli.JSON_MAPPING_ADAPTER.validate_python(job["env"])
                    tm.that(environment, lacks="GITHUB_TOKEN")

    def test_workflow_ci_policy_matrix_default_dispatch_only(
        self,
        rendered_project: Path,
    ) -> None:
        """Blocking CI covers integration; matrix defaults to dispatch-only."""
        root = rendered_project
        branch = u.Tests.provider_branch()
        blocking = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8",
        )
        integrations = config.Infra.codegen.branch_policy.ci_trigger_branches
        tm.that(integrations, has=branch)
        for integration in integrations:
            tm.that(blocking, has=f"      - {integration}")
        tm.that(blocking, has="draft == false")
        tm.that(blocking, has="ready_for_review")
        triggers = matrix.split("c.ParserBooleanToken.ON:", maxsplit=1)[1].split(
            "# End SECTION: triggers",
            maxsplit=1,
        )[0]
        self._assert_dispatch_only(triggers)

    @staticmethod
    def test_draft_selection_preserves_gate_jobs_without_subject_merge_lock(
        rendered_project: Path,
    ) -> None:
        """Workflow gates retain native results without a separate WIP veto."""
        workflow = tm.ok(
            u.Cli.yaml_parse(
                (rendered_project / ".github/workflows/ci.yml").read_text(
                    encoding="utf-8",
                ),
            ),
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
        ci = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["ci"])
        tm.that(ci["if"], has="github.event.pull_request.draft == false")
        tm.fail("merge-guard" in jobs)

    @staticmethod
    def test_docs_workflow_covers_every_blocking_ci_branch(
        rendered_project: Path,
    ) -> None:
        """Docs validation follows the same governed branch lanes as CI."""
        root = rendered_project
        content = (root / ".github" / "workflows" / "docs.yml").read_text(
            encoding="utf-8",
        )

        for branch in config.Infra.codegen.branch_policy.ci_trigger_branches:
            tm.that(content, has=f"      - {branch}")

    @staticmethod
    def test_ci_failure_upload_includes_its_hidden_report_paths(
        rendered_project: Path,
    ) -> None:
        """The artifact consumer includes declared reports and fails if absent."""
        workflow = u.Cli.yaml_load_mapping(
            rendered_project / ".github" / "workflows" / "ci.yml",
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
        action = config.Infra.codegen.github_actions["upload-artifact"]
        uploads = [
            step
            for payload in jobs.values()
            for step in (
                u.Cli.JSON_MAPPING_ADAPTER.validate_python(value)
                for value in u.Cli.JSON_LIST_ADAPTER.validate_python(
                    u.Cli.JSON_MAPPING_ADAPTER.validate_python(payload)["steps"],
                )
            )
            if step.get("uses") == f"{action.repository}@{action.version}"
        ]
        tm.that(uploads, empty=False)
        for upload in uploads:
            inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(upload["with"])
            paths = str(inputs["path"]).splitlines()
            tm.that(paths, empty=False)
            tm.that(
                any(
                    part.startswith(".") and part != "."
                    for path in paths
                    for part in Path(path).parts
                ),
                eq=True,
            )
            tm.that(inputs["include-hidden-files"], eq=True)
            tm.that(inputs["if-no-files-found"], eq="error")

    @staticmethod
    def test_docs_failure_upload_keeps_audit_failure_and_scopes_hidden_reports(
        rendered_project: Path,
    ) -> None:
        """A generated Docs job fails on audit findings and retains safe reports."""
        workflow = u.Cli.yaml_load_mapping(
            rendered_project / ".github" / "workflows" / "docs.yml",
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
        docs_job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["docs-quality"])
        steps = [
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(step)
            for step in u.Cli.JSON_LIST_ADAPTER.validate_python(docs_job["steps"])
        ]
        docs_step = next(
            step for step in steps if step.get("name") == "Docs lifecycle (blocking)"
        )
        upload = next(
            step
            for step in steps
            if step.get("name") == "Upload docs reports on failure"
        )
        tm.that(docs_step.get("run"), eq="make docs")
        tm.that(docs_step.get("continue-on-error"), eq=None)
        tm.that(upload["if"], eq="failure()")
        upload_with = u.Cli.JSON_MAPPING_ADAPTER.validate_python(upload["with"])
        tm.that(upload_with["include-hidden-files"], eq=True)
        tm.that(upload_with["if-no-files-found"], eq="error")
        report_paths = str(upload_with["path"]).splitlines()
        tm.that(report_paths, empty=False)
        tm.that(
            {Path(path).name for path in report_paths},
            eq=set(c.Infra.DOCS_STRUCTURED_REPORT_FILENAMES),
        )
        for path in report_paths:
            tm.ok(".reports" in Path(path).parts)

    @staticmethod
    def test_docs_workflow_jobs_authenticate_toolchain_resolution(
        rendered_project: Path,
    ) -> None:
        """Every Docs job running make setup resolves the toolchain authenticated.

        Shared-egress runners exhaust the anonymous REST budget before mise
        resolves the moving @latest backends, so each job that provisions the
        toolchain carries the job token exactly like blocking CI.
        """
        root = rendered_project
        content = (root / ".github" / "workflows" / "docs.yml").read_text(
            encoding="utf-8",
        )
        _, jobs = content.split("\njobs:\n", maxsplit=1)
        setup_jobs = [
            job for job in re.split(r"\n  (?=\S)", jobs) if "run: make setup" in job
        ]
        tm.that(setup_jobs, empty=False)
        for job in setup_jobs:
            tm.that(job, has="GITHUB_TOKEN: ${{ github.token }}")
            tm.that(job, lacks="MISE_GITHUB_TOKEN")

    @staticmethod
    def test_ci_matrix_runs_the_declared_lifecycle_on_every_distro(
        rendered_project: Path,
    ) -> None:
        """Every distro runs the ordered ci lifecycle steps, never a hand list."""
        root = rendered_project
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8",
        )
        make = config.Infra.codegen.make
        ci = make.ci
        smoke = matrix.split("Lifecycle acceptance (", maxsplit=1)[1].split(
            "# End SECTION: distro-matrix",
            maxsplit=1,
        )[0]
        tm.that(smoke, has=f"-e {ci.variable}={ci.value}")
        tm.that(smoke, has="-e GITHUB_TOKEN")
        tm.that(smoke, lacks="-e GITHUB_TOKEN=")
        tm.that(
            smoke,
            has=" && ".join(
                step.make_command
                for step in make.lifecycle_steps
                if "ci" in step.contexts
            ),
        )
        tm.that(smoke, lacks="make upg")
        dockerfiles = list(
            (root / "tests" / "fixtures" / "ci" / "docker").glob("*.Dockerfile"),
        )
        tm.ok(len(dockerfiles) > 0)
        for dockerfile in dockerfiles:
            body = dockerfile.read_text(encoding="utf-8")
            tm.that(body, has="ENV CI=Y")
            tm.that(body, has="make setup")
            tm.that(body, has="RUN --mount=type=secret")

    @staticmethod
    def test_makefile_normalizes_windows_runtime_paths(
        rendered_project: Path,
    ) -> None:
        """Generated POSIX Make resolves Windows uv and virtualenv executables."""
        root = rendered_project
        content = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(content, has="ifeq ($(OS),Windows_NT)")
        tm.that(content, has='cygpath --path "$(CALLER_PATH)"')
        tm.that(content, has="RUNTIME_BIN := $(RUNTIME_VENV)/Scripts")
        tm.that(content, has="RUNTIME_PYTHON := $(RUNTIME_BIN)/python.exe")
        tm.that(content, has="override PATH := $(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)")
        tm.that(
            content,
            has="_builtin-help:\n\t@printf '%s\\n' 'flext-demo [standalone]' '';",
        )


__all__: list[str] = ["TestsFlextInfraCodegenCiMatrixArtifacts"]
