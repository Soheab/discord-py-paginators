import warnings

warnings.warn(
    (
        f"Importing model_paginator from `discord.ext.paginators` is deprecated since v0.3.0. "
        "Please install the `discord-ext-modal-paginator` package and import from `discord.ext.modal_paginator` manually."
        " This module and extra requirement will be removed in v0.5.0."
        " Apologies for the inconvenience."
    ),
    DeprecationWarning,
    stacklevel=2,
)


try:
    from discord.ext.modal_paginator import *  # type: ignore # noqa: F403 # it's fine
except ImportError:
    import sys
    print(
        f"discord.ext.modal_paginator not found. Install it with `{sys.executable} -m pip install -U discord-ext-modal-paginator` or use the `[modalpaginator]` extra when installing this package."
    )
