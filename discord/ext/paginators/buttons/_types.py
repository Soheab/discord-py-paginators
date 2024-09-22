from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional, TypeVar, TypedDict, Union

import discord

from .paginator import ButtonPaginator

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class OriginalButtonKwargs(TypedDict):
    # must provide either an emoji or a label
    emoji: NotRequired[Optional[Union[str, discord.PartialEmoji, discord.Emoji]]]  # default: None
    label: NotRequired[Optional[str]]  # default: None
    style: NotRequired[discord.ButtonStyle]  # default: discord.ButtonStyle.secondary
    disabled: NotRequired[bool]  # default: False
    row: NotRequired[Optional[int]]  # default: 0
    custom_id: NotRequired[Optional[str]]  # default: None


class OriginalButtonKwargsWithPosition(TypedDict):
    # must provide either an emoji or a label
    emoji: NotRequired[Optional[Union[str, discord.PartialEmoji, discord.Emoji]]]  # default: None
    label: NotRequired[Optional[str]]  # default: None
    style: NotRequired[discord.ButtonStyle]  # default: discord.ButtonStyle.secondary
    disabled: NotRequired[bool]  # default: False
    row: NotRequired[Optional[int]]  # default: 0
    custom_id: NotRequired[Optional[str]]  # default: None
    position: NotRequired[int]  # default: None / 0


class ButtonOverrideMetadata(TypedDict):
    button: OriginalButtonKwargs
    callback: Callable[..., Coroutine[Any, Any, Any]]
    override: bool


class CustomButtonKwargs(TypedDict):
    custom_id: str
    label: Optional[str]
    emoji: Optional[Union[str, discord.PartialEmoji, discord.Emoji]]
    style: discord.ButtonStyle
    disabled: bool
    row: Optional[int]
    position: Optional[int]


DecoFunc = TypeVar("DecoFunc", bound=Callable[[Any, discord.Interaction[Any]], Coroutine[Any, Any, Any]])
DecoCls = TypeVar("DecoCls", bound=type[ButtonPaginator[Any]])
