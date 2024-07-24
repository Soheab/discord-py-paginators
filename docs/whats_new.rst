.. currentmodule:: discord.ext.paginators

Changelogs
===========
This page keeps a human-readable changelog of significant changes to the project.

0.2.1 (2024-07-24)
-------------------

Rather small release with only bug fixes.

- Fixed a bug where using the `buttons=` kwarg in :class:`button_paginator.ButtonPaginator` would raise falsely raise an error.
- Fixed a where the labels for the `First` and `Last` buttons were not being set correctly in :class:`button_paginator.ButtonPaginator`.
  - The way the labels are set has been changed to be more reliable and less error-prone.
- Fixed a bug where the label for the :class:`select_paginator.PaginatorOption` was not being set correctly and would raise an internal error.
- Fixed an internal bug where editing a message would raise an error.

0.2.0 (2024-02-20)
-------------------

Many Quality of Life improvements and bug fixes.

Changes per module
~~~~~~~~~~~~~~~~~~~

errors
+++++++

This module has been removed. All errors are now either :exc:`ValueError` or :exc:`TypeError`.

base_paginator
+++++++++++++++

Added

- ``add_page_string`` kwarg to :class:`.BaseClassPaginator` to disable the automatic page string addition. Defaults to ``True``.

Bug Fixes:

- ``BaseClassPaginator.message`` is not set to ``None`` outside :meth:`.BaseClassPaginator.stop_paginator`.

- | :meth:`.BaseClassPaginator.stop_paginator` now takes an optional ``interaction`` parameter to stop the paginator using 
     the interaction's message instead of the paginator's message if available. Falls back to the paginator's message otherwise.
- | Kwargs like ``delete_after`` and ``disable_after`` are now properly handled usingt the available methods and erorrs that are raised are ignored
     and logged as debug now.

- | The page should also be edited properly now using the available and correct methods. E.g. the pagaintor can be used in an ephemeral message now.
     The ``edit_message`` kwarg in :meth:`.BaseClassPaginator.send` also works properly now.

Changes:

- ``NoPages`` exception has been replaced by a :exc:`ValueError`.
- :attr:`.BaseClassPaginator.current_page`'s setter now sets it to the maximum/minimum page if it's out of bounds.
- | :meth:`.BaseClassPaginator.interaction_check` & :meth:`.BaseClassPaginator.format_page` now call a private method 
     instead of directly doing the work in the method. This allows for easier overriding.
- :class:`.BaseClassPaginator` is no longer slotted. This did nothing anyways since :class:`discord.ui.View` is not slotted.

Miscellaneous:

- Better docstring for ``pages`` kwarg/attribute.
- More desciptive error messages like for the ``check`` callable checker.
- Owner ids are now cached on the instance on a private attribute. If ``always_allow_bot_owner`` is set to ``True``.
- | Just like :meth:`discord.ext.commands.Bot.is_owner` in discord.py version 2.4, team roles are now also taken into consideration 
     if ``always_allow_bot_owner`` is set to ``True``.
- If a :class:`dict` is passed to the ``pages`` kwarg, it's now copied to prevent any changes to the original dict from affecting the paginator.

button_paginator
+++++++++++++++++

Bug Fixes:

- | The ``buttons=`` kwarg in :class:`button_paginator.ButtonPaginator` now checks whether a :class:`dict` is passed and if all the required keys
     are present and if the values are of the correct type. This is to prevent any errors from happening when the buttons are added to the paginator. 
     The passed dict is also copied now to prevent any changes to the original dict from affecting the paginator. 
- Fixed a bug where the label of the ``First`` & ``Last`` buttons were not being set correctly.

Miscellaneous:

- :meth:`button_paginator.ButtonPaginator` no longer overrides ``stop_paginator`` but instead uses the one from :class:`.BaseClassPaginator`.
- The label and style of buttons should be set to the original value more reliably now.

modal_paginator
++++++++++++++++

Miscellaneous:

- Fixed a mistake in the print when the package was not installed. ``modalpagintor`` -> ``modalpaginator``.


Overall, a lot of typing improvements like ``Page`` has been replaced with ``Any`` to allow for more flexibility.
And other unnecessary type hints have been removed.


0.1.0 (2023-12-26)
-------------------

- Initial release!