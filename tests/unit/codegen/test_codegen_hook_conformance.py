"""Behavioral contracts for generated Git-hook conformance."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml
from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u as test_u

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
        """Load the smallest repository-local topology needed by conform."""
        test_u.Tests.write_project_beads_config(root, "flext-demo")
        (root / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
            encoding="utf-8",
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

        Conform never installs git-hook shims. With both gates off the rendered
        config declares no stages, so an absent shim is not drift. The check
        may still report unrelated managed-file drift; it
        must never mention hook installation.
        """
        root = infra_git_repo
        workspace = self._standalone_workspace(root)
        self._render_hooks(root)

        result = self._check(root, workspace)

        if result.failure:
            tm.that(result.error or "", lacks="git hook is not installed")

    def test_apply_does_not_install_hook_shims(self, infra_git_repo: Path) -> None:
        """Apply materializes files only and never provisions hook shims."""
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
        tm.that(rendered, lacks="fail-open")
        tm.that(rendered, lacks="2>/dev/null")
        tm.that(rendered, lacks="guard || exit 0")
        tm.that(rendered, has='gh pr list --head "$branch"')

    def test_pre_push_preserves_gh_failure_status(self, tmp_path: Path) -> None:
        """A failed draft-state query blocks the push before Make can run."""
        make = config.Infra.codegen.make.model_copy(update={"pre_push": True})
        rendered = tm.ok(
            u.Cli.template_render(
                _HOOK_TEMPLATE,
                m.Infra.MakeWorkflowRenderSpec(dist="flext-demo", make=make),
            )
        )
        document = yaml.safe_load(rendered)
        assert isinstance(document, dict)
        repositories = document.get("repos")
        assert isinstance(repositories, list)
        assert len(repositories) == 1
        (repository,) = repositories
        assert isinstance(repository, dict)
        hooks = repository.get("hooks")
        assert isinstance(hooks, list)
        selected = tuple(
            hook
            for hook in hooks
            if isinstance(hook, dict) and hook.get("id") == "flext-pre-push-gen"
        )
        tm.that(len(selected), eq=1)
        (hook,) = selected
        entry = hook.get("entry")
        assert isinstance(entry, str)

        fake_bin = tmp_path / "fake-bin"
        fake_bin.mkdir()
        fake_git = fake_bin / "git"
        fake_git.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "rev-parse" ] && [ "$2" = "--show-toplevel" ]; then pwd; exit 0; fi\n'
            'if [ "$1" = "branch" ] && [ "$2" = "--show-current" ]; then echo feature/test; exit 0; fi\n'
            'if [ "$1" = "rev-parse" ] && [ "$2" = "--local-env-vars" ]; then exit 0; fi\n'
            "exit 43\n",
            encoding="utf-8",
        )
        fake_gh = fake_bin / "gh"
        fake_gh.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
        fake_make = fake_bin / "make"
        fake_make.write_text(
            '#!/bin/sh\nprintf "called\\n" >"$MAKE_MARKER"\n', encoding="utf-8"
        )
        for executable in (fake_git, fake_gh, fake_make):
            executable.chmod(0o755)
        marker = tmp_path / "make-called"

        output = tm.ok(
            u.Cli.run_raw(
                ["bash", "-c", entry],
                cwd=tmp_path,
                env={
                    "MAKE_MARKER": str(marker),
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                },
            )
        )

        tm.that(output.exit_code, eq=42)
        tm.that(marker.exists(), eq=False)

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

    def test_member_hook_config_is_retired_by_conform(self, tmp_path: Path) -> None:
        """A workspace member keeps its own hook config; conform does not retire it."""
        root = tmp_path / "flext-member"
        root.mkdir()
        hook_config = root / ".pre-commit-config.yaml"
        hook_config.write_text(
            "# Generated by flext_infra codegen for flext-member — DO NOT EDIT\n"
            "repos: []\n",
            encoding="utf-8",
        )

        planned = FlextInfraCodegenConform.retired_projection_plans(
            root, c.Infra.MakeProfile.STANDALONE
        )

        retired = {plan.path for plan in tm.ok(planned) if plan.absent}
        tm.that(hook_config in retired, eq=False)

    def test_declared_retired_projection_is_planned_absent_by_identity(
        self, tmp_path: Path
    ) -> None:
        """Retire only a file carrying every marker declared by its old owner."""
        specs = tuple(
            item
            for item in config.Infra.codegen.retired_projections
            if item.path.name == "check-beads-policy.sh"
        )
        tm.that(len(specs), eq=1)
        (spec,) = specs
        target = tmp_path / spec.path
        target.parent.mkdir(parents=True)
        target.write_text("\n".join(spec.markers), encoding="utf-8")

        planned = tm.ok(
            FlextInfraCodegenConform.retired_projection_plans(
                tmp_path, c.Infra.MakeProfile.STANDALONE
            )
        )

        absent = tuple(plan for plan in planned if plan.path == target and plan.absent)
        tm.that(len(absent), eq=1)

    def test_retired_projection_identity_mismatch_fails_without_deletion(
        self, tmp_path: Path
    ) -> None:
        """A foreign file at a retired path blocks mutation and remains intact."""
        specs = tuple(
            item
            for item in config.Infra.codegen.retired_projections
            if item.path.name == "install-git-hooks.sh"
        )
        tm.that(len(specs), eq=1)
        (spec,) = specs
        target = tmp_path / spec.path
        target.parent.mkdir(parents=True)
        target.write_text("foreign owner\n", encoding="utf-8")

        result = FlextInfraCodegenConform.retired_projection_plans(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )

        tm.fail(result, has="retired projection identity mismatch")
        tm.that(target.read_text(encoding="utf-8"), eq="foreign owner\n")


__all__: list[str] = ["TestGitHookConformance"]
