"""Typed shared owners for codegen tests."""

from __future__ import annotations

from flext_infra import c, config, m, t


class CodegenTestSupport:
    """Own shared typed construction for codegen test contracts."""

    class Ci:
        """Construct GitHub workflow render contracts from canonical config."""

        @staticmethod
        def workflow_spec(
            *,
            dist: t.NonEmptyStr,
            make_profile: c.Infra.MakeProfile,
            repository_branch: t.NonEmptyStr,
            ci_trigger_branches: tuple[t.NonEmptyStr, ...],
            system_packages: tuple[t.NonEmptyStr, ...] = (),
        ) -> m.Infra.GithubWorkflowRenderSpec:
            """Build the common strictly typed workflow rendering contract."""
            codegen = config.Infra.codegen
            return m.Infra.GithubWorkflowRenderSpec(
                dist=dist,
                make_profile=make_profile,
                repository_branch=repository_branch,
                ci_trigger_branches=ci_trigger_branches,
                system_packages=system_packages,
                python_version=codegen.toolchain.python_version,
                mise_version=codegen.toolchain.mise_version,
                uv_version=codegen.toolchain.uv_version,
                dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
                github_actions=codegen.github_actions,
                make=codegen.make,
                workspace_repositories=(),
                checkout_submodules=codegen.checkout_submodules,
            )


__all__ = ["CodegenTestSupport"]
