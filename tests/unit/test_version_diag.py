import flext_infra as infra_pkg
from flext_infra.__version__ import FlextInfraVersion


def test_version_diag() -> None:
    version_value = infra_pkg.__version__
    if not isinstance(version_value, str):
        version_value = version_value.__version__
    assert version_value == FlextInfraVersion.__version__
