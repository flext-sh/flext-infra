"""Behavioral proof for generated setup submodule bootstrapping."""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import c, u
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_tests import tm


class TestsCodegenSetupSubmodules:
    @staticmethod
    def _git(root: Path, *arguments: str) -> str:
        return tm.ok(u.Cli.capture(["git", *arguments], cwd=root)).strip()

    @classmethod
    def _commit_repository(cls, root: Path, branch: str, marker: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        cls._git(root, "init", "-q", "-b", branch)
        cls._git(root, "config", "user.email", "tests@flext.local")
        cls._git(root, "config", "user.name", "FLEXT Tests")
        (root / "marker.txt").write_text(marker, encoding="utf-8")
        cls._git(root, "add", "marker.txt")
        cls._git(root, "commit", "-q", "-m", marker)

    @classmethod
    def _generated_project(cls, root: Path) -> None:
        tm.ok(
            FlextInfraCodegenProjectNew(
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
            ).execute()
        )
        cls._git(root, "init", "-q", "-b", "main")
        cls._git(root, "config", "user.email", "tests@flext.local")
        cls._git(root, "config", "user.name", "FLEXT Tests")

    @staticmethod
    def _fake_uv(
        root: Path, expected_submodule_file: Path | None = None
    ) -> dict[str, str]:
        bin_dir = root / "fixture-bin"
        bin_dir.mkdir()
        (bin_dir / "uv").write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            'if [ -n "${EXPECTED_SUBMODULE_FILE:-}" ] && '
            '[ ! -f "$EXPECTED_SUBMODULE_FILE" ]; then\n'
            '  printf "submodule missing before uv\\n" >&2\n'
            "  exit 70\n"
            "fi\n"
            'printf "%s\\n" "$*" >> "$UV_LOG"\n',
            encoding="utf-8",
        )
        (bin_dir / "uv").chmod(0o755)
        (bin_dir / "mise").write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            'if [ "$1" = "install" ]; then exit 0; fi\n'
            'if [ "$1" = "exec" ]; then\n'
            "  shift\n"
            '  if [ "${1:-}" = "--" ]; then shift; fi\n'
            '  exec "$@"\n'
            "fi\n"
            'printf "unsupported mise fixture command: %s\\n" "$*" >&2\n'
            "exit 64\n",
            encoding="utf-8",
        )
        (bin_dir / "mise").chmod(0o755)
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "MISE": str(bin_dir / "mise"),
            "UV_LOG": str(root / "uv.log"),
            "GIT_ALLOW_PROTOCOL": "file",
        }
        if expected_submodule_file is not None:
            environment["EXPECTED_SUBMODULE_FILE"] = str(expected_submodule_file)
        return environment

    @classmethod
    def _add_submodule(
        cls, superproject: Path, repository: Path, path: str, branch: str
    ) -> None:
        cls._git(
            superproject,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            "-f",
            "-b",
            branch,
            str(repository),
            path,
        )
        cls._git(superproject, "add", "-f", ".gitmodules", path)
        cls._git(superproject, "commit", "-q", "-m", f"Add {path}")

    def test_virgin_recursive_submodules_initialize_before_environment(
        self, tmp_path: Path
    ) -> None:
        nested = tmp_path / "nested"
        child = tmp_path / "child"
        self._commit_repository(nested, "nested-dev", "nested")
        self._commit_repository(child, "child-dev", "child")
        self._add_submodule(child, nested, "nested", "nested-dev")

        source = tmp_path / "source"
        self._commit_repository(source, "source-dev", "source")
        self._add_submodule(source, child, "child", "child-dev")

        project = tmp_path / "project"
        self._generated_project(project)
        self._add_submodule(project, source, "vendor/source", "source-dev")
        self._git(project, "submodule", "deinit", "-q", "-f", "--all")
        nested_marker = project / "vendor/source/child/nested/marker.txt"

        tm.ok(
            u.Cli.capture(
                ["make", "setup"],
                cwd=project,
                env=self._fake_uv(project, nested_marker),
            )
        )

        tm.that(
            self._git(project / "vendor/source", "branch", "--show-current"),
            eq="source-dev",
        )
        tm.that(
            self._git(
                project / "vendor/source/child/nested", "branch", "--show-current"
            ),
            eq="nested-dev",
        )

    def test_setup_is_repeatable_without_gitmodules(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        self._generated_project(project)
        environment = self._fake_uv(project)

        tm.ok(u.Cli.capture(["make", "setup"], cwd=project, env=environment))
        tm.ok(u.Cli.capture(["make", "setup"], cwd=project, env=environment))

    def test_conflicting_branch_fails_before_environment(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        self._commit_repository(source, "declared-dev", "source")
        project = tmp_path / "project"
        self._generated_project(project)
        self._add_submodule(project, source, "vendor/source", "declared-dev")
        self._git(project / "vendor/source", "switch", "-q", "-c", "local-work")
        environment = self._fake_uv(project)

        result = tm.ok(u.Cli.run_raw(["make", "setup"], cwd=project, env=environment))

        tm.that(result.exit_code, eq=2)
        tm.that(result.stderr, has="conflicting branch")
        tm.that(
            self._git(project / "vendor/source", "branch", "--show-current"),
            eq="local-work",
        )
        tm.that((project / "uv.log").exists(), eq=False)

    def test_local_changes_fail_before_environment(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        self._commit_repository(source, "declared-dev", "source")
        project = tmp_path / "project"
        self._generated_project(project)
        self._add_submodule(project, source, "vendor/source", "declared-dev")
        marker = project / "vendor/source/marker.txt"
        marker.write_text("local change", encoding="utf-8")
        environment = self._fake_uv(project)

        result = tm.ok(u.Cli.run_raw(["make", "setup"], cwd=project, env=environment))

        tm.that(result.exit_code, eq=2)
        tm.that(result.stderr, has="local changes must be reconciled")
        tm.that(marker.read_text(encoding="utf-8"), eq="local change")
        tm.that((project / "uv.log").exists(), eq=False)

    def test_declared_branch_ahead_of_gitlink_is_preserved(
        self, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        self._commit_repository(source, "declared-dev", "source")
        project = tmp_path / "project"
        self._generated_project(project)
        self._add_submodule(project, source, "vendor/source", "declared-dev")
        checkout = project / "vendor/source"
        advanced_marker = checkout / "advanced.txt"
        advanced_marker.write_text("fix forward", encoding="utf-8")
        self._git(checkout, "add", "advanced.txt")
        self._git(checkout, "commit", "-q", "-m", "Advance declared branch")
        advanced_head = self._git(checkout, "rev-parse", "HEAD")

        tm.ok(u.Cli.capture(["make", "setup"], cwd=project, env=self._fake_uv(project)))

        tm.that(self._git(checkout, "branch", "--show-current"), eq="declared-dev")
        tm.that(self._git(checkout, "rev-parse", "HEAD"), eq=advanced_head)
        tm.that(advanced_marker.read_text(encoding="utf-8"), eq="fix forward")

    def test_same_branch_declaration_uses_superproject_branch(
        self, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        self._commit_repository(source, "main", "source")
        project = tmp_path / "project"
        self._generated_project(project)
        self._add_submodule(project, source, "vendor/source", "main")
        self._git(
            project,
            "config",
            "-f",
            ".gitmodules",
            "submodule.vendor/source.branch",
            ".",
        )
        self._git(project, "add", ".gitmodules")
        self._git(project, "commit", "-q", "-m", "Track superproject branch")
        self._git(project, "submodule", "deinit", "-q", "-f", "--all")

        tm.ok(u.Cli.capture(["make", "setup"], cwd=project, env=self._fake_uv(project)))

        tm.that(
            self._git(project / "vendor/source", "branch", "--show-current"), eq="main"
        )


__all__: tuple[str, ...] = ()
