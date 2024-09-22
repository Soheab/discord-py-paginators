from __future__ import annotations
from copy import deepcopy
import os
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    Union,
)
from collections.abc import Sequence

import discord

from .._types import PageT

if TYPE_CHECKING:
    from typing_extensions import Self
else:
    Self = Any

__all__ = (
    "PaginatorOption",
)


class PaginatorOption(discord.SelectOption, Generic[PageT]):
    """A subclass of :class:`discord.SelectOption` representing a page in a :class:`SelectOptionsPaginator`.

    Other parameters are the same as :class:`~.discord.SelectOption`.

    Parameters
    ----------
    content: Union[Any, Sequence[Any]]
        The content of the page. See :class:`SelectOptionsPaginator` for more the supported types.
    emoji: Optional[Union[:class:`str`, :class:`discord.Emoji`, :class:`discord.PartialEmoji`]]
        The emoji to use for the option. Defaults to ``None``.
    """

    def __init__(
        self,
        content: Union[PageT, Sequence[PageT]],
        *,
        label: str = discord.utils.MISSING,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(label=label, value=value, description=description, emoji=emoji, default=False)
        self.content: Union[PageT, Sequence[PageT]] = content

    def __repr__(self) -> str:
        return f"<PaginatorOption emoji={self.emoji!r} label={self.label!r} value={self.value!r}>"
    
    @staticmethod
    def __get_default_option_per_page(page: Any) -> discord.SelectOption:
        label: Optional[str] = None
        if isinstance(page, discord.Embed):
            label = page.title or page.description or page.author.name or page.footer.text
        elif isinstance(page, (discord.File, discord.Attachment)):
            label = page.filename
        elif isinstance(page, (int, str)):
            label = str(page)

        if label:
            label = str(label.split("\n")[0][:99])
        return discord.SelectOption(label=label or "Untitled")

    @staticmethod
    def __ensure_unique_value(option: Optional[discord.SelectOption]) -> Optional[discord.SelectOption]:
        if not option:
            return None

        # discord.py sets the value to the label if it's not provided
        # but the user might have set the value to the label themselves
        if option.value != option.label:
            return option

        new_option = deepcopy(option)
        new_option.value = (str(os.urandom(16).hex()) if option.value == option.label else "")[:99]
        return new_option

    @classmethod
    def _from_page(
        cls,
        page: Union[PageT, Self],
        default_option: Optional[discord.SelectOption] = None,
        *,
        label: str = discord.utils.MISSING,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
    ) -> Self:
        if page.__class__ is discord.SelectOption:
            raise TypeError(
                "A regular SelectOption is not supported as it doesn't contain any content. Use PaginatorOption instead or pass a Page."
            )

        page_option: Optional[PaginatorOption[Any]] = page if isinstance(page, PaginatorOption) else None
        copy_from = cls.__ensure_unique_value(page_option or default_option or cls.__get_default_option_per_page(page))

        if not copy_from and label is discord.utils.MISSING and emoji is None:
            raise TypeError("Either label or emoji must be provided if copy_from is not provided")

        # cannot happen, __get_default_option_per_page always returns a SelectOption
        if not copy_from:
            raise TypeError("copy_from is required if label and emoji are not provided")

        label = label
        if not label or label is discord.utils.MISSING:
            label = copy_from.label

        value = value
        if not value or value is discord.utils.MISSING:
            value = copy_from.value

        description = description
        if not description:
            description = copy_from.description

        emoji = emoji
        if not emoji:
            emoji = copy_from.emoji

        return cls(
            content=page.content if isinstance(page, PaginatorOption) else page,  # type: ignore
            label=label,
            value=value,
            description=description,
            emoji=emoji,
        )
