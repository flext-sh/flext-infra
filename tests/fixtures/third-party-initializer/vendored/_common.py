"""A third-party module whose function attribute Rope cannot resolve."""


def wrap_numbers() -> None:
    """Return nothing; carries a cache handle attribute."""


wrap_numbers.cache_clear = _undeclared_cache.cache_clear
