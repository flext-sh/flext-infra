"""Verify published exports and real entrypoints in fresh child processes.

The conformance transaction runs this guard before committing its journal.
Each entrypoint loads before any package smoke so cached imports cannot hide
consumer-order defects. Imported workspace modules must belong to this checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_core import r
from flext_infra import c, m, p, t, u

from ..base import FlextInfraServiceBase


class FlextInfraValidateFreshImport(FlextInfraServiceBase[bool]):
    """Verify consumers and publication contracts without inherited import state."""

    packages: Annotated[
        t.StrSequence,
        m.Field(description="Packages to validate in fresh subprocesses"),
    ] = (c.Infra.PKG_CORE_UNDERSCORE, "flext_infra", "flext_tests")

    _PRELUDE: ClassVar[str] = (
        "import importlib, sys\n"
        "from importlib.metadata import EntryPoint\n"
        "from pathlib import Path\n"
    )
    _EXPORT_CODE: ClassVar[str] = (
        "module = importlib.import_module({package!r})\n"
        "for name in (*{exports!r}, *getattr(module, '__all__', ())):\n"
        "    getattr(module, name)\n"
    )
    _ORIGIN_CODE: ClassVar[str] = (
        "for name, module in tuple(sys.modules.items()):\n"
        "    for package, directory in __ORIGINS__:\n"
        "        if name == package or name.startswith(package + '.'):\n"
        "            origin = getattr(module, '__file__', None)\n"
        "            if origin is None or not Path(origin).resolve().is_relative_to(Path(directory)):\n"
        "                raise ImportError(f'{name}: origin {origin!r} is outside {directory}')\n"
    )

    def build_report(
        self,
        packages: t.StrSequence = (),
        *,
        publications: t.SequenceOf[m.Infra.LazyInitPlan] = (),
        repository_roots: t.SequenceOf[Path] = (),
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate complete publications, stopping at the first causal failure."""
        layouts: t.MutableSequenceOf[m.Infra.RopeProjectLayout] = []
        for root in repository_roots:
            layout = u.Infra.layout(root)
            if layout is None:
                return r[m.Infra.ValidationReport].fail(
                    f"fresh-import has no Python layout for {root}"
                )
            layouts.append(layout)
        origins = tuple(
            (layout.package_name, str(layout.package_dir.resolve()))
            for layout in layouts
        )
        origin_code = self._ORIGIN_CODE.replace("__ORIGINS__", repr(origins))
        probes: t.MutableSequenceOf[m.Infra.FreshImportProbe] = []
        for layout in layouts:
            source = u.Cli.files_read_text(
                layout.project_root / c.Infra.PYPROJECT_FILENAME
            )
            if source.failure:
                return r[m.Infra.ValidationReport].from_failure(source)
            payload = u.Cli.toml_mapping_from_text(source.value)
            if payload is None:
                return r[m.Infra.ValidationReport].fail(
                    f"invalid published pyproject in {layout.project_root}"
                )
            metadata = m.Infra.FreshImportMetadata.model_validate(payload).project
            groups = (
                ("console_scripts", metadata.scripts),
                ("gui_scripts", metadata.gui_scripts),
                *metadata.entry_points.items(),
            )
            for group, entries in groups:
                for name, value in entries.items():
                    probes.append(m.Infra.FreshImportProbe(
                        subject=f"{layout.package_name}: {group}/{name}={value}",
                        code=(
                            self._PRELUDE
                            + f"EntryPoint(name={name!r}, value={value!r}, group={group!r}).load()\n"
                            + origin_code
                        ),
                    ))
            owned = tuple(
                plan for plan in publications
                if plan.context.importable
                and plan.action == c.Infra.LazyInitAction.WRITE
                and plan.context.pkg_dir.is_relative_to(layout.package_dir)
            )
            if not any(
                plan.context.pkg_dir == layout.package_dir for plan in owned
            ):
                return r[m.Infra.ValidationReport].fail(
                    f"missing public export contract for {layout.package_name}"
                )
            body = "".join(
                self._EXPORT_CODE.format(
                    package=plan.context.current_pkg, exports=tuple(plan.exports)
                )
                for plan in owned
            )
            probes.append(m.Infra.FreshImportProbe(
                subject=layout.package_name,
                code=self._PRELUDE + body + origin_code,
            ))
        for package in packages:
            if not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(package):
                return r[m.Infra.ValidationReport].fail(
                    f"{package}: not a valid Python package name"
                )
            probes.append(m.Infra.FreshImportProbe(
                subject=package,
                code=self._PRELUDE + self._EXPORT_CODE.format(
                    package=package, exports=()
                ) + origin_code,
            ))
        env = self._workspace_import_env(
            tuple(layout.src_dir for layout in layouts)
        )
        for probe in probes:
            smoke = u.Cli.run_raw(
                [sys.executable, "-W", "error", "-c", probe.code],
                cwd=self.repository_root,
                env=env,
            )
            if smoke.failure:
                return r[m.Infra.ValidationReport].from_failure(smoke)
            output = smoke.value
            if not u.Cli.process_succeeded(output.outcome):
                detail = (
                    f"{probe.subject}: {output.outcome.model_dump_json()}\n"
                    f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}"
                )
                return r[m.Infra.ValidationReport].ok(m.Infra.ValidationReport(
                    passed=False, violations=(detail,),
                    summary=f"fresh-import failed: {probe.subject}",
                ))
        return r[m.Infra.ValidationReport].ok(m.Infra.ValidationReport(
            passed=True, summary=f"{len(probes)} fresh-import probe(s) passed"
        ))

    def _workspace_import_env(
        self, source_roots: t.SequenceOf[Path] = ()
    ) -> t.StrMapping:
        """Prefer the complete candidate fleet over inherited editable installs."""
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
            overrides={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: pythonpath}
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the same guard used by managed publication."""
        result = self.build_report(packages=self.packages)
        if result.failure:
            return r[bool].from_failure(result)
        report = result.value
        return (
            r[bool].ok(True)
            if report.passed
            else r[bool].fail("\n".join((report.summary, *report.violations)))
        )


__all__: t.StrSequence = ("FlextInfraValidateFreshImport",)
