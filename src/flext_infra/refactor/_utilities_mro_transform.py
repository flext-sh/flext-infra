"""Rope-driven migration of module constants into MRO constants facades.

Centralizes the MRO migration logic into the MRO utility chain, removing legacy CST dependency.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import c, m, t


class FlextInfraUtilitiesRefactorMroTransform:
    """Move module-level constants into the constants facade class.

    Usage via namespace::

        from flext_infra import u

        code, migration, symbol_map = u.Infra.migrate_file(
            scan_result=scan_result,
        )
    """

    @staticmethod
    def migrate_file(
        *,
        scan_result: m.Infra.MROScanReport,
    ) -> t.Infra.Triple[str, m.Infra.MROFileMigration, t.StrMapping]:
        """Transform a candidate file and return code plus symbol map."""
        source = Path(scan_result.file).read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()

        empty_migration = m.Infra.MROFileMigration(
            file=scan_result.file,
            module=scan_result.module,
            moved_symbols=(),
            created_classes=(),
        )
        if not scan_result.candidates:
            return (source, empty_migration, {})

        class_name = scan_result.constants_class or c.Infra.DEFAULT_CONSTANTS_CLASS
        facade_alias = scan_result.facade_alias or class_name

        # Process from bottom to top to preserve line indices when deleting
        candidates = sorted(scan_result.candidates, key=lambda x: x.line, reverse=True)

        moved_symbols: list[str] = []
        symbol_map: dict[str, str] = {}
        moved_code: list[str] = []

        for cand in candidates:
            idx = cand.line - 1
            if idx < 0 or idx >= len(lines):
                continue

            line_str = lines[idx]
            moved_symbols.insert(0, cand.symbol)
            target = cand.symbol.lstrip("_") or cand.symbol
            symbol_map[cand.symbol] = f"{facade_alias}.{target}"

            # Replace target name if symbol was private
            if cand.symbol != target:
                line_str = re.sub(rf"\b{cand.symbol}\b", target, line_str, count=1)

            moved_code.insert(0, f"    {line_str}")
            del lines[idx]

            # Remove trailing blank lines above
            while idx - 1 >= 0 and not lines[idx - 1].strip():
                del lines[idx - 1]
                idx -= 1

        # Find or create class
        class_found = False
        insert_idx = -1
        for i, line in enumerate(lines):
            if line.startswith(f"class {class_name}"):
                class_found = True
                insert_idx = i + 1
                break

        if class_found:
            lines = lines[:insert_idx] + moved_code + lines[insert_idx:]
            created_classes = ()
        else:
            lines.extend(
                [
                    "",
                    "",
                    f"class {class_name}:",
                    '    """Module constants."""',
                ]
                + moved_code
            )
            created_classes = (class_name,)

        new_source = "\n".join(lines) + "\n"

        # Replace occurrences of bare symbols with facade_alias.symbol
        for symbol, target_path in symbol_map.items():
            pattern = re.compile(rf"\b{symbol}\b")
            new_source = pattern.sub(target_path, new_source)

        migration = m.Infra.MROFileMigration(
            file=scan_result.file,
            module=scan_result.module,
            moved_symbols=tuple(reversed(moved_symbols)),
            created_classes=created_classes,
        )
        return (new_source, migration, symbol_map)


__all__ = ["FlextInfraUtilitiesRefactorMroTransform"]
