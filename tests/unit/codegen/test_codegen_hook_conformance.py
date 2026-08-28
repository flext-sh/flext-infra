"""Behavioral contracts for generated Git-hook conformance."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

pytestmark = pytest.mark.slow

if TYPE_CHECKING:
    from flext_infra import p

_HOOK_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / ".pre-commit-config.yaml.j2"
)


class TestGitHookConformance:
    """Prove generated hook configs and installed shims converge together."""

    @staticmethod
    def _standalone_workspace(root: Path) -> m.Infra.WorkspaceSpec:
        """Load repository identity directly from its canonical metadata."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.PYPROJECT_FILENAME,
                '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
            )
        )
        return tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

    @staticmethod
    def _render_hooks(root: Path) -> str:
        """Render the manifest-owned hook artifact through the public owner."""
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo", make=config.Infra.codegen.make
                ),
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(root / ".pre-commit-config.yaml", rendered))
        return rendered

    @staticmethod
    def _check(
        root: Path, workspace: m.Infra.WorkspaceSpec
    ) -> p.Result[m.Infra.CodegenResult]:
        return FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            ),
            initial_workspace=workspace,
        )

    def test_check_never_requires_hook_shims_when_gates_are_off(
        self, infra_git_repo: Path
    ) -> None:
        """Operator law 2026-08-24: disabled stage gates demand no shims.

        Conform on this branch never installs git-hook shims (the generated
        install-git-hooks.sh script owns provisioning), and with both gates
        off the rendered config declares no stages, so an absent shim is not
        drift. The check may still report unrelated managed-file drift; it
        must never mention hook installation.
        """
        root = infra_git_repo
        workspace = self._standalone_workspace(root)
        self._render_hooks(root)

        result = self._check(root, workspace)

        if result.failure:
            tm.that(result.error or "", lacks="git hook is not installed")

    def test_apply_does_not_install_hook_shims(self, infra_git_repo: Path) -> None:
        """Apply materializes files only; hook provisioning is script-owned."""
        root = infra_git_repo
        workspace = self._standalone_workspace(root)
        hooks_dir = root / ".git" / "hooks"

        FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )

        for stage in ("pre-commit", "pre-push"):
            hook = hooks_dir / stage
            if hook.is_file():
                tm.that(hook.read_text(encoding="utf-8"), lacks=f"--hook-type={stage}")

    def test_generated_hooks_use_one_make_only_shell_per_step(
        self, infra_git_repo: Path
    ) -> None:
        """Generated hooks expose no executable path outside canonical Make.

        Why (operator law 2026-08-24): stage gates default off, so the step
        contract is proven on an explicitly enabled copy of the SSOT make spec.
        """
        root = infra_git_repo
        make = config.Infra.codegen.make.model_copy(
            update={"pre_commit": True, "pre_push": True}
        )
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(dist="flext-demo", make=make),
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(root / ".pre-commit-config.yaml", rendered))
        hook_contexts = {"pre_commit", "pre_push"}
        expected = sum(
            len(hook_contexts.intersection(step.contexts))
            for step in config.Infra.codegen.make.workflow
        )

        tm.that(rendered.count("bash -eu -o pipefail -c"), eq=expected)
        tm.that(rendered, lacks=".local")

    def test_check_and_apply_never_overwrite_foreign_hook_shims(
        self, infra_git_repo: Path
    ) -> None:
        """Conform never overwrites a foreign executable hook."""
        root = infra_git_repo
        workspace = self._standalone_workspace(root)
        self._render_hooks(root)
        hooks_dir = root / ".git" / "hooks"
        foreign = "#!/bin/sh\nexit 0\n"
        for stage in ("pre-commit", "pre-push"):
            (hooks_dir / stage).write_text(foreign, encoding="utf-8")

        self._check(root, workspace)
        FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )

        for stage in ("pre-commit", "pre-push"):
            tm.that((hooks_dir / stage).read_text(encoding="utf-8"), eq=foreign)

    def test_hook_stages_are_disabled_by_default(self) -> None:
        """Operator law 2026-08-24: both git-hook stage gates default to off."""
        make = config.Infra.codegen.make

        tm.that(make.pre_commit, eq=False)
        tm.that(make.pre_push, eq=False)

    def test_disabled_gates_render_no_hook_stages(self) -> None:
        """With both gates off the generated config carries zero hook steps."""
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo", make=config.Infra.codegen.make
                ),
            )
        )

        tm.that(rendered, lacks="stages: [pre-commit]")
        tm.that(rendered, lacks="stages: [pre-push]")
        tm.that(rendered, lacks="flext-pre-commit-")
        tm.that(rendered, lacks="flext-pre-push-")

    def test_enabled_gates_render_exactly_the_declared_stages(self) -> None:
        """Each gate renders exactly its configured workflow rows, no more."""
        make = config.Infra.codegen.make

        both = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo",
                    make=make.model_copy(update={"pre_commit": True, "pre_push": True}),
                ),
            )
        )
        expected = sum(
            len({"pre_commit", "pre_push"}.intersection(step.contexts))
            for step in make.workflow
        )
        tm.that(both.count("bash -eu -o pipefail -c"), eq=expected)

        commit_only = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(
                    dist="flext-demo", make=make.model_copy(update={"pre_commit": True})
                ),
            )
        )
        tm.that(commit_only, has="stages: [pre-commit]")
        tm.that(commit_only, lacks="stages: [pre-push]")


__all__: list[str] = ["TestGitHookConformance"]
