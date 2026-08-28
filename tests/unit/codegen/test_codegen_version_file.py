"""Repository-local version-file generation contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
from flext_tests import tm
from tests import c, t

if TYPE_CHECKING:
    from pathlib import Path


def _create_repository(tmp_path: Path, project_name: str) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    repository.mkdir(parents=True)
    (repository / "pyproject.toml").write_text(
        f'[project]\nname = "{project_name}"\n'
        f'version = "{c.Tests.RELEASE_VERSION_BASE}"\n',
        encoding="utf-8",
    )
    package = repository / "src" / project_name.replace("-", "_")
    package.mkdir(parents=True)
    (package / "__init__.py").touch()
    return repository, package


class TestsFlextInfraCodegenVersionFile:
    def test_generates_canonical_version_file(self, tmp_path: Path) -> None:
        repository, package = _create_repository(tmp_path, c.Tests.DEMO_PROJECT_NAME)

        tm.ok(FlextInfraCodegenVersionFile(workspace_root=repository).execute())

        content = (package / "__version__.py").read_text(encoding="utf-8")
        tm.that(content, has=["DemoProjectVersion", "FlextVersion"])

    def test_check_only_and_dry_run_do_not_write(self, tmp_path: Path) -> None:
        for option in ("check_only", "dry_run"):
            repository, package = _create_repository(
                tmp_path / option, c.Tests.DEMO_PROJECT_NAME
            )
            service = FlextInfraCodegenVersionFile.model_validate({
                "workspace_root": repository,
                option: True,
            })

            tm.ok(service.execute())
            tm.that((package / "__version__.py").exists(), eq=False)

    def test_second_generation_is_idempotent(self, tmp_path: Path) -> None:
        repository, package = _create_repository(tmp_path, c.Tests.DEMO_PROJECT_NAME)
        service = FlextInfraCodegenVersionFile(workspace_root=repository)

        tm.ok(service.execute())
        first = (package / "__version__.py").read_text(encoding="utf-8")
        tm.ok(service.execute())

        tm.that((package / "__version__.py").read_text(encoding="utf-8"), eq=first)

    def test_unknown_project_filter_fails(self, tmp_path: Path) -> None:
        repository, _package = _create_repository(tmp_path, c.Tests.DEMO_PROJECT_NAME)
        service = FlextInfraCodegenVersionFile(
            workspace_root=repository, project_filter="another-project"
        )

        tm.fail(service.execute(), has="unknown project")

    def test_missing_package_directory_is_a_noop(self, tmp_path: Path) -> None:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "demo-project"\nversion = "0.1.0"\n', encoding="utf-8"
        )

        tm.ok(FlextInfraCodegenVersionFile(workspace_root=repository).execute())


__all__: t.StrSequence = []
