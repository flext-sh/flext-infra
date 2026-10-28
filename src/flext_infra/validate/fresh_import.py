"""Verify published exports and real entrypoints in fresh child processes.

The ``fresh-import`` check gate runs this guard in the checkout's provisioned
runtime. Each entrypoint loads before any package smoke so cached imports cannot hide
consumer-order defects. Imported workspace modules must belong to this checkout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from collections.abc import Iterable, Mapping, MutableSequence, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, get_type_hints, override

from flext_infra import FlextInfraServiceBase, c, config, m, p, r, settings, t, u


class FlextInfraValidateFreshImport(FlextInfraServiceBase[bool]):
    """Verify consumers and publication contracts without inherited import state."""

    packages: Annotated[
        Sequence[str],
        m.Field(description="Packages to validate in fresh subprocesses"),
    ] = (c.Infra.PKG_CORE_UNDERSCORE, "flext_infra", "flext_tests")
    runtime_root: Annotated[
        Path | None,
        m.Field(
            description=(
                "Declared runtime root whose environment runs the probes; "
                "undeclared, the target checkout's own environment"
            ),
        ),
    ] = m.Field(
        default_factory=lambda: type(settings).fetch_global().Infra.runtime_root
    )

    def build_report(
        self,
        packages: Sequence[str] = (),
        *,
        publications: Sequence[m.Infra.LazyInitPlan] = (),
        repository_roots: Sequence[Path] = (),
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate complete publications, stopping at the first causal failure.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        layouts_result = self._project_layouts(repository_roots)
        if layouts_result.failure:
            return r[m.Infra.ValidationReport].from_failure(layouts_result)
        layouts = layouts_result.value
        origin_code = self._origin_code(layouts)
        probes: MutableSequence[m.Infra.FreshImportProbe] = []
        for layout in layouts:
            built = self._layout_probes(layout, origin_code, publications)
            if built.failure:
                return r[m.Infra.ValidationReport].from_failure(built)
            probes.extend(built.value)
        packaged = self._package_probes(packages, origin_code)
        if packaged.failure:
            return r[m.Infra.ValidationReport].from_failure(packaged)
        probes.extend(packaged.value)
        if not probes:
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=True,
                    violations=(),
                    summary="0 fresh-import probe(s) passed",
                ),
            )
        return self._execute_probes(probes, layouts)

    @staticmethod
    def _project_layouts(
        repository_roots: Sequence[Path],
    ) -> p.Result[tuple[m.Infra.RopeProjectLayout, ...]]:
        """Resolve one Rope layout per requested repository root.

        Returns:
            The resulting project layouts.

        """
        layouts: MutableSequence[m.Infra.RopeProjectLayout] = []
        for root in repository_roots:
            layout = u.Infra.layout(root)
            if layout is None:
                return r[tuple[m.Infra.RopeProjectLayout, ...]].fail(
                    f"fresh-import has no Python layout for {root}",
                )
            layouts.append(layout)
        return r[tuple[m.Infra.RopeProjectLayout, ...]].ok(tuple(layouts))

    @staticmethod
    def _origin_code(layouts: Sequence[m.Infra.RopeProjectLayout]) -> str:
        """Render the origin-containment guard code for the probed layouts.

        Returns:
            The origin guard source injected into every probe.

        """
        origins = tuple(
            (layout.package_name, str(layout.package_dir.resolve()))
            for layout in layouts
        )
        return c.Infra.FRESH_IMPORT_ORIGIN_CODE.replace(
            c.Infra.FRESH_IMPORT_ORIGINS_PLACEHOLDER,
            repr(origins),
        )

    def _layout_probes(
        self,
        layout: m.Infra.RopeProjectLayout,
        origin_code: str,
        publications: Sequence[m.Infra.LazyInitPlan],
    ) -> p.Result[MutableSequence[m.Infra.FreshImportProbe]]:
        """Build one layout's entry-point and export probes.

        Returns:
            The resulting probes for the layout.

        """
        source = u.Cli.files_read_text(layout.project_root / c.PYPROJECT_FILENAME)
        if source.failure:
            return r[MutableSequence[m.Infra.FreshImportProbe]].from_failure(source)
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[MutableSequence[m.Infra.FreshImportProbe]].fail(
                f"invalid published pyproject in {layout.project_root}",
            )
        metadata = m.Infra.FreshImportMetadata.model_validate(payload).project
        probes = self._entry_point_probes(layout, metadata, origin_code)
        export = self._export_probe(layout, origin_code, publications)
        if export.failure:
            return r[MutableSequence[m.Infra.FreshImportProbe]].from_failure(export)
        probes.append(export.value)
        return r[MutableSequence[m.Infra.FreshImportProbe]].ok(probes)

    @staticmethod
    def _entry_point_probes(
        layout: m.Infra.RopeProjectLayout,
        metadata: m.Infra.FreshImportEntryPoints,
        origin_code: str,
    ) -> MutableSequence[m.Infra.FreshImportProbe]:
        """Build one probe per declared console, GUI, and entry point.

        Returns:
            The entry-point probes of the layout.

        """
        groups: list[tuple[str, Mapping[str, str]]] = []
        if metadata.scripts is not None:
            groups.append(("console_scripts", metadata.scripts))
        if metadata.gui_scripts is not None:
            groups.append(("gui_scripts", metadata.gui_scripts))
        if metadata.entry_points is not None:
            groups.extend(metadata.entry_points.items())
        probes: MutableSequence[m.Infra.FreshImportProbe] = []
        for group, entries in groups:
            for name, value in entries.items():
                probes.append(
                    m.Infra.FreshImportProbe(
                        subject=f"{layout.package_name}: {group}/{name}={value}",
                        code=(
                            c.Infra.FRESH_IMPORT_PRELUDE + f"EntryPoint(name={name!r}, "
                            f"value={value!r}, group={group!r}).load()\n" + origin_code
                        ),
                    ),
                )
        return probes

    @staticmethod
    def _export_probe(
        layout: m.Infra.RopeProjectLayout,
        origin_code: str,
        publications: Sequence[m.Infra.LazyInitPlan],
    ) -> p.Result[m.Infra.FreshImportProbe]:
        """Build one layout's public-export probe from its plan contract.

        A publication plan describes a package the generation rewrote. The
        lazy-init planner only covers the packages of a single Rope workspace
        index, so a workspace root plans its own packages while a generation
        that also declares member repositories
        leaves those members planless (their initializers are owned by their
        own self-scoped runs). A layout no plan claims is therefore verified
        against its real on-disk contract: import it in the fresh runtime and
        resolve the exports it declares. A plan that does claim the layout
        must still carry an importable, non-removal contract, and a
        broken live package fails on its import or on a declared name that
        cannot resolve.

        Returns:
            The resulting export probe of the layout.

        """
        layout_plans = tuple(
            plan
            for plan in publications
            if plan.context.pkg_dir.is_relative_to(layout.package_dir)
        )
        if layout_plans:
            owned = tuple(
                plan
                for plan in layout_plans
                if plan.context.importable
                and plan.action != c.Infra.LazyInitAction.REMOVE
            )
            if not any(plan.context.pkg_dir == layout.package_dir for plan in owned):
                return r[m.Infra.FreshImportProbe].fail(
                    f"missing public export contract for {layout.package_name}",
                )
            body = "".join(
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=plan.context.current_pkg
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(
                    exports=tuple(plan.exports)
                )
                for plan in owned
            )
        else:
            body = (
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=layout.package_name
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(exports=())
            )
        return r[m.Infra.FreshImportProbe].ok(
            m.Infra.FreshImportProbe(
                subject=layout.package_name,
                code=c.Infra.FRESH_IMPORT_PRELUDE + body + origin_code,
            ),
        )

    @staticmethod
    def _package_probes(
        packages: Sequence[str],
        origin_code: str,
    ) -> p.Result[MutableSequence[m.Infra.FreshImportProbe]]:
        """Build one whole-package import probe per declared package name.

        Returns:
            The resulting package probes.

        """
        probes: MutableSequence[m.Infra.FreshImportProbe] = []
        for package in packages:
            if not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(package):
                return r[MutableSequence[m.Infra.FreshImportProbe]].fail(
                    f"{package}: not a valid Python package name",
                )
            probes.append(
                m.Infra.FreshImportProbe(
                    subject=package,
                    code=c.Infra.FRESH_IMPORT_PRELUDE
                    + c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(package=package)
                    + origin_code
                    + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(exports=()),
                ),
            )
        return r[MutableSequence[m.Infra.FreshImportProbe]].ok(probes)

    def _execute_probes(
        self,
        probes: Sequence[m.Infra.FreshImportProbe],
        layouts: Sequence[m.Infra.RopeProjectLayout],
    ) -> p.Result[m.Infra.ValidationReport]:
        """Run every probe in the declared runtime and judge the outcomes.

        The probes execute the target checkout's code, so they run in the
        declared runtime root's environment (the generated Makefile's
        RUNTIME_ROOT), never the one hosting this tool: probing with the
        host's dependency set would grade the target against packages it
        does not install.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        workers = config.Infra.codegen.fresh_import_workers
        u.Cli.info(f"fresh-import: running {len(probes)} probes with {workers} workers")

        # Each source travels on stdin because the workspace export probe may
        # exceed the kernel's single-argument limit. map preserves report order.
        # ``-B``: a validator never writes into the checkout it validates, so
        # the probed sources leave no bytecode cache behind.
        def run_probe(probe: m.Infra.FreshImportProbe) -> p.Result[p.Cli.CommandOutput]:
            return self.execute_probe(
                probe,
                source_roots=tuple(layout.src_dir for layout in layouts),
            )

        with ThreadPoolExecutor(max_workers=workers) as executor:
            outcomes = tuple(executor.map(run_probe, probes))
        for probe, smoke in zip(probes, outcomes, strict=True):
            if smoke.failure:
                return r[m.Infra.ValidationReport].from_failure(smoke)
            output = smoke.value
            if u.Cli.process_succeeded(output.outcome):
                continue
            outcome = m.Cli.ProcessOutcome.model_validate(
                output.outcome,
                from_attributes=True,
            )
            detail = (
                f"{probe.subject}: {outcome.model_dump_json()}\n"
                f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}"
            )
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=False,
                    violations=(detail,),
                    summary=f"fresh-import failed: {probe.subject}",
                ),
            )
        summary = f"{len(probes)} fresh-import probe(s) passed"
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(passed=True, violations=(), summary=summary),
        )

    @staticmethod
    def require_complete_models(module: t.RegistryModule) -> None:
        """Fail when a pydantic class reachable from the exports cannot build.

        The walk starts at the module's declared exports (the facades and the
        settings, config and service classes it publishes) and follows the
        classes nested in each FLEXT class through its MRO, so the scope is
        derived from the public surface, never from a list. The ``m.*``
        presets defer model builds to first use, so a class still pending
        after import is expected; each one the probed package defines is
        built here through the canonical type adapter, exactly as its first
        use would. An annotation that stays unresolved (a ``TYPE_CHECKING``-
        only type, a misspelled name) still fails that build, and pydantic's
        own error escapes unchanged naming the unresolved name. Inherited
        classes belong to their own package's probe.

        """
        package = module.__name__.partition(".")[0]
        pending: MutableSequence[type] = [
            value
            for name in getattr(module, c.Infra.DUNDER_ALL, ())
            if isinstance(value := getattr(module, name), type)
        ]
        seen: set[type] = set()
        incomplete: MutableSequence[type] = []
        while pending:
            klass = pending.pop()
            if klass in seen or not klass.__module__.startswith(c.Infra.PKG_ROOT):
                continue
            seen.add(klass)
            if vars(klass).get("__pydantic_complete__") is False:
                incomplete.append(klass)
            pending.extend(
                member
                for base in klass.__mro__
                for member in vars(base).values()
                if isinstance(member, type)
            )
        owned = sorted(
            (
                klass
                for klass in incomplete
                if klass.__module__.partition(".")[0] == package
            ),
            key=lambda klass: f"{klass.__module__}.{klass.__qualname__}",
        )
        for klass in owned:
            u.type_adapter(klass)
        FlextInfraValidateFreshImport._require_schema_fields(package, seen)

    @staticmethod
    def _require_schema_fields(package: str, classes: Iterable[type]) -> None:
        """Fail on the first field that only builds by ``arbitrary_types_allowed``.

        Every model of the probed package that sets or inherits the flag has
        each field type built without it, through the canonical type adapter.
        A field type without a schema raises pydantic's own schema-generation
        error, which escapes unchanged with a note naming the model and field;
        its owner type (a ``t.Port`` or a validated ``t`` alias) is the fix.

        Raises:
            c.PydanticSchemaGenerationError: For the first such field.

        """
        models = sorted(
            (
                klass
                for klass in classes
                if klass.__module__.partition(".")[0] == package
                and "__pydantic_fields__" in vars(klass)
                and getattr(klass, "model_config", {}).get("arbitrary_types_allowed")
            ),
            key=lambda klass: f"{klass.__module__}.{klass.__qualname__}",
        )
        for klass in models:
            fields: Mapping[str, t.FieldInfo] = vars(klass)["__pydantic_fields__"]
            # A deferred model keeps its field annotations as forward
            # references; the stdlib evaluator resolves them in the model's
            # own module and class namespace, as pydantic does on build, and
            # pydantic's own field split drops the field-level metadata.
            hints = get_type_hints(klass, include_extras=True)
            for name, info in fields.items():
                if info.annotation is None:
                    continue
                field_type = m.FieldInfo.from_annotation(hints[name]).annotation
                try:
                    u.type_adapter(field_type)
                except c.PydanticSchemaGenerationError as exc:
                    exc.add_note(
                        f"{klass.__module__}.{klass.__qualname__}.{name} needs "
                        "arbitrary_types_allowed: declare its type through t.Port "
                        "or a validated t alias"
                    )
                    raise

    def execute_probe(
        self,
        probe: m.Infra.FreshImportProbe,
        *,
        source_roots: Sequence[Path] = (),
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run the selected native consumer in its declared physical runtime.

        Returns:
            Result carrying the consumer's command output, or a failure when
            the runtime is not a physical directory or the interpreter is
            missing.

        """
        interpreter = u.Infra.runtime_python(
            self.repository_root,
            runtime_root=self.runtime_root,
        )
        environment = u.Infra.runtime_environment_dir(
            self.repository_root,
            runtime_root=self.runtime_root,
        )
        if environment.is_symlink() or not environment.is_dir():
            return r[p.Cli.CommandOutput].fail(
                f"fresh-import runtime must be physical: {environment}",
            )
        if not interpreter.is_file():
            return r[p.Cli.CommandOutput].fail(
                f"fresh-import target interpreter is missing: {interpreter}; "
                "make setup provisions it",
            )
        return u.Cli.run_raw(
            [
                str(interpreter),
                *("-O",) * sys.flags.optimize,
                "-B",
                "-W",
                "error",
                "-",
            ],
            cwd=self.repository_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(
                env=self._workspace_import_env(source_roots),
                input_data=probe.code,
            ),
        )

    def _workspace_import_env(
        self,
        source_roots: Sequence[Path] = (),
    ) -> Mapping[str, str]:
        """Prefer the complete candidate fleet over inherited editable installs.

        Returns:
            The resulting ``Mapping[str, str]``.

        """
        inherited_env = u.Cli.process_env()
        import_roots = (
            *(str(root) for root in source_roots),
            str(self.repository_root),
            str(self.repository_root / c.Infra.DEFAULT_SRC_DIR),
        )
        existing = inherited_env.get(c.Infra.ORCHESTRATOR_ENV_PYTHONPATH, "")
        pythonpath = c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
            part for part in (*import_roots, existing) if part
        )
        return u.Cli.process_env(
            overrides={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: pythonpath},
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the same guard used by managed publication.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result = self.build_report(packages=self.packages)
        if result.failure:
            return r[bool].from_failure(result)
        report = result.value
        return (
            r[bool].ok(value=True)
            if report.passed
            else r[bool].fail("\n".join((report.summary, *report.violations)))
        )


__all__: Sequence[str] = ("FlextInfraValidateFreshImport",)
