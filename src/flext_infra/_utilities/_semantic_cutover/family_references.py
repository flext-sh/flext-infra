"""Identity-bound consumer edits for one pure namespace wrapper."""

from __future__ import annotations

from flext_infra import c, m, p, t

from ..rope_runtime_refactors import FlextInfraUtilitiesRopeRuntimeRefactors
from ..rope_structure import FlextInfraUtilitiesRopeStructure

class FlextInfraUtilitiesSemanticFamilyReferences:
    """Use Rope occurrences, never textual wrapper-name substitutions."""

    @staticmethod
    def _family_consumer_rewrites(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        *,
        owner_name: str,
        wrapper_name: str,
        wrapper: p.Infra.RopePyName,
        names: t.MappingKV[str, str],
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeRefactors
        finder = runtime.create_occurrence_finder(
            project, wrapper_name, wrapper, imports=True, in_hierarchy=False
        )
        for occurrence in finder.find_occurrences(resource=resource):
            if occurrence.is_defined():
                continue
            _start, end = occurrence.get_word_range()
            if not source[end:].lstrip().startswith("."):
                msg = "namespace wrapper is used as a value or inheritance base: "
                raise ValueError(f"{msg}{resource.real_path}:{occurrence.lineno}")
            suffix = source[end:]
            member_offset = end + len(suffix) - len(suffix.lstrip()) + 1
            while source[member_offset].isspace():
                member_offset += 1
            member_name = runtime.word_primary_at(source, member_offset).rpartition(".")[2]
            if member_name not in names:
                msg = "namespace wrapper consumer has an unresolved member: "
                raise ValueError(f"{msg}{resource.real_path}:{occurrence.lineno}")
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        edits: list[m.Infra.SourceRewrite] = []
        for name, replacement in names.items():
            member = wrapper.get_object().get_attribute(name)
            members = runtime.create_occurrence_finder(
                project, name, member, imports=True, in_hierarchy=False
            )
            for occurrence in members.find_occurrences(resource=resource):
                start, end = occurrence.get_word_range()
                primary_start, primary_end = runtime.word_primary_range(
                    source, occurrence.offset
                )
                primary = source[primary_start:primary_end]
                qualifier, dot, _member = primary.rpartition(".")
                parent, separator, last = qualifier.rpartition(".")
                if dot and (last if separator else qualifier) == wrapper_name:
                    if not separator:
                        in_function = any(
                            statement.line <= occurrence.lineno <= statement.end_line
                            and statement.enclosing_kind == c.Infra.RopeScopeKind.FUNCTION
                            for statement in statements
                        )
                        parent = owner_name if in_function else ""
                    text = f"{parent}.{replacement}" if parent else replacement
                    edits.append(
                        m.Infra.SourceRewrite(
                            start=primary_start, end=primary_end, text=text
                        )
                    )
                elif name != replacement:
                    edits.append(m.Infra.SourceRewrite(start=start, end=end, text=replacement))
        return tuple(edits)


__all__: list[str] = ["FlextInfraUtilitiesSemanticFamilyReferences"]
