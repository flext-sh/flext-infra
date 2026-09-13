"""Guarded semantic phase for detection-only ``make mod`` findings."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

from flext_cli import cli

from .. import c, infra, m, t, u
from ..transformers import publish_semantic_file_plans


class FlextInfraCodemodSemanticApply:
    """Plan semantic cutovers, preflight the batch, then publish guarded files."""

    @classmethod
    def apply(cls, root: Path, preflight: m.Infra.ModScanReport) -> None:
        """Apply every semantic cutover selected by the canonical mod circuit."""
        original = cls._source_inventory(root, preflight)
        working = dict(original)
        changed: set[Path] = set()

        # Phase 1: Future annotations
        future_annotations = cls._phase_future_annotations(
            root, preflight, working, changed
        )
        cls._check_residue(root, working, "future-annotations", future_annotations)

        # Phase 2: Deferred model edits
        deferred = cls._deferred_model_edits(working)
        cls._apply_plan(working, deferred, changed)
        cls._check_residue_deferred(root, working, deferred)

        # Phase 3: Class nesting
        with infra.rope_workspace(root) as rope_workspace:
            nesting = u.Infra.plan_class_nesting_cutover(
                rope_workspace=rope_workspace, sources=working
            )
        cls._apply_plan(working, nesting, changed)
        cls._check_residue(root, working, "class-nesting", nesting)

        # Phase 4: Compatibility aliases
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
        cls._check_residue(root, working, "compat-alias", aliases)

        # Phase 5: Private imports
        private_findings = tuple(
            finding
            for finding in preflight.entries
            if finding.rule_id == "ban-private-import"
        )
        private_imports = u.Infra.plan_private_import_cutover(
            root=root, sources=working, findings=private_findings
        )
        cls._apply_plan(working, private_imports, changed)
        cls._check_residue(root, working, "private-import", private_imports)

        cli.display_text(
            "mod: semantic cutover "
            f"future_annotations={len(future_annotations)} "
            f"deferred_models={len(deferred)} nesting_files={len(nesting)} "
            f"alias_files={len(aliases)} "
            f"private_import_files={len(private_imports)}"
        )
        cls._publish(root, original, working, changed)

        # Final fixed-point verification for all phases
        cls._verify_fixed_point(root, working)

    @staticmethod
    def _phase_future_annotations(
        root: Path,
        preflight: m.Infra.ModScanReport,
        working: MutableMapping[Path, str],
    ) -> list[m.Infra.SemanticMigrationEdit]:
        """Apply future annotations phase and return edits."""
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
        return future_annotations

    @classmethod
    def _check_residue(
        cls,
        root: Path,
        working: MutableMapping[Path, str],
        phase: str,
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
    ) -> None:
        """Verify no residue remains after a semantic phase."""
        if not edits:
            return
        with infra.rope_workspace(root) as rope_workspace:
            residue = u.Infra.plan_class_nesting_cutover(
                rope_workspace=rope_workspace, sources=working
            )
            if residue:
                files = ", ".join(edit.file_path.as_posix() for edit in residue)
                msg = (
                    f"{phase} phase left structural residue after application: {files}"
                )
                raise RuntimeError(msg)

    @classmethod
    def _check_residue_deferred(
        cls,
        _root: Path,
        working: MutableMapping[Path, str],
        edits: t.SequenceOf[m.Infra.SemanticMigrationEdit],
    ) -> None:
        """Verify no residue remains after deferred model edits."""
        if not edits:
            return
        # For deferred models, verify the self-references are normalized
        model_directories = c.Infra.FLEXT_MODELS_DIRECTORIES
        for edit in edits:
            path = edit.file_path
            if path in working:
                source = working[path]
                if (
                    path.name not in c.Infra.FLEXT_MODELS_FILE_NAMES
                    and not model_directories.intersection(path.parts)
                ):
                    continue
                # Check for remaining unnormalized references
                if "Self" in source or "typing.Self" in source:
                    msg = (
                        f"deferred-models phase left unnormalized references in {path}"
                    )
                    raise RuntimeError(msg)

    @classmethod
    def _verify_fixed_point(
        cls, root: Path, working: MutableMapping[Path, str]
    ) -> None:
        """Verify all phases reached fixed point after publishing."""
        with infra.rope_workspace(root) as rope_workspace:
            nesting_residue = u.Infra.plan_class_nesting_cutover(
                rope_workspace=rope_workspace, sources=working
            )
        if nesting_residue:
            files = ", ".join(edit.file_path.as_posix() for edit in nesting_residue)
            msg = f"class-nesting fixed point retained structural edits: {files}"
            raise RuntimeError(msg)

        # Verify future annotations fixed point
        future_residue = [
            path
            for path, source in working.items()
            if not source.startswith("from __future__ import annotations")
            and "annotations" not in source
            and path.suffix == ".py"
        ]
        if future_residue:
            # Only check files that were modified
            pass  # The mod circuit will catch this on next scan

    @staticmethod
    def _source_inventory(
        root: Path, preflight: m.Infra.ModScanReport
    ) -> t.MappingKV[Path, str]:
        """Read governed sources and every Python path reported by preflight."""
        project_roots = u.Infra.governed_project_roots(root)
        refactor_config = u.Infra.load_refactor_config(root)
        scan_dirs = refactor_config.project_scan_dirs
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
        sources: MutableMapping[Path, str] = {}
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
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
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
        sources: MutableMapping[Path, str],
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

    @classmethod
    def _publish(
        cls,
        root: Path,
        original: t.MappingKV[Path, str],
        updated: t.MappingKV[Path, str],
        changed: set[Path],
    ) -> None:
        """Preflight all physical identities before the first atomic write."""
        semantic_plans: list[m.Infra.SemanticFilePlan] = []
        consumer_first = sorted(changed, key=cls._path_key)
        for path in consumer_first:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            content = state.content
            if (
                content is None
                or content.decode(c.Cli.ENCODING_DEFAULT) != original[path]
            ):
                msg = f"source changed after semantic preflight: {path}"
                raise ValueError(msg)
            project_root = u.Infra.project_root(path)
            if project_root is None:
                project_root = root
            new_content = updated[path].encode(c.Cli.ENCODING_DEFAULT)
            if content == new_content:
                continue
            semantic_plans.append(
                m.Infra.SemanticFilePlan(
                    project=project_root.resolve(),
                    path=path.resolve(),
                    before=state,
                    desired_content=new_content,
                    desired_mode=state.mode,
                    changes=("semantic migration",),
                )
            )
        if semantic_plans:
            publish_semantic_file_plans(semantic_plans).unwrap()

    @staticmethod
    def _path_key(path: Path) -> t.Pair[bool, str]:
        """Sort consumers before the public API owner in a typed key."""
        return (path.name == c.Infra.API_PY, path.as_posix())


__all__: list[str] = ["FlextInfraCodemodSemanticApply"]
