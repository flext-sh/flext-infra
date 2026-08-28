"""Workspace/parser helper tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_core import r
from flext_infra import config, m, u as infra_u
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_tests import tm
from tests import c, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraDepsModernizerWorkspace:
    """Validate helper behavior through public utilities and entrypoints."""

    def test_tooling_context_resolution_does_not_launch_external_formatter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = tmp_path / "flext-demo"
        monkeypatch.setenv("PATH", "")

        resolved = FlextInfraPyprojectModernizer(
            workspace_root=project, skip_check=True
        ).resolve_tooling_context(
            project_name="flext-demo",
            package_name="flext_demo",
            path=project / "pyproject.toml",
            declared_python_dirs=("src", "tests"),
            declared_python_dirs_are_complete=True,
        )

        tm.ok(resolved)

    def test_taplo_cache_key_tracks_config_content_and_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        commands: list[tuple[str, ...]] = []
        working_directories: list[Path] = []

        def run_raw(
            command: list[str], *, cwd: Path, input_data: bytes
        ) -> r[m.Cli.CommandOutput]:
            commands.append(tuple(command))
            working_directories.append(cwd)
            tm.that(input_data, eq=source.encode())
            return r[m.Cli.CommandOutput].ok(
                m.Cli.CommandOutput(stdout='name = "demo"\n', stderr="", exit_code=0)
            )

        monkeypatch.setattr(u.Cli, "run_raw", run_raw)
        config_path = tmp_path / ".taplo.toml"
        config_path.write_text('include = ["**/*.toml"]\n', encoding="utf-8")
        formatter = infra_u.Infra.format_toml_source
        taplo_version = config.Infra.codegen.toolchain.taplo_version
        source = 'name="demo"\n'

        formatted = tm.ok(
            formatter(
                source,
                path=tmp_path / "first" / "pyproject.toml",
                toolchain_root=tmp_path,
                taplo_version=taplo_version,
            )
        )
        tm.ok(
            formatter(
                source,
                path=tmp_path / "first" / "pyproject.toml",
                toolchain_root=tmp_path,
                taplo_version=taplo_version,
            )
        )
        config_path.write_text('include = ["pyproject.toml"]\n', encoding="utf-8")
        tm.ok(
            formatter(
                source,
                path=tmp_path / "first" / "pyproject.toml",
                toolchain_root=tmp_path,
                taplo_version=taplo_version,
            )
        )
        tm.ok(
            formatter(
                source,
                path=tmp_path / "second" / "pyproject.toml",
                toolchain_root=tmp_path,
                taplo_version=taplo_version,
            )
        )

        tm.that(commands, len=3)
        tm.that(formatted, eq='name = "demo"')
        tm.that(commands[0], has="first/pyproject.toml")
        tm.that(commands[2], has="second/pyproject.toml")
        tm.that(working_directories, eq=[tmp_path.resolve()] * 3)
        tm.that(commands[0], has=str(config_path.resolve()))

    def test_taplo_uses_nearest_existing_root_for_scaffold_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        working_directories: list[Path] = []

        def run_raw(
            _command: list[str], *, cwd: Path, input_data: bytes
        ) -> r[m.Cli.CommandOutput]:
            working_directories.append(cwd)
            tm.that(input_data, eq=b'name="demo"\n')
            return r[m.Cli.CommandOutput].ok(
                m.Cli.CommandOutput(stdout='name = "demo"\n', stderr="", exit_code=0)
            )

        monkeypatch.setattr(u.Cli, "run_raw", run_raw)
        future_root = tmp_path / "future" / "project"

        tm.ok(
            infra_u.Infra.format_toml_source(
                'name="demo"\n',
                path=future_root / "pyproject.toml",
                toolchain_root=future_root,
                taplo_version=config.Infra.codegen.toolchain.taplo_version,
            )
        )

        tm.that(working_directories, eq=[tmp_path.resolve()])

    @pytest.mark.parametrize(
        ("content", "exists", "expected"),
        [
            pytest.param('key = "value"\n', True, True, id="valid"),
            pytest.param("invalid toml content [[[", True, False, id="invalid"),
            pytest.param("", False, False, id="missing"),
        ],
    )
    def test_toml_read_handles_public_file_cases(
        self, tmp_path: Path, content: str, *, exists: bool, expected: bool
    ) -> None:
        """Verify toml read handles public file cases."""
        toml_file = tmp_path / "test.toml"
        if exists:
            toml_file.write_text(content, encoding="utf-8")
        with u.structlog().testing.capture_logs() as log_entries:
            result = u.Cli.toml_read(toml_file)
        tm.that(result is not None, eq=expected)
        if exists and not expected:
            tm.that(log_entries, len=1)
            tm.that(log_entries[0].get("log_level"), eq="warning")
        else:
            tm.that(log_entries, empty=True)

    def test_workspace_root_returns_explicit_path(self, tmp_path: Path) -> None:
        """Verify workspace root returns explicit path."""
        explicit = tmp_path / "explicit"
        explicit.mkdir()
        result = u.Infra.resolve_workspace_root_or_cwd(explicit)
        tm.that(str(result), eq=str(explicit.resolve()))

    def test_workspace_root_fallback_returns_non_empty_path(
        self, tmp_path: Path
    ) -> None:
        """Verify workspace root fallback returns non empty path."""
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True, exist_ok=True)
        result = u.Infra.resolve_workspace_root_or_cwd(deep_path)
        tm.that(str(result), ne="")

    @pytest.mark.parametrize(
        ("description", "sort_first"),
        [
            pytest.param("Config-owned metadata", None, id="config-owner"),
            pytest.param(
                "Portable process runner",
                ("project", "dependency-groups"),
                id="project-first",
            ),
            pytest.param(
                "Typed metadata: punctuation-safe.",
                ("dependency-groups", "project"),
                id="groups-first",
            ),
        ],
    )
    def test_conform_preserves_explicit_project_table_boundary(
        self, tmp_path: Path, description: str, sort_first: t.StrSequence | None
    ) -> None:
        """Keep project scalars explicit for arbitrary valid top-level orders."""
        pyproject = tmp_path / c.Infra.PYPROJECT_FILENAME
        package_init = tmp_path / "src" / "flext_example" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        package_init.write_text("", encoding="utf-8")
        expected_order = (
            config.Infra.tooling.tools.tomlsort.sort_first
            if sort_first is None
            else sort_first
        )
        source = (
            "[project]\n"
            'name = "flext-example"\n'
            'version = "0.1.0"\n'
            f'description = "{description}"\n'
            "\n[dependency-groups]\n"
            'dev = ["pytest"]\n'
        )
        modernizer = (
            FlextInfraPyprojectModernizer(
                workspace_root=tmp_path, skip_check=True, skip_comments=True
            )
            if sort_first is None
            else FlextInfraPyprojectModernizer(
                workspace_root=tmp_path,
                skip_check=True,
                skip_comments=True,
                tomlsort_sort_first=sort_first,
            )
        )
        rendered = tm.ok(modernizer.conform_source(source, path=pyproject))
        tm.that(rendered.count("[project]"), eq=1)
        payload = u.Cli.toml_mapping_from_text(rendered)
        tm.that(payload, none=False)
        if payload is None:
            pytest.fail("conformed pyproject must remain valid TOML")
        project = u.Cli.toml_mapping_child(payload, c.Infra.PROJECT)
        tm.that(project, none=False)
        if project is None:
            pytest.fail("conformed pyproject must retain [project]")
        tm.that(project.get("description"), eq=description)
        groups = u.Cli.toml_mapping_child(payload, "dependency-groups")
        tm.that(groups, none=False)
        if groups is None:
            pytest.fail("conformed pyproject must retain [dependency-groups]")
        tm.that(u.Cli.json_as_sequence(groups.get(c.Infra.DEV)), eq=["pytest"])
        tm.that(list(payload)[: len(expected_order)], eq=list(expected_order))
