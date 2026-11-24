import sys
from pathlib import Path
from importlib.util import find_spec, module_from_spec, spec_from_file_location
package = find_spec('flext_infra')
if package is None or package.origin is None:
    raise ModuleNotFoundError('flext_infra._pytest.profile_child')
child_path = Path(package.origin).parent.joinpath(*('_pytest', 'profile_child')).with_suffix('.py')
spec = spec_from_file_location('flext_infra._pytest.profile_child', child_path)
if spec is None or spec.loader is None:
    raise ImportError('flext_infra._pytest.profile_child')
child = sys.modules.get(spec.name)
if child is None:
    child = module_from_spec(spec)
    sys.modules[spec.name] = child
    spec.loader.exec_module(child)
child.FlextInfraPytestProfileChild.startup(__file__, 'flext_infra._pytest.clock', 'FLEXT_PYTEST_PROFILE_CHILD_ROOT')
