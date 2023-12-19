try:
    from discord.ext.modal_paginator import *  # type: ignore
except ImportError:
    print(
        "discord.ext.modal_paginator not found. Install it with `python -m pip install -U discord-ext-modal-paginator` or use the `[modalpagintor]` option when install this package."
    )
