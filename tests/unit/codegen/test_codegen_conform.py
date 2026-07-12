"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.17 / agent: codex): this suite exercises only the
# public services and emitted artifacts; the former private catalog golden is gone.
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew


class TestCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    @pytest.mark.parametrize(
        ("kind", "name", "expected_profile"),
        [
            (
                c.Infra.ProjectKind.EXTERNAL,
                "flext-demo",
                c.Infra.MakeProfile.STANDALONE,
            ),
            (
                c.Infra.ProjectKind.INTERNAL,
                "flext-member",
                c.Infra.MakeProfile.WORKSPACE_MEMBER,
            ),
        ],
    )
    def test_new_project_is_complete_and_idempotent(
        self,
        tmp_path: Path,
        kind: c.Infra.ProjectKind,
        name: str,
        expected_profile: c.Infra.MakeProfile,
    ) -> None:
        root = tmp_path / kind.value
        service = FlextInfraCodegenProjectNew(
            name=name,
            kind=kind,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_core",
            year=2026,
            apply_changes=True,
        )
        first = service.execute()
        assert first.success, first.error
        second = service.execute()
        assert second.success, second.error
        tm.that(bool(first.value.written_files), eq=True)
        tm.that(second.value.written_files, eq=())
        tm.that(first.value.plan.workspace.repository.profile, eq=expected_profile)
        tm.that(first.value.plan.request.root, eq=root.resolve())
        tm.that((root / "config" / "workspace.yaml").is_file(), eq=True)
        tm.that((root / "pyproject.toml").is_file(), eq=True)
        package_name = name.replace("-", "_")
        pythonpath = os.pathsep.join(
            part
            for part in (str(root / "src"), os.environ.get("PYTHONPATH", ""))
            if part
        )
        process = subprocess.run(
            [sys.executable, "-m", package_name, "ping"],
            capture_output=True,
            text=True,
            cwd=root,
            env={**os.environ, "PYTHONPATH": pythonpath},
            timeout=60,
            check=False,
        )
        tm.that(process.returncode, eq=0)
        tm.that(process.stderr.strip(), eq="")

    def test_existing_manifest_converges_to_identical_tree(
        self,
        tmp_path: Path,
    ) -> None:
        new_root = tmp_path / "new" / "flext-demo"
        existing_root = tmp_path / "existing" / "flext-demo"
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=new_root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_core",
            year=2026,
            apply_changes=True,
        ).execute()
        assert created.success, created.error
        manifest = u.Cli.files_read_text(new_root / "config" / "workspace.yaml")
        assert manifest.success, manifest.error
        written = u.Cli.atomic_write_text_file(
            existing_root / "config" / "workspace.yaml",
            manifest.value,
        )
        assert written.success, written.error
        migrated = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=existing_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        assert migrated.success, migrated.error
        new_tree = tuple(
            sorted(
                (path.relative_to(new_root).as_posix(), path.read_bytes())
                for path in new_root.rglob("*")
                if path.is_file()
            ),
        )
        existing_tree = tuple(
            sorted(
                (path.relative_to(existing_root).as_posix(), path.read_bytes())
                for path in existing_root.rglob("*")
                if path.is_file()
            ),
        )
        tm.that(existing_tree, eq=new_tree)

    def test_workspace_uv_plan_owns_root_lock_and_editable_repositories(
        self,
        tmp_path: Path,
    ) -> None:
        """Keep workspace setup data complete without Make-side re-derivation."""
        root_repository = next(
            item for item in config.Infra.codegen.repositories if item.name == "flext"
        )
        member = next(
            item
            for item in config.Infra.codegen.repositories
            if item.name == "flext-core"
        )
        workspace = m.Infra.WorkspaceSpec(
            version=1,
            name="flext",
            repository=root_repository,
            project=m.Infra.ProjectSpec(
                package_name="flext",
                class_stem="Flext",
                namespace="Flext",
                constant_name="flext",
                namespace_attribute="flext",
                alias="flext",
                environment_prefix="FLEXT_",
                description="FLEXT workspace",
                version="0.12.0.dev0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_core",
                homepage="https://github.com/flext-sh/flext",
                documentation="https://github.com/flext-sh/flext",
                workspace_root_rel=".",
                year=2026,
            ),
            members=(member,),
        )
        root = tmp_path / "flext"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            workspace_root=root,
            request=request,
            initial_workspace=workspace,
        ).plan(request)
        assert planned.success, planned.error
        environment = planned.value.uv_environments[0]
        tm.that(environment.environment_root, eq=root.resolve())
        tm.that(environment.lock_path, eq=root.resolve() / "uv.lock")
        tm.that(environment.groups, eq=("dev", "codegen", "workspace"))
        tm.that(
            tuple(item.name for item in environment.editable_repositories),
            eq=("flext", "flext-core"),
        )

    def test_public_cli_routes_check_and_apply_to_one_handler(
        self,
        tmp_path: Path,
    ) -> None:
        """Execute both public modes without changing an already conform tree."""
        root = tmp_path / "flext-demo"
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_core",
            year=2026,
            apply_changes=True,
        ).execute()
        assert created.success, created.error
        before = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            ),
        )
        for mode in ("check", "apply"):
            # NOTE (multi-agent, mro-wkii.17 / agent: codex): invoke the real
            # module entrypoint; the route and emitted tree are the assertions.
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "codegen",
                    "conform",
                    "--root",
                    str(root),
                    "--scope",
                    "self",
                    "--mode",
                    mode,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            tm.that(process.returncode, eq=0)
            tm.that(process.stderr.strip(), eq="")
        after = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file()
            ),
        )
        tm.that(after, eq=before)


__all__: list[str] = []
