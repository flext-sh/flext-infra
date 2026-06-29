"""Export-collision resolution for the lazy-init planner."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerCollisionMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _collision_count: int

        def _module_file(self, module_path: str) -> Path | None: ...

    def _target_score(self, name: str, target: t.StrPair) -> int:
        """Score a candidate export target to break collision ties."""
        module_path, attr = target
        score = 0
        module_file = self._module_file(module_path)
        if module_file is None:
            return score
        convention = self.rope_workspace.convention(module_file)
        policy = convention.module_policy
        if policy.expected_alias == name:
            score += 100
        elif policy.expected_alias:
            # Governed root facades should primarily own their canonical alias.
            score -= 40
        if policy.expected_family and name.endswith(policy.expected_family):
            score += 25
        elif policy.expected_family and name != (policy.expected_alias or ""):
            # Penalize cross-family leakage from governed facade files.
            score -= 20
        if policy.export_symbols:
            score += 20
        if policy.enforce_contract:
            score += 10
        if module_file.name in self.lazy_init.root_namespace_files:
            score += 5
        preferred_stem_by_alias = {
            alias: file_name.removesuffix(".py")
            for file_name, alias in self.lazy_init.public_file_aliases.items()
        }
        preferred_stem = preferred_stem_by_alias.get(name, "")
        if preferred_stem and module_file.stem == preferred_stem:
            score += 15
        if attr == name:
            score += 3
        part_number = module_file.stem.rpartition("_part_")[2]
        if part_number.isdecimal():
            score += int(part_number)
        score -= module_path.count(".")
        final_score: int = score
        return final_score

    def _pick_preferred_target(
        self,
        name: str,
        existing: t.StrPair,
        target: t.StrPair,
    ) -> t.StrPair:
        """Return the higher-scored of two competing export targets."""
        existing_score = self._target_score(name, existing)
        target_score = self._target_score(name, target)
        if target_score > existing_score:
            return target
        if target_score < existing_score:
            return existing
        return min(existing, target)

    def _add(
        self,
        index: t.MutableLazyAliasMap,
        name: str,
        target: t.StrPair,
    ) -> None:
        """Insert a name/target pair, resolving collisions via policy scoring."""
        existing = index.get(name)
        if existing is None or existing == target:
            index[name] = target
            return
        if not isinstance(existing, tuple):
            index[name] = target
            return
        winner = self._pick_preferred_target(name, existing, target)
        if self._is_intentional_reexport(existing, target):
            index[name] = winner
            return
        self._collision_count += 1
        u.Cli.warning(
            f"export collision for {name!r}: {existing} vs {target}; "
            f"resolved by canonical policy scorer to {winner}",
        )
        index[name] = winner

    @staticmethod
    def _is_intentional_reexport(
        a: t.StrPair,
        b: t.StrPair,
    ) -> bool:
        """Return whether one module is a root-namespace stub re-exporting from the other."""
        for pub_mod, priv_mod in ((a[0], b[0]), (b[0], a[0])):
            pub_file = f"{pub_mod.rsplit('.', maxsplit=1)[-1]}.py"
            if not u.Infra.matches_root_namespace_file(pub_file):
                continue
            if "." in priv_mod and priv_mod.split(".")[-2].startswith("_"):
                return True
        return False

    @staticmethod
    def _publish(name: str, *, allow_main: bool) -> bool:
        """Return whether a name should be published in the lazy __init__."""
        return (
            not name.startswith("_")
            and name not in c.Infra.INFRA_ONLY_EXPORTS
            and name not in {c.Infra.DUNDER_INIT, "pytestmark"}
            and (name != "main" or allow_main)
        )
