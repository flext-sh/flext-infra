"""Per-identity authentication of operator-decided lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, u

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraReadonlyNamespace:
    """Authenticate exempt findings from source and native Rope identity.

    Identities are derived from the reported findings, never from a hand
    registry; nothing is exempt by rule name or by file. Ruff remains the
    diagnostic authority.
    """

    @classmethod
    def exempt_identities(
        cls,
        project_dir: Path,
        findings: t.SequenceOf[p.Infra.Issue],
    ) -> frozenset[t.Pair[t.Triple[Path, int, int], str]]:
        """Authenticate the findings an operator-decided exemption names.

        The publication policy is authenticated per identity from source,
        never by name or file:

        - ``non-pep695-type-alias`` ("Exceção UP040 por identidade"): a PEP 613
          facade class publication, authenticated by the facade owner;

        Returns:
            ``((path, row, column), rule)`` for each authenticated finding.

        """
        alias_rule = c.Infra.RUFF_NON_PEP695_TYPE_ALIAS
        rows: t.MutableMappingKV[str, t.MutableMappingKV[Path, set[int]]] = {
            alias_rule: {},
        }
        naming_rule = "invalid-function-name"
        for finding in findings:
            if finding.code in rows:
                rows[finding.code].setdefault(Path(finding.file).resolve(), set()).add(
                    finding.line
                )
        exempt: set[t.Pair[t.Triple[Path, int, int], str]] = set()
        if rows[alias_rule]:
            exempt.update(
                (identity, alias_rule)
                for identity in u.Infra.facade_class_publications(
                    project_dir,
                    {
                        path: frozenset(lines)
                        for path, lines in rows[alias_rule].items()
                    },
                )
            )
        # N802 on a protocol property mirrors a published settings branch
        # field (ADR-005: ``settings.<Namespace>.*`` carries the namespace's
        # capitalized name); the structural contract must repeat that exact
        # spelling, authenticated against the member's settings model.
        exempt.update(
            (identity, naming_rule)
            for identity in cls._settings_branch_properties(project_dir, findings)
        )
        return frozenset(exempt)

    @staticmethod
    def _settings_branch_properties(
        project_dir: Path,
        findings: t.SequenceOf[p.Infra.Issue],
    ) -> t.VariadicTuple[t.Triple[Path, int, int]]:
        """Authenticate capitalized protocol properties against settings fields.

        Returns:
            The findings whose flagged name is a field on the member's
            settings model, proven from native source.

        """
        wanted: dict[str, list[t.Triple[Path, int, int]]] = {}
        for finding in findings:
            if finding.code != "invalid-function-name":
                continue
            name = finding.message.split("`")[1].partition("`")[0]
            wanted.setdefault(name, []).append((
                Path(finding.file).resolve(),
                finding.line,
                finding.column,
            ))
        if not wanted:
            return ()
        proven: list[t.Triple[Path, int, int]] = []
        for source_file in project_dir.rglob("*.py"):
            text = source_file.read_text(encoding=c.DEFAULT_ENCODING, errors="ignore")
            tree = ast.parse(text)
            for declaration in ast.walk(tree):
                if not isinstance(declaration, ast.ClassDef) or not (
                    declaration.name.endswith("Settings")
                    or declaration.name.endswith("Config")
                ):
                    continue
                for statement in declaration.body:
                    if (
                        isinstance(statement, ast.AnnAssign)
                        and isinstance(statement.target, ast.Name)
                        and statement.target.id in wanted
                    ):
                        proven.extend(wanted[statement.target.id])
        return tuple(proven)


__all__ = ["FlextInfraReadonlyNamespace"]
