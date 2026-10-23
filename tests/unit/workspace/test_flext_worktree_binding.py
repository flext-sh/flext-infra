"""The explicit binding CLI rebinds a consumer onto one flext checkout.

An external project declares flext packages by pinned git URL, so it validates
PUBLISHED code and never the checkout being worked on. Reviewing a cross-project
change then required publishing first, which is backwards.

The binding is a SESSION override, not a declaration: the consumer's
``pyproject.toml`` keeps its pins untouched, so nothing local is ever committed
and canonical setup restores the pinned resolution. Which distributions get
rebound is derived from the worktree's own manifest, never a hardcoded list.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import sysconfig
from collections.abc import Callable
from pathlib import Path

from flext_infra import config, workspace
from tests import c, m, tm, u


class TestsFlextInfraWorktreeBinding:
    """The service resolves which distributions a worktree can supply."""

    @staticmethod
    def _declare_supplier_packaging(root: Path) -> None:
        """Make fixture suppliers genuine native package participants."""
        path = root / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(path.read_text(encoding=c.DEFAULT_ENCODING))
        build = config.Infra.codegen.scaffold.build
        document["build-system"] = {
            "requires": list(build.requirements),
            "build-backend": build.backend,
        }
        tm.ok(u.Cli.atomic_write_text_file(path, u.Cli.toml_dumps(document)))

    @staticmethod
    def test_local_supplier_opt_in_selects_an_isolated_resolution(
        tmp_path: Path,
        editable_supplier: Callable[[Path | None], None],
    ) -> None:
        """Local configuration elects a dev lock, never another environment."""
        consumer = TestsFlextInfraWorktreeBinding._consumer(tmp_path)
        supplier = TestsFlextInfraWorktreeBinding._flext_workspace(tmp_path)
        default = tm.ok(
            workspace.FlextInfraWorkspaceDetector.resolution_context(consumer)
        )
        editable_supplier(supplier)
        inputs = tm.ok(u.Infra.load_codegen_inputs(consumer))
        selected = tm.ok(
            workspace.FlextInfraWorkspaceDetector.resolution_context(consumer)
        )
        tm.that(selected.editable_supplier_root, eq=supplier.resolve())
        supplier_runtime = tm.ok(
            workspace.FlextInfraWorkspaceDetector.resolution_context(supplier)
        )
        tm.that(supplier_runtime.editable_supplier_root, eq=None)
        tm.that(selected.environment_path, eq=default.environment_path)
        tm.that(
            selected.lock_path,
            eq=consumer
            / inputs.spec.make.uv_resolution.editable_directory
            / c.Infra.UV_LOCK_FILENAME,
        )
        tm.fail(selected.lock_path == default.lock_path)
        artifact = next(
            item
            for item in inputs.spec.managed_file_specs
            if item.path
            == inputs.spec.make.uv_resolution.editable_directory / c.PYPROJECT_FILENAME
        )
        tm.that(artifact.tracking, eq="runtime-local")

    @staticmethod
    def _consumer(tmp_path: Path) -> Path:
        """Return an external consumer declaring flext packages by pinned git URL.

        Returns:
            An external consumer declaring flext packages by pinned git URL.

        """
        provider = u.Tests.provider()
        consumer = tmp_path / "consumer"
        consumer.mkdir()
        (consumer / c.PYPROJECT_FILENAME).write_text(
            "[project]\n"
            'name = "consumer"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13"\n'
            "dependencies = [\n"
            f'  "flext-core @ git+{provider.base_url.rstrip("/")}/flext-core.git@'
            f'{u.Tests.provider_branch()}",\n'
            f'  "flext-cli @ git+{provider.base_url.rstrip("/")}/flext-cli.git@'
            f'{u.Tests.provider_branch()}",\n'
            '  "httpx>=0.27",\n'
            "]\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(consumer)
        tm.ok(u.Tests.create_python_environment(consumer))
        return consumer

    @staticmethod
    def _python(consumer: Path) -> Path:
        """Use the fixture consumer's physical environment.

        Returns:
            The resulting ``Path``.

        """
        environment = u.Infra.runtime_environment_dir(consumer)
        return (
            Path(
                sysconfig.get_path(
                    "scripts",
                    scheme="venv",
                    vars={"base": str(environment), "platbase": str(environment)},
                ),
            )
            / c.Infra.PromotedSelector.VENV_PYTHON
        )

    @staticmethod
    def _flext_workspace(tmp_path: Path) -> Path:
        """Return a self-contained flext workspace supplying flext-core and flext-cli.

        Built here rather than pointed at a real checkout so the test states its
        own premise: the rebind set is the intersection of what the consumer
        declares with what the worktree PROVIDES, and only a fixture that owns
        both sides can prove the intersection rather than inherit it from one
        machine's disk.

        Returns:
            A self-contained flext workspace supplying flext-core and flext-cli.

        """
        flext_root = tmp_path / "flext"
        u.Tests.WorktreeFixture.initialize_governed_project(
            flext_root,
            "flext",
            beads=u.Tests.BeadsIdentity(
                workspace="flext",
                database="flext",
                issue_prefix="flext",
            ),
        )
        for name in ("flext-core", "flext-cli"):
            u.Tests.WorktreeFixture.initialize_governed_project(
                flext_root / name,
                name,
                beads=u.Tests.BeadsIdentity(
                    workspace=name,
                    database=name,
                    issue_prefix=name,
                ),
                beads_owner=False,
            )
            u.Tests.WorktreeFixture.link_member_beads(
                flext_root / name,
                flext_root,
                workspace_name="flext",
                database="flext",
                issue_prefix="flext",
            )
            TestsFlextInfraWorktreeBinding._declare_supplier_packaging(
                flext_root / name
            )
        u.Tests.WorktreeFixture.write_gitmodules(
            flext_root,
            ("flext-core", "flext-cli"),
        )
        return flext_root

    def test_binding_targets_only_the_flext_packages_the_consumer_declares(
        self,
        tmp_path: Path,
    ) -> None:
        """Only declared flext deps present in the worktree are rebound."""
        consumer = self._consumer(tmp_path)

        planned = workspace.FlextInfraBindingService.plan_targets(
            consumer_root=consumer,
            flext_root=self._flext_workspace(tmp_path),
            python=self._python(consumer),
        )

        names = tm.ok(planned)
        tm.that(sorted(names), eq=["flext-cli", "flext-core"])

    def test_standalone_supplier_satisfies_a_development_dependency(
        self,
        tmp_path: Path,
    ) -> None:
        """A root-only supplier checkout serves a consumer's declared dev group."""
        distribution = config.Infra.codegen.infra_repository.distribution
        supplier = tmp_path / "supplier"
        u.Tests.WorktreeFixture.initialize_governed_project(
            supplier,
            distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=distribution,
                database=distribution,
                issue_prefix=distribution,
            ),
        )
        self._declare_supplier_packaging(supplier)
        consumer = self._consumer(tmp_path)
        declaration = consumer / c.PYPROJECT_FILENAME
        with declaration.open("a", encoding=c.DEFAULT_ENCODING) as stream:
            stream.write(f'[dependency-groups]\ndev = ["{distribution}"]\n')
        before = declaration.read_bytes()

        planned = workspace.FlextInfraBindingService.plan_targets(
            consumer_root=consumer,
            flext_root=supplier,
            python=self._python(consumer),
        )

        tm.that(tuple(tm.ok(planned)), eq=(distribution,))
        tm.that(declaration.read_bytes(), eq=before)

    def test_binding_rejects_a_path_that_is_not_a_flext_workspace(
        self,
        tmp_path: Path,
    ) -> None:
        """A non-workspace path fails closed instead of silently binding nothing."""
        consumer = self._consumer(tmp_path)
        not_flext = tmp_path / "elsewhere"
        not_flext.mkdir()

        planned = workspace.FlextInfraBindingService.plan_targets(
            consumer_root=consumer,
            flext_root=not_flext,
            python=self._python(consumer),
        )

        tm.ok(planned.failure)
        tm.that(planned.error or "", has="workspace")

    def test_a_consumer_without_flext_dependencies_rejects_empty_binding(
        self,
        tmp_path: Path,
    ) -> None:
        """An explicit request cannot succeed without selecting a supplier."""
        consumer = tmp_path / "plain"
        consumer.mkdir()
        (consumer / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "plain"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13"\ndependencies = ["httpx>=0.27"]\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(consumer)
        tm.ok(u.Tests.create_python_environment(consumer))

        planned = workspace.FlextInfraBindingService.plan_targets(
            consumer_root=consumer,
            flext_root=self._flext_workspace(tmp_path),
            python=self._python(consumer),
        )

        tm.ok(planned.failure)
        tm.that(planned.error or "", has="no active declared dependency")

    def test_binding_rejects_foreign_interpreter(self, tmp_path: Path) -> None:
        """A valid supplier cannot redirect installation to the running agent."""
        consumer = self._consumer(tmp_path)
        result = workspace.FlextInfraBindingService.consumer_marker_environment(
            consumer_root=consumer,
            python=Path(sys.executable),
        )
        tm.ok(result.failure)
        tm.that(result.error or "", has="must belong to the consumer")

    def test_consumer_markers_match_the_actual_interpreter(
        self,
        tmp_path: Path,
    ) -> None:
        """Marker selection uses full consumer interpreter facts."""
        consumer = self._consumer(tmp_path)
        facts = tm.ok(
            workspace.FlextInfraBindingService.consumer_marker_environment(
                consumer_root=consumer,
                python=self._python(consumer),
            ),
        )
        for key in ("python_full_version", "implementation_version", "sys_platform"):
            requirement = f"binding-candidate; {key} == '{facts[key]}'"
            tm.that(
                u.Infra.active_requirement(requirement, environment=facts),
                none=False,
            )
        tm.that(
            u.Infra.active_requirement(
                "binding-candidate; python_version < '0'",
                environment=facts,
            ),
            none=True,
        )

    @staticmethod
    def test_ci_binding_rejects_before_consumer_or_supplier_access(
        tmp_path: Path,
    ) -> None:
        """The real public CLI rejects CI before any environment mutation."""
        ci = config.Infra.codegen.make.ci
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "workspace",
                    "flext-binding",
                    "--repository-root",
                    str(tmp_path / "consumer"),
                    "--flext-root",
                    str(tmp_path / "supplier"),
                    "--python",
                    str(tmp_path / "python"),
                ),
                options=m.Cli.ProcessOptions(env={ci.variable: ci.value}),
            ),
        )
        tm.ok(result.outcome.raw_return_code != 0)
        tm.that(
            f"{result.stdout}{result.stderr}",
            has=f"prohibited with {ci.variable}={ci.value}",
        )
        tm.that(tuple(tmp_path.iterdir()), eq=())
