"""Export-collision resolution for the lazy-init planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerCollisionMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _collision_count: int

        def _module_file(self, module_path: str) -> Path | None: ...

    def _target_score(self, name: str, target: t.StrPair) -> int:
        """Score a candidate export target to break collision ties.

        Returns:
            The resulting ``int``.

        """
        module_path, attr = target
        module_file = self._module_file(module_path)
        if module_file is None:
            return 0
        score = self._policy_score(name, module_file)
        if attr == name:
            score += 3
        if name in c.Infra.ALIAS_NAMES and "." not in module_path:
            score -= 80
        final_score: int = score
        return final_score

    def _policy_score(self, name: str, module_file: Path) -> int:
        """Score a target by its module's governed publication policy.

        Returns:
            The resulting ``int``.

        """
        score = 0
        policy = u.Infra.publication_policy(
            module_file,
            rope_project=self.rope_workspace.rope_project,
        )
        if policy.expected_alias == name:
            score += 100
        elif policy.expected_family and name.endswith(policy.expected_family):
            # A governed facade owns its declared family class.
            score += 25
        elif policy.expected_alias:
            # Governed root facades should primarily own their canonical alias.
            score -= 40
        elif policy.expected_family:
            # Penalize cross-family leakage from governed facade files.
            score -= 20
        if policy.export_symbols:
            score += 20
        if policy.enforce_contract:
            score += 10
        declared_exports = self.rope_workspace.exports(
            module_file,
            export_options=m.Infra.ExportOptions(
                allow_assignments=True,
                allow_functions=True,
                require_explicit_all=True,
            ),
        )
        if name in declared_exports:
            score += 15
        return score

    def _add(self, index: t.MutableLazyAliasMap, name: str, target: t.StrPair) -> None:
        """Insert a name/target pair and record ambiguous ownership."""
        existing = index.get(name)
        if existing is None or existing == target:
            index[name] = target
            return
        if self._is_intentional_reexport(existing, target):
            elected = self._published_reexport_target(
                existing,
                target,
                name=name,
            )
            if elected is not None:
                index[name] = elected
                return
        self._collision_count += 1
        u.Cli.error(
            f"export collision for {name!r}: {existing} vs {target}; "
            "no unique native publication owner",
        )

    def _published_reexport_target(
        self,
        a: t.StrPair,
        b: t.StrPair,
        *,
        name: str,
    ) -> t.StrPair | None:
        """Elect the published facade path of one re-export pair.

        Native introducing subclasses own their composed behavior. Reexports
        of the same declaration use their public facade and governed publication
        authority, then the native introducing module. Equal unrelated publication
        routes remain ambiguous; filename ordering never elects one.

        Returns:
            The authenticated owner, or None for equally authoritative routes.

        """
        a_file = self._module_file(a[0])
        b_file = self._module_file(b[0])
        a_binding = u.Infra.require_semantic_module(
            self.rope_workspace.rope_project.get_module(a[0])
        ).get_attribute(a[1])
        b_binding = u.Infra.require_semantic_module(
            self.rope_workspace.rope_project.get_module(b[0])
        ).get_attribute(b[1])
        a_object, b_object = a_binding.get_object(), b_binding.get_object()
        if a_object != b_object and a_object in u.Infra.class_ancestry(b_object):
            return b
        if a_object != b_object and b_object in u.Infra.class_ancestry(a_object):
            return a
        if a_file is not None and a_file.name == c.Infra.INIT_PY:
            return b if b_file is not None and b_file.name != c.Infra.INIT_PY else None
        if b_file is not None and b_file.name == c.Infra.INIT_PY:
            return a
        ranked = self._rank_reexport_target(a, b, name=name)
        if ranked is not None:
            return ranked
        return self._introducing_target((a, a_binding, a_file), (b, b_binding, b_file))

    def _rank_reexport_target(
        self, a: t.StrPair, b: t.StrPair, *, name: str
    ) -> t.StrPair | None:
        """Compare publication routes without inventing a filename tie-breaker.

        Returns:
            The stronger route, or None for equally authoritative routes.

        """
        a_parts = self._module_parts(a[0])
        b_parts = self._module_parts(b[0])
        a_private = len(self._private_segments(a_parts))
        b_private = len(self._private_segments(b_parts))
        if a_private != b_private:
            return a if a_private < b_private else b
        if len(a_parts) != len(b_parts):
            return a if len(a_parts) < len(b_parts) else b
        a_score, b_score = self._target_score(name, a), self._target_score(name, b)
        if a_score != b_score:
            return a if a_score > b_score else b
        return None

    @staticmethod
    def _introducing_target(
        a: t.Triple[t.StrPair, p.Infra.RopePyName, Path | None],
        b: t.Triple[t.StrPair, p.Infra.RopePyName, Path | None],
    ) -> t.StrPair | None:
        """Elect a sole native introducing declaration.

        Returns:
            The sole introducing target, or None when ambiguous.

        """
        introducing = [
            target
            for target, binding, module_file in (a, b)
            if FlextInfraCodegenLazyInitPlannerCollisionMixin._introduces_binding(
                binding, module_file
            )
        ]
        return introducing[0] if len(introducing) == 1 else None

    @staticmethod
    def _introduces_binding(
        binding: p.Infra.RopePyName, module_file: Path | None
    ) -> bool:
        """Check whether publication comes from the native declaration module.

        Returns:
            Whether the target module introduces the binding.

        """
        module, _line = u.Infra.definition_location(binding)
        resource = module.get_resource() if u.Infra.source_module(module) else None
        return (
            resource is not None
            and module_file is not None
            and resource.real_path == str(module_file)
        )

    def _is_intentional_reexport(self, a: t.StrPair, b: t.StrPair) -> bool:
        """Authenticate reexports and introducing subclasses in the native graph.

        Returns:
            Whether the targets share a declaration or composed class lineage.

        """
        if not a[1] or not b[1]:
            return False
        a_module = u.Infra.require_semantic_module(
            self.rope_workspace.rope_project.get_module(a[0])
        )
        b_module = u.Infra.require_semantic_module(
            self.rope_workspace.rope_project.get_module(b[0])
        )
        if (
            a[1] not in a_module.get_attributes()
            or b[1] not in b_module.get_attributes()
        ):
            return False
        a_binding = a_module.get_attribute(a[1])
        b_binding = b_module.get_attribute(b[1])
        if u.Infra.same_name(a_binding, b_binding):
            return True
        a_object, b_object = a_binding.get_object(), b_binding.get_object()
        return a_object != b_object and (
            a_object in u.Infra.class_ancestry(b_object)
            or b_object in u.Infra.class_ancestry(a_object)
        )

    @staticmethod
    def _module_parts(module_path: str) -> t.VariadicTuple[str]:
        """Return normalized dotted module path parts.

        Returns:
            Normalized dotted module path parts.

        """
        return tuple(part for part in module_path.split(".") if part)

    @classmethod
    def _private_segments(cls, parts: t.StrSequence) -> frozenset[t.Pair[int, str]]:
        """Return private implementation segments with their path positions.

        Returns:
            Private implementation segments with their path positions.

        """
        return frozenset(
            (index, part)
            for index, part in enumerate(parts[1:], start=1)
            if part.startswith("_")
            and not (part.startswith("__") and part.endswith("__"))
        )

    @staticmethod
    def _publish(name: str, *, allow_main: bool) -> bool:
        """Return whether a name should be published in the lazy __init__.

        Returns:
            Whether a name should be published in the lazy __init__.

        """
        return (
            not name.startswith("_")
            and name not in {c.Infra.DUNDER_INIT, "pytestmark"}
            and (name != "main" or allow_main)
        )


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerCollisionMixin"]
