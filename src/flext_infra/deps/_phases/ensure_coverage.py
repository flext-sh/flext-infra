"""Phase: Ensure coverage configuration in pyproject.toml."""

from __future__ import annotations

from flext_infra import FlextInfraToml, m, t


class FlextInfraEnsureCoverageConfigPhase:
    """Ensure coverage report configuration with per-project-type thresholds."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        project_kind: str = "core",
    ) -> t.StrSequence:
        cov_config = self._tool_config.tools.coverage
        fail_under_map: t.IntMapping = {
            "core": cov_config.fail_under.core,
            "domain": cov_config.fail_under.domain,
            "platform": cov_config.fail_under.platform,
            "integration": cov_config.fail_under.integration,
            "app": cov_config.fail_under.app,
        }
        fail_under = fail_under_map.get(project_kind, cov_config.fail_under.core)
        report_phase = (
            m.Infra.TomlPhaseConfig
            .Builder("coverage-report")
            .table("coverage", "report")
            .value("fail_under", fail_under)
            .value("show_missing", True)
            .value("skip_covered", False)
            .value("precision", cov_config.precision)
            .build()
        )
        run_phase = (
            m.Infra.TomlPhaseConfig
            .Builder("coverage-run")
            .table("coverage", "run")
            .list("omit", sorted(set(cov_config.omit)))
            .build()
        )
        return FlextInfraToml.apply_phases(doc, report_phase, run_phase)


__all__ = ["FlextInfraEnsureCoverageConfigPhase"]
