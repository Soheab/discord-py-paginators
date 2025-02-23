import warnings

from .selects import *

warnings.warn(
    (
        f"Importing from `{__name__}` is deprecated since v0.3.0. "
        "Please use `from discord.ext.paginators import SelectOptionPaginator` instead."
        " This module will be removed in v0.5.0."
    ),
    DeprecationWarning,
    stacklevel=2,
)
