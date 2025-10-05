"""Extension for discord.py that provides various paginators."""

from typing import Tuple

from .button_paginator import *  # noqa: F401, F403
from .select_paginator import *  # noqa: F401, F403

__all__: Tuple[str, ...] = (
    "ButtonPaginator",  # noqa: F405
    "PaginatorButton",  # noqa: F405
    "SelectOptionsPaginator",  # noqa: F405
)


__author__ = "Soheab_"
__version__ = "0.3.0"
__license__ = "MPL-2.0"
