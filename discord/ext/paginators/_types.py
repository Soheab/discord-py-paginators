from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    TypeVar,
    TypedDict,
    Union,
)

from collections.abc import Callable, Coroutine

import discord

if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from .base_paginator import BaseClassPaginator
else:
    BaseClassPaginator = Any


if TYPE_CHECKING:
    from .base_paginator import _PaginatorLayoutView, _PaginatorView
else:
    _PaginatorView = discord.ui.View
    _PaginatorLayoutView = discord.ui.LayoutView

type PaginatorCheck[PaginatorT: BaseClassPaginator[Any]] = Callable[
    [PaginatorT, discord.Interaction[Any]], Union[bool, Coroutine[Any, Any, bool]]
]
type Destination = Union[discord.abc.Messageable, discord.Interaction[Any]]
type Sequence[T] = list[T] | tuple[T, ...]
type View = _PaginatorView | _PaginatorLayoutView


class BaseKwargs(TypedDict, total=False):
    content: str | None
    """Optional[:class:`str`]: Content of the page."""
    embeds: list[discord.Embed]
    """List[:class:`discord.Embed`]: Embeds of the page."""
    view: discord.ui.View | discord.ui.LayoutView
    """View of the page. (the paginator)"""

    files: NotRequired[list[discord.File | discord.Attachment]]
    """NotRequired[List[:class:`discord.File`]]: Files of the page. Not always available like when using `edit`."""
    attachments: NotRequired[list[discord.File]]  # used in edit over files
    """NotRequired[List[Union[:class:`discord.File`, :class:`discord.Attachment`]]]: Attachments of the page. Not always available, probably only when using `edit`."""
    wait: NotRequired[bool]  # webhook/followup
    """NotRequired[:class:`bool`]: Whether to wait for the webhook message to be sent and returned. Only used in interaction followups."""


class BasePaginatorKwargs[PaginatorT: BaseClassPaginator[Any]](TypedDict):
    per_page: NotRequired[int]
    """
    The amount of pages to display per page.
    Defaults to ``1``.

    E.g.: If ``per_page`` is ``2`` and ``pages`` is ``[Page("1"), Page("2"), Page("3"), Page("4")]``, then the message
    will show ``[Page("1"), Page("2")]`` on the first page and ``[Page("3"), Page("4")]`` on the second page.
    """
    author_id: NotRequired[Optional[int]]
    """
    The id of the user who can interact with the paginator.
    Defaults to ``None``.
    """
    check: NotRequired[Optional[PaginatorCheck[PaginatorT]]]
    """
    A callable that checks if the interaction is valid. This must be a callable that takes 2 or 3 parameters.
    The last two parameters represent the interaction and paginator respectively.
    It CAN be a coroutine.

    This is called in :meth:`~discord.ui.View.interaction_check`.

    If ``author_id`` is not ``None``, this won't be called.
    Defaults to ``None``.
    """
    always_allow_bot_owner: NotRequired[bool]
    """
    Whether to always allow the bot owner to interact with the paginator.
    Defaults to ``True``.
    """
    delete_message_after: NotRequired[bool]
    """
    Whether to delete the message after the paginator stops. Only works if ``message`` is not ``None``.
    Defaults to ``False``.
    """
    disable_items_after: NotRequired[bool]
    """
    Whether to disable the paginator after the paginator stops. Only works if ``message`` is not ``None``.
    Defaults to ``False``.
    """
    clear_items_after: NotRequired[bool]
    """
    Whether to clear the buttons after the paginator stops. Only works if ``message`` is not ``None``.
    Defaults to ``False``.
    """
    message: NotRequired[Optional[discord.Message]]
    """
    The message to use for the paginator. This is set automatically when ``_send`` is called.
    Defaults to ``None``.
    """
    add_page_string: NotRequired[bool]
    """
    Whether to add the page string to the page. Defaults to ``True``.
    This is a string that represents the current page and the max pages. E.g.: ``"Page 1 of 2"``.

    If the page is an embed, it will be appended to the footer text.
    If the page is a string, it will be appended to the string.
    Else, it will be set as the content of the message.
    """
    components_v2: NotRequired[bool]
    """
    Whether to use the v2 component system. See `pages` for more information.

    Defaults to ``False``.
    """
    timeout: NotRequired[Optional[Union[int, float]]]
    """
    The timeout for the paginator.
    Defaults to ``180.0``.
    """
    pages_on_demand: NotRequired[bool]
    cache_pages: NotRequired[bool]
    max_cache_time: NotRequired[Optional[float]]
    switch_pages_humanly: NotRequired[bool]
    auto_wrap_in_actionrow: NotRequired[bool]
