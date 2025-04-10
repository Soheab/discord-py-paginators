from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    TypedDict,
    Union,
    TypeVar,
)

from collections.abc import Callable, Coroutine

import discord

if TYPE_CHECKING:
    from typing_extensions import NotRequired

    from .base_paginator import BaseClassPaginator

    BaseClassPaginator = BaseClassPaginator[Any]
else:
    BaseClassPaginator = Any


PaginatorT = TypeVar("PaginatorT", bound=BaseClassPaginator)  # type: ignore
PaginatorCheck = Callable[[PaginatorT, discord.Interaction[Any]], Union[bool, Coroutine[Any, Any, bool]]]
Destination = Union[discord.abc.Messageable, discord.Interaction[Any]]
PageT = TypeVar("PageT", covariant=True)


class BaseKwargs(TypedDict):
    content: Optional[str]
    """Optional[:class:`str`]: Content of the page."""
    embeds: list[discord.Embed]
    """List[:class:`discord.Embed`]: Embeds of the page."""
    view: discord.ui.View
    """View of the page. (the paginator)"""

    files: NotRequired[list[Union[discord.File, discord.Attachment]]]
    """NotRequired[List[:class:`discord.File`]]: Files of the page. Not always available like when using `edit`."""
    attachments: NotRequired[list[discord.File]]  # used in edit over files
    """NotRequired[List[Union[:class:`discord.File`, :class:`discord.Attachment`]]]: Attachments of the page. Not always available, probably only when using `edit`."""
    wait: NotRequired[bool]  # webhook/followup
    """NotRequired[:class:`bool`]: Whether to wait for the webhook message to be sent and returned. Only used in interaction followups."""


class BasePaginatorKwargs(TypedDict, Generic[PaginatorT]):
    per_page: NotRequired[int]
    """
    The amount of pages to display per page.
    Defaults to ``1``.

    E.g.: If ``per_page`` is ``2`` and ``pages`` is ``["1", "2", "3", "4"]``, then the message
    will show ``["1", "2"]`` on the first page and ``["3", "4"]`` on the second page.
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
    delete_after: NotRequired[bool]
    """
    Whether to delete the message after the paginator stops. Only works if ``message`` is not ``None``.
    Defaults to ``False``.
    """
    disable_after: NotRequired[bool]
    """
    Whether to disable the paginator after the paginator stops. Only works if ``message`` is not ``None``.
    Defaults to ``False``.
    """
    clear_buttons_after: NotRequired[bool]
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
    timeout: NotRequired[Optional[Union[int, float]]]
    """
    The timeout for the paginator.
    Defaults to ``180.0``.
    """
