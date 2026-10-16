"""Identity-preserving native type edits for class movement and nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesSemanticNestingTypes(
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
):
    """Share native annotation regions and original lexical binding identity."""

    @classmethod
    def _rewrite_quoted_types(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        replacement: Callable[[p.Infra.RopeScope, str], str | None],
        *,
        protected: t.Pair[int, int] | None = None,
    ) -> str:
        module = project.get_pymodule(resource)
        edits = []
        for begin, end, literal, scope in cls.quoted_type_regions(
            source, project, module
        ):
            line = module.lines.get_line_number(begin)
            if protected is not None and protected[0] <= line <= protected[1]:
                continue
            changed = cls.rewrite_type_source(literal, project, scope, replacement)
            if changed != literal:
                edits.append(
                    m.Infra.SourceRewrite(start=begin, end=end, text=repr(changed))
                )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents

    @classmethod
    def _nesting_quoted_sources(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        definitions: t.MappingKV[Path, t.StrMapping],
    ) -> t.MappingKV[Path, str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        bindings = tuple(
            (
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                ),
                name,
                owner,
            )
            for path, names in definitions.items()
            for name, owner in names.items()
        )

        def replacement(scope: p.Infra.RopeScope, expression: str) -> str | None:
            actual = runtime.expression_name(scope, expression)
            for provider, name, owner in bindings:
                if not runtime.same_name(provider.get_attribute(name), actual):
                    continue
                if isinstance(actual, p.Infra.RopeImportedName):
                    module = scope.pyobject.get_module()
                    if module is None:
                        msg = "quoted type scope has no declaring module"
                        raise ValueError(msg)
                    _, destination = runtime.import_binding(
                        project, module, provider.get_name(), owner
                    )
                    selected = f"{destination}.{name}"
                else:
                    prefix, separator, _name = expression.rpartition(".")
                    selected = (
                        f"{prefix}.{owner}.{name}" if separator else f"{owner}.{name}"
                    )
                return cls._checked_type_reference(scope, selected)
            return None

        return {
            path: cls._rewrite_quoted_types(
                project,
                project.get_resource(path.relative_to(root).as_posix()),
                source,
                replacement,
            )
            for path, source in sources.items()
        }

    @staticmethod
    def _checked_type_reference(scope: p.Infra.RopeScope, expression: str) -> str:
        if not all(part.isidentifier() for part in expression.split(".")):
            msg = f"quoted type destination is not an identifier chain: {expression}"
            raise TypeError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = expression.partition(".")[0]
        module = scope.pyobject.get_module()
        if module is None:
            msg = "quoted type scope has no declaring module"
            raise ValueError(msg)
        local = runtime.expression_name(scope, root)
        global_binding = runtime.expression_name(module.get_scope(), root)
        if local is not None and (
            global_binding is None or not runtime.same_name(global_binding, local)
        ):
            msg = f"shadowed quoted type destination: {expression}"
            raise ValueError(msg)
        return expression


__all__: list[str] = ["FlextInfraUtilitiesSemanticNestingTypes"]
