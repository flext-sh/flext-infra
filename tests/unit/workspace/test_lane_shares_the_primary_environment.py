"""A lane borrows the primary checkout's environment instead of building one.

A lane that provisions its own environment is a second ``uv sync`` target for the
same sources. Syncing it rewrites the editable pointers every other checkout
resolves through, so the primary and every sibling lane silently start importing
this lane's code. Linking the lane's environment name to the primary's leaves the
primary as the only writer, and generated Make then recognizes the borrowed
environment and provisions nothing (mro-c6di).
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
    """The lane environment name always resolves to a single owner."""

    def test_lane_environment_links_to_the_primary_environment(
        self, tmp_path: Path
    ) -> None:
        """A new lane borrows the primary environment rather than creating one."""
        repository = _repository(tmp_path)
        primary_venv = _primary_environment(repository)

        lane = _add_lane(repository, "feature/borrowed-environment")

        lane_venv = lane / _VENV_NAME
        tm.that(lane_venv.is_symlink(), eq=True)
        tm.that(lane_venv.resolve(), eq=primary_venv.resolve())

    def test_lane_without_a_primary_environment_invents_no_link(
        self, tmp_path: Path
    ) -> None:
        """Nothing is borrowed when the primary owns no environment."""
        repository = _repository(tmp_path)

        lane = _add_lane(repository, "feature/no-owner")

        tm.that((lane / _VENV_NAME).is_symlink(), eq=False)

    def test_a_real_lane_environment_is_never_replaced(self, tmp_path: Path) -> None:
        """A present local environment is preserved: a process may be using it."""
        repository = _repository(tmp_path)
        primary_venv = _primary_environment(repository)
        lane = _add_lane(repository, "feature/preserved-environment")
        lane_venv = lane / _VENV_NAME
        lane_venv.unlink()
        (lane_venv / "bin").mkdir(parents=True)
        (lane_venv / "bin" / "python").write_text("local\n", encoding="utf-8")

        borrowed = tm.ok(
            FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)
        )

        tm.that(borrowed, eq=True)
        tm.that(lane_venv.is_symlink(), eq=False)
        tm.that(
            (lane_venv / "bin" / "python").read_text(encoding="utf-8"), eq="local\n"
        )
        tm.that(primary_venv.is_dir(), eq=True)


__all__: tuple[str, ...] = ()
