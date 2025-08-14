from __future__ import annotations
import inspect
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, Union, overload

import logging
from collections.abc import Coroutine
from math import ceil

import discord

from . import utils as _utils
from .ttl_cache import MaybeTTLPages

if TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import PaginatorCheck, BaseKwargs, Destination, Sequence
else:
    PaginatorCheck = Callable[[Any, discord.Interaction[Any]], bool | Coroutine[Any, Any, bool]]


__all__ = ("BaseClassPaginator",)

_log = logging.getLogger(__name__)


class _PaginatorView(discord.ui.View):
    _get_parent: Callable[[], BaseClassPaginator[Any]]

    async def on_timeout(self) -> None:
        await self._get_parent().on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self._get_parent().interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self._get_parent().stop()
        return super().stop()


class _PaginatorLayoutView(discord.ui.LayoutView):
    _get_parent: Callable[[], BaseClassPaginator[Any]]

    async def on_timeout(self) -> None:
        await self._get_parent().on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self._get_parent().interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self._get_parent().stop()
        return super().stop()


class BaseClassPaginator[PageT: Any]:
    """Base class for all paginators.

    Parameters
    -----------
    pages: Sequence[Any]
        A sequence of pages to paginate.
        Supported types for pages:

        - :class:`str`: Will be set as the content of the message.
        - :class:`.discord.Embed`: Will be appended to the embeds of the message.
        - :class:`.discord.File`: Will be appended to the files of the message.
        - :class:`.discord.Attachment`: Calls :meth:`~discord.Attachment.to_file()` and appends it to the files of the message.
        - :class:`discord.ui.Item`: Will be appended to the items of the view. See the warning below if item is a v2 component.
        - :class:`dict`: Will be updated with the kwargs of the message. Beware of v2 component restrictions.
        - Sequence[Any]: Will be flattened and each entry will be handled as above.

        Sequence = List, Tuple

        Any other types will probably be ignored.
        You can hot swap the pages at any time by setting this attribute.

        .. warning::
            The types and behavior of the items changes depending on the types you passed OR the ``components_v2`` parameter.

            Passing a :class:`discord.ui.Item` will add it to the view, but if the item is a v2 component
            (e.g. :class:`discord.ui.Container`) OR ``components_v2`` is set to True, it is not
            allowed to include any embeds, content or attachments in a message. So the paginator will do
            following to "work around" that:

            - Pages with type :class:`str` will be converted to :class:`discord.ui.TextDisplay`
            - Pages with type :class:`discord.Embed` are not allowed, so that will raise an error.
            - Pages with type :class:`discord.File` or :class:`discord.Attachment` are allowed because
            you can attach those to a :class:`discord.ui.MediaGallery`, :class:`discord.ui.MediaGalleryItem`,
            :class:`discord.ui.File` or :class:`discord.ui.Thumbnail`.

            Example
            -------

            .. code-block:: python3

                page = Page(discord.ui.TextDisplay("Page 1"))
                # or multiple items
                page = Page(discord.ui.TextDisplay("Page 1"), discord.ui.TextDisplay("Page 2"))
                # ^ on one page

    per_page: :class:`int`
        The amount of pages to display per page.
        Defaults to ``1``.

        E,g: If ``per_page`` is ``2`` and ``pages`` is ``[Page("1"), Page("2"), Page("3"), Page("4")]``, then the message
        will show ``[Page("1"), Page("2")]`` on the first page and ``[Page("3"), Page("4")]`` on the second page.
    author_id: Optional[:class:`int`]
        The id of the user who can interact with the paginator.
        Defaults to ``None``.
    check: Optional[Callable[[:class:`.BaseClassPaginator`, :class:`discord.Interaction`], Union[:class:`bool`, Coroutine[Any, Any, :class:`bool`]]]]
        A callable that checks if the interaction is valid. This must be a callable that takes 2 or 3 parameters.
        The last two parameters represent the interaction and paginator respectively.
        It CAN be a coroutine.

        This is called in :meth:`~discord.ui.View.interaction_check`.

        If ``author_id`` is not ``None``, this won't be called.
        Defaults to ``None``.
    always_allow_bot_owner: :class:`bool`
        Whether to always allow the bot owner to interact with the paginator.
        Defaults to ``False``.

        .. versionchanged:: 1.0.0
            Now defaults to ``False`` instead of ``True`` to prevent
            unexpected behavior.
    delete_message_after: :class:`bool`
        Whether to delete the message after the paginator stops.
        Defaults to ``False``.
    disable_items_after: :class:`bool`
        Whether to disable the paginator after the paginator stops.
        Defaults to ``False``.
    clear_items_after: :class:`bool`
        Whether to clear the items after the paginator stops.
        Defaults to ``False``.
    message: Optional[:class:`discord.Message`]
        The message to use for the paginator.
        Defaults to ``None``.
    add_page_string: :class:`bool`
        Whether to add the page string to the page. Defaults to ``True``.
        This is a string that represents the current page and the max pages. E,g: ``"Page 1 of 2"``.

        If the page is an embed, it will be appended to the footer text.
        If the page is a string, it will be appended to the string.
        else, it will be set as the content of the message.

    components_v2: bool
        Whether to use the v2 component system. See `pages` for more information.

        Defaults to ``False``.
    auto_wrap_in_actionrow: :class:`bool`
        Whether to automatically wrap items that require it into a :class:`discord.ui.ActionRow`.

        Defaults to ``False``.
    timeout: Optional[Union[:class:`int`, :class:`float`]]
        The timeout for the view.
        Defaults to ``180.0``.
    """

    _get_base_kwargs: Callable[[], BaseKwargs]

    def __init__(
        self,
        pages: Sequence[PageT] | None = discord.utils.MISSING,
        *,
        per_page: int = 1,
        author_id: int | None = None,
        check: PaginatorCheck[Self] | None = None,
        always_allow_bot_owner: bool = False,
        delete_message_after: bool = False,
        disable_items_after: bool = False,
        clear_items_after: bool = False,
        message: discord.Message | None = None,
        add_page_string: bool = True,
        switch_pages_humanly: bool = False,
        timeout: int | float | None = 180.0,
        components_v2: bool = discord.utils.MISSING,
        auto_wrap_in_actionrow: bool = False,
        pages_on_demand: bool = False,
        cache_pages: bool = False,
        max_cache_time: int | float | None = discord.utils.MISSING,
    ) -> None:
        self.__view: _PaginatorView | _PaginatorLayoutView
        self.__components_v2: bool = components_v2 or auto_wrap_in_actionrow
        self._initial_pages: bool = pages is not discord.utils.MISSING

        if pages:
            if components_v2 or any(isinstance(page, discord.ui.Item) and page._is_v2() for page in pages):
                if any(isinstance(page, discord.Embed) for page in pages):
                    raise TypeError(
                        "Cannot use discord.Embed with components_v2 or v2 components. Use a discord.ui.Container instead."
                    )

                self.__components_v2 = True
            else:
                self.__components_v2 = False
        else:
            if components_v2 is discord.utils.MISSING:
                raise ValueError("components_v2 must be specified if no pages are provided.")

        if components_v2:
            self.__view = _PaginatorLayoutView(timeout=timeout)
        else:
            self.__view = _PaginatorView(timeout=timeout)

        self.__view._get_parent = lambda: self

        self._per_page: int = per_page
        self._pages_on_demand: bool = pages_on_demand or cache_pages or (max_cache_time is not discord.utils.MISSING)
        self._max_cache_time: int | float | None = max_cache_time

        if self._pages_on_demand and cache_pages and max_cache_time is not discord.utils.MISSING:
            if max_cache_time is None:
                self._max_cache_time = 5 * 60
            else:
                if not isinstance(max_cache_time, (int, float)):
                    raise TypeError("max_cache_time must be an int or float.")
                self._max_cache_time = max_cache_time

        self._cache_pages: bool = cache_pages or max_cache_time is not discord.utils.MISSING

        self._pages: MaybeTTLPages[PageT] | Sequence[PageT]
        if pages_on_demand and cache_pages:
            self._pages = MaybeTTLPages(pages or [], self._max_cache_time)
        else:
            self._pages = pages or []

        self.__replace_str_with_text_display()
        self._current_page: int = 0

        self.author_id: int | None = author_id
        self._check: PaginatorCheck[Self] | None = check

        self.always_allow_bot_owner: bool = always_allow_bot_owner
        self.delete_message_after: bool = delete_message_after
        self.disable_items_after: bool = disable_items_after
        self.clear_items_after: bool = clear_items_after
        self.add_page_string: bool = add_page_string
        self.switch_pages_humanly: bool = switch_pages_humanly
        self._auto_wrap_in_actionrow: bool = auto_wrap_in_actionrow

        self.message: discord.Message | None = message

        self.__owner_ids: set[int] | None = None
        self.__uses_commands_bot: bool | None = None

        self._reset_base_kwargs()

        self._get_base_kwargs = lambda: self.__base_kwargs

    async def __is_bot_owner(self, interaction: discord.Interaction[Any]) -> bool:
        if self.__uses_commands_bot is None:
            from discord.ext.commands import Bot

            self.__uses_commands_bot = isinstance(interaction.client, Bot)
            del Bot

        if self.__uses_commands_bot:
            return await interaction.client.is_owner(interaction.user)

        if self.__owner_ids is not None:
            return interaction.user.id in self.__owner_ids

        self.__owner_ids = await _utils.__get_bot_owner_ids(interaction.client)
        return interaction.user.id in self.__owner_ids

    def _clear_all_view_items(self) -> None:
        self.view.clear_items()

    def _reset_base_kwargs(self) -> None:
        if self.__components_v2:
            self.__base_kwargs: BaseKwargs = {}
        else:
            self.__base_kwargs: BaseKwargs = {
                "content": None,
                "embeds": [],
            }

        self.__base_kwargs["view"] = self.view
        self._clear_all_view_items()

    def _disable_all_children(self) -> None:
        for child in self.view.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # pyright: ignore[reportAttributeAccessIssue]

    async def _handle_checks(self, interaction: discord.Interaction[Any]) -> bool:
        """Handles the checks for the paginator.

        This is called in :meth:`~discord.ui.View.interaction_check` / :meth:`~discord.ui.LayoutView.interaction_check`.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction to check.

        Returns
        -------
        :class:`bool`
            Whether the interaction is valid or not.
        """
        _log.debug("Checking interaction %s", interaction)
        if self.always_allow_bot_owner and await self.__is_bot_owner(interaction):
            _log.debug(
                "Allowing bot owner %s to interact with the paginator since always_allow_bot_owner is True", interaction.user
            )
            return True
        elif self.author_id is not None:
            _log.debug("Checking if %s equals %s", interaction.user, self.author_id)
            return interaction.user.id == self.author_id
        elif self._check:
            _log.debug("Calling check %s", self._check)
            return await discord.utils.maybe_coroutine(self._check, self, interaction)

        _log.debug("No checks to run, allowing interaction")
        return True

    def _do_format_page(self, page: PageT | Sequence[PageT]) -> Coroutine[Any, Any, Union[PageT, Sequence[PageT]]]:
        return discord.utils.maybe_coroutine(self.format_page, page)

    def __replace_str_with_text_display(self) -> None:
        if not self.__components_v2:
            return

        for i, page in enumerate(self.pages):
            if isinstance(page, (int, str)):
                self._pages[i] = (  # pyright: ignore[reportArgumentType, reportIndexIssue, reportCallIssue]
                    discord.ui.TextDisplay(str(page))
                )

    def _handle_page_string(self) -> None:
        if not self.add_page_string or self.__components_v2:
            return

        embeds = self.__base_kwargs.get("embeds", [])
        content = self.__base_kwargs.get("content")
        if embeds:
            for embed in embeds:
                to_set = self.page_string
                if footer_text := embed.footer.text:
                    if "|" in footer_text:
                        footer_text = footer_text.split("|")[0].strip()
                        to_set = f"{footer_text} | {self.page_string}"

                embed.set_footer(text=to_set)
        elif content:
            self.__base_kwargs["content"] = f"{content}\n{self.page_string}"
        else:
            self.__base_kwargs["content"] = self.page_string

    async def _edit_message(self, interaction: Optional[discord.Interaction[Any]] = None, /, **kwargs: Any) -> None:
        """Edits the message with the given kwargs.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit. If available.
        **kwargs: Any
            The kwargs to edit the message with.

        Raises
        ------
        ValueError
            If ``interaction`` is ``None`` and :attr:`.BaseClassPaginator.message` is ``None``.
        """
        kwargs.pop("ephemeral", None)

        files_to_edit: list[discord.File] = []

        atachments_or_Files = kwargs.pop("files", []) + kwargs.pop("attachments", [])
        if atachments_or_Files:
            for file in atachments_or_Files:
                files_to_edit.append(await _utils._new_file(file))

        kwargs["attachments"] = files_to_edit

        if interaction:
            if interaction.response.is_done():
                await interaction.edit_original_response(**kwargs)
            else:
                await interaction.response.edit_message(**kwargs)
        elif self.message:
            await self.message.edit(**kwargs)

        if self.view.is_finished():
            await self.stop_paginator()

    def _wrap_in_actionrow(
        self, item: discord.ui.Button[Any] | discord.ui.Select[Any]
    ) -> tuple[discord.ui.ActionRow[Any] | None, bool]:
        if not isinstance(item, (discord.ui.Button, discord.ui.Select)):
            return None, False

        existing_actionrow = next(
            (
                child
                for child in self.view.walk_children()
                if isinstance(child, discord.ui.ActionRow) and child.id not in (90, 100)
            ),
            None,
        )
        print("Existing action row:", existing_actionrow, existing_actionrow.id if existing_actionrow else None)
        if existing_actionrow and len(existing_actionrow.children) < 5 and (existing_actionrow._weight + item.width) < 5:
            existing_actionrow.add_item(item)
            return existing_actionrow, False

        actionrow = discord.ui.ActionRow[Any]()
        actionrow.add_item(item)
        return actionrow, True

    def _add_item[Item: discord.ui.Item[Any]](self, item: Item) -> Item:
        self.view.add_item(item)
        return item

    @property
    def view(self) -> discord.ui.View | discord.ui.LayoutView:
        """Returns the view of the paginator. The type depends on the pages passed to the paginator."""
        return self.__view

    @property
    def current_page(self) -> int:
        """:class:`int`: The current page. Starts from ``0``."""
        if self._current_page <= 0:
            self._current_page = 0
        elif self._current_page >= self.max_pages:
            self._current_page = self.max_pages - 1
        elif self.per_page == 0:
            self._current_page = 0
        elif self.per_page == 1:
            self._current_page = self._current_page % len(self.pages)
        else:
            self._current_page = self._current_page % self.max_pages

        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        """:class:`int`: Sets the current page to the given value."""
        if value <= 0:
            self._current_page = 0
        else:
            self._current_page = max(0, min(value, self.max_pages - 1))

    @property
    def page_string(self) -> str:
        """:class:`str`: A string representing the current page and the max pages."""
        if self._pages_on_demand and not self._cache_pages:
            return f"Page {self.current_page + 1}"

        return f"Page {self.current_page + 1} of {self.max_pages}"

    @property
    def pages(self) -> Sequence[PageT] | MaybeTTLPages[PageT]:
        """Sequence[Any]: The pages of the paginator."""
        return self._pages

    @pages.setter
    def pages(self, value: Sequence[PageT]) -> None:
        """Sets the pages of the paginator."""

        if not isinstance(value, (list, tuple)):
            raise TypeError("pages must be a list or tuple.")

        if self.__components_v2 and any(not isinstance(page, (discord.ui.Item, str)) for page in value):
            raise TypeError("Cannot swap v2 components with non-v2 components after construction.")

        if self.per_page > len(value):
            raise ValueError("per_page cannot be greater than the amount of pages.")

        if isinstance(self._pages, MaybeTTLPages):
            self._pages.replace_pages(value)
        else:
            self._pages = value

        self.__replace_str_with_text_display()

    @property
    def per_page(self) -> int:
        """:class:`int`: The amount of pages to display per page."""
        return self._per_page

    @per_page.setter
    def per_page(self, value: int) -> None:
        """Sets the amount of pages to display per page."""
        if not isinstance(value, int):
            raise TypeError("per_page must be an int.")

        if value < 1:
            raise ValueError("per_page must be greater than 0.")

        if value > len(self.pages):
            raise ValueError("per_page cannot be greater than the amount of pages.")

        self._per_page = value

    @property
    def max_pages(self) -> int:
        """int: The max pages of the paginator."""
        if self._pages_on_demand and self._cache_pages:
            current_pages = len(self.pages)
            if current_pages < self.current_page + 1:
                return self.current_page + 1

        return ceil(len(self.pages) / self.per_page)

    def stop(self) -> None:
        """Stops the view and resets the base kwargs."""
        self._reset_base_kwargs()
        self.message = None

    async def on_timeout(self) -> None:
        """This method is called when the paginator times out.

        This method does the following checks (in order):
        - Calls :meth:`.BaseClassPaginator.stop_paginator`.
        - Calls :meth:`discord.ui.View.on_timeout` / :meth:`discord.ui.LayoutView.on_timeout`.
        """
        await self.stop_paginator()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        """This method is called by the library when the paginator receives an interaction.

        This method does the following checks (in order):

        - If ``always_allow_bot_owner`` is ``True``, it checks if the interaction's author id is one of the bot owners.
        - If ``author_id`` is not ``None``, it checks if the interaction's author id is the same as the one set.
        - If ``check`` is not ``None``, it calls it and checks if it returns ``True``.
        - If none of the above checks are ``True``, it returns ``False``.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction received.
        """
        return await self._handle_checks(interaction)

    async def format_page(self, page: PageT | Sequence[PageT]) -> Sequence[PageT]:
        return page

    async def stop_paginator(self, interaction: Optional[discord.Interaction[Any]] = None) -> None:
        """Stops the paginator.

        This method does handles deleting the message, disabling the paginator and clearing the buttons.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            Optionally, the last interaction to edit. If ``None``, ``.message`` is used.
        """
        if self.delete_message_after:
            if interaction:
                if not interaction.response.is_done():
                    await interaction.response.defer()
                await interaction.delete_original_response()
            elif self.message:
                await self.message.delete()

            self.stop()
            return

        if self.disable_items_after or self.clear_items_after:
            if self.clear_items_after:
                self.view.clear_items()
            else:
                self._disable_all_children()

            if interaction:
                await interaction.response.defer()
                await interaction.edit_original_response(view=self.view)
            elif self.message:
                await self.message.edit(view=self.view)

            self.stop()
            return

    def get_page(self, page_number: int) -> PageT | Sequence[PageT]:
        """Gets the page with the given page number.

        Parameters
        ----------
        page_number: :class:`int`
            The page number to get.

        Returns
        -------
        Page | Sequence[Page]
            The page(s) with the given page number.
        """
        if not self.pages:
            raise ValueError(
                "No pages are available.\n"
                "Possible solutions:\n"
                "- Provide a non-empty 'pages' sequence when creating the paginator, or assign to '.pages' before sending.\n"
                "- Or implement 'get_next_pages', 'get_previous_pages', and 'get_initial_pages' to load pages on demand.\n"
                "- Optional: If loading on demand, enable 'cache_pages=True' and set 'max_cache_time' (seconds) to cache results and avoid repeated work."
            )

        page_number = max(0, min(page_number, self.max_pages - 1))
        if isinstance(self.pages, MaybeTTLPages):
            return self.pages[page_number]

        if self.per_page == 1:
            return self.pages[page_number]
        base = page_number * self.per_page
        return self.pages[base : base + self.per_page]

    async def __get_pages_on_demand(
        self,
        interaction: discord.Interaction[Any],
        /,
        to_call: Callable[[discord.Interaction[Any], int], Coroutine[Any, Any, PageT | Sequence[PageT]]],
        before: int,
    ) -> PageT | Sequence[PageT]:
        try:
            cached = self.pages[self.current_page]
            return cached
        except KeyError:
            pages = await to_call(interaction, before)

            if self._cache_pages and isinstance(self.pages, MaybeTTLPages):
                self.pages[self.current_page] = pages

            return pages

    async def __get_initial_pages(
        self,
    ) -> PageT | Sequence[PageT]:
        pages = await self.get_initial_pages()
        if self._cache_pages and isinstance(self.pages, MaybeTTLPages):
            self.pages[self.current_page] = pages
        return pages

    async def get_initial_pages(
        self,
    ) -> PageT | Sequence[PageT]:
        if self._pages_on_demand:
            msg = (
                "get_initial_pages must be implemented if any of the following are set: "
                "pages_on_demand, cache_pages, or max_cache_time."
            )
            raise NotImplementedError(msg)

        return self.get_page(0)

    async def get_next_pages(
        self,
        interaction: discord.Interaction[Any],
        before: int,
    ) -> PageT | Sequence[PageT]:
        if self._pages_on_demand:
            msg = (
                "get_next_pages must be implemented if any of the following are set: "
                "pages_on_demand, cache_pages, or max_cache_time."
            )
            raise NotImplementedError(msg)
        return self.get_page(self.current_page)

    async def get_previous_pages(
        self,
        interaction: discord.Interaction[Any],
        before: int,
    ) -> PageT | Sequence[PageT]:
        if self._pages_on_demand:
            msg = (
                "get_previous_pages must be implemented if any of the following are set: "
                "pages_on_demand, cache_pages, or max_cache_time. "
            )
            raise NotImplementedError(msg)
        return self.get_page(self.current_page)

    async def on_next_page(self, interaction: discord.Interaction[Any], before: int) -> None:
        """Called when the paginator goes to the next page.

        This method is called after the page is switched and does nothing by default.

        .. versionadded:: 0.2.2

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that triggered the event.
        before: :class:`int`
            The page number before.
        current: :class:`int`
            The current number after.
        """
        pass

    async def on_previous_page(self, interaction: discord.Interaction[Any], before: int) -> None:
        """Called when the paginator goes to the previous page.

        This method is called after the page is switched and does nothing by default.

        .. versionadded:: 0.2.2

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that triggered the event.
        before: :class:`int`
            The page number before.
        current: :class:`int`
            The current number after.
        """
        pass

    def _after_handling_pages(self) -> None:
        pass

    async def handle_pages(self, page: PageT | Sequence[PageT], /, skip_formatting: bool = False) -> BaseKwargs:
        print(
            "handle pages called from:",
            inspect.stack()[1].function,
        )
        print(
            "Handling pages:",
            page,
            type(page),
        )
        if not skip_formatting:
            self._reset_base_kwargs()
            return await self.handle_pages(await self._do_format_page(page), skip_formatting=True)

        # Sequence[Page[PageT]]
        if isinstance(page, (list, tuple)):
            pages: Sequence[PageT] = page  # pyright: ignore[reportUnknownVariableType]
            inner_page: PageT
            for inner_page in pages:
                await self.handle_pages(inner_page, skip_formatting=True)

        if isinstance(page, (int, str, discord.ui.TextDisplay)):
            if isinstance(page, discord.ui.TextDisplay):
                self._add_item(page)  # pyright: ignore[reportUnknownArgumentType]
            elif not self.__components_v2:
                try:
                    self.__base_kwargs[
                        "content"
                    ] += str(  # pyright: ignore[reportTypedDictNotRequiredAccess, reportOperatorIssue]
                        page
                    )
                except Exception:
                    self.__base_kwargs["content"] = str(page)
            else:
                self._add_item(discord.ui.TextDisplay[Any](str(page)))
        elif isinstance(page, discord.Embed):
            if not self.__components_v2:
                self.__base_kwargs.setdefault("embeds", []).append(page)
        elif isinstance(page, (discord.File, discord.Attachment)):
            file = await _utils._new_file(page)
            self.__base_kwargs.setdefault("files", []).append(file)

        elif isinstance(page, dict):
            # kinda the same thing as above but it didn't appricate that it
            # didn't know the type of the key&value so it was "dict[Unknown, Unknown]"
            data: dict[Any, Any] = page.copy()  # pyright: ignore[reportUnknownVariableType]
            self.__base_kwargs.update(data)
        elif isinstance(page, discord.ui.Item):
            if self.__components_v2 and isinstance(page, (discord.ui.Button, discord.ui.Select)):
                if self._auto_wrap_in_actionrow:
                    row, add_to_view = self._wrap_in_actionrow(page)  # pyright: ignore[reportUnknownArgumentType]
                    if row and add_to_view:
                        self._add_item(row)
                else:
                    raise ValueError(
                        f"Cannot add a {type(page)!r} to the paginator without wrapping it in an action row. "  # pyright: ignore[reportUnknownArgumentType]
                        "Either wrap it in an action row or set `auto_wrap_in_actionrow` to True in the paginator."
                    )
            else:
                self._add_item(page)  # pyright: ignore[reportUnknownArgumentType]

        return self.__base_kwargs

    @staticmethod
    def _should_switch_page(before: int, after: int) -> bool:
        return before != after

    async def switch_page(self, interaction: Optional[discord.Interaction[Any]], page_number: int) -> None:
        """Switches the page to the given page number.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit. If ``None``, ``.message`` is used.
        page_number: :class:`int`
            The page number to switch to.
        """
        previous_page_number: int = self.current_page
        self.current_page = page_number
        if previous_page_number == self.current_page:
            if interaction and not interaction.response.is_done():
                await interaction.response.defer()
            return

        if not interaction:
            pages = self.get_page(page_number)
        else:
            try:
                if page_number > previous_page_number:
                    pages = await self.__get_pages_on_demand(interaction, self.get_next_pages, previous_page_number)
                else:
                    pages = await self.__get_pages_on_demand(interaction, self.get_previous_pages, previous_page_number)
            except IndexError:
                self.current_page = previous_page_number
                raise

        page_kwargs = await self.handle_pages(pages)
        self._after_handling_pages()
        # self._handle_page_string()

        print(
            "CHILDREN",
            self.view.children,
            list(self.view.walk_children()),
            [i.id for i in list(self.view.walk_children())],
            sep="\n",
        )
        await self._edit_message(interaction, **page_kwargs)

        if interaction:
            if page_number > previous_page_number:
                await self.on_next_page(interaction=interaction, before=previous_page_number)
            else:
                await self.on_previous_page(interaction=interaction, before=previous_page_number)

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = ...,
        edit_message: Literal[True] = ...,
        **send_kwargs: Any,
    ) -> None: ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = ...,
        edit_message: Literal[False] = ...,
        **send_kwargs: Any,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: Literal[False] = ...,
        edit_message: bool = ...,
    ) -> Optional[discord.Message]: ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: Literal[True] = ...,
        edit_message: bool = ...,
        **send_kwargs: Any,
    ) -> Optional[discord.Message]: ...

    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = False,
        edit_message: bool = False,
        **send_kwargs: Any,
    ) -> Optional[discord.Message]:
        """Sends the message to the given destination.

        Parameters
        ----------
        destination: Union[:class:`discord.abc.Messageable`, :class:`discord.Interaction`]
            The destination to send the message to. Handles responding to the interaction if given.
        override_page_kwargs: :class:`bool`
            Whether to override the page kwargs with the given kwargs to ``send_kwargs``.
            Defaults to ``True``.

            .. versionchanged:: 1.0
               The default value was changed to ``True``.
        edit_message: :class:`bool`
            Whether to edit the message instead of sending a new one.
            Defaults to ``False``.
        **send_kwargs: Any
            The kwargs to pass to the destination's send method. Only used if ``override_page_kwargs`` is ``True``.

        Returns
        -------
        Optional[:class:`discord.Message`]
            The message or response sent.
        """
        return await self._send(
            destination, override_page_kwargs=override_page_kwargs, edit_message=edit_message, **send_kwargs
        )

    async def _send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = True,
        edit_message: bool = False,
        **send_kwargs: Any,
    ) -> Optional[discord.Message]:
        if self.current_page > 0:
            pages = self.get_page(self.current_page)
        else:
            pages = await self.__get_initial_pages()

        page_kwargs: dict[str, Any] = await self.handle_pages(pages)  # pyright: ignore[reportAssignmentType]
        self._after_handling_pages()

        if override_page_kwargs:
            page_kwargs |= send_kwargs

        print(
            "SENDING VIEW",
            self.view,
            self.view.children,
            list(self.view.walk_children()),
            [x.id for x in self.view.walk_children()],
        )

        if edit_message:
            return await self._edit_message(
                destination if isinstance(destination, discord.Interaction) else None, **page_kwargs
            )

        elif isinstance(destination, discord.Interaction):
            if destination.response.is_done():
                self.message = await destination.followup.send(**page_kwargs, wait=True)
            else:
                response = await destination.response.send_message(**page_kwargs)
                if response and isinstance(response.resource, discord.InteractionMessage):
                    self.message = response.resource
                else:
                    self.message = await destination.original_response()

        else:
            self.message = await destination.send(**page_kwargs)

        return self.message
