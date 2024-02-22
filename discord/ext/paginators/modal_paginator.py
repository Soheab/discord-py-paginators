try:
    from discord.ext.modal_paginator import *  # type: ignore # noqa: F403 # it's fine
except ImportError:
    print(
        "discord.ext.modal_paginator not found. Install it with `python -m pip install -U discord-ext-modal-paginator` or use the `[modalpaginator]` option when install this package."
    )
