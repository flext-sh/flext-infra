"""Compare a freshly imported stand-in's MRO with its real class's MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from importlib import import_module

standin = import_module("examples._capability").ExamplesFlextDemoCapabilityExtra
print("examples._capability.extra" not in sys.modules)
real = import_module("examples._capability.extra").ExamplesFlextDemoCapabilityExtra
print(standin is not real)
print(standin.__mro__[1:] == real.__mro__[1:])
