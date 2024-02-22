from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    TypedDict,
    Union,
    TypeVar,
)

from collections.abc import Callable, Coroutine

import discord

if TYPE_CHECKING:
    from typing_extensions import Self, NotRequired

    from .base_paginator import BaseClassPaginator

    BaseClassPaginator = BaseClassPaginator[Any]
else:
    BaseClassPaginator = Any


PaginatorT = TypeVar("PaginatorT", bound=BaseClassPaginator)
PaginatorCheck = Callable[[PaginatorT, discord.Interaction[Any]], Union[bool, Coroutine[Any, Any, bool]]]
Destination = Union[discord.abc.Messageable, discord.Interaction[Any]]
PageT = TypeVar("PageT", covariant=True)


class BaseKwargs(TypedDict):
    content: Optional[str]
    """Optional[:class:`str`]: Content of the page."""
    embeds: list[discord.Embed]
    """List[:class:`discord.Embed`]: Embeds of the page."""
    view: Self
    """View of the page. (the paginator)"""

    files: NotRequired[list[Union[discord.File, discord.Attachment]]]
    """NotRequired[List[:class:`discord.File`]]: Files of the page. Not always available like when using `edit`."""
    attachments: NotRequired[list[discord.File]]  # used in edit over files
    """NotRequired[List[Union[:class:`discord.File`, :class:`discord.Attachment`]]]: Attachments of the page. Not always available, probably only when using `edit`."""
    wait: NotRequired[bool]  # webhook/followup
    """NotRequired[:class:`bool`]: Whether to wait for the webhook message to be sent and returned. Only used in interaction followups."""


class BasePaginatorKwargs(TypedDict):
    check: NotRequired[Optional[PaginatorCheck[Any]]]  # default: None
    author_id: NotRequired[Optional[int]]  # default: None
    delete_after: NotRequired[bool]  # default: False
    disable_after: NotRequired[bool]  # default: False
    clear_buttons_after: NotRequired[bool]  # default: False
    per_page: NotRequired[int]  # default: 1
    timeout: NotRequired[Optional[Union[int, float]]]  # default: 180.0
    message: NotRequired[discord.Message]  # default: None
