"""Codegen manifest ownership inside linked worktrees."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


# Exemplar: conform materializes a full managed tree on disk, so the render
# itself dominates the runtime. The class declares its true end-to-end budget
# instead of raising the global unit-test timeout and masking real hangs.
@pytest.mark.slow
class TestCodegenLinkedWorktreeManifest:
    """Render generated artifacts from the active lane's declared manifest."""

    def test_conform_renders_the_lane_local_manifest(self, tmp_path: Path) -> None:
        """Use lane declarations while retaining the shared ledger database."""
        repository = test_u.Tests.repository_ref(config.Infra.name).model_copy(
            update={
                "path": Path(),
                "role": c.Infra.RepositoryRole.STANDALONE,
                "checkout": c.Infra.CheckoutKind.INDEPENDENT,
                "editable": False,
            }
        )
        primary = tmp_path / "primary"
        primary.mkdir()
        (primary / "pyproject.toml").write_text(
            f'[project]\nname = "{repository.distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        package_init = primary / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        package_init.write_text("", encoding="utf-8")
        spec = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.distribution,
            repository=repository,
            ledger_id="workspace-ledger",
            ledger_prefix="primary-prefix",
            repository_policy_overlays=(
                m.Infra.RepositoryPolicyOverlaySpec(
                    project=repository.distribution, beads_enabled=True
                ),
            ),
        )
        tm.ok(
            u.Cli.yaml_dump(
                primary / "config" / "workspace.yaml",
                spec.model_dump(
                    mode="json",
                    exclude_none=True,
                    exclude={"external_dependency_paths"},
                ),
            )
        )
        test_u.Tests.initialize_git_repo(primary, repository.url)
        lane = tmp_path / "lane"
        tm.ok(
            u.Infra.git_add_lane_worktree(
                m.Infra.GitWorktreeAddRequest(
                    repo_root=primary,
                    lane=lane,
                    branch="bugfix/lane",
                    base=c.Infra.GIT_HEAD,
                )
            )
        )
        loaded = tm.ok(u.Infra.workspace_spec_load(lane))
        tm.ok(
            u.Cli.yaml_dump(
                lane / "config" / "workspace.yaml",
                loaded.model_copy(update={"ledger_prefix": "lane-prefix"}).model_dump(
                    mode="json",
                    exclude_none=True,
                    exclude={"external_dependency_paths"},
                ),
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=lane,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )

        plan = tm.ok(FlextInfraCodegenConform(workspace_root=lane).plan(request))
        rendered = next(
            item.rendered
            for item in plan.files
            if item.path == lane / c.Infra.BEADS_CONFIG_RELPATH
        )

        tm.that(rendered, has='issue-prefix: "lane-prefix"')
        tm.that(rendered, has="database: workspace-ledger")
