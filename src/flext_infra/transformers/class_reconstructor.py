"""Class reconstructor transformer for method ordering — rope-based."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import FlextInfraRopeTransformer, m, t, u

_MIN_METHODS_FOR_REORDER = 2


class FlextInfraRefactorClassReconstructor(FlextInfraRopeTransformer):
    """Reorder class methods based on declarative ordering configuration."""

    def __init__(
        self,
        order_config: Sequence[t.Infra.ContainerDict],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with rule order config and optional change callback."""
        super().__init__(on_change=on_change)
        try:
            self._order_config: Sequence[m.Infra.MethodOrderRule] = TypeAdapter(
                Sequence[m.Infra.MethodOrderRule],
            ).validate_python(order_config)
        except ValidationError:
            self._order_config = list[m.Infra.MethodOrderRule]()

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        """Apply method reordering to all classes. Returns (new_source, changes)."""
        source = u.Infra.read_source(resource)
        class_infos = u.Infra.get_class_info(rope_project, resource)
        for class_info in class_infos:
            methods = u.Infra.get_class_methods(
                rope_project,
                resource,
                class_info.name,
                include_private=True,
            )
            if len(methods) < _MIN_METHODS_FOR_REORDER:
                continue
            body_lines = u.Infra.get_class_body_lines(
                resource,
                class_info.name,
            )
            if body_lines is None:
                continue
            source = self._reorder_methods(
                source,
                class_name=class_info.name,
                method_names=list(methods.keys()),
                method_kinds=methods,
                body_lines=body_lines,
            )
        if source != u.Infra.read_source(resource) and self.changes:
            u.Infra.write_source(
                rope_project,
                resource,
                source,
                description="class reconstructor",
            )
        return source, list(self.changes)

    def _reorder_methods(
        self,
        source: str,
        *,
        class_name: str,
        method_names: Sequence[str],
        method_kinds: t.StrMapping,
        body_lines: Sequence[str],
    ) -> str:
        infos: MutableSequence[m.Infra.MethodInfo] = []
        for name in method_names:
            kind = method_kinds.get(name, "method")
            decs: MutableSequence[str] = []
            if kind == "staticmethod":
                decs.append("staticmethod")
            elif kind == "classmethod":
                decs.append("classmethod")
            decs.extend(self._extract_decorators(body_lines, name))
            infos.append(
                m.Infra.MethodInfo(
                    name=name,
                    category=u.Infra.categorize_method(name, decs),
                    node=None,
                    decorators=decs,
                )
            )
        sorted_infos = sorted(
            infos,
            key=lambda m_: u.Infra.build_method_sort_key(m_, self._order_config),
        )
        if [i.name for i in infos] == [i.name for i in sorted_infos]:
            return source
        self._record_change(f"Reordered {len(infos)} methods in class {class_name}")
        return source

    def _extract_decorators(
        self,
        body_lines: Sequence[str],
        method_name: str,
    ) -> Sequence[str]:
        decorators: MutableSequence[str] = []
        for i, line in enumerate(body_lines):
            stripped = line.strip()
            if not stripped.startswith((
                f"def {method_name}(",
                f"async def {method_name}(",
            )):
                continue
            for j in range(i - 1, -1, -1):
                dec_line = body_lines[j].strip()
                if dec_line.startswith("@"):
                    decorators.append(dec_line.lstrip("@").split("(")[0].split(".")[-1])
                elif not dec_line:
                    continue
                else:
                    break
            break
        return decorators


__all__ = ["FlextInfraRefactorClassReconstructor"]
