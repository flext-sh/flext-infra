"""Facade-letter election for lazy-init root namespaces (``u.Infra``).

A root namespace inherits the facade letters of its facade parents: the
nearest parent that declares a letter wins, else the nearest that serves it
through its effective published surface. The public root also publishes its
manifest-declared upstream facets after native identity verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesPyprojectConform,
    FlextInfraUtilitiesPythonModel,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesLazyInitLetters:
    """Elect inherited facade letters over one lazy-init run."""

    @staticmethod
    def lazy_init_text(run: m.Infra.LazyInitRun, path: Path) -> str | None:
        """Return one source through the run's view, ``None`` when absent.

        Returns:
            The source text, or ``None`` when ``path`` is not a file.

        """
        view = run.model.source_project
        return view.source_text(path) if view.source_query(path, "isfile") else None

    @staticmethod
    def lazy_init_public_root(
        run: m.Infra.LazyInitRun, project_root: Path
    ) -> Path | None:
        """Return the project's declared public ``src`` package directory.

        Returns:
            The package directory, or ``None`` without a declared package.

        """
        package = run.packages.get(project_root)
        if package is None:
            package = FlextInfraUtilitiesPyprojectConform.project_package_name(
                project_root, source_project=run.model.source_project
            )
            run.packages[project_root] = package
        return (
            project_root.joinpath(c.Infra.DEFAULT_SRC_DIR, *package.split("."))
            if package
            else None
        )

    @classmethod
    def lazy_init_resolve_aliases(
        cls,
        run: m.Infra.LazyInitRun,
        context: m.Infra.LazyInitPackageContext,
        lazy_map: t.MutableLazyAliasMap,
    ) -> None:
        """Inherit facade letters of a root namespace from its facade parents.

        Discovery reads the nearest-first facade chain; the election walks
        only this project's chain (foreign parents are leaves) and takes the
        nearest parent that declares the letter, else the nearest actual
        publisher. A transitive dependency does not establish publication.
        Local owners win; manifest facets require identical upstream bindings.
        """
        python = FlextInfraUtilitiesPythonModel
        pkg_dir, current = context.pkg_dir, context.current_pkg
        entry = run.index.packages_by_dir.get(str(pkg_dir))
        project = entry.project_root if entry is not None else None
        if project is None or (
            pkg_dir.parent != project
            and pkg_dir != cls.lazy_init_public_root(run, project)
        ):
            return
        view = run.model.source_project
        local_owners = {
            owner[0]
            for child in view.source_children(pkg_dir)
            if child.suffix == c.Infra.EXT_PYTHON
            and child.name != c.Infra.INIT_PY
            and child.stem.isidentifier()
            and view.source_query(child, "isfile")
            and (
                owner := python.python_model_facade_owner(
                    python.python_model_module_at(
                        run.model, child, f"{current}.{child.stem}"
                    )
                )
            )
            is not None
        }
        direct = (
            *cls.lazy_init_parent_packages(run, pkg_dir),
            run.index.project_package_by_root.get(str(project), ""),
        )
        election = tuple(
            name
            for name in cls._lazy_init_facade_chain(run, direct, within=project)
            if name != current
        )
        letters = dict.fromkeys(
            name
            for package in cls._lazy_init_facade_chain(run, direct, within=None)
            for name in sorted(cls._lazy_init_package_names(run, package))
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
                    if letter in cls._lazy_init_declared_letters(run, package)
                    and letter in cls._lazy_init_package_names(run, package)
                ),
                "",
            ) or next(
                (
                    package
                    for package in election
                    if letter in cls._lazy_init_package_names(run, package)
                ),
                "",
            )
            if owner:
                lazy_map[letter] = (owner, letter)
            elif existing is not None:
                del lazy_map[letter]
        if pkg_dir == cls.lazy_init_public_root(run, project):
            cls._lazy_init_inherited_facets(run, context, lazy_map, local_owners)

    @classmethod
    def _lazy_init_inherited_facets(
        cls,
        run: m.Infra.LazyInitRun,
        context: m.Infra.LazyInitPackageContext,
        lazy_map: t.MutableLazyAliasMap,
        local_owners: set[str],
    ) -> None:
        """Publish only explicitly declared upstream facets by native identity.

        An absent optional project subsection declares no manifest-only facets;
        ordinary source-derived letters remain governed by ADR-018.

        Raises:
            ValueError: If a declared owner or inherited publication is invalid.

        """
        view = run.model.source_project
        project = run.index.packages_by_dir[str(context.pkg_dir)].project_root
        if project is None:
            msg = f"lazy-init public root has no repository owner: {context.pkg_dir}"
            raise ValueError(msg)
        declaration = (
            FlextInfraUtilitiesProjectManagedArtifacts
            .load_repository_declaration_inputs(project, source_project=view)
            .unwrap()
            .spec.project
        )
        if declaration is None:
            return
        upstream = declaration.upstream
        facets = dict.fromkeys(declaration.inherited_facets)
        for name in cls._lazy_init_imported_facets(run, context, upstream):
            facets.setdefault(name)
        for name in facets:
            if name in local_owners:
                continue
            if name not in cls._lazy_init_package_names(run, upstream):
                msg = f"lazy-init upstream '{upstream}' does not publish facet '{name}'"
                raise ValueError(msg)
            canonical = cls._lazy_init_facet_binding(run, (upstream, name))
            existing = lazy_map.get(name)
            if existing is not None and existing[0] != context.current_pkg:
                actual = cls._lazy_init_facet_binding(run, existing)
                if actual.get_object() is not canonical.get_object():
                    msg = (
                        f"lazy-init ambiguous inherited facet '{name}': "
                        f"{existing} differs from {(upstream, name)}"
                    )
                    raise ValueError(msg)
            lazy_map[name] = (upstream, name)

    @classmethod
    def _lazy_init_imported_facets(
        cls,
        run: m.Infra.LazyInitRun,
        context: m.Infra.LazyInitPackageContext,
        upstream: str,
    ) -> t.StrSequence:
        """Identify consumer imports bound to the declared upstream facets.

        Returns:
            Imported facet names in their native source traversal order.

        """
        view = run.model.source_project
        declared = cls._lazy_init_declared_letters(run, upstream)
        imported: list[str] = []
        for child in view.source_children(context.pkg_dir):
            if (
                child.suffix != c.Infra.EXT_PYTHON
                or child.name == c.Infra.INIT_PY
                or not view.source_query(child, "isfile")
            ):
                continue
            module = FlextInfraUtilitiesPythonModel.python_model_module_at(
                run.model, child, f"{context.current_pkg}.{child.stem}"
            )
            for name, target in FlextInfraUtilitiesPythonModel.python_model_imports(
                module
            ).items():
                provider, _, attribute = target.rpartition(".")
                if (
                    provider in {upstream, context.current_pkg}
                    and name == attribute
                    and name in declared
                ):
                    imported.append(name)
        return imported

    @staticmethod
    def _lazy_init_facet_binding(
        run: m.Infra.LazyInitRun, target: t.StrPair
    ) -> p.Infra.RopePyName:
        """Resolve the effective publication route through the run's native engine.

        Returns:
            The original class binding, never an inferred string identity.

        Raises:
            ValueError: If the planned publication is absent, incomplete or cyclic.

        """
        seen: set[t.StrPair] = set()
        while target not in seen:
            seen.add(target)
            module, attribute = target
            package_dir = run.index.package_dir_by_name.get(module)
            plan = run.plans.get(package_dir) if package_dir is not None else None
            if plan is None:
                break
            if (
                plan.action
                not in {
                    c.Infra.LazyInitAction.WRITE,
                    c.Infra.LazyInitAction.RETAIN,
                }
                or attribute not in plan.exports
            ):
                msg = f"lazy-init facet route is not published by its plan: {target}"
                raise ValueError(msg)
            route = plan.lazy_map.get(attribute) or plan.eager_dunders.get(attribute)
            if route is None:
                msg = f"lazy-init published facet has no planned route: {target}"
                raise ValueError(msg)
            if route == target and plan.ownership == "authored":
                break
            target = route
        else:
            msg = f"lazy-init cyclic facet publication: {target}"
            raise ValueError(msg)
        reference = m.Infra.SourceClassReference(
            target=target[0],
            attributes=(target[1],),
            qualified_base=f"{target[0]}.{target[1]}",
        )
        binding = FlextInfraUtilitiesRopeRuntime.qualified_name(
            run.model.source_project,
            ".".join(reference.attributes),
            module_name=reference.target,
        )
        FlextInfraUtilitiesRopeRuntime.require_class_object(
            binding.get_object(), reference.qualified_base
        )
        return binding

    @classmethod
    def _lazy_init_facade_chain(
        cls, run: m.Infra.LazyInitRun, packages: t.StrSequence, *, within: Path | None
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
            package_dir = run.index.package_dir_by_name.get(package)
            if package_dir is None:
                continue
            entry = run.index.packages_by_dir.get(str(package_dir))
            if within is None or (entry is not None and entry.project_root == within):
                queue.extend(cls.lazy_init_parent_packages(run, package_dir))
        return tuple(ordered)

    @classmethod
    def lazy_init_parent_packages(
        cls, run: m.Infra.LazyInitRun, pkg_dir: Path
    ) -> t.StrSequence:
        """Return the facade parents declared by ``constants.py`` class bases.

        Returns:
            The parent package names, nearest first.

        """
        cached = run.parents.get(pkg_dir)
        if cached is None:
            entry = run.index.packages_by_dir.get(str(pkg_dir))
            constants = pkg_dir / c.Infra.CONSTANTS_PY
            cached = (
                cls._lazy_init_constants_parents(
                    run,
                    constants,
                    entry.package_name if entry is not None else "",
                    set(),
                )
                if run.model.source_project.source_query(constants, "isfile")
                else ()
            )
            run.parents[pkg_dir] = cached
        return cached

    @classmethod
    def _lazy_init_constants_parents(
        cls, run: m.Infra.LazyInitRun, path: Path, current: str, seen: set[Path]
    ) -> t.StrSequence:
        """Follow ``*Constants`` class bases, recursing into same-package owners.

        Returns:
            The declared parent packages in declaration order.

        Raises:
            ValueError: If a declared base resolves to no package.

        """
        python = FlextInfraUtilitiesPythonModel
        seen.add(path)
        entry = run.index.modules_by_path.get(str(path))
        module = python.python_model_module_at(
            run.model, path, entry.module_name if entry else current
        )
        imports = python.python_model_imports(module)
        targets = tuple(
            f"{target}.{tail}" if tail else target
            for name, bases in python.python_model_class_bases(module).items()
            if c.Infra.LAZY_INIT_CONSTANTS_MARKER in name
            for base in bases
            for head, _, tail in (base.partition("."),)
            if (target := imports.get(head))
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
                    if ".".join(parts[:size]) in run.index.package_dir_by_name
                ),
                "",
            ) or (
                parts[0]
                if python.python_model_package_dir(parts[0]) is not None
                else ""
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
            owner = run.model.module_files.get(head if last[:1].isupper() else target)
            if owner is not None and owner not in seen:
                found.extend(
                    cls._lazy_init_constants_parents(run, owner, current, seen)
                )
        return tuple(dict.fromkeys(name for name in found if name and name != current))

    @staticmethod
    def _lazy_init_package_dir(
        run: m.Infra.LazyInitRun, package: str
    ) -> t.Pair[Path | None, bool]:
        """Return a package's directory and whether this run indexes it.

        Returns:
            The indexed or installed directory and the indexed flag.

        """
        indexed = run.index.package_dir_by_name.get(package)
        if indexed is not None:
            return indexed, True
        return FlextInfraUtilitiesPythonModel.python_model_package_dir(package), False

    @classmethod
    def _lazy_init_declared_letters(
        cls, run: m.Infra.LazyInitRun, package: str
    ) -> frozenset[str]:
        """Return the facade letters a package's own modules declare.

        An indexed package's generated initializer is this run's output and
        never a declaration owner; an installed package's initializer is.

        Returns:
            The declared letters.

        """
        python = FlextInfraUtilitiesPythonModel
        cached = run.declared.get(package)
        if cached is None:
            package_dir, indexed = cls._lazy_init_package_dir(run, package)
            view = run.model.source_project
            cached = frozenset(
                letter
                for child in (
                    view.source_children(package_dir) if package_dir is not None else ()
                )
                if child.suffix == c.Infra.EXT_PYTHON
                and not (indexed and child.name == c.Infra.INIT_PY)
                and view.source_query(child, "isfile")
                for letter in python.python_model_letters(
                    python.python_model_module_at(
                        run.model,
                        child,
                        package
                        if child.name == c.Infra.INIT_PY
                        else f"{package}.{child.stem}",
                    )
                )
            )
            run.declared[package] = cached
        return cached

    @classmethod
    def _lazy_init_package_names(
        cls, run: m.Infra.LazyInitRun, package: str
    ) -> frozenset[str]:
        """Return a parent's effective published names, never candidate declarations.

        Returns:
            The effectively published names of one parent.

        Raises:
            ValueError: If an installed parent is a module, not a package.

        """
        python = FlextInfraUtilitiesPythonModel
        package_dir, indexed = cls._lazy_init_package_dir(run, package)
        if package_dir is None:
            msg = (
                f"lazy-init facade parent '{package}' resolves to a module,"
                " not a package, in the active environment"
            )
            raise ValueError(msg)
        plan = run.plans.get(package_dir)
        if plan is not None:
            return (
                frozenset(plan.exports)
                if plan.action
                in {c.Infra.LazyInitAction.WRITE, c.Infra.LazyInitAction.RETAIN}
                else frozenset()
            )
        init_path = package_dir / c.Infra.INIT_PY
        text = cls.lazy_init_text(run, init_path)
        names: t.StrSequence = ()
        generated = text is not None and text.startswith(c.Infra.AUTOGEN_HEADER)
        if text is not None and not (
            indexed
            and generated
            and FlextInfraUtilitiesBase.first_merge_conflict_marker(text)
        ):
            module = python.python_model_module_at(run.model, init_path, package)
            declared = python.python_model_exports(module)
            names = (
                python.python_model_implicit_exports(module)
                if declared is None and indexed and not generated
                else declared or ()
            )
        return frozenset(names)


__all__: list[str] = ["FlextInfraUtilitiesLazyInitLetters"]
