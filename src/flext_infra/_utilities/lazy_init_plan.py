"""Lazy-init package planning over one repository run (``u.Infra``).

Each package publishes what its direct modules declare in ``__all__`` plus
its direct child packages; the facade root withholds private children and
nested exports; root namespaces inherit their facade letters.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from keyword import iskeyword
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.codegen_file_plan import FlextInfraUtilitiesCodegenFilePlan
from flext_infra._utilities.lazy_init_letters import FlextInfraUtilitiesLazyInitLetters
from flext_infra._utilities.lazy_init_render import FlextInfraUtilitiesLazyInitRender
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.python_model import FlextInfraUtilitiesPythonModel


class FlextInfraUtilitiesLazyInitPlan:
    """Decide every package initializer of one repository, children first."""

    @staticmethod
    def lazy_init_run(
        source_project: p.Infra.RopeProject,
        index: m.Infra.RopeWorkspaceIndex,
        *,
        root: Path,
        scoped: bool,
    ) -> m.Infra.LazyInitRun:
        """Open one repository run over its source inventory.

        Returns:
            The run every planning step reads and caches through.

        """
        return m.Infra.LazyInitRun(
            root=root,
            scoped=scoped,
            index=index,
            model=FlextInfraUtilitiesPythonModel.python_model_run(
                source_project,
                {
                    entry.module_name: entry.file_path
                    for entry in index.modules_by_path.values()
                    if entry.module_name
                    and entry.file_path.suffix == c.Infra.EXT_PYTHON
                },
            ),
            plans={},
            contexts={},
            parents={},
            declared={},
            packages={},
            collisions=[],
        )

    @staticmethod
    def lazy_init_target_dirs(
        index: m.Infra.RopeWorkspaceIndex,
        root: Path,
        *,
        module: str,
        scoped: bool,
    ) -> t.VariadicTuple[Path]:
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
        cls, run: m.Infra.LazyInitRun, target: Path | None
    ) -> p.Result[t.VariadicTuple[m.Infra.LazyInitPlan]]:
        """Plan the repository's packages bottom-up; a target narrows the tree.

        ``target`` is the selected package directory, ``None`` plans the tree.

        Returns:
            The selected package plans, or the first planning failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.LazyInitPlan]]
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
        package_dirs = sorted(
            (entry.package_dir for entry in entries),
            key=FlextInfraUtilitiesBase.path_depth,
            reverse=True,
        )
        if target is not None and target not in package_dirs:
            return result_type.fail(
                f"lazy-init target belongs to retired support: {target}"
            )
        selected: list[m.Infra.LazyInitPlan] = []
        for package_dir in package_dirs:
            if target is not None and not package_dir.is_relative_to(target):
                continue
            plan = cls._lazy_init_build_plan(run, package_dir)
            run.plans[package_dir] = plan
            if target in {None, package_dir} or (
                target is not None and target.name == c.Infra.DIR_TESTS
            ):
                selected.append(plan)
        if run.collisions:
            return result_type.fail(
                "lazy-init public export ownership is ambiguous: "
                f"{len(run.collisions)} collision(s)",
            )
        return result_type.ok(tuple(selected))

    @classmethod
    def lazy_init_file_plans(
        cls,
        run: m.Infra.LazyInitRun,
        plans: t.VariadicTuple[m.Infra.LazyInitPlan],
        *,
        first_party: t.MappingKV[Path, frozenset[str]],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind every decided initializer and generated-source tree to its effect.

        ``first_party`` maps each owning project root to its first-party
        namespaces.

        Returns:
            The file plans sorted by destination path.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        view = run.model.source_project
        by_path: dict[Path, m.Infra.CodegenFilePlan] = {}
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
                file_plan = m.Infra.CodegenFilePlan(
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
        run: m.Infra.LazyInitRun,
        plan: m.Infra.LazyInitPlan,
        first_party: frozenset[str],
    ) -> t.SequenceOf[t.Pair[Path, bytes | None]]:
        """Return the desired bytes of one package and its generated-source trees.

        Returns:
            ``(path, desired)`` pairs; ``None`` removes a generated file.

        """
        render = FlextInfraUtilitiesLazyInitRender.lazy_init_render
        view = run.model.source_project
        effects: list[t.Pair[Path, bytes | None]] = []
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
            init_path = tree / c.Infra.INIT_PY
            text = FlextInfraUtilitiesLazyInitLetters.lazy_init_text(run, init_path)
            if FlextInfraUtilitiesCodegenFilePlan.codegen_initializer_is_authored(
                None if text is None else text.encode(c.DEFAULT_ENCODING)
            ):
                continue
            generated = text is not None and text.startswith(c.Infra.AUTOGEN_HEADERS)
            if any(
                module.suffix == c.Infra.EXT_PYTHON
                and module.name != c.Infra.INIT_PY
                and view.source_query(module, "isfile")
                for module in view.source_children(tree)
            ):
                tree_plan = m.Infra.LazyInitPlan(
                    context=m.Infra.LazyInitPackageContext(
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
        cls, run: m.Infra.LazyInitRun, pkg_dir: Path
    ) -> m.Infra.LazyInitPackageContext:
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
            context = m.Infra.LazyInitPackageContext(
                pkg_dir=pkg_dir,
                init_path=pkg_dir / c.Infra.INIT_PY,
                current_pkg=name,
                surface=name.split(".", maxsplit=1)[0],
                generated_init=init is not None
                and init.startswith(c.Infra.AUTOGEN_HEADERS),
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
        cls, run: m.Infra.LazyInitRun, pkg_dir: Path
    ) -> m.Infra.LazyInitPlan:
        """Decide one package's initializer after its children are planned.

        Returns:
            The package plan.

        """
        python = FlextInfraUtilitiesPythonModel
        context = cls.lazy_init_context(run, pkg_dir)
        init = FlextInfraUtilitiesLazyInitLetters.lazy_init_text(run, context.init_path)
        if FlextInfraUtilitiesCodegenFilePlan.codegen_initializer_is_authored(
            None if init is None else init.encode(c.DEFAULT_ENCODING)
        ):
            exports = (
                python.python_model_exports(
                    python.python_model_module_at(
                        run.model, context.init_path, context.current_pkg
                    )
                )
                or ()
            )
            return m.Infra.LazyInitPlan(
                context=context,
                action=c.Infra.LazyInitAction.RETAIN,
                ownership="authored",
                disposition="retained",
                exports=tuple(sorted(exports)),
                lazy_map={name: (context.current_pkg, name) for name in exports},
                eager_dunders={},
            )
        residue = (
            c.Infra.LazyInitAction.REMOVE
            if context.generated_init
            else c.Infra.LazyInitAction.SKIP
        )
        if not context.importable or cls._lazy_init_shadows_stdlib(context):
            return cls._lazy_init_empty_plan(context, residue)
        lazy_map = cls._lazy_init_package_exports(run, context)
        children = cls._lazy_init_merge_children(run, context, lazy_map)
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
        if not lazy_map and not eager:
            keeps = (
                context.surface == c.Infra.DIR_TESTS
                and context.current_pkg != c.Infra.DIR_TESTS
            ) or cls._lazy_init_owns_modules(run, pkg_dir)
            return cls._lazy_init_empty_plan(
                context, c.Infra.LazyInitAction.WRITE if keeps else residue
            )
        if facade_root:
            root = context.current_pkg
            lazy_map = {
                name: target
                for name, target in lazy_map.items()
                if target[0].rsplit(".", maxsplit=1)[0] == root
                or not target[0].startswith(f"{root}.")
            }
            children = ()
        return m.Infra.LazyInitPlan(
            context=context,
            action=c.Infra.LazyInitAction.WRITE,
            ownership="generator",
            disposition="planned",
            exports=tuple(sorted({*lazy_map, *eager})),
            lazy_map=lazy_map,
            eager_dunders=eager,
            child_packages_for_lazy=children,
        )

    @staticmethod
    def _lazy_init_empty_plan(
        context: m.Infra.LazyInitPackageContext,
        action: c.Infra.LazyInitAction,
    ) -> m.Infra.LazyInitPlan:
        """Return a plan without exports for one decided action.

        Returns:
            The plan; written and removed initializers are generator-owned.

        """
        owned = action in {c.Infra.LazyInitAction.WRITE, c.Infra.LazyInitAction.REMOVE}
        return m.Infra.LazyInitPlan(
            context=context,
            action=action,
            ownership="generator" if owned else None,
            disposition="planned" if owned else None,
            lazy_map={},
            eager_dunders={},
        )

    @staticmethod
    def lazy_init_is_facade_root(context: m.Infra.LazyInitPackageContext) -> bool:
        """Return whether a package is a public ``src`` root or the tests root.

        Returns:
            Whether the package withholds private children and nested exports.

        """
        name = context.current_pkg
        return bool(
            context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and name
            and "." not in name
        ) or (name == c.Infra.DIR_TESTS and context.pkg_dir.name == c.Infra.DIR_TESTS)

    @staticmethod
    def _lazy_init_shadows_stdlib(context: m.Infra.LazyInitPackageContext) -> bool:
        """Return whether the importable name shadows a stdlib module for Ruff.

        Returns:
            Whether the name relative to its source root is a stdlib module.

        """
        parts = context.current_pkg.split(".")
        if parts[0] in c.Infra.NON_PUBLIC_LAZY_ROOTS:
            parts = parts[1:]
        return len(parts) == 1 and parts[0] in sys.stdlib_module_names

    @staticmethod
    def _lazy_init_owns_modules(run: m.Infra.LazyInitRun, pkg_dir: Path) -> bool:
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
        cls, run: m.Infra.LazyInitRun, context: m.Infra.LazyInitPackageContext
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
        for path, module_name in modules:
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
    def _lazy_init_merge_children(
        cls,
        run: m.Infra.LazyInitRun,
        context: m.Infra.LazyInitPackageContext,
        lazy_map: t.MutableLazyAliasMap,
    ) -> t.StrSequence:
        """Publish direct child packages and their exports into the parent.

        Non-public tiers (tests, examples, scripts) list no children; the
        facade root withholds private ``_x`` children; every other package
        publishes all of them (operator ruling 2026-10-24).

        Returns:
            The sorted names of the merged child packages.

        """
        entry = run.index.packages_by_dir.get(str(context.pkg_dir))
        if entry is None:
            return ()
        publish = context.surface not in c.Infra.NON_PUBLIC_LAZY_ROOTS
        facade_root = cls.lazy_init_is_facade_root(context)
        merged: list[str] = []
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
            merged.append(child)
            leaf = child.rsplit(".", maxsplit=1)[-1]
            if not publish or (facade_root and leaf.startswith("_")):
                continue
            cls._lazy_init_add(run, lazy_map, leaf, (child, ""))
            plan = run.plans.get(child_dir)
            for name, (module_name, attr) in (
                plan.lazy_map.items() if plan is not None else ()
            ):
                if (
                    attr
                    and not name.startswith("_")
                    and name not in c.Infra.LAZY_INIT_HIDDEN_CHILD_EXPORTS
                    and c.Infra.TEST_ONLY_SOURCE_MODULE_RE.fullmatch(
                        f"{module_name.rsplit('.', maxsplit=1)[-1]}.py"
                    )
                    is None
                ):
                    cls._lazy_init_add(run, lazy_map, name, (module_name, attr))
        return tuple(sorted(merged))

    @classmethod
    def _lazy_init_child_name(
        cls,
        run: m.Infra.LazyInitRun,
        context: m.Infra.LazyInitPackageContext,
        child_dir: Path,
    ) -> str:
        """Return the import name of a child package that merges into its parent.

        A planned write counts as a package before its initializer exists; a
        planned removal or skip never does; without a plan the on-disk
        initializer decides.

        Returns:
            The child's package name, or ``""`` when it does not merge.

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
        cls, run: m.Infra.LazyInitRun, pkg_dir: Path
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
    def _lazy_init_add(
        cls,
        run: m.Infra.LazyInitRun,
        lazy_map: t.MutableLazyAliasMap,
        name: str,
        target: t.StrPair,
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
        cls, run: m.Infra.LazyInitRun, a: t.StrPair, b: t.StrPair, *, name: str
    ) -> t.StrPair | None:
        """Elect between two targets that publish one declaration or class lineage.

        Order: an introducing subclass wins; a package initializer loses to a
        module; fewer private segments, a shorter path, then the higher
        publication score win; finally the sole native declaring module.

        Returns:
            The elected target, or ``None`` when the publication is ambiguous.

        """
        python = FlextInfraUtilitiesPythonModel
        modules = tuple(
            python.python_model_module(run.model, module_name) if attr else None
            for module_name, attr in (a, b)
        )
        if any(
            module is None or target[1] not in python.python_model_members(module)
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
            (path := python.python_model_locate(run.model, target[0])) is not None
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
        cls, run: m.Infra.LazyInitRun, a: t.StrPair, b: t.StrPair, *, name: str
    ) -> t.StrPair | None:
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
        run: m.Infra.LazyInitRun,
        path: Path,
        module: t.Infra.PythonModule,
        exports: t.StrSequence,
    ) -> t.Pair[str | None, str | None]:
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
        cls, run: m.Infra.LazyInitRun, name: str, target: t.StrPair
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
        alias, family = cls._lazy_init_route_identity(run, path, module, exports)
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
