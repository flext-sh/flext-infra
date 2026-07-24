"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.17 / agent: codex): this suite exercises only the
# public services and emitted artifacts; the former private catalog golden is gone.
from __future__ import annotations

import os
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
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        first = service.execute()
        tm.ok(first)
        second = service.execute()
        tm.ok(second)
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
        process = u.Cli.capture(
            [sys.executable, "-m", package_name, "ping"],
            cwd=root,
            env={**os.environ, "PYTHONPATH": pythonpath},
            timeout=60,
        )
        tm.ok(process)
        tm.that(process.value, eq="✅ pong")

    def test_existing_manifest_converges_to_identical_tree(
        self, tmp_path: Path, infra_git_repo: Path
    ) -> None:
        new_root = tmp_path / "new" / "flext-demo"
        existing_root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=new_root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        copied = u.Cli.files_copy_directory(new_root, existing_root, dirs_exist_ok=True)
        tm.ok(copied)
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / ".gitignore", "# committed managed drift\n"
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / "Makefile", "# committed managed drift\n"
            )
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=existing_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed committed drift"], cwd=existing_root
            )
        )
        migrated = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=existing_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.ok(migrated)
        new_tree = tuple(
            sorted(
                (path.relative_to(new_root).as_posix(), path.read_bytes())
                for path in new_root.rglob("*")
                if path.is_file()
            )
        )
        existing_tree = tuple(
            sorted(
                (path.relative_to(existing_root).as_posix(), path.read_bytes())
                for path in existing_root.rglob("*")
                if path.is_file()
                and ".git" not in path.relative_to(existing_root).parts
            )
        )
        tm.that(existing_tree, eq=new_tree)

    def test_workspace_uv_plan_owns_root_lock_and_editable_repositories(
        self, tmp_path: Path
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
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
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
                upstream="flext_cli",
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
            workspace_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        tm.ok(planned)
        environment = planned.value.uv_environments[0]
        tm.that(environment.environment_root, eq=root.resolve())
        tm.that(environment.lock_path, eq=root.resolve() / "uv.lock")
        tm.that(environment.groups, eq=("dev", "codegen", "workspace"))
        tm.that(
            tuple(item.name for item in environment.editable_repositories),
            eq=("flext-core",),
        )

    def test_public_cli_routes_check_and_apply_to_one_handler(
        self, infra_git_repo: Path
    ) -> None:
        """Execute both public modes without changing an already conform tree."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )
        before = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )
        for mode in ("check", "apply"):
            # NOTE (multi-agent, mro-wkii.17 / agent: codex): invoke the real
            # module entrypoint; the route and emitted tree are the assertions.
            process = u.Cli.capture(
                [
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "codegen",
                    "conform",
                    "--root",
                    str(root),
                    "--what",
                    "all",
                    "--scope",
                    "self",
                    "--mode",
                    mode,
                ],
                timeout=60,
            )
            tm.ok(process)
        after = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )
        tm.that(after, eq=before)

    def test_dependency_surface_excludes_unowned_managed_files(
        self, infra_git_repo: Path
    ) -> None:
        """Plan only dependency metadata when another managed surface is invalid."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk", ".PHONY: public-handler\npublic-handler:\n\t@true\n"
            )
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.DEPENDENCIES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(workspace_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        tm.that(
            tuple(file.path.name for file in planned.value.files),
            eq=("pyproject.toml",),
        )
        process = u.Cli.capture(
            [
                sys.executable,
                "-m",
                "flext_infra",
                "codegen",
                "conform",
                "--root",
                str(root),
                "--what",
                "dependencies",
                "--scope",
                "self",
                "--mode",
                "check",
            ],
            timeout=60,
        )
        tm.ok(process)

    def test_invalid_public_custom_make_is_preserved_with_rejection(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        custom = root / "custom.mk"
        content = ".PHONY: public-handler\npublic-handler:\n\t@true\n"
        tm.ok(u.Cli.atomic_write_text_file(custom, content))
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        output = capsys.readouterr().out
        rejection = Path(f"{custom}.rej")
        tm.that("WARN:" in output, eq=True)
        tm.that("custom.mk line 1 is not a private custom handler" in output, eq=True)
        tm.that(rejection.is_file(), eq=True)
        tm.that(
            "custom.mk line 1 is not a private custom handler"
            in rejection.read_text(encoding="utf-8"),
            eq=True,
        )
        tm.that(custom.read_text(encoding="utf-8"), eq=content)

    def test_valid_private_custom_make_has_no_rejection(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        custom = root / "custom.mk"
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom, ".PHONY: _custom_check_demo\n_custom_check_demo:\n\t@true\n"
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    def test_scaffold_make_help_documents_and_lists_custom_hooks(
        self, infra_git_repo: Path
    ) -> None:
        """Scaffold help documents the hook contract and lists custom.mk hooks."""
        root = infra_git_repo
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
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-check post-test-all _custom_check_myscan\n"
                "pre-check:\n\t@true\n"
                "post-test-all:\n\t@true\n"
                "_custom_check_myscan:\n\t@true\n",
            )
        )
        outcome = u.Cli.run_raw(["make", "-C", str(root), "help"])
        output = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)
        tm.that(
            output.stdout,
            has=[
                "Custom hooks (custom.mk):",
                "pre-<verb>",
                "pre-check",
                "post-test-all",
                "_custom_check_myscan",
            ],
        )

    def test_scaffold_make_runs_pre_and_post_verb_hooks_in_order(
        self, infra_git_repo: Path
    ) -> None:
        """Generated _dispatch runs pre-<verb>, handler, post-<verb> in order."""
        root = infra_git_repo
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
        # A custom WHAT keeps the handler offline (no uv/network); the
        # pre-/post-<verb> hooks prove ordering around it.
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-check post-check _custom_check_probe\n"
                "pre-check:\n\t@echo HOOK_PRE\n"
                "_custom_check_probe:\n\t@echo HANDLER_BODY\n"
                "post-check:\n\t@echo HOOK_POST\n",
            )
        )
        outcome = u.Cli.run_raw(["make", "-C", str(root), "check", "WHAT=probe"])
        output = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)
        combined = output.stdout + output.stderr
        pre_at = combined.find("HOOK_PRE")
        body_at = combined.find("HANDLER_BODY")
        post_at = combined.find("HOOK_POST")
        tm.that(pre_at >= 0 and body_at >= 0 and post_at >= 0, eq=True)
        tm.that(pre_at < body_at, eq=True)
        tm.that(body_at < post_at, eq=True)

    def test_custom_make_accepts_pre_post_verb_hooks(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """custom.mk may append pre/post verb hooks (verb-wide and WHAT-scoped)."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        custom = root / "custom.mk"
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom,
                ".PHONY: pre-check post-check pre-test-all post-test-all\n"
                "pre-check:\n\t@true\n"
                "post-check:\n\t@true\n"
                "pre-test-all:\n\t@true\n"
                "post-test-all:\n\t@true\n",
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    def test_non_regular_custom_make_remains_fatal(self, infra_git_repo: Path) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
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
        tm.ok(created)
        tm.ok(u.Cli.files_delete(root / "custom.mk"))
        (root / "custom.mk").mkdir()
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.fail(result)
        tm.that(
            result.error,
            eq=f"custom Make destination is not a regular file: {root / 'custom.mk'}",
        )


__all__: list[str] = []
