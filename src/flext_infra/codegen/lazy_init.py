"""Lazy-init ``__init__.py`` planner (PEP 562).

Each package publishes what its direct modules declare in ``__all__`` plus
its direct child packages; root namespaces inherit the facade letters of
their nearest facade parents. Facts come from one static Python model per
run; publication belongs to the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from keyword import iskeyword
from pathlib import Path
from typing import Annotated, override

from flext_infra import c, config, d, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenExecutionBase,
    FlextInfraCodegenLazyInitRender,
    FlextInfraCodegenPythonModel,
)


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenExecutionBase[bool],
    m.Infra.ModuleSelectionMixin,
):
    """Plan every generated ``__init__.py`` of the selected repositories."""

    project_scope_roots: Annotated[
        t.VariadicTuple[Path] | None,
        m.Field(
            description=(
                "Repository roots selected by conformance; None plans every "
                "package of the repository root"
            ),
        ),
    ] = None
    _view: p.Infra.RopeProject | None = m.PrivateAttr(default=None)
    _model: FlextInfraCodegenPythonModel | None = m.PrivateAttr(default=None)
    _index: m.Infra.RopeWorkspaceIndex | None = m.PrivateAttr(default=None)
    _plans: t.MutableMappingKV[Path, m.Infra.LazyInitPlan] = m.PrivateAttr(
        default_factory=dict[Path, m.Infra.LazyInitPlan],
    )
    _contexts: t.MutableMappingKV[Path, m.Infra.LazyInitPackageContext] = m.PrivateAttr(
        default_factory=dict[Path, m.Infra.LazyInitPackageContext]
    )
    _parents: t.MutableMappingKV[Path, t.StrSequence] = m.PrivateAttr(
        default_factory=dict[Path, t.StrSequence],
    )
    _declared: t.MutableMappingKV[str, frozenset[str]] = m.PrivateAttr(
        default_factory=dict[str, frozenset[str]],
    )
    _packages: t.MutableMappingKV[Path, str] = m.PrivateAttr(
        default_factory=dict[Path, str],
    )
    _collisions: int = m.PrivateAttr(default=0)

    @override
    def execute(self) -> p.Result[bool]:
        """Check lazy-init drift; publication belongs to conform.

        Returns:
            Success when every planned initializer matches its source.

        """
        planned = self.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        if not self.effective_dry_run:
            return r[bool].fail(
                "lazy-init publication is owned by codegen conform; "
                "conform must publish plan_files()",
            )
        changed = tuple(
            str(plan.path)
            for plan in planned.value
            if u.Infra.codegen_file_requires_effect(plan)
        )
        if changed:
            return r[bool].fail(
                f"init drift detected in {len(changed)} generated artifacts: "
                + ", ".join(changed),
            )
        return r[bool].ok(value=True)

    @d.log_operation("lazy_init_plan", track_perf=True)
    def plan_files(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Return the immutable initializer plans; publication belongs to conform.

        Returns:
            The initializer file plans sorted by path, or the first failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        workspace = self.repository_root.resolve()
        roots = (
            (workspace,)
            if self.project_scope_roots is None
            else tuple(sorted({root.resolve() for root in self.project_scope_roots}))
        )
        if not (
            workspace.is_dir()
            if source_project is None
            else source_project.source_query(workspace, "isdir")
        ):
            return result_type.fail(
                f"lazy-init workspace is not a directory: {workspace}"
            )
        with self._source_view(workspace, source_project, roots) as view:
            self._view = view
            invalid = next(
                (
                    root
                    for root in roots
                    if not root.is_relative_to(workspace)
                    or not view.source_query(root, "isdir")
                ),
                None,
            )
            if invalid is not None:
                return result_type.fail(
                    "lazy-init repository scope is missing or outside "
                    f"{workspace}: {invalid}",
                )
            indexes = {root: u.Infra.index_rope_workspace(view, root) for root in roots}
            targets = {
                root: self._target_dirs(index, root) if self.module else ()
                for root, index in indexes.items()
            }
            found = sum(map(len, targets.values()))
            if self.module and found != 1:
                state = "is ambiguous" if found else "not found"
                return result_type.fail(
                    f"lazy-init target module {state}: {self.module}"
                )
            by_path: dict[Path, m.Infra.CodegenFilePlan] = {}
            for root, index in indexes.items():
                if self.module and not targets[root]:
                    continue
                planned = self._plan_root(root, index, targets[root])
                if planned.failure:
                    return planned
                for file_plan in planned.value:
                    if by_path.setdefault(file_plan.path, file_plan) != file_plan:
                        return result_type.fail(
                            f"conflicting lazy-init plans for {file_plan.path}"
                        )
        files = tuple(by_path[path] for path in sorted(by_path))
        u.Cli.info(
            "Lazy-init plan: "
            f"{sum(map(u.Infra.codegen_file_requires_effect, files))} effects"
        )
        return result_type.ok(files)

    @staticmethod
    @contextmanager
    def _source_view(
        workspace: Path,
        source_project: p.Infra.RopeProject | None,
        roots: t.VariadicTuple[Path],
    ) -> Generator[p.Infra.RopeProject]:
        """Bind the run's source view without replacing an injected one.

        Yields:
            The source view every source is read through.

        Raises:
            ValueError: When the injected view does not cover the workspace.

        """
        if source_project is not None:
            if not workspace.is_relative_to(Path(source_project.root.real_path)):
                msg = "lazy-init consumer is outside its injected source view"
                raise ValueError(msg)
            yield source_project
            return
        with u.Infra.facade_source_project(
            workspace,
            project_roots=tuple(
                root for root in roots if root.is_relative_to(workspace)
            ),
        ) as (project, _):
            yield project

    @property
    def view(self) -> p.Infra.RopeProject:
        """The bound source view of the current run.

        Raises:
            ValueError: Outside ``plan_files``.

        """
        if self._view is None:
            msg = "lazy-init has no bound source view"
            raise ValueError(msg)
        return self._view

    @property
    def model(self) -> FlextInfraCodegenPythonModel:
        """The static Python model of the current repository.

        Raises:
            ValueError: Before a repository is planned.

        """
        if self._model is None:
            msg = "lazy-init has no static Python model"
            raise ValueError(msg)
        return self._model

    @property
    def index(self) -> m.Infra.RopeWorkspaceIndex:
        """The source inventory of the current repository.

        Raises:
            ValueError: Before a repository is planned.

        """
        if self._index is None:
            msg = "lazy-init has no source inventory"
            raise ValueError(msg)
        return self._index

    def _plan_root(
        self,
        root: Path,
        index: m.Infra.RopeWorkspaceIndex,
        targets: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan and render one repository bottom-up from its source inventory.

        Returns:
            The repository's initializer file plans, or the first failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        self._index = index
        self._model = FlextInfraCodegenPythonModel(
            source_project=self.view,
            module_files={
                entry.module_name: entry.file_path
                for entry in index.modules_by_path.values()
                if entry.module_name and entry.file_path.suffix == c.Infra.EXT_PYTHON
            },
        )
        self._plans.clear()
        self._contexts.clear()
        self._parents.clear()
        self._declared.clear()
        self._collisions = 0
        package_dirs = self._root_package_dirs(root)
        if package_dirs.failure:
            return result_type.from_failure(package_dirs)
        if targets and targets[0] not in package_dirs.value:
            return result_type.fail(
                f"lazy-init target belongs to retired support: {self.module}"
            )
        selected = self._plan_dirs(package_dirs.value, targets[0] if targets else None)
        if self._collisions:
            return result_type.fail(
                "lazy-init public export ownership is ambiguous: "
                f"{self._collisions} collision(s)",
            )
        return self._file_plans(selected)

    def _root_package_dirs(self, root: Path) -> p.Result[t.VariadicTuple[Path]]:
        """Return the repository's package directories, children before parents.

        Returns:
            The owned package directories, deepest first.

        """
        entries = tuple(
            self.index.packages_by_dir[str(package_dir)]
            for package_dir in self.index.package_dirs
            if package_dir.is_relative_to(root)
            and not frozenset(package_dir.relative_to(root).parts)
            & c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
        )
        if self.project_scope_roots is not None:
            unowned = next(
                (entry.package_dir for entry in entries if entry.project_root is None),
                None,
            )
            if unowned is not None:
                return r[t.VariadicTuple[Path]].fail(
                    f"lazy-init package has no repository owner: {unowned}"
                )
            entries = tuple(entry for entry in entries if entry.project_root == root)
        return r[t.VariadicTuple[Path]].ok(
            tuple(
                sorted(
                    (entry.package_dir for entry in entries),
                    key=u.Infra.path_depth,
                    reverse=True,
                )
            )
        )

    def _plan_dirs(
        self, package_dirs: t.VariadicTuple[Path], target: Path | None
    ) -> t.VariadicTuple[m.Infra.LazyInitPlan]:
        """Plan the selected tree bottom-up; a tests target keeps its descendants.

        Returns:
            The selected package plans.

        """
        selected: list[m.Infra.LazyInitPlan] = []
        for package_dir in package_dirs:
            if target is not None and not package_dir.is_relative_to(target):
                continue
            plan = self._build_plan(package_dir)
            self._plans[package_dir] = plan
            if target in {None, package_dir} or (
                target is not None and target.name == c.Infra.DIR_TESTS
            ):
                selected.append(plan)
        return tuple(selected)

    def _target_dirs(
        self, index: m.Infra.RopeWorkspaceIndex, root: Path
    ) -> t.VariadicTuple[Path]:
        """Return the package directories the selected module names in ``root``.

        Returns:
            Every matching package directory, sorted.

        """
        found = {
            entry.package_dir
            for entry in index.modules_by_path.values()
            if entry.module_name == self.module
            and (self.project_scope_roots is None or entry.project_root == root)
        }
        mapped = index.package_dir_by_name.get(self.module or "")
        if mapped is not None and (
            self.project_scope_roots is None
            or index.packages_by_dir[str(mapped)].project_root == root
        ):
            found.add(mapped)
        return tuple(sorted(found))

    def _text(self, path: Path) -> str | None:
        """Return one source through the run's view, ``None`` when absent.

        Returns:
            The source text, or ``None`` when ``path`` is not a file.

        """
        return (
            self.view.source_text(path)
            if self.view.source_query(path, "isfile")
            else None
        )

    def _context(self, pkg_dir: Path) -> m.Infra.LazyInitPackageContext:
        """Return the package context of one directory.

        Returns:
            The package's import name, surface and initializer facts.

        """
        context = self._contexts.get(pkg_dir)
        if context is None:
            entry = self.index.packages_by_dir.get(str(pkg_dir))
            name = entry.package_name if entry is not None else ""
            init = self._text(pkg_dir / c.Infra.INIT_PY)
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
            self._contexts[pkg_dir] = context
        return context

    def _build_plan(self, pkg_dir: Path) -> m.Infra.LazyInitPlan:
        """Decide one package's initializer after its children are planned.

        Returns:
            The package plan.

        """
        context = self._context(pkg_dir)
        init = self._text(context.init_path)
        if u.Infra.codegen_initializer_is_authored(
            None if init is None else init.encode(c.DEFAULT_ENCODING)
        ):
            exports = (
                self.model.exports(
                    self.model.module_at(context.init_path, context.current_pkg)
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
        if not context.importable or self._shadows_stdlib(context):
            return self._empty_plan(context, residue)
        lazy_map = self._package_exports(context)
        children = self._merge_children(context, lazy_map)
        self._resolve_aliases(context, lazy_map)
        version = (
            f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
            c.Infra.DUNDER_VERSION,
        )
        eager: t.MutableLazyAliasMap = (
            {c.Infra.DUNDER_VERSION: lazy_map.pop(c.Infra.DUNDER_VERSION)}
            if lazy_map.get(c.Infra.DUNDER_VERSION) == version
            else {}
        )
        facade_root = self._is_facade_root(context)
        if facade_root and context.current_pkg == c.Infra.DIR_TESTS:
            for name, target in c.Infra.TEST_RUNTIME_ALIAS_TARGETS.items():
                lazy_map.setdefault(name, target)
        if not lazy_map and not eager:
            keeps = (
                context.surface == c.Infra.DIR_TESTS
                and context.current_pkg != c.Infra.DIR_TESTS
            ) or self._owns_modules(pkg_dir)
            return self._empty_plan(
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
    def _empty_plan(
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
    def _is_facade_root(context: m.Infra.LazyInitPackageContext) -> bool:
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
    def _shadows_stdlib(context: m.Infra.LazyInitPackageContext) -> bool:
        """Return whether the importable name shadows a stdlib module for Ruff.

        Returns:
            Whether the name relative to its source root is a stdlib module.

        """
        parts = context.current_pkg.split(".")
        if parts[0] in c.Infra.NON_PUBLIC_LAZY_ROOTS:
            parts = parts[1:]
        return len(parts) == 1 and parts[0] in sys.stdlib_module_names

    def _owns_modules(self, pkg_dir: Path) -> bool:
        """Return whether a package tree owns any module besides initializers.

        Returns:
            Whether the package or a descendant has a non-initializer module.

        """
        entry = self.index.packages_by_dir.get(str(pkg_dir))
        if entry is None:
            return False
        return any(
            not module.is_package_init
            for candidate in (pkg_dir, *entry.descendant_child_dirs)
            if (tree := self.index.packages_by_dir.get(str(candidate))) is not None
            for module in tree.modules
        )

    def _package_exports(
        self, context: m.Infra.LazyInitPackageContext
    ) -> t.MutableLazyAliasMap:
        """Collect what the package's direct modules declare in ``__all__``.

        Returns:
            The export map of the package's own modules.

        Raises:
            ValueError: If a declaring module is shadowed by a same-named package.

        """
        lazy_map: t.MutableLazyAliasMap = {}
        entry = self.index.packages_by_dir.get(str(context.pkg_dir))
        modules = sorted(
            (module.file_path, module.module_name)
            for module in (entry.modules if entry is not None else ())
            if module.file_path.suffix == c.Infra.EXT_PYTHON
            and module.file_path.parent == context.pkg_dir
            and module.file_path.name != c.Infra.INIT_PY
        )
        for path, module_name in modules:
            names = self.model.exports(self.model.module_at(path, module_name)) or ()
            shadow = self.index.packages_by_dir.get(str(path.with_suffix("")))
            if names and shadow is not None and shadow.package_name:
                msg = (
                    "declared publication module is shadowed by a package: "
                    f"{module_name}"
                )
                raise ValueError(msg)
            for name in names:
                self._add(lazy_map, name, (module_name, name))
        version_path = context.pkg_dir / f"{c.Infra.DUNDER_VERSION}.py"
        if self.view.source_query(version_path, "isfile"):
            version_module = f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}"
            lazy_map.update(
                (name, (version_module, name))
                for name in self.model.exports(
                    self.model.module_at(version_path, version_module)
                )
                or ()
            )
        return lazy_map

    def _merge_children(
        self,
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
        entry = self.index.packages_by_dir.get(str(context.pkg_dir))
        if entry is None:
            return ()
        publish = context.surface not in c.Infra.NON_PUBLIC_LAZY_ROOTS
        facade_root = self._is_facade_root(context)
        merged: list[str] = []
        candidates = dict.fromkeys((
            *entry.descendant_child_dirs,
            *(
                plan.context.pkg_dir
                for plan in self._plans.values()
                if plan.action == c.Infra.LazyInitAction.WRITE
                and plan.context.pkg_dir.parent == context.pkg_dir
            ),
        ))
        for child_dir in candidates:
            if child_dir.parent != context.pkg_dir:
                continue
            child = self._child_name(context, child_dir)
            if not child:
                continue
            merged.append(child)
            leaf = child.rsplit(".", maxsplit=1)[-1]
            if not publish or (facade_root and leaf.startswith("_")):
                continue
            self._add(lazy_map, leaf, (child, ""))
            plan = self._plans.get(child_dir)
            for name, (module_name, attr) in (
                plan.lazy_map.items() if plan is not None else ()
            ):
                if (
                    attr
                    and not name.startswith("_")
                    and name not in {c.Infra.DUNDER_INIT, "pytestmark"}
                    and c.Infra.TEST_ONLY_SOURCE_MODULE_RE.fullmatch(
                        f"{module_name.rsplit('.', maxsplit=1)[-1]}.py"
                    )
                    is None
                ):
                    self._add(lazy_map, name, (module_name, attr))
        return tuple(sorted(merged))

    def _child_name(
        self, context: m.Infra.LazyInitPackageContext, child_dir: Path
    ) -> str:
        """Return the import name of a child package that merges into its parent.

        A planned write counts as a package before its initializer exists; a
        planned removal or skip never does; without a plan the on-disk
        initializer decides.

        Returns:
            The child's package name, or ``""`` when it does not merge.

        """
        plan = self._plans.get(child_dir)
        action = plan.action if plan is not None else None
        written = action == c.Infra.LazyInitAction.WRITE
        if child_dir.name in c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES or not (
            written or self._context(child_dir).importable
        ):
            return ""
        if action == c.Infra.LazyInitAction.REMOVE or (
            not written
            and not self.view.source_query(child_dir / c.Infra.INIT_PY, "isfile")
        ):
            return ""
        entry = self.index.packages_by_dir.get(str(child_dir))
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
            and not self._has_live_content(child_dir)
        ):
            return ""
        return name

    def _has_live_content(self, pkg_dir: Path) -> bool:
        """Return whether a package tree owns a module or an authored initializer.

        Returns:
            Whether the tree carries content generation does not own.

        """
        if self._owns_modules(pkg_dir):
            return True
        entry = self.index.packages_by_dir.get(str(pkg_dir))
        return entry is not None and any(
            (text := self._text(candidate / c.Infra.INIT_PY)) is not None
            and text.strip()
            and not text.startswith(c.Infra.AUTOGEN_HEADER)
            for candidate in (pkg_dir, *entry.descendant_child_dirs)
            if str(candidate) in self.index.packages_by_dir
        )

    def _add(
        self, lazy_map: t.MutableLazyAliasMap, name: str, target: t.StrPair
    ) -> None:
        """Insert one export; a competing target is elected or counted as ambiguous."""
        existing = lazy_map.get(name)
        if existing is None or existing == target:
            lazy_map[name] = target
            return
        elected = self._elect_reexport(existing, target, name=name)
        if elected is not None:
            lazy_map[name] = elected
            return
        self._collisions += 1
        u.Cli.error(
            f"export collision for {name!r}: {existing} vs {target}; "
            "no unique native publication owner",
        )

    def _elect_reexport(
        self, a: t.StrPair, b: t.StrPair, *, name: str
    ) -> t.StrPair | None:
        """Elect between two targets that publish one declaration or class lineage.

        Order: an introducing subclass wins; a package initializer loses to a
        module; fewer private segments, a shorter path, then the higher
        publication score win; finally the sole native declaring module.

        Returns:
            The elected target, or ``None`` when the publication is ambiguous.

        """
        model = self.model
        modules = tuple(
            model.module(module_name) if attr else None for module_name, attr in (a, b)
        )
        if any(
            module is None or target[1] not in module.members
            for module, target in zip(modules, (a, b), strict=True)
        ):
            return None
        a_def, b_def = (model.resolve(f"{mod}.{attr}") for mod, attr in (a, b))
        if a_def != b_def:
            return self._lineage_winner(a, b, a_def, b_def)
        a_init, b_init = (
            (path := model.locate(target[0])) is not None
            and path.name == c.Infra.INIT_PY
            for target in (a, b)
        )
        if a_init or b_init:
            return None if a_init and b_init else (b if a_init else a)
        introducing = tuple(
            target
            for module, target in zip(modules, (a, b), strict=True)
            if module is not None and model.defines(module, target[1])
        )
        return self._rank(a, b, name=name) or (
            introducing[0] if len(introducing) == 1 else None
        )

    def _lineage_winner(
        self, a: t.StrPair, b: t.StrPair, a_def: str, b_def: str
    ) -> t.StrPair | None:
        """Elect the subclass of two distinct declarations in one class lineage.

        Returns:
            The introducing subclass, or ``None`` for unrelated declarations.

        """
        if a_def in self.model.ancestors(b_def):
            return b
        if b_def in self.model.ancestors(a_def):
            return a
        return None

    def _rank(self, a: t.StrPair, b: t.StrPair, *, name: str) -> t.StrPair | None:
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
        a_score, b_score = self._score(name, a), self._score(name, b)
        if a_score != b_score:
            return a if a_score > b_score else b
        return None

    def _score(self, name: str, target: t.StrPair) -> int:
        """Score one route by its module's governed publication facts.

        Returns:
            The publication score of ``target`` for ``name``.

        """
        module_name, attr = target
        path = self.model.module_files.get(module_name)
        if path is None:
            return 0
        module = self.model.module_at(path, module_name)
        exports = self.model.exports(module) or ()
        uppercase = tuple(export for export in exports if export[:1].isupper())
        letter = u.Infra.facade_family_of_directory(path.parent.name)
        family = (
            uppercase[0]
            if len(uppercase) == 1
            else (u.Infra.facade_families()[letter].suffix if letter else None)
        )
        alias: str | None = None
        entry = self.index.modules_by_path.get(str(path))
        project = entry.project_root if entry is not None else None
        if project is not None and (
            path.parent.parent == project or path.parent == self._public_root(project)
        ):
            owner = self.model.facade_owner(module)
            if owner is not None:
                alias, family = owner
        score = 0
        if alias == name:
            score += 100
        elif family and name.endswith(family):
            score += 25
        elif alias:
            score -= 40
        elif family:
            score -= 20
        root_namespace = bool(exports) and len(module_name.split(".")) <= 1
        score += 20 + 15 * (name in exports) + 3 * (attr == name)
        if path.parent.name == "_fixtures" or alias or family or root_namespace:
            score += 10
        if name in c.Infra.ALIAS_NAMES and "." not in module_name:
            score -= 80
        return score

    def _public_root(self, project_root: Path) -> Path | None:
        """Return the project's declared public ``src`` package directory.

        Returns:
            The package directory, or ``None`` without a declared package.

        """
        package = self._packages.get(project_root)
        if package is None:
            package = u.Infra.project_package_name(
                project_root, source_project=self.view
            )
            self._packages[project_root] = package
        return (
            project_root.joinpath(c.Infra.DEFAULT_SRC_DIR, *package.split("."))
            if package
            else None
        )

    def _resolve_aliases(
        self,
        context: m.Infra.LazyInitPackageContext,
        lazy_map: t.MutableLazyAliasMap,
    ) -> None:
        """Inherit facade letters of a root namespace from its facade parents.

        Discovery reads the nearest-first facade chain; the election walks
        only this project's chain (foreign parents are leaves) and takes the
        nearest parent that declares the letter, else the nearest that serves
        it. Local owners and foreign local overrides are never replaced.
        """
        pkg_dir, current = context.pkg_dir, context.current_pkg
        entry = self.index.packages_by_dir.get(str(pkg_dir))
        project = entry.project_root if entry is not None else None
        if project is None or (
            pkg_dir.parent != project and pkg_dir != self._public_root(project)
        ):
            return
        local_owners = {
            owner[0]
            for child in self.view.source_children(pkg_dir)
            if child.suffix == c.Infra.EXT_PYTHON
            and child.name != c.Infra.INIT_PY
            and child.stem.isidentifier()
            and self.view.source_query(child, "isfile")
            and (
                owner := self.model.facade_owner(
                    self.model.module_at(child, f"{current}.{child.stem}")
                )
            )
            is not None
        }
        direct = (
            *self._parent_packages(pkg_dir),
            self.index.project_package_by_root.get(str(project), ""),
        )
        discovery = self._facade_chain(direct, within=None)
        election = tuple(
            name
            for name in self._facade_chain(direct, within=project)
            if name != current
        )
        letters = dict.fromkeys(
            name
            for package in discovery
            for name in sorted(self._package_names(package))
            if name.isidentifier() and name.islower() and not name.startswith("_")
        )
        for letter in letters:
            existing = lazy_map.get(letter)
            if letter in local_owners or (
                existing is not None and existing[0] != current
            ):
                continue
            owner = next(
                (
                    package
                    for package in election
                    if letter in self._declared_letters(package)
                ),
                "",
            ) or next(
                (
                    package
                    for package in election
                    if self._serves(package, letter, set())
                ),
                "",
            )
            if owner:
                lazy_map[letter] = (owner, letter)
            elif existing is not None:
                del lazy_map[letter]

    def _facade_chain(
        self, packages: t.StrSequence, *, within: Path | None
    ) -> t.StrSequence:
        """Expand facade parents breadth-first, nearest first.

        ``within`` limits expansion to that project's packages; parents of
        other projects stay leaves served through their published surface.

        Returns:
            The packages followed by their transitive facade parents.

        """
        ordered: list[str] = []
        queue = list(packages)
        while queue:
            package = queue.pop(0)
            if not package or package in ordered:
                continue
            ordered.append(package)
            package_dir = self.index.package_dir_by_name.get(package)
            if package_dir is None:
                continue
            entry = self.index.packages_by_dir.get(str(package_dir))
            if within is None or (entry is not None and entry.project_root == within):
                queue.extend(self._parent_packages(package_dir))
        return tuple(ordered)

    def _parent_packages(self, pkg_dir: Path) -> t.StrSequence:
        """Return the facade parents declared by ``constants.py`` class bases.

        Returns:
            The parent package names, nearest first.

        """
        cached = self._parents.get(pkg_dir)
        if cached is None:
            entry = self.index.packages_by_dir.get(str(pkg_dir))
            constants = pkg_dir / c.Infra.CONSTANTS_PY
            cached = (
                self._constants_parents(
                    constants, entry.package_name if entry is not None else "", set()
                )
                if self.view.source_query(constants, "isfile")
                else ()
            )
            self._parents[pkg_dir] = cached
        return cached

    def _constants_parents(
        self, path: Path, current: str, seen: set[Path]
    ) -> t.StrSequence:
        """Follow ``*Constants`` class bases, recursing into same-package owners.

        Returns:
            The declared parent packages in declaration order.

        Raises:
            ValueError: If a declared base resolves to no package.

        """
        seen.add(path)
        entry = self.index.modules_by_path.get(str(path))
        module = self.model.module_at(path, entry.module_name if entry else current)
        targets = tuple(
            f"{target}.{tail}" if tail else target
            for name, bases in self.model.class_bases(module).items()
            if "Constants" in name
            for base in bases
            for head, _, tail in (base.partition("."),)
            if (target := module.imports.get(head))
        )
        found: list[str] = []
        for target in targets:
            if target.startswith(f"{current}."):
                continue
            parts = target.split(".")
            package = next(
                (
                    ".".join(parts[:size])
                    for size in range(len(parts), 0, -1)
                    if ".".join(parts[:size]) in self.index.package_dir_by_name
                ),
                parts[0] if self.model.package_dir(parts[0]) is not None else "",
            )
            if not package:
                msg = (
                    f"lazy-init: declared facade parent '{parts[0]}' "
                    "resolves nowhere in the active environment"
                )
                raise ValueError(msg)
            found.append(package)
        for target in targets:
            if not target.startswith(f"{current}."):
                continue
            head, _, last = target.rpartition(".")
            owner = self.model.module_files.get(head if last[:1].isupper() else target)
            if owner is not None and owner not in seen:
                found.extend(self._constants_parents(owner, current, seen))
        return tuple(dict.fromkeys(p for p in found if p and p != current))

    def _package_dir(self, package: str) -> t.Pair[Path | None, bool]:
        """Return a package's directory and whether this run indexes it.

        Returns:
            The indexed or installed directory and the indexed flag.

        """
        indexed = self.index.package_dir_by_name.get(package)
        if indexed is not None:
            return indexed, True
        return self.model.package_dir(package), False

    def _declared_letters(self, package: str) -> frozenset[str]:
        """Return the facade letters a package's own modules declare.

        An indexed package's generated initializer is this run's output and
        never a declaration owner; an installed package's initializer is.

        Returns:
            The declared letters.

        """
        cached = self._declared.get(package)
        if cached is None:
            package_dir, indexed = self._package_dir(package)
            cached = frozenset(
                letter
                for child in (
                    self.view.source_children(package_dir)
                    if package_dir is not None
                    else ()
                )
                if child.suffix == c.Infra.EXT_PYTHON
                and not (indexed and child.name == c.Infra.INIT_PY)
                and self.view.source_query(child, "isfile")
                for letter in self.model.letters(
                    self.model.module_at(
                        child,
                        package
                        if child.name == c.Infra.INIT_PY
                        else f"{package}.{child.stem}",
                    )
                )
            )
            self._declared[package] = cached
        return cached

    def _package_names(self, package: str) -> frozenset[str]:
        """Return a parent's published names plus its declared letters.

        Returns:
            The candidate letter names of one parent.

        Raises:
            ValueError: If an installed parent is a module, not a package.

        """
        package_dir, indexed = self._package_dir(package)
        if package_dir is None:
            msg = (
                f"lazy-init facade parent '{package}' resolves to a module,"
                " not a package, in the active environment"
            )
            raise ValueError(msg)
        init_path = package_dir / c.Infra.INIT_PY
        text = self._text(init_path)
        names: t.StrSequence = ()
        generated = text is not None and text.startswith(c.Infra.AUTOGEN_HEADERS)
        if text is not None and not (
            indexed and generated and u.Infra.first_merge_conflict_marker(text)
        ):
            module = self.model.module_at(init_path, package)
            declared = self.model.exports(module)
            names = (
                self.model.implicit_exports(module)
                if declared is None and indexed and not generated
                else declared or ()
            )
        return (
            frozenset(names) | self._declared_letters(package)
            if indexed
            else frozenset(names)
        )

    def _serves(self, package: str, letter: str, visited: set[str]) -> bool:
        """Return whether a package declares a letter or re-exports a declarer's.

        Returns:
            Whether ``package`` serves ``letter``.

        """
        if package in visited:
            return False
        visited.add(package)
        if letter in self._declared_letters(package):
            return True
        package_dir, indexed = self._package_dir(package)
        init_path = None if package_dir is None else package_dir / c.Infra.INIT_PY
        text = None if init_path is None else self._text(init_path)
        if (
            indexed
            and package_dir is not None
            and (
                text is None
                or not u.Infra.codegen_initializer_is_authored(
                    text.encode(c.DEFAULT_ENCODING)
                )
            )
        ):
            sources = self._parent_packages(package_dir)
        elif init_path is not None and text is not None:
            target = self.model.import_target(
                self.model.module_at(init_path, package), letter
            )
            sources = (target.split(".", maxsplit=1)[0],) if target else ()
        else:
            sources = ()
        return any(self._serves(source, letter, visited) for source in sources)

    def _file_plans(
        self, plans: t.VariadicTuple[m.Infra.LazyInitPlan]
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind every decided initializer and generated-source tree to its effect.

        Returns:
            The file plans sorted by destination path.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        by_path: dict[Path, m.Infra.CodegenFilePlan] = {}
        for plan in plans:
            entry = self.index.packages_by_dir.get(str(plan.context.pkg_dir))
            project = entry.project_root if entry is not None else None
            if project is None:
                return result_type.fail(
                    "lazy-init package has no physical project owner: "
                    f"{plan.context.pkg_dir}",
                )
            for path, desired in self._effects(plan):
                file_plan = m.Infra.CodegenFilePlan(
                    project=project,
                    path=path,
                    before=self.view.source_state(path, required=False),
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

    def _effects(
        self, plan: m.Infra.LazyInitPlan
    ) -> t.SequenceOf[t.Pair[Path, bytes | None]]:
        """Return the desired bytes of one package and its generated-source trees.

        Returns:
            ``(path, desired)`` pairs; ``None`` removes a generated file.

        """
        effects: list[t.Pair[Path, bytes | None]] = []
        if plan.action == c.Infra.LazyInitAction.WRITE:
            effects.append((plan.context.init_path, self._render(plan)))
        elif plan.action == c.Infra.LazyInitAction.REMOVE:
            effects.append((plan.context.init_path, None))
        names = frozenset(config.Infra.codegen.generated_sources)
        for tree in sorted(
            child
            for child in self.view.source_children(plan.context.pkg_dir)
            if child.name in names and self.view.source_query(child, "isdir")
        ):
            init_path = tree / c.Infra.INIT_PY
            text = self._text(init_path)
            if u.Infra.codegen_initializer_is_authored(
                None if text is None else text.encode(c.DEFAULT_ENCODING)
            ):
                continue
            generated = text is not None and text.startswith(c.Infra.AUTOGEN_HEADERS)
            if any(
                module.suffix == c.Infra.EXT_PYTHON
                and module.name != c.Infra.INIT_PY
                and self.view.source_query(module, "isfile")
                for module in self.view.source_children(tree)
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
                effects.append((init_path, self._render(tree_plan)))
            elif generated:
                effects.append((init_path, None))
        return effects

    def _render(self, plan: m.Infra.LazyInitPlan) -> bytes:
        """Render one written initializer.

        Returns:
            The initializer bytes.

        """
        return FlextInfraCodegenLazyInitRender.render(plan, model=self.model).encode(
            c.DEFAULT_ENCODING
        )


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
