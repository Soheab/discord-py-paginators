from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    TypeAlias,
    TypedDict,
    Union,
)

from collections.abc import Callable, Coroutine, Sequence

import discord

if TYPE_CHECKING:
    from .core import BaseClassPaginator
    from .views import View


__all__ = (
    "BoundPage",
    "BoundV2Page",
    "BasePaginatorKwargs",
)


type PaginatorCheck[PaginatorT: BaseClassPaginator[Any]] = Callable[
    [PaginatorT, discord.Interaction[Any]], Union[bool, Coroutine[Any, Any, bool]]
]
# type Seq[T] = list[T] | tuple[T, ...]
# type Sequence[T] = Seq[T] | Seq[Seq[T]]

type File = discord.File | discord.Attachment

type _BoundPage = str | discord.Embed | discord.ui.Button[Any] | discord.ui.Select[Any] | dict[str, Any] | File
type BoundPage = _BoundPage | Sequence[_BoundPage]
"""
The type of a page supported by paginators for not v2 components. Can be a single supported type or a sequence of supported types.

This includes:

- :class:`str`
- :class:`discord.Embed`
- :class:`discord.ui.Button`
- :class:`discord.ui.Select`
- :class:`dict`
- :class:`discord.File`
- :class:`discord.Attachment`

"""
type _BoundV2Page = (
    str
    | discord.ui.ActionRow[Any]
    | discord.ui.Container[Any]
    | discord.ui.File[Any]
    | discord.ui.MediaGallery[Any]
    | discord.ui.Section[Any]
    | discord.ui.Separator[Any]
    | discord.ui.TextDisplay[Any]
    | dict[str, Any]
    | File
)
type BoundV2Page = _BoundV2Page | Sequence[_BoundV2Page]
"""
The type of a page supported by paginators for v2 components. Can be a single supported type or a sequence of supported types.

This includes: 

- :class:`str`
- :class:`discord.ui.ActionRow`
- :class:`discord.ui.Container`
- :class:`discord.ui.File`
- :class:`discord.ui.MediaGallery`
- :class:`discord.ui.Section`
- :class:`discord.ui.Separator`
- :class:`discord.ui.TextDisplay`
- :class:`dict`
- :class:`discord.File`
- :class:`discord.Attachment`
"""


class BaseKwargs(TypedDict, total=False):
    view: discord.ui.View | discord.ui.LayoutView
    content: str | None
    embeds: list[discord.Embed]
    files: list[discord.File]
    attachments: list[discord.File | discord.Attachment]  # used in edit over files
    allowed_mentions: discord.AllowedMentions | None


class BasePaginatorKwargs[PaginatorT: BaseClassPaginator[Any]](TypedDict, total=False):
    """
    See :class:`.BaseClassPaginator` for documentation on these parameters.
    """

    per_page: int
    author_id: int | None
    check: PaginatorCheck[PaginatorT] | None
    always_allow_bot_owner: bool
    delete_message_after: bool
    disable_items_after: bool
    clear_items_after: bool
    message: discord.Message | None
    add_page_string: bool
    components_v2: bool | None
    timeout: int | float | None
    switch_pages_humanly: bool

    allowed_mentions: discord.AllowedMentions | bool | None
    view_cls: type[View[PaginatorT]] | None

    title: str | discord.ui.TextDisplay[Any] | None
    description: str | discord.ui.TextDisplay[Any] | None
