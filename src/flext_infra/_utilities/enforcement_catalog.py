"""Static enforcement catalog owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesNativeTooling,
)


class FlextInfraUtilitiesEnforcementCatalog:
    """Load ``config/rules/catalog.yaml`` and prove every owner it names."""

    @staticmethod
    def enforcement_catalog(
        source: Path | None = None,
    ) -> p.Result[m.Infra.EnforcementCatalog]:
        """Load an enforcement catalog, failing closed on any owner gap.

        Every ast-grep reference names a rule the packaged rule catalog
        declares, every Ruff reference names a rule the tooling selection keeps
        enabled, every gate reference names a registered gate (and only a
        finding code that gate declares), and every codegen reference names a
        template entry. The first unresolved reference fails the load.

        Args:
            source: Catalog file to load; the packaged
                ``config/rules/catalog.yaml`` when omitted.

        Returns:
            The validated catalog, or the first unresolved owner reference.

        """
        result = r[m.Infra.EnforcementCatalog]
        package_root = type(config).ssot_config_dir().parent
        loaded = FlextInfraUtilitiesEnforcementCatalog._read_catalog(
            package_root / c.Infra.ENFORCEMENT_CATALOG_RELPATH
            if source is None
            else source
        )
        if loaded.failure:
            return loaded
        declared = FlextInfraUtilitiesCodemodRules.codemod_catalog_rules(
            c.Infra.PACKAGE_IMPORT_NAME,
            package_root / c.Infra.CODEMOD_CONFIG_RELPATH,
        )
        if declared.failure:
            return result.from_failure(declared)
        catalog = loaded.value
        owners: t.MappingKV[c.Infra.EnforcementEngine, frozenset[str]] = {
            c.Infra.EnforcementEngine.AST_GREP: frozenset(
                rule.id for rule in declared.value
            ),
            c.Infra.EnforcementEngine.RUFF: (
                FlextInfraUtilitiesEnforcementCatalog._enabled_ruff_rules(catalog)
            ),
            c.Infra.EnforcementEngine.GATE: c.Infra.ALLOWED_GATES,
            c.Infra.EnforcementEngine.CODEGEN: frozenset(
                entry.destination for entry in config.Infra.codegen.templates.entries
            ),
        }
        defect = next(
            (
                f"{row.id}: {reference.engine} {reference.id}: {problem}"
                for row in catalog.rules
                for reference in row.rules
                for problem in (
                    FlextInfraUtilitiesEnforcementCatalog._reference_problem(
                        reference, owners
                    ),
                )
                if problem is not None
            ),
            None,
        )
        return result.ok(catalog) if defect is None else result.fail(defect)

    @staticmethod
    def _read_catalog(path: Path) -> p.Result[m.Infra.EnforcementCatalog]:
        """Read and validate one catalog document.

        Returns:
            The schema-validated catalog, before owner resolution.

        """
        result = r[m.Infra.EnforcementCatalog]
        state = u.Cli.atomic_read_binary_file_state(path, required=True)
        if state.failure:
            return result.from_failure(state)
        if state.value.content is None:
            return result.fail(f"enforcement catalog is absent: {path}")
        parsed = u.Cli.yaml_parse(state.value.content.decode(c.DEFAULT_ENCODING))
        if parsed.failure:
            return result.from_failure(parsed)
        return result.ok(
            m.Infra.EnforcementCatalog.model_validate_json(
                u.json_mapping_adapter().dump_json(parsed.value)
            )
        )

    @staticmethod
    def _reference_problem(
        reference: m.Infra.EnforcementRuleRef,
        owners: t.MappingKV[c.Infra.EnforcementEngine, frozenset[str]],
    ) -> str | None:
        """Describe why one reference names no declared owner or code.

        Returns:
            The problem, or ``None`` when its owner declares the reference.

        """
        if reference.id not in owners[reference.engine]:
            return "owner is not declared or not enabled"
        if not FlextInfraUtilitiesEnforcementCatalog._code_declared(reference):
            return f"declares no finding code {reference.code}"
        return None

    @staticmethod
    def _enabled_ruff_rules(catalog: m.Infra.EnforcementCatalog) -> frozenset[str]:
        """Return the catalog's Ruff rule names the tooling selection enables.

        A rule is enabled when the selection names it or selects ``ALL`` and
        neither the native ignore list, the operator-ruled disabled rules nor
        the delegated rule owners remove it from the lint gate.

        Returns:
            The enabled Ruff rule names referenced by the catalog.

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
            reference.id
            for row in catalog.rules
            for reference in row.rules
            if reference.engine == c.Infra.EnforcementEngine.RUFF
            and reference.id not in excluded
            and (c.Infra.RUFF_SELECT_ALL in selected or reference.id in selected)
        )

    @staticmethod
    def _code_declared(reference: m.Infra.EnforcementRuleRef) -> bool:
        """Whether a reference's finding code is one its gate declares.

        Only the smells gate declares a finding vocabulary: its qlty checks,
        keyed in tooling ``smells.fix-text``.

        Returns:
            True when the reference carries no code or a declared one.

        """
        if reference.code is None:
            return True
        prefix = c.Infra.SMELLS_RULE_PREFIX
        return (
            reference.engine == c.Infra.EnforcementEngine.GATE
            and reference.id == c.Infra.SMELLS
            and reference.code.startswith(prefix)
            and reference.code.removeprefix(prefix)
            in config.Infra.tooling.smells.fix_text
        )


__all__: list[str] = ["FlextInfraUtilitiesEnforcementCatalog"]
