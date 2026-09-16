"""Gitignore rendering for conformed repositories."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u


class FlextInfraCodegenConformGitignoreMixin:
    """Gitignore rendering for conformed repositories."""

    @staticmethod
    def _package_root() -> Path:
        """Return the installed flext-infra package root."""
        return Path(__file__).resolve().parent.parent

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

        Public seam consumed by the layout engine: per-project
        layout ``gitignore_additions`` from the layout SSOT and the
        repository-owned ``ManagedArtifacts.Gitignore.patterns`` read from
        ``project_dir`` are appended as trailing derived sections so conform
        and layout never diverge.
        """
        entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.GITIGNORE
            ),
            None,
        )
        if entry is None:
            return r[str].fail(
                "gitignore template is missing from codegen configuration"
            )
        templates_root = (
            FlextInfraCodegenConformGitignoreMixin._package_root()
            / "templates"
            / codegen.templates.root
        ).resolve()
        project_patterns: t.StrSequence = ()
        if project_dir is not None:
            resolved = u.Infra.load_project_managed_artifacts(project_dir)
            if resolved.failure:
                return r[str].from_failure(resolved)
            project_patterns = resolved.value.artifacts.Gitignore.patterns
        context = m.Infra.GitignoreRenderSpec(
            gitignore_sections=FlextInfraCodegenConformGitignoreMixin._gitignore_sections(
                codegen,
                profile=profile,
                project_name=project_name,
                workspace=workspace,
                project_patterns=project_patterns,
            )
        )
        return u.Cli.template_render(templates_root / entry.source, context)
