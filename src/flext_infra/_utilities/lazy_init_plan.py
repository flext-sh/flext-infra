"""Lazy-init package planning over one repository run (``u.Infra``).

Each package publishes what its direct modules declare in ``__all__`` plus
its child packages; elected private domains retain their owning facade boundary
at every depth; root namespaces inherit their facade letters.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from keyword import iskeyword
from pathlib import Path
from typing import cast

from flext_cli import p, r, t, u
from packaging.utils import canonicalize_name

from flext_infra import c, config
from flext_infra._models._codegen import (
    FlextInfraModelsCodegenLazyInit,
    FlextInfraModelsCodegenTransaction,
)
from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot
from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenLazyInit
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesLazyInitLetters,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesPythonModel,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodRulesDistributions


class FlextInfraUtilitiesLazyInitPlan:
    """Decide every package initializer of one repository, children first."""

    @staticmethod
    def lazy_init_run(
        source_project: FlextInfraProtocolsWorkspaceSnapshot.RopeProject,
        index: FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex,
        *,
        root: Path,
        scoped: bool,
        snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot | None = None,
    ) -> FlextInfraModelsCodegenLazyInit.LazyInitRun:
        """Open one repository run over its source inventory.

        Returns:
            The run every planning step reads and caches through.

        """
        return FlextInfraModelsCodegenLazyInit.LazyInitRun.model_validate({
            "root": root,
            "scoped": scoped,
            "index": index,
            "model": FlextInfraUtilitiesPythonModel.python_model_run(
                source_project,
                {
                    entry.module_name: entry.file_path
                    for entry in index.modules_by_path.values()
                    if entry.module_name
                    and entry.file_path.suffix == c.Infra.EXT_PYTHON
                },
                module_facts=(
                    snapshot.python_module_facts
                    if snapshot is not None and source_project is snapshot.engine
                    else None
                ),
            ),
            "plans": {},
            "contexts": {},
            "parents": {},
            "declared": {},
            "declarations": {},
            "packages": {},
            "collisions": [],
            "deferred_imports": {},
        })

    @staticmethod
    def lazy_init_target_dirs(
        index: FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex,
        root: Path,
        *,
        module: str,
        scoped: bool,
    ) -> tuple[Path, ...]:
        """Return the package directories a selected module names in ``root``.

        Returns:
            Every matching package directory, sorted.

        """
        found = {
            entry.package_dir
            for entry in index.modules_by_path.values()
            if entry.module_name == module
            and (not scoped or entry.project_root == root)
        }
        mapped = index.package_dir_by_name.get(module)
        if mapped is not None and (
            not scoped or index.packages_by_dir[str(mapped)].project_root == root
        ):
            found.add(mapped)
        return tuple(sorted(found))

    @classmethod
    def lazy_init_plan_root(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun, target: Path | None
    ) -> p.Result[tuple[FlextInfraModelsCodegenLazyInit.LazyInitPlan, ...]]:
        """Plan the repository's packages bottom-up; a target narrows the tree.

        ``target`` is the selected package directory, ``None`` plans the tree.

        Returns:
            The selected package plans, or the first planning failure.

        """
        result_type = r[tuple[FlextInfraModelsCodegenLazyInit.LazyInitPlan, ...]]
        entries = tuple(
            run.index.packages_by_dir[str(package_dir)]
            for package_dir in run.index.package_dirs
            if package_dir.is_relative_to(run.root)
            and not frozenset(package_dir.relative_to(run.root).parts)
            & c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
        )
        if run.scoped:
            unowned = next(
                (entry.package_dir for entry in entries if entry.project_root is None),
                None,
            )
            if unowned is not None:
                return result_type.fail(
                    f"lazy-init package has no repository owner: {unowned}"
                )
            entries = tuple(
                entry for entry in entries if entry.project_root == run.root
            )
        # Deepest first; at one depth the tests namespace comes last, because
        # it publishes its sibling packages' planned exports.
        package_dirs = sorted(
            (entry.package_dir for entry in entries),
            key=lambda package_dir: (
                FlextInfraUtilitiesBase.path_depth(package_dir),
                package_dir.name != c.Infra.DIR_TESTS,
            ),
            reverse=True,
        )
        if target is not None and target not in package_dirs:
            return result_type.fail(
                f"lazy-init target belongs to retired support: {target}"
            )
        selected: list[Path] = []
        for package_dir in package_dirs:
            if target is not None and not package_dir.is_relative_to(target):
                continue
            candidate = r[
                FlextInfraModelsCodegenLazyInit.LazyInitPlan
            ].create_from_callable(
                lambda package_dir=package_dir: cls._lazy_init_build_plan(
                    run, package_dir
                )
            )
            if candidate.failure:
                return result_type.from_failure(candidate)
            plan = candidate.value
            run.plans[package_dir] = plan
            if target in {None, package_dir} or (
                target is not None and target.name == c.Infra.DIR_TESTS
            ):
                selected.append(package_dir)
        deferrals = r[
            Mapping[Path, FlextInfraModelsCodegenLazyInit.LazyInitPlan]
        ].create_from_callable(lambda: cls._lazy_init_deferrals(run))
        if deferrals.failure:
            return result_type.from_failure(deferrals)
        run.plans.update(deferrals.value)
        if run.collisions:
            return result_type.fail(
                "lazy-init public export ownership is ambiguous: "
                f"{len(run.collisions)} collision(s)",
            )
        return result_type.ok(tuple(run.plans[package_dir] for package_dir in selected))

    @classmethod
    def lazy_init_file_plans(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        plans: tuple[FlextInfraModelsCodegenLazyInit.LazyInitPlan, ...],
        *,
        first_party: Mapping[Path, frozenset[str]],
    ) -> p.Result[tuple[FlextInfraModelsCodegenTransaction.CodegenFilePlan, ...]]:
        """Bind every decided initializer and generated-source tree to its effect.

        ``first_party`` maps each owning project root to its first-party
        namespaces.

        Returns:
            The file plans sorted by destination path.

        """
        result_type = r[tuple[FlextInfraModelsCodegenTransaction.CodegenFilePlan, ...]]
        view = run.model.source_project
        by_path: dict[Path, FlextInfraModelsCodegenTransaction.CodegenFilePlan] = {}
        for plan in plans:
            entry = run.index.packages_by_dir.get(str(plan.context.pkg_dir))
            project = entry.project_root if entry is not None else None
            if project is None:
                return result_type.fail(
                    "lazy-init package has no physical project owner: "
                    f"{plan.context.pkg_dir}",
                )
            owner = FlextInfraUtilitiesLazyInitRender.lazy_init_project_root(
                run.model, plan.context.pkg_dir
            )
            for path, desired in cls._lazy_init_effects(run, plan, first_party[owner]):
                file_plan = FlextInfraModelsCodegenTransaction.CodegenFilePlan(
                    project=project,
                    path=path,
                    before=view.source_state(path, required=False),
                    desired_content=desired,
                    desired_mode=(
                        config.Infra.codegen.modes.file_default
                        if desired is not None
                        else None
                    ),
                )
                if by_path.setdefault(path, file_plan) != file_plan:
                    return result_type.fail(f"conflicting lazy-init plans for {path}")
        return result_type.ok(tuple(by_path[path] for path in sorted(by_path)))

    @classmethod
    def _lazy_init_effects(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        plan: FlextInfraModelsCodegenLazyInit.LazyInitPlan,
        first_party: frozenset[str],
    ) -> Sequence[tuple[Path, bytes | None]]:
        """Return the desired bytes of one package and its generated-source trees.

        Returns:
            ``(path, desired)`` pairs; ``None`` removes a generated file.

        """
        render = FlextInfraUtilitiesLazyInitRender.lazy_init_render
        view = run.model.source_project
        effects: list[tuple[Path, bytes | None]] = []
        if plan.action == c.Infra.LazyInitAction.WRITE:
            effects.append((
                plan.context.init_path,
                render(plan, model=run.model, first_party=first_party).encode(
                    c.DEFAULT_ENCODING
                ),
            ))
        elif plan.action == c.Infra.LazyInitAction.REMOVE:
            effects.append((plan.context.init_path, None))
        names = frozenset(config.Infra.codegen.generated_sources)
        for tree in sorted(
            child
            for child in view.source_children(plan.context.pkg_dir)
            if child.name in names and view.source_query(child, "isdir")
        ):
            # One initializer, one owner: a tree the package planner already
            # planned owns its own exports-bearing initializer; this fallback
            # only serves generated trees outside the indexed package set.
            if tree in run.plans:
                continue
            init_path = tree / c.Infra.INIT_PY
            text = FlextInfraUtilitiesLazyInitLetters.lazy_init_text(run, init_path)
            if (
                FlextInfraUtilitiesCodegenFilePlan.codegen_initializer_is_authored(
                    None if text is None else text.encode(c.DEFAULT_ENCODING),
                )
                and not FlextInfraUtilitiesPythonModel.python_model_module_at(
                    run.model,
                    init_path,
                    f"{plan.context.current_pkg}.{tree.name}",
                ).declaration_only
            ):
                continue
            generated = text is not None and text.startswith(c.Infra.AUTOGEN_HEADER)
            if any(
                module.suffix == c.Infra.EXT_PYTHON
                and module.name != c.Infra.INIT_PY
                and view.source_query(module, "isfile")
                for module in view.source_children(tree)
            ):
                tree_plan = FlextInfraModelsCodegenLazyInit.LazyInitPlan(
                    context=FlextInfraModelsCodegenLazyInit.LazyInitPackageContext(
                        pkg_dir=tree,
                        init_path=init_path,
                        current_pkg=f"{plan.context.current_pkg}.{tree.name}",
                        surface=plan.context.surface,
                        generated_init=generated,
                        importable=True,
                    ),
                    action=c.Infra.LazyInitAction.WRITE,
                    lazy_map={},
                    eager_dunders={},
                )
                effects.append((
                    init_path,
                    render(tree_plan, model=run.model, first_party=first_party).encode(
                        c.DEFAULT_ENCODING
                    ),
                ))
            elif generated:
                effects.append((init_path, None))
        return effects

    @classmethod
    def lazy_init_context(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun, pkg_dir: Path
    ) -> FlextInfraModelsCodegenLazyInit.LazyInitPackageContext:
        """Return the package context of one directory.

        Returns:
            The package's import name, surface and initializer facts.

        """
        context = run.contexts.get(pkg_dir)
        if context is None:
            entry = run.index.packages_by_dir.get(str(pkg_dir))
            name = entry.package_name if entry is not None else ""
            init = FlextInfraUtilitiesLazyInitLetters.lazy_init_text(
                run, pkg_dir / c.Infra.INIT_PY
            )
            context = FlextInfraModelsCodegenLazyInit.LazyInitPackageContext(
                pkg_dir=pkg_dir,
                init_path=pkg_dir / c.Infra.INIT_PY,
                current_pkg=name,
                surface=name.split(".", maxsplit=1)[0],
                generated_init=init is not None
                and init.startswith(c.Infra.AUTOGEN_HEADER),
                importable=bool(name)
                and all(
                    part.isidentifier() and not iskeyword(part)
                    for part in name.split(".")
                ),
            )
            run.contexts[pkg_dir] = context
        return context

    @classmethod
    def _lazy_init_build_plan(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun, pkg_dir: Path
    ) -> FlextInfraModelsCodegenLazyInit.LazyInitPlan:
        """Decide one package's initializer after its children are planned.

        Returns:
            The package plan.

        """
        python = FlextInfraUtilitiesPythonModel
        context = cls.lazy_init_context(run, pkg_dir)
        init = FlextInfraUtilitiesLazyInitLetters.lazy_init_text(run, context.init_path)
        if (
            FlextInfraUtilitiesCodegenFilePlan.codegen_initializer_is_authored(
                None if init is None else init.encode(c.DEFAULT_ENCODING),
            )
            and not python.python_model_module_at(
                run.model, context.init_path, context.current_pkg
            ).declaration_only
        ):
            exports = (
                python.python_model_exports(
                    python.python_model_module_at(
                        run.model, context.init_path, context.current_pkg
                    )
                )
                or ()
            )
            return FlextInfraModelsCodegenLazyInit.LazyInitPlan(
                context=context,
                action=c.Infra.LazyInitAction.RETAIN,
                ownership="authored",
                disposition="retained",
                exports=tuple(sorted(exports)),
                lazy_map={name: (context.current_pkg, name) for name in exports},
                eager_dunders={},
                child_packages_for_lazy=cls._lazy_init_child_packages(run, context),
            )
        residue = (
            c.Infra.LazyInitAction.REMOVE
            if context.generated_init
            else c.Infra.LazyInitAction.SKIP
        )
        if not context.importable or cls._lazy_init_shadows_stdlib(context):
            return cls._lazy_init_empty_plan(context, residue)
        lazy_map = cls._lazy_init_package_exports(run, context)
        children = cls._lazy_init_child_packages(run, context)
        FlextInfraUtilitiesLazyInitLetters.lazy_init_resolve_aliases(
            run, context, lazy_map
        )
        version = (
            f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
            c.Infra.DUNDER_VERSION,
        )
        eager: t.MutableLazyAliasMap = (
            {c.Infra.DUNDER_VERSION: lazy_map.pop(c.Infra.DUNDER_VERSION)}
            if lazy_map.get(c.Infra.DUNDER_VERSION) == version
            else {}
        )
        facade_root = cls.lazy_init_is_facade_root(context)
        if facade_root and context.current_pkg == c.Infra.DIR_TESTS:
            for name, target in c.Infra.TEST_RUNTIME_ALIAS_TARGETS.items():
                lazy_map.setdefault(name, target)
            for name, target in cls._lazy_init_test_namespace_publics(
                run, context
            ).items():
                lazy_map.setdefault(name, target)
        if not lazy_map and not eager:
            keeps = (
                context.surface == c.Infra.DIR_TESTS
                and context.current_pkg != c.Infra.DIR_TESTS
            ) or cls._lazy_init_owns_modules(run, pkg_dir)
            return cls._lazy_init_empty_plan(
                context,
                c.Infra.LazyInitAction.WRITE if keeps else residue,
                child_packages=children,
            )
        return FlextInfraModelsCodegenLazyInit.LazyInitPlan(
            context=context,
            action=c.Infra.LazyInitAction.WRITE,
            ownership="generator",
            disposition="planned",
            exports=tuple(sorted({*lazy_map, *eager})),
            lazy_map=lazy_map,
            eager_dunders=eager,
            child_packages_for_lazy=children,
        )

    @classmethod
    def _lazy_init_deferrals(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun
    ) -> Mapping[Path, FlextInfraModelsCodegenLazyInit.LazyInitPlan]:
        """Give each heavy-module class export the facade import reaches a stand-in.

        A class is reached when a facade composes it by MRO, or when a module
        that importing the facades loads binds it by a runtime import. Either
        reach would load its heavy module, so it gets a stand-in. Selection
        waits until every package is planned, because both reaches resolve
        through the packages that publish them. Every other class export of a
        heavy module stays a plain lazy export.

        Returns:
            Each plan that gained stand-ins, by package directory.

        """
        updated: dict[Path, FlextInfraModelsCodegenLazyInit.LazyInitPlan] = {}
        roots: dict[Path, frozenset[str]] = {}
        composed: frozenset[tuple[str, str]] | None = None
        python = FlextInfraUtilitiesPythonModel
        for package_dir, plan in tuple(run.plans.items()):
            heavy = roots.get(plan.context.pkg_dir)
            if heavy is None:
                heavy = cls._lazy_init_deferred_imports(run, plan.context.pkg_dir)
                roots[plan.context.pkg_dir] = heavy
            if not heavy:
                continue
            if composed is None:
                composed = cls._lazy_init_import_reached(
                    run, cls._lazy_init_facade_composed(run), heavy
                )
            deferred: dict[str, Sequence[str]] = {}
            for name, (module, attr) in sorted(plan.lazy_map.items()):
                facts = python.python_model_module(run.model, module)
                if (
                    facts is not None
                    and attr in facts.classes
                    and facts.runtime_imports & heavy
                    and (module, attr) in composed
                ):
                    deferred[name] = cls._lazy_init_class_members(
                        run, (plan.context, plan.lazy_map), (module, attr)
                    )
            if deferred:
                updated[package_dir] = plan.model_copy(
                    update={"deferred_members": deferred}
                )
        return updated

    @classmethod
    def _lazy_init_facade_roots(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun
    ) -> Mapping[tuple[str, str], FlextInfraModelsCodegenLazyInit.LazyInitPlan]:
        """Return the facade class of each root-namespace module with its package plan.

        Returns:
            The planned root package of each ``(module, class)`` facade pair.

        """
        python = FlextInfraUtilitiesPythonModel
        roots: dict[tuple[str, str], FlextInfraModelsCodegenLazyInit.LazyInitPlan] = {}
        for plan in run.plans.values():
            if not cls.lazy_init_is_facade_root(plan.context):
                continue
            entry = run.index.packages_by_dir.get(str(plan.context.pkg_dir))
            for module in entry.modules if entry is not None else ():
                if (
                    module.file_path.suffix != c.Infra.EXT_PYTHON
                    or module.file_path.parent != plan.context.pkg_dir
                    or module.file_path.name == c.Infra.INIT_PY
                ):
                    continue
                owner = python.python_model_facade_owner(
                    python.python_model_module_at(
                        run.model, module.file_path, module.module_name
                    )
                )
                if owner is not None:
                    roots[module.module_name, owner[1]] = plan
        return roots

    @classmethod
    def _lazy_init_import_reached(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        composed: frozenset[tuple[str, str]],
        heavy: frozenset[str],
    ) -> frozenset[tuple[str, str]]:
        """Return every in-package class importing the facades reaches.

        The modules of the composed classes load with the facades unless the
        class itself imports a declared distribution, and every class such a
        loaded module binds by a runtime import is reached too; a reached
        class of a light module loads that module in turn.

        Returns:
            The composed classes and every class their loaded modules import.

        """
        python = FlextInfraUtilitiesPythonModel
        plans = {plan.context.current_pkg: plan for plan in run.plans.values()}

        def light(module: str) -> bool:
            facts = python.python_model_module(run.model, module)
            return facts is not None and not (facts.runtime_imports & heavy)

        reached = set(composed)
        pending = sorted({module for module, _ in composed if light(module)})
        loaded = set(pending)
        while pending:
            module = pending.pop()
            facts = python.python_model_module(run.model, module)
            plan = plans.get(module.rpartition(".")[0])
            if facts is None or plan is None:
                continue
            for name in sorted(facts.runtime_names):
                target = cls._lazy_init_base_target(
                    run, (plan.context, plan.lazy_map), facts.imports.get(name)
                )
                if target is None:
                    continue
                target_facts = python.python_model_module(run.model, target[0])
                if target_facts is None or target[1] not in target_facts.classes:
                    continue
                reached.add(target)
                if target[0] not in loaded and light(target[0]):
                    loaded.add(target[0])
                    pending.append(target[0])
        return frozenset(reached)

    @classmethod
    def _lazy_init_facade_composed(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun
    ) -> frozenset[tuple[str, str]]:
        """Return every in-package class a facade root class composes by MRO.

        The facade roots are the classes the root namespaces publish as facades;
        their bases, and those of the namespace classes nested in them, resolve
        through the published routes. A base outside every planned package (a
        third-party class) ends the walk.

        Returns:
            The ``(module, class)`` pair of each facade root and in-package base.

        """
        python = FlextInfraUtilitiesPythonModel
        roots = cls._lazy_init_facade_roots(run)
        pending = [(*root, plan) for root, plan in roots.items()]
        composed: set[tuple[str, str]] = set()
        while pending:
            module, name, plan = pending.pop()
            if (module, name) in composed:
                continue
            facts = python.python_model_module(run.model, module)
            if facts is None or name not in facts.classes:
                continue
            composed.add((module, name))
            bases = (
                *facts.classes[name],
                *(
                    python.python_model_namespace_bases(run.model, module, name)
                    if (module, name) in roots
                    else ()
                ),
            )
            for base in bases:
                target = (
                    (module, base)
                    if base in facts.classes
                    else cls._lazy_init_base_target(
                        run, (plan.context, plan.lazy_map), facts.imports.get(base)
                    )
                )
                if target is not None:
                    pending.append((*target, plan))
        return frozenset(composed)

    @staticmethod
    def _lazy_init_deferred_imports(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun, pkg_dir: Path
    ) -> frozenset[str]:
        """Return the import packages of the owning project's deferred distributions.

        The owning project declares the distributions; its own environment
        reports the import packages each one installs, once per project.

        Returns:
            The import packages, empty when the project declares none.

        Raises:
            ValueError: If a declared distribution installs no import package.

        """
        project_root = FlextInfraUtilitiesLazyInitRender.lazy_init_project_root(
            run.model, pkg_dir
        )
        known = run.deferred_imports.get(project_root)
        if known is not None:
            return known
        artifacts = FlextInfraUtilitiesProjectManagedArtifacts
        declared = frozenset(
            artifacts
            .load_repository_declaration_inputs(
                project_root, source_project=run.model.source_project
            )
            .unwrap()
            .spec.deferred_distributions
        )
        roots: frozenset[str] = frozenset()
        if declared:
            distributions = FlextInfraUtilitiesCodemodRulesDistributions
            environment = distributions.codemod_target_environment(
                project_root
            ).unwrap()
            installed = {
                module: frozenset(map(canonicalize_name, providers)) & declared
                for module, providers in environment.package_distributions.items()
            }
            missing = declared.difference(*installed.values())
            if missing:
                msg = (
                    f"deferred distributions install no import package in "
                    f"{project_root}: {sorted(missing)}"
                )
                raise ValueError(msg)
            roots = frozenset(module for module, owners in installed.items() if owners)
        run.deferred_imports[project_root] = roots
        return roots

    @classmethod
    def _lazy_init_class_members(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        scope: tuple[
            FlextInfraModelsCodegenLazyInit.LazyInitPackageContext, t.LazyAliasMap
        ],
        owner: tuple[str, str],
    ) -> Sequence[str]:
        """Return every non-dunder name the class bodies of an in-package MRO bind.

        Returns:
            The member names in MRO declaration order.

        Raises:
            ValueError: If a base is not a class of the same package.

        """
        python = FlextInfraUtilitiesPythonModel
        surface = scope[0].surface
        members: dict[str, None] = {}
        pending: list[tuple[str, str]] = [owner]
        visited: set[tuple[str, str]] = set()
        while pending:
            module, name = pending.pop(0)
            if (module, name) in visited:
                continue
            visited.add((module, name))
            facts = python.python_model_module(run.model, module)
            if (
                facts is None
                or name not in facts.classes
                or module.split(".", maxsplit=1)[0] != surface
            ):
                msg = (
                    f"deferred export {owner[0]}.{owner[1]} has a base that is "
                    f"not a class of its package: {module}.{name}"
                )
                raise ValueError(msg)
            members.update(
                dict.fromkeys(
                    # A class-private name lives in the class namespace mangled.
                    f"_{name.lstrip('_')}{member}"
                    if member.startswith("__")
                    else member
                    for member in facts.class_members[name]
                    if not (member.startswith("__") and member.endswith("__"))
                )
            )
            for base in facts.classes[name]:
                target = (
                    (module, base)
                    if base in facts.classes
                    else cls._lazy_init_base_target(run, scope, facts.imports.get(base))
                )
                if target is None:
                    msg = (
                        f"deferred export {owner[0]}.{owner[1]} has an "
                        f"unresolvable base: {base}"
                    )
                    raise ValueError(msg)
                pending.append(target)
        return tuple(members)

    @staticmethod
    def _lazy_init_base_target(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        scope: tuple[
            FlextInfraModelsCodegenLazyInit.LazyInitPackageContext, t.LazyAliasMap
        ],
        dotted: str | None,
    ) -> tuple[str, str] | None:
        """Resolve one imported base through its published package route.

        A family sibling resolves through the lazy map planned for that
        package (this one, or a child decided before it); a module path
        resolves to the class that module defines.

        Returns:
            The declaring ``(module, class)``, or ``None`` when unresolvable.

        """
        if dotted is None:
            return None
        context, lazy_map = scope
        module, _, name = dotted.rpartition(".")
        if module == context.current_pkg:
            return lazy_map.get(name)
        facts = FlextInfraUtilitiesPythonModel.python_model_module(run.model, module)
        if facts is not None and name in facts.classes:
            return (module, name)
        published = next(
            (
                plan.lazy_map
                for plan in run.plans.values()
                if plan.context.current_pkg == module
            ),
            None,
        )
        return None if published is None else published.get(name)

    @staticmethod
    def _lazy_init_empty_plan(
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
        action: c.Infra.LazyInitAction,
        *,
        child_packages: Sequence[str] = (),
    ) -> FlextInfraModelsCodegenLazyInit.LazyInitPlan:
        """Return a plan without exports for one decided action.

        Returns:
            The plan; written and removed initializers are generator-owned.

        """
        owned = action in {c.Infra.LazyInitAction.WRITE, c.Infra.LazyInitAction.REMOVE}
        return FlextInfraModelsCodegenLazyInit.LazyInitPlan(
            context=context,
            action=action,
            ownership="generator" if owned else None,
            disposition="planned" if owned else None,
            lazy_map={},
            eager_dunders={},
            child_packages_for_lazy=child_packages,
        )

    @staticmethod
    def lazy_init_is_facade_root(
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> bool:
        """Return whether a package is a public ``src`` root or the tests root.

        Returns:
            Whether the package owns a root facade surface.

        """
        name = context.current_pkg
        return bool(
            context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and name
            and "." not in name
        ) or (name == c.Infra.DIR_TESTS and context.pkg_dir.name == c.Infra.DIR_TESTS)

    @staticmethod
    def _lazy_init_shadows_stdlib(
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> bool:
        """Return whether the importable name shadows a stdlib module for Ruff.

        Returns:
            Whether the name relative to its source root is a stdlib module.

        """
        parts = context.current_pkg.split(".")
        if parts[0] in c.Infra.NON_PUBLIC_LAZY_ROOTS:
            parts = parts[1:]
        return len(parts) == 1 and parts[0] in sys.stdlib_module_names

    @staticmethod
    def _lazy_init_owns_modules(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun, pkg_dir: Path
    ) -> bool:
        """Return whether a package tree owns any module besides initializers.

        Returns:
            Whether the package or a descendant has a non-initializer module.

        """
        entry = run.index.packages_by_dir.get(str(pkg_dir))
        if entry is None:
            return False
        return any(
            not module.is_package_init
            for candidate in (pkg_dir, *entry.descendant_child_dirs)
            if (tree := run.index.packages_by_dir.get(str(candidate))) is not None
            for module in tree.modules
        )

    @classmethod
    def _lazy_init_package_exports(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> t.MutableLazyAliasMap:
        """Collect what the package's direct modules declare in ``__all__``.

        Returns:
            The export map of the package's own modules.

        Raises:
            ValueError: If a declaring module is shadowed by a same-named package.

        """
        python = FlextInfraUtilitiesPythonModel
        lazy_map: t.MutableLazyAliasMap = {}
        entry = run.index.packages_by_dir.get(str(context.pkg_dir))
        modules = sorted(
            (module.file_path, module.module_name)
            for module in (entry.modules if entry is not None else ())
            if module.file_path.suffix == c.Infra.EXT_PYTHON
            and module.file_path.parent == context.pkg_dir
            and module.file_path.name != c.Infra.INIT_PY
        )
        if context.current_pkg == c.Infra.DIR_TESTS:
            # The test namespace publishes the public API of src/scripts/
            # examples and the test facades. Test modules are collection
            # units, never namespace exports.
            modules = [
                (path, module_name)
                for path, module_name in modules
                if not path.name.startswith(c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX)
            ]
        for path, module_name in modules:
            if not run.model.source_project.source_query(path, "isfile"):
                # A staged sibling plan already moved this module on disk
                # within the same pipeline run; the pre-move index entry is
                # stale. Skip it — the fixed-point rerun plans the moved
                # module under its destination name.
                continue
            names = (
                python.python_model_exports(
                    python.python_model_module_at(run.model, path, module_name)
                )
                or ()
            )
            shadow = run.index.packages_by_dir.get(str(path.with_suffix("")))
            if names and shadow is not None and shadow.package_name:
                msg = (
                    "declared publication module is shadowed by a package: "
                    f"{module_name}"
                )
                raise ValueError(msg)
            for name in names:
                cls._lazy_init_add(run, lazy_map, name, (module_name, name))
        version_path = context.pkg_dir / f"{c.Infra.DUNDER_VERSION}.py"
        if run.model.source_project.source_query(version_path, "isfile"):
            version_module = f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}"
            lazy_map.update(
                (name, (version_module, name))
                for name in python.python_model_exports(
                    python.python_model_module_at(
                        run.model, version_path, version_module
                    )
                )
                or ()
            )
        return lazy_map

    @classmethod
    def _lazy_init_child_packages(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> Sequence[str]:
        """Record importable direct child packages without publishing their names.

        The child initializer owns its own direct declarations. Its exports
        never participate in the parent's export election.

        Returns:
            The sorted child package names retained as planning metadata.

        """
        entry = run.index.packages_by_dir.get(str(context.pkg_dir))
        if entry is None:
            return ()
        children: list[str] = []
        candidates = dict.fromkeys((
            *entry.descendant_child_dirs,
            *(
                plan.context.pkg_dir
                for plan in run.plans.values()
                if plan.action == c.Infra.LazyInitAction.WRITE
                and plan.context.pkg_dir.parent == context.pkg_dir
            ),
        ))
        for child_dir in candidates:
            if child_dir.parent != context.pkg_dir:
                continue
            child = cls._lazy_init_child_name(run, context, child_dir)
            if not child:
                continue
            children.append(child)
        return tuple(sorted(children))

    @classmethod
    def _lazy_init_child_name(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
        child_dir: Path,
    ) -> str:
        """Return an importable child package name for the parent's metadata.

        A planned write counts as a package before its initializer exists; a
        planned removal or skip never does; without a plan the on-disk
        initializer decides.

        Returns:
            The child's package name, or ``""`` when it is not importable.

        """
        plan = run.plans.get(child_dir)
        action = plan.action if plan is not None else None
        written = action == c.Infra.LazyInitAction.WRITE
        if child_dir.name in c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES or not (
            written or cls.lazy_init_context(run, child_dir).importable
        ):
            return ""
        if action == c.Infra.LazyInitAction.REMOVE or (
            not written
            and not run.model.source_project.source_query(
                child_dir / c.Infra.INIT_PY, "isfile"
            )
        ):
            return ""
        entry = run.index.packages_by_dir.get(str(child_dir))
        name = (
            entry.package_name
            if entry is not None and entry.package_name
            else (f"{context.current_pkg}.{child_dir.name}" if written else "")
        )
        if (
            name
            and not written
            and entry is not None
            and not (plan is not None and plan.lazy_map)
            and not cls._lazy_init_has_live_content(run, child_dir)
        ):
            return ""
        return name

    @classmethod
    def _lazy_init_has_live_content(
        cls, run: FlextInfraModelsCodegenLazyInit.LazyInitRun, pkg_dir: Path
    ) -> bool:
        """Return whether a package tree owns a module or an authored initializer.

        Returns:
            Whether the tree carries content generation does not own.

        """
        if cls._lazy_init_owns_modules(run, pkg_dir):
            return True
        entry = run.index.packages_by_dir.get(str(pkg_dir))
        return entry is not None and any(
            (
                text := FlextInfraUtilitiesLazyInitLetters.lazy_init_text(
                    run, candidate / c.Infra.INIT_PY
                )
            )
            is not None
            and text.strip()
            and not text.startswith(c.Infra.AUTOGEN_HEADER)
            for candidate in (pkg_dir, *entry.descendant_child_dirs)
            if str(candidate) in run.index.packages_by_dir
        )

    @classmethod
    def _lazy_init_test_namespace_publics(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> t.MutableLazyAliasMap:
        """Collect the sibling public declarations the tests facade exposes.

        The generated tests namespace carries the public API of the project
        source, scripts and examples packages, so behaviour tests import only
        ``from tests import ...``. Test-only declarations remain in the tests
        package's own ``_<base>`` modules.

        Returns:
            The public declarations keyed by exported name.

        """
        entry = run.index.packages_by_dir.get(str(context.pkg_dir))
        project = entry.project_root if entry is not None else None
        if project is None:
            return {}
        publics: t.MutableLazyAliasMap = {}
        for sibling in cls._lazy_init_test_namespace_dirs(run, context, project):
            sibling_context = cls.lazy_init_context(run, sibling)
            if not sibling_context.importable:
                continue
            for name, target in cls._lazy_init_package_declarations(
                run, sibling_context
            ).items():
                publics.setdefault(name, target)
            for name in cls._lazy_init_candidate_exports(
                run, sibling, sibling_context.current_pkg
            ):
                publics[name] = (sibling_context.current_pkg, name)
        return publics

    @staticmethod
    def _lazy_init_candidate_exports(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        package_dir: Path,
        package: str,
    ) -> Sequence[str]:
        """Return a package initializer's exports in this run's candidate.

        A package this run planned publishes its planned exports; reading its
        initializer from disk would replay the previous generation and take a
        second run to converge. An unplanned package keeps its current
        initializer.

        Returns:
            The exports the candidate initializer of ``package_dir`` declares.

        """
        planned = run.plans.get(package_dir)
        if planned is not None:
            return planned.exports
        initializer = package_dir / c.Infra.INIT_PY
        if not run.model.source_project.source_query(initializer, "isfile"):
            return ()
        python = FlextInfraUtilitiesPythonModel
        return (
            python.python_model_exports(
                python.python_model_module_at(run.model, initializer, package)
            )
            or ()
        )

    @staticmethod
    def _lazy_init_test_namespace_dirs(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
        project: Path,
    ) -> tuple[Path, ...]:
        """Return the sibling namespaces the tests facade publishes.

        Returns:
            The source packages, ``scripts`` and ``examples`` directories.

        """
        directories = [
            entry.package_dir
            for entry in run.index.packages_by_dir.values()
            if entry.project_root == project
            and entry.package_dir != context.pkg_dir
            and entry.package_dir.parent == project / c.Infra.DEFAULT_SRC_DIR
        ]
        for name in (c.Infra.DIR_SCRIPTS, c.Infra.DIR_EXAMPLES):
            candidate = project / name
            if (
                str(candidate) in run.index.packages_by_dir
                and candidate != context.pkg_dir
            ):
                directories.append(candidate)
        directories.extend(
            child
            for child in sorted(
                run.model.source_project.source_children(context.pkg_dir)
            )
            if run.model.source_project.source_query(child, "isdir")
            and run.model.source_project.source_query(child / c.Infra.INIT_PY, "isfile")
            and str(child) in run.index.packages_by_dir
        )
        return tuple(sorted(dict.fromkeys(directories)))

    @staticmethod
    def _lazy_init_package_declarations(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext,
    ) -> t.MutableLazyAliasMap:
        """Collect a package's direct public declarations without election.

        The tests facade only re-exports names a namespace publishes in
        ``__all__``; it never reaches into a module that the namespace does not
        declare.

        Returns:
            The declarations keyed by exported name.

        """
        python = FlextInfraUtilitiesPythonModel
        entry = run.index.packages_by_dir.get(str(context.pkg_dir))
        declarations: t.MutableLazyAliasMap = {}
        for module in entry.modules if entry is not None else ():
            if (
                module.file_path.suffix != c.Infra.EXT_PYTHON
                or module.file_path.parent != context.pkg_dir
                or module.file_path.name == c.Infra.INIT_PY
            ):
                continue
            for name in (
                python.python_model_exports(
                    python.python_model_module_at(
                        run.model, module.file_path, module.module_name
                    )
                )
                or ()
            ):
                declarations.setdefault(name, (module.module_name, name))
        return declarations

    @classmethod
    def _lazy_init_add(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        lazy_map: t.MutableLazyAliasMap,
        name: str,
        target: tuple[str, str],
    ) -> None:
        """Insert one export; a competing target is elected or recorded ambiguous."""
        existing = lazy_map.get(name)
        if existing is None or existing == target:
            lazy_map[name] = target
            return
        elected = cls._lazy_init_elect(run, existing, target, name=name)
        if elected is not None:
            lazy_map[name] = elected
            return
        finding = (
            f"export collision for {name!r}: {existing} vs {target}; "
            "no unique native publication owner"
        )
        run.collisions.append(finding)
        u.Cli.error(finding)

    @classmethod
    def _lazy_init_elect(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        a: tuple[str, str],
        b: tuple[str, str],
        *,
        name: str,
    ) -> tuple[str, str] | None:
        """Elect between two targets that publish one declaration or class lineage.

        Order: an introducing subclass wins; a package initializer loses to a
        module; fewer private segments, a shorter path, then the higher
        publication score win; finally the sole native declaring module.

        Returns:
            The elected target, or ``None`` when the publication is ambiguous.

        """
        python = FlextInfraUtilitiesPythonModel
        modules = tuple(
            python.python_model_module(run.model, module_name)
            for module_name, _attr in (a, b)
        )
        if any(
            module is None or target[1] not in module.members
            for module, target in zip(modules, (a, b), strict=True)
        ):
            return None
        a_def, b_def = (
            python.python_model_resolve(run.model, f"{mod}.{attr}")
            for mod, attr in (a, b)
        )
        if a_def != b_def:
            if a_def in python.python_model_ancestors(run.model, b_def):
                return b
            return (
                a if b_def in python.python_model_ancestors(run.model, a_def) else None
            )
        a_init, b_init = (
            (path := run.model.module_files.get(target[0])) is not None
            and path.name == c.Infra.INIT_PY
            for target in (a, b)
        )
        if a_init or b_init:
            return None if a_init and b_init else (b if a_init else a)
        introducing = tuple(
            target
            for module, target in zip(modules, (a, b), strict=True)
            if module is not None and python.python_model_defines(module, target[1])
        )
        return cls._lazy_init_rank(run, a, b, name=name) or (
            introducing[0] if len(introducing) == 1 else None
        )

    @classmethod
    def _lazy_init_rank(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        a: tuple[str, str],
        b: tuple[str, str],
        *,
        name: str,
    ) -> tuple[str, str] | None:
        """Rank two publication routes without a filename tie-breaker.

        Returns:
            The stronger route, or ``None`` when equally authoritative.

        """
        a_parts, b_parts = a[0].split("."), b[0].split(".")
        a_private, b_private = (
            sum(part.startswith("_") and not part.endswith("__") for part in parts[1:])
            for parts in (a_parts, b_parts)
        )
        if a_private != b_private:
            return a if a_private < b_private else b
        if len(a_parts) != len(b_parts):
            return a if len(a_parts) < len(b_parts) else b
        a_score, b_score = (
            cls._lazy_init_score(run, name, a),
            cls._lazy_init_score(run, name, b),
        )
        if a_score != b_score:
            return a if a_score > b_score else b
        return None

    @staticmethod
    def _lazy_init_route_identity(
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        path: Path,
        module: FlextInfraModelsCodegenLazyInit.PythonModuleFacts,
        exports: Sequence[str],
    ) -> tuple[str | None, str | None]:
        """Return a route module's facade alias and family suffix.

        A root-namespace facade owner supplies both; otherwise the family is
        the sole public class or the directory's facade family suffix.

        Returns:
            The ``(alias, family)`` pair, each ``None`` when undeclared.

        """
        namespace = FlextInfraUtilitiesCodegenNamespace
        uppercase = tuple(export for export in exports if export[:1].isupper())
        letter = namespace.facade_family_of_directory(path.parent.name)
        family = (
            uppercase[0]
            if len(uppercase) == 1
            else (namespace.facade_families()[letter].suffix if letter else None)
        )
        entry = run.index.modules_by_path.get(str(path))
        project = entry.project_root if entry is not None else None
        owner = (
            FlextInfraUtilitiesPythonModel.python_model_facade_owner(module)
            if project is not None
            and (
                path.parent.parent == project
                or path.parent
                == FlextInfraUtilitiesLazyInitLetters.lazy_init_public_root(
                    run, project
                )
            )
            else None
        )
        return owner if owner is not None else (None, family)

    @classmethod
    def _lazy_init_score(
        cls,
        run: FlextInfraModelsCodegenLazyInit.LazyInitRun,
        name: str,
        target: tuple[str, str],
    ) -> int:
        """Score one route by its module's governed publication facts.

        Returns:
            The publication score of ``target`` for ``name``.

        """
        module_name, attr = target
        path = run.model.module_files.get(module_name)
        if path is None:
            return 0
        module = FlextInfraUtilitiesPythonModel.python_model_module_at(
            run.model, path, module_name
        )
        exports = FlextInfraUtilitiesPythonModel.python_model_exports(module) or ()
        alias, family = cls._lazy_init_route_identity(
            run,
            path,
            cast(FlextInfraModelsCodegenLazyInit.PythonModuleFacts, module),
            exports,
        )
        weight = c.Infra.LazyInitScore
        score = 0
        if alias == name:
            score += weight.FACADE_ALIAS
        elif family and name.endswith(family):
            score += weight.FAMILY_SUFFIX
        elif alias:
            score += weight.FOREIGN_ALIAS
        elif family:
            score += weight.FOREIGN_FAMILY
        root_namespace = bool(exports) and len(module_name.split(".")) <= 1
        score += (
            weight.PUBLISHED
            + weight.DECLARED * (name in exports)
            + weight.SELF_NAMED * (attr == name)
        )
        if (
            path.parent.name == c.Infra.LAZY_INIT_FIXTURES_DIR
            or alias
            or family
            or root_namespace
        ):
            score += weight.GOVERNED
        if name in c.Infra.ALIAS_NAMES and "." not in module_name:
            score += weight.BARE_ALIAS
        return score


__all__: list[str] = ["FlextInfraUtilitiesLazyInitPlan"]
