"""Move and compatibility rewrites for namespace refactors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t
from flext_infra.refactor._utilities_namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)


class FlextInfraUtilitiesRefactorNamespaceMoves(
    FlextInfraUtilitiesRefactorNamespaceCommon
):
    """Helpers for block moves and compatibility-alias rewrites."""

    @staticmethod
    def rewrite_manual_protocol_violations(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        violations: Sequence[m.Infra.ManualProtocolViolation],
    ) -> None:
        grouped: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped[Path(violation.file)].add(violation.name)
        protocol_moves: MutableSequence[
            t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]
        ] = []
        for source_file, protocol_names in grouped.items():
            move = FlextInfraUtilitiesRefactorNamespaceMoves._move_named_blocks(
                project_root=project_root,
                source_file=source_file,
                target_filename="protocols.py",
                names=protocol_names,
                header_prefix="class ",
            )
            if move is not None:
                protocol_moves.append(move)
        if protocol_moves:
            FlextInfraUtilitiesRefactorNamespaceMoves._rewrite_moved_imports(
                project_root=project_root,
                py_files=py_files,
                moves=protocol_moves,
            )

    @staticmethod
    def rewrite_manual_typing_alias_violations(
        *,
        project_root: Path,
        violations: Sequence[m.Infra.ManualTypingAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        _ = parse_failures
        grouped: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped[Path(violation.file)].add(violation.name)
        for source_file, alias_names in grouped.items():
            FlextInfraUtilitiesRefactorNamespaceMoves._move_typing_alias_lines(
                project_root=project_root,
                source_file=source_file,
                alias_names=alias_names,
            )

    @staticmethod
    def rewrite_compatibility_alias_violations(
        *,
        violations: Sequence[m.Infra.CompatibilityAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        _ = parse_failures
        grouped: Mapping[Path, t.MutableStrMapping] = defaultdict(dict)
        for violation in violations:
            grouped[Path(violation.file)][violation.alias_name] = violation.target_name
        for file_path, alias_map in grouped.items():
            FlextInfraUtilitiesRefactorNamespaceMoves._rewrite_compat_aliases_in_file(
                file_path=file_path,
                alias_map=alias_map,
            )

    @staticmethod
    def _rewrite_compat_aliases_in_file(
        *,
        file_path: Path,
        alias_map: t.StrMapping,
    ) -> None:
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        kept_source = "\n".join(
            line
            for line in source.splitlines()
            if FlextInfraUtilitiesRefactorNamespaceMoves._compat_assignment_target(
                line,
                alias_map=alias_map,
            )
            is None
        )
        rewritten = FlextInfraUtilitiesRefactorNamespaceMoves._apply_token_replacements(
            source=kept_source,
            alias_map=alias_map,
        )
        if rewritten != source:
            _ = file_path.write_text(rewritten, encoding=c.Infra.Encoding.DEFAULT)

    @staticmethod
    def _move_named_blocks(
        *,
        project_root: Path,
        source_file: Path,
        target_filename: str,
        names: t.Infra.StrSet,
        header_prefix: str,
    ) -> t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]] | None:
        source = source_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        blocks: MutableSequence[str] = []
        ranges: MutableSequence[t.Infra.IntPair] = []
        moved: MutableSequence[str] = []
        for name in sorted(names):
            found = FlextInfraUtilitiesRefactorNamespaceMoves._find_top_level_block(
                lines=lines,
                header=f"{header_prefix}{name}",
            )
            if found is None:
                continue
            start, end = found
            blocks.append("\n".join(lines[start:end]))
            ranges.append((start, end))
            moved.append(name)
        if not blocks:
            return None
        target_file = FlextInfraUtilitiesRefactorNamespaceMoves._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename=target_filename,
        )
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else "from __future__ import annotations\n"
        )
        updated_target = target_source.rstrip()
        for block in blocks:
            if block.splitlines()[0] not in updated_target:
                updated_target += f"\n\n{block}"
        _ = target_file.write_text(
            updated_target.rstrip() + "\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        filtered_lines = list(lines)
        for start, end in sorted(ranges, reverse=True):
            del filtered_lines[start:end]
        _ = source_file.write_text(
            "\n".join(filtered_lines).rstrip() + "\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )
        return (source_file, target_file, tuple(moved))

    @staticmethod
    def _move_typing_alias_lines(
        *,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
    ) -> None:
        lines = source_file.read_text(encoding=c.Infra.Encoding.DEFAULT).splitlines()
        moved_lines: MutableSequence[str] = []
        kept_lines: MutableSequence[str] = []
        for line in lines:
            stripped = line.strip()
            should_move = any(
                stripped.startswith((f"type {name} =", f"{name}: TypeAlias ="))
                for name in alias_names
            )
            if should_move:
                moved_lines.append(line)
            else:
                kept_lines.append(line)
        if not moved_lines:
            return
        target_file = FlextInfraUtilitiesRefactorNamespaceMoves._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename="typings.py",
        )
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else "from __future__ import annotations\n"
        )
        updated_target = target_source.rstrip() + "\n\n" + "\n".join(moved_lines) + "\n"
        _ = target_file.write_text(updated_target, encoding=c.Infra.Encoding.DEFAULT)
        _ = source_file.write_text(
            "\n".join(kept_lines).rstrip() + "\n",
            encoding=c.Infra.Encoding.DEFAULT,
        )

    @staticmethod
    def _rewrite_moved_imports(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        moves: Sequence[t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]],
    ) -> None:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR

        def _module_path(file_path: Path) -> str:
            try:
                relative = file_path.relative_to(src_dir)
            except ValueError:
                return ""
            parts = list(relative.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            return ".".join(parts)

        mappings = [
            (_module_path(source), _module_path(target), set(names))
            for source, target, names in moves
            if _module_path(source) and _module_path(target)
        ]
        for py_file in py_files:
            source = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            updated = source
            for source_module, target_module, names in mappings:
                for name in names:
                    updated = updated.replace(
                        f"from {source_module} import {name}",
                        f"from {target_module} import {name}",
                    )
            if updated != source:
                _ = py_file.write_text(updated, encoding=c.Infra.Encoding.DEFAULT)


__all__ = ["FlextInfraUtilitiesRefactorNamespaceMoves"]
