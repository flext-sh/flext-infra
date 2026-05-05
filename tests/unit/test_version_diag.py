from pathlib import Path

import flext_infra as infra_pkg
from flext_infra import u


def test_version_diag() -> None:
    project_root = Path(__file__).resolve().parents[2]
    constants = u.read_project_constants(infra_pkg.__title__, root=project_root)

    assert infra_pkg.__version__ == constants.PACKAGE_VERSION
