"""Derived enforcement catalog owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities._codemod.codemod_rules import (
    FlextInfraUtilitiesCodemodRules,
)
from flext_infra._utilities.native_tooling import FlextInfraUtilitiesNativeTooling


class FlextInfraUtilitiesEnforcementCatalog:
    """Derive the enforcement catalog from the owners that claim each law."""

    @staticmethod
    def accessor_prefix_constraints(
        _project: Path,
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Project the accessor-policy prefixes into a native ast-grep util.

        Tooling ``accessor-policy.forbidden-prefixes`` is the one owner of the
        accessor prefixes; ``ban-accessor-method-name`` matches this util
        instead of repeating them.

        Returns:
            The ``accessor-forbidden-prefix`` util keyed by its id.

        """
        prefixes = config.Infra.tooling.accessor_policy.forbidden_prefixes
        alternation = "|".join(re.escape(prefix) for prefix in prefixes)
        return {
            c.Infra.ACCESSOR_PREFIX_UTIL_ID: {"regex": f"^(?:{alternation})"},
        }

    @staticmethod
    def enforcement_catalog(
        codemod_config: Path | None = None,
    ) -> p.Result[m.Infra.EnforcementCatalog]:
        """Derive the catalog from every owner's claims, failing on the first defect.

        Claims come from ast-grep rule ``metadata.enforce``, the Ruff rules'
        ``tools.ruff.lint.enforce``, the smells checks' ``smells.enforce``, the
        gate registry's ``GATE_ENFORCES`` and codegen template ``enforce``. An
        id is valid when at least one active owner claims it. A claim the same
        owner repeats is a duplicate; an id claimed only by disabled or
        unregistered owners is an orphan.

        Args:
            codemod_config: ast-grep provider config whose rule documents are
                read; the packaged provider config when omitted.

        Returns:
            The derived catalog, or the first duplicate or orphan claim.

        """
        result = r[m.Infra.EnforcementCatalog]
        package_root = type(config).ssot_config_dir().parent
        rules = FlextInfraUtilitiesCodemodRules.codemod_catalog_rules(
            c.Infra.PACKAGE_IMPORT_NAME,
            package_root / c.Infra.CODEMOD_CONFIG_RELPATH
            if codemod_config is None
            else codemod_config,
        )
        if rules.failure:
            return result.from_failure(rules)
        claims = FlextInfraUtilitiesEnforcementCatalog._claims(rules.value)
        defect = FlextInfraUtilitiesEnforcementCatalog._defect(claims)
        if defect is not None:
            return result.fail(defect)
        if not claims:
            return result.fail("no owner claims any enforcement law")
        return result.ok(m.Infra.EnforcementCatalog(claims=claims))

    @staticmethod
    def _claims(
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> t.VariadicTuple[m.Infra.EnforcementClaim]:
        """Collect every owner's claims in declaration order.

        Returns:
            One claim per law id an owner declares.

        """
        tooling = config.Infra.tooling
        enabled_ruff = FlextInfraUtilitiesEnforcementCatalog._enabled_ruff_rules()
        smells_active = c.Infra.SMELLS in c.Infra.ALLOWED_GATES
        engine = c.Infra.EnforcementEngine
        return tuple(
            m.Infra.EnforcementClaim(
                id=law, engine=kind, owner=owner, code=code, active=active
            )
            for kind, owner, code, active, laws in (
                *(
                    (engine.AST_GREP, rule.id, None, not rule.disabled, rule.enforce)
                    for rule in rules
                ),
                *(
                    (engine.RUFF, rule, None, rule in enabled_ruff, laws)
                    for rule, laws in tooling.tools.ruff.lint.enforce.items()
                ),
                *(
                    (
                        engine.GATE,
                        c.Infra.SMELLS,
                        f"{c.Infra.SMELLS_RULE_PREFIX}{check}",
                        smells_active and check in tooling.smells.fix_text,
                        laws,
                    )
                    for check, laws in tooling.smells.enforce.items()
                ),
                *(
                    (engine.GATE, gate, None, gate in c.Infra.ALLOWED_GATES, laws)
                    for gate, laws in c.Infra.GATE_ENFORCES.items()
                ),
                *(
                    (engine.CODEGEN, entry.destination, None, True, entry.enforce)
                    for entry in config.Infra.codegen.templates.entries
                ),
            )
            for law in laws
        )

    @staticmethod
    def _defect(claims: t.SequenceOf[m.Infra.EnforcementClaim]) -> str | None:
        """Describe the first duplicate or orphan claim.

        Returns:
            The defect, or ``None`` when every claim is unique and owned.

        """
        repeated = Counter(
            (claim.id, claim.engine, claim.owner, claim.code) for claim in claims
        )
        duplicate = next((key for key, count in repeated.items() if count > 1), None)
        if duplicate is not None:
            law, kind, owner, code = duplicate
            return f"{law}: {kind} {owner}{f' {code}' if code else ''} claims it twice"
        active_ids = frozenset(claim.id for claim in claims if claim.active)
        orphan = next(
            (claim for claim in claims if claim.id not in active_ids),
            None,
        )
        if orphan is not None:
            return (
                f"{orphan.id}: orphan claim; its only owner {orphan.engine} "
                f"{orphan.owner} is disabled or unregistered"
            )
        return None

    @staticmethod
    def _enabled_ruff_rules() -> frozenset[str]:
        """Return the claiming Ruff rules the tooling selection enables.

        A rule is enabled when the selection names it or selects ``ALL`` and
        neither the native ignore list, the operator-ruled disabled rules nor
        the delegated rule owners remove it from the lint gate.

        Returns:
            The enabled Ruff rule names among the claiming rules.

        """
        tooling = config.Infra.tooling
        lint = tooling.tools.ruff.lint
        selected = frozenset((
            *FlextInfraUtilitiesNativeTooling.native_tool_strings(
                tooling, "ruff.lint", "select"
            ),
            *FlextInfraUtilitiesNativeTooling.native_tool_strings(
                tooling, "ruff.lint", "extend-select"
            ),
        ))
        excluded = frozenset((
            *FlextInfraUtilitiesNativeTooling.native_tool_strings(
                tooling, "ruff.lint", "ignore"
            ),
            *lint.ruling_disabled_rules,
            *lint.rule_owners,
        ))
        return frozenset(
            rule
            for rule in lint.enforce
            if rule not in excluded
            and (c.Infra.RUFF_SELECT_ALL in selected or rule in selected)
        )


__all__: list[str] = ["FlextInfraUtilitiesEnforcementCatalog"]
