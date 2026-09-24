"""``FLEXT=<worktree>`` rebinds an external consumer onto one flext checkout.

An external project declares flext packages by pinned git URL, so it validates
PUBLISHED code and never the checkout being worked on. Reviewing a cross-project
change then required publishing first, which is backwards.

The binding is a SESSION override, not a declaration: the consumer's
``pyproject.toml`` keeps its pins untouched, so nothing local is ever committed
and dropping the flag restores the pinned resolution. Which distributions get
rebound is derived from the worktree's own manifest, never a hardcoded list.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import p as core_p
from flext_infra import c, config
from flext_infra.workspace.flext_binding import FlextInfraFlextBindingService
from tests import t, u


class TestsFlextInfraWorktreeBinding:
    """The service resolves which distributions a worktree can supply."""

    @staticmethod
    def _consumer(tmp_path: Path) -> Path:
        """Return an external consumer declaring flext packages by pinned git URL."""
        provider = u.Tests.provider()
        consumer = tmp_path / "consumer"
        consumer.mkdir()
        (consumer / "pyproject.toml").write_text(
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
        return consumer

    @staticmethod
    def _flext_workspace(tmp_path: Path) -> Path:
        """Return a self-contained flext workspace supplying flext-core and flext-cli.

        Built here rather than pointed at a real checkout so the test states its
        own premise: the rebind set is the intersection of what the consumer
        declares with what the worktree PROVIDES, and only a fixture that owns
        both sides can prove the intersection rather than inherit it from one
        machine's disk.
        """
        flext_root = tmp_path / "flext"
        u.Tests.WorktreeFixture.initialize_governed_project(
            flext_root,
            "flext",
            workspace="flext",
            database="flext",
            issue_prefix="flext",
        )
        for name in ("flext-core", "flext-cli"):
            u.Tests.WorktreeFixture.initialize_governed_project(
                flext_root / name,
                name,
                workspace=name,
                database=name,
                issue_prefix=name,
                beads_owner=False,
            )
            u.Tests.WorktreeFixture.link_member_beads(
                flext_root / name,
                flext_root,
                workspace_name="flext",
                database="flext",
                issue_prefix="flext",
            )
        u.Tests.WorktreeFixture.write_gitmodules(
            flext_root, ("flext-core", "flext-cli")
        )
        return flext_root

    def test_binding_targets_only_the_flext_packages_the_consumer_declares(
        self, tmp_path: Path
    ) -> None:
        """Only declared flext deps present in the worktree are rebound."""
        consumer = self._consumer(tmp_path)

        planned: core_p.Result[t.VariadicTuple[str]] = (
            FlextInfraFlextBindingService.plan_targets(
                consumer_root=consumer, flext_root=self._flext_workspace(tmp_path)
            )
        )

        names = tm.ok(planned)
        tm.that(sorted(names), eq=["flext-cli", "flext-core"])

    def test_binding_rejects_a_path_that_is_not_a_flext_workspace(
        self, tmp_path: Path
    ) -> None:
        """A non-workspace path fails closed instead of silently binding nothing."""
        consumer = self._consumer(tmp_path)
        not_flext = tmp_path / "elsewhere"
        not_flext.mkdir()

        planned = FlextInfraFlextBindingService.plan_targets(
            consumer_root=consumer, flext_root=not_flext
        )

        tm.that(planned.failure, eq=True)
        tm.that(planned.error or "", has="workspace")

    def test_a_consumer_without_flext_dependencies_rejects_requested_binding(
        self, tmp_path: Path
    ) -> None:
        """An explicit binding must never report success without a candidate."""
        consumer = tmp_path / "plain"
        consumer.mkdir()
        (consumer / "pyproject.toml").write_text(
            '[project]\nname = "plain"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13"\ndependencies = ["httpx>=0.27"]\n',
            encoding="utf-8",
        )

        planned = FlextInfraFlextBindingService.plan_targets(
            consumer_root=consumer, flext_root=self._flext_workspace(tmp_path)
        )

        tm.that(planned.failure, eq=True)
        tm.that(planned.error or "", has="selects no declared dependency")

    def test_standalone_supplier_satisfies_a_development_dependency(
        self, tmp_path: Path
    ) -> None:
        """A root-only generator checkout supplies a consumer's declared dev group."""
        supplier = tmp_path / "supplier"
        u.Tests.WorktreeFixture.initialize_governed_project(
            supplier, "flext-infra", workspace="flext-infra",
            database="flext-infra", issue_prefix="flext-infra",
        )
        consumer = self._consumer(tmp_path)
        declaration = consumer / c.Infra.PYPROJECT_FILENAME
        with declaration.open("a", encoding="utf-8") as stream:
            stream.write('[dependency-groups]\ndev = ["flext-infra"]\n')
        before = declaration.read_bytes()

        planned = FlextInfraFlextBindingService.plan_targets(
            consumer_root=consumer, flext_root=supplier,
        )

        assert tm.ok(planned) == ("flext-infra",)
        assert declaration.read_bytes() == before

    @pytest.mark.parametrize("symlinked_environment", [False, True])
    def test_binding_rejects_a_foreign_environment_before_installation(
        self, tmp_path: Path, *, symlinked_environment: bool
    ) -> None:
        """A caller cannot point the installer at the runner's own environment."""
        consumer = tmp_path / "consumer"
        u.Tests.WorktreeFixture.initialize_governed_project(
            consumer, "flext-consumer", workspace="flext-consumer",
            database="flext-consumer", issue_prefix="flext-consumer",
        )
        if symlinked_environment:
            (consumer / config.Infra.tooling.tools.pyright.path_rules.venv_name).symlink_to(
                Path(sys.prefix), target_is_directory=True,
            )
        ci = config.Infra.codegen.make.ci
        outcome = tm.ok(u.Cli.run_raw(
            (
                sys.executable, "-m", "flext_infra", "workspace", "flext-binding",
                "--repository-root", str(consumer), "--flext-root", str(tmp_path / "supplier"),
                "--python", sys.executable,
            ),
            env=u.Cli.process_env(overrides={ci.variable: ci.local_value}),
        ))
        assert outcome.outcome.raw_return_code != 0
        expected = "physical consumer environment" if symlinked_environment else "interpreter must belong to the consumer"
        assert expected in f"{outcome.stdout}{outcome.stderr}"

    def test_binding_cli_rejects_ci_before_installation(self, tmp_path: Path) -> None:
        """The public CLI rejects local editable candidates under the configured CI token."""
        ci = config.Infra.codegen.make.ci
        outcome = tm.ok(u.Cli.run_raw(
            (
                sys.executable, "-m", "flext_infra", "workspace", "flext-binding",
                "--repository-root", str(tmp_path), "--flext-root", str(tmp_path),
                "--python", sys.executable,
            ),
            env=u.Cli.process_env(overrides={ci.variable: ci.value}),
        ))
        assert outcome.outcome.raw_return_code != 0
        assert f"prohibited with {ci.variable}={ci.value}" in f"{outcome.stdout}{outcome.stderr}"


__all__: list[str] = ["TestsFlextInfraWorktreeBinding"]
