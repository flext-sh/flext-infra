"""Per-identity authentication of operator-decided lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
        return frozenset(exempt)


__all__ = ["FlextInfraReadonlyNamespace"]
