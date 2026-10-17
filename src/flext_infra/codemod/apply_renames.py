"""Transactional CSV campaigns using existing Rope and publication primitives.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from contextlib import closing
from os.path import commonpath
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra._utilities._rope.project import FlextInfraRopeProject
from flext_infra.codemod import FlextInfraRenameSources, FlextInfraRenameSymbols
from flext_infra.transformers import FlextInfraSemanticPublication


class FlextInfraApplyRenames:
    """Plan against authenticated bytes and commit only after a real post-scan."""

    @staticmethod
    def _consumer_roots(params: m.Infra.ApplyRenamesInput) -> t.VariadicTuple[Path]:
        """Elect the complete declared composition without widening prose edits.

        Returns:
            Requested roots and their canonical native consumers.

        """
        requested = {Path(value).resolve() for value in params.roots}
        return tuple(
            sorted(
                requested
                | {
                    project
                    for path in requested
                    if params.bindings
                    for project in u.Infra.import_project_roots(
                        path, include_consumers=True
                    )
                }
            )
        )

    @classmethod
    def _plan(
        cls,
        params: m.Infra.ApplyRenamesInput,
        roots: t.SequenceOf[Path],
        pairs: t.SequenceOf[t.Pair[str, str]],
    ) -> t.Triple[
        t.VariadicTuple[m.Infra.SemanticFilePlan],
        int,
        Callable[[], p.Result[bool]],
    ]:

        inventory = FlextInfraRenameSources.inventory(roots, params)
        sources = {
            path: state.content.decode(c.DEFAULT_ENCODING)
            for path, state in inventory.items()
            if state.content is not None
        }
        python = {
            path: source
            for path, source in sources.items()
            if path.suffix == c.Infra.EXT_PYTHON
        }
        root = Path(commonpath(roots))
        plans: t.MutableSequenceOf[m.Infra.SemanticFilePlan] = []
        occurrences = 0
        symbols: t.MutableMappingKV[Path, list[m.Infra.SourceRewrite]] = {}
        guards: list[Callable[[], None]] = []
        dependencies = list(inventory.values())
        for consumer in roots if params.bindings else ():
            with (
                u.Infra.open_project(
                    root,
                    project_roots=roots,
                    consumer_root=consumer,
                ) as live,
                closing(
                    FlextInfraRopeProject.from_atomic_reads(
                        live,
                        tuple(inventory.values()),
                        election=m.Infra.RopeProjectElection(
                            source_folders=tuple(
                                folder.path for folder in live.get_source_folders()
                            ),
                            ignored_resources=tuple(
                                u.type_adapter(list[str]).validate_python(
                                    live.get_prefs().get("ignored_resources"),
                                    strict=True,
                                )
                            ),
                            extension_modules=tuple(
                                sorted(
                                    u.type_adapter(set[str]).validate_python(
                                        live.get_pycore().extension_modules,
                                        strict=True,
                                    )
                                )
                            ),
                            python_path_folders=tuple(
                                folder.real_path
                                for folder in live.get_python_path_folders()
                                if folder.is_folder()
                            ),
                        ),
                        sources={},
                    )
                ) as project,
                project.frozen_layout(),
            ):
                selected = {
                    path
                    for path in python
                    if path.is_relative_to(consumer)
                    and not any(
                        other != consumer
                        and other.is_relative_to(consumer)
                        and path.is_relative_to(other)
                        for other in roots
                    )
                }
                if params.rename_definitions:
                    for prefix, owners in params.bindings.items():
                        qualifier = prefix + "." if prefix else ""
                        for old, _new in pairs:
                            if not old.startswith(qualifier):
                                continue
                            for owner in owners:
                                binding = FlextInfraRenameSymbols.resolve_member(
                                    project,
                                    owner,
                                    old.removeprefix(qualifier),
                                )
                                module, _line = (
                                    binding.get_definition_location()
                                    if binding
                                    else (None, None)
                                )
                                resource = module.get_resource() if module else None
                                if resource is not None:
                                    selected.add(Path(resource.real_path))
                changes = FlextInfraRenameSymbols.plan(
                    project,
                    python,
                    pairs,
                    params.bindings,
                    rename_definitions=params.rename_definitions,
                    resource_paths=tuple(sorted(selected)),
                )
                for path, edits in changes.items():
                    merged = symbols.setdefault(path, [])
                    merged.extend(edit for edit in edits if edit not in merged)
                dependencies.extend(project.consumed_source_states())
                guards.append(project.verify_source_states)
                project.verify_source_states()
        source_states = m.Infra.CodemodBindingSnapshot(
            states=tuple(dependencies)
        ).states
        with u.Infra.open_project(root, project_roots=roots) as project:
            for path, source in sources.items():
                edits = list(symbols.get(path, ()))
                declared_text = any(
                    path.is_relative_to(Path(value).resolve()) for value in params.roots
                )
                if path in python:
                    if params.python_documentation and declared_text:
                        edits.extend(
                            FlextInfraRenameSources.documentation_edits(source, pairs),
                        )
                elif declared_text:
                    edits.extend(FlextInfraRenameSources.text_edits(source, pairs))
                occurrences += len(edits)
                desired = inventory[path].content
                if edits:
                    resource = project.get_resource(path.relative_to(root).as_posix())
                    changed = u.Infra.content_change(resource, source, edits)
                    if path in python:
                        ast.parse(changed.new_contents, filename=str(path))
                    desired = changed.new_contents.encode(c.DEFAULT_ENCODING)
                plans.append(
                    m.Infra.SemanticFilePlan(
                        project=max(
                            (owner for owner in roots if path.is_relative_to(owner)),
                            key=lambda owner: len(owner.parts),
                        ),
                        path=path,
                        before=inventory[path],
                        desired_content=desired if edits else None,
                        desired_mode=inventory[path].mode,
                        changes=("CSV campaign",) if edits else (),
                        source_states=source_states,
                    ),
                )

        def guard() -> p.Result[bool]:
            for verify in guards:
                verify()
            return r[bool].ok(value=True)

        return tuple(plans), occurrences, guard

    @staticmethod
    def _campaign_error(
        params: m.Infra.ApplyRenamesInput,
        roots: t.SequenceOf[Path],
    ) -> str | None:
        """Return the campaign validation failure message, or ``None`` when valid."""
        for root in roots:
            if not root.is_dir():
                return f"rename root is not a directory: {root}"
        if (
            not params.bindings
            and not params.text_globs
            and not params.python_documentation
        ):
            return "rename campaign has no declared symbol or text surfaces"
        return None

    @classmethod
    def _publish(
        cls,
        params: m.Infra.ApplyRenamesInput,
        roots: t.SequenceOf[Path],
        state: t.Pair[Path, m.Cli.AtomicFileState],
        pairs: t.SequenceOf[t.Pair[str, str]],
        planned: t.Triple[
            t.SequenceOf[m.Infra.SemanticFilePlan],
            int,
            Callable[[], p.Result[bool]],
        ],
    ) -> p.Result[t.Pair[t.SequenceOf[Path], int]]:
        """Publish the campaign atomically and re-plan until the post-scan is clean.

        Returns:
            The resulting ``p.Result[t.Pair[t.SequenceOf[Path], int]]`` holding the
            changed paths and the residual pending-edit count.

        """
        csv_path, driver = state
        plans, pending, source_guard = planned

        def verify(candidate_root: Path) -> p.Result[bool]:
            nonlocal pending
            current_driver = u.Cli.atomic_read_binary_file_state(
                csv_path,
                required=True,
            ).unwrap()
            if current_driver != driver:
                return r[bool].fail(
                    f"rename campaign driver changed during publish: {csv_path}",
                )
            publication_root = Path(commonpath(roots))
            candidate_roots = tuple(
                candidate_root / path.relative_to(publication_root) for path in roots
            )
            _fresh, remaining, _guard = cls._plan(params, candidate_roots, pairs)
            pending = remaining
            if remaining:
                return r[bool].fail(
                    f"CSV campaign candidate scan found {remaining} pending edits",
                )
            return r[bool].ok(value=True)

        driver_plan = m.Infra.SemanticFilePlan(
            project=Path(commonpath(roots)),
            path=csv_path,
            before=driver,
            desired_content=None,
            desired_mode=driver.mode,
            changes=(),
        )
        publication = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (*plans, driver_plan),
            repository_root=Path(commonpath(roots)),
            options=m.Infra.SemanticPublicationOptions(
                validator=verify,
                source_guard=lambda: (
                    source_guard()
                    if cls._consumer_roots(params) == roots
                    else r[bool].fail(
                        "declared rename consumer scope changed after planning"
                    )
                ),
                projection_roots=tuple(
                    path
                    for path in roots
                    if params.bindings and u.Infra.layout(path) is not None
                ),
                dependency_group=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            ),
        )
        if publication.failure:
            return r[t.Pair[t.SequenceOf[Path], int]].from_failure(publication)
        changed = publication.value
        return r[t.Pair[t.SequenceOf[Path], int]].ok((changed, pending))

    @classmethod
    def run(
        cls,
        params: m.Infra.ApplyRenamesInput,
    ) -> p.Result[m.Infra.ApplyRenamesReport]:
        """Apply one declared campaign; check and verification share the planner.

        Returns:
            The resulting ``p.Result[m.Infra.ApplyRenamesReport]``.

        """
        roots = cls._consumer_roots(params)
        error = cls._campaign_error(params, roots)
        if error is not None:
            return r[m.Infra.ApplyRenamesReport].fail(error)
        csv_path = Path(params.csv).resolve()
        driver = u.Cli.atomic_read_binary_file_state(csv_path, required=True).unwrap()
        if driver.content is None:
            return r[m.Infra.ApplyRenamesReport].fail(
                f"rename CSV disappeared: {csv_path}",
            )
        pairs = FlextInfraRenameSources.pairs(
            driver.content.decode(c.DEFAULT_ENCODING),
        )
        plans, pending, source_guard = cls._plan(params, roots, pairs)
        changed: t.SequenceOf[Path] = ()
        if params.apply:
            publication = cls._publish(
                params,
                roots,
                (csv_path, driver),
                pairs,
                (plans, pending, source_guard),
            )
            if publication.failure:
                return r[m.Infra.ApplyRenamesReport].from_failure(publication)
            changed, pending = publication.value
        report = m.Infra.ApplyRenamesReport(
            label=csv_path.stem,
            files_scanned=len(plans),
            occurrences=pending,
            files_changed=len(changed),
            applied=params.apply,
        )
        return r[m.Infra.ApplyRenamesReport].ok(report)


__all__: list[str] = ["FlextInfraApplyRenames"]
