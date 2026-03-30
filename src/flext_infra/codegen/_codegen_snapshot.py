from __future__ import annotations

import ast
import operator
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraCodegenCoercion,
    FlextInfraUtilitiesCodegenTransforms,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesParsing,
    c,
    t,
)


class FlextInfraCodegenSnapshot(FlextInfraCodegenCoercion):
    """Snapshot and change detection for code generation operations."""

    @staticmethod
    def find_package_dir(project_root: Path) -> Path | None:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                return child
        return None

    @staticmethod
    def snapshot_init_files(*, project_path: Path) -> t.StrMapping:
        snapshot: MutableMapping[str, str] = {}
        for root_name in c.Infra.MRO_SCAN_DIRECTORIES:
            root = project_path / root_name
            if not root.is_dir():
                continue
            for init_file in FlextInfraUtilitiesIteration.iter_directory_python_files(
                root,
                pattern=c.Infra.Files.INIT_PY,
            ):
                try:
                    snapshot[str(init_file)] = init_file.read_text(
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                except OSError:
                    continue
        return snapshot

    @staticmethod
    def snapshot_files(*, file_paths: Sequence[Path]) -> t.StrMapping:
        snapshot: MutableMapping[str, str] = {}
        for file_path in file_paths:
            try:
                snapshot[str(file_path)] = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
            except OSError:
                continue
        return snapshot

    @staticmethod
    def detect_changed_files(
        *,
        before_snapshot: t.StrMapping,
        file_paths: Sequence[Path],
    ) -> t.Infra.StrSet:
        changed: t.Infra.StrSet = set()
        for file_path in file_paths:
            path_key = str(file_path)
            previous = before_snapshot.get(path_key)
            try:
                current = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except OSError:
                continue
            if previous != current:
                changed.add(path_key)
        return changed

    @staticmethod
    def write_changes(
        *,
        source_path: Path,
        target_path: Path,
        nodes_moved: Sequence[ast.stmt],
        moved_names: t.StrSequence,
        source_tree: ast.Module,
        pkg_name: str,
        target_module: str,
        dry_run: bool,
    ) -> None:
        if dry_run:
            return
        encoding = c.Infra.Encoding.DEFAULT
        source_text = source_path.read_text(encoding=encoding)
        source_lines = source_text.splitlines()
        target_text = target_path.read_text(encoding=encoding)

        extracted: MutableSequence[str] = []
        ranges: MutableSequence[t.Infra.IntPair] = []
        for node in nodes_moved:
            start = node.lineno
            end = node.end_lineno or node.lineno
            block = "\n".join(source_lines[start - 1 : end])
            extracted.append(block)
            ranges.append((start, end))

        import_texts = (
            FlextInfraUtilitiesCodegenTransforms.collect_import_texts_for_nodes(
                nodes_moved,
                source_lines,
                source_tree,
                target_text,
            )
        )

        for start, end in sorted(ranges, key=operator.itemgetter(0), reverse=True):
            del source_lines[start - 1 : end]

        source_result = "\n".join(source_lines)
        re_export = f"from {pkg_name}.{target_module} import " + ", ".join(
            sorted(moved_names),
        )
        source_result = FlextInfraUtilitiesParsing.insert_import_statement(
            source_result,
            re_export,
        )
        if source_text.endswith("\n") and not source_result.endswith("\n"):
            source_result += "\n"

        target_result = target_text
        for imp in import_texts:
            target_result = FlextInfraUtilitiesParsing.insert_import_statement(
                target_result,
                imp,
            )
        for block in extracted:
            target_result = target_result.rstrip() + "\n\n\n" + block + "\n"

        source_path.write_text(source_result, encoding=encoding)
        target_path.write_text(target_result, encoding=encoding)

        FlextInfraUtilitiesFormatting.run_ruff_fix(source_path)
        FlextInfraUtilitiesFormatting.run_ruff_fix(target_path)


__all__ = ["FlextInfraCodegenSnapshot"]
