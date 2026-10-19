"""Pyproject, tooling-root, and custom Make policy projections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen._conform import FlextInfraCodegenConformFilePlans
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.workspace import FlextInfraBindingService, FlextInfraWorkspaceDetector


class FlextInfraCodegenConformPyprojectPolicy(FlextInfraCodegenConformFilePlans):
    """Pyproject, tooling-root, and custom Make policy projections."""

    def native_resolution_plans(
        self,
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        inputs: m.Infra.CodegenInputs,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        rendered_by: str,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan both native resolver inputs from this generation's desired sources.

        The complete repository plan supplies desired member metadata before
        publication. Reading an older member document here would make the
        workspace view drift as soon as that same transaction published it.
        Locks remain exclusively owned by the upgrade lifecycle.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        sources: list[m.Cli.AtomicFileState] = list(inputs.sources)
        projects = self._collected_resolution_projects(
            root,
            workspace,
            planned,
            sources,
        )
        if projects.failure:
            return result_type.from_failure(projects)
        suppliers: list[m.Infra.UvResolutionProject] = []
        supplier_root = inputs.spec.make.uv_resolution.editable_supplier_root
        if supplier_root is not None:
            collected = self._collected_supplier_projects(root, supplier_root, sources)
            if collected.failure:
                return result_type.from_failure(collected)
            suppliers = collected.value
        authenticated = FlextInfraCodegenPreconditions.unique_states(tuple(sources))
        if authenticated.failure:
            return result_type.from_failure(authenticated)
        return self._planned_resolution_files(
            [*projects.value, *suppliers],
            authenticated.value,
            inputs,
            rendered_by,
            workspace=workspace,
        )

    @classmethod
    def _collected_supplier_projects(
        cls,
        root: Path,
        supplier_root: Path,
        sources: list[m.Cli.AtomicFileState],
    ) -> p.Result[list[m.Infra.UvResolutionProject]]:
        """Authenticate active external suppliers and their generation inputs.

        Returns:
            Selected runtime suppliers or the first discovery failure.

        """
        result_type = r[list[m.Infra.UvResolutionProject]]
        runtime = FlextInfraWorkspaceDetector.resolution_context(root)
        if runtime.failure:
            return result_type.from_failure(runtime)
        targets = FlextInfraBindingService.plan_targets(
            consumer_root=root,
            flext_root=supplier_root,
            python=u.Infra.runtime_python(
                root, runtime_root=runtime.value.runtime_root
            ),
        )
        if targets.failure:
            return result_type.from_failure(targets)
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(supplier_root)
        if workspace.failure:
            return result_type.from_failure(workspace)
        inputs = u.Infra.load_codegen_inputs(supplier_root)
        if inputs.failure:
            return result_type.from_failure(inputs)
        sources.extend(inputs.value.sources)
        captured = u.Cli.atomic_read_binary_file_state(
            supplier_root / ".gitmodules", required=True
        )
        if captured.failure:
            return result_type.from_failure(captured)
        sources.append(captured.value)
        return cls._collected_resolution_projects(
            supplier_root,
            workspace.value,
            (),
            sources,
            selected_names=targets.value,
        ).map(
            lambda projects: [
                item.model_copy(update={"role": "supplier"}) for item in projects
            ]
        )

    @staticmethod
    def _collected_resolution_projects(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        sources: list[m.Cli.AtomicFileState],
        *,
        selected_names: t.StrSequence | None = None,
    ) -> p.Result[list[m.Infra.UvResolutionProject]]:
        """Collect every member's resolution project and consulted sources.

        Args:
            root: Resolved repository root of the workspace.
            workspace: Loaded workspace specification.
            planned: Desired file plans of the complete repository plan.
            sources: Mutable source list extended with every consulted state.

        Returns:
            The owner-first resolution projects, or the first collection
            failure.

        """
        result_type = r[list[m.Infra.UvResolutionProject]]
        desired = {file.path: file for file in planned}
        projects: list[m.Infra.UvResolutionProject] = []
        for repository in (workspace.repository, *workspace.subprojects):
            if (
                selected_names is not None
                and u.Infra.dep_name(repository.distribution) not in selected_names
            ):
                continue
            if repository is not workspace.repository and not repository.package:
                continue
            directory = (
                root if repository is workspace.repository else root / repository.path
            ).resolve()
            path = directory / c.PYPROJECT_FILENAME
            projected = desired.get(path)
            if projected is None:
                captured = u.Cli.atomic_read_binary_file_state(path, required=True)
                if captured.failure:
                    return result_type.from_failure(captured)
                state = captured.value
                content = state.content
            else:
                before = projected.before
                if isinstance(before, m.Cli.AtomicDirectoryChainPlan):
                    # An absent-leaf plan cannot authenticate a consulted input.
                    return result_type.fail(
                        f"native resolution input is absent: {path}",
                    )
                state = before
                content = projected.desired_content
                sources.extend(projected.source_states)
            if content is None:
                return result_type.fail(
                    f"native resolution input is absent: {path}",
                )
            document = u.Cli.toml_parse_text(content.decode(c.DEFAULT_ENCODING))
            if document is None:
                return result_type.fail(
                    f"native resolution input is not valid TOML: {path}",
                )
            sources.append(state)
            projects.append(
                m.Infra.UvResolutionProject(
                    repository=repository,
                    directory=directory,
                    document=document,
                ),
            )
        return result_type.ok(projects)

    def _planned_resolution_files(
        self,
        projects: t.SequenceOf[m.Infra.UvResolutionProject],
        authenticated: t.VariadicTuple[m.Cli.AtomicFileState],
        inputs: m.Infra.CodegenInputs,
        rendered_by: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan both managed native resolution views.

        Args:
            projects: The owner-first resolution projects of the workspace.
            authenticated: Authenticated source states binding both views.
            inputs: Loaded codegen inputs owning the resolution policy.
            rendered_by: Render-provenance line of the running generator.
            workspace: Authenticated composition electing remote member sources.

        Returns:
            The managed resolution view plans, or the first planning failure.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        policy = inputs.spec.make.uv_resolution
        catalogue = {item.path: item for item in inputs.spec.managed_file_specs}
        owner, *members = projects
        local_members = tuple(item for item in members if item.role == "member")
        root = owner.directory
        files: list[m.Infra.CodegenFilePlan] = []
        views = (
            (policy.local_directory, local_members),
            (policy.standalone_directory, ()),
            *(
                ((policy.editable_directory, tuple(members)),)
                if policy.editable_supplier_root is not None
                else ()
            ),
        )
        for relative, selected in views:
            destination = relative / c.PYPROJECT_FILENAME
            metadata = catalogue.get(destination)
            if metadata is None:
                return result_type.fail(
                    f"native resolution view has no managed owner: {destination}",
                )
            path = (root / destination).resolve()
            if not path.is_relative_to(root.resolve()):
                return result_type.fail(
                    f"native resolution view escapes its repository: {path}",
                )
            formatted = self._rendered_resolution_source(
                owner,
                selected,
                path.parent,
                inputs,
                workspace=workspace,
            )
            if formatted.failure:
                return result_type.from_failure(formatted)
            file = self.file_plan(
                root,
                destination.as_posix(),
                (f"{c.Infra.BANNER}{rendered_by}\n{formatted.value.lstrip()}"),
                mode=metadata.mode,
                source_states=authenticated,
            )
            if file.failure:
                return result_type.from_failure(file)
            files.append(
                file.value.model_copy(
                    update={
                        "owner": metadata.owner,
                        "policy": metadata.policy,
                        "tracking": metadata.tracking,
                    },
                ),
            )
        return result_type.ok(tuple(files))

    def _rendered_resolution_source(
        self,
        owner: m.Infra.UvResolutionProject,
        members: t.VariadicTuple[m.Infra.UvResolutionProject],
        directory: Path,
        inputs: m.Infra.CodegenInputs,
        *,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[str]:
        """Render and format one native resolution view's TOML source.

        Args:
            owner: The workspace owner resolution project.
            members: The member resolution projects rendered into the view.
            directory: Destination directory of the view.
            inputs: Loaded codegen inputs owning the resolution policy.
            workspace: Authenticated composition electing remote member sources.

        Returns:
            The formatted view source, or the first render or format failure.

        """
        rendered = u.Infra.pyproject_native_resolution_view(
            owner,
            workspace=workspace,
            members=members,
            directory=directory,
            policy=inputs.spec.make.uv_resolution,
        )
        if rendered.failure:
            return r[str].from_failure(rendered)
        return u.Infra.format_toml_source(
            u.Cli.toml_dumps(rendered.value),
            path=directory / c.PYPROJECT_FILENAME,
            toolchain_root=self.state.repository_root,
            taplo_version=inputs.spec.toolchain.tool_versions["taplo"],
        )

    @staticmethod
    def _scaffold_python_dirs(
        entries: t.SequenceOf[p.Infra.TemplateEntrySpec],
        profile: c.Infra.MakeProfile,
        *,
        package: bool = True,
    ) -> t.StrSequence:
        """Return Python roots the selected scaffold manifest actually creates.

        Returns:
            Python roots the selected scaffold manifest actually creates.

        """
        # Derive future roots from both
        # declarative owners so scaffold and existing-tree discovery converge.
        generated_roots = {
            Path(entry.destination).parts[0]
            for entry in entries
            if profile in entry.profiles
            and entry.delegate == c.Infra.TemplateDelegate.RENDER
            and Path(entry.destination).parts
        }
        # An existing package:false repository (a solo workspace root)
        # materializes no package source dir: its manifest declares no
        # importable package, so analyzers must not include it — pyright
        # fails hard on an include entry whose directory does not exist.
        # The atomic scaffold path never passes ``package=False``: its own
        # manifest renders the source tree, and dropping ``src`` there made
        # the first plan fall back to disk discovery for mypy/pyrefly search
        # paths, which oscillates once the scaffold's directory chain exists.
        source_dir = config.Infra.tooling.tools.pyright.path_rules.source_dir
        return tuple(
            directory
            for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
            if directory in generated_roots and (package or directory != source_dir)
        )

    @classmethod
    def conformed_pyproject_source(
        cls,
        source: str,
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        member_declarations: t.VariadicTuple[m.Cli.AtomicFileState] | None = None,
    ) -> p.Result[str]:
        """Conform one pyproject source.

        Returns:
            The resulting ``p.Result[str]``.

        """
        flext_line = u.Infra.flext_integration_line_for_checkout(
            codegen=codegen,
            repository_root=target.root,
            workspace=workspace,
        )
        if flext_line.failure:
            return r[str].from_failure(flext_line)
        if workspace.integration is None:
            # Attached members render on the workspace's own integration line
            # (a governed .gitmodules branch must equal it), derived from the
            # checkout when the manifest does not declare it.
            branch = u.Infra.resolve_integration_branch(
                target.root,
                policy_branch=codegen.branch_policy.integration_branch,
            )
            if branch.failure:
                return r[str].from_failure(branch)
            workspace = workspace.model_copy(
                update={
                    "integration": m.Infra.WorkspaceIntegrationSpec(
                        provider=workspace.repository.provider,
                        branch=branch.value,
                    ),
                },
            )
        return u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=u.Infra.project_development_requirements(
                codegen.scaffold.project,
                distribution=target.repository.distribution,
                kind=target.repository.kind,
            ),
            uv_resolution=m.Infra.UvResolutionSpec(
                link_mode=cls.link_mode(target.repository, codegen.toolchain),
                constraint_dependencies=tuple(
                    codegen.toolchain.uv_constraint_dependencies,
                ),
                override_dependencies=tuple(
                    codegen.toolchain.uv_override_dependencies,
                ),
                environments=tuple(codegen.toolchain.uv_environments),
            ),
            options=u.Infra.PyprojectConformOptions(
                flext_line=flext_line.value,
                repository_root=target.root,
                member_declarations=member_declarations,
            ),
        )

    @classmethod
    def validate_custom_make(
        cls,
        content: str,
        policy: m.Infra.CustomHandlerPolicy,
    ) -> p.Result[bool]:
        """Reject public targets, aliases, includes, and toolchain declarations.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        target_re = re.compile(policy.target_pattern)
        logical_lines = cls._logical_make_lines(content, policy)
        if logical_lines.failure:
            return r[bool].from_failure(logical_lines)
        in_define = False
        for line_number, raw_line in logical_lines.value:
            if in_define:
                in_define = not raw_line.startswith("endef")
                continue
            if raw_line.startswith("define "):
                if not policy.allow_toolchain_declarations:
                    return r[bool].fail(
                        f"{policy.filename} line {line_number} "
                        "declares a macro, which this profile forbids",
                    )
                in_define = True
                continue
            if cls._skippable_make_line(raw_line):
                continue
            verdict = cls._judge_make_line(target_re, policy, line_number, raw_line)
            if verdict is not None:
                return verdict
        return r[bool].ok(value=True)

    @staticmethod
    def _judge_make_line(
        target_re: re.Pattern[str],
        policy: m.Infra.CustomHandlerPolicy,
        line_number: int,
        raw_line: str,
    ) -> p.Result[bool] | None:
        """Judge one logical make line against the custom-handler policy.

        Returns:
            The resulting ``p.Result[bool] | None`` where None accepts the
            line and continues validation.

        """
        phony_names = (
            raw_line.partition(":")[2].strip().split()
            if raw_line.startswith(".PHONY:")
            else None
        )
        target = raw_line.partition(":")[0].strip() if ":" in raw_line else ""
        banned = target in {"pre-commit", "_custom-pre-commit"} or (
            phony_names is not None
            and bool({"pre-commit", "_custom-pre-commit"} & set(phony_names))
        )
        if banned:
            return r[bool].fail("mandatory approval cannot be a custom target")
        if phony_names is not None:
            if phony_names and all(target_re.fullmatch(name) for name in phony_names):
                return None
        elif target and target_re.fullmatch(target):
            return None
        if c.Infra.MAKE_ASSIGNMENT_RE.match(
            raw_line,
        ) or c.Infra.MAKE_DIRECTIVE_RE.match(raw_line):
            return (
                None
                if policy.allow_toolchain_declarations
                else r[bool].fail(
                    f"{policy.filename} line {line_number} "
                    "declares a variable, which this profile forbids",
                )
            )
        if target and policy.allow_public_targets:
            return None
        return r[bool].fail(
            f"{policy.filename} line {line_number} is not a private custom handler",
        )

    @staticmethod
    def _skippable_make_line(raw_line: str) -> bool:
        """Whether a logical make line carries no handler-decision weight.

        Returns:
            The resulting ``bool``.

        """
        if not raw_line or raw_line.lstrip().startswith("#"):
            return True
        if raw_line[0].isspace():
            return True
        return bool(c.Infra.MAKE_CONDITIONAL_RE.match(raw_line))

    @staticmethod
    def _logical_make_lines(
        content: str,
        policy: m.Infra.CustomHandlerPolicy,
    ) -> p.Result[t.VariadicTuple[t.Pair[int, str]]]:
        """Collapse backslash continuations into reportable logical lines.

        Only non-recipe lines collapse (recipe lines start with whitespace and
        are skipped by the validator); the reported line number is the first
        physical line. A continuation collapses several physical lines into
        one logical line, which is reported at the line the continuation
        STARTED on, not the line it ended on. Assigning back onto the loop
        variables made the two indistinguishable and left the next iteration
        reading a value the iterator never produced.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[int, str]]]``.

        """
        result_type = r[t.VariadicTuple[t.Pair[int, str]]]
        logical_lines: list[t.Pair[int, str]] = []
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
                return result_type.fail(
                    f"{policy.filename} has an unterminated .PHONY continuation",
                )
            logical_lines.append((pending_number, pending_line))
        return result_type.ok(tuple(logical_lines))


__all__: list[str] = ["FlextInfraCodegenConformPyprojectPolicy"]
