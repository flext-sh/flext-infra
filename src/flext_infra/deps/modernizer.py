"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.deps._modernizer_constraints import (
    FlextInfraPyprojectModernizerConstraintsMixin,
)
from flext_infra.deps._modernizer_document import (
    FlextInfraPyprojectModernizerDocumentMixin,
)
from flext_infra.deps._modernizer_payload import (
    FlextInfraPyprojectModernizerPayloadMixin,
)
from flext_infra.deps._modernizer_run import FlextInfraPyprojectModernizerRunMixin
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPyprojectModernizer(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraPyprojectModernizerConstraintsMixin,
    FlextInfraPyprojectModernizerPayloadMixin,
    FlextInfraPyprojectModernizerDocumentMixin,
    FlextInfraPyprojectModernizerRunMixin,
):
    """Modernize all workspace pyproject.toml files."""

    audit: Annotated[
        bool, m.Field(False, description="Audit pyproject changes without writing")
    ] = False
    skip_check: Annotated[
        bool, m.Field(alias="skip-check", description="Skip post-write validation")
    ] = False
    skip_comments: Annotated[
        bool, m.Field(alias="skip-comments", description="Skip managed comment updates")
    ] = False
    rewrite_constraints: Annotated[
        bool,
        m.Field(
            alias="rewrite-constraints",
            description="Rewrite dependency constraints from uv.lock",
        ),
    ] = False
    constraint_policy: Annotated[
        c.Infra.DependencyConstraintPolicy,
        m.Field(
            alias="constraint-policy",
            description="Policy used when rewriting dependency constraints",
        ),
        m.BeforeValidator(
            lambda v: (
                c.Infra.DependencyConstraintPolicy(v.strip().lower())
                if isinstance(v, str)
                else v
            )
        ),
    ] = c.Infra.DependencyConstraintPolicy.FLOOR

    def conform_source(
        self, source: str, *, path: Path, declared_python_dirs: t.StrSequence = ()
    ) -> p.Result[str]:
        """Return one canonical pyproject using the same phases as workspace apply."""
        payload_source = u.Cli.toml_mapping_from_text(source)
        if payload_source is None:
            return r[str].fail(f"invalid TOML: {path}")
        try:
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
                payload_source
            )
            canonical_dev = t.Infra.STR_SEQ_ADAPTER.validate_python(
                u.Infra.canonical_dev_dependencies_from_payload(payload)
            )
        except c.ValidationError as exc:
            return r[str].fail_op("pyproject model validation", exc)
        state = m.Infra.PyprojectDocumentState(
            pyproject_path=path, original_rendered=source, payload=payload
        )
        # mro-j47u (codex): atomic scaffolds provide validated future roots;
        # existing repositories keep filesystem discovery through the empty default.
        self._process_document_state(
            state,
            canonical_dev=canonical_dev,
            dry_run=True,
            skip_comments=False,
            declared_python_dirs=declared_python_dirs,
        )
        if not state.rendered:
            return r[str].fail(f"pyproject tooling render failed: {path}")
        return r[str].ok(state.rendered)

    def resolve_tooling_context(
        self,
        *,
        project_name: t.NonEmptyStr,
        package_name: t.NonEmptyStr,
        path: Path,
        declared_python_dirs: t.StrSequence = (),
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Resolve typed project/workspace values for the complete Jinja template."""
        # mro-j47u (codex): resolve values only; template retains the full structure.
        seed = u.Cli.toml_document()
        project = u.Cli.toml_table()
        project.add(c.Infra.NAME, project_name)
        seed.add(c.Infra.PROJECT, project)
        tool = u.Cli.toml_table()
        flext = u.Cli.toml_table()
        docs = u.Cli.toml_table()
        docs.add("package_name", package_name)
        flext.add("docs", docs)
        tool.add("flext", flext)
        seed.add(c.Infra.TOOL, tool)
        # NOTE(mro-p68a.5, agent codex): resolve from the declared future roots
        # so first generation and post-write conformance are the same fixed point.
        conformed = self.conform_source(
            u.Cli.toml_dumps(seed), path=path, declared_python_dirs=declared_python_dirs
        )
        if conformed.failure:
            return r[m.Infra.ToolingRuntimeContext].fail(
                conformed.error or f"tooling resolution failed: {path}"
            )
        payload = u.Cli.toml_mapping_from_text(conformed.value)
        if payload is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution produced invalid TOML: {path}"
            )
        tooling = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tooling is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution produced no [tool] table: {path}"
            )
        coverage = u.Cli.toml_mapping_path(tooling, ("coverage", "report"))
        deptry = u.Cli.toml_mapping_child(tooling, "deptry")
        mypy = u.Cli.toml_mapping_child(tooling, c.Infra.MYPY)
        pyrefly = u.Cli.toml_mapping_child(tooling, c.Infra.PYREFLY)
        pyright = u.Cli.toml_mapping_child(tooling, c.Infra.PYRIGHT)
        ruff = u.Cli.toml_mapping_child(tooling, c.Infra.RUFF)
        ruff_lint = (
            u.Cli.toml_mapping_child(ruff, c.Infra.LINT_SECTION)
            if ruff is not None
            else None
        )
        ruff_isort = (
            u.Cli.toml_mapping_path(ruff, ("lint", "isort"))
            if ruff is not None
            else None
        )
        if coverage is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted coverage.report: {path}"
            )
        if deptry is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted deptry: {path}"
            )
        if mypy is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted mypy: {path}"
            )
        if pyrefly is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted pyrefly: {path}"
            )
        if pyright is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted pyright: {path}"
            )
        if ruff is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted ruff: {path}"
            )
        if ruff_lint is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted ruff.lint: {path}"
            )
        if ruff_isort is None:
            return r[m.Infra.ToolingRuntimeContext].fail(
                f"tooling resolution omitted ruff.lint.isort: {path}"
            )
        scalar_keys = frozenset({
            c.Infra.EXCLUDE,
            c.Infra.IGNORE,
            c.Infra.INCLUDE,
            c.Infra.EXTRA_PATHS,
            "executionEnvironments",
            "venv",
            "venvPath",
        })
        raw_environments = u.Cli.json_as_sequence(pyright.get("executionEnvironments"))
        if declared_python_dirs:
            raw_environments = FlextInfraEnsurePyrightConfigPhase(
                config.Infra.tooling
            ).environment_payloads_for_dirs(declared_python_dirs)
        declared_pyrefly_includes = (
            FlextInfraExtraPathsManager.pyrefly_include_globs(declared_python_dirs)
            if declared_python_dirs
            else ()
        )
        project_kind = "core"
        if path.parent.resolve() != self.root.resolve() or self._project_is_flext_child(
            path.parent
        ):
            classified = self._classify_project(path.parent, payload=payload)
            if classified.failure:
                return r[m.Infra.ToolingRuntimeContext].fail(
                    classified.error or f"project classification failed: {path}"
                )
            project_kind = classified.value
        try:
            environments = self._tooling_pyright_environments(raw_environments)
            runtime = m.Infra.ToolingRuntimeContext.model_validate({
                "project_kind": project_kind,
                "coverage_fail_under": coverage.get("fail_under"),
                "first_party": ruff_isort.get("known-first-party"),
                "mypy_path": mypy.get("mypy_path"),
                "pyrefly_interpreter_path": pyrefly.get("python-interpreter-path"),
                "pyrefly_search_path": pyrefly.get(c.Infra.SEARCH_PATH),
                "pyrefly_project_includes": (
                    declared_pyrefly_includes or pyrefly.get(c.Infra.PROJECT_INCLUDES)
                ),
                "pyright_exclude": pyright.get(c.Infra.EXCLUDE),
                "pyright_ignore": pyright.get(c.Infra.IGNORE, ()),
                "pyright_include": (
                    declared_python_dirs or pyright.get(c.Infra.INCLUDE)
                ),
                "pyright_extra_paths": pyright.get(c.Infra.EXTRA_PATHS),
                "pyright_venv": pyright.get("venv"),
                "pyright_venv_path": pyright.get("venvPath"),
                "pyright_settings": [
                    {"name": key, "value": value}
                    for key, value in sorted(pyright.items())
                    if key not in scalar_keys
                ],
                "pyright_execution_environments": environments,
                "ruff_src": ruff.get("src"),
                "ruff_ignore": ruff_lint.get(c.Infra.IGNORE),
            })
        except c.ValidationError as exc:
            return r[m.Infra.ToolingRuntimeContext].fail_op(
                "tooling runtime context validation", exc
            )
        return r[m.Infra.ToolingRuntimeContext].ok(runtime)

    @staticmethod
    def _tooling_pyright_environments(
        raw_environments: t.SequenceOf[t.JsonValue],
    ) -> t.SequenceOf[m.Infra.ToolingPyrightEnvironment]:
        """Validate Pyright environments once into their canonical models."""
        # mro-j47u: nested tooling data crosses the TOML boundary as models, not dicts.
        environments: t.MutableSequenceOf[m.Infra.ToolingPyrightEnvironment] = []
        excluded = frozenset({"root", c.Infra.EXTRA_PATHS})
        for raw_environment in raw_environments:
            environment = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_environment)
            environments.append(
                m.Infra.ToolingPyrightEnvironment.model_validate({
                    "root": environment.get("root"),
                    "extra_paths": environment.get(c.Infra.EXTRA_PATHS, ()),
                    "settings": tuple(
                        m.Infra.ToolingScalarSetting.model_validate({
                            "name": key,
                            "value": value,
                        })
                        for key, value in sorted(environment.items())
                        if key not in excluded
                    ),
                })
            )
        return tuple(environments)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute pyproject modernization for the configured workspace."""
        exit_code = self.run()
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPyprojectModernizer"]
