"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

from flext_tests import tm

from flext_infra import c, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew


class TestsCodegenMakeEnvironment:
    def test_generated_make_overrides_inherited_uv_environment(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "demo-root"
        created = FlextInfraCodegenProjectNew(
            name="demo-root",
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
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, has="$(UV_RUN) python -m pytest")
        tm.that(makefile, has="$(UV_RUN) python -m flext_infra codegen conform")
        (root / "custom.mk").write_text(
            "_custom_check_probe:\n"
            "\t@printf '%s\\n%s\\n%s\\n' "
            "'$(UV_PROJECT)' '$(UV_PROJECT_ENVIRONMENT)' '$(VIRTUAL_ENV)'\n",
            encoding="utf-8",
        )
        hostile_root = tmp_path / "hostile"
        hostile_venv = hostile_root / ".venv"
        active_env = os.environ.copy()
        active_env.update({
            "UV_PROJECT": str(hostile_root),
            "UV_PROJECT_ENVIRONMENT": str(hostile_venv),
            "VIRTUAL_ENV": str(hostile_venv),
        })

        result = u.Cli.run_raw(
            ["make", "check", "WHAT=probe"], cwd=root, env=active_env
        )

        output = tm.ok(result).stdout.splitlines()
        tm.that(output, eq=[str(root), str(root / ".venv"), str(root / ".venv")])

    def test_makefile_surface_applies_only_makefile(self, tmp_path: Path) -> None:
        root = tmp_path / "demo-root"
        created = FlextInfraCodegenProjectNew(
            name="demo-root",
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
        custom_content = ".PHONY: public-handler\npublic-handler:\n\t@true\n"
        custom.write_text(custom_content, encoding="utf-8")
        (root / "Makefile").write_text("stale\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "tests@flext.sh"], cwd=root
            )
        )
        tm.ok(
            u.Cli.run_checked(["git", "config", "user.name", "FLEXT Tests"], cwd=root)
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        applied = tm.ok(result)
        tm.that(tuple(path.name for path in applied.written_files), eq=("Makefile",))
        tm.that(custom.read_text(encoding="utf-8"), eq=custom_content)


__all__: tuple[str, ...] = ()
