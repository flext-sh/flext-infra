"""Behavior contract for the generated recurring FLEXT-law dispatcher."""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


class TestsFlextLawLoop:
    """Exercise the configured workspace-root script as a real process."""

    def test_once_propagates_fixer_failure(self, tmp_path: Path) -> None:
        """A failing fixer makes a one-shot cycle return that exact status."""
        repository = test_u.Tests.repository_ref("fixture-workspace")
        homepage = repository.url.removesuffix(".git")
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            project=m.Infra.ProjectSpec(
                package_name="fixture_workspace",
                class_stem="FixtureWorkspace",
                namespace="FixtureWorkspace",
                constant_name=repository.name,
                namespace_attribute="fixture_workspace",
                alias="fixture_workspace",
                environment_prefix="FIXTURE_WORKSPACE_",
                description="Fixture workspace",
                version="0.12.0.dev0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                homepage=homepage,
                documentation=homepage,
                workspace_root_rel=".",
                year=2026,
            ),
        )
        workspace_root = tmp_path / repository.name
        workspace_root.mkdir()
        test_u.Tests.initialize_git_repo(workspace_root, origin_url=repository.url)
        request = m.Infra.CodegenConformRequest(
            root=workspace_root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan = tm.ok(
            FlextInfraCodegenConform(
                workspace_root=workspace_root,
                request=request,
                initial_workspace=workspace,
            ).plan(request)
        )
        loop_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.source).name == "flext-law-loop.sh.j2"
        )
        tm.that(loop_entries, len=1)
        script_path = workspace_root / loop_entries[0].destination
        script_plans = tuple(file for file in plan.files if file.path == script_path)
        tm.that(script_plans, len=1)
        test_u.Tests.write_executable(script_path, script_plans[0].rendered)

        fixer_exit = 23
        fake_bin = tmp_path / "fake-bin"
        fake_uv = fake_bin / c.Infra.UV
        test_u.Tests.write_executable(fake_uv, f"#!/bin/sh\nexit {fixer_exit}\n")
        process = tm.ok(
            u.Cli.run_raw(
                [str(script_path), "--once"],
                cwd=workspace_root,
                env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
                timeout=c.Infra.TIMEOUT_DEFAULT,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=fixer_exit, msg=output)


__all__: tuple[str, ...] = ()
