"""Automatic class-nesting plans derived from the public Rope workspace."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m

from .class_nesting_cst import FlextInfraUtilitiesClassNestingCst

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraUtilitiesClassNesting(FlextInfraUtilitiesClassNestingCst):
    """Plan class nesting from semantic module ownership instead of record lists."""

    @staticmethod
    def class_nesting_plan(
        rope_workspace: p.Infra.RopeWorkspaceDsl, file_path: Path
    ) -> p.Result[tuple[m.Infra.ClassNestingViolation, ...]]:
        """Return top-level classes that must move under the declared module owner."""
        resolved_file = file_path.resolve()
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(resolved_file.name)
        if family is None:
            family = next(
                (
                    alias
                    for alias, directory in c.Infra.FAMILY_DIRECTORIES.items()
                    if resolved_file.parent.name == directory
                ),
                None,
            )
        if family is None:
            return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(())
        convention = rope_workspace.convention(resolved_file)
        top_level_classes = tuple(
            item
            for item in rope_workspace.objects(
                resolved_file, include_local_scopes=False, include_references=False
            )
            if item.kind == "class" and item.class_path == item.name
        )
        if len(top_level_classes) <= 1:
            return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(())

        target_namespace = convention.module_policy.expected_family
        owners = tuple(
            item for item in top_level_classes if item.name == target_namespace
        )
        if target_namespace is None or len(owners) != 1:
            class_names = ", ".join(item.name for item in top_level_classes)
            return r[tuple[m.Infra.ClassNestingViolation, ...]].fail(
                "class-nesting requires exactly one declared module owner "
                f"for {convention.module_name}; discovered: {class_names}"
            )

        relative_file = resolved_file.relative_to(
            rope_workspace.repository_root.resolve()
        ).as_posix()
        confidence = max(
            c.Infra.CONFIDENCE_RANKS, key=c.Infra.CONFIDENCE_RANKS.__getitem__
        )
        return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(
            tuple(
                m.Infra.ClassNestingViolation(
                    file=relative_file,
                    line=max(1, item.line),
                    class_name=item.name,
                    target_namespace=target_namespace,
                    confidence=confidence,
                    rewrite_scope=c.Infra.RK_FILE,
                )
                for item in top_level_classes
                if item.name != target_namespace
            )
        )

    @classmethod
    def plan_class_nesting_cutover(
        cls,
        *,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan all structural nesting and consumer rewrites without effects."""
        modules = {
            entry.file_path.resolve(): entry for entry in rope_workspace.modules()
        }
        plans_by_file: dict[Path, tuple[m.Infra.ClassNestingViolation, ...]] = {}
        bindings_by_module: dict[str, dict[str, str]] = {}
        for file_path, source in sorted(sources.items()):
            resolved_file = file_path.resolve()
            module = modules.get(resolved_file)
            if module is None or source.startswith(c.Infra.AUTOGEN_HEADERS):
                continue
            violations = cls.class_nesting_plan(rope_workspace, resolved_file).unwrap()
            if not violations:
                continue
            plans_by_file[resolved_file] = violations
            module_bindings = bindings_by_module.setdefault(module.module_name, {})
            for violation in violations:
                previous = module_bindings.get(violation.class_name)
                if previous not in {None, violation.target_namespace}:
                    msg = (
                        f"ambiguous class-nesting owner for {module.module_name}."
                        f"{violation.class_name}: {previous}, "
                        f"{violation.target_namespace}"
                    )
                    raise ValueError(msg)
                module_bindings[violation.class_name] = violation.target_namespace
        if not plans_by_file:
            return ()

        nested_names = frozenset(
            name for bindings in bindings_by_module.values() for name in bindings
        )
        edits: list[m.Infra.SemanticMigrationEdit] = []
        changed_owners: set[Path] = set()
        immutable_bindings = {
            module: dict(bindings) for module, bindings in bindings_by_module.items()
        }
        for file_path, source in sorted(sources.items()):
            resolved_file = file_path.resolve()
            if source.startswith(c.Infra.AUTOGEN_HEADERS) or (
                resolved_file not in plans_by_file
                and not any(name in source for name in nested_names)
            ):
                continue
            module = modules.get(resolved_file)
            definitions = {
                violation.class_name: violation.target_namespace
                for violation in plans_by_file.get(resolved_file, ())
            }
            updated = cls.rewrite_class_nesting_source(
                source,
                module_name=module.module_name if module is not None else "",
                is_package_init=module.is_package_init if module is not None else False,
                bindings_by_module=immutable_bindings,
                definitions=definitions,
            )
            if updated == source:
                continue
            if definitions:
                changed_owners.add(resolved_file)
            edits.append(
                m.Infra.SemanticMigrationEdit(
                    file_path=resolved_file,
                    original_source=source,
                    updated_source=updated,
                    changes=tuple(
                        f"nested {name} under {owner}"
                        for name, owner in definitions.items()
                    )
                    or ("rewired nested-class consumer",),
                )
            )
        missing_owners = set(plans_by_file) - changed_owners
        if missing_owners:
            msg = "class-nesting owners produced no structural edit: " + ", ".join(
                path.as_posix() for path in sorted(missing_owners)
            )
            raise ValueError(msg)
        return tuple(edits)


__all__: list[str] = ["FlextInfraUtilitiesClassNesting"]
