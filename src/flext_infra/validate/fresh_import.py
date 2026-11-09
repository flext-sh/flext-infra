"""Verify published exports and real entrypoints in fresh child processes.

The ``fresh-import`` check gate runs this guard in the checkout's provisioned
runtime. Each entrypoint loads before any package smoke so cached imports cannot hide
consumer-order defects. Imported workspace modules must belong to this checkout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping, MutableSequence, Sequence
from concurrent.futures import ThreadPoolExecutor
from inspect import getsource
from pathlib import Path
from textwrap import dedent, indent
from types import ModuleType
from typing import Annotated, cast, override

from pydantic.warnings import UnsupportedFieldAttributeWarning
from typing_extensions import TypeForm

from flext_infra import c, config, m, p, r, s, settings, t, u
from flext_infra.workspace._environment.provenance_module_source import (
    FlextInfraWorkspaceEnvironmentProvenanceModuleSource,
)


class FlextInfraValidateFreshImport(s[bool]):
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
        publications: Sequence[p.Infra.LazyInitPlan] = (),
        repository_roots: Sequence[Path] = (),
    ) -> p.Result[p.Infra.ValidationReport]:
        """Validate complete publications, stopping at the first causal failure.

        Returns:
            The resulting ``p.Result[p.Infra.ValidationReport]``.

        """
        layouts_result = self._project_layouts(repository_roots)
        if layouts_result.failure:
            return r[p.Infra.ValidationReport].from_failure(layouts_result)
        layouts = layouts_result.value
        origin_code = self._origin_code(layouts)
        probes: MutableSequence[p.Infra.FreshImportProbe] = []
        for layout in layouts:
            built = self._layout_probes(layout, origin_code, publications)
            if built.failure:
                return r[p.Infra.ValidationReport].from_failure(built)
            probes.extend(built.value)
        packaged = self._package_probes(packages, origin_code)
        if packaged.failure:
            return r[p.Infra.ValidationReport].from_failure(packaged)
        probes.extend(packaged.value)
        if not probes:
            return r[p.Infra.ValidationReport].ok(
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
    ) -> p.Result[tuple[p.Infra.RopeProjectLayout, ...]]:
        """Resolve package layouts without treating explicit non-packages as packages.

        A missing layout is accepted only when the native project metadata
        explicitly declares ``tool.uv.package = false``. Invalid metadata and
        every other missing package layout remain failures.

        Returns:
            The resulting project layouts.

        """
        layouts: MutableSequence[p.Infra.RopeProjectLayout] = []
        for root in repository_roots:
            layout = u.Infra.layout(root)
            if layout is None:
                metadata = u.Infra.read_project_metadata_state(root)
                if metadata.failure:
                    return r[tuple[p.Infra.RopeProjectLayout, ...]].from_failure(
                        metadata
                    )
                if metadata.value.packaging.uv_package is False:
                    continue
                return r[tuple[p.Infra.RopeProjectLayout, ...]].fail(
                    f"fresh-import has no Python layout for {root}",
                )
            layouts.append(layout)
        return r[tuple[p.Infra.RopeProjectLayout, ...]].ok(tuple(layouts))

    @staticmethod
    def _origin_code(layouts: Sequence[p.Infra.RopeProjectLayout]) -> str:
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
        layout: p.Infra.RopeProjectLayout,
        origin_code: str,
        publications: Sequence[p.Infra.LazyInitPlan],
    ) -> p.Result[MutableSequence[p.Infra.FreshImportProbe]]:
        """Build one layout's entry-point and export probes.

        Returns:
            The resulting probes for the layout.

        """
        source = u.Cli.files_read_text(layout.project_root / c.PYPROJECT_FILENAME)
        if source.failure:
            return r[MutableSequence[p.Infra.FreshImportProbe]].from_failure(source)
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[MutableSequence[p.Infra.FreshImportProbe]].fail(
                f"invalid published pyproject in {layout.project_root}",
            )
        metadata = m.Infra.FreshImportMetadata.model_validate(payload).project
        probes = self._entry_point_probes(layout, metadata, origin_code)
        export = self._export_probe(layout, origin_code, publications)
        if export.failure:
            return r[MutableSequence[p.Infra.FreshImportProbe]].from_failure(export)
        probes.append(export.value)
        return r[MutableSequence[p.Infra.FreshImportProbe]].ok(probes)

    @staticmethod
    def _entry_point_probes(
        layout: p.Infra.RopeProjectLayout,
        metadata: p.Infra.FreshImportEntryPoints,
        origin_code: str,
    ) -> MutableSequence[p.Infra.FreshImportProbe]:
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
        probes: MutableSequence[p.Infra.FreshImportProbe] = []
        for group, entries in groups:
            for name, value in entries.items():
                probes.append(
                    m.Infra.FreshImportProbe(
                        subject=f"{layout.package_name}: {group}/{name}={value}",
                        code=(
                            FlextInfraValidateFreshImport._probe_prelude()
                            + f"EntryPoint(name={name!r}, "
                            f"value={value!r}, group={group!r}).load()\n" + origin_code
                        ),
                    ),
                )
        return probes

    @staticmethod
    def _export_probe(
        layout: p.Infra.RopeProjectLayout,
        origin_code: str,
        publications: Sequence[p.Infra.LazyInitPlan],
    ) -> p.Result[p.Infra.FreshImportProbe]:
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
                return r[p.Infra.FreshImportProbe].fail(
                    f"missing public export contract for {layout.package_name}",
                )
            body = "".join(
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=plan.context.current_pkg
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(
                    exports=tuple(plan.exports), prefix=c.Infra.PKG_ROOT
                )
                for plan in owned
            )
        else:
            body = (
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=layout.package_name
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(
                    exports=(), prefix=c.Infra.PKG_ROOT
                )
            )
        return r[p.Infra.FreshImportProbe].ok(
            m.Infra.FreshImportProbe(
                subject=layout.package_name,
                code=(
                    FlextInfraValidateFreshImport._probe_prelude() + body + origin_code
                ),
            ),
        )

    @staticmethod
    def _package_probes(
        packages: Sequence[str],
        origin_code: str,
    ) -> p.Result[MutableSequence[p.Infra.FreshImportProbe]]:
        """Build one whole-package import probe per declared package name.

        Returns:
            The resulting package probes.

        """
        probes: MutableSequence[p.Infra.FreshImportProbe] = []
        for package in packages:
            if not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(package):
                return r[MutableSequence[p.Infra.FreshImportProbe]].fail(
                    f"{package}: not a valid Python package name",
                )
            probes.append(
                m.Infra.FreshImportProbe(
                    subject=package,
                    code=FlextInfraValidateFreshImport._probe_prelude()
                    + c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(package=package)
                    + origin_code
                    + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(
                        exports=(), prefix=c.Infra.PKG_ROOT
                    ),
                ),
            )
        return r[MutableSequence[p.Infra.FreshImportProbe]].ok(probes)

    def _execute_probes(
        self,
        probes: Sequence[p.Infra.FreshImportProbe],
        layouts: Sequence[p.Infra.RopeProjectLayout],
    ) -> p.Result[p.Infra.ValidationReport]:
        """Run every probe in the declared runtime and judge the outcomes.

        The probes execute the target checkout's code, so they run in the
        declared runtime root's environment (the generated Makefile's
        RUNTIME_ROOT), never the one hosting this tool: probing with the
        host's dependency set would grade the target against packages it
        does not install.

        Returns:
            The resulting ``p.Result[p.Infra.ValidationReport]``.

        """
        workers = config.Infra.codegen.fresh_import_workers
        u.Cli.info(f"fresh-import: running {len(probes)} probes with {workers} workers")

        # Each source travels on stdin because the workspace export probe may
        # exceed the kernel's single-argument limit. map preserves report order.
        # ``-B``: a validator never writes into the checkout it validates, so
        # the probed sources leave no bytecode cache behind.
        def run_probe(
            indexed: tuple[int, p.Infra.FreshImportProbe],
        ) -> p.Result[p.Cli.CommandOutput]:
            index, probe = indexed
            u.Cli.info(f"fresh-import: probe {index} start {probe.subject}")
            result = self.execute_probe(
                probe,
                source_roots=tuple(layout.src_dir for layout in layouts),
                profile_slot=index,
            )
            if result.failure:
                u.Cli.error(f"fresh-import: probe {index} failed: {result.error}")
            else:
                output = result.value
                succeeded = u.Cli.process_succeeded(output.outcome)
                u.Cli.info(f"fresh-import: probe {index} end success={succeeded}")
                if not succeeded:
                    u.Cli.error(output.stderr)
            return result

        with ThreadPoolExecutor(max_workers=workers) as executor:
            outcomes = tuple(executor.map(run_probe, enumerate(probes)))
        for probe, smoke in zip(probes, outcomes, strict=True):
            if smoke.failure:
                return r[p.Infra.ValidationReport].from_failure(smoke)
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
            return r[p.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=False,
                    violations=(detail,),
                    summary=f"fresh-import failed: {probe.subject}",
                ),
            )
        summary = f"{len(probes)} fresh-import probe(s) passed"
        return r[p.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(passed=True, violations=(), summary=summary),
        )

    @staticmethod
    def _probe_prelude() -> str:
        """Project the installed check owners into the consumer's stdin probe.

        Only canonical packaged source is transferred. The child needs the
        runtime APIs of Core, never an installation of the Infra tool.

        Returns:
            The self-contained imports and unchanged validation definitions.

        """
        return (
            "from __future__ import annotations\n"
            + c.Infra.FRESH_IMPORT_PRELUDE
            + "import os, sysconfig\n"
            "from collections.abc import Iterable, Mapping, MutableSequence, Sequence\n"
            "from contextlib import ExitStack\n"
            "from importlib.machinery import BuiltinImporter, ExtensionFileLoader, "
            "FrozenImporter, ModuleSpec\n"
            "from sys import modules\n"
            "from types import ModuleType\n"
            "from pydantic.warnings import UnsupportedFieldAttributeWarning\n"
            "from typing import cast\n"
            "from typing_extensions import TypeForm\n"
            "from flext_core import c, p, r, t, u\n"
            + getsource(FlextInfraWorkspaceEnvironmentProvenanceModuleSource)
            + "\nclass FlextInfraValidateFreshImport:\n"
            + "\n".join(
                indent(dedent(getsource(method)), "    ")
                for method in (
                    FlextInfraValidateFreshImport.require_complete_models,
                    FlextInfraValidateFreshImport._require_schema_fields,
                )
            )
        )

    @staticmethod
    def require_complete_models(module: t.RegistryModule, prefix: str) -> None:
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
            for name in getattr(module, "__all__", ())
            if isinstance(value := getattr(module, name), type)
        ]
        seen: set[type] = set()
        incomplete: MutableSequence[type] = []
        while pending:
            klass = pending.pop()
            if klass in seen or not klass.__module__.startswith(prefix):
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
        FlextInfraValidateFreshImport._require_schema_fields(package, seen)
        for klass in owned:
            u.type_adapter(klass).rebuild(raise_errors=True)

    @staticmethod
    def _require_schema_fields(package: str, classes: Iterable[type]) -> None:
        """Fail on the first declared field without its own native schema.

        Every model of the probed package has each field built independently,
        including its validation metadata, through the canonical type adapter.
        A field type without a schema raises pydantic's own schema-generation
        error, which escapes unchanged with a note naming the model and field;
        its owner type (a ``t.Port`` or a validated ``t`` alias) is the fix.

        Raises:
            c.PydanticSchemaGenerationError: For the first such field.
            AttributeError: A field annotation does not resolve in its module.
            NameError: A field annotation names an unbound symbol.
            UnsupportedFieldAttributeWarning: For field metadata on an alias.

        """
        models = sorted(
            (
                klass
                for klass in classes
                if klass.__module__.partition(".")[0] == package
                and "__pydantic_fields__" in vars(klass)
            ),
            key=lambda klass: f"{klass.__module__}.{klass.__qualname__}",
        )
        probe_module = ModuleType("_flext_fresh_import_probe")
        sys.modules[probe_module.__name__] = probe_module
        try:
            for klass in models:
                # The model is built natively first, in its own module namespace
                # (Pydantic's resolution), so each field annotation below is the
                # resolved type rather than a forward reference of another frame.
                u.type_adapter(klass)
                # A synthetic subclass in an empty module reproduces cross-module
                # inheritance: any field left incomplete when `klass` was defined
                # is re-evaluated in `probe_module` and fails through Pydantic's
                # public TypeAdapter build.
                probe_subclass = type(
                    f"_Probe{klass.__name__}",
                    (klass,),
                    {"__module__": probe_module.__name__},
                )
                # The synthetic subclass declares no PEP 695 parameters of its own,
                # so the ones its inherited annotations name come from `klass`.
                parent_namespace = (
                    dict(vars(sys.modules[klass.__module__]))
                    | {
                        parameter.__name__: parameter
                        for parameter in getattr(klass, "__type_params__", ())
                    }
                    | {klass.__name__: klass}
                )
                u.type_adapter(cast(TypeForm[object], probe_subclass)).rebuild(
                    force=True,
                    raise_errors=True,
                    _types_namespace=parent_namespace,
                )
                fields: Mapping[str, t.FieldInfo] = vars(klass)["__pydantic_fields__"]
                for name, info in fields.items():
                    if info.annotation is None:
                        continue
                    # An inherited field's annotation is written in its declaring
                    # class's module; resolving it in the subclass module reads
                    # a different binding of the same letter.
                    owner = next(
                        (
                            base
                            for base in klass.__mro__
                            if name in vars(base).get("__annotations__", {})
                        ),
                        klass,
                    )
                    namespace = (
                        vars(sys.modules[klass.__module__])
                        | vars(sys.modules[owner.__module__])
                        | dict(vars(owner))
                        | {
                            parameter.__name__: parameter
                            for parameter in getattr(klass, "__type_params__", ())
                        }
                        | {klass.__name__: klass, owner.__name__: owner}
                    )
                    try:
                        # Deferred build: an eager adapter resolves forward
                        # references in this probe's own frame (whose letters are
                        # flext-infra's), not in the declaring module namespace.
                        annotation = info.rebuild_annotation()
                        # The probe body runs in a fresh script that binds only
                        # flext-core's ``c, p, r, t, u``: no ``m`` here.
                        if isinstance(annotation, type) and (
                            "__pydantic_fields__" in vars(annotation)
                        ):
                            # A model field type builds in its own module namespace.
                            u.type_adapter(cast(TypeForm[object], annotation))
                        else:
                            u.type_adapter(
                                cast(TypeForm[object], annotation),
                                config={"defer_build": True},
                            ).rebuild(
                                force=True,
                                raise_errors=True,
                                _types_namespace=namespace,
                            )
                    except c.PydanticSchemaGenerationError as exc:
                        exc.add_note(
                            f"{klass.__module__}.{klass.__qualname__}.{name} needs "
                            "arbitrary_types_allowed: declare its type through t.Port "
                            "or a validated t alias"
                        )
                        raise
                    except (AttributeError, NameError) as exc:
                        exc.add_note(
                            f"{klass.__module__}.{klass.__qualname__}.{name} "
                            f"annotation "
                            f"does not resolve in {owner.__module__}"
                        )
                        raise
                    except UnsupportedFieldAttributeWarning as exc:
                        exc.add_note(
                            f"{klass.__module__}.{klass.__qualname__}.{name} places "
                            "field metadata inside an Annotated alias"
                        )
                        raise
        finally:
            sys.modules.pop(probe_module.__name__, None)

    def execute_probe(
        self,
        probe: p.Infra.FreshImportProbe,
        *,
        source_roots: Sequence[Path] = (),
        profile_slot: int = 0,
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
        source = probe.code
        if settings.Infra.profile or settings.Infra.profile_children:
            destination = settings.Infra.profile_output
            if destination is None:
                return r[p.Cli.CommandOutput].fail(
                    "fresh-import profiling requires the command profile destination"
                )
            source = c.Infra.FRESH_IMPORT_PROFILE_CODE.format(
                source=source,
                output=str(
                    destination.with_stem(
                        f"{destination.stem}-fresh-import-{profile_slot}"
                    )
                ),
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
                input_data=source,
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
