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

from pathlib import Path

from flext_core import p as core_p
from flext_infra.workspace.flext_binding import FlextInfraFlextBindingService
from flext_tests import tm


def _consumer(tmp_path: Path) -> Path:
    """Return an external consumer declaring flext packages by pinned git URL."""
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    (consumer / "pyproject.toml").write_text(
        "[project]\n"
        'name = "consumer"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.13"\n'
        "dependencies = [\n"
        '  "flext-core @ git+https://github.com/flext-sh/flext-core.git@0.12.0-dev",\n'
        '  "flext-cli @ git+https://github.com/flext-sh/flext-cli.git@0.12.0-dev",\n'
        '  "httpx>=0.27",\n'
        "]\n",
        encoding="utf-8",
    )
    return consumer


class TestsFlextWorktreeBinding:
    """The service resolves which distributions a worktree can supply."""

    def test_binding_targets_only_the_flext_packages_the_consumer_declares(
        self, tmp_path: Path
    ) -> None:
        """Only declared flext deps present in the worktree are rebound."""
        consumer = _consumer(tmp_path)

        planned: core_p.Result[tuple[str, ...]] = (
            FlextInfraFlextBindingService.plan_targets(
                consumer_root=consumer, flext_root=Path("/home/marlonsc/flext")
            )
        )

        names = tm.ok(planned)
        tm.that(sorted(names), eq=["flext-cli", "flext-core"])

    def test_binding_rejects_a_path_that_is_not_a_flext_workspace(
        self, tmp_path: Path
    ) -> None:
        """A non-workspace path fails closed instead of silently binding nothing."""
        consumer = _consumer(tmp_path)
        not_flext = tmp_path / "elsewhere"
        not_flext.mkdir()

        planned = FlextInfraFlextBindingService.plan_targets(
            consumer_root=consumer, flext_root=not_flext
        )

        tm.that(planned.failure, eq=True)
        tm.that(planned.error or "", has="workspace")

    def test_a_consumer_without_flext_dependencies_binds_nothing(
        self, tmp_path: Path
    ) -> None:
        """No flext dependency means no rebind, not an error."""
        consumer = tmp_path / "plain"
        consumer.mkdir()
        (consumer / "pyproject.toml").write_text(
            '[project]\nname = "plain"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13"\ndependencies = ["httpx>=0.27"]\n',
            encoding="utf-8",
        )

        planned = FlextInfraFlextBindingService.plan_targets(
            consumer_root=consumer, flext_root=Path("/home/marlonsc/flext")
        )

        tm.that(tm.ok(planned), eq=())


__all__: tuple[str, ...] = ()
