from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    Optional,
    Union,
)
from collections.abc import Sequence

import os

import discord

from .base_paginator import BaseClassPaginator
from ._types import PageT

if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from ._types import BasePaginatorKwargs
else:
    Self = Unpack = BasePaginatorKwargs = Any


__all__ = (
    "PaginatorOption",
    "SelectOptionsPaginator",
)


class PaginatorOption(discord.SelectOption, Generic[PageT]):
    """A subclass of :class:`discord.SelectOption` representing a page in a :class:`SelectOptionsPaginator`.

    Other parameters are the same as :class:`~.discord.SelectOption`.

    Parameters
    ----------
    content: Union[Any, Sequence[Any]]
        The content of the page. See :class:`SelectOptionsPaginator` for more the supported types.
    label_from_content: :class:`bool`
        Whether to base the label of the option from the content.
        E.g. if the content is an embed, it will try to get the title or author name, etc and use that as the label.

        Defaults to ``True`` if ``label`` is not provided.
    """

    def __init__(
        self,
        content: Union[PageT, Sequence[PageT]],
        *,
        label: str = discord.utils.MISSING,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
        label_from_page: bool = True,
    ) -> None:
        self.content: Union[PageT, Sequence[PageT]] = content
        if not label and label_from_page:
            label = self.__label_from_content()

        super().__init__(label=label, value=self.__ensure_unique_value(label, value), description=description, emoji=emoji)

    def __str__(self) -> str:
        return self.content if isinstance(self.content, str) else str(self.content) or self.label

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} label={self.label!r}>"

    def copy(self: Self) -> Self:
        return self.__class__(
            self.content, label=self.label, emoji=self.emoji, value=self.value, description=self.description
        )

    def __label_from_content(self) -> str:
        if isinstance(self.content, discord.Embed):
            return (
                self.content.title
                or self.content.description
                or self.content.author.name
                or self.content.footer.text
                or "Untitled"
            )
        elif isinstance(self.content, (discord.File, discord.Attachment)):
            return self.content.filename
        elif isinstance(self.content, (int, str)):
            return str(self.content)

        return "Untitled"

    def __ensure_unique_value(self, label: str = discord.utils.MISSING, value: str = discord.utils.MISSING) -> str:
        if value != label:
            return value or label

        return (str(os.urandom(16).hex()) if value == label else "")[:99]


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

        Note that a nested list ([1, 2, 3, [4, 5, 6]]) is not supported.
    per_select: Optional[:class:`int`]
        The amount of options per select. Defaults to :attr:`SelectOptionsPaginator.MAX_SELECT_OPTIONS`.
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

        async def get_page_kwargs(self, page: PaginatorOption[PageT]) -> BaseKwargs:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
            ...

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
        default_option: Optional[discord.SelectOption] = None,
        **kwargs: Unpack[BasePaginatorKwargs],
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
            self._construct_options(pages),  # type: ignore
            **kwargs,
        )
        self.current_option_index: int = 0

    def _construct_options(self, pages: Sequence[Sequence[PageT]]) -> list[list[PaginatorOption[PageT]]]:
        def actual_construct(page: Union[PageT, PaginatorOption[PageT]]) -> PaginatorOption[PageT]:
            if isinstance(page, PaginatorOption):
                return page.copy()  # pyright: ignore[reportUnknownVariableType] # it's a PaginatorOption dwai

            return PaginatorOption[PageT](page)

        res: list[list[PaginatorOption[PageT]]] = []
        options: list[PaginatorOption[PageT]] = []

        for page in pages:
            # Sequence
            if isinstance(page, (list, tuple)):
                nested_options = [actual_construct(item) for item in page]

                if len(nested_options) > self.per_select:
                    raise ValueError(
                        f"Too many options for one select in nested list (max: {self.per_select}, got: {len(nested_options)})"
                    )

                res.append(nested_options)
                continue

            # PaginatorOption
            if isinstance(page, PaginatorOption):
                options.append(page)
                continue

            # Single page
            options.append(actual_construct(page))

        for option in options:
            if isinstance(option, list):
                res.append(option)
                options.remove(option)

        if len(options) > 0:
            res.extend(discord.utils.as_chunks(options, self.per_select))

        return res

    def __reset_options(self) -> None:
        for option in self.select_page.options:
            option.default = False

    async def format_page(self, page: PaginatorOption[PageT]) -> Union[PageT, Sequence[PageT]]:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
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

    def get_page(self, page_number: int) -> PaginatorOption[PageT]:  # pyright: ignore[reportIncompatibleMethodOverride] # dwai
        page: Sequence[PaginatorOption[PageT]] = super().get_page(page_number)  # pyright: ignore[reportAssignmentType] # it's a list of PaginatorOption
        option: PaginatorOption[PageT] = page[self.current_option_index]
        return option

    async def switch_page(self, interaction: Optional[discord.Interaction[Any]], page_number: int) -> None:
        self.current_option_index = 0
        self.select_page.options = self.pages[page_number]  # type: ignore
        self.__reset_options()

        if self._default_on_switch:
            self.select_page.options[self.current_option_index].default = True  # type: ignore

        self.select_page.placeholder = f"Select a page | {self.page_string}"
        self.previous_page.disabled = self.current_page <= 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1
        return await super().switch_page(interaction, page_number)

    async def switch_options(self, interaction: discord.Interaction[Any]) -> None:
        selected: str = self.select_page.values[0]
        for idx, option in enumerate(self.select_page.options):
            if option.label == selected or option.value == selected:
                self.current_option_index = idx
                break

        page = self.get_page(self.current_page)
        self.select_page.options = self.pages[self.current_page]  # type: ignore
        self.__reset_options()
        if self._default_on_select:
            self.select_page.options[self.current_option_index].default = True  # pyright: ignore[reportIndexIssue]

        kwrgs = await self.get_page_kwargs(page)
        super()._handle_page_string()
        await self._edit_message(interaction, **kwrgs)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, row=1)
    async def previous_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        if self.current_page <= 0:
            self.current_page = 0
        else:
            self.current_page -= 1

        await self.switch_page(interaction, self.current_page)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, interaction: discord.Interaction[Any], _: discord.ui.Button[Self]) -> None:
        if self.current_page >= self.max_pages - 1:
            self.current_page = self.max_pages - 1
        else:
            self.current_page += 1

        await self.switch_page(interaction, self.current_page)

    @discord.ui.select(cls=discord.ui.Select[Self], placeholder="Select a page", row=0)
    async def select_page(self, interaction: discord.Interaction[Any], _: discord.ui.Select[Any]) -> None:
        await self.switch_options(interaction)

    async def _send(self, *args: Any, **kwargs: Any) -> Optional[discord.Message]:
        self.current_option_index = 0
        self.select_page.options = self.pages[0]  # type: ignore # nothing really possible to do here
        self.__reset_options()
        self.select_page.placeholder = f"Select a page | {self.page_string}"
        self.previous_page.disabled = True
        self.next_page.disabled = self.max_pages == 1
        if self._default_on_switch:
            self.select_page.options[self.current_option_index].default = True  # type: ignore
        return await super()._send(*args, **kwargs)
