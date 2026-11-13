"""Project SSOT facts generated as native ast-grep utility rules.

ast-grep matches one file's syntax; a rule whose meaning depends on the
project it runs in (its own package, the standard library, the runtime
dependency closure) reads that fact as a native utility rule the rule
references through ``matches``. Each producer derives one family of those
utilities from an existing source of truth; ``make gen`` writes them into the
project's catalog overlay, so a native ``ast-grep scan`` and the engine see
the same rule semantics.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
import tempfile
import time
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from functools import cache
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name
from typing_extensions import TypeForm

from flext_infra import c, config, m, p, r, settings, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDependencyRequirements,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform


class FlextInfraUtilitiesCodemodNative:
    """Derive native ast-grep utility rules from project sources of truth."""

    @staticmethod
    @contextmanager
    def _producer_progress(name: str, project: Path) -> Generator[None]:
        """Measure one declared producer through the existing progress owner.

        Yields:
            Control while the producer runs; failures escape unchanged.

        """
        FlextInfraUtilitiesImportLaw.codemod_progress(
            f"producer start name={name} project={project.name}"
        )
        started = time.monotonic()
        completed = False
        try:
            yield
            completed = True
        finally:
            FlextInfraUtilitiesImportLaw.codemod_progress(
                f"producer stop name={name} completed={completed} "
                f"duration={time.monotonic() - started:.2f}s"
            )

    @staticmethod
    def codemod_native_utility_document(
        utility_id: str, rule: t.JsonMapping
    ) -> t.JsonMapping:
        """Wrap one native rule object as an ast-grep utility rule document.

        Returns:
            The utility document ast-grep loads from a ``utilDirs`` entry.

        """
        return {
            "id": utility_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "rule": dict(rule),
        }

    @staticmethod
    def codemod_module_names_rule(names: Sequence[str]) -> t.JsonMapping:
        """Match a captured dotted module whose top-level package is listed.

        The top-level package is the captured text up to its first dot or
        whitespace, the same reading the import law applies to a module.

        Returns:
            A native ``regex`` rule over the captured module text.

        """
        alternatives = "|".join(re.escape(name) for name in sorted(set(names)))
        return {"regex": rf"^(?:{alternatives})(?:[.\s]|$)"}

    @classmethod
    def codemod_own_package_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Own package: the public package, internal tiers, declared namespaces.

        An absolute import between the project's package and its internal
        tiers (tests, examples, scripts) never crosses a package boundary.

        Returns:
            The ``own-package`` utility rule of the project.

        """
        del snapshot
        return {
            c.Infra.CODEMOD_OWN_PACKAGE_UTILITY: (
                cls.codemod_module_names_rule(cls.codemod_own_package_names(project))
            ),
        }

    @staticmethod
    def codemod_own_package_names(project: Path) -> Sequence[str]:
        """Top-level packages the project owns: its package, tiers, namespaces.

        Returns:
            The import package names an absolute import of the project uses.

        """
        return (
            FlextInfraUtilitiesPyprojectConform.project_package_name(project),
            *c.Infra.NON_PUBLIC_LAZY_ROOTS,
            *FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(project),
        )

    @classmethod
    def codemod_stdlib_module_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Standard library: ``sys.stdlib_module_names`` plus declared backports.

        Returns:
            The ``stdlib-module`` utility rule.

        """
        del snapshot, project
        backports = config.Infra.tooling.lazy_init.stdlib_backports
        return {
            c.Infra.CODEMOD_STDLIB_MODULE_UTILITY: (
                cls.codemod_module_names_rule(
                    tuple(sorted({*sys.stdlib_module_names, *backports}))
                )
            ),
        }

    @staticmethod
    def codemod_generated_module_utilities(
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
    ) -> Mapping[str, t.JsonMapping]:
        """Generated module: a module whose first line is the generator header.

        The same header ``generated_source`` reads proves a file is a
        generator projection. Rules use this ownership fact for specific
        publication contracts, never as a blanket source-admission exclusion.

        Returns:
            The ``generated-module`` utility rule.

        """
        del snapshot, project
        return {
            c.Infra.CODEMOD_GENERATED_MODULE_UTILITY: {
                "kind": "module",
                "has": {
                    "kind": "comment",
                    "nthChild": 1,
                    "regex": rf"^{re.escape(c.Infra.AUTOGEN_HEADER)}$",
                },
            },
        }

    @classmethod
    def codemod_runtime_package_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Runtime package: an import package of the runtime dependency closure.

        Returns:
            The ``runtime-package`` utility rule of the project.

        """
        del snapshot
        modules = cls.codemod_runtime_modules(project)
        return {
            c.Infra.CODEMOD_RUNTIME_PACKAGE_UTILITY: (
                cls.codemod_module_names_rule(tuple(modules))
                if modules
                else {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
            ),
        }

    @classmethod
    def codemod_runtime_distributions(cls, root: Path) -> Mapping[str, t.StrTuple]:
        """Map import packages to the distributions of the project's own runtime.

        Installed metadata is a fact of the TARGET repository's runtime, the
        same observation its runtime closure reads; the invoking interpreter
        is never read. A project declaring no runtime requirement installs no
        distribution of its own, so nothing is observed.

        Returns:
            The import packages and the distributions providing each.

        """
        del cls
        if not (root / c.PYPROJECT_FILENAME).is_file():
            return MappingProxyType({})
        if not FlextInfraUtilitiesCodemodRules.project_requirements(root).unwrap()[1]:
            return MappingProxyType({})
        return (
            FlextInfraUtilitiesCodemodRules
            .codemod_target_environment(root.resolve())
            .unwrap()
            .package_distributions
        )

    @classmethod
    def codemod_runtime_modules(cls, root: Path) -> frozenset[str]:
        """Top-level import names provided by the project's runtime closure.

        Returns:
            The import packages whose distributions the closure contains.

        """
        if not (root / c.PYPROJECT_FILENAME).is_file():
            return frozenset()
        project = FlextInfraUtilitiesCodemodRules.project_requirements(
            root,
        ).unwrap()
        if not project[1]:
            return frozenset()
        return cls._runtime_modules_of(root.resolve(), tuple(project[1]))

    @staticmethod
    @cache
    def _runtime_modules_of(
        root: Path, requirements: tuple[str, ...]
    ) -> frozenset[str]:
        """Resolve the import packages of one requirement set, once per root.

        Installed metadata is a fact of the TARGET repository's own runtime
        environment, observed through its own interpreter; the invoking
        interpreter is never read. Every plan, gate and render of one
        repository shares the one closure its direct requirements select.

        Returns:
            The import packages whose distributions the closure contains.

        """
        progress = FlextInfraUtilitiesImportLaw.codemod_progress
        owner = FlextInfraUtilitiesCodemodRules
        progress(f"runtime distributions start requirements={len(requirements)}")
        environment = owner.codemod_target_environment(root).unwrap()
        distributions = owner.codemod_target_distributions(root).unwrap()
        progress(f"runtime distributions finish distributions={len(distributions)}")
        progress("runtime dependency closure start")
        closure = owner.codemod_runtime_closure(requirements, distributions)
        progress(f"runtime dependency closure finish distributions={len(closure)}")
        packages = {
            module: frozenset(canonicalize_name(name) for name in providers)
            for module, providers in environment.package_distributions.items()
        }
        progress(f"runtime import package metadata finish packages={len(packages)}")
        selected: set[str] = set()
        due = 0.0
        for index, (module, providers) in enumerate(packages.items(), start=1):
            due = progress(
                f"runtime imports package={index}/{len(packages)} "
                f"module={module} selected={len(selected)}",
                due,
            )
            if providers & closure:
                selected.add(module)
        progress(f"runtime imports finish modules={len(selected)}")
        return frozenset(selected)

    @classmethod
    def codemod_native_generated(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        spec: p.Infra.CodegenAstGrepSpec,
        *,
        rule_ids: Sequence[str] | None = None,
    ) -> p.Infra.CodemodNativeGenerated:
        """Render the generated file scopes, rule documents and utilities in memory.

        Without a selection everything is rendered. An exact selection of rule
        ids (authored or generated) renders only what those rules read: the
        scope producers when a selected renderer or catalog rule consumes file
        scopes, the selected renderers' documents, and the utility producers
        when a selected document references a utility it does not declare.
        Only ``make mod`` consumes them: its native cascade stages them;
        nothing is projected to disk.

        The rendering is a pure function of the member's sources, its manifest
        and the declared spec, so the injected snapshot keeps one rendering
        per member and render-input digest.

        Returns:
            The project's generated utility and rule documents keyed by id.

        """
        root = project.resolve()
        key = (root, cls._generated_key(snapshot, root, spec, rule_ids))
        rendered = snapshot.codemod_renderings.get(key)
        if rendered is None:
            cache_path = cls._rendering_cache_path(key[1])
            if cache_path.is_file():
                try:
                    rendered = m.Infra.CodemodNativeGenerated.model_validate_json(
                        cache_path.read_text(encoding=c.DEFAULT_ENCODING)
                    )
                except ValueError:
                    rendered = None
            if rendered is not None:
                snapshot.codemod_renderings[key] = rendered
                return rendered
            catalog = (
                ()
                if rule_ids is None
                else cls._selected_catalog_documents(root, rule_ids)
            )
            scopes: Mapping[str, t.StrTuple] = (
                cls.codemod_native_scopes(snapshot, root, spec.scopes)
                if rule_ids is None
                or cls._selection_consumes_scopes(spec, rule_ids, catalog)
                else MappingProxyType({})
            )
            rules = cls.codemod_native_rules(
                snapshot,
                root,
                spec,
                rule_ids=rule_ids,
                facts={
                    c.Infra.CODEMOD_SCOPE_FACTS: m.Infra.CodemodScopeFacts(
                        scopes=scopes
                    )
                },
            )
            required = (
                None
                if rule_ids is None
                else cls._referenced_generated_utilities((*catalog, *rules.values()))
            )
            utilities: Mapping[str, t.JsonMapping] = (
                MappingProxyType({})
                if required is not None and not required
                else cls.native_utilities(
                    snapshot, root, spec.producers, required=required
                )
            )
            rendered = m.Infra.CodemodNativeGenerated(
                utilities=utilities, rules=rules, scopes=scopes
            )
            cls._store_rendering(cache_path, rendered)
            snapshot.codemod_renderings[key] = rendered
        return rendered

    @staticmethod
    def _rendering_cache_path(digest: str) -> Path:
        """Return the persistent rendering cache path of one input digest.

        Returns:
            The cache file holding the rendered generated provider.

        """
        return settings.work_dir / "codemod-renderings" / f"{digest}.json"

    @staticmethod
    def _store_rendering(path: Path, rendered: m.Infra.CodemodNativeGenerated) -> None:
        """Publish one rendering to its cache without exposing a partial file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(rendered.model_dump_json(), encoding=c.DEFAULT_ENCODING)
        temporary.replace(path)

    @staticmethod
    def _selected_catalog_documents(
        root: Path, rule_ids: Sequence[str]
    ) -> tuple[t.JsonMapping, ...]:
        """Read the authored catalog documents of an exact rule selection.

        Generated identities are not catalog rules and yield nothing here;
        their renderers produce them.

        Returns:
            The authored document of every selected catalog rule.

        """
        selected = frozenset(rule_ids)
        owner = FlextInfraUtilitiesCodemodRules
        plan = owner.codemod_compose_rule_plan(root, {root: None}).unwrap()
        documents: dict[Path, Sequence[t.JsonMapping]] = {}
        for ruleset in plan.rulesets:
            owner.codemod_catalog_rules(
                ruleset.provider, ruleset.config, documents=documents
            ).unwrap()
        return tuple(
            document
            for rule in plan.rules
            if rule.id in selected
            for document in documents[rule.resource.resolve()]
            if document.get("id") == rule.id
        )

    @classmethod
    def _selection_consumes_scopes(
        cls,
        spec: p.Infra.CodegenAstGrepSpec,
        rule_ids: Sequence[str],
        catalog: Sequence[t.JsonMapping],
    ) -> bool:
        """Whether an exact rule selection reads the project's file scopes.

        The file-scope producers are rope-backed and dominate a rendering, so
        they run only for a consumer the selection names: a selected renderer
        whose declared facts are the scope facts, or a selected catalog rule
        that declares ``metadata.scope``. A selection of any other rule ids
        reads no scope.

        Returns:
            Whether a selected rule consumes file scopes.

        """
        selected = frozenset(rule_ids)
        if any(
            entry.facts == c.Infra.CODEMOD_SCOPE_FACTS
            and cls._renderer_selects_rule_ids(entry, selected)
            for entry in spec.renderers
        ):
            return True
        return any(
            isinstance(metadata := document.get("metadata"), Mapping)
            and metadata.get(c.Infra.CODEMOD_SCOPE_METADATA_KEY) is not None
            for document in catalog
        )

    @classmethod
    def _referenced_generated_utilities(
        cls, documents: Sequence[t.JsonMapping]
    ) -> frozenset[str]:
        """Collect the utilities selected rule documents call outside their own.

        A native ``matches`` reference resolves to a utility the document
        declares itself (``utils``) or to one a provider publishes; the
        producers emit the latter, so only these identities need producing.

        Returns:
            Every non-local utility identity the documents reference.

        """
        return frozenset().union(
            *(
                cls._matched_utilities(document).difference(
                    local if isinstance(local := document.get("utils"), Mapping) else ()
                )
                for document in documents
            )
        )

    @classmethod
    def _matched_utilities(cls, value: t.JsonValue | t.JsonMapping) -> frozenset[str]:
        """Collect every utility identity a native rule references by ``matches``.

        Returns:
            The identities named by ``matches`` anywhere under the value.

        """
        if isinstance(value, Mapping):
            found: set[str] = set()
            for key, item in value.items():
                if key == "matches":
                    found.update(
                        (item,)
                        if isinstance(item, str)
                        else tuple(item)
                        if isinstance(item, Mapping)
                        else ()
                    )
                found.update(cls._matched_utilities(item))
            return frozenset(found)
        if isinstance(value, list):
            return frozenset().union(*(cls._matched_utilities(item) for item in value))
        return frozenset()

    @staticmethod
    def _generated_key(
        snapshot: p.Infra.WorkspaceSnapshot,
        root: Path,
        spec: p.Infra.CodegenAstGrepSpec,
        rule_ids: Sequence[str] | None,
    ) -> str:
        """Digest every input a generated rendering reads, from the snapshot.

        Returns:
            The digest of the spec, the manifest and every member source.

        """
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        digest = hashlib.sha256(spec.model_dump_json().encode(c.DEFAULT_ENCODING))
        digest.update(b"\0")
        digest.update(config.Infra.tooling.model_dump_json().encode(c.DEFAULT_ENCODING))
        digest.update(b"\0")
        digest.update((root / c.PYPROJECT_FILENAME).read_bytes())
        digest.update(b"\0")
        selected_ids: t.JsonValue = (
            None if rule_ids is None else list[t.JsonValue](sorted(rule_ids))
        )
        digest.update(
            u.Cli
            .json_dumps(selected_ids, sort_keys=True)
            .unwrap()
            .encode(c.DEFAULT_ENCODING)
        )
        workspace = (
            root.parent if (root.parent / c.Infra.GITMODULES).is_file() else root
        )
        requirements = FlextInfraUtilitiesCodemodRules.project_requirements(
            root
        ).unwrap()[1]
        identities = (
            FlextInfraUtilitiesDependencyRequirements.requirement_identity(requirement)
            for requirement in requirements
        )
        members = (
            root,
            *(
                workspace / identity
                for identity in identities
                if identity.startswith("flext-") and (workspace / identity).is_dir()
            ),
        )
        # A rendering holds root-relative paths and names generated rules after
        # the member directory, never its location: the key names each source
        # from the member's parent, so identical content under the same member
        # name shares one rendering across checkouts, and every byte still
        # authenticates it.
        for member_root in members:
            for path in snapshots.workspace_python_files(snapshot, member_root):
                digest.update(
                    path.relative_to(root.parent).as_posix().encode(c.DEFAULT_ENCODING)
                )
                digest.update(b"\0")
                digest.update(path.read_bytes())
                digest.update(b"\0")
        for module in (
            Path(__file__),
            Path(__file__).with_name("project_facts.py"),
            Path(__file__).with_name("rules.py"),
        ):
            digest.update(module.read_bytes())
        return digest.hexdigest()

    @classmethod
    def codemod_scope_facts(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> p.Infra.CodemodScopeFacts:
        """Compute the project's file scopes as the facts of scoped renderers.

        A generation computes them once and seeds every renderer with them.

        Returns:
            The project's file scopes keyed by selector.

        """
        return m.Infra.CodemodScopeFacts(
            scopes=cls.codemod_native_scopes(
                snapshot, project.resolve(), config.Infra.codegen.ast_grep.scopes
            )
        )

    @classmethod
    def codemod_native_scopes(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        producers: Sequence[str],
    ) -> Mapping[str, t.StrTuple]:
        """Run every registered file-scope producer and merge its selectors.

        Returns:
            Project-relative file sets keyed by scope selector.

        Raises:
            TypeError: If a producer is not a declared file-scope producer.
            ValueError: If two producers emit the same selector.

        """
        scopes: dict[str, t.StrTuple] = {}
        adapter = u.type_adapter(TypeForm(Mapping[str, t.StrTuple]))
        for name in producers:
            producer = getattr(cls, name, None)
            if not callable(producer):
                msg = f"ast-grep file-scope producer is not declared: {name}"
                raise TypeError(msg)
            with cls._producer_progress(name, project):
                emitted = adapter.validate_python(
                    producer(snapshot, project), strict=True
                )
            for selector, files in emitted.items():
                if selector in scopes:
                    msg = f"ast-grep file scope produced twice: {selector}"
                    raise ValueError(msg)
                scopes[selector] = files
        return MappingProxyType(dict(sorted(scopes.items())))

    @staticmethod
    @contextmanager
    def codemod_workspace_snapshot(
        root: Path,
    ) -> Generator[p.Infra.WorkspaceSnapshot]:
        """Open one repository-scoped snapshot for this invocation.

        The workspace organizer owns the repository loop. Each invocation
        therefore captures only its selected repository and injects that
        snapshot into every plan, render and scan of the source epoch.

        Yields:
            The snapshot of this repository only.

        """
        resolved = root.resolve()
        with FlextInfraUtilitiesWorkspaceSnapshot.workspace_snapshot(
            resolved,
            (resolved,),
        ) as snapshot:
            yield snapshot

    @classmethod
    def codemod_rule_plan(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        *,
        rule_ids: Sequence[str] | None = None,
    ) -> p.Result[p.Infra.CodemodRulePlan]:
        """Build the sole executable rule plan for check and mutation.

        The caller injects its single repository snapshot. The public workspace
        composition invokes each repository separately, so generated identities
        and scopes never merge with a sibling's project plan. A repository is
        identified by its ``pyproject.toml`` ``[project]`` table; a root without
        one fails before any rendering reads it.

        Returns:
            The resulting ``p.Result[p.Infra.CodemodRulePlan]``.

        """
        spec = config.Infra.codegen.ast_grep
        root = snapshot.workspace_root.resolve()
        if snapshot.members != (root,):
            return r[p.Infra.CodemodRulePlan].fail(
                "codemod rule planning requires one repository-owned snapshot"
            )
        if rule_ids is not None:
            if not rule_ids or any(not rule_id.strip() for rule_id in rule_ids):
                return r[p.Infra.CodemodRulePlan].fail(
                    "codemod rule selection requires non-empty exact rule IDs",
                )
            if len(frozenset(rule_ids)) != len(rule_ids):
                return r[p.Infra.CodemodRulePlan].fail(
                    "duplicate codemod rule IDs in selection",
                )
        project = FlextInfraUtilitiesCodemodRules.project_requirements(root)
        if project.failure:
            return r[p.Infra.CodemodRulePlan].from_failure(project)
        provider = cls.codemod_generated_provider(
            snapshot, root, spec, rule_ids=rule_ids
        )
        return FlextInfraUtilitiesCodemodRules.codemod_compose_rule_plan(
            root, {root: provider}, rule_ids=rule_ids
        )

    @classmethod
    def codemod_law_rule_ids(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        laws: frozenset[str],
    ) -> p.Result[t.StrTuple]:
        """Expand a theme's laws into this repository's exact planned rule ids.

        The repository's authored catalogs elect their rules (owner and
        consumer scopes applied); an elected rule belongs to the theme when
        its ``enforce`` intersects ``laws``. Generated rules belong to it by
        the laws their documents claim, rendered only by the renderers whose
        declared laws, or the catalog laws of the authored rules they render
        (partitions), intersect ``laws``. The ids feed the existing exact
        selection, so the theme's plan is the plan those ids compose.

        Returns:
            The theme's rule ids in plan order, empty when the repository
            plans no rule of the theme, or the first composition failure.

        """
        outcome = r[t.StrTuple]
        root = snapshot.workspace_root.resolve()
        owner = FlextInfraUtilitiesCodemodRules
        composed = owner.codemod_compose_rule_plan(root, {root: None})
        if composed.failure:
            return outcome.from_failure(composed)
        catalog: dict[str, frozenset[str]] = {}
        for ruleset in composed.value.rulesets:
            parsed = owner.codemod_catalog_rules(ruleset.provider, ruleset.config)
            if parsed.failure:
                return outcome.from_failure(parsed)
            catalog.update({rule.id: frozenset(rule.enforce) for rule in parsed.value})
        generated = cls._rendered_rules(
            snapshot,
            root,
            tuple(
                entry
                for entry in config.Infra.codegen.ast_grep.renderers
                if laws.intersection(
                    frozenset(entry.enforce).union(
                        *(
                            catalog.get(shape, ())
                            for shape in cls._renderer_shapes(entry)
                        )
                    )
                )
            ),
            None,
            lambda _rule_id, claimed: bool(laws.intersection(claimed)),
        )
        return outcome.ok((
            *(
                rule.id
                for rule in composed.value.rules
                if laws.intersection(rule.enforce)
            ),
            *generated,
        ))

    @staticmethod
    def codemod_fixture_resources(
        plan: p.Infra.CodemodRulePlan,
    ) -> tuple[Path, ...]:
        """Return the authored rule files whose catalogs own rule fixtures.

        A generated provider renders its rules from project sources of truth
        and carries no fixtures; renderer tests own its proof.

        Returns:
            Each authored rule resource once, in plan order.

        """
        return tuple(
            dict.fromkeys(
                rule.resource
                for rule in plan.rules
                if rule.provider != c.Infra.CODEMOD_GENERATED_PROVIDER
            )
        )

    @classmethod
    def codemod_generated_provider(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        spec: p.Infra.CodegenAstGrepSpec,
        *,
        rule_ids: Sequence[str] | None = None,
    ) -> tuple[str, Path] | None:
        """Materialize the project's rendered rules as one native provider root.

        The root is content-addressed under the project's native stage
        reports: identical renderings share one immutable directory, so a
        native ``ast-grep scan -c <root>/sgconfig.yml`` reproduces exactly the
        rules the plan elected, and concurrent plans never rewrite each other.
        Rule identities remain owned by their renderers. Repository isolation
        belongs to the plan/provider composition, never an extra ID namespace.

        Returns:
            The generated provider name and its sgconfig path, or ``None``
            when no producer, renderer or file scope yields anything: the
            stable utilities and file scopes alone still back the catalog
            rules that reference them.

        Raises:
            OSError: If ``not final.is_dir()``.

        """
        rendered = cls.codemod_native_generated(
            snapshot, project, spec, rule_ids=rule_ids
        )
        if not rendered.rules and not rendered.utilities and not rendered.scopes:
            return None
        files: dict[Path, t.JsonMapping] = {
            Path(c.Infra.CODEMOD_CONFIG_FILENAME): {
                c.Infra.CODEMOD_RULE_DIRS_KEY: [c.Infra.CODEMOD_RULE_DIRS_KEY],
                c.Infra.CODEMOD_UTIL_DIRS_KEY: [c.Infra.CODEMOD_UTIL_DIRS_KEY],
            },
            Path(c.Infra.CODEMOD_SCOPES_FILENAME): {
                selector: list(paths) for selector, paths in rendered.scopes.items()
            },
            **{
                Path(c.Infra.CODEMOD_UTIL_DIRS_KEY)
                / f"{identity}{c.Infra.CODEMOD_RULE_SUFFIX}": document
                for identity, document in rendered.utilities.items()
            },
            **{
                Path(c.Infra.CODEMOD_RULE_DIRS_KEY)
                / f"{identity}{c.Infra.CODEMOD_RULE_SUFFIX}": document
                for identity, document in rendered.rules.items()
            },
        }
        rules = FlextInfraUtilitiesCodemodRules
        texts = {
            path: rules.codemod_native_documents_text((document,))
            for path, document in files.items()
        }
        digest = u.Cli.sha256_content(
            u.Cli.json_dumps(
                [[str(path), content] for path, content in sorted(texts.items())],
                sort_keys=True,
            ).unwrap()
        )
        reports = (
            project.resolve()
            / c.Infra.MOD_NATIVE_STAGE_RELATIVE_PATH
            / c.Infra.CODEMOD_GENERATED_PROVIDER
        )
        final = reports / digest
        if not final.is_dir():
            u.Cli.ensure_dir(reports).unwrap()
            staging = Path(tempfile.mkdtemp(prefix=f".{digest}-", dir=reports))
            try:
                for declared in (
                    c.Infra.CODEMOD_RULE_DIRS_KEY,
                    c.Infra.CODEMOD_UTIL_DIRS_KEY,
                ):
                    u.Cli.ensure_dir(staging / declared).unwrap()
                for relative, content in texts.items():
                    u.Cli.ensure_dir((staging / relative).parent).unwrap()
                    u.Cli.atomic_write_text_file(staging / relative, content).unwrap()
            except BaseException:
                # Rollback removes only this invocation's own staging tree;
                # the original failure is re-raised unchanged.
                shutil.rmtree(staging)
                raise
            try:
                staging.rename(final)
            except OSError:
                # A concurrent plan published the identical content first.
                shutil.rmtree(staging)
                if not final.is_dir():
                    raise
        cls._verify_generated_provider(final, texts)
        return (
            c.Infra.CODEMOD_GENERATED_PROVIDER,
            final / c.Infra.CODEMOD_CONFIG_FILENAME,
        )

    @staticmethod
    def _verify_generated_provider(root: Path, texts: Mapping[Path, str]) -> None:
        """Authenticate an immutable provider's complete inventory and contents.

        Raises:
            ValueError: If materialized entries differ from their content identity.

        """
        expected = {
            **{
                Path(declared): ("directory", None)
                for declared in (
                    c.Infra.CODEMOD_RULE_DIRS_KEY,
                    c.Infra.CODEMOD_UTIL_DIRS_KEY,
                    *{
                        parent.as_posix()
                        for relative in texts
                        for parent in relative.parents
                        if parent != Path()
                    },
                )
            },
            **{
                relative: ("file", u.Cli.sha256_content(content))
                for relative, content in texts.items()
            },
        }
        manifest = u.Cli.atomic_inventory_physical_tree(root).unwrap()
        observed = {
            entry.path.relative_to(root): (entry.kind, entry.sha256)
            for entry in manifest.entries
        }
        if observed != expected:
            msg = (
                f"generated codemod provider differs from its content identity: {root}"
            )
            raise ValueError(msg)

    @classmethod
    def codemod_native_render(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        entry: p.Infra.CodegenAstGrepRendererSpec,
        facts: dict[str, p.BaseModel],
    ) -> Mapping[str, t.JsonMapping]:
        """Run one renderer, passing its facts model computed once per generation.

        Every renderer and facts producer receives the injected snapshot and
        the member root.

        Returns:
            The renderer's rule documents keyed by rule id, strictly validated.

        Raises:
            TypeError: If the renderer or its facts producer is not declared,
                or the facts producer returns no model.

        """
        renderer = getattr(cls, entry.name, None)
        if not callable(renderer):
            msg = f"ast-grep rule renderer is not declared: {entry.name}"
            raise TypeError(msg)
        adapter = u.type_adapter(TypeForm(Mapping[str, t.JsonMapping]))
        if entry.facts is None:
            return adapter.validate_python(renderer(snapshot, project), strict=True)
        if entry.facts not in facts:
            producer = getattr(cls, entry.facts, None)
            if not callable(producer):
                msg = f"ast-grep facts producer is not declared: {entry.facts}"
                raise TypeError(msg)
            model = producer(snapshot, project)
            if not isinstance(model, p.BaseModel):
                msg = f"ast-grep facts producer returned no model: {entry.facts}"
                raise TypeError(msg)
            facts[entry.facts] = model
        return adapter.validate_python(
            renderer(snapshot, project, facts[entry.facts]), strict=True
        )

    @classmethod
    def _renderer_shapes(
        cls, entry: p.Infra.CodegenAstGrepRendererSpec
    ) -> frozenset[str]:
        """Read a renderer's registered shapes, declared or derived.

        Returns:
            The shapes the renderer may emit.

        Raises:
            TypeError: If the declared shape producer is not a u.Infra callable.

        """
        if entry.shapes_from is None:
            return frozenset(entry.shapes)
        producer = getattr(cls, entry.shapes_from, None)
        if not callable(producer):
            msg = f"ast-grep shape producer is not declared: {entry.shapes_from}"
            raise TypeError(msg)
        return frozenset(
            u.type_adapter(TypeForm(Sequence[str])).validate_python(
                producer(), strict=True
            )
        )

    @classmethod
    def codemod_native_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        spec: p.Infra.CodegenAstGrepSpec,
        *,
        facts: Mapping[str, p.BaseModel] | None = None,
        rule_ids: Sequence[str] | None = None,
    ) -> Mapping[str, t.JsonMapping]:
        """Run every registered renderer and merge its rule documents by id.

        ``facts`` seeds facts models the generation already computed. Every
        document carries its renderer's declared laws (``_law_document``).

        Returns:
            Every generated native rule document keyed by its rule id.

        """
        selected = None if rule_ids is None else frozenset(rule_ids)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        header_prefix = f"{c.Infra.CODEMOD_IMPORT_HEADER_SHAPE}{separator}"
        return cls._rendered_rules(
            snapshot,
            project,
            tuple(
                entry
                for entry in spec.renderers
                if selected is None
                or cls._renderer_selects_rule_ids(entry, selected)
                or c.Infra.CODEMOD_IMPORT_HEADER_SHAPE in cls._renderer_shapes(entry)
            ),
            facts,
            lambda rule_id, _claimed: (
                selected is None
                or rule_id in selected
                or rule_id.startswith(header_prefix)
            ),
        )

    @classmethod
    def _rendered_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        entries: Sequence[p.Infra.CodegenAstGrepRendererSpec],
        facts: Mapping[str, p.BaseModel] | None,
        keep: Callable[[str, frozenset[str]], bool],
    ) -> Mapping[str, t.JsonMapping]:
        """Render the given renderers and keep the documents ``keep`` admits.

        ``keep`` receives each validated rule id and the laws its stamped
        document claims, so an exact id selection and a law selection share
        one rendering and validation path.

        Returns:
            The kept native rule documents keyed by their rule id.

        Raises:
            ValueError: If a rule id repeats, names an unregistered shape, or
                disagrees with its document id.

        """
        documents: dict[str, t.JsonMapping] = {}
        computed: dict[str, p.BaseModel] = dict(facts or {})
        for entry in entries:
            with cls._producer_progress(entry.name, project):
                rendered = cls.codemod_native_render(snapshot, project, entry, computed)
            shapes = cls._renderer_shapes(entry)
            for rule_id, document in rendered.items():
                shape = rule_id.partition(c.Infra.CODEMOD_GENERATED_ID_SEPARATOR)[0]
                if shape not in shapes:
                    msg = (
                        f"ast-grep renderer {entry.name} emitted an unregistered "
                        f"shape: {rule_id}"
                    )
                    raise ValueError(msg)
                if rule_id in documents:
                    msg = f"ast-grep rule id rendered twice: {rule_id}"
                    raise ValueError(msg)
                if document.get("id") != rule_id:
                    msg = f"ast-grep rule document id disagrees with {rule_id}"
                    raise ValueError(msg)
                claimed = cls._law_document(entry, document)
                if keep(rule_id, claimed[1]):
                    documents[rule_id] = claimed[0]
        return MappingProxyType(dict(sorted(documents.items())))

    @staticmethod
    def _law_document(
        entry: p.Infra.CodegenAstGrepRendererSpec, document: t.JsonMapping
    ) -> tuple[t.JsonMapping, frozenset[str]]:
        """Stamp the renderer's laws on a document that claims none of its own.

        A renderer declares every law its documents enforce; a document that
        claims a narrower set of them keeps its own. A renderer that declares
        none renders authored catalog rules, whose documents carry theirs.

        Returns:
            The document with its law claim, and the laws it claims.

        Raises:
            ValueError: If a document claims a law its renderer does not declare.

        """
        key = c.Infra.CODEMOD_RULE_ENFORCE_KEY
        metadata = document.get("metadata")
        declared: dict[str, t.JsonValue] = (
            dict(metadata) if isinstance(metadata, Mapping) else {}
        )
        claimed = declared.get(key)
        laws = (
            frozenset(law for law in claimed if isinstance(law, str))
            if isinstance(claimed, list)
            else frozenset[str]()
        )
        if entry.enforce and not laws.issubset(entry.enforce):
            msg = (
                f"ast-grep renderer {entry.name} document {document.get('id')} "
                f"claims undeclared laws: {', '.join(sorted(laws))}"
            )
            raise ValueError(msg)
        if claimed is not None or not entry.enforce:
            return document, laws
        stamped = list[t.JsonValue](entry.enforce)
        return (
            {**document, "metadata": {**declared, key: stamped}},
            frozenset(entry.enforce),
        )

    @classmethod
    def _renderer_selects_rule_ids(
        cls,
        entry: p.Infra.CodegenAstGrepRendererSpec,
        rule_ids: frozenset[str],
    ) -> bool:
        """Whether an exact generated identity belongs to one renderer.

        A generated identity qualifies its registered shape. A bare shape is a
        catalog partition alias, so it is left for exact-plan validation to
        reject rather than expanding into every rendered partition.

        Returns:
            Whether the renderer owns an exact selected generated identity.

        """
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        shapes = {
            rule_id.partition(separator)[0]
            for rule_id in rule_ids
            if separator in rule_id
        }
        return bool(shapes.intersection(cls._renderer_shapes(entry)))

    @classmethod
    def native_utilities(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        producers: Sequence[str],
        *,
        required: frozenset[str] | None = None,
    ) -> Mapping[str, t.JsonMapping]:
        """Run the registered producers in order and merge their utilities by id.

        ``required`` names the utilities a selection references: production
        stops once every required utility, and every utility those reference
        in turn, is emitted, so an exact selection never pays for producers it
        does not read. ``None`` runs every producer.

        Returns:
            The produced utility documents keyed by their utility id.

        Raises:
            TypeError: If a producer is not a declared utility producer.
            ValueError: If two producers emit the same utility id.

        """
        documents: dict[str, t.JsonMapping] = {}
        adapter = u.type_adapter(TypeForm(Mapping[str, t.JsonMapping]))
        pending = None if required is None else set(required)
        for name in producers:
            if pending is not None and pending.issubset(documents):
                break
            producer = getattr(cls, name, None)
            if not callable(producer):
                msg = f"ast-grep utility producer is not declared: {name}"
                raise TypeError(msg)
            with cls._producer_progress(name, project):
                emitted = adapter.validate_python(
                    producer(snapshot, project), strict=True
                )
            for utility_id, rule in emitted.items():
                if utility_id in documents:
                    msg = f"ast-grep utility id produced twice: {utility_id}"
                    raise ValueError(msg)
                documents[utility_id] = cls.codemod_native_utility_document(
                    utility_id, rule
                )
                if pending is not None and utility_id in pending:
                    pending.update(cls._matched_utilities(rule))
        return MappingProxyType(dict(sorted(documents.items())))


__all__: list[str] = ["FlextInfraUtilitiesCodemodNative"]
