"""Edge-case tests for public modernizer flows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.deps import FlextInfraPyprojectModernizer
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsModernizerMainExtra:
    """Validate edge cases through the public modernizer API."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("content", "expected"),
        [
            u.Tests.param(None, 2, id="missing-root-pyproject"),
            u.Tests.param("", 2, id="empty-root-pyproject"),
            u.Tests.param("[invalid toml {", 2, id="invalid-root-pyproject"),
        ],
    )
    def test_run_handles_root_edge_cases(
        tmp_path: Path,
        content: str | None,
        expected: int,
    ) -> None:
        """Fail loud for missing, empty, or invalid root project contracts."""
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (workspace / c.PYPROJECT_FILENAME).write_text(content, encoding="utf-8")
        modernizer = FlextInfraPyprojectModernizer(repository_root=workspace)
        tm.that(modernizer.run(), eq=expected)

    @staticmethod
    def test_audit_returns_zero_after_workspace_is_canonical(
        modernizer_workspace: Path,
    ) -> None:
        """Reach a fixed point after one canonical apply."""
        apply_exit = FlextInfraPyprojectModernizer(
            repository_root=modernizer_workspace,
            apply_changes=True,
            skip_comments=True,
            skip_check=True,
        ).run()
        audit_exit = FlextInfraPyprojectModernizer(
            repository_root=modernizer_workspace,
            audit=True,
            skip_comments=True,
        ).run()
        tm.that(apply_exit, eq=0)
        tm.that(audit_exit, eq=0)

    @staticmethod
    def test_run_fails_when_selected_project_has_invalid_toml(
        modernizer_workspace_with_projects: Path,
    ) -> None:
        """Invalid TOML in a declared member escapes before any write."""
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.PYPROJECT_FILENAME
        )
        selected_pyproject.write_text("[invalid", encoding="utf-8")
        root_pyproject = modernizer_workspace_with_projects / c.PYPROJECT_FILENAME
        root_before = root_pyproject.read_bytes()
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=modernizer_workspace_with_projects,
            apply_changes=True,
            skip_comments=True,
            skip_check=False,
        )

        # The canonical docs-scope reader owns the typed invalid-TOML error and
        # names the file; the run lets it leave instead of logging an exit code.
        with u.Tests.raises(
            ValueError,
            match="docs pyproject TOML is invalid",
        ) as raised:
            modernizer.run()
        tm.that(str(raised.value), has=str(selected_pyproject))
        tm.that(root_pyproject.read_bytes(), eq=root_before)
        tm.that(selected_pyproject.read_text(encoding="utf-8"), eq="[invalid")

    @staticmethod
    def test_run_scopes_default_audit_to_root_without_external_siblings(
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """Keep default modernization inside the declared workspace boundary."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "flext",
            pyproject=(
                "[project]\n"
                "name='flext'\n"
                "version='0.1.0'\n"
                "requires-python='>=3.13,<3.14'\n"
                "dependencies=[]\n"
            ),
        )
        u.Tests.write_project_beads_config(workspace, "flext")
        # The governed tree above the workspace carries the committed Mise
        # declaration and lock that activate its locked tools.
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        external = tmp_path / "gruponos-data"
        (external / "src" / "gruponos_data").mkdir(parents=True)
        external_pyproject = external / c.PYPROJECT_FILENAME
        external_pyproject.write_text(
            "[project]\nname='gruponos-data'\ndependencies=['flext-core']\n",
            encoding="utf-8",
        )

        modernizer = FlextInfraPyprojectModernizer(
            repository_root=workspace,
            audit=True,
            skip_comments=True,
        )

        tm.that(modernizer.run(), eq=1)
        output = capsys.readouterr().out
        tm.that(output, has="pyproject.toml:")
        tm.that(output, lacks=str(external_pyproject.resolve()))
        tm.that(output, lacks="not in the subpath")

    @staticmethod
    def test_conform_source_preserves_taplo_process_error(tmp_path: Path) -> None:
        """Return the exact formatter process failure from the public conform path."""
        # A governed tree carries the Mise declaration with its lock; the
        # formatter resolves through the declared toolchain.
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        invalid_glob = "/x/["
        (tmp_path / c.Infra.TAPLO_CONFIG_FILENAME).write_text(
            f'include = ["{invalid_glob}"]\n',
            encoding="utf-8",
        )
        source = '[project]\nname = "sample"\nversion = "0.1.0"\n'
        path = tmp_path / c.PYPROJECT_FILENAME
        modernizer = FlextInfraPyprojectModernizer(repository_root=tmp_path)
        topology = m.Infra.PyprojectDeclaredTopology()
        codegen = tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec
        canonical_source = tm.ok(
            modernizer.conform_source(
                source,
                path=path,
                format_source=False,
                topology=topology,
                codegen=codegen,
            ),
        )
        baseline = u.Infra.format_toml_source(
            canonical_source,
            path=path,
            toolchain_root=tmp_path,
            taplo_version=config.Infra.codegen.toolchain.tool_versions["taplo"],
            process_timeout_seconds=(
                config.Infra.tooling.tools.tomlsort.process_timeout_seconds
            ),
        )

        result = modernizer.conform_source(
            canonical_source,
            path=path,
            topology=topology,
            codegen=codegen,
        )

        error = tm.fail(result)
        tm.that(error, eq=tm.fail(baseline))
        tm.that(error, has="taplo format failed (1):")
        tm.that(
            error,
            lacks=["couldn't exec process", "pyproject tooling render failed"],
        )
