"""Typed shared owners for codegen tests."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, config, m, t


class CodegenTestSupport:
    """Own shared typed construction for codegen test contracts."""

    class Ci:
        """Construct GitHub workflow render contracts from canonical config."""

        # Why: ci_trigger_branches is no longer config-owned (flext-jwpyy.1
        # relocated it from BranchPolicySpec to a per-render derivation in
        # FlextInfraCodegenConform._artifact_render_context). Mirror the exact
        # literal baseline conform.py renders so tests stay in lockstep with
        # production without reading a retired config field.
        CI_TRIGGER_BASELINE_BRANCHES: ClassVar[tuple[str, ...]] = (
            "dev",
            "develop",
            "0.12.0-dev",
            "main",
        )

        @classmethod
        def ci_trigger_branches(cls, repository_branch: str) -> tuple[str, ...]:
            """Reproduce conform.py's deduplicated per-render trigger set."""
            return tuple(
                dict.fromkeys((
                    *cls.CI_TRIGGER_BASELINE_BRANCHES[:-1],
                    repository_branch,
                    cls.CI_TRIGGER_BASELINE_BRANCHES[-1],
                ))
            )

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
                state_directory_name=codegen.toolchain.state_directory_name,
                dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
                github_actions=codegen.github_actions,
                make=codegen.make,
                workspace_repositories=(),
                checkout_submodules=codegen.checkout_submodules,
            )


__all__ = ["CodegenTestSupport"]
