"""MRO resolution helpers and migration rewrite orchestration."""

from __future__ import annotations

import inspect
from collections.abc import Mapping, MutableSequence, Sequence

from flext_infra import (
    c,
    m,
    t,
)


class FlextInfraRefactorMROResolver:
    """Resolve MRO inheritance chains and detect loose classes needing absorption."""

    CONSTANT_PATTERN: t.Infra.RegexPattern = c.Infra.CONSTANT_NAME_RE

    @classmethod
    def resolve(
        cls,
        *,
        family_classes: Mapping[t.Infra.FacadeFamily, type],
        expected_base_chains: Mapping[
            t.Infra.FacadeFamily,
            Sequence[t.Infra.ExpectedBase],
        ],
    ) -> t.Infra.VariadicTuple[m.Infra.FamilyMROResolution]:
        """Resolve expected and effective MRO data for all facade families."""
        resolutions: MutableSequence[m.Infra.FamilyMROResolution] = []
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
                ),
            )
        return tuple(resolutions)

    @classmethod
    def _resolve_family(
        cls,
        *,
        family: t.Infra.FacadeFamily,
        facade_class: type,
        expected_chain: Sequence[t.Infra.ExpectedBase],
    ) -> m.Infra.FamilyMROResolution:
        expected_names = cls._normalize_expected_chain(expected_chain=expected_chain)
        cls._validate_base_policy(
            family=family,
            facade_class=facade_class,
            expected_names=expected_names,
        )
        resolved_mro = tuple(entry.__name__ for entry in inspect.getmro(facade_class))
        accessible_namespaces = cls._collect_accessible_namespaces(
            family=family,
            facade_class=facade_class,
        )
        cls._validate_expected_accessibility(
            family=family,
            expected_names=expected_names,
            accessible_namespaces=accessible_namespaces,
        )
        return m.Infra.FamilyMROResolution(
            family=family,
            expected_bases=expected_names,
            resolved_mro=resolved_mro,
            accessible_namespaces=accessible_namespaces,
        )

    @classmethod
    def _normalize_expected_chain(
        cls,
        *,
        expected_chain: Sequence[t.Infra.ExpectedBase],
    ) -> t.Infra.VariadicTuple[str]:
        expected_names: t.StrSequence = [
            base if isinstance(base, str) else base.__name__ for base in expected_chain
        ]
        return tuple(expected_names)

    @classmethod
    def _validate_base_policy(
        cls,
        *,
        family: t.Infra.FacadeFamily,
        facade_class: type,
        expected_names: t.Infra.VariadicTuple[str],
    ) -> None:
        direct_base_names = tuple(base.__name__ for base in facade_class.__bases__)
        if len(direct_base_names) < len(expected_names):
            msg = f"family={family} has fewer direct bases than expected: expected={expected_names!r} direct={direct_base_names!r}"
            raise ValueError(msg)
        if direct_base_names[: len(expected_names)] != expected_names:
            msg = f"family={family} direct base order violates policy: expected={expected_names!r} direct={direct_base_names!r}"
            raise ValueError(msg)
        mro_types = inspect.getmro(facade_class)
        mro_names = tuple(entry.__name__ for entry in mro_types)
        mro_index = {name: index for index, name in enumerate(mro_names)}
        missing = tuple(name for name in expected_names if name not in mro_index)
        if missing:
            msg = f"family={family} missing expected bases in MRO: missing={missing!r} mro={mro_names!r}"
            raise ValueError(msg)
        previous_index = -1
        for base_name in expected_names:
            current_index = mro_index[base_name]
            if current_index <= previous_index:
                msg = f"family={family} MRO order is not C3-coherent for expected chain: expected={expected_names!r} mro={mro_names!r}"
                raise ValueError(msg)
            previous_index = current_index

    @classmethod
    def _validate_expected_accessibility(
        cls,
        *,
        family: t.Infra.FacadeFamily,
        expected_names: t.Infra.VariadicTuple[str],
        accessible_namespaces: t.Infra.VariadicTuple[str],
    ) -> None:
        missing_namespaces: MutableSequence[str] = []
        for base_name in expected_names:
            namespace = cls._namespace_from_class_name(
                class_name=base_name,
                family=family,
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
        cls,
        *,
        family: t.Infra.FacadeFamily,
        facade_class: type,
    ) -> t.Infra.VariadicTuple[str]:
        namespace_order: MutableSequence[str] = []
        for current in inspect.getmro(facade_class):
            if current.__name__ == "NormalizedValue":
                continue
            class_namespace = cls._namespace_from_class_name(
                class_name=current.__name__,
                family=family,
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
        cls,
        *,
        class_name: str,
        family: t.Infra.FacadeFamily,
    ) -> str | None:
        suffix = c.Infra.FAMILY_SUFFIXES[family]
        if not class_name.endswith(suffix):
            return None
        root = class_name[: -len(suffix)]
        root = root.removeprefix("Flext")
        if not root:
            return None
        return root

    @staticmethod
    def _append_unique(namespaces: MutableSequence[str], candidate: str) -> None:
        if candidate not in namespaces:
            namespaces.append(candidate)


__all__: list[str] = [
    "FlextInfraRefactorMROResolver",
]
