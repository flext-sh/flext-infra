"""Gitignore rendering for conformed repositories."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t, u


class FlextInfraCodegenConformGitignoreMixin:
    """Gitignore rendering for conformed repositories."""

    @staticmethod
    def render_project_gitignore(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec | None = None,
        project_dir: Path | None = None,
    ) -> p.Result[str]:
        """Render the canonical ``.gitignore`` for one named project.

        Thin delegating wrapper to the canonical utility owner (u.Infra).
        """
        return u.Infra.render_project_gitignore(
            codegen,
            profile=profile,
            project_name=project_name,
            workspace=workspace,
            project_dir=project_dir,
        )

    @staticmethod
    def _gitignore_sections(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str | None = None,
        workspace: m.Infra.WorkspaceSpec | None = None,
        project_patterns: t.StrSequence = (),
    ) -> t.VariadicTuple[m.Infra.ScaffoldGitignoreSectionSpec]:
        """Derive the ordered ``.gitignore`` sections for one project.

        Thin delegating wrapper to the canonical utility owner (u.Infra).
        """
        return u.Infra.gitignore_sections(
            codegen,
            profile=profile,
            project_name=project_name,
            workspace=workspace,
            project_patterns=project_patterns,
        )


__all__: list[str] = ["FlextInfraCodegenConformGitignoreMixin"]
