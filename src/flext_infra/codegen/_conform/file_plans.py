"""Desired-state file, environment, and retirement plans."""

from __future__ import annotations

from pathlib import Path

from flext_core import r

from ... import c, config, m, p, t, u
from .beads_routes import FlextInfraCodegenConformBeadsRoutes


class FlextInfraCodegenConformFilePlans(FlextInfraCodegenConformBeadsRoutes):
    """Desired-state file, environment, and retirement plans."""

    @classmethod
    def git_attributes_plans(
        cls,
        plan: m.Infra.CodegenPlan,
        phase_files: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Derive merge policy from full projections, preserving mixed files."""
        codegen = config.Infra.codegen
        template = (
            u.Infra.codegen_templates_root(codegen)
            / plan.make_spec.git_attributes_template
        )
        source = u.Cli.atomic_read_binary_file_state(template, required=True)
        if source.failure:
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(source)
        files = tuple(file for file in plan.files if file.policy == "full") + tuple(
            phase_files
        )
        result: list[m.Infra.CodegenFilePlan] = []
        for environment in plan.uv_environments:
            root = environment.project_root
            paths = sorted({
                "/" + file.path.relative_to(root).as_posix()
                for file in files
                if file.project == root
                and file.desired_content is not None
                and file.path != root / c.Infra.GITATTRIBUTES_FILENAME
            })
            patterns = tuple(u.Infra.git_attribute_pattern(path) for path in paths)
            rendered = u.Cli.template_render(
                template,
                m.Infra.MakeWorkflowRenderSpec(
                    dist=root.name, make=plan.make_spec, generated_paths=patterns
                ),
            )
            if rendered.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(
                    rendered
                )
            planned = cls.file_plan(
                root,
                c.Infra.GITATTRIBUTES_FILENAME,
                rendered.value,
                source_states=(source.value,),
            )
            if planned.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(planned)
            result.append(planned.value)
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(result))

    @staticmethod
    def file_plan(
        root: Path,
        relative_path: str,
        rendered: str,
        *,
        mode: int = 0o644,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Snapshot one target and bind it to exact desired bytes and mode."""
        project = root.expanduser().absolute()
        path = (project / relative_path).absolute()
        # Optional snapshots represent missing parents without effects. The
        # transaction journals and materializes directories before publication.
        before = u.Cli.atomic_read_binary_file_state(path, required=False)
        if before.failure:
            return r[m.Infra.CodegenFilePlan].from_failure(before)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                project=project,
                path=path,
                before=before.value,
                desired_content=rendered.encode(c.Cli.ENCODING_DEFAULT),
                desired_mode=mode,
                source_states=source_states,
            )
        )

    @staticmethod
    def mise_config_plans(
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Select one planned Mise configuration for each selected repository."""
        expected = tuple(
            environment.project_root / c.Infra.MISE_TOML_FILENAME
            for environment in plan.uv_environments
        )
        by_path = {item.path: item for item in plan.files if item.path in expected}
        if (
            len(expected) != len(plan.repositories)
            or len(set(expected)) != len(expected)
            or len(by_path) != len(expected)
        ):
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].fail(
                "conform plan must contain one Mise configuration per repository"
            )
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(
            tuple(by_path[path] for path in expected)
        )

    @staticmethod
    def uv_environment_plan(
        *,
        root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        config: m.Infra.CodegenConfigSpec,
    ) -> m.Infra.UvEnvironmentPlan:
        """Describe the exact setup overlay without executing uv."""
        workspace_environment = target.make_profile is c.Infra.MakeProfile.WORKSPACE
        groups: t.VariadicTuple[str] = ("dev", "codegen")
        editable_repositories: t.VariadicTuple[m.Infra.RepositoryRef] = ()
        if workspace_environment:
            groups = (*groups, "workspace")
            editable_repositories = tuple(
                item
                for item in (workspace.repository, *workspace.subprojects)
                if item.package and item.editable and not item.read_only
            )
        return m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=target.root,
            python_version=config.toolchain.python_version,
            groups=groups,
            editable_repositories=editable_repositories,
        )

    @staticmethod
    def _absent_file_plan(root: Path, path: Path) -> p.Result[m.Infra.CodegenFilePlan]:
        """Plan the removal of one retired projection."""
        return u.Infra.planned_file(
            root.expanduser().absolute(),
            path.expanduser().absolute(),
            required=True,
            desired_content=None,
            desired_mode=None,
        )

    @classmethod
    def retired_projection_plans(
        cls, root: Path, profile: c.Infra.MakeProfile
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan removal of generated projections excluded from this profile."""
        planned: list[m.Infra.CodegenFilePlan] = []
        for filename in (
            *config.Infra.codegen.toolchain.retired_dependency_artifacts,
            *config.Infra.codegen.retired_projections,
        ):
            relative = Path(filename)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or relative.as_posix() != filename
            ):
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"Retired projection must be a normalized relative path: {filename}"
                )
            path = root / filename
            if path.is_symlink() or (path.exists() and not path.is_file()):
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"Refusing non-file dependency artifact: {path}"
                )
            if not path.exists():
                continue
            absent_plan = cls._absent_file_plan(root, path)
            if absent_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    absent_plan
                )
            planned.append(absent_plan.value)
        for entry in config.Infra.codegen.templates.entries:
            if profile in entry.profiles or "{" in entry.destination:
                continue
            path = root / Path(entry.destination)
            if not path.is_file():
                continue
            current = u.Cli.files_read_text(path)
            if current.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(current)
            if not any(
                marker in current.value for marker in c.Infra.TEMPLATE_GENERATED_MARKERS
            ):
                continue
            absent_plan = cls._absent_file_plan(root, path)
            if absent_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    absent_plan
                )
            planned.append(absent_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))


__all__: list[str] = ["FlextInfraCodegenConformFilePlans"]
