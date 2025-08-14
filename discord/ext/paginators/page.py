from __future__ import annotations
from typing import TYPE_CHECKING, Any

import discord

if TYPE_CHECKING:
    from .base_paginator import BaseClassPaginator

    from ._types import Sequence


class Page[ItemT: Any]:
    """Represents a single page of the paginator.

    items: Any
        A sequence of pages to paginate.
        Supported types for pages:

        - :class:`str`: Will be set as the content of the message.
        - :class:`.discord.Embed`: Will be appended to the embeds of the message.
        - :class:`.discord.File`: Will be appended to the files of the message.
        - :class:`.discord.Attachment`: Calls :meth:`~discord.Attachment.to_file()` and appends it to the files of the message.
        - :class:`discord.ui.Item`: Will be appended to the items of the view. See warning below if item is a v2 component.
        - :class:`dict`: Will be updated with the kwargs of the message. Beware of v2 component restrictions.
        - Sequence[Any]: Will be flattened and each entry will be handled as above.

        Sequence = List, Tuple, etc.

        Any other types will probably be ignored.
        You can hot swap the pages at any time by setting this attribute.

        .. warning::
            The types and behavior of the items changes depending on the types you passed OR the ``components_v2`` parameter
            on the paginator.

            Passing a :class:`discord.ui.Item` will add it to the view, but if the item is a v2 component
            (e.g. :class:`discord.ui.Container`) OR ``components_v2`` is set to True in the paginator, it is not
            allowed to include any embeds, content or attachments in a message. So the paginator will do
            following to "work around" that:

            - Pages with type :class:`str` will be converted to :class:`discord.ui.TextDisplay`
            - Pages with type :class:`discord.Embed` are not allowed, so that will raise an error.
            - Pages with type :class:`discord.File` or :class:`discord.Attachment` are allowed because
            you can attach those to a :class:`discord.ui.MediaGallery`, :class:`discord.ui.MediaGalleryItem`,
            :class:`discord.ui.File` or :class:`discord.ui.Thumbnail`.

            Example
            -------

            .. code-block:: python3

                page = Page(discord.ui.TextDisplay("Page 1"))
                # or multiple items
                page = Page(discord.ui.TextDisplay("Page 1"), discord.ui.TextDisplay("Page 2"))
                # ^ on one page
    """

    def __init__(self, *items: ItemT) -> None:
        if not items:
            raise ValueError("At least one item must be provided.")

        self.items: list[ItemT] = list(items)

        self._paginator: BaseClassPaginator[ItemT] | None = None

    @property
    def paginator(self) -> BaseClassPaginator[ItemT] | None:
        """:class:`BaseClassPaginator` | None: The paginator associated with this page."""
        return self._paginator

    async def format(self) -> ItemT | Sequence[ItemT]:
        """Any | Sequence[ItemT]: Method to format the page before sending it.

        This method is called before processing the page, e.g,
        adding it to the view. This is optional is async.

        By default, this method simply returns the items as they are.
        """
        return self.items

    def _is_v2(self) -> bool:
        if any(isinstance(item, discord.Embed) for item in self.items):
            return False

        return any((isinstance(item, discord.ui.Item) and item._is_v2) or isinstance(item, str) for item in self.items)
