"""Beads routes, docs ownership, and projection plan helpers"""

from __future__ import annotations

import re
import time
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, override

from ... import c, config, m, p, r, s, t, u
from ...deps import FlextInfraEnsureRuffConfigPhase, FlextInfraPyprojectModernizer
from ...docs import FlextInfraDocGenerator
from ...services.codegen import FlextInfraCodegen
from ...workspace import FlextInfraWorkspaceDetector
from .. import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from .._conform_gitignore import FlextInfraCodegenConformGitignoreMixin

if TYPE_CHECKING:
    from .base import FlextInfraCodegenConform



from .bootstrap import FlextInfraCodegenConformBootstrap
from .execute import FlextInfraCodegenConformExecute

class FlextInfraCodegenConformMisc:
    """Beads routes, docs ownership, and projection plan helpers."""
    @staticmethod
    def _member_repository_roots(
        request: m.Infra.CodegenConformRequest, plan: m.Infra.CodegenPlan
    ) -> tuple[Path, ...]:
        """Return the physical roots of the declared member repositories."""
        return tuple(
            (request.root / repository.path).resolve()
            for repository in plan.repositories
            if repository.path != Path()
        )
    @classmethod
    def _owned_docs_files(
        cls,
        request: m.Infra.CodegenConformRequest,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Keep only docs plans owned by the invoked repository's own scope.

        Member repositories declared ``codegen: conform`` are self-governing:
        their generated docs (``mkdocs.yml``, ``docs/api-reference/generated/**``)
        are planned and published exclusively by the member's own conform run.
        The planner already stamps each docs plan with its physical owning
        project root, so the workspace-root conform drops every plan whose
        owner is a member; otherwise the root and member scopes publish
        different content to the same file and gen never reaches a fixed
        point across the root and member CI gates.
        """
        root = request.root.resolve()
        return tuple(file for file in files if file.project.resolve() == root)
    @classmethod
    def _owned_docs_directories(
        cls,
        request: m.Infra.CodegenConformRequest,
        plan: m.Infra.CodegenPlan,
        directories: t.SequenceOf[Path],
    ) -> tuple[Path, ...]:
        """Keep only docs directory chains inside the invoked repository."""
        root = request.root.resolve()
        member_roots = cls._member_repository_roots(request, plan)
        owned: list[Path] = []
        for directory in directories:
            resolved = directory.resolve()
            if root not in resolved.parents:
                continue
            if any(member in resolved.parents for member in member_roots):
                continue
            owned.append(directory)
        return tuple(owned)
    def _conform_workspace_beads_routes(
        self, request: m.Infra.CodegenConformRequest
    ) -> p.Result[bool]:
        """Reconcile private metadata directories without cross-project links.

        A composed project follows the workspace ledger through its own rendered
        ``.beads`` configuration, which every checkout resolves identically. It
        previously followed the ledger through ``.beads -> ../.beads``, a link
        escaping into another repository: a second owner of a fact the
        configuration already declares, resolvable only on one machine's exact
        layout, and invisible to review because it reads as a directory. This
        method used to create those links and delete the real directory first;
        now it proves none survive and enforces the client's private-directory
        contract after publication, for the root and its composed members.
        """
        root = request.root.expanduser().resolve()
        workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if workspace_result.failure:
            return r[bool].from_failure(workspace_result)
        workspace = workspace_result.value
        owner = root / c.Infra.BEADS_DIRNAME
        # The ledger directory is a conform projection: absent before the
        # first render is normal; a link, or a non-directory, is not physical.
        if owner.is_symlink() or (owner.exists() and not owner.is_dir()):
            return r[bool].fail(
                f"workspace Beads ledger owner is not physical: {owner}"
            )
        if owner.is_dir():
            owner.chmod(c.Infra.BEADS_DIRECTORY_MODE)
        for repository in workspace.subprojects:
            state = self._beads_route_state(
                (root / repository.path).resolve()
            )
            if state.failure:
                return state
        return r[bool].ok(True)
    @staticmethod
    def _beads_route_state(root: Path) -> p.Result[bool]:
        """Prove one repository reaches the ledger through its own directory.

        The route used to be a symlink into the workspace, so the directory
        always existed by the time anything rendered into it. Each repository
        now owns a real ``.beads`` holding its own generated configuration, and
        a generator owns the destination directory of the artifacts it
        declares: without it the first render fails reading a before-state
        whose parent is missing. The directory is created empty;
        ``.beads/config.yaml`` and ``.beads/metadata.json`` are rendered into
        it by generation, never copied and never linked.
        """
        allowed_entries = frozenset({
            Path(c.Infra.BEADS_CONFIG_RELPATH).name,
            Path(c.Infra.BEADS_METADATA_RELPATH).name,
            c.Infra.BEADS_LOCAL_VERSION_FILENAME,
            c.Infra.BEADS_LAST_TOUCHED_FILENAME,
        })
        route = root / c.Infra.BEADS_DIRNAME
        if route.is_symlink():
            return r[bool].fail(
                "composed project reaches the workspace ledger through a "
                f"cross-project symbolic link: {route}"
            )
        if not route.exists():
            route.mkdir(mode=c.Infra.BEADS_DIRECTORY_MODE, parents=True)
            return r[bool].ok(True)
        if not route.is_dir():
            return r[bool].fail(
                f"composed project Beads route is not a directory: {route}"
            )
        unexpected = sorted(
            entry.name
            for entry in route.iterdir()
            if entry.name not in allowed_entries
            and not FlextInfraCodegenConform._is_dry_run_config_backup(entry.name)
        )
        if unexpected:
            return r[bool].fail(
                f"composed project has unmerged Beads state at {route}: "
                + ", ".join(unexpected)
            )
        route.chmod(c.Infra.BEADS_DIRECTORY_MODE)
        return r[bool].ok(True)
    @staticmethod
    def _mise_config_plans(
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
            return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                "conform plan must contain one Mise configuration per repository"
            )
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(
            tuple(by_path[path] for path in expected)
        )
    @staticmethod
    def _scaffold_python_dirs(
        entries: t.SequenceOf[p.Infra.TemplateEntrySpec], profile: c.Infra.MakeProfile
    ) -> t.StrSequence:
        """Return Python roots the selected scaffold manifest actually creates."""
        # Derive future roots from both
        # declarative owners so scaffold and existing-tree discovery converge.
        generated_roots = {
            Path(entry.destination).parts[0]
            for entry in entries
            if profile in entry.profiles
            and entry.delegate == "render"
            and Path(entry.destination).parts
        }
        return tuple(
            directory
            for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
            if directory in generated_roots
        )
    @staticmethod
    def _conformed_pyproject_source(
        source: str,
        *,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        workspace_mode: c.Infra.MakeProfile,
        uv_exclude_dependencies: t.VariadicTuple[
            m.Infra.UvScopedDependencyExclusionSpec
        ],
    ) -> p.Result[str]:
        """Conform one pyproject source."""
        return u.Infra.pyproject_conform(
            source,
            providers=codegen.providers,
            workspace=workspace,
            workspace_mode=workspace_mode,
            toolchain=codegen.toolchain,
            required_dev_dependencies=codegen.scaffold.project.dev,
            uv_link_mode=FlextInfraCodegenConform._link_mode(
                repository, codegen.toolchain
            ),
            uv_exclude_dependencies=uv_exclude_dependencies,
            namespace_scan_dirs=(
                workspace.project.namespace_scan_dirs
                if workspace.project is not None
                else None
            ),
        )
    @staticmethod
    def _routed_uv_exclude_dependencies(
        *,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> t.VariadicTuple[m.Infra.UvScopedDependencyExclusionSpec]:
        """Return the uv dependency exclusions routed to one repository.

        Workspace root owns resolution for attached subprojects (uv reads
        exclude-dependencies only from the workspace root). Subprojects still
        receive their own routed excludes for standalone CI clones.
        """
        if target.make_profile is c.Infra.MakeProfile.WORKSPACE:
            return tuple(codegen.uv_exclude_dependencies)
        return tuple(
            item
            for item in codegen.uv_exclude_dependencies
            if item.project == repository.distribution
        )
    @staticmethod
    def _file_plan(
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
        # Generation owns the destination directory of every artifact it
        # declares. Reading the before-state of a declared file whose parent
        # does not exist yet fails on the missing parent rather than reporting
        # an absent file, so a repository that has never rendered a nested
        # artifact — `.beads/config.yaml` on a fresh clone — could not even be
        # planned. Materializing the empty destination is idempotent and is the
        # generator's own responsibility.
        path.parent.mkdir(parents=True, exist_ok=True)
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
    def _uv_environment_plan(
        *,
        root: Path,
        repository_root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        config: m.Infra.CodegenConfigSpec,
    ) -> m.Infra.UvEnvironmentPlan:
        """Describe the exact setup overlay without executing uv."""
        del repository_root
        workspace_environment = target.make_profile is c.Infra.MakeProfile.WORKSPACE
        environment_root = target.root
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
            environment_root=environment_root,
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
        codegen = config.Infra.codegen
        planned: list[m.Infra.CodegenFilePlan] = []
        for entry in codegen.templates.entries:
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
    @staticmethod
    def validate_custom_make(
        content: str, policy: m.Infra.CustomHandlerPolicy
    ) -> p.Result[bool]:
        """Reject public targets, aliases, includes, and toolchain declarations."""
        target_re = re.compile(policy.target_pattern)
        in_define = False
        # Collapse backslash continuation lines before validating so that
        # directives like `.PHONY` can span multiple physical lines. Only
        # collapse non-recipe lines (recipe lines start with whitespace and are
        # skipped below); the reported line number is the first physical line.
        logical_lines: list[tuple[int, str]] = []
        pending_line: str | None = None
        pending_number: int = 0
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if (
                raw_line
                and not raw_line[0].isspace()
                and raw_line.rstrip().endswith("\\")
            ):
                trimmed = raw_line.rstrip()[:-1].rstrip()
                if pending_line is None:
                    pending_line = trimmed
                    pending_number = line_number
                else:
                    pending_line += " " + trimmed
                continue
            # A continuation collapses several physical lines into one logical
            # line, which is reported at the line the continuation STARTED on,
            # not the line it ended on. Assigning back onto the loop variables
            # made the two indistinguishable and left the next iteration reading
            # a value the iterator never produced.
            logical_line = raw_line
            logical_number = line_number
            if pending_line is not None:
                joined = pending_line + " " + raw_line.strip()
                if joined.rstrip().endswith("\\"):
                    pending_line = joined.rstrip()[:-1].rstrip()
                    continue
                logical_line = joined
                logical_number = pending_number
                pending_line = None
            logical_lines.append((logical_number, logical_line))
        if pending_line is not None:
            if pending_line.startswith(".PHONY:"):
                return r[bool].fail(
                    f"{policy.filename} has an unterminated .PHONY continuation"
                )
            logical_lines.append((pending_number, pending_line))
        for line_number, raw_line in logical_lines:
            if in_define:
                in_define = not raw_line.startswith("endef")
                continue
            if raw_line.startswith("define "):
                if not policy.allow_toolchain_declarations:
                    return r[bool].fail(
                        f"{policy.filename} line {line_number} "
                        "declares a macro, which this profile forbids"
                    )
                in_define = True
                continue
            if not raw_line or raw_line.lstrip().startswith("#"):
                continue
            if raw_line[0].isspace():
                continue
            if c.Infra.MAKE_CONDITIONAL_RE.match(raw_line):
                continue
            if raw_line.startswith(".PHONY:"):
                declaration = raw_line.partition(":")[2].strip()
                names = declaration.split()
                if names and all(target_re.fullmatch(name) for name in names):
                    continue
            target = raw_line.partition(":")[0].strip() if ":" in raw_line else ""
            if target and target_re.fullmatch(target):
                continue
            if c.Infra.MAKE_ASSIGNMENT_RE.match(
                raw_line
            ) or c.Infra.MAKE_DIRECTIVE_RE.match(raw_line):
                if policy.allow_toolchain_declarations:
                    continue
                return r[bool].fail(
                    f"{policy.filename} line {line_number} "
                    "declares a variable, which this profile forbids"
                )
            if target and policy.allow_public_targets:
                continue
            return r[bool].fail(
                f"{policy.filename} line {line_number} is not a private custom handler"
            )
        return r[bool].ok(True)
