"""CSV rename campaigns over the shared Rope and publication owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from contextlib import closing
from difflib import unified_diff
from os.path import commonpath
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod import FlextInfraRenameSources, FlextInfraRenameSymbols
from flext_infra.transformers import FlextInfraSemanticPublication


class FlextInfraApplyRenames:
    """Plan a campaign once and accept it only after a clean post-scan."""

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
    ) -> t.Pair[t.VariadicTuple[m.Infra.SemanticFilePlan], int]:
        """Plan one campaign pass against the current inventory.

        Returns:
            The file plans and the pending-edit count.

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
        for consumer in roots if params.bindings else ():
            selected = cls._elected_python_paths(
                {path: python[path] for path in candidates}, consumer, roots
            )
            if not selected:
                continue
            with (
                u.Infra.open_project(
                    root, project_roots=roots, consumer_root=consumer
                ) as live,
                closing(
                    u.Infra.planned_project(
                        live, election=u.Infra.native_election(live)
                    )
                ) as project,
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
        scope = (params, pairs, root, roots)
        context = (frozenset(python), inventory)
        with u.Infra.open_project(root, project_roots=roots) as project:
            for path, source in sources.items():
                plan, edits = cls._file_plan(
                    scope, context, project, symbols, (path, source)
                )
                plans.append(plan)
                occurrences += edits
        return tuple(plans), occurrences

    @classmethod
    def _file_plan(
        cls,
        scope: t.Quad[
            m.Infra.ApplyRenamesInput,
            t.SequenceOf[t.Pair[str, str]],
            Path,
            t.SequenceOf[Path],
        ],
        context: t.Pair[frozenset[Path], t.MappingKV[Path, m.Cli.AtomicFileState]],
        project: p.Infra.RopeProject,
        symbols: t.MappingKV[Path, t.SequenceOf[p.Infra.SourceRewrite]],
        entry: t.Pair[Path, str],
    ) -> t.Pair[m.Infra.SemanticFilePlan, int]:
        """Plan one inventoried file's edits against its authenticated bytes.

        Returns:
            The file plan and its pending-edit count.

        """
        params, pairs, root, roots = scope
        python_paths, inventory = context
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
        state: t.Pair[
            t.Pair[Path, m.Cli.AtomicFileState], t.SequenceOf[t.Pair[str, str]]
        ],
        planned: t.Pair[t.SequenceOf[m.Infra.SemanticFilePlan], int],
    ) -> p.Result[t.Pair[t.SequenceOf[Path], int]]:
        """Accept the previewed campaign by a clean re-scan, then publish it.

        Returns:
            The changed paths and the residual pending-edit count.

        """
        (csv_path, driver), pairs = state
        plans, pending = planned
        publication_root = Path(commonpath(roots))

        def verify(candidate_root: Path) -> p.Result[bool]:
            nonlocal pending
            current = u.Cli.atomic_read_binary_file_state(csv_path, required=True)
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != driver:
                return r[bool].fail(
                    f"rename campaign driver changed during publish: {csv_path}",
                )
            _fresh, pending = cls._plan(
                params,
                tuple(
                    candidate_root / path.relative_to(publication_root)
                    for path in roots
                ),
                pairs,
            )
            if pending:
                return r[bool].fail(
                    f"CSV campaign candidate scan found {pending} pending edits",
                )
            return r[bool].ok(value=True)

        publication = FlextInfraSemanticPublication.publish_semantic_file_plans(
            plans,
            repository_root=publication_root,
            options=m.Infra.SemanticPublicationOptions(
                validator=verify,
                projection_roots=tuple(
                    path
                    for path in roots
                    if params.bindings and u.Infra.layout(path) is not None
                ),
            ),
        )
        if publication.failure:
            return r[t.Pair[t.SequenceOf[Path], int]].from_failure(publication)
        return r[t.Pair[t.SequenceOf[Path], int]].ok((publication.value, pending))

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
        plans, pending = cls._plan(params, roots, pairs)
        changed: t.SequenceOf[Path] = ()
        if params.apply:
            publication = cls._publish(
                params, roots, ((csv_path, driver), pairs), (plans, pending)
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
