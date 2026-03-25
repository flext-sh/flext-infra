"""Domain models for namespace enforcer violations and reports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Self

from flext_core import FlextModels
from pydantic import Field

from flext_infra import t


class FlextInfraNamespaceEnforcerModels:
    """Namespace enforcer violation and report models."""

    class FacadeStatus(FlextModels.FrozenStrictModel):
        family: Annotated[t.NonEmptyStr, Field(description="Facade family name")]
        exists: Annotated[bool, Field(description="Whether facade exists")]
        class_name: Annotated[str, Field(default="", description="Facade class name")]
        file: Annotated[str, Field(default="", description="Facade file path")]
        symbol_count: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Symbol count"),
        ]

        @classmethod
        def create(
            cls,
            *,
            family: str,
            exists: bool,
            class_name: str,
            file: str,
            symbol_count: int,
        ) -> Self:
            return cls(
                family=family,
                exists=exists,
                class_name=class_name,
                file=file,
                symbol_count=symbol_count,
            )

    class LooseObjectViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        name: Annotated[t.NonEmptyStr, Field(description="Symbol name")]
        kind: Annotated[str, Field(description="Object kind")]
        suggestion: Annotated[str, Field(default="", description="Fix suggestion")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            name: str,
            kind: str,
            suggestion: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                name=name,
                kind=kind,
                suggestion=suggestion,
            )

    class ImportAliasViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        current_import: Annotated[str, Field(description="Current import statement")]
        suggested_import: Annotated[
            str,
            Field(description="Suggested import statement"),
        ]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            current_import: str,
            suggested_import: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                current_import=current_import,
                suggested_import=suggested_import,
            )

    class NamespaceSourceViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        alias: Annotated[t.NonEmptyStr, Field(description="Runtime alias letter")]
        current_source: Annotated[
            t.NonEmptyStr,
            Field(description="Current import source"),
        ]
        correct_source: Annotated[
            t.NonEmptyStr,
            Field(description="Correct import source"),
        ]
        current_import: Annotated[str, Field(description="Current import statement")]
        suggested_import: Annotated[
            str,
            Field(description="Suggested import statement"),
        ]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            alias: str,
            current_source: str,
            correct_source: str,
            current_import: str,
            suggested_import: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                alias=alias,
                current_source=current_source,
                correct_source=correct_source,
                current_import=current_import,
                suggested_import=suggested_import,
            )

    class ClassPlacementViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        base_class: Annotated[t.NonEmptyStr, Field(description="Base class name")]
        suggestion: Annotated[str, Field(description="Fix suggestion")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            name: str,
            base_class: str,
            suggestion: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                name=name,
                base_class=base_class,
                suggestion=suggestion,
            )

    class MROCompletenessViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        family: Annotated[t.NonEmptyStr, Field(description="Facade family")]
        facade_class: Annotated[t.NonEmptyStr, Field(description="Facade class name")]
        missing_base: Annotated[t.NonEmptyStr, Field(description="Missing base class")]
        suggestion: Annotated[str, Field(description="Fix suggestion")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            family: str,
            facade_class: str,
            missing_base: str,
            suggestion: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                family=family,
                facade_class=facade_class,
                missing_base=missing_base,
                suggestion=suggestion,
            )

    class InternalImportViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        current_import: Annotated[str, Field(description="Current import statement")]
        detail: Annotated[str, Field(description="Violation detail")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            current_import: str,
            detail: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                current_import=current_import,
                detail=detail,
            )

    class ManualProtocolViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        name: Annotated[t.NonEmptyStr, Field(description="Protocol class name")]
        suggestion: Annotated[
            str,
            Field(
                default="Move to protocols.py/protocols/*.py/_protocols.py",
                description="Fix suggestion",
            ),
        ] = "Move to protocols.py/protocols/*.py/_protocols.py"

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            name: str,
            suggestion: str = "",
        ) -> Self:
            if suggestion:
                return cls(file=file, line=line, name=name, suggestion=suggestion)
            return cls(
                file=file,
                line=line,
                name=name,
                suggestion="Move to protocols.py/protocols/*.py/_protocols.py",
            )

    class CyclicImportViolation(FlextModels.FrozenStrictModel):
        cycle: Annotated[
            t.Infra.VariadicTuple[str], Field(description="Import cycle chain")
        ]
        files: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Files in cycle"),
        ] = Field(default_factory=tuple)

        @classmethod
        def create(
            cls, *, cycle: t.Infra.VariadicTuple[str], files: t.Infra.VariadicTuple[str]
        ) -> Self:
            return cls(cycle=cycle, files=files)

    class RuntimeAliasViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.NonNegativeInt, Field(default=0, description="Line number")]
        kind: Annotated[str, Field(description="Violation kind")]
        alias: Annotated[str, Field(description="Alias involved")]
        detail: Annotated[str, Field(default="", description="Violation detail")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            kind: str,
            alias: str,
            detail: str,
            line: int = 0,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                kind=kind,
                alias=alias,
                detail=detail,
            )

    class FutureAnnotationsViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]

        @classmethod
        def create(cls, *, file: str) -> Self:
            return cls(file=file)

    class ManualTypingAliasViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        name: Annotated[t.NonEmptyStr, Field(description="Alias name")]
        detail: Annotated[str, Field(default="", description="Violation detail")]

        @classmethod
        def create(cls, *, file: str, line: int, name: str, detail: str) -> Self:
            return cls(file=file, line=line, name=name, detail=detail)

    class CompatibilityAliasViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        alias_name: Annotated[t.NonEmptyStr, Field(description="Alias name")]
        target_name: Annotated[t.NonEmptyStr, Field(description="Target name")]

        @classmethod
        def create(
            cls,
            *,
            file: str,
            line: int,
            alias_name: str,
            target_name: str,
        ) -> Self:
            return cls(
                file=file,
                line=line,
                alias_name=alias_name,
                target_name=target_name,
            )

    class ParseFailureViolation(FlextModels.FrozenStrictModel):
        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        stage: Annotated[t.NonEmptyStr, Field(description="Parse stage")]
        error_type: Annotated[t.NonEmptyStr, Field(description="Error type")]
        detail: Annotated[str, Field(default="", description="Error detail")]

        @classmethod
        def create(cls, *, file: str, stage: str, error_type: str, detail: str) -> Self:
            return cls(file=file, stage=stage, error_type=error_type, detail=detail)

    class ProjectEnforcementReport(FlextModels.ArbitraryTypesModel):
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        project_root: Annotated[str, Field(description="Project root path")]
        facade_statuses: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.FacadeStatus],
            Field(description="Facade status list"),
        ] = []
        loose_objects: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.LooseObjectViolation],
            Field(description="Loose object violations"),
        ] = []
        import_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ImportAliasViolation],
            Field(description="Import alias violations"),
        ] = []
        namespace_source_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.NamespaceSourceViolation],
            Field(description="Namespace source violations"),
        ] = []
        internal_import_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.InternalImportViolation],
            Field(description="Internal import violations"),
        ] = []
        manual_protocol_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ManualProtocolViolation],
            Field(description="Manual protocol violations"),
        ] = []
        cyclic_imports: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.CyclicImportViolation],
            Field(description="Cyclic import violations"),
        ] = []
        runtime_alias_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.RuntimeAliasViolation],
            Field(description="Runtime alias violations"),
        ] = []
        future_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.FutureAnnotationsViolation],
            Field(description="Future annotations violations"),
        ] = []
        manual_typing_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ManualTypingAliasViolation],
            Field(description="Manual typing alias violations"),
        ] = []
        compatibility_alias_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.CompatibilityAliasViolation],
            Field(description="Compatibility alias violations"),
        ] = []
        class_placement_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ClassPlacementViolation],
            Field(description="Class placement violations"),
        ] = []
        mro_completeness_violations: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.MROCompletenessViolation],
            Field(description="MRO completeness violations"),
        ] = []
        parse_failures: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ParseFailureViolation],
            Field(description="Parse failures"),
        ] = []
        files_scanned: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Files scanned"),
        ]

        @classmethod
        def create(
            cls,
            *,
            project: str,
            project_root: str,
            facade_statuses: Sequence[FlextInfraNamespaceEnforcerModels.FacadeStatus],
            loose_objects: Sequence[
                FlextInfraNamespaceEnforcerModels.LooseObjectViolation
            ],
            import_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.ImportAliasViolation
            ],
            namespace_source_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.NamespaceSourceViolation
            ],
            internal_import_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.InternalImportViolation
            ],
            manual_protocol_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.ManualProtocolViolation
            ],
            cyclic_imports: Sequence[
                FlextInfraNamespaceEnforcerModels.CyclicImportViolation
            ],
            runtime_alias_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.RuntimeAliasViolation
            ],
            future_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.FutureAnnotationsViolation
            ],
            manual_typing_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.ManualTypingAliasViolation
            ],
            compatibility_alias_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.CompatibilityAliasViolation
            ],
            class_placement_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.ClassPlacementViolation
            ],
            mro_completeness_violations: Sequence[
                FlextInfraNamespaceEnforcerModels.MROCompletenessViolation
            ],
            parse_failures: Sequence[
                FlextInfraNamespaceEnforcerModels.ParseFailureViolation
            ],
            files_scanned: int,
        ) -> Self:
            return cls(
                project=project,
                project_root=project_root,
                facade_statuses=facade_statuses,
                loose_objects=loose_objects,
                import_violations=import_violations,
                namespace_source_violations=namespace_source_violations,
                internal_import_violations=internal_import_violations,
                manual_protocol_violations=manual_protocol_violations,
                cyclic_imports=cyclic_imports,
                runtime_alias_violations=runtime_alias_violations,
                future_violations=future_violations,
                manual_typing_violations=manual_typing_violations,
                compatibility_alias_violations=compatibility_alias_violations,
                class_placement_violations=class_placement_violations,
                mro_completeness_violations=mro_completeness_violations,
                parse_failures=parse_failures,
                files_scanned=files_scanned,
            )

    class WorkspaceEnforcementReport(FlextModels.ArbitraryTypesModel):
        workspace: Annotated[t.NonEmptyStr, Field(description="Workspace root path")]
        projects: Annotated[
            Sequence[FlextInfraNamespaceEnforcerModels.ProjectEnforcementReport],
            Field(description="Project enforcement reports"),
        ] = []
        total_facades_missing: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total missing facades"),
        ]
        total_loose_objects: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total loose objects"),
        ]
        total_import_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total import violations"),
        ]
        total_namespace_source_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total namespace source violations"),
        ]
        total_internal_import_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total internal import violations"),
        ]
        total_manual_protocol_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total manual protocol violations"),
        ]
        total_cyclic_imports: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total cyclic imports"),
        ]
        total_runtime_alias_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total runtime alias violations"),
        ]
        total_future_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total future annotations violations"),
        ]
        total_manual_typing_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total manual typing violations"),
        ]
        total_compatibility_alias_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total compatibility alias violations"),
        ]
        total_class_placement_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total class placement violations"),
        ]
        total_mro_completeness_violations: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total MRO completeness violations"),
        ]
        total_parse_failures: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total parse failures"),
        ]
        total_files_scanned: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total files scanned"),
        ]

        @classmethod
        def create(
            cls,
            *,
            workspace: str,
            projects: Sequence[
                FlextInfraNamespaceEnforcerModels.ProjectEnforcementReport
            ],
            total_facades_missing: int,
            total_loose_objects: int,
            total_import_violations: int,
            total_namespace_source_violations: int,
            total_internal_import_violations: int,
            total_manual_protocol_violations: int,
            total_cyclic_imports: int,
            total_runtime_alias_violations: int,
            total_future_violations: int,
            total_manual_typing_violations: int,
            total_compatibility_alias_violations: int,
            total_class_placement_violations: int,
            total_mro_completeness_violations: int,
            total_parse_failures: int,
            total_files_scanned: int,
        ) -> Self:
            return cls(
                workspace=workspace,
                projects=projects,
                total_facades_missing=total_facades_missing,
                total_loose_objects=total_loose_objects,
                total_import_violations=total_import_violations,
                total_namespace_source_violations=total_namespace_source_violations,
                total_internal_import_violations=total_internal_import_violations,
                total_manual_protocol_violations=total_manual_protocol_violations,
                total_cyclic_imports=total_cyclic_imports,
                total_runtime_alias_violations=total_runtime_alias_violations,
                total_future_violations=total_future_violations,
                total_manual_typing_violations=total_manual_typing_violations,
                total_compatibility_alias_violations=total_compatibility_alias_violations,
                total_class_placement_violations=total_class_placement_violations,
                total_mro_completeness_violations=total_mro_completeness_violations,
                total_parse_failures=total_parse_failures,
                total_files_scanned=total_files_scanned,
            )

        @property
        def has_violations(self) -> bool:
            return (
                self.total_facades_missing > 0
                or self.total_loose_objects > 0
                or self.total_import_violations > 0
                or self.total_namespace_source_violations > 0
                or self.total_internal_import_violations > 0
                or self.total_manual_protocol_violations > 0
                or self.total_cyclic_imports > 0
                or self.total_runtime_alias_violations > 0
                or self.total_future_violations > 0
                or self.total_manual_typing_violations > 0
                or self.total_compatibility_alias_violations > 0
                or self.total_class_placement_violations > 0
                or self.total_mro_completeness_violations > 0
                or self.total_parse_failures > 0
            )


__all__ = ["FlextInfraNamespaceEnforcerModels"]
