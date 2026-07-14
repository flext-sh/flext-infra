from pathlib import Path

import flext_infra as infra_pkg
from flext_infra import u
from flext_tests import tm


def test_version_diag() -> None:
    project_root = Path(__file__).resolve().parents[2]
    constants = u.read_project_constants(infra_pkg.__title__, root=project_root)

    tm.that(infra_pkg.__version__, eq=constants.PACKAGE_VERSION)
