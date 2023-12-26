from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    Optional,
    Sequence,
    Union,
)

from copy import deepcopy
import os

import discord

from .base_paginator import BaseClassPaginator
from ._types import Page

if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from ._types import BasePaginatorKwargs, Interaction


__all__ = (
    "PaginatorOption",
    "SelectOptionsPaginator",
)


class PaginatorOption(discord.SelectOption, Generic[Page]):
    """A subclass of :class:`discord.SelectOption` representing a page in a :class:`SelectOptionsPaginator`.

    Other parameters are the same as :class:`~.discord.SelectOption`.

    Parameters
    ----------
    content: Union[:class:`~discord.ext.paginators._types.Page`, Sequence[:class:`~discord.ext.paginators._types.Page`]]
        The content of the page. See :class:`SelectOptionsPaginator` for more the supported types.
    """

    def __init__(
        self,
        content: Union[Page, Sequence[Page]],
        *,
        label: str = discord.utils.MISSING,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(label=label, value=value, description=description, emoji=emoji)
        self.content: Union[Page, Sequence[Page]] = content

    @classmethod
    def from_page(
        cls,
        page: Page,
        copy_from: Optional[discord.SelectOption] = None,
        *,
        label: str = discord.utils.MISSING,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
    ) -> Self:
        if isinstance(page, discord.SelectOption):
            raise TypeError(
                "A regular SelectOption is not supported as it doesn't contain any content. Use PaginatorOption instead or pass a Page."
            )

        if not copy_from and label is discord.utils.MISSING and emoji is None:
            raise TypeError("Either label or emoji must be provided if copy_from is not provided")

        return cls(
            content=page,
            label=label or copy_from.label,  # type: ignore # it's handled in the if statement above
            value=value or copy_from.value,  # type: ignore # it's handled in the if statement above
            description=description or copy_from.description,  # type: ignore # it's handled in the if statement above
            emoji=emoji or copy_from.emoji,  # type: ignore # it's handled in the if statement above
        )


class SelectOptionsPaginator(BaseClassPaginator[Any]):
    """A paginator that uses discord.ui.Select to select pages.

    This paginator provides one select and two buttons to navigate through "pages" with options.

    Just for clarification, here is a list of supported pages:

    - :class:`discord.Embed`
    - :class:`discord.File`
    - :class:`discord.Attachment`
    - :class:`str`
    - :class:`list` or :class:`tuple` of the above
    - :class:`PaginatorOption` (a sbuclass of :class:`discord.SelectOption` with a ``content`` kwarg that can be any of the above)

    Other parameters are the same as :class:`discord.ext.paginators.base_paginator.BaseClassPaginator`. Except ``per_page`` which is always ``1`` and cannot be changed.

    Parameters
    ----------
    pages: Sequence[Union[:class:`~discord.ext.paginators._types.Page`, :class:`~discord.ext.paginators.select_paginator.PaginatorOption`]]
        A sequence of pages to paginate through. A page can be anything that is supported by the :class:`~discord.ext.paginators.base_paginator.BaseClassPaginator` class.
        With the addition of :class:`PaginatorOption` which is a subclass of :class:`discord.SelectOption` that also contains a ``content`` attribute,
        it can be used to provide a custom label, description and emoji for each "page".

        All options will be split into chunks of ``per_select`` and each chunk will be a select.
        IF a chunk is a already a list, it will be treated as a single select. If this chunk contains less or more items than ``per_select``,
        it will raise a ValueError.

        Example:

        .. code-block:: python3

            pages = [
                # This will be a single select with 3 options
                # per_select must be >= 3 or it will raise a ValueError
                ["Page 1", "Page 2", "Page 3"],
                # These will span across the needed amount of selects
                "Page 4", "Page 5", "Page 6", "Page 7",
                ...
            ]
    per_select: `Optional[:class:`int`]`
        The amount of options per select. Defaults to :attr:`SelectOptionsPaginator.MAX_SELECT_OPTIONS`.
    default_option: `Optional[:class:`discord.SelectOption`]`
        The option to get the metadata from if the a page is not an instance of :class:`PaginatorOption`.
        If this is ``None``, it will try to get the metadata from the page itself.
        E,g if the page is an embed, it will try to get the title or description, etc and use that as the label.
        Defaults to ``None``.
    """

    MAX_SELECT_OPTIONS: ClassVar[Literal[25]] = 25
    """The maximum amount of options per select by discord by the time of writing this."""

    def __init__(
        self,
        pages: Sequence[
            Union[
                Page,
                PaginatorOption[Page],
                Sequence[Page],
                Sequence[PaginatorOption[Page]],
            ]
        ],
        *,
        per_select: Optional[int] = None,
        default_option: Optional[discord.SelectOption] = None,
        **kwargs: Unpack[BasePaginatorKwargs],
    ) -> None:
        self.per_select: int = per_select or self.MAX_SELECT_OPTIONS
        self.default_option: Optional[discord.SelectOption] = default_option

        if "per_page" in kwargs:
            raise TypeError("per_page cannot be changed for SelectOptionsPaginator")

        kwargs["per_page"] = 1
        super().__init__(
            self._construct_options(pages),  # type: ignore
            **kwargs,
        )
        self.current_option_index: int = 0

    def _ensure_unique_value(self, option: Optional[discord.SelectOption]) -> Optional[discord.SelectOption]:
        if not option:
            return None

        if option.value != option.label:
            return option

        new_option = deepcopy(option)
        new_option.value += str(os.urandom(16).hex()) if option.value == option.label else ""
        new_option.value = new_option.value[:99]
        return new_option

    def _get_default_option_per_page(self, page: Any) -> discord.SelectOption:
        label: Optional[str] = None
        if isinstance(page, discord.Embed):
            label = page.title or page.description or page.author.name or page.footer.text
        elif isinstance(page, (discord.File, discord.Attachment)):
            label = page.filename
        elif isinstance(page, str):
            label = page

        if label:
            label = str(label.split("\n")[0][:99])
        return discord.SelectOption(label=label or "Untitled")

    def _construct_options(self, pages: Sequence[Sequence[Page]]) -> list[list[PaginatorOption[Page]]]:
        def actual_construct(page: Union[Page, PaginatorOption[Page]]) -> PaginatorOption[Page]:
            if isinstance(page, PaginatorOption):
                return page

            return PaginatorOption.from_page(
                page,
                self._ensure_unique_value(self.default_option) or self._get_default_option_per_page(page),
            )

        res: list[list[PaginatorOption[Page]]] = []
        options: list[PaginatorOption[Page]] = []
        nested_options: list[PaginatorOption[Page]] = []

        for page in pages:
            # Sequence
            if isinstance(page, (list, tuple)):
                if len(page) == 0:
                    continue

                for item in page:
                    if isinstance(item, (list, tuple)):
                        raise TypeError("Nested lists are not supported")

                    nested_options.append(actual_construct(item))

                if len(nested_options) > self.per_select:
                    raise ValueError(
                        f"Too many options for one select in nested list (max: {self.per_select}, got: {len(nested_options)})"
                    )

                options.append(nested_options)  # type: ignore # dw, it's a list of PaginatorOption
                nested_options = []
            else:
                options.append(actual_construct(page))  # type: ignore # Sequence is handled above

        for option in options:
            if isinstance(option, list):
                res.append(option)
                options.remove(option)

        if len(options) > 0:
            res.extend(discord.utils.as_chunks(options, self.per_select))

        return res

    def get_page(self, page_number: int):
        page = super().get_page(page_number)
        page[self.current_option_index].default = True
        return page[self.current_option_index].content

    async def switch_page(self, interaction: Optional[Interaction], page_number: int) -> None:
        self.current_option_index = 0
        self.select_page.options = self.pages[page_number]
        for option in self.select_page.options:
            option.default = False

        self.select_page.placeholder = f"Select a page | {self.page_string}"

        self.previous_page.disabled = self.current_page <= 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1
        return await super().switch_page(interaction, page_number)

    async def switch_options(self, interaction: Interaction) -> None:
        selected: str = self.select_page.values[0]
        for idx, option in enumerate(self.select_page.options):
            if option.label == selected or option.value == selected:
                self.current_option_index = idx
                option.default = True
            else:
                option.default = False

        page = self.get_page(self.current_page)
        self.select_page.options = self.pages[self.current_page]
        kwrgs = await self.get_page_kwargs(page)
        await self._edit_message(interaction, **kwrgs)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, row=1)
    async def previous_page(self, interaction: Interaction, _: discord.ui.Button[Self]) -> None:
        if self.current_page <= 0:
            self.current_page = 0
        else:
            self.current_page -= 1

        await self.switch_page(interaction, self.current_page)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, interaction: Interaction, _: discord.ui.Button[Self]) -> None:
        if self.current_page >= self.max_pages - 1:
            self.current_page = self.max_pages - 1
        else:
            self.current_page += 1

        await self.switch_page(interaction, self.current_page)

    @discord.ui.select(placeholder="Select a page", row=0)
    async def select_page(self, interaction: Interaction, _: discord.ui.Select[Any]) -> None:
        await self.switch_options(interaction)

    async def _send(self, *args: Any, **kwargs: Any) -> Optional[discord.Message]:
        self.select_page.options = self.pages[0]
        self.select_page.options[0].default = True
        self.select_page.placeholder = f"Select a page | {self.page_string}"
        self.previous_page.disabled = True
        self.next_page.disabled = self.max_pages == 1
        return await super()._send(*args, **kwargs)
