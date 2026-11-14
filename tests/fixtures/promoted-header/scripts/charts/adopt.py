# /// flext-command
# verb = "charts"
# what = "adopt"
# summary = "Adota pin de dependencia interna em consumidores"
# description = "Atualiza dependencies[].version internas (registry do projeto) para TO só nos consumidores nomeados em CHARTS; o release do owner nunca reescreve consumidores."
# domain = "charts"
# mutates = true
# aliases = []
# example = "make chart-adopt DEP=common-lib TO=0.7.128 CHARTS=platform-app"
# rules = ["mutador: executa a acao; OPTIONS=Y mostra o contrato", "ADR-136 selective pins", "delega para demo-charts release adopt"]
# params = [
#   { name = "WHAT", help = "acao de charts", required = false, default = "adopt", choices = ["adopt"] },
#   { name = "DEP", help = "nome da dependencia interna", required = true },
#   { name = "TO", help = "semver a pinjar", required = true },
#   { name = "CHARTS", help = "lista csv dos consumidores que adotam", required = true },
# ]
# ///
"""Adopt an internal chart dependency pin into consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import u

from demo_charts.promoted.charts_command import DemoChartsChartsCommand


def adopt_pins() -> int:
    """Run chart-release adopt with DEP/TO/CHARTS from the environment.

    Returns:
        The canonical chart-release exit code.

    """
    charts = [
        part.strip() for part in u.Infra.env_value("CHARTS").split(",") if part.strip()
    ]
    argv = [
        "adopt",
        f"--adopt-dep={u.Infra.env_value('DEP')}",
        f"--adopt-to={u.Infra.env_value('TO')}",
    ]
    for chart in charts:
        argv.extend(["--charts", chart])
    return DemoChartsChartsCommand.run_chart_release(*argv)


if __name__ == "__main__":
    u.Infra.promoted_main(__file__, adopt_pins)
