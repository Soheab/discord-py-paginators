from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Optional,
    Union,
)

import os
from functools import partial

import discord

from .core import BaseClassPaginator


if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from ._types import BasePaginatorKwargs, Sequence
else:
    Self = Unpack = BasePaginatorKwargs = Any


__all__ = (
    "PaginatorOption",
    "SelectOptionsPaginator",
)


class PaginatorOption[PageT: Any](discord.SelectOption):
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
        content: PageT | Sequence[PageT],
        *,
        label: str = discord.utils.MISSING,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        value: str = discord.utils.MISSING,
        description: str | None = None,
    ) -> None:
        super().__init__(label=label, value=value, description=description, emoji=emoji, default=False)
        self.content: PageT | Sequence[PageT] = content

    def __repr__(self) -> str:
        return f"<PaginatorOption emoji={self.emoji!r} label={self.label!r} value={self.value!r}>"

    @staticmethod
    def _get_default_option_per_page(page: Any) -> discord.SelectOption:
        if isinstance(page, PaginatorOption):
            return PaginatorOption._get_default_option_per_page(page.content)  # pyright: ignore[reportUnknownMemberType]

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
    def __ensure_unique_value(option: discord.SelectOption) -> discord.SelectOption:
        if option.value != option.label:
            return option
        return discord.SelectOption(
            label=option.label,
            value=str(os.urandom(16).hex())[:99],
            description=option.description,
            emoji=option.emoji,
            default=option.default,
        )

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

        copy_from = cls.__ensure_unique_value(default_option or cls._get_default_option_per_page(page))

        if isinstance(page, cls):
            label = page.label
            value = page.value
            description = page.description
            emoji = page.emoji

        label = label if label is not discord.utils.MISSING else copy_from.label
        value = value if value is not discord.utils.MISSING else copy_from.value
        description = description or copy_from.description
        emoji = emoji or copy_from.emoji

        return cls(
            content=(
                page.content if isinstance(page, PaginatorOption) else page
            ),  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            label=label,
            value=value,
            description=description,
            emoji=emoji,
        )


class SelectOptionsPaginator[PageT](BaseClassPaginator[PageT]):
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

        Note that a nested list ([1, 2, 3, [4, 5, 6]]) is not supported.
    per_select: Optional[:class:`int`]
        The amount of options per select. Defaults to :attr:`SelectOptionsPaginator.MAX_SELECT_OPTIONS`.
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

        .. versionadded:: 0.2.2
    set_default_on_switch: :class:`bool`
        Whether to set the first option of each "page" as the default option.

        This is also used when sending the paginator for the first time.

        Defaults to ``True``.

        .. versionadded:: 0.2.2
    set_default_on_select: :class:`bool`
        Whether to set the selected option as the default option. Defaults to ``True``.

        .. versionadded:: 0.2.2
    default_option: Optional[:class:`discord.SelectOption`]
        The option to get the metadata from if the a page is not an instance of :class:`PaginatorOption`.
        If this is ``None``, it will try to get the metadata from the page itself.
        E,g if the page is an embed, it will try to get the title or description, etc and use that as the label.

        Defaults to ``None``.

        .. deprecated:: 0.2.2
            This parameter is deprecated and will be removed in a future version. It is recommended to use :class:`PaginatorOption` instead.
    """

    if TYPE_CHECKING:
        from ._types import BaseKwargs

        async def get_page_kwargs(
            self, page: PaginatorOption[PageT]
        ) -> BaseKwargs:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
            ...

        pages: list[list[PaginatorOption[PageT]]]  # pyright: ignore[reportIncompatibleVariableOverride] # dwai

    MAX_SELECT_OPTIONS: ClassVar[Literal[25]] = 25
    """The maximum amount of options per select by discord by the time of writing this."""

    def __init__(
        self,
        pages: Sequence[
            Union[
                PageT,
                PaginatorOption[PageT],
                Sequence[PageT],
                Sequence[PaginatorOption[PageT]],
            ]
        ],
        *,
        per_select: int = discord.utils.MISSING,
        set_default_on_switch: bool = True,
        set_default_on_select: bool = True,
        add_in_order: bool = False,
        default_option: Optional[discord.SelectOption] = None,
        **kwargs: Unpack[BasePaginatorKwargs[Self]],
    ) -> None:
        if default_option is not None:
            import warnings

            warnings.warn(
                (
                    "The 'default_option' parameter is deprecated since v0.2.2 and will be removed in a future version. "
                    "It is recommended to use PaginatorOption instead."
                ),
                DeprecationWarning,
                stacklevel=2,
            )

        self.per_select: int = per_select or self.MAX_SELECT_OPTIONS
        self._default_on_switch: bool = set_default_on_switch
        self._default_on_select: bool = set_default_on_select

        if "per_page" in kwargs:
            raise TypeError("per_page cannot be changed for SelectOptionsPaginator")

        kwargs["per_page"] = 1
        super().__init__(
            self._construct_options(pages=pages, add_in_order=add_in_order, default_option=default_option),  # type: ignore
            **kwargs,
        )

        # None means the options were just set / paginator has not been sent yet
        self.current_option_index: int | None = None
    # --- Properties ----------------------------------------------------------
    async def format_page(
        self, page: PaginatorOption[PageT]
    ) -> Union[PageT, Sequence[PageT]]:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
        """This method can be overridden to format the page before sending it.
        By default, it returns the page's content.

        Parameters
        ----------
        page: :class:`PaginatorOption`
            The option to format.

            Use the ``content`` attribute to get the contents of the page.

            .. versionchanged:: 0.2.2
                This is now the selected option instead of the page's contents.

        Returns
        -------
        Union[Any], Sequence[Any]]
            The formatted page(s).
        """
        return page.content

    async def on_select(self, interaction: discord.Interaction[Any], option: PaginatorOption[PageT]) -> None:
        """This method is called when an option is selected.

        This method can be overridden to provide custom behavior when an option is selected.
        This method is called after the select is updated and does nothing by default.

        .. versionadded:: 0.2.2

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that triggered the select.
        option: :class:`PaginatorOption`
            The selected option.
        """
        pass

    def get_page(
        self, page_number: int
    ) -> PaginatorOption[PageT]:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
        pages: Sequence[PaginatorOption[PageT]] = super().get_page(
            page_number
        )  # pyright: ignore[reportAssignmentType] # it's a list of PaginatorOption
        option: PaginatorOption[PageT] = pages[self.current_option_index or 0]
        return option

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        super(__class__, type(self)).current_page.__set__(self, value)  # type: ignore
        self.update_select_state()
    # --- UI state management -------------------------------------------------
    def update_select_state(
        self,
    ) -> None:
        options = self.__handle_options(self.pages[self.current_page].copy())
        self.select_page.options = list(options)
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1
        self.select_page.placeholder = f"Select a page | {self.page_string}"

    # --- UI callbacks --------------------------------------------------------
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, row=1)
    async def previous_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        new_page = self.current_page - 1
        await self.switch_page(interaction, new_page)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        new_page = self.current_page + 1
        await self.switch_page(interaction, new_page)

    @discord.ui.select(cls=discord.ui.Select[Any], placeholder="Select a page", row=0)
    async def select_page(self, interaction: discord.Interaction[Any], _: discord.ui.Select[Any]) -> None:
        await self.switch_page(interaction, self.current_page)
        await self.on_select(interaction, self.get_page(self.current_page))

    async def _send(self, *args: Any, **kwargs: Any) -> Optional[discord.Message]:
        self.update_select_state()
        return await super()._send(*args, **kwargs)
