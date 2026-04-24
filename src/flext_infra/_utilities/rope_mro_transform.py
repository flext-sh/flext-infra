"""Rope-driven migration of module constants into MRO constants facades.

Centralizes the MRO migration logic into the rope utility chain, removing
legacy CST-era placement from the non-rope utility surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import c, m, t


class FlextInfraUtilitiesRopeMroTransform:
    """Move module-level constants into the constants facade class."""

    @staticmethod
    def migrate_file(
        *,
        scan_result: m.Infra.MROScanReport,
    ) -> tuple[str, m.Infra.MROFileMigration, t.StrMapping]:
        """Transform a candidate file and return code plus symbol map."""
        source = Path(scan_result.file).read_text(encoding=c.Cli.ENCODING_DEFAULT)
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

        candidates = sorted(scan_result.candidates, key=lambda x: x.line, reverse=True)

        moved_symbols: list[str] = []
        symbol_map: dict[str, str] = {}
        moved_code: list[str] = []

        for cand in candidates:
            start_idx = cand.line - 1
            end_idx = (cand.end_line or cand.line) - 1
            if (
                start_idx < 0
                or start_idx >= len(lines)
                or end_idx < start_idx
                or end_idx >= len(lines)
            ):
                continue

            block_lines = list(lines[start_idx : end_idx + 1])
            moved_symbols.insert(0, cand.symbol)
            target = cand.symbol.lstrip("_") or cand.symbol
            symbol_map[cand.symbol] = target

            if cand.symbol != target:
                block_lines = (
                    FlextInfraUtilitiesRopeMroTransform._rename_symbol_in_block(
                        block_lines=block_lines,
                        symbol=cand.symbol,
                        target=target,
                    )
                )

            moved_code = (
                FlextInfraUtilitiesRopeMroTransform._indent_block(block_lines)
                + moved_code
            )
            del lines[start_idx : end_idx + 1]

            while start_idx - 1 >= 0 and not lines[start_idx - 1].strip():
                del lines[start_idx - 1]
                start_idx -= 1

        class_found = False
        insert_idx = -1
        for index, line in enumerate(lines):
            if line.startswith(f"class {class_name}"):
                class_found = True
                insert_idx = index + 1
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

        lines = FlextInfraUtilitiesRopeMroTransform._drop_redundant_class_aliases(
            lines=lines,
            class_name=class_name,
            symbol_map=symbol_map,
        )
        new_source = "\n".join(lines) + "\n"
        new_source = FlextInfraUtilitiesRopeMroTransform._qualify_local_references(
            source=new_source,
            facade_alias=facade_alias,
            symbol_map=symbol_map,
        )

        migration = m.Infra.MROFileMigration(
            file=scan_result.file,
            module=scan_result.module,
            moved_symbols=tuple(reversed(moved_symbols)),
            created_classes=created_classes,
        )
        return (new_source, migration, symbol_map)

    @staticmethod
    def _rename_symbol_in_block(
        *,
        block_lines: t.StrSequence,
        symbol: str,
        target: str,
    ) -> list[str]:
        renamed_lines = list(block_lines)
        for index, line in enumerate(renamed_lines):
            if f"class {symbol}" not in line and not re.match(
                rf"^\s*{re.escape(symbol)}\b",
                line,
            ):
                continue
            renamed_lines[index] = re.sub(
                rf"\b{re.escape(symbol)}\b",
                target,
                line,
                count=1,
            )
            break
        return renamed_lines

    @staticmethod
    def _indent_block(block_lines: t.StrSequence) -> list[str]:
        return [("    " + line) if line else "" for line in block_lines]

    @staticmethod
    def _drop_redundant_class_aliases(
        *,
        lines: t.StrSequence,
        class_name: str,
        symbol_map: t.StrMapping,
    ) -> list[str]:
        alias_lines = {
            f"{target} = {symbol}"
            for symbol, target in symbol_map.items()
            if symbol != target
        }
        if not alias_lines:
            return list(lines)
        updated: list[str] = []
        in_class = False
        for line in lines:
            stripped = line.strip()
            if line.startswith(f"class {class_name}"):
                in_class = True
                updated.append(line)
                continue
            if in_class and stripped and not line.startswith((" ", "\t")):
                in_class = False
            if in_class and stripped in alias_lines:
                continue
            updated.append(line)
        return updated

    @staticmethod
    def _qualify_local_references(
        *,
        source: str,
        facade_alias: str,
        symbol_map: t.StrMapping,
    ) -> str:
        updated_source = source
        for symbol, target_path in symbol_map.items():
            qualified = f"{facade_alias}.{target_path}"
            bare_pattern = re.compile(
                rf"(?<!class\s)(?<!def\s)(?<!\.)(?<!import\s)"
                rf"\b{re.escape(symbol)}\b"
                rf"(?!\s*[=:](?!=))"
                rf"(?!\s*\()",
            )
            annotation_pattern = re.compile(rf"(:[ \t]*)\b{re.escape(symbol)}\b")
            return_pattern = re.compile(rf"(->[ \t]*)\b{re.escape(symbol)}\b")
            updated_source = bare_pattern.sub(qualified, updated_source)
            updated_source = annotation_pattern.sub(
                rf"\1{qualified}",
                updated_source,
            )
            updated_source = return_pattern.sub(
                rf"\1{qualified}",
                updated_source,
            )
        return updated_source


__all__: list[str] = ["FlextInfraUtilitiesRopeMroTransform"]
