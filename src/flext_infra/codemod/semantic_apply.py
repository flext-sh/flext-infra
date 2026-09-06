"""Guarded semantic phase for detection-only ``make mod`` findings."""

from __future__ import annotations

from pathlib import Path

from flext_cli import cli
from flext_infra import u
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraCodemodSemanticApply:
    """Plan semantic cutovers, preflight the batch, then publish guarded files."""

    @classmethod
    def apply(cls, root: Path, preflight: m.Infra.ModScanReport) -> None:
        """Apply deferred-model, API-alias, and private-import cutovers."""
        original = cls._source_inventory(root, preflight)
        working = dict(original)
        changed: set[Path] = set()

        future_annotations: list[m.Infra.SemanticMigrationEdit] = []
        for file_path in sorted({
            (root / finding.file).resolve()
            for finding in preflight.entries
            if finding.rule_id == "require-future-annotations"
        }):
            original_source = working.get(file_path)
            if original_source is None:
                state = u.Cli.atomic_read_binary_file_state(
                    file_path, required=True
                ).unwrap()
                content = state.content
                if content is None:
                    msg = (
                        "authenticated source disappeared during mod preflight: "
                        f"{file_path}"
                    )
                    raise ValueError(msg)
                original_source = content.decode(c.Cli.ENCODING_DEFAULT)
                working[file_path] = original_source
            updated_source = u.Infra.ensure_future_annotations(original_source)
            if updated_source != original_source:
                future_annotations.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=file_path,
                        original_source=original_source,
                        updated_source=updated_source,
                        changes=("inserted canonical future annotations import",),
                    )
                )
        cls._apply_plan(working, future_annotations, changed)
        deferred = cls._deferred_model_edits(working)
        cls._apply_plan(working, deferred, changed)
        alias_findings = tuple(
            finding
            for finding in preflight.entries
            if finding.rule_id == "ban-compat-alias"
            and finding.file.name == c.Infra.API_PY
        )
        aliases = u.Infra.plan_api_alias_cutover(
            root=root, sources=working, findings=alias_findings
        )
        cls._apply_plan(working, aliases, changed)
        private_findings = tuple(
            finding
            for finding in preflight.entries
            if finding.rule_id == "ban-private-import"
        )
        private_imports = u.Infra.plan_private_import_cutover(
            root=root, sources=working, findings=private_findings
        )
        cls._apply_plan(working, private_imports, changed)

        cli.display_text(
            "mod: semantic cutover "
            f"future_annotations={len(future_annotations)} "
            f"deferred_models={len(deferred)} alias_files={len(aliases)} "
            f"private_import_files={len(private_imports)}"
        )
        cls._publish(original, working, changed)

    @staticmethod
    def _source_inventory(
        root: Path, preflight: m.Infra.ModScanReport
    ) -> t.MappingKV[Path, str]:
        """Read governed sources and every Python path reported by preflight."""
        project_roots = u.Infra.governed_project_roots(root)
        scan_dirs = m.Infra.RefactorConfig().project_scan_dirs
        paths = {
            path.resolve()
            for project_root in project_roots
            for directory in scan_dirs
            for path in u.Infra.iter_directory_python_files(project_root / directory)
        }
        paths.update(
            path
            for finding in preflight.entries
            if (path := (root / finding.file).resolve()).suffix == c.Infra.EXT_PYTHON
        )
        sources: dict[Path, str] = {}
        for path in sorted(paths):
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            content = state.content
            if content is None:
                msg = f"authenticated source disappeared during mod preflight: {path}"
                raise ValueError(msg)
            sources[path] = content.decode(c.Cli.ENCODING_DEFAULT)
        return sources

    @staticmethod
    def _deferred_model_edits(
        sources: t.MappingKV[Path, str],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Normalize every handwritten canonical model source from its AST."""
        edits: list[m.Infra.SemanticMigrationEdit] = []
        model_directories = c.Infra.FLEXT_MODELS_DIRECTORIES
        for path, source in sorted(sources.items()):
            if source.startswith("# AUTO-GENERATED FILE"):
                continue
            if (
                path.name not in c.Infra.FLEXT_MODELS_FILE_NAMES
                and not model_directories.intersection(path.parts)
            ):
                continue
            updated = u.Infra.normalize_deferred_self_references(source)
            if updated != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=source,
                        updated_source=updated,
                        changes=("normalized definition-time model references",),
                    )
                )
        return tuple(edits)

    @staticmethod
    def _apply_plan(
        sources: dict[Path, str],
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
        changed: set[Path],
    ) -> None:
        """Compose validated edit plans in memory without partial effects."""
        for edit in edits:
            current = sources.get(edit.file_path)
            if current != edit.original_source:
                msg = f"semantic plans disagree for {edit.file_path}"
                raise ValueError(msg)
            sources[edit.file_path] = edit.updated_source
            changed.add(edit.file_path)

    @staticmethod
    def _publish(
        original: t.MappingKV[Path, str],
        updated: t.MappingKV[Path, str],
        changed: set[Path],
    ) -> None:
        """Preflight all physical identities before the first atomic write."""
        publications: list[tuple[Path, m.Cli.AtomicFileState]] = []
        consumer_first = sorted(changed, key=FlextInfraCodemodSemanticApply._path_key)
        for path in consumer_first:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            content = state.content
            if (
                content is None
                or content.decode(c.Cli.ENCODING_DEFAULT) != original[path]
            ):
                msg = f"source changed after semantic preflight: {path}"
                raise ValueError(msg)
            publications.append((path, state))
        for path, state in publications:
            u.Cli.atomic_write_text_file_guarded(state, updated[path]).unwrap()

    @staticmethod
    def _path_key(path: Path) -> tuple[bool, str]:
        """Sort consumers before the public API owner in a typed key."""
        return (path.name == c.Infra.API_PY, path.as_posix())


__all__: list[str] = ["FlextInfraCodemodSemanticApply"]
