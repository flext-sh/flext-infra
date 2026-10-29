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
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from functools import cache
from importlib.metadata import packages_distributions
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
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
    def codemod_runtime_modules(cls, root: Path) -> frozenset[str]:
        """Top-level import names provided by the project's runtime closure.

        Returns:
            The import packages whose distributions the closure contains.

        """
        project = FlextInfraUtilitiesCodemodRules.codemod_project_requirements(
            root,
        ).unwrap()
        if not project[1]:
            return frozenset()
        return cls._runtime_modules_of(tuple(project[1]))

    @staticmethod
    @cache
    def _runtime_modules_of(requirements: tuple[str, ...]) -> frozenset[str]:
        """Resolve the import packages of one requirement set, once per process.

        Installed metadata is a fact of the one owning runtime environment for
        the life of the process, so every plan, gate and render of the
        invocation shares the one closure its direct requirements select.

        Returns:
            The import packages whose distributions the closure contains.

        """
        progress = FlextInfraUtilitiesImportLaw.codemod_progress
        progress(f"runtime distributions start requirements={len(requirements)}")
        distributions = (
            FlextInfraUtilitiesCodemodRules.codemod_environment_distributions()
        )
        progress(f"runtime distributions finish distributions={len(distributions)}")
        progress("runtime dependency closure start")
        closure = FlextInfraUtilitiesCodemodRules.codemod_runtime_closure(
            requirements,
            distributions,
        )
        progress(f"runtime dependency closure finish distributions={len(closure)}")
        progress("runtime import package metadata start")
        owner = FlextInfraUtilitiesCodemodNative
        packages = owner.codemod_installed_import_packages()
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

    @staticmethod
    @cache
    def codemod_installed_import_packages() -> Mapping[str, frozenset[str]]:
        """Map each installed import package to its canonical distributions.

        Installed metadata is a fact of the interpreter environment, fixed for
        the life of the process, so it is read once; a project's runtime
        closure over it is still computed per call.

        Returns:
            Import package to the canonical names of its distributions.

        """
        return MappingProxyType({
            module: frozenset(canonicalize_name(name) for name in providers)
            for module, providers in packages_distributions().items()
        })

    @classmethod
    def codemod_native_generated(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        spec: m.Infra.CodegenAstGrepSpec,
    ) -> m.Infra.CodemodNativeGenerated:
        """Render every generated utility, then every rule document, in memory.

        Renderers run after the producers because rendered rules reference the
        generated utilities through ``matches``. Only ``make mod`` consumes
        them: its native cascade stages them; nothing is projected to disk.

        The rendering is a pure function of the member's sources, its manifest
        and the declared spec, so the injected snapshot keeps one rendering
        per member and render-input digest.

        Returns:
            The project's generated utility and rule documents keyed by id.

        """
        root = project.resolve()
        key = (root, cls._generated_key(snapshot, root, spec))
        rendered = snapshot.codemod_renderings.get(key)
        if rendered is None:
            scopes = cls.codemod_native_scopes(snapshot, root, spec.scopes)
            rendered = m.Infra.CodemodNativeGenerated(
                utilities=cls.codemod_native_utilities(snapshot, root, spec.producers),
                rules=cls.codemod_native_rules(
                    snapshot,
                    root,
                    spec,
                    facts={
                        c.Infra.CODEMOD_SCOPE_FACTS: m.Infra.CodemodScopeFacts(
                            scopes=scopes
                        )
                    },
                ),
                scopes=scopes,
            )
            snapshot.codemod_renderings[key] = rendered
        return rendered

    @staticmethod
    def _generated_key(
        snapshot: p.Infra.WorkspaceSnapshot,
        root: Path,
        spec: m.Infra.CodegenAstGrepSpec,
    ) -> str:
        """Digest every input a generated rendering reads, from the snapshot.

        Returns:
            The digest of the spec, the manifest and every member source.

        """
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        digest = hashlib.sha256(spec.model_dump_json().encode(c.DEFAULT_ENCODING))
        manifest = root / c.PYPROJECT_FILENAME
        for path in (
            *((manifest,) if manifest.is_file() else ()),
            *snapshots.workspace_python_files(snapshot, root),
        ):
            digest.update(str(path).encode(c.DEFAULT_ENCODING))
            digest.update(b"\0")
            digest.update(
                snapshots.workspace_source(snapshot, path).digest.encode(
                    c.DEFAULT_ENCODING
                )
            )
            digest.update(b"\0")
        return digest.hexdigest()

    @classmethod
    def codemod_scope_facts(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> m.Infra.CodemodScopeFacts:
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
        adapter = u.type_adapter(t.TypeForm(Mapping[str, t.StrTuple]))
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
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Build the sole executable rule plan for check and mutation.

        The caller injects its single repository snapshot. The public workspace
        composition invokes each repository separately, so generated identities
        and scopes never merge with a sibling's project plan.

        Returns:
            The resulting ``p.Result[m.Infra.CodemodRulePlan]``.

        """
        spec = config.Infra.codegen.ast_grep
        root = snapshot.workspace_root.resolve()
        if snapshot.members != (root,):
            return r[m.Infra.CodemodRulePlan].fail(
                "codemod rule planning requires one repository-owned snapshot"
            )
        provider = cls.codemod_generated_provider(snapshot, root, spec)
        return FlextInfraUtilitiesCodemodRules.codemod_compose_rule_plan(
            root, {root: provider}, rule_ids=rule_ids
        )

    @staticmethod
    def codemod_facade_alias_base_rules(
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
    ) -> Mapping[str, t.JsonMapping]:
        """Render the rule dropping a bare runtime facade alias used as a base.

        Facade members are reached through the alias, never by inheriting it;
        a bare alias base outside the facade families and the package
        ``api.py`` composes the facade's own layout into an unrelated class.
        The aliases are the core package's runtime aliases and the family
        locations come from the declared facade families.

        Returns:
            The single native rule document keyed by its rule id.

        """
        del snapshot
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(project)
        aliases = sorted(u.runtime_alias_names(c.Infra.PKG_CORE_UNDERSCORE))
        families = FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        rule_id = (
            f"{c.Infra.CODEMOD_FACADE_ALIAS_BASE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        alternatives = "|".join(re.escape(alias) for alias in aliases)
        return {
            rule_id: {
                "id": rule_id,
                "language": "python",
                "severity": "error",
                "files": ["**/*.py"],
                "ignores": [
                    *(
                        glob
                        for family in families
                        for glob in (
                            f"**/{family.module}{c.Infra.EXT_PYTHON}",
                            f"**/_{family.module}/**",
                        )
                    ),
                    f"**/{c.Infra.API_PY}",
                ],
                "rule": {
                    "kind": "identifier",
                    "pattern": "$ALIAS",
                    "regex": f"^(?:{alternatives})$",
                    "inside": {
                        "kind": "argument_list",
                        "inside": {"kind": "class_definition"},
                    },
                },
                "fix": {"template": "", "expandEnd": {"regex": "^,$"}},
                "message": (
                    "Bare facade alias `$ALIAS` used as a class base: reach facade "
                    "members through the alias instead of inheriting it."
                ),
            }
        }

    @staticmethod
    def codemod_fixture_resources(
        plan: m.Infra.CodemodRulePlan,
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
        spec: m.Infra.CodegenAstGrepSpec,
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
        rendered = cls.codemod_native_generated(snapshot, project, spec)
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
        entry: m.Infra.CodegenAstGrepRendererSpec,
        facts: dict[str, p.Model],
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
        adapter = u.type_adapter(t.TypeForm(Mapping[str, t.JsonMapping]))
        if entry.facts is None:
            return adapter.validate_python(renderer(snapshot, project), strict=True)
        if entry.facts not in facts:
            producer = getattr(cls, entry.facts, None)
            if not callable(producer):
                msg = f"ast-grep facts producer is not declared: {entry.facts}"
                raise TypeError(msg)
            model = producer(snapshot, project)
            if not isinstance(model, p.Model):
                msg = f"ast-grep facts producer returned no model: {entry.facts}"
                raise TypeError(msg)
            facts[entry.facts] = model
        return adapter.validate_python(
            renderer(snapshot, project, facts[entry.facts]), strict=True
        )

    @classmethod
    def _renderer_shapes(
        cls, entry: m.Infra.CodegenAstGrepRendererSpec
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
            u.type_adapter(t.TypeForm(Sequence[str])).validate_python(
                producer(), strict=True
            )
        )

    @classmethod
    def codemod_native_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        spec: m.Infra.CodegenAstGrepSpec,
        *,
        facts: Mapping[str, p.Model] | None = None,
    ) -> Mapping[str, t.JsonMapping]:
        """Run every registered renderer and merge its rule documents by id.

        ``facts`` seeds facts models the generation already computed.

        Returns:
            Every generated native rule document keyed by its rule id.

        Raises:
            ValueError: If a rule id repeats, names an unregistered shape, or
                disagrees with its document id.

        """
        documents: dict[str, t.JsonMapping] = {}
        computed: dict[str, p.Model] = dict(facts or {})
        for entry in spec.renderers:
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
                documents[rule_id] = document
        return MappingProxyType(dict(sorted(documents.items())))

    @classmethod
    def codemod_native_utilities(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        producers: Sequence[str],
    ) -> Mapping[str, t.JsonMapping]:
        """Run every registered producer and merge its utilities by id.

        Returns:
            Every utility document keyed by its utility id.

        Raises:
            TypeError: If a producer is not a declared utility producer.
            ValueError: If two producers emit the same utility id.

        """
        documents: dict[str, t.JsonMapping] = {}
        adapter = u.type_adapter(t.TypeForm(Mapping[str, t.JsonMapping]))
        for name in producers:
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
        return MappingProxyType(dict(sorted(documents.items())))


__all__: list[str] = ["FlextInfraUtilitiesCodemodNative"]
