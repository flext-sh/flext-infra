"""CST extraction utilities — accessed via u.Infra.*."""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, m


class FlextInfraUtilitiesCst:
    """Generic libcst extraction and analysis utilities — accessed via u.Infra.*."""

    # ── Parsing ─────────────────────────────────────────────────────

    @staticmethod
    def cst_parse_file(file_path: Path) -> cst.Module | None:
        """Parse a Python file into a libcst Module.

        Returns None on syntax errors or IO errors.
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            return cst.parse_module(source)
        except (cst.ParserSyntaxError, SyntaxError, UnicodeDecodeError, OSError):
            return None

    @staticmethod
    def cst_parse_source(source: str) -> cst.Module | None:
        """Parse a source string into a libcst Module.

        Returns None on syntax errors.
        """
        try:
            return cst.parse_module(source)
        except (cst.ParserSyntaxError, SyntaxError):
            return None

    # ── Name extraction ─────────────────────────────────────────────

    @staticmethod
    def cst_dotted_name(expr: cst.BaseExpression) -> str:
        """Extract dotted name string from a CST expression.

        Examples:
            Name("foo") → "foo"
            Attribute(Name("foo"), "bar") → "foo.bar"
            Call(Name("foo")) → "foo"

        """
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            left = FlextInfraUtilitiesCst.cst_dotted_name(expr.value)
            return f"{left}.{expr.attr.value}" if left else expr.attr.value
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesCst.cst_dotted_name(expr.func)
        if isinstance(expr, cst.Subscript):
            return FlextInfraUtilitiesCst.cst_dotted_name(expr.value)
        return ""

    @staticmethod
    def cst_simple_name(expr: cst.BaseExpression) -> str:
        """Extract the rightmost simple name from a CST expression.

        Examples:
            Name("foo") → "foo"
            Attribute(Name("foo"), "bar") → "bar"

        """
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return expr.attr.value
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesCst.cst_simple_name(expr.func)
        if isinstance(expr, cst.Subscript):
            return FlextInfraUtilitiesCst.cst_simple_name(expr.value)
        return ""

    @staticmethod
    def cst_root_name(expr: cst.BaseExpression) -> str:
        """Extract the leftmost root name from a CST expression.

        Examples:
            Name("foo") → "foo"
            Attribute(Name("foo"), "bar") → "foo"

        """
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return FlextInfraUtilitiesCst.cst_root_name(expr.value)
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesCst.cst_root_name(expr.func)
        return ""

    # ── Annotation detection ────────────────────────────────────────

    @staticmethod
    def cst_has_annotation(
        annotation: cst.BaseExpression,
        names: frozenset[str],
    ) -> bool:
        """Check if an annotation references any of the given names.

        Handles: Name("Final"), Subscript(Name("Final"), ...), Attribute(x, "Final").
        """
        simple = FlextInfraUtilitiesCst.cst_simple_name(annotation)
        return simple in names

    @staticmethod
    def cst_is_final(annotation: cst.Annotation) -> bool:
        """Check if annotation is typing.Final or typing.Final[T]."""
        return FlextInfraUtilitiesCst.cst_has_annotation(
            annotation.annotation,
            c.Infra.Cst.CONSTANT_ANNOTATIONS,
        )

    @staticmethod
    def cst_is_type_alias_annotation(annotation: cst.Annotation) -> bool:
        """Check if annotation is typing.TypeAlias."""
        return FlextInfraUtilitiesCst.cst_has_annotation(
            annotation.annotation,
            c.Infra.Cst.TYPE_ANNOTATIONS,
        )

    # ── Decorator extraction ────────────────────────────────────────

    @staticmethod
    def cst_extract_decorators(
        decorators: Sequence[cst.Decorator],
    ) -> Sequence[m.Infra.Cst.ExtractedDecorator]:
        """Extract decorator metadata from a sequence of CST Decorator nodes."""
        result: MutableSequence[m.Infra.Cst.ExtractedDecorator] = []
        for dec in decorators:
            name = FlextInfraUtilitiesCst.cst_dotted_name(dec.decorator)
            if name:
                result.append(
                    m.Infra.Cst.ExtractedDecorator(
                        name=name,
                        is_call=isinstance(dec.decorator, cst.Call),
                    )
                )
        return result

    # ── Base class extraction ───────────────────────────────────────

    @staticmethod
    def cst_extract_bases(
        bases: Sequence[cst.Arg],
    ) -> Sequence[m.Infra.Cst.ExtractedBase]:
        """Extract base class references from ClassDef.bases."""
        result: MutableSequence[m.Infra.Cst.ExtractedBase] = []
        for arg in bases:
            if arg.keyword is not None:
                continue  # Skip metaclass= and other keyword args
            dotted = FlextInfraUtilitiesCst.cst_dotted_name(arg.value)
            simple = FlextInfraUtilitiesCst.cst_simple_name(arg.value)
            if simple:
                result.append(
                    m.Infra.Cst.ExtractedBase(
                        name=simple,
                        dotted=dotted,
                    )
                )
        return result

    # ── Constant name detection ─────────────────────────────────────

    _CONSTANT_RE: re.Pattern[str] = re.compile(r"^_?[A-Z][A-Z0-9_]+$")

    @staticmethod
    def cst_is_upper_case_name(name: str) -> bool:
        """Check if a name matches UPPER_CASE constant pattern."""
        return bool(FlextInfraUtilitiesCst._CONSTANT_RE.match(name))

    # ── Facade detection ────────────────────────────────────────────

    @staticmethod
    def cst_is_facade_class(name: str) -> bool:
        """Check if a class name looks like a namespace facade.

        Matches: FlextXxxConstants, FlextXxxModels, FlextXxxUtilities, etc.
        """
        if not name.startswith(c.Infra.Cst.FACADE_PREFIX):
            return False
        return any(name.endswith(suffix) for suffix in c.Infra.Cst.FACADE_SUFFIXES)

    # ── Method kind detection ───────────────────────────────────────

    @staticmethod
    def cst_method_kind(decorators: Sequence[cst.Decorator]) -> str:
        """Determine method kind from its decorators."""
        for dec in decorators:
            name = FlextInfraUtilitiesCst.cst_dotted_name(dec.decorator)
            if name in c.Infra.Cst.STATIC_DECORATORS:
                return c.Infra.Cst.METHOD_STATIC
            if name in c.Infra.Cst.CLASS_DECORATORS:
                return c.Infra.Cst.METHOD_CLASS
            if name in c.Infra.Cst.PROPERTY_DECORATORS:
                return c.Infra.Cst.METHOD_PROPERTY
        return c.Infra.Cst.METHOD_INSTANCE

    # ── Base class classification helpers ───────────────────────────

    @staticmethod
    def cst_has_protocol_base(bases: Sequence[m.Infra.Cst.ExtractedBase]) -> bool:
        """Check if any base class is a Protocol."""
        return any(b.name in c.Infra.Cst.PROTOCOL_BASES for b in bases)

    @staticmethod
    def cst_has_model_base(bases: Sequence[m.Infra.Cst.ExtractedBase]) -> bool:
        """Check if any base class is a BaseModel/TypedDict/etc."""
        return any(b.name in c.Infra.Cst.MODEL_BASES for b in bases)

    # ── File extraction ─────────────────────────────────────────────

    @staticmethod
    def cst_extract_file(
        file_path: Path,
        project_name: str,
    ) -> m.Infra.Cst.FileResult:
        """Extract all objects from a single Python file.

        Parses the file with libcst and walks top-level statements
        to extract classes, assignments, functions, imports, and
        unified objects.

        Args:
            file_path: Absolute path to the Python file.
            project_name: Name of the containing project.

        Returns:
            FileResult with extracted objects (or parse_error set on failure).

        """
        module = FlextInfraUtilitiesCst.cst_parse_file(file_path)
        if module is None:
            return m.Infra.Cst.FileResult(
                file_path=str(file_path),
                project=project_name,
                parse_error=f"Failed to parse {file_path}",
            )

        visitor = _CstFileExtractorVisitor(
            file_path=file_path,
            project_name=project_name,
        )
        module.visit(visitor)

        return m.Infra.Cst.FileResult(
            file_path=str(file_path),
            project=project_name,
            classes=visitor.classes,
            assignments=visitor.assignments,
            functions=visitor.functions,
            imports=visitor.imports,
            objects=visitor.objects,
        )

    @staticmethod
    def cst_extract_workspace(
        workspace_root: Path,
        *,
        project_names: Sequence[str] | None = None,
        project_prefix: str = "flext-",
        src_dir: str = "src",
    ) -> Sequence[m.Infra.Cst.FileResult]:
        """Extract objects from all Python files across workspace projects.

        Args:
            workspace_root: Root of the monorepo workspace.
            project_names: Optional filter for specific projects.
            project_prefix: Prefix for project directories.
            src_dir: Subdirectory containing source code.

        Returns:
            Sequence of FileResult, one per parsed file.

        """
        results: MutableSequence[m.Infra.Cst.FileResult] = []
        for project_dir in sorted(workspace_root.iterdir()):
            if not project_dir.name.startswith(project_prefix):
                continue
            if project_names and project_dir.name not in project_names:
                continue
            src_path = project_dir / src_dir
            if not src_path.is_dir():
                continue
            for py_file in sorted(src_path.rglob("*.py")):
                if py_file.name in c.Infra.Cst.SKIP_FILES:
                    continue
                if any(skip in py_file.parts for skip in c.Infra.Cst.SKIP_DIRS):
                    continue
                result = FlextInfraUtilitiesCst.cst_extract_file(
                    py_file,
                    project_dir.name,
                )
                results.append(result)
        return results


# ── Private visitor ─────────────────────────────────────────────────


class _CstFileExtractorVisitor(cst.CSTVisitor):
    """Walk top-level statements and extract all objects."""

    def __init__(
        self,
        *,
        file_path: Path,
        project_name: str,
    ) -> None:
        super().__init__()
        self._file_path = file_path
        self._project = project_name
        self._depth = 0
        self._class_stack: MutableSequence[str] = []

        self.classes: MutableSequence[m.Infra.Cst.ExtractedClass] = []
        self.assignments: MutableSequence[m.Infra.Cst.ExtractedAssignment] = []
        self.functions: MutableSequence[m.Infra.Cst.ExtractedFunction] = []
        self.imports: MutableSequence[m.Infra.Cst.ExtractedImport] = []
        self.objects: MutableSequence[m.Infra.Cst.ExtractedObject] = []

    # -- Class extraction -------------------------------------------------

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        bases = FlextInfraUtilitiesCst.cst_extract_bases(node.bases)
        decorators = FlextInfraUtilitiesCst.cst_extract_decorators(node.decorators)
        is_protocol = FlextInfraUtilitiesCst.cst_has_protocol_base(bases)
        is_model = FlextInfraUtilitiesCst.cst_has_model_base(bases)
        is_facade = FlextInfraUtilitiesCst.cst_is_facade_class(node.name.value)

        methods: MutableSequence[m.Infra.Cst.ExtractedMethod] = []
        for stmt in _iter_body_statements(node.body):
            if isinstance(stmt, cst.FunctionDef):
                kind = FlextInfraUtilitiesCst.cst_method_kind(stmt.decorators)
                method_decs = FlextInfraUtilitiesCst.cst_extract_decorators(
                    stmt.decorators,
                )
                methods.append(
                    m.Infra.Cst.ExtractedMethod(
                        name=stmt.name.value,
                        kind=kind,
                        line=0,
                        decorators=method_decs,
                    )
                )

        extracted = m.Infra.Cst.ExtractedClass(
            name=node.name.value,
            line=0,
            bases=bases,
            decorators=decorators,
            methods=methods,
            is_protocol=is_protocol,
            is_model=is_model,
            is_facade=is_facade,
        )

        if self._depth == 0:
            self.classes.append(extracted)
            class_path = node.name.value if self._class_stack else ""
            base_names = [b.name for b in bases]
            self.objects.append(
                m.Infra.Cst.ExtractedObject(
                    name=node.name.value,
                    kind="class",
                    line=0,
                    bases=base_names,
                    is_protocol=is_protocol,
                    is_model=is_model,
                    is_facade=is_facade,
                    class_path=class_path,
                )
            )

        self._depth += 1
        self._class_stack.append(node.name.value)
        return True

    @override
    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        self._depth -= 1
        if self._class_stack:
            self._class_stack.pop()

    # -- Assignment extraction --------------------------------------------

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool:
        if self._depth > 0:
            return False
        if not isinstance(node.target, cst.Name):
            return False
        name = node.target.value
        has_final = FlextInfraUtilitiesCst.cst_is_final(node.annotation)
        is_ta = FlextInfraUtilitiesCst.cst_is_type_alias_annotation(node.annotation)
        is_upper = FlextInfraUtilitiesCst.cst_is_upper_case_name(name)
        has_classvar = FlextInfraUtilitiesCst.cst_has_annotation(
            node.annotation.annotation,
            frozenset({c.Infra.Cst.CLASSVAR}),
        )

        self.assignments.append(
            m.Infra.Cst.ExtractedAssignment(
                name=name,
                line=0,
                has_final=has_final,
                has_classvar=has_classvar,
                is_type_alias=is_ta,
                is_upper_case=is_upper,
            )
        )
        self.objects.append(
            m.Infra.Cst.ExtractedObject(
                name=name,
                kind="type_alias" if is_ta else "assignment",
                line=0,
                has_final=has_final,
                has_classvar=has_classvar,
                is_type_alias=is_ta,
                is_upper_case=is_upper,
            )
        )
        return False

    @override
    def visit_Assign(self, node: cst.Assign) -> bool:
        if self._depth > 0:
            return False
        if len(node.targets) != 1:
            return False
        target = node.targets[0].target
        if not isinstance(target, cst.Name):
            return False
        name = target.value
        is_upper = FlextInfraUtilitiesCst.cst_is_upper_case_name(name)

        self.assignments.append(
            m.Infra.Cst.ExtractedAssignment(
                name=name,
                line=0,
                is_upper_case=is_upper,
            )
        )
        self.objects.append(
            m.Infra.Cst.ExtractedObject(
                name=name,
                kind="assignment",
                line=0,
                is_upper_case=is_upper,
            )
        )
        return False

    # -- PEP 695 type alias -----------------------------------------------

    @override
    def visit_TypeAlias(self, node: cst.TypeAlias) -> bool:
        if self._depth > 0:
            return False
        name = node.name.value
        if not name:
            return False

        self.assignments.append(
            m.Infra.Cst.ExtractedAssignment(
                name=name,
                line=0,
                is_pep695=True,
                is_type_alias=True,
            )
        )
        self.objects.append(
            m.Infra.Cst.ExtractedObject(
                name=name,
                kind="type_alias",
                line=0,
                is_type_alias=True,
            )
        )
        return False

    # -- Function extraction ----------------------------------------------

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        if self._depth > 0:
            return False
        decorators = FlextInfraUtilitiesCst.cst_extract_decorators(node.decorators)
        is_private = node.name.value.startswith("_")

        self.functions.append(
            m.Infra.Cst.ExtractedFunction(
                name=node.name.value,
                line=0,
                decorators=decorators,
                is_private=is_private,
            )
        )
        self.objects.append(
            m.Infra.Cst.ExtractedObject(
                name=node.name.value,
                kind="function",
                line=0,
                is_private=is_private,
            )
        )
        return False

    # -- Import extraction ------------------------------------------------

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if node.module is None:
            return False
        module_str = FlextInfraUtilitiesCst.cst_dotted_name(node.module)
        if not module_str:
            return False

        if isinstance(node.names, cst.ImportStar):
            self.imports.append(
                m.Infra.Cst.ExtractedImport(
                    module=module_str,
                    is_star=True,
                    line=0,
                )
            )
            return False

        names: dict[str, str] = {}
        for alias in node.names:
            imported = alias.name.value if isinstance(alias.name, cst.Name) else ""
            local = imported
            if alias.asname is not None:
                asname_node = alias.asname.name
                if isinstance(asname_node, cst.Name):
                    local = asname_node.value
            if imported:
                names[local] = imported
        self.imports.append(
            m.Infra.Cst.ExtractedImport(
                module=module_str,
                names=names,
                line=0,
            )
        )
        return False


def _iter_body_statements(
    body: cst.BaseSuite,
) -> Sequence[cst.BaseStatement | cst.BaseSmallStatement]:
    """Yield all direct statements from a class/function body."""
    if isinstance(body, cst.IndentedBlock):
        result: MutableSequence[cst.BaseStatement | cst.BaseSmallStatement] = []
        for stmt in body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                result.extend(stmt.body)
            else:
                result.append(stmt)
        return result
    return []


__all__ = ["FlextInfraUtilitiesCst"]
