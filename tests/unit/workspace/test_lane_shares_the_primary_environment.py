"""Lane provisioning is owned by the canonical primary checkout."""

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
        ".PHONY: setup\n"
        "setup:\n"
        '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
        f"\t@mkdir -p {_VENV_NAME}/bin\n"
        f"\t@printf '#!/bin/sh\\n' > {_VENV_NAME}/bin/python\n"
        "\t@printf '%s\\n' \"$(WORKSPACE)\" >> setup-runs.log\n",
        encoding="utf-8",
    )
    (repository / ".gitignore").write_text(
        f"{_VENV_NAME}\nsetup-runs.log\n", encoding="utf-8"
    )
    u.Tests.initialize_git_repo(repository)
    return repository


def _add_lane(repository: Path, branch: str) -> Path:
    """Create one Git lane without provisioning it."""
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


def _declared_child(tmp_path: Path, repository: Path) -> Path:
    child = tmp_path / "child"
    child.mkdir()
    (child / "child.txt").write_text("clean\n", encoding="utf-8")
    u.Tests.initialize_git_repo(child)
    tm.ok(
        u.Cli.run_checked(
            [
                c.Infra.GIT,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(child),
                "member",
            ],
            cwd=repository,
        )
    )
    tm.ok(
        u.Cli.run_checked([c.Infra.GIT, "commit", "-am", "add member"], cwd=repository)
    )
    return child


class TestsFlextInfraLaneEnvironment:
    """The lane shares the primary checkout's canonical environment."""

    def test_setup_runs_from_primary_and_links_lane_environment(
        self, tmp_path: Path
    ) -> None:
        repository = _repository(tmp_path)
        lane = _add_lane(repository, "feature/shared-environment")

        provisioned = tm.ok(
            FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)
        )
        tm.that(provisioned, eq=True)
        tm.that(
            (repository / "setup-runs.log").read_text(encoding="utf-8"),
            eq=f"{repository.resolve()}\n",
        )
        tm.that((lane / _VENV_NAME).is_symlink(), eq=True)
        tm.that((lane / _VENV_NAME).resolve(), eq=(repository / _VENV_NAME).resolve())

    def test_correct_environment_link_is_idempotent(self, tmp_path: Path) -> None:
        repository = _repository(tmp_path)
        lane = _add_lane(repository, "feature/idempotent-environment")
        tm.ok(FlextInfraWorktreeService.setup_lane(repository.resolve(), lane))

        tm.ok(FlextInfraWorktreeService.setup_lane(repository.resolve(), lane))

        tm.that((lane / _VENV_NAME).is_symlink(), eq=True)
        tm.that(
            (repository / "setup-runs.log").read_text(encoding="utf-8").splitlines(),
            eq=[str(repository.resolve()), str(repository.resolve())],
        )

    def test_conflicting_real_lane_environment_fails_closed(
        self, tmp_path: Path
    ) -> None:
        repository = _repository(tmp_path)
        lane = _add_lane(repository, "feature/conflicting-environment")
        lane_venv = lane / _VENV_NAME
        (lane_venv / "bin").mkdir(parents=True)
        (lane_venv / "bin" / "python").write_text("local\n", encoding="utf-8")

        provisioned = FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)

        tm.fail(provisioned, has="refusing to replace")
        tm.that(lane_venv.is_symlink(), eq=False)
        tm.that(
            (lane_venv / "bin" / "python").read_text(encoding="utf-8"), eq="local\n"
        )

    def test_conflicting_lane_environment_symlink_fails_closed(
        self, tmp_path: Path
    ) -> None:
        repository = _repository(tmp_path)
        lane = _add_lane(repository, "feature/conflicting-link")
        foreign = tmp_path / "foreign-venv"
        foreign.mkdir()
        (lane / _VENV_NAME).symlink_to(foreign, target_is_directory=True)

        provisioned = FlextInfraWorktreeService.setup_lane(repository.resolve(), lane)

        tm.fail(provisioned, has="points outside the primary environment")
        tm.that((lane / _VENV_NAME).resolve(), eq=foreign.resolve())

    def test_absent_direct_gitlink_is_initialized_before_setup(
        self, tmp_path: Path
    ) -> None:
        repository = _repository(tmp_path)
        _declared_child(tmp_path, repository)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "submodule", "deinit", "-f", "member"], cwd=repository
            )
        )
        lane = _add_lane(repository, "feature/initialize-member")

        tm.ok(FlextInfraWorktreeService.setup_lane(repository.resolve(), lane))

        tm.that((repository / "member" / ".git").exists(), eq=True)

    def test_initialized_dirty_gitlink_is_untouched(self, tmp_path: Path) -> None:
        repository = _repository(tmp_path)
        _declared_child(tmp_path, repository)
        dirty = repository / "member" / "child.txt"
        dirty.write_text("dirty\n", encoding="utf-8")
        lane = _add_lane(repository, "feature/preserve-member")

        tm.ok(FlextInfraWorktreeService.setup_lane(repository.resolve(), lane))

        tm.that(dirty.read_text(encoding="utf-8"), eq="dirty\n")


__all__: tuple[str, ...] = ()
