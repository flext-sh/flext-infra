"""Calculate runtime requirement changes from native deptry and injected provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t, u


class FlextInfraRuntimeDependencyCalculator:
    """Derive only native-evidenced changes, preserving target requirement policy."""

    @staticmethod
    def calculate(
        scan: m.Infra.DeptryScan,
        inputs: m.Infra.RuntimeDependencyInputs,
    ) -> p.Result[m.Infra.RuntimeDependencyPlan]:
        """Calculate changes without discovering packages or writing any file.

        Returns:
            Target-owned requirement changes and unresolved native import identities.
        """
        result_type = r[m.Infra.RuntimeDependencyPlan]
        target = inputs.target_root
        if (
            not target.is_absolute()
            or scan.settings.path != target / c.PYPROJECT_FILENAME
        ):
            return result_type.fail("dependency provenance belongs to another target")
        if not inputs.python.is_absolute() or scan.settings.content is None:
            return result_type.fail(
                "dependency provenance lacks its interpreter or settings"
            )
        document = u.Cli.toml_mapping_from_text(
            scan.settings.content.decode(c.DEFAULT_ENCODING),
        )
        if document is None:
            return result_type.fail(
                f"invalid dependency declaration: {scan.settings.path}"
            )
        project = u.Cli.toml_mapping_child(document, c.Infra.PROJECT)
        if project is None:
            return result_type.fail(
                f"project declaration is absent: {scan.settings.path}"
            )
        runtime = tuple(
            t.Infra.STR_SEQ_ADAPTER.validate_python(
                project.get(c.Infra.DEPENDENCIES, []),
            ),
        )
        development = tuple(
            u.Infra.raw_requirement_values(
                document.get(c.Infra.DEPENDENCY_GROUPS, {}),
            )
        )
        parsed_runtime = tuple(Requirement(item) for item in runtime)
        parsed_development = tuple(Requirement(item) for item in development)
        suppliers = tuple(
            (provider, Requirement(provider.requirement))
            for provider in inputs.providers
        )
        for provider, requirement in suppliers:
            if canonicalize_name(requirement.name) != canonicalize_name(
                provider.package.name
            ):
                return result_type.fail(
                    f"import supplier requirement differs from its locked identity: {provider.package.name}",
                )
        unused = {
            canonicalize_name(item.module)
            for item in scan.report.root
            if item.error.code == "DEP002"
        }
        selected = [
            raw
            for raw, requirement in zip(runtime, parsed_runtime, strict=True)
            if canonicalize_name(requirement.name) not in unused
        ]
        promoted: list[str] = []
        unresolved: list[str] = []
        for diagnostic in scan.report.root:
            if diagnostic.error.code not in {"DEP001", "DEP003", "DEP004"}:
                continue
            providers = tuple(
                (provider, requirement)
                for provider, requirement in suppliers
                if diagnostic.module in provider.modules
            )
            if len(providers) != 1:
                unresolved.append(diagnostic.module)
                continue
            provider, requirement = providers[0]
            name = canonicalize_name(provider.package.name)
            if name == canonicalize_name(str(project[c.Infra.NAME])):
                unresolved.append(diagnostic.module)
                continue
            authored = tuple(
                raw
                for raw, parsed in zip(development, parsed_development, strict=True)
                if canonicalize_name(parsed.name) == name
            )
            additions = authored or (provider.requirement,)
            if authored:
                promoted.extend(authored)
            selected.extend(item for item in additions if item not in selected)
        return result_type.ok(
            m.Infra.RuntimeDependencyPlan(
                before=scan.settings,
                dependencies=tuple(selected),
                promoted=tuple(dict.fromkeys(promoted)),
                unresolved_modules=tuple(dict.fromkeys(unresolved)),
                inputs=(
                    *inputs.inputs,
                    *(
                        state
                        for provider in inputs.providers
                        for state in provider.inputs
                    ),
                    scan.settings,
                    scan.report_state,
                ),
            )
        )


__all__: list[str] = ["FlextInfraRuntimeDependencyCalculator"]
