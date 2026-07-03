"""Rope-backed autofix for ENFORCE-079 ClassVar constants outside _constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rope.base.pyobjects import PyClass
from rope.refactor import occurrences
from rope.refactor.occurrences import worder

from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.typings import t

if TYPE_CHECKING:
    from rope.base.project import Project


@dataclass(frozen=True)
class ClassvarConstantAutofixPlan:
    """Planned edits for one ENFORCE-079 autofix."""

    class_module: str
    class_name: str
    constant_name: str
    constants_module: str
    source_resource: t.Infra.RopeResource
    target_resource: t.Infra.RopeResource
    declaration_line: str
    class_lineno: int


class FlextInfraRefactorClassvarConstantAutofix:
    """Move a ClassVar constant from a class body to a _constants module.

    The fix keeps the public facade contract intact: consumers inside the
    package access the constant through the canonical ``_constants`` module,
    while external consumers continue to reach it via ``c.Infra.*``.
    """

    @staticmethod
    def plan(
        workspace_root: Path,
        class_full_name: str,
        constant_name: str,
        constants_module: str,
    ) -> ClassvarConstantAutofixPlan:
        """Build an autofix plan without touching disk."""
        with FlextInfraUtilitiesRopeCore.open_project(workspace_root) as project:
            return FlextInfraRefactorClassvarConstantAutofix._plan_with_project(
                project,
                class_full_name,
                constant_name,
                constants_module,
            )

    @staticmethod
    def _plan_with_project(
        project: Project,
        class_full_name: str,
        constant_name: str,
        constants_module: str,
    ) -> ClassvarConstantAutofixPlan:
        class_module, class_name = class_full_name.rsplit(".", maxsplit=1)
        source_mod = project.get_module(class_module)
        source_resource = source_mod.get_resource()
        pyclass = source_mod.get_attribute(class_name).get_object()
        if not isinstance(pyclass, PyClass):
            # Expected PyClass; if rope gives something else, fail loud.
            msg = f"{class_full_name} did not resolve to a class"
            raise TypeError(msg)
        class_lineno = _class_start_lineno(source_resource.read(), class_name)
        declaration_line = _extract_declaration_line(
            source_resource.read(),
            class_name,
            constant_name,
            class_lineno,
        )
        target_mod = project.get_module(constants_module)
        target_resource = target_mod.get_resource()
        return ClassvarConstantAutofixPlan(
            class_module=class_module,
            class_name=class_name,
            constant_name=constant_name,
            constants_module=constants_module,
            source_resource=source_resource,
            target_resource=target_resource,
            declaration_line=declaration_line,
            class_lineno=class_lineno,
        )

    @staticmethod
    def apply(
        workspace_root: Path,
        class_full_name: str,
        constant_name: str,
        constants_module: str,
        *,
        dry_run: bool = False,
    ) -> dict[str, object]:
        """Move the constant and rewrite all internal references.

        Returns a summary dict with ``touched_files`` and ``constant_module``.
        """
        with FlextInfraUtilitiesRopeCore.open_project(workspace_root) as project:
            plan = FlextInfraRefactorClassvarConstantAutofix._plan_with_project(
                project,
                class_full_name,
                constant_name,
                constants_module,
            )
            return FlextInfraRefactorClassvarConstantAutofix._apply_with_project(
                project,
                plan,
                dry_run=dry_run,
            )

    @staticmethod
    def _apply_with_project(
        project: Project,
        plan: ClassvarConstantAutofixPlan,
        *,
        dry_run: bool,
    ) -> dict[str, object]:
        source_text = plan.source_resource.read()
        target_text = plan.target_resource.read()
        touched: set[str] = {
            plan.source_resource.path,
            plan.target_resource.path,
        }

        # 1. Remove the ClassVar declaration from the class body.
        new_source = _remove_declaration_line(
            source_text,
            plan.declaration_line,
            plan.class_lineno,
        )

        # 2. Append the constant to the target _constants module.
        new_target = _append_constant(target_text, plan.declaration_line)

        # 3. Rewrite internal references from ClassName.NAME / cls.NAME to the
        # canonical constants module access.
        class_module_obj = project.get_module(plan.class_module)
        pyclass = class_module_obj.get_attribute(plan.class_name).get_object()
        pyname = pyclass.get_attribute(plan.constant_name)
        finder = occurrences.create_finder(
            project,
            plan.constant_name,
            pyname,
            imports=True,
            in_hierarchy=False,
        )
        rewrites: dict[t.Infra.RopeResource, list[tuple[int, int, str]]] = {}
        # Iterate over concrete project resources to avoid rope crashing when
        # an occurrence cannot be resolved to a resource (resource=None).
        for resource in project.get_python_files():
            for occurrence in finder.find_occurrences(resource=resource):
                start, end = occurrence.get_word_range()
                # Determine whether this occurrence is an attribute access on the
                # original class or on ``cls``.  We inspect the source around the
                # occurrence using rope's worder utilities.
                offset = occurrence.offset
                source = resource.read()
                prefix = _attribute_prefix(source, offset)
                if prefix in {plan.class_name, "cls"}:
                    replacement = (
                        f"{plan.constants_module.split('.')[-1]}.{plan.constant_name}"
                    )
                    rewrites.setdefault(resource, []).append((start, end, replacement))
                    touched.add(resource.path)

        if dry_run:
            return {
                "touched_files": sorted(touched),
                "source_text": new_source,
                "target_text": new_target,
                "rewrites": {
                    resource.path: edits for resource, edits in rewrites.items()
                },
            }

        # Apply resource edits directly to disk; rope's ChangeContents can
        # mis-apply offsets when the in-memory source has already been edited.
        Path(plan.source_resource.real_path).write_text(new_source, encoding="utf-8")
        Path(plan.target_resource.real_path).write_text(new_target, encoding="utf-8")
        for resource, edits in rewrites.items():
            if resource is plan.source_resource:
                continue  # already applied above
            text = resource.read()
            for start, end, replacement in sorted(edits, reverse=True):
                text = text[:start] + replacement + text[end:]
            Path(resource.real_path).write_text(text, encoding="utf-8")

        return {
            "touched_files": sorted(touched),
            "constant_module": plan.constants_module,
        }


def _class_start_lineno(source: str, class_name: str) -> int:
    """Return the 1-based line where ``class class_name`` starts."""
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("class ") and class_name in stripped:
            return lineno
    msg = f"Could not locate class {class_name}"
    raise ValueError(msg)


def _extract_declaration_line(
    source: str,
    class_name: str,
    constant_name: str,
    class_lineno: int,
) -> str:
    """Return the exact source line that declares the class-level constant."""
    lines = source.splitlines()
    for idx in range(class_lineno, len(lines)):
        line = lines[idx]
        stripped = line.lstrip()
        if stripped.startswith("class "):
            break
        if stripped.startswith((f"{constant_name}:", f"{constant_name} =")):
            return line.rstrip()
    msg = f"Could not find constant declaration for {constant_name} in {class_name}"
    raise ValueError(msg)


def _remove_declaration_line(
    source: str,
    declaration_line: str,
    class_lineno: int,
) -> str:
    """Remove the constant declaration from the class body, preserving layout."""
    lines = source.splitlines(keepends=True)
    for idx in range(class_lineno - 1, len(lines)):
        if lines[idx].rstrip() == declaration_line:
            # Also remove the blank line that typically precedes it, if any.
            if idx > 0 and not lines[idx - 1].strip():
                del lines[idx - 1 : idx + 1]
            else:
                del lines[idx : idx + 1]
            return "".join(lines)
    return source


def _append_constant(target_text: str, declaration_line: str) -> str:
    """Append the constant declaration to the target module source."""
    trimmed = target_text.rstrip()
    return f"{trimmed}\n\n{declaration_line}\n"


def _attribute_prefix(source: str, offset: int) -> str:
    """Return the prefix object name for an attribute access at ``offset``.

    For ``Foo.BAR`` at the position of ``BAR`` this returns ``"Foo"``.
    For bare ``BAR`` returns the empty string.
    """
    word_finder = worder.Worder(source, True)
    try:
        primary = word_finder.get_primary_at(offset)
    except Exception:
        primary = ""
    return primary


__all__: list[str] = ["FlextInfraRefactorClassvarConstantAutofix"]
