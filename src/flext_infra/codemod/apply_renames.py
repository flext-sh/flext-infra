"""Transactional CSV campaigns using existing Rope and publication primitives.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from contextlib import closing
from difflib import unified_diff
from os.path import commonpath
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codemod import FlextInfraRenameSources, FlextInfraRenameSymbols
from flext_infra.transformers import FlextInfraSemanticPublication


class FlextInfraApplyRenames:
    """Plan against authenticated bytes and commit only after a real post-scan."""

    @staticmethod
    def _identifier_campaign(
        params: m.Infra.ApplyRenamesInput,
        pairs: t.SequenceOf[t.Pair[str, str]],
    ) -> bool:
        """Whether this campaign changes only semantic identifier declarations.

        Returns:
            True when definitions are renamed, no documentation or text-glob edits
            are requested, and every old name is a valid Python identifier.

        """
        return (
            params.rename_definitions
            and not params.python_documentation
            and not params.text_globs
            and all(old.isidentifier() for old, _new in pairs)
        )

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

    @staticmethod
    def _decoded_sources(
        inventory: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> t.MappingKV[Path, str]:
        """Decode the authenticated campaign inventory.

        Returns:
            The decoded sources of every inventoried file with content.

        """
        return {
            path: state.content.decode(c.DEFAULT_ENCODING)
            for path, state in inventory.items()
            if state.content is not None
        }

    @classmethod
    def _consumer_project(
        cls,
        live: p.Infra.RopeProject,
        inventory: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Infra.RopeProject:
        """Freeze one authenticated snapshot project for a consumer root.

        Returns:
            The closed-over snapshot project elected from the live analysis pass.

        Raises:
            TypeError: If the snapshot project does not satisfy its contract.

        """
        owner = u.Infra.runtime_type(
            "flext_infra._utilities._rope.project",
            "FlextInfraRopeProject",
        )
        factory = getattr(owner, "from_atomic_reads", None)
        if not callable(factory):
            msg = "Rope project owner does not expose authenticated construction"
            raise TypeError(msg)
        reader = u.Infra.runtime_callable("builtins", "getattr")
        extension_modules = reader(live.get_pycore(), "extension_modules")
        project = factory(
            live,
            tuple(inventory.values()),
            election=m.Infra.RopeProjectElection(
                source_folders=tuple(
                    folder.path for folder in live.get_source_folders()
                ),
                ignored_resources=tuple(
                    sorted(config.Infra.codegen.source_scan_ignored)
                ),
                extension_modules=tuple(
                    sorted(
                        u.type_adapter(set[str]).validate_python(
                            extension_modules,
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
        if not isinstance(project, p.Infra.RopeProject):
            msg = "Rope snapshot does not satisfy its project contract"
            raise TypeError(msg)
        return project

    @staticmethod
    def _elected_python_paths(
        python: t.MappingKV[Path, str],
        consumer: Path,
        roots: t.SequenceOf[Path],
    ) -> set[Path]:
        """Elect the python files one consumer root owns most directly.

        Returns:
            The consumer's python paths not shadowed by a narrower root.

        """
        return {
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

    @classmethod
    def _definition_resource_paths(
        cls,
        params: m.Infra.ApplyRenamesInput,
        pairs: t.SequenceOf[t.Pair[str, str]],
        project: t.Infra.RopeProject,
    ) -> set[Path]:
        """Resolve each bound rename destination's declaring resource.

        Returns:
            The resources declaring the destinations the campaign rewires.

        """
        selected: set[Path] = set()
        if not params.rename_definitions:
            return selected
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
                        binding.get_definition_location() if binding else (None, None)
                    )
                    resource = module.get_resource() if module else None
                    if resource is not None:
                        selected.add(Path(resource.real_path))
        return selected

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
        """Plan one campaign pass against the authenticated inventory.

        Returns:
            The file plans, pending-edit count, and source guard closure.

        """
        inventory = FlextInfraRenameSources.inventory(roots, params)
        sources = cls._decoded_sources(inventory)
        python = {
            path: source
            for path, source in sources.items()
            if path.suffix == c.Infra.EXT_PYTHON
        }
        candidates = (
            FlextInfraRenameSources.symbol_paths(
                python, frozenset(old for old, _new in pairs)
            )
            if cls._identifier_campaign(params, pairs)
            else frozenset(python)
        )
        root = Path(commonpath(roots))
        plans: t.MutableSequenceOf[m.Infra.SemanticFilePlan] = []
        occurrences = 0
        symbols: t.MutableMappingKV[
            Path, t.MutableSequenceOf[p.Infra.SourceRewrite]
        ] = {}
        guards: list[Callable[[], None]] = []
        dependencies: list[m.Cli.AtomicFileState] = (
            [] if cls._identifier_campaign(params, pairs) else list(inventory.values())
        )

        def campaign(consumer: Path) -> None:
            selected = cls._elected_python_paths(
                {path: python[path] for path in candidates}, consumer, roots
            )
            if not selected:
                return
            with (
                u.Infra.open_project(
                    root,
                    project_roots=roots,
                    consumer_root=consumer,
                ) as live,
                closing(cls._consumer_project(live, inventory)) as project,
                project.frozen_layout(),
            ):
                selected |= cls._definition_resource_paths(params, pairs, project)
                changes = FlextInfraRenameSymbols.plan(
                    project,
                    python,
                    (pairs, params.bindings),
                    rename_definitions=params.rename_definitions,
                    resource_paths=tuple(sorted(selected)),
                )
                for path, edits in changes.items():
                    merged = symbols.setdefault(path, [])
                    merged.extend(edit for edit in edits if edit not in merged)
                dependencies.extend(project.consumed_source_states())
                guards.append(project.verify_source_states)
                project.verify_source_states()

        for consumer in roots if params.bindings else ():
            campaign(consumer)
        source_states = m.Infra.CodemodBindingSnapshot(
            states=tuple(dependencies)
        ).states
        scope = (params, pairs, root, roots)
        context = (frozenset(python), source_states, inventory)
        with u.Infra.open_project(root, project_roots=roots) as project:
            for path, source in sources.items():
                plan, edits = cls._file_plan(
                    scope,
                    context,
                    project,
                    symbols,
                    (path, source),
                )
                plans.append(plan)
                occurrences += edits

        def guard() -> p.Result[bool]:
            if cls._identifier_campaign(params, pairs):
                current = cls._decoded_sources(
                    FlextInfraRenameSources.inventory(roots, params)
                )
                current_python = {
                    path: source
                    for path, source in current.items()
                    if path.suffix == c.Infra.EXT_PYTHON
                }
                if (
                    FlextInfraRenameSources.symbol_paths(
                        current_python, frozenset(old for old, _new in pairs)
                    )
                    != candidates
                ):
                    return r[bool].fail(
                        "rename identifier election changed after planning"
                    )
            return cls._verify_sources(guards)

        return tuple(plans), occurrences, guard

    @classmethod
    def _file_plan(
        cls,
        scope: t.Quad[
            m.Infra.ApplyRenamesInput,
            t.SequenceOf[t.Pair[str, str]],
            Path,
            t.SequenceOf[Path],
        ],
        context: t.Triple[
            frozenset[Path],
            t.VariadicTuple[m.Cli.AtomicFileState],
            t.MappingKV[Path, m.Cli.AtomicFileState],
        ],
        project: p.Infra.RopeProject,
        symbols: t.MappingKV[Path, t.SequenceOf[p.Infra.SourceRewrite]],
        entry: t.Pair[Path, str],
    ) -> t.Pair[m.Infra.SemanticFilePlan, int]:
        """Plan one inventoried file's edits against its authenticated bytes.

        Returns:
            The file plan and its pending-edit count.

        """
        params, pairs, root, roots = scope
        python_paths, _source_states, inventory = context
        path, source = entry
        edits = list(symbols.get(path, ()))
        declared_text = any(
            path.is_relative_to(Path(value).resolve()) for value in params.roots
        )
        if path in python_paths:
            if params.python_documentation and declared_text:
                edits.extend(
                    FlextInfraRenameSources.documentation_edits(source, pairs),
                )
        elif declared_text:
            edits.extend(FlextInfraRenameSources.text_edits(source, pairs))
        desired = inventory[path].content
        if edits:
            resource = project.get_resource(path.relative_to(root).as_posix())
            changed = u.Infra.content_change(resource, source, edits)
            if path in python_paths:
                ast.parse(changed.new_contents, filename=str(path))
            desired = changed.new_contents.encode(c.DEFAULT_ENCODING)
        plan = m.Infra.SemanticFilePlan(
            project=max(
                (owner for owner in roots if path.is_relative_to(owner)),
                key=lambda owner: len(owner.parts),
            ),
            path=path,
            before=inventory[path],
            desired_content=desired if edits else None,
            desired_mode=inventory[path].mode,
            changes=("CSV campaign",) if edits else (),
        )
        return plan, len(edits)

    @staticmethod
    def _verify_sources(
        guards: t.SequenceOf[Callable[[], None]],
    ) -> p.Result[bool]:
        """Re-run every captured source guard once more.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for verify in guards:
            verify()
        return r[bool].ok(value=True)

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
            (
                *(
                    plan
                    for plan in plans
                    if plan.desired_content is not None
                    or not cls._identifier_campaign(params, pairs)
                ),
                driver_plan,
            ),
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
            preview_diff="".join(
                "".join(
                    unified_diff(
                        plan.before.content.decode(c.DEFAULT_ENCODING).splitlines(
                            keepends=True
                        ),
                        plan.desired_content.decode(c.DEFAULT_ENCODING).splitlines(
                            keepends=True
                        ),
                        fromfile=str(plan.path),
                        tofile=str(plan.path),
                    )
                )
                for plan in plans
                if not params.apply
                and plan.before.content is not None
                and plan.desired_content is not None
                and plan.before.content != plan.desired_content
            ),
            label=csv_path.stem,
            files_scanned=len(plans),
            occurrences=pending,
            files_changed=len(changed),
            applied=params.apply,
        )
        return r[m.Infra.ApplyRenamesReport].ok(report)


__all__: list[str] = ["FlextInfraApplyRenames"]
