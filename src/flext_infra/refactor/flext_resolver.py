"""FLEXT resolution helpers and migration rewrite orchestration."""

from __future__ import annotations

from flext_infra import c, m, t


class FlextInfraRefactorFLEXTResolver:
    """Resolve FLEXT inheritance chains and detect loose classes needing absorption."""

    @classmethod
    def resolve(
        cls,
        *,
        family_classes: t.MappingKV[c.Infra.FacadeFamily, type],
        expected_base_chains: t.MappingKV[
            c.Infra.FacadeFamily, t.SequenceOf[t.Infra.ExpectedBase]
        ],
    ) -> t.VariadicTuple[m.Infra.FamilyFLEXTResolution]:
        """Resolve expected and effective FLEXT data for all facade families."""
        resolutions: t.MutableSequenceOf[m.Infra.FamilyFLEXTResolution] = []
        for family in (
            c.Infra.FacadeFamily.C,
            c.Infra.FacadeFamily.T,
            c.Infra.FacadeFamily.P,
            c.Infra.FacadeFamily.M,
            c.Infra.FacadeFamily.U,
        ):
            facade_class = family_classes[family]
            expected_chain = expected_base_chains[family]
            resolutions.append(
                cls._resolve_family(
                    family=family,
                    facade_class=facade_class,
                    expected_chain=expected_chain,
                )
            )
        return tuple(resolutions)

    @classmethod
    def _resolve_family(
        cls,
        *,
        family: c.Infra.FacadeFamily,
        facade_class: type,
        expected_chain: t.SequenceOf[t.Infra.ExpectedBase],
    ) -> m.Infra.FamilyFLEXTResolution:
        """Resolve family."""
        expected_names = cls._normalize_expected_chain(expected_chain=expected_chain)
        cls._validate_base_policy(
            family=family, facade_class=facade_class, expected_names=expected_names
        )
        resolved_flext = tuple(
            entry.__name__ for entry in cls._inheritance_chain(facade_class)
        )
        accessible_namespaces = cls._collect_accessible_namespaces(
            family=family, facade_class=facade_class
        )
        cls._validate_expected_accessibility(
            family=family,
            expected_names=expected_names,
            accessible_namespaces=accessible_namespaces,
        )
        return m.Infra.FamilyFLEXTResolution(
            family=family,
            expected_bases=expected_names,
            resolved_flext=resolved_flext,
            accessible_namespaces=accessible_namespaces,
        )

    @classmethod
    def _normalize_expected_chain(
        cls, *, expected_chain: t.SequenceOf[t.Infra.ExpectedBase]
    ) -> t.VariadicTuple[str]:
        """Normalize expected chain."""
        expected_names: t.StrSequence = [
            base if isinstance(base, str) else base.__name__ for base in expected_chain
        ]
        return tuple(expected_names)

    @classmethod
    def _validate_base_policy(
        cls,
        *,
        family: c.Infra.FacadeFamily,
        facade_class: type,
        expected_names: t.VariadicTuple[str],
    ) -> None:
        """Validate base policy."""
        direct_base_names = tuple(base.__name__ for base in facade_class.__bases__)
        if len(direct_base_names) < len(expected_names):
            msg = f"family={family} has fewer direct bases than expected: expected={expected_names!r} direct={direct_base_names!r}"
            raise ValueError(msg)
        if direct_base_names[: len(expected_names)] != expected_names:
            msg = f"family={family} direct base order violates policy: expected={expected_names!r} direct={direct_base_names!r}"
            raise ValueError(msg)
        flext_types = cls._inheritance_chain(facade_class)
        flext_names = tuple(entry.__name__ for entry in flext_types)
        flext_index = {name: index for index, name in enumerate(flext_names)}
        missing = tuple(name for name in expected_names if name not in flext_index)
        if missing:
            msg = f"family={family} missing expected bases in FLEXT: missing={missing!r} flext={flext_names!r}"
            raise ValueError(msg)
        previous_index = -1
        for base_name in expected_names:
            current_index = flext_index[base_name]
            if current_index <= previous_index:
                msg = f"family={family} FLEXT order is not C3-coherent for expected chain: expected={expected_names!r} flext={flext_names!r}"
                raise ValueError(msg)
            previous_index = current_index

    @classmethod
    def _inheritance_chain(cls, facade_class: type) -> t.VariadicTuple[type]:
        """Return the deterministic, de-duplicated class inheritance chain."""
        ordered: list[type] = []

        def _visit(current: type) -> None:
            if current in ordered:
                return
            ordered.append(current)
            for base in current.__bases__:
                _visit(base)

        _visit(facade_class)
        return tuple(ordered)

    @classmethod
    def _validate_expected_accessibility(
        cls,
        *,
        family: c.Infra.FacadeFamily,
        expected_names: t.VariadicTuple[str],
        accessible_namespaces: t.VariadicTuple[str],
    ) -> None:
        """Validate expected accessibility."""
        missing_namespaces: t.MutableSequenceOf[str] = []
        for base_name in expected_names:
            namespace = cls._namespace_from_class_name(
                class_name=base_name, family=family
            )
            if namespace is None:
                continue
            if namespace in accessible_namespaces:
                continue
            missing_namespaces.append(namespace)
        if missing_namespaces:
            msg = f"family={family} expected namespaces are not accessible: missing={tuple(missing_namespaces)!r} accessible={accessible_namespaces!r}"
            raise ValueError(msg)

    @classmethod
    def _collect_accessible_namespaces(
        cls, *, family: c.Infra.FacadeFamily, facade_class: type
    ) -> t.VariadicTuple[str]:
        """Collect accessible namespaces."""
        namespace_order: t.MutableSequenceOf[str] = []
        for current in cls._inheritance_chain(facade_class):
            if current.__name__ == "NormalizedValue":
                continue
            class_namespace = cls._namespace_from_class_name(
                class_name=current.__name__, family=family
            )
            if class_namespace is not None:
                cls._append_unique(namespace_order, class_namespace)
            for member_name, member in vars(current).items():
                if member_name.startswith("_"):
                    continue
                if not isinstance(member, type):
                    continue
                cls._append_unique(namespace_order, member_name)
        return tuple(namespace_order)

    @classmethod
    def _namespace_from_class_name(
        cls, *, class_name: str, family: c.Infra.FacadeFamily
    ) -> str | None:
        """Namespace from class name."""
        suffix = c.Infra.FAMILY_SUFFIXES[family]
        if not class_name.endswith(suffix):
            return None
        root = class_name[: -len(suffix)]
        root = root.removeprefix("Flext")
        if not root:
            return None
        return root

    @staticmethod
    def _append_unique(namespaces: t.MutableSequenceOf[str], candidate: str) -> None:
        """Append unique."""
        if candidate not in namespaces:
            namespaces.append(candidate)


__all__: list[str] = ["FlextInfraRefactorFLEXTResolver"]
