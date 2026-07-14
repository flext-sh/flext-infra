from pathlib import Path

import flext_infra as infra_pkg
from flext_infra import u
from flext_tests import tm


def test_version_full_import() -> None:
    project_root = Path(__file__).resolve().parents[2]
    metadata = u.read_project_metadata(project_root)

    tm.that(infra_pkg.__title__, eq=metadata.name)
