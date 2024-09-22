from __future__ import annotations
from collections import Counter
from functools import partial
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
)
from collections.abc import Sequence

from copy import deepcopy
import os

import discord

from ..base_paginator import BaseClassPaginator
from .option import PaginatorOption

if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from .._types import BasePaginatorKwargs

    PageT = TypeVar("PageT", covariant=True, bound=Union[Any, PaginatorOption[Any]])
else:
    PageT, Self, Unpack, BasePaginatorKwargs = Any, Any, Any, Any


__all__ = ("SelectOptionsPaginator",)


class SelectOptionsPaginator(BaseClassPaginator[PageT]):
    """A paginator that uses discord.ui.Select to select pages.

    This paginator provides one select and two buttons to navigate through "pages" with options.

    Just for clarification, here is a list of supported pages:

    - :class:`discord.Embed`
    - :class:`discord.File`
    - :class:`discord.Attachment`
    - :class:`str`
    - :class:`list` or :class:`tuple` of the above
    - :class:`PaginatorOption` (a subclass of :class:`discord.SelectOption` with a ``content`` kwarg that can be any of the above)

    Other parameters are the same as :class:`discord.ext.paginators.base_paginator.BaseClassPaginator`. Except ``per_page`` which is always ``1`` and cannot be changed.

    Parameters
    ----------
    pages: Sequence[Union[Any, :class:`.PaginatorOption`]]
        A sequence of pages to paginate through. A page can be anything that is supported by the :class:`.BaseClassPaginator` class.
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
    per_select: Optional[:class:`int`]
        The amount of options per select. Defaults to :attr:`SelectOptionsPaginator.MAX_SELECT_OPTIONS`.
    default_option: Optional[:class:`discord.SelectOption`]
        The option to get the metadata from if the a page is not an instance of :class:`PaginatorOption`.
        If this is ``None``, it will try to get the metadata from the page itself.
        E,g if the page is an embed, it will try to get the title or description, etc and use that as the label.
        Defaults to ``None``.
    add_in_order: :class:`bool`
        Whether to add the options in the order they are provided. Defaults to ``False``.
        ``False`` will add the option in whatever order the library parses them.

        Example
        -------

        .. code-block:: python3
            :linenos:

            # if True
            pages = [
                | <page 1>, |
                | <page 2>, |
                | <page 3>, |
                # this ^ will be a single select with 3 options
                [<page 4>, <page 5>, <page 6>, <page 7>],
                # this ^ will be a single select with 4 options
                | <page 7>, |
                # this ^ will be a single select with 1 option
                [<page 8>, <page 9>, <page 10>],
                # this ^ will be a single select with 3 options
                ...
                # and so on
            ]

            # if False
            pages = [
                <page 1>,
                <page 2>,
                <page 3>,
                [<page 4>, <page 5>, <page 6>, <page 7>],
                # this ^ will be a single select with 4 options
                <page 7>,
                [<page 8>, <page 9>, <page 10>],
                # this ^ will be a single select with 3 options
                ...
                # and so on

                # pages 1, 2, 3 and 7 will be in one select.
            ]

        Make sure to experiment with this to see what fits your needs the best.

    Attributes
    ----------
    MAX_SELECT_OPTIONS: :class:`int`
        The hardcoded maximum amount of options per select by discord by the time of writing this.
    pages: :class:`list`[:class:`list`[:class:`PaginatorOption`[:class:`PageT`]]]
        A list of pages for each select. Each select contains a list of options.
    per_select: :class:`int`
        The amount of options per select that the you provided. Defaults to :attr:`SelectOptionsPaginator.MAX_SELECT_OPTIONS`.
    default_option: Optional[:class:`discord.SelectOption`]
        The default option to get the metadata from if the page is not an instance of :class:`PaginatorOption`.
    current_option_index: :class:`int`
        The index of the currently selected option in the current select. Zero-indexed.
    """

    MAX_SELECT_OPTIONS: ClassVar[Literal[25]] = 25
    """The maximum amount of options per select by discord by the time of writing this."""

    pages: list[list[PaginatorOption[PageT]]]  # type: ignore

    def __init__(
        self,
        pages: Sequence[PageT],
        *,
        per_select: Optional[int] = None,
        default_option: Optional[discord.SelectOption] = None,
        add_in_order: bool = False,
        **kwargs: Unpack[BasePaginatorKwargs[Self]],
    ) -> None:

        self.per_select: int = per_select or self.MAX_SELECT_OPTIONS
        self.default_option: Optional[discord.SelectOption] = default_option
        self._add_in_order: bool = add_in_order

        if "per_page" in kwargs:
            raise TypeError("per_page cannot be set for SelectOptionsPaginator at the moment.")

        kwargs["per_page"] = 1
        super().__init__(
            self._construct_options(list(pages)),  # type: ignore
            **kwargs,
        )
        self.current_option_index: int = 0

    def _construct_options(self, pages: list[list[PageT] | PageT]) -> list[list[PaginatorOption[PageT]]]:
        """Constructs the options for the selects.

        This will split the pages into chunks of ``per_select`` and each chunk will be a select.
        If a chunk is a list, it will be treated as a single select and will not be split further.
        If a chunk contains less or more items than ``per_select``, it will raise a ValueError.

        Parameters
        ----------
        pages: Sequence[Sequence[PageT] | PageT]
            The pages to construct the selects from.

        Returns
        -------
        list[list[PaginatorOption[PageT]]]
            A list of selects with options.
        """
        actual_construct: partial[PaginatorOption[PageT]] = partial(
            PaginatorOption[PageT]._from_page, default_option=self.default_option
        )

        # separate function to ensure the inner page isn't a list/tuple
        def construct_option(page: PageT) -> PaginatorOption[PageT]:
            if isinstance(page, (list, tuple)):
                # yes, I know this is a bit overkill, but it's for the sake of clarity (and a bit of fun/why not)
                error_msg = (
                    "Nested list/tuple as page is not allowed:"
                    " \033[91m[..., [<page>, \033[91m\033[1m[<page>, <page>]\033[0m\033[91m, <page>], ...,]\033[0m vs"
                    " \033[92m[..., \033[92m\033[1m[<page>, <page>, <page>, <page>]\033[0m\033[92m, ...,]\033[0m"
                )
                raise ValueError(error_msg)

            return actual_construct(page)

        res: list[list[PaginatorOption[PageT]]] = []

        chunk: list[PaginatorOption[PageT]] = []

        for page in pages.copy():
            print("page", page)
            if isinstance(page, (list, tuple)):
                if chunk and self._add_in_order:
                    res.append(chunk)
                    chunk = []

                list_page: Union[list[PageT], tuple[PageT, ...]] = page
                if len(list_page) > self.per_select:
                    raise ValueError(
                        f"Too many options for one select in nested list/tuple (max: {self.per_select}, got: {len(list_page)})"
                    )

                res.append([construct_option(page) for page in list_page])

            else:
                chunk.append(construct_option(page))
                if len(chunk) >= self.per_select:
                    res.append(chunk)
                    chunk = []
        if chunk:
            res.append(chunk)

        return res

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        super().current_page = value
        self.update_select_state()

    def __handle_options(self, options: list[PaginatorOption[Any]]) -> list[PaginatorOption[Any]]:
        selected_values = set(self.select_page.values)
        set_default = False

        for idx, option in enumerate(options):
            option.default = option.value in selected_values
            if option.default:
                self.current_option_index = idx
                set_default = True

        if not set_default:
            options[0].default = True

        return options

    def update_select_state(
        self,
    ) -> None:
        options = self.__handle_options(self.pages[self.current_page].copy())
        self.select_page.options = list(options)
        self.previous_page.disabled = not self.loop_pages and self.current_page == 0
        self.next_page.disabled = not self.loop_pages and (self.current_page >= self.max_pages - 1)
        self.select_page.placeholder = f"Select a page | {self.page_string}"

    def get_page(self, page_number: int) -> Union[PageT, list[PageT]]:
        pages: list[PaginatorOption[PageT]] = super().get_page(page_number)  # type: ignore # it's a list of PaginatorOption
        return pages[self.current_option_index].content  # type: ignore

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, row=1)
    async def previous_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        new_page = self.current_page - 1
        await self.switch_page(interaction, new_page)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        new_page = self.current_page + 1
        await self.switch_page(interaction, new_page)

    @discord.ui.select(placeholder="Select a page", row=0)
    async def select_page(self, interaction: discord.Interaction[Any], _: discord.ui.Select[Any]) -> None:
        await self.switch_page(interaction, self.current_page)

    async def _send(self, *args: Any, **kwargs: Any) -> Optional[discord.Message]:
        self.update_select_state()
        return await super()._send(*args, **kwargs)
