"""A lane owns the environment `make setup` provisions for it.

An environment name that resolves to another checkout makes the lane import
that checkout's sources: `uv` writes editable finders as per-environment
``.pth`` files holding absolute paths, so borrowing another checkout's
environment silently binds the lane to the owner's code. Every lane therefore
provisions its own environment through the canonical `make setup` surface
(mro-j4vd).
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService, c, config
from flext_tests import tm
from tests import u

_VENV_NAME = config.Infra.tooling.tools.pyright.path_rules.venv_name


def _repository(tmp_path: Path) -> Path:
    """Return one committed repository whose ``setup`` target is observable."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        'description = "A standard PEP 621 description string"\n',
        encoding="utf-8",
    )
    (repository / "Makefile").write_text(
        ".PHONY: setup\nsetup:\n\t@printf 'setup %s\\n' \"$(WORKSPACE)\"\n",
        encoding="utf-8",
    )
    u.Tests.initialize_git_repo(repository)
    return repository


def _primary_environment(repository: Path) -> Path:
    """Materialize the primary checkout's environment interpreter."""
    primary_venv = repository / _VENV_NAME
    (primary_venv / "bin").mkdir(parents=True)
    (primary_venv / "bin" / "python").write_text("", encoding="utf-8")
    return primary_venv


def _add_lane(repository: Path, branch: str) -> Path:
    """Create one lane through the canonical worktree service."""
    return Path(
        tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
    )


class TestsFlextInfraLaneEnvironment:
    """The lane environment always belongs to the lane itself."""

    def test_lane_environment_never_links_to_another_checkout(
        self, tmp_path: Path
    ) -> None:
        """A lane must not resolve its environment name to the primary's."""
        repository = _repository(tmp_path)
        primary_venv = _primary_environment(repository)

        lane = _add_lane(repository, "feature/owned-environment")

        lane_venv = lane / _VENV_NAME
        tm.that(lane_venv.is_symlink(), eq=False)
        if lane_venv.exists():
            tm.that(lane_venv.resolve() == primary_venv.resolve(), eq=False)

    def test_lane_setup_runs_the_canonical_setup_surface(
        self, tmp_path: Path
    ) -> None:
        """Provisioning goes through `make setup`, never a link shortcut."""
        repository = _repository(tmp_path)
        _ = _primary_environment(repository)
        lane = _add_lane(repository, "feature/provisioned-environment")

        provisioned = tm.ok(
            FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)
        )

        tm.that(provisioned, eq=True)
        tm.that((lane / _VENV_NAME).is_symlink(), eq=False)

    def test_a_real_lane_environment_is_never_replaced(self, tmp_path: Path) -> None:
        """A present local environment is preserved: a process may be using it."""
        repository = _repository(tmp_path)
        primary_venv = _primary_environment(repository)
        lane = _add_lane(repository, "feature/preserved-environment")
        lane_venv = lane / _VENV_NAME
        if lane_venv.is_symlink() or lane_venv.exists():
            lane_venv.unlink()
        (lane_venv / "bin").mkdir(parents=True)
        (lane_venv / "bin" / "python").write_text("local\n", encoding="utf-8")

        provisioned = tm.ok(
            FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)
        )

        tm.that(provisioned, eq=True)
        tm.that(lane_venv.is_symlink(), eq=False)
        tm.that(
            (lane_venv / "bin" / "python").read_text(encoding="utf-8"), eq="local\n"
        )
        tm.that(primary_venv.is_dir(), eq=True)


__all__: tuple[str, ...] = ()
