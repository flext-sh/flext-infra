"""Automatic class-nesting plan derivation from source paths and Rope ASTs."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraUtilitiesClassNesting:
    """Derive class-nesting plans without registries or cached policy state."""

    @staticmethod
    def class_nesting_plans(
        project_root: Path,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.SequenceOf[m.Infra.ClassNestingViolation]:
        """Return plans only for classes additional to one semantic module owner."""
        resolved_root = project_root.resolve()
        source_root = (resolved_root / c.Infra.DEFAULT_SRC_DIR).resolve()
        resolved_file = file_path.resolve()
        relative = resolved_file.relative_to(source_root)
        if relative.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return ()
        layout = FlextInfraUtilitiesCodegenNamespace.layout(resolved_root)
        if layout is None:
            msg = f"class-nesting target has no project layout: {resolved_file}"
            raise ValueError(msg)
        module_relative = resolved_file.relative_to(layout.package_dir.resolve())
        classes = tuple(
            FlextInfraUtilitiesRopeAnalysis.get_class_info(rope_project, resource)
        )
        if len(classes) <= 1:
            return ()
        owner = FlextInfraUtilitiesClassNesting._module_owner(
            class_stem=layout.class_stem,
            module_relative=module_relative,
            classes=classes,
            file_path=resolved_file,
        )
        namespace = FlextInfraUtilitiesClassNesting._target_namespace(
            module_relative=module_relative,
            owner=owner,
            rope_project=rope_project,
            resource=resource,
        )
        confidence = (
            "high" if module_relative.parent.parts else c.Infra.SeverityLevel.LOW
        )
        return tuple(
            m.Infra.ClassNestingViolation(
                file=relative.as_posix(),
                line=class_info.line,
                class_name=class_info.name,
                target_namespace=namespace,
                confidence=confidence,
                rewrite_scope=c.Infra.RK_FILE,
            )
            for class_info in classes
            if class_info.name != owner.name
        )

    @staticmethod
    def _module_owner(
        *,
        class_stem: str,
        module_relative: Path,
        classes: t.SequenceOf[m.Infra.ClassInfo],
        file_path: Path,
    ) -> m.Infra.ClassInfo:
        """Resolve the unique path-, name-, or MRO-owned class for one module."""
        expected_name = class_stem + "".join(
            FlextInfraUtilitiesClassNesting._namespace_part(part)
            for part in (*module_relative.parent.parts, module_relative.stem)
        )
        named = tuple(info for info in classes if info.name == expected_name)
        if len(named) == 1:
            return named[0]
        class_names = {info.name for info in classes}
        local_base_names = {
            terminal
            for info in classes
            for base in info.bases
            if (terminal := base.rsplit(".", maxsplit=1)[-1]) in class_names
        }
        mro_owned = tuple(info for info in classes if info.name in local_base_names)
        if len(mro_owned) == 1:
            return mro_owned[0]
        public = tuple(info for info in classes if not info.name.startswith("_"))
        if len(public) == 1:
            return public[0]
        candidates = ", ".join(info.name for info in classes)
        msg = (
            f"ambiguous class-nesting owner for {file_path}: "
            f"expected {expected_name}; candidates: {candidates}"
        )
        raise ValueError(msg)

    @staticmethod
    def _namespace_part(part: str) -> str:
        """Return a canonical class-name component for one module path part."""
        normalized = part.lstrip("_")
        family = next(
            (
                alias
                for alias, directory in c.Infra.FAMILY_DIRECTORIES.items()
                if directory.lstrip("_") == normalized
            ),
            None,
        )
        return (
            c.Infra.FAMILY_SUFFIXES[family]
            if family
            else u.derive_class_stem(normalized)
        )

    @staticmethod
    def _target_namespace(
        *,
        module_relative: Path,
        owner: m.Infra.ClassInfo,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> str:
        """Use a real root-facade alias, otherwise the module owner itself."""
        if module_relative.parent.parts:
            return owner.name
        tree = FlextInfraUtilitiesRopeCore.get_pymodule(
            rope_project, resource
        ).get_ast()
        aliases: list[str] = []
        for node in getattr(tree, "body", ()) or ():
            if FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "Assign":
                continue
            if (
                FlextInfraUtilitiesRopeAnalysis.name_of(getattr(node, "value", None))
                != owner.name
            ):
                continue
            aliases.extend(
                alias
                for alias in FlextInfraUtilitiesRopeAnalysis.assignment_target_names(
                    node
                )
                if len(alias) == 1 and alias.islower()
            )
        if len(aliases) > 1:
            msg = f"ambiguous facade aliases for {resource.real_path}: {aliases}"
            raise ValueError(msg)
        namespace = aliases[0] if aliases else owner.name
        if not isinstance(namespace, str):
            msg = f"invalid facade namespace for {resource.real_path}: {namespace!r}"
            raise TypeError(msg)
        return namespace


__all__: list[str] = ["FlextInfraUtilitiesClassNesting"]
