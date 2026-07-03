"""Rope-backed autofix for ENFORCE-079 ClassVar constants outside _constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rope.base.exceptions import ModuleNotFoundError as RopeModuleNotFoundError
from rope.base.pyobjects import PyClass
from rope.base.resources import File
from rope.refactor import occurrences
from rope.refactor.occurrences import worder

from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.typings import t

if TYPE_CHECKING:
    from rope.base.project import Project


_DOCSTRING_DELIMITER_COUNT = 2


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
        target_resource = _target_resource_for_module(
            project,
            constants_module,
        )
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
        target_path = Path(plan.target_resource.real_path)
        target_text = (
            plan.target_resource.read()
            if target_path.exists()
            else _new_constants_module_source(plan.constants_module)
        )
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

        # 3. Rewrite internal references from ClassName.NAME / cls.NAME /
        # self.__class__.NAME to the canonical constants module access.
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
        rewrites: dict[str, list[tuple[int, int, str]]] = {}
        # Iterate over concrete project resources to avoid rope crashing when
        # an occurrence cannot be resolved to a resource (resource=None).
        for resource in project.get_python_files():
            for occurrence in finder.find_occurrences(resource=resource):
                offset = occurrence.offset
                source = resource.read()
                prefix = _attribute_prefix(source, offset)
                if _should_rewrite_prefix(prefix, plan.class_name):
                    word_finder = worder.Worder(source, True)
                    try:
                        start, end = word_finder.get_primary_range(offset)
                    except Exception:
                        start, end = occurrence.get_word_range()
                    replacement = (
                        f"{plan.constants_module.split('.')[-1]}.{plan.constant_name}"
                    )
                    rewrites.setdefault(resource.path, []).append(
                        (start, end, replacement),
                    )
                    touched.add(resource.path)

        if dry_run:
            source_preview = _rewrite_class_access_in_source(
                new_source,
                plan.class_name,
                plan.constant_name,
                plan.constants_module.split(".")[-1],
            )
            return {
                "touched_files": sorted(touched),
                "source_text": source_preview,
                "target_text": new_target,
                "rewrites": dict(rewrites),
            }

        # 4. Rewrite source-module references textually. Rope occurrence offsets
        # target the original source and become stale after the declaration is
        # removed, so the modified source uses the known class-access forms.
        constants_alias = plan.constants_module.split(".")[-1]
        rewrites.pop(plan.source_resource.path, None)
        new_source = _rewrite_class_access_in_source(
            new_source,
            plan.class_name,
            plan.constant_name,
            constants_alias,
        )
        # 5. Inject ``from . import _constants`` (or equivalent) into the source
        # module so the rewritten references resolve.
        new_source = _ensure_constants_import(
            new_source,
            constants_alias,
            plan.class_module,
            plan.constants_module,
        )
        Path(plan.source_resource.real_path).write_text(new_source, encoding="utf-8")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(new_target, encoding="utf-8")

        # 6. Apply remaining rewrites to other resources.
        for resource in project.get_python_files():
            edits = rewrites.get(resource.path)
            if not edits:
                continue
            text = resource.read()
            text = _apply_edits(text, edits)
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


def _target_resource_for_module(
    project: Project,
    constants_module: str,
) -> t.Infra.RopeResource:
    """Return the existing or creatable sibling constants module resource."""
    try:
        target_mod = project.get_module(constants_module)
        target_resource = target_mod.get_resource()
        if isinstance(target_resource, File):
            return target_resource
    except RopeModuleNotFoundError:
        pass
    constants_file = Path(*constants_module.split(".")).with_suffix(".py")
    return project.get_file(str(constants_file))


def _new_constants_module_source(constants_module: str) -> str:
    """Return minimal source for a newly-created constants module."""
    return (
        f'"""Constants for {constants_module}."""\n\n'
        "from __future__ import annotations\n"
    )


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


def _apply_edits(
    text: str,
    edits: t.SequenceOf[tuple[int, int, str]],
) -> str:
    """Apply (start, end, replacement) edits to ``text`` in reverse order."""
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _append_constant(target_text: str, declaration_line: str) -> str:
    """Append the constant declaration to the target module source."""
    trimmed = target_text.rstrip()
    dedented = declaration_line.lstrip()
    return f"{trimmed}\n\n{dedented}\n"


def _attribute_prefix(source: str, offset: int) -> str:
    """Return the primary expression for an attribute access at ``offset``.

    For ``Foo.BAR`` at the position of ``BAR`` this returns ``"Foo"``.
    For ``cls.BAR`` returns ``"cls"``.  For ``self.__class__.BAR`` returns
    ``"self.__class__"``.  For bare ``BAR`` returns the empty string.
    """
    word_finder = worder.Worder(source, True)
    try:
        primary = word_finder.get_primary_at(offset)
    except Exception:
        primary = ""
    return str(primary)


def _should_rewrite_prefix(prefix: str, class_name: str) -> bool:
    """Return whether an attribute prefix should be rewritten to _constants."""
    return prefix in {class_name, "cls"} or prefix.endswith(".__class__")


def _ensure_constants_import(
    source: str,
    constants_alias: str,
    class_module: str,
    constants_module: str,
) -> str:
    """Add an import for the canonical _constants module if absent.

    Computes a relative import from ``class_module`` to ``constants_module``.
    The import binds the module itself so consumers write
    ``_constants.NAME``.
    """
    if constants_module == class_module:
        return source
    class_parts = class_module.split(".")
    constants_parts = constants_module.split(".")
    common = 0
    for a, b in zip(class_parts, constants_parts, strict=False):
        if a != b:
            break
        common += 1
    ups = len(class_parts) - common - 1  # minus the source module itself
    rel_parts = constants_parts[common:]
    if ups == 0 and rel_parts == [constants_alias]:
        import_line = f"from . import {constants_alias}\n"
    elif ups == 0 and rel_parts:
        import_line = f"from .{'.'.join(rel_parts)} import {constants_alias}\n"
    elif ups > 0 and rel_parts:
        import_line = (
            f"from {'.' * ups}{'.'.join(rel_parts)} import {constants_alias}\n"
        )
    elif ups > 0:
        import_line = f"from {'.' * ups} import {constants_alias}\n"
    else:
        import_line = f"from {constants_module} import {constants_alias}\n"

    lines = source.splitlines(keepends=True)
    existing = {line.strip() for line in lines}
    if import_line.strip() in existing:
        return source
    insert_after = _module_import_insert_after(lines)
    if insert_after >= 0:
        lines.insert(insert_after + 1, import_line)
    else:
        lines.insert(0, import_line)
    return "".join(lines)


def _module_import_insert_after(lines: t.StrSequence) -> int:
    """Return index after module docstring and future imports only."""
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    insert_after = -1
    if idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith(('"""', "'''")):
            quote = stripped[:3]
            insert_after = idx
            if stripped.count(quote) < _DOCSTRING_DELIMITER_COUNT:
                idx += 1
                while idx < len(lines):
                    insert_after = idx
                    if quote in lines[idx]:
                        idx += 1
                        break
                    idx += 1
            else:
                idx += 1
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped:
            idx += 1
            continue
        if stripped.startswith("from __future__ import"):
            insert_after = idx
            idx += 1
            continue
        break
    return insert_after


def _rewrite_class_access_in_source(
    source: str,
    class_name: str,
    constant_name: str,
    constants_alias: str,
) -> str:
    """Rewrite class-qualified constant access inside the source module itself.

    Rope's occurrence finder binds ``ClassName.NAME`` and ``cls.NAME`` but not
    ``self.__class__.NAME``.  We perform a fast textual pass over the source
    (after the declaration was removed) and rewrite the known patterns.
    """
    patterns = (
        f"{class_name}.{constant_name}",
        f"cls.{constant_name}",
        f"self.{constant_name}",
        f"self.__class__.{constant_name}",
    )
    replacement = f"{constants_alias}.{constant_name}"
    edits: list[tuple[int, int, str]] = []
    for pattern in patterns:
        start = 0
        while True:
            idx = source.find(pattern, start)
            if idx < 0:
                break
            edits.append((idx, idx + len(pattern), replacement))
            start = idx + len(replacement)
    return _apply_edits(source, edits)


__all__: list[str] = ["FlextInfraRefactorClassvarConstantAutofix"]
