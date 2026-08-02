"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, config, m, t, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_tests import tm


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
            tm.that(workflows, has=f"{action} # {catalog[action]}")

        tm.that(workflows, lacks="continue-on-error")
        tm.that(workflows, lacks="set +e")
        tm.that(workflows, lacks="|| make")
        tm.that(workflows, lacks="soft-pass")

    def test_blocking_ci_installs_declared_toolchain_before_make(
        self, tmp_path: Path
    ) -> None:
        """Generated blocking CI provides every binary consumed by canonical Make."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        mise_action = config.Infra.codegen.github_actions["mise"]
        install = f"{mise_action.repository}@{mise_action.sha}"

        tm.that(workflow, has=install)
        tm.that(workflow.index(install), lt=workflow.index("run: make setup"))

    def test_blocking_ci_runs_complete_suite_as_typed_xdist_shards(
        self, tmp_path: Path
    ) -> None:
        """Blocking CI partitions the full collection and verifies its exact union."""
        root = self._render_project(tmp_path / "external")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        pytest_policy = config.Infra.codegen.ci.pytest
        matrix = ", ".join(str(index) for index in range(pytest_policy.shard_count))
        expected_args = (
            f"--flext-shard-count {pytest_policy.shard_count}",
            f"--flext-shard-max-workers {pytest_policy.max_workers_per_shard}",
            f"--flext-shard-assignment {pytest_policy.assignment}",
            f"--dist={pytest_policy.distribution}",
        )

        tm.that(workflow, has=f"shard: [{matrix}]")
        for expected in expected_args:
            tm.that(workflow, has=expected)
        tm.that(workflow, has=f"-n {pytest_policy.max_workers_per_shard}")
        tm.that(workflow, has="--flext-shard-manifest")
        tm.that(workflow, has="-p flext_infra.pytest_shard")
        tm.that(workflow, has="PYTEST_DISABLE_PLUGIN_AUTOLOAD=1")
        tm.that(workflow, has="-p xdist.plugin")
        tm.that(workflow, has="-p pytest_cov.plugin")
        tm.that(workflow, has="-p pytest_timeout")
        tm.that(
            workflow,
            has=f"PYTEST_REPORTS_DIR: {pytest_policy.reports_dir}/test-reports/shard-",
        )
        tm.that(workflow, has="make test WHAT=shard")
        tm.that(workflow, has="run: make test WHAT=aggregate")
        tm.that(workflow, has="\n  ci:\n    name: ci\n")
        tm.that(workflow, has="merge-multiple: true")
        tm.that(workflow, has="include-hidden-files: true")
        tm.that(workflow.count("run: make test"), eq=1)
        tm.that(workflow, lacks="FILE=")
        tm.that(workflow, lacks="FILES=")
        tm.that(workflow, lacks="MATCH=")
        tm.that(workflow, lacks="--no-cov")
        tm.that(workflow, lacks="--cov-fail-under=0")
        tm.that(workflow, lacks=".venv/bin/python")

        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, has="_builtin_test_shard")
        tm.that(makefile, has="_builtin_test_aggregate")
        tm.that(makefile, has="validate pytest-shards")
        tm.that(
            makefile,
            has=f"PYTEST_SHARD_COVERAGE_CONFIG ?= {pytest_policy.collection_config}",
        )

        coverage_config = (root / pytest_policy.collection_config).read_text(
            encoding="utf-8"
        )
        for source in config.Infra.tooling.tools.coverage.source:
            tm.that(coverage_config, has=f'"{source}"')
        for omitted in config.Infra.tooling.tools.coverage.omit:
            tm.that(coverage_config, has=f'"{omitted}"')
        tm.that(coverage_config, lacks="fail_under")
        tm.that(coverage_config, lacks="[report]")

    def test_ci_pytest_policy_rejects_serial_or_unsupported_schedulers(self) -> None:
        """Typed CI policy cannot regress to serial or duplicate-suite execution."""
        pytest_policy = config.Infra.codegen.ci.pytest

        with pytest.raises(ValueError, match="shard_count"):
            m.Infra.CiPytestSpec.model_validate({
                "shard_count": 1,
                "max_workers_per_shard": pytest_policy.max_workers_per_shard,
                "distribution": pytest_policy.distribution,
                "assignment": pytest_policy.assignment,
                "reports_dir": pytest_policy.reports_dir,
                "collection_config": pytest_policy.collection_config,
                "coverage_output": pytest_policy.coverage_output,
                "summary_output": pytest_policy.summary_output,
            })
        with pytest.raises(ValueError, match="distribution"):
            m.Infra.CiPytestSpec.model_validate({
                "shard_count": pytest_policy.shard_count,
                "max_workers_per_shard": pytest_policy.max_workers_per_shard,
                "distribution": "each",
                "assignment": pytest_policy.assignment,
                "reports_dir": pytest_policy.reports_dir,
                "collection_config": pytest_policy.collection_config,
                "coverage_output": pytest_policy.coverage_output,
                "summary_output": pytest_policy.summary_output,
            })
        with pytest.raises(ValueError, match="assignment"):
            m.Infra.CiPytestSpec.model_validate({
                "shard_count": pytest_policy.shard_count,
                "max_workers_per_shard": pytest_policy.max_workers_per_shard,
                "distribution": pytest_policy.distribution,
                "assignment": "python-hash",
                "reports_dir": pytest_policy.reports_dir,
                "collection_config": pytest_policy.collection_config,
                "coverage_output": pytest_policy.coverage_output,
                "summary_output": pytest_policy.summary_output,
            })
        with pytest.raises(ValueError, match="repository-relative"):
            m.Infra.CiPytestSpec.model_validate({
                "shard_count": pytest_policy.shard_count,
                "max_workers_per_shard": pytest_policy.max_workers_per_shard,
                "distribution": pytest_policy.distribution,
                "assignment": pytest_policy.assignment,
                "reports_dir": pytest_policy.reports_dir,
                "collection_config": pytest_policy.collection_config,
                "coverage_output": "../coverage.xml",
                "summary_output": pytest_policy.summary_output,
            })

    def test_distro_dockerfiles_emitted(self, tmp_path: Path) -> None:
        """Generated project carries one Dockerfile per supported distro."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            tm.that(
                (root / "ci" / "docker" / f"{distro}.Dockerfile").is_file(), eq=True
            )

    def test_distro_bootstrap_is_fail_closed_and_provisions_uv(
        self, tmp_path: Path
    ) -> None:
        """Every distro provisions uv, Node, and canonical bootstrap fail-closed."""
        root = self._render_project(tmp_path / "external")
        for distro in ("ubuntu", "debian", "fedora", "alpine", "arch"):
            content = (root / "ci" / "docker" / f"{distro}.Dockerfile").read_text(
                encoding="utf-8"
            )
            tm.that(content, has="UV_UNMANAGED_INSTALL=/usr/local/bin")
            tm.that(content, has="RUN uv python install 3.13")
            tm.that(content, has="RUN make setup")
            tm.that(content, has="nodejs")
            tm.that(content.index("nodejs"), lt=content.index("RUN make setup"))
            tm.that(content, lacks="mise install")
            tm.that(content, lacks="set +e")
            tm.that(content, lacks="soft-pass")
            tm.that(content, lacks="EXTERNAL BLOCKER")
            if distro == "alpine":
                tm.that(content, has="coreutils")
                tm.that(content, has="util-linux-misc")

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

    def test_host_bootstrap_provisions_python_uv_and_declared_tools(
        self, tmp_path: Path
    ) -> None:
        """MacOS and Windows receive every executable needed before Make."""
        root = self._render_project(tmp_path / "external")
        content = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        actions = config.Infra.codegen.github_actions
        expected = tuple(
            f"{actions[name].repository}@{actions[name].sha}"
            for name in ("setup-python", "setup-uv", "mise")
        )
        macos = content.split("\n  macos:", maxsplit=1)[1].split(
            "\n  windows:", maxsplit=1
        )[0]
        windows = content.split("\n  windows:", maxsplit=1)[1]
        for host in (macos, windows):
            for action in expected:
                tm.that(host, has=action)
            tm.that(host.index(expected[0]), lt=host.index("run: make setup"))
            tm.that(host.index(expected[1]), lt=host.index("run: make setup"))
        tm.that(windows.count("shell: bash"), eq=2)

    def test_workflow_branches_derive_from_workspace_manifest(
        self, tmp_path: Path
    ) -> None:
        """Generated workflows consume the repository branch topology owner."""
        root = self._render_project(tmp_path / "external")
        manifest = u.Cli.yaml_load_mapping(root / "config" / "workspace.yaml")
        repository = t.Cli.JSON_MAPPING_ADAPTER.validate_python(manifest["repository"])
        branch = str(repository["branch"])
        blocking = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        matrix = (root / ".github" / "workflows" / "ci-matrix.yml").read_text(
            encoding="utf-8"
        )
        tm.that(blocking, has=f"      - {branch}")
        tm.that(matrix, has=f"branches: [{branch}]")
        tm.that(blocking, lacks="      - main")
        tm.that(matrix, lacks="branches: [main]")

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


__all__: list[str] = []
