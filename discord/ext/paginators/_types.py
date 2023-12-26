from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Optional,
    Sequence,
    TypedDict,
    Union,
)

import discord

if TYPE_CHECKING:
    from typing_extensions import Self, NotRequired

    from .base_paginator import BaseClassPaginator

    BaseClassPaginator = BaseClassPaginator[Any]
else:
    Self = NotRequired = BaseClassPaginator = Any

if TYPE_CHECKING:
    from typing_extensions import TypeVar

    ClientT = TypeVar("ClientT", bound=discord.Client, covariant=True, default=discord.Client)
else:
    from typing import TypeVar 
    ClientT = TypeVar("ClientT", bound=discord.Client, covariant=True)  # type: ignore

from typing import TypeVar  # F811 Redefinition of unused `TypeVar`

Interaction = discord.Interaction[ClientT]
PaginatorT = TypeVar("PaginatorT", bound="BaseClassPaginator")
PaginatorCheck = Callable[[PaginatorT, Interaction], Union[bool, Coroutine[Any, Any, bool]]]
Destination = Union[discord.abc.Messageable, Interaction]

_PossiblePages = Union[
    str,
    discord.Embed,
    discord.File,
    discord.Attachment,
    dict[str, Any],
]
# fmt: off
PossiblePage = Union[
    _PossiblePages,
    Sequence[_PossiblePages],
    Any,
]
# fmt: on

Page = TypeVar("Page", bound=PossiblePage)


class BaseKwargs(TypedDict):
    content: Optional[str]
    """Content of the page."""
    embeds: list[discord.Embed]
    """Embeds of the page."""
    view: Self
    """View of the page. (the paginator)"""

    files: NotRequired[list[discord.File]]
    """Files of the page. Not always available like when using `edit`."""
    attachments: NotRequired[list[discord.File]]  # used in edit over files
    """Attachments of the page. Not always available, probably only when using `edit`."""
    wait: NotRequired[bool]  # webhook/followup
    """Whether to wait for the webhook message to be sent and returned. Only used ``Webhook.send``."""


class BasePaginatorKwargs(TypedDict):
    check: NotRequired[Optional[PaginatorCheck[Any]]]  # default: None
    author_id: NotRequired[Optional[int]]  # default: None
    delete_after: NotRequired[bool]  # default: False
    disable_after: NotRequired[bool]  # default: False
    clear_buttons_after: NotRequired[bool]  # default: False
    per_page: NotRequired[int]  # default: 1
    timeout: NotRequired[Optional[Union[int, float]]]  # default: 180.0
    message: NotRequired[discord.Message]  # default: None
