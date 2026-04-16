"""Domain models for namespace enforcer violations and reports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Self

from flext_core import m
from flext_infra import FlextInfraModelsMixins, t


class FlextInfraModelsNamespaceEnforcer:
    """Namespace enforcer violation and report models."""

    class FileLineViolation(
        FlextInfraModelsMixins.FileLineViolationMixin,
        m.ContractModel,
    ):
        """Shared base: file + line for all violation models."""

    class ImportViolationBase(
        FlextInfraModelsMixins.CurrentImportMixin,
        FileLineViolation,
    ):
        """Shared base: file + line + current_import."""

    class FacadeStatus(m.ContractModel):
        family: Annotated[t.NonEmptyStr, m.Field(description="Facade family name")]
        exists: Annotated[bool, m.Field(description="Whether facade exists")]
        class_name: Annotated[str, m.Field(description="Facade class name")] = ""
        file: Annotated[str, m.Field(description="Facade file path")] = ""
        symbol_count: Annotated[
            t.NonNegativeInt, m.Field(description="Symbol count")
        ] = 0

    class LooseObjectViolation(FileLineViolation):
        name: Annotated[t.NonEmptyStr, m.Field(description="Symbol name")]
        kind: Annotated[str, m.Field(description="Object kind")]
        suggestion: Annotated[str, m.Field(description="Fix suggestion")] = ""

    class ImportAliasViolation(ImportViolationBase):
        suggested_import: Annotated[
            str,
            m.Field(description="Suggested import statement"),
        ]

    class NamespaceSourceViolation(FileLineViolation):
        alias: Annotated[t.NonEmptyStr, m.Field(description="Runtime alias letter")]
        current_source: Annotated[
            t.NonEmptyStr,
            m.Field(description="Current import source"),
        ]
        correct_source: Annotated[
            t.NonEmptyStr,
            m.Field(description="Correct import source"),
        ]
        current_import: Annotated[str, m.Field(description="Current import statement")]
        suggested_import: Annotated[
            str,
            m.Field(description="Suggested import statement"),
        ]

    class ClassPlacementViolation(FileLineViolation):
        name: Annotated[t.NonEmptyStr, m.Field(description="Class name")]
        base_class: Annotated[t.NonEmptyStr, m.Field(description="Base class name")]
        suggestion: Annotated[str, m.Field(description="Fix suggestion")]

    class MROCompletenessViolation(FileLineViolation):
        family: Annotated[t.NonEmptyStr, m.Field(description="Facade family")]
        facade_class: Annotated[t.NonEmptyStr, m.Field(description="Facade class name")]
        missing_base: Annotated[
            t.NonEmptyStr, m.Field(description="Missing base class")
        ]
        suggestion: Annotated[str, m.Field(description="Fix suggestion")]

    class InternalImportViolation(
        FlextInfraModelsMixins.ViolationDetailMixin,
        ImportViolationBase,
    ):
        pass

    class ManualProtocolViolation(FileLineViolation):
        name: Annotated[t.NonEmptyStr, m.Field(description="Protocol class name")]
        suggestion: Annotated[
            str,
            m.Field(
                description="Fix suggestion",
            ),
        ] = "Move to protocols.py/protocols/*.py/_protocols.py"

    class CyclicImportViolation(m.ContractModel):
        cycle: Annotated[
            t.Infra.VariadicTuple[str], m.Field(description="Import cycle chain")
        ]
        files: Annotated[
            t.Infra.VariadicTuple[str],
            m.Field(description="Files in cycle"),
        ] = m.Field(default_factory=tuple)

    class RuntimeAliasViolation(
        FlextInfraModelsMixins.FilePathMixin,
        FlextInfraModelsMixins.NonNegativeLineMixin,
        FlextInfraModelsMixins.ViolationDetailMixin,
        m.ContractModel,
    ):
        kind: Annotated[str, m.Field(description="Violation kind")]
        alias: Annotated[str, m.Field(description="Alias involved")]

    class FutureAnnotationsViolation(
        FlextInfraModelsMixins.FilePathMixin,
        m.ContractModel,
    ):
        pass

    class ManualTypingAliasViolation(
        FlextInfraModelsMixins.ViolationDetailMixin,
        FileLineViolation,
    ):
        name: Annotated[t.NonEmptyStr, m.Field(description="Alias name")]

    class CompatibilityAliasViolation(FileLineViolation):
        alias_name: Annotated[t.NonEmptyStr, m.Field(description="Alias name")]
        target_name: Annotated[t.NonEmptyStr, m.Field(description="Target name")]

    class ParseFailureViolation(
        FlextInfraModelsMixins.FilePathMixin,
        FlextInfraModelsMixins.ErrorDetailMixin,
        m.ContractModel,
    ):
        stage: Annotated[t.NonEmptyStr, m.Field(description="Parse stage")]
        error_type: Annotated[t.NonEmptyStr, m.Field(description="Error type")]

    class ProjectEnforcementReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        project_root: Annotated[str, m.Field(description="Project root path")]
        facade_statuses: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.FacadeStatus],
            m.Field(default_factory=list, description="Facade status list"),
        ]
        loose_objects: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.LooseObjectViolation],
            m.Field(default_factory=list, description="Loose object violations"),
        ]
        import_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ImportAliasViolation],
            m.Field(default_factory=list, description="Import alias violations"),
        ]
        namespace_source_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.NamespaceSourceViolation],
            m.Field(default_factory=list, description="Namespace source violations"),
        ]
        internal_import_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.InternalImportViolation],
            m.Field(default_factory=list, description="Internal import violations"),
        ]
        manual_protocol_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ManualProtocolViolation],
            m.Field(default_factory=list, description="Manual protocol violations"),
        ]
        cyclic_imports: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.CyclicImportViolation],
            m.Field(default_factory=list, description="Cyclic import violations"),
        ]
        runtime_alias_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.RuntimeAliasViolation],
            m.Field(default_factory=list, description="Runtime alias violations"),
        ]
        future_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.FutureAnnotationsViolation],
            m.Field(default_factory=list, description="Future annotations violations"),
        ]
        manual_typing_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ManualTypingAliasViolation],
            m.Field(default_factory=list, description="Manual typing alias violations"),
        ]
        compatibility_alias_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.CompatibilityAliasViolation],
            m.Field(default_factory=list, description="Compatibility alias violations"),
        ]
        class_placement_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ClassPlacementViolation],
            m.Field(default_factory=list, description="Class placement violations"),
        ]
        mro_completeness_violations: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.MROCompletenessViolation],
            m.Field(default_factory=list, description="MRO completeness violations"),
        ]
        parse_failures: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ParseFailureViolation],
            m.Field(default_factory=list, description="Parse failures"),
        ]
        files_scanned: Annotated[
            t.NonNegativeInt, m.Field(description="Files scanned")
        ] = 0

        @property
        def has_violations(self) -> bool:
            """Check if this project has any violations."""
            missing_facades = any(not f.exists for f in self.facade_statuses)
            violation_fields = (
                self.loose_objects,
                self.import_violations,
                self.namespace_source_violations,
                self.internal_import_violations,
                self.manual_protocol_violations,
                self.cyclic_imports,
                self.runtime_alias_violations,
                self.future_violations,
                self.manual_typing_violations,
                self.compatibility_alias_violations,
                self.class_placement_violations,
                self.mro_completeness_violations,
                self.parse_failures,
            )
            return missing_facades or any(v for v in violation_fields)

    class WorkspaceEnforcementReport(m.ArbitraryTypesModel):
        workspace: Annotated[t.NonEmptyStr, m.Field(description="Workspace root path")]
        projects: Annotated[
            Sequence[FlextInfraModelsNamespaceEnforcer.ProjectEnforcementReport],
            m.Field(default_factory=list, description="Project enforcement reports"),
        ]
        total_facades_missing: Annotated[
            t.NonNegativeInt, m.Field(description="Total missing facades")
        ] = 0
        total_loose_objects: Annotated[
            t.NonNegativeInt, m.Field(description="Total loose objects")
        ] = 0
        total_import_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total import violations")
        ] = 0
        total_namespace_source_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total namespace source violations")
        ] = 0
        total_internal_import_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total internal import violations")
        ] = 0
        total_manual_protocol_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total manual protocol violations")
        ] = 0
        total_cyclic_imports: Annotated[
            t.NonNegativeInt, m.Field(description="Total cyclic imports")
        ] = 0
        total_runtime_alias_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total runtime alias violations")
        ] = 0
        total_future_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total future annotations violations")
        ] = 0
        total_manual_typing_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total manual typing violations")
        ] = 0
        total_compatibility_alias_violations: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total compatibility alias violations"),
        ] = 0
        total_class_placement_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total class placement violations")
        ] = 0
        total_mro_completeness_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Total MRO completeness violations")
        ] = 0
        total_parse_failures: Annotated[
            t.NonNegativeInt, m.Field(description="Total parse failures")
        ] = 0
        total_files_scanned: Annotated[
            t.NonNegativeInt, m.Field(description="Total files scanned")
        ] = 0

        @classmethod
        def from_projects(
            cls,
            *,
            workspace: str,
            projects: Sequence[
                FlextInfraModelsNamespaceEnforcer.ProjectEnforcementReport
            ],
        ) -> Self:
            return cls(
                workspace=workspace,
                projects=projects,
                total_facades_missing=sum(
                    1 for p in projects for f in p.facade_statuses if not f.exists
                ),
                total_loose_objects=sum(len(p.loose_objects) for p in projects),
                total_import_violations=sum(len(p.import_violations) for p in projects),
                total_namespace_source_violations=sum(
                    len(p.namespace_source_violations) for p in projects
                ),
                total_internal_import_violations=sum(
                    len(p.internal_import_violations) for p in projects
                ),
                total_manual_protocol_violations=sum(
                    len(p.manual_protocol_violations) for p in projects
                ),
                total_cyclic_imports=sum(len(p.cyclic_imports) for p in projects),
                total_runtime_alias_violations=sum(
                    len(p.runtime_alias_violations) for p in projects
                ),
                total_future_violations=sum(len(p.future_violations) for p in projects),
                total_manual_typing_violations=sum(
                    len(p.manual_typing_violations) for p in projects
                ),
                total_compatibility_alias_violations=sum(
                    len(p.compatibility_alias_violations) for p in projects
                ),
                total_class_placement_violations=sum(
                    len(p.class_placement_violations) for p in projects
                ),
                total_mro_completeness_violations=sum(
                    len(p.mro_completeness_violations) for p in projects
                ),
                total_parse_failures=sum(len(p.parse_failures) for p in projects),
                total_files_scanned=sum(p.files_scanned for p in projects),
            )

        @property
        def has_violations(self) -> bool:
            return any(
                getattr(self, f) > 0
                for f in type(self).model_fields
                if f.startswith("total_") and f != "total_files_scanned"
            )


__all__: list[str] = ["FlextInfraModelsNamespaceEnforcer"]
