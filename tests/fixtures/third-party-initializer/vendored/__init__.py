"""A third-party initializer with no FLEXT lazy exports.

Its module body reads a function attribute whose value Rope cannot resolve,
the shape of ``psutil``'s ``net_io_counters.cache_clear``.
"""

from functools import partial

from vendored._common import wrap_numbers as _wrap_numbers


def net_io_counters() -> None:
    """Return nothing; republishes the wrapped cache handle."""


net_io_counters.cache_clear = partial(_wrap_numbers.cache_clear, "net_io_counters")
