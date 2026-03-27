"""CST extraction models — accessed via m.Infra.Cst.*."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, ClassVar

from flext_core import FlextModels
from pydantic import ConfigDict, Field

from flext_infra import t


class FlextInfraModelsCst:
    """Models for CST-based code extraction — accessed via m.Infra.Cst.*."""

    class Cst:
        """Namespace for CST extraction data contracts."""

        class ExtractedBase(FlextModels.ArbitraryTypesModel):
            """A base class reference extracted from a ClassDef."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[
                t.NonEmptyStr,
                Field(description="Base class name as it appears in source"),
            ]
            dotted: Annotated[
                str,
                Field(
                    default="",
                    description="Dotted attribute path (e.g. FlextModels.FrozenStrictModel)",
                ),
            ] = ""

        class ExtractedDecorator(FlextModels.ArbitraryTypesModel):
            """A decorator extracted from a class or function definition."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[
                t.NonEmptyStr,
                Field(
                    description="Decorator name (e.g. staticmethod, runtime_checkable)"
                ),
            ]
            is_call: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether decorator is a call (e.g. @decorator())",
                ),
            ] = False

        class ExtractedMethod(FlextModels.ArbitraryTypesModel):
            """A method extracted from a class definition."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Method name")]
            kind: Annotated[
                str,
                Field(description="Method kind: static, class, instance, property"),
            ]
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]
            decorators: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedDecorator],
                Field(description="Decorators applied to this method"),
            ] = Field(default_factory=lambda: ())

        class ExtractedClass(FlextModels.ArbitraryTypesModel):
            """A class definition extracted from a Python file."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Class name")]
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]
            bases: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedBase],
                Field(description="Base class references"),
            ] = Field(default_factory=lambda: ())
            decorators: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedDecorator],
                Field(description="Class-level decorators"),
            ] = Field(default_factory=lambda: ())
            methods: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedMethod],
                Field(description="Methods defined in this class"),
            ] = Field(default_factory=lambda: ())
            inner_classes: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedClass],
                Field(description="Nested inner class definitions"),
            ] = Field(default_factory=lambda: ())
            is_protocol: Annotated[
                bool,
                Field(
                    default=False, description="Whether class inherits from Protocol"
                ),
            ] = False
            is_model: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether class inherits from BaseModel/TypedDict",
                ),
            ] = False
            is_facade: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether class is a namespace facade (FlextXxxModels, etc.)",
                ),
            ] = False

        class ExtractedAssignment(FlextModels.ArbitraryTypesModel):
            """A module-level assignment extracted from a Python file."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Assignment target name")]
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]
            has_final: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether annotated with typing.Final",
                ),
            ] = False
            has_classvar: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether annotated with typing.ClassVar",
                ),
            ] = False
            is_type_alias: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether annotated with TypeAlias",
                ),
            ] = False
            is_pep695: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether this is a PEP 695 type alias (type X = ...)",
                ),
            ] = False
            is_upper_case: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether name matches UPPER_CASE pattern",
                ),
            ] = False
            value_repr: Annotated[
                str,
                Field(
                    default="",
                    description="Source representation of the assigned value",
                ),
            ] = ""

        class ExtractedFunction(FlextModels.ArbitraryTypesModel):
            """A module-level function extracted from a Python file."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Function name")]
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]
            decorators: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedDecorator],
                Field(description="Function decorators"),
            ] = Field(default_factory=lambda: ())
            is_private: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether name starts with underscore",
                ),
            ] = False

        class ExtractedImport(FlextModels.ArbitraryTypesModel):
            """An import statement extracted from a Python file."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            module: Annotated[
                str,
                Field(description="Imported module path (e.g. flext_core)"),
            ]
            names: Annotated[
                Mapping[str, str],
                Field(
                    description="Mapping of local name → imported name",
                ),
            ] = Field(default_factory=dict)
            is_star: Annotated[
                bool,
                Field(default=False, description="Whether this is a star import"),
            ] = False
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]

        class ExtractedObject(FlextModels.ArbitraryTypesModel):
            """Unified object extracted from a Python file.

            Normalizes classes, assignments, functions, and type aliases
            into a single contract for downstream analysis pipelines.
            """

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Object identifier")]
            kind: Annotated[
                str,
                Field(
                    description="Object kind: class, assignment, function, type_alias",
                ),
            ]
            line: Annotated[
                t.NonNegativeInt, Field(description="Line number (1-based)")
            ]
            # Classification signals
            bases: Annotated[
                Sequence[str],
                Field(description="Base class names (for classes)"),
            ] = Field(default_factory=lambda: ())
            has_final: Annotated[
                bool,
                Field(default=False, description="Has Final annotation"),
            ] = False
            has_classvar: Annotated[
                bool,
                Field(default=False, description="Has ClassVar annotation"),
            ] = False
            is_type_alias: Annotated[
                bool,
                Field(
                    default=False, description="Is a type alias (PEP 695 or TypeAlias)"
                ),
            ] = False
            is_protocol: Annotated[
                bool,
                Field(default=False, description="Inherits from Protocol"),
            ] = False
            is_model: Annotated[
                bool,
                Field(default=False, description="Inherits from BaseModel/TypedDict"),
            ] = False
            is_facade: Annotated[
                bool,
                Field(default=False, description="Is a namespace facade class"),
            ] = False
            is_upper_case: Annotated[
                bool,
                Field(default=False, description="Name matches UPPER_CASE pattern"),
            ] = False
            is_private: Annotated[
                bool,
                Field(default=False, description="Name starts with underscore"),
            ] = False
            class_path: Annotated[
                str,
                Field(
                    default="",
                    description="Dotted path within parent class (e.g. Auth.DEFAULT_TIMEOUT)",
                ),
            ] = ""

        class FileResult(FlextModels.ArbitraryTypesModel):
            """Complete extraction result for a single Python file."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            file_path: Annotated[str, Field(description="Absolute file path")]
            project: Annotated[t.NonEmptyStr, Field(description="Project name")]
            classes: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedClass],
                Field(description="Extracted class definitions"),
            ] = Field(default_factory=lambda: ())
            assignments: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedAssignment],
                Field(description="Extracted assignments"),
            ] = Field(default_factory=lambda: ())
            functions: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedFunction],
                Field(description="Extracted module-level functions"),
            ] = Field(default_factory=lambda: ())
            imports: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedImport],
                Field(description="Extracted import statements"),
            ] = Field(default_factory=lambda: ())
            objects: Annotated[
                Sequence[FlextInfraModelsCst.Cst.ExtractedObject],
                Field(description="Unified extracted objects"),
            ] = Field(default_factory=lambda: ())
            parse_error: Annotated[
                str,
                Field(default="", description="Parse error message if file failed"),
            ] = ""


__all__ = ["FlextInfraModelsCst"]
