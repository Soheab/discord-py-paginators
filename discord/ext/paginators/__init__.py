"""Extension for discord.py that provides various paginators."""

from .button_paginator import *  # noqa: F401, F403
from .select_paginator import *  # noqa: F401, F403
from .core import *  # noqa: F401, F403
from .views import *  # noqa: F401, F403
from .enums import *  # noqa: F401, F403

__all__: tuple[str, ...] = (
    "ButtonPaginator",  # noqa: F405
    "PaginatorButton",  # noqa: F405
    "SelectOptionsPaginator",  # noqa: F405
    "AfterAction",  # noqa: F405
    "BaseClassPaginator",  # noqa: F405
)


__author__ = "Soheab_"
__version__ = "0.4.0a"
__license__ = "MPL-2.0"
