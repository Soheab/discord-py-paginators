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
    TypeVar,
)

import discord

if TYPE_CHECKING:
    from typing_extensions import Self, NotRequired

    from .base_paginator import BaseClassPaginator

if TYPE_CHECKING:
    from typing_extensions import TypeVar

    ClientT = TypeVar("ClientT", bound=discord.Client, covariant=True, default=discord.Client)
else:
    ClientT = TypeVar("ClientT", bound=discord.Client, covariant=True)  # type: ignore


InteractionT = discord.Interaction[ClientT]
PaginatorT = TypeVar("PaginatorT", bound="BaseClassPaginator[Any]")
PaginatorCheck = Callable[[PaginatorT, InteractionT], Union[bool, Coroutine[Any, Any, bool]]]
Destination = Union[discord.abc.Messageable, InteractionT]

# fmt: off
PossiblePage = Union[
    str,
    discord.Embed,
    discord.File,
    discord.Attachment,
    dict[str, Any],
    Sequence["PossiblePage"],
    Any,
]
# fmt: on

Page = TypeVar("Page", bound=PossiblePage)



class BaseKwargs(TypedDict):
    content: Optional[str]
    embeds: list[discord.Embed]
    view: Self

    files: NotRequired[list[discord.File]]
    attachments: NotRequired[list[discord.File]]  # used in edit over files
    wait: NotRequired[bool]  # webhook/followup

class BasePaginatorKwargs(TypedDict):
    check: NotRequired[Optional[PaginatorCheck[Any]]]  # default: None
    author_id: NotRequired[Optional[int]]  # default: None
    delete_after: NotRequired[bool]  # default: False
    disable_after: NotRequired[bool]  # default: False
    clear_buttons_after: NotRequired[bool]  # default: False
    per_page: NotRequired[int]  # default: 1
    timeout: NotRequired[Optional[Union[int, float]]]  # default: 180.0
    message: NotRequired[discord.Message]  # default: None