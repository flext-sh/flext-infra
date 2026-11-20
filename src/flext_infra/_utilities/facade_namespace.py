"""Facade own parts compose the package's nested domain namespace.

ADR-028 Decision 10: a facade composed on an upstream FLEXT family inherits
only that family; the package's own parts compose one nested class named by
the package (``class FlextDbOracleTypes(FlextCliTypes): class DbOracle(...)``),
never extra bases of the outer class. Rope's class layout and base bindings
own every span and origin; edits replace only part spans, so comments and
layout survive.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, p
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisImportState,
)


class FlextInfraUtilitiesFacadeNamespace:
    """Move a facade's own-package bases into its nested domain namespace."""

    @staticmethod
    def facade_domain_name(path: Path) -> str | None:
        """Name the domain namespace a package facade nests its own parts in.

        Returns:
            ``DbOracle`` for ``flext_db_oracle``, or ``None`` outside a
            ``flext_<domain>`` package (tests, examples, the root package).

        """
        package = path.parent.name
        if not package.startswith(c.Infra.PKG_PREFIX_UNDERSCORE):
            return None
        return FlextInfraUtilitiesCodegenNamespace.domain_namespace(
            u.derive_class_stem(package)
        )

    @classmethod
    def facade_nested_domain_source(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        *,
        declares_parts: bool,
        indent_step: int,
    ) -> str | None:
        """Rewrite a facade so its own parts compose the nested domain class.

        Root own parts move into the nested class (created after the owner
        body when absent, appended after its last base when present). A
        facade whose family declares parts but which has no nested class
        gains an empty one, so the planner composes the family there in the
        same invocation. A part that declares the domain name contributes
        ``Part.<Domain>``.

        Returns:
            The rewritten source, or ``None`` when the facade has no upstream
            family, already composes only through its nested namespace, or
            inherits the namespace (a lazy or upstream holder). A domain
            name bound to a non-class raises ``TypeError`` from the helper
            that finds it.

        """
        domain = cls.facade_domain_name(path)
        resource = FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
        published = FlextInfraUtilitiesRopeAnalysisImportState.published_facade_owner(
            project, resource
        )
        if domain is None or published is None:
            return None
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            project.get_pymodule(resource)
        )
        attributes = module.get_attributes()
        if published[1] not in attributes:
            return None
        owner = attributes[published[1]].get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(owner):
            return None
        nested = domain in owner.get_scope().get_defined_names()
        if not nested and not cls._facade_own_holder(owner, domain, path.parent.name):
            return None
        index = module.get_source_binding_index()
        layout = index.class_layout(owner.get_scope())
        parts, upstream = cls._facade_own_part_bases(layout, path.parent.name)
        if not upstream or (not parts and (nested or not declares_parts)):
            return None
        source = module.source_code
        names = cls._facade_part_expressions(source, parts, domain)
        edits = [
            *cls._facade_span_removals(layout, parts),
            cls._facade_namespace_base_insertion(index, owner, domain, names)
            if nested
            else (
                layout.body[1],
                layout.body[1],
                cls._facade_namespace_class_text(
                    domain,
                    names,
                    layout.region[0]
                    - source.rfind("\n", 0, layout.region[0])
                    - 1
                    + indent_step,
                ),
            ),
        ]
        for start, end, text in sorted(edits, reverse=True):
            source = source[:start] + text + source[end:]
        return source

    @staticmethod
    def _facade_own_holder(
        owner: p.Infra.RopeSourceClass, domain: str, package: str
    ) -> bool:
        """Whether an inherited domain binding still admits the rewrite.

        Nothing inherited admits it; an own-package class admits it (a
        namespace-holder part, composed as ``Part.<Domain>``). Any other
        binding (a lazy descriptor guarding an import cycle, an upstream
        namespace) owns the domain and blocks the rewrite.

        Returns:
            True when the facade may gain or extend its nested namespace.

        """
        if domain not in owner.get_attributes():
            return True
        inherited = owner.get_attributes()[domain].get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(inherited):
            return False
        origin = inherited.get_module()
        return origin is not None and origin.get_name().partition(".")[0] == package

    @staticmethod
    def _facade_own_part_bases(
        layout: p.Infra.RopeSourceClassLayout, package: str
    ) -> tuple[tuple[tuple[tuple[int, int], p.Infra.RopeSourceClass], ...], bool]:
        """Split a facade's bound bases into own parts and an upstream family.

        Returns:
            The spans and classes declared inside ``package``, and whether
            another FLEXT package supplies a base.

        """
        parts: list[tuple[tuple[int, int], p.Infra.RopeSourceClass]] = []
        upstream = False
        for span, binding in layout.base_bindings:
            base = None if binding is None else binding.get_object()
            origin = None if base is None else base.get_module()
            root = None if origin is None else origin.get_name().partition(".")[0]
            if root == package and FlextInfraUtilitiesRopeRuntimeTypes.py_class(base):
                parts.append((span, base))
            else:
                upstream = upstream or (root or "").startswith(
                    c.Infra.PKG_PREFIX_UNDERSCORE
                )
        return tuple(parts), upstream

    @staticmethod
    def _facade_part_expressions(
        source: str,
        parts: Sequence[tuple[tuple[int, int], p.Infra.RopeSourceClass]],
        domain: str,
    ) -> list[str]:
        """Name what each part contributes to the domain namespace.

        A pure holder part (its only member is the domain class) contributes
        ``Part.<Domain>``, so ``c.<Domain>.X`` keeps resolving. Any other
        part composes whole, including one declaring a real ``<Domain>``
        class beside other members (``flext-tap-ldap`` precedent:
        ``p.TapLdap.TapLdap``).

        Returns:
            One base expression per part.

        """
        return [
            f"{source[start:end]}.{domain}"
            if set(part.get_scope().get_defined_names()) == {domain}
            else source[start:end]
            for (start, end), part in parts
        ]

    @staticmethod
    def _facade_span_removals(
        layout: p.Infra.RopeSourceClassLayout,
        parts: Sequence[tuple[tuple[int, int], p.Infra.RopeSourceClass]],
    ) -> list[tuple[int, int, str]]:
        """Delete each part base and one adjacent separator, nothing else.

        Returns:
            One ``(start, end, "")`` edit per part span.

        """
        items = sorted((*layout.bases, *layout.keywords))
        removed = {span for span, _part in parts}
        edits: list[tuple[int, int, str]] = []
        for position, (start, end) in enumerate(items):
            if (start, end) not in removed:
                continue
            following = next(
                (item for item in items[position + 1 :] if item not in removed), None
            )
            if following is not None:
                edits.append((start, following[0], ""))
                continue
            previous = next(
                (item for item in reversed(items[:position]) if item not in removed),
                None,
            )
            edits.append((start if previous is None else previous[1], end, ""))
        return edits

    @staticmethod
    def _facade_namespace_class_text(
        domain: str, names: Sequence[str], column: int
    ) -> str:
        """Render the nested domain class composing ``names`` at ``column``.

        Returns:
            The class block appended after the owner body.

        """
        margin = " " * column
        bases = f"({', '.join(names)})" if names else ""
        return (
            f"\n\n{margin}class {domain}{bases}:\n"
            f'{margin}    """Domain namespace of the package parts."""\n'
        )

    @staticmethod
    def _facade_namespace_base_insertion(
        index: p.Infra.RopeSourceBindingIndex,
        owner: p.Infra.RopeSourceClass,
        domain: str,
        names: Sequence[str],
    ) -> tuple[int, int, str]:
        """Append the parts the existing nested namespace does not compose.

        Returns:
            An insertion edit after the nested class's last base, or after
            its name when it declares none.

        Raises:
            TypeError: If the domain name is bound to a non-class.

        """
        nested = owner.get_attributes()[domain].get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(nested):
            msg = (
                f"{owner.get_name()}.{domain} is bound to a non-class; the domain "
                "namespace must be a class composing the package parts"
            )
            raise TypeError(msg)
        inner = index.class_layout(nested.get_scope())
        source = nested.get_module().source_code
        present = {source[start:end] for start, end in inner.bases}
        missing = [name for name in names if name not in present]
        if not missing:
            return (inner.name_region[1], inner.name_region[1], "")
        if inner.bases:
            last = inner.bases[-1][1]
            return (last, last, "".join(f", {name}" for name in missing))
        if inner.arguments_region is not None:
            first = inner.arguments_region[0]
            return (first, first, ", ".join(missing))
        end = inner.name_region[1]
        return (end, end, f"({', '.join(missing)})")


__all__: list[str] = ["FlextInfraUtilitiesFacadeNamespace"]
