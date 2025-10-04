from __future__ import annotations
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, overload

import logging
from collections.abc import Coroutine
from math import ceil

import discord

from . import utils as _utils

if TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import PaginatorCheck, BaseKwargs, Destination, View


class PaginatorView[PaginatorT: BaseClassPaginator[Any]](discord.ui.View):
    paginator: PaginatorT

    def __init__(self, paginator: PaginatorT, *args: Any, **kwargs: Any) -> None:
        self.paginator = paginator
        super().__init__(*args, **kwargs)

    async def on_timeout(self) -> None:
        await self.paginator.on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self.paginator.interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self.paginator.stop()
        return super().stop()


class PaginatorLayoutView[PaginatorT: BaseClassPaginator[Any]](discord.ui.LayoutView):
    paginator: PaginatorT

    def __init__(self, paginator: PaginatorT, *args: Any, **kwargs: Any) -> None:
        self.paginator = paginator
        super().__init__(*args, **kwargs)

    async def on_timeout(self) -> None:
        await self.paginator.on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self.paginator.interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self.paginator.stop()
        return super().stop()


class AfterAction(IntEnum):
    """An enum that represents the action to take after the paginator stops or times out."""

    DELETE_MESSAGE = 0
    """Delete the original message."""
    DISABLE_ITEMS = 1
    """Disable all interactive items."""
    CLEAR_ITEMS = 2
    """Clear all items from the view."""
    NOTHING = 3
    """Do nothing."""


__all__ = ("BaseClassPaginator",)

_log = logging.getLogger(__name__)


class BaseClassPaginator[PageT]:
    """Base class for all paginators.

    Parameters
    -----------
    pages: list[Any]
        A sequence of pages to paginate.
        Supported types for pages:

        - :class:`str`: Will be set as the content of the message.
        - :class:`.discord.Embed`: Will be appended to the embeds of the message.
        - :class:`.discord.File`: Will be appended to the files of the message.
        - :class:`.discord.Attachment`: Calls :meth:`~discord.Attachment.to_file()` and appends it to the files of the message.
        - :class:`discord.ui.Item`: Will be appended to the items of the view. See the warning below if item is a v2 component.
        - :class:`dict`: Will be updated with the kwargs of the message. Beware of v2 component restrictions.
        - list[Any]: Will be flattened and each entry will be handled as above.

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

    per_page: :class:`int`
        The amount of pages to display per page.
        Defaults to ``1``.

        E,g: If ``per_page`` is ``2`` and ``pages`` is ``["1", "2", "3", "4"]``, then the message
        will show ``["1", "2"]`` on the first page and ``["3", "4"]`` on the second page.
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

        If `components_v2` is ``True``, it will be added as a :class:`discord.ui.TextDisplay` item instead.
        Unless a :class:`discord.ui.Container` is present, then it will be added to that container.

    components_v2: bool
        Whether to use the v2 component system. See `pages` for more information.

        Defaults to ``False``.
    timeout: Optional[Union[:class:`int`, :class:`float`]]
        The timeout for the view.
        Defaults to ``180.0``.
    """

    _get_base_kwargs: Callable[[], BaseKwargs]

    def __init__(
        self,
        pages: list[PageT] = discord.utils.MISSING,
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
        view_cls: type[View[Self]] | None = None,
        after_stop: AfterAction = AfterAction.NOTHING,
        after_timeout: AfterAction = AfterAction.NOTHING,
        title: str | discord.ui.TextDisplay[Any] | None = None,
        description: str | discord.ui.TextDisplay[Any] | None = None,
        allowed_mentions: discord.AllowedMentions | bool | None = None,
    ) -> None:
        self._initial_pages = pages is not discord.utils.MISSING
        self.__components_v2: bool = components_v2
        if pages:
            if components_v2 is discord.utils.MISSING:
                self.__components_v2 = any(isinstance(page, discord.ui.Item) and page._is_v2() for page in pages)

            if self.__components_v2:
                if any(isinstance(page, discord.Embed) for page in pages):
                    raise TypeError("Cannot use discord.Embed with components_v2. " "Use discord.ui.Container instead.")

                if any(isinstance(page, (discord.ui.Button, discord.ui.Select)) for page in pages):
                    raise TypeError(
                        "Cannot use discord.ui.Button or discord.ui.Select with components_v2. "
                        "Wrap them in discord.ui.ActionRow instead."
                    )
        elif components_v2 is discord.utils.MISSING:
            self.__components_v2 = False

        self.__view: View[Self] = self.__init_view(view_cls=view_cls, timeout=timeout)

        self._per_page: int = per_page
        self._pages: list[PageT] = []
        self.pages = pages if pages is not discord.utils.MISSING else []
        self._current_page_index: int = 0

        self.author_id: int | None = author_id
        self._check: PaginatorCheck[Self] | None = check
        self.always_allow_bot_owner: bool = always_allow_bot_owner

        self.after_stop: AfterAction = after_stop
        self.after_timeout: AfterAction = after_timeout

        self.add_page_string: bool = add_page_string
        self.switch_pages_humanly: bool = switch_pages_humanly
        self.title: str | None = title if isinstance(title, str) else title.content if title else None
        self.description: str | None = (
            description if isinstance(description, str) else description.content if description else None
        )

        self.message: discord.Message | None = message

        if allowed_mentions is not None and not isinstance(allowed_mentions, (discord.AllowedMentions, bool)):
            raise TypeError(
                f"allowed_mentions must be AllowedMentions, bool or None, not {allowed_mentions.__class__.__name__!r}."
            )

        if allowed_mentions is True:
            allowed_mentions = discord.AllowedMentions.all()
        elif allowed_mentions is False:
            allowed_mentions = discord.AllowedMentions.none()

        self.allowed_mentions: discord.AllowedMentions | None = allowed_mentions

        self.__owner_ids: set[int] | None = None
        self.__uses_commands_bot: bool | None = None

        self._reset_base_kwargs()
        self._get_base_kwargs = lambda: self.__base_kwargs

    @property
    def view(self) -> View[Self]:
        """Returns the view of the paginator. The type depends on the pages passed to the paginator."""
        return self.__view

    @property
    def current_page_index(self) -> int:
        """:class:`int`: The current page. Starts from ``0``."""
        if self._current_page_index <= 0:
            self._current_page_index = 0
        elif self._current_page_index >= self.max_pages:
            self._current_page_index = self.max_pages - 1
        elif self.per_page == 0:
            self._current_page_index = 0
        elif self.per_page == 1:
            self._current_page_index = self._current_page_index % len(self.pages)
        else:
            self._current_page_index = self._current_page_index % self.max_pages

        return self._current_page_index

    @current_page_index.setter
    def current_page_index(self, value: int) -> None:
        """:class:`int`: Sets the current page to the given value."""
        if value <= 0:
            self._current_page_index = 0
        else:
            self._current_page_index = max(0, min(value, self.max_pages - 1))

    @property
    def current_pages(self) -> list[PageT]:
        """list[Any]: The current chunk of pages."""
        return self.get_page(self.current_page_index)

    @property
    def page_string(self) -> str:
        """:class:`str`: A string representing the current page and the max pages."""
        return f"Page {self.current_page_index + 1} of {self.max_pages}"

    @property
    def pages(self) -> list[PageT]:
        """list[Any]: The pages of the paginator."""
        return self._pages

    @pages.setter
    def pages(self, value: list[PageT]) -> None:

        if not isinstance(value, list):
            raise TypeError(f"Expected a list of pages, got {value.__class__.__name__!r}.")

        if self.per_page > len(value):
            raise ValueError("per_page cannot be greater than the amount of pages.")

        if self.__components_v2 and any(not isinstance(page, (discord.ui.Item, str)) for page in value):
            raise TypeError("Non v2 components are not allowed when using components_v2.")

        self._pages = list(value)

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
        """int: The max pages on the current page."""
        return ceil(len(self.pages) / self.per_page)

    @property
    def total_pages(self) -> int:
        """int: The total amount of pages in the paginator."""
        return len(self.pages)

    def __init_view(
        self,
        view_cls: type[View[Self]] | None = None,
        timeout: int | float | None = None,
    ) -> View[Self]:
        expected_cls = PaginatorLayoutView if self.__components_v2 else PaginatorView
        if view_cls is None:
            return expected_cls(paginator=self, timeout=timeout)  # pyright: ignore[reportUnknownVariableType]

        if not issubclass(view_cls, expected_cls):
            raise TypeError(f"view_cls must be a subclass of {expected_cls.__name__!r}.")

        return view_cls(paginator=self, timeout=timeout)

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

    # --- Paging & rendering helpers -----------------------------------------
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

    def _add_item[Item: discord.ui.Item[Any]](self, item: Item) -> Item:
        self.view.add_item(item)
        return item

    # --- Lifecycle & navigation --------------------------------------------
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
        await self.stop_paginator(is_timeout=True)

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

    async def stop_paginator(self, interaction: Optional[discord.Interaction[Any]] = None, is_timeout: bool = False) -> None:
        """Stops the paginator.

        This method does handles deleting the message, disabling the paginator and clearing the buttons.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            Optionally, the last interaction to edit. If ``None``, ``.message`` is used.
        is_timeout: :class:`bool`
            Whether the paginator is stopping because of a timeout or not. This is used to determine which action to take.
            Defaults to ``False``.
        """
        action = self.after_timeout if is_timeout else self.after_stop
        if action is AfterAction.NOTHING:
            self.stop()
            return

        if action is AfterAction.DELETE_MESSAGE:
            if interaction:
                if not interaction.response.is_done():
                    await interaction.response.defer()
                await interaction.delete_original_response()
            elif self.message:
                await self.message.delete()
        else:
            if action is AfterAction.CLEAR_ITEMS:
                self.view.clear_items()
            else:
                self._disable_all_children()

            if interaction:
                await interaction.response.defer()
                await interaction.edit_original_response(view=self.view)
            elif self.message:
                await self.message.edit(view=self.view)

        self.stop()
        self._reset_base_kwargs()

    def _do_format_page(self, page: list[PageT]) -> Coroutine[Any, Any, list[PageT]]:
        return discord.utils.maybe_coroutine(self.format_page, page)

    async def format_page(self, page: list[PageT]) -> list[PageT]:
        """list[Any]: An optional coroutine that can be overridden to format the pages before they are processed and sent."""
        return page

    def get_page(self, page_number: int) -> list[PageT]:
        """Gets the pages with the given page number.

        This will return a list of pages with one item, even if there is only one page.

        Parameters
        ----------
        page_number: :class:`int`
            The page number to get.

        Returns
        -------
        list[Page]
            The pages with the given page number.
        """
        if not self.pages:
            raise ValueError(
                "No pages are available. Either provide a non-empty 'pages' sequence when creating the paginator, or assign to '.pages' before sending."
            )

        page_number = max(0, min(page_number, self.max_pages - 1))

        if self.per_page == 1:
            return [self.pages[page_number]]
        base = page_number * self.per_page
        return list(self.pages[base : base + self.per_page])

    async def on_page(self, interaction: discord.Interaction[Any], before: int, after: int) -> None:
        """Called when the paginator switches to a page.

        This method is called after the page is switched and does nothing by default.

        .. versionadded:: 0.3.0

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that triggered the change.
        before: :class:`int`
            The page number before.
        after: :class:`int`
            The page number after.
        """
        pass

    def _after_handling_pages(self) -> None:
        if not (self.title or self.description):
            return

        if self.__components_v2:
            if self.title:
                self._add_item(discord.ui.TextDisplay[Any](self.title))
            if self.description:
                self._add_item(discord.ui.TextDisplay[Any](self.description))
        else:
            if self.title or self.description:
                if self.__base_kwargs.get("content"):
                    orginal_content = self.__base_kwargs["content"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
                    if self.title:
                        orginal_content = f"**{self.title}**\n{orginal_content}"
                    if self.description:
                        orginal_content = f"{self.description}\n{orginal_content}"

                    self.__base_kwargs["content"] = orginal_content
                elif self.__base_kwargs.get("embeds"):
                    embed = self.__base_kwargs["embeds"][0]  # pyright: ignore[reportTypedDictNotRequiredAccess]
                    if self.title:
                        embed.title = self.title
                    if self.description:
                        embed.description = self.description

                else:
                    embed = discord.Embed()
                    if self.title:
                        embed.title = self.title
                    if self.description:
                        embed.description = self.description

                    self.__base_kwargs.setdefault("embeds", []).append(embed)

    async def handle_pages(self, pages: list[PageT], /, skip_formatting: bool = False) -> BaseKwargs:
        print(
            "Handling pages:",
            pages,
            type(pages),
        )
        if not skip_formatting:
            self._reset_base_kwargs()
            return await self.handle_pages(await self._do_format_page(pages), skip_formatting=True)

        for page in pages:
            # Sequence[Page[PageT]]
            if isinstance(page, (list, tuple)):
                await self.handle_pages(page, skip_formatting=True)  # type: ignore

            if isinstance(page, (int, str, discord.ui.TextDisplay)):
                if isinstance(page, discord.ui.TextDisplay):
                    self._add_item(page)  # type: ignore
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
                self._add_item(page)  # pyright: ignore[reportUnknownArgumentType]

        return self.__base_kwargs

    async def switch_page(self, interaction: Optional[discord.Interaction[Any]], page_number: int) -> None:
        """Switches the page to the given page number.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit. If ``None``, ``.message`` is used.
        page_number: :class:`int`
            The page number to switch to.
        """
        previous_page_number: int = self.current_page_index
        self.current_page_index = page_number
        if previous_page_number == self.current_page_index:
            if interaction and not interaction.response.is_done():
                await interaction.response.defer()
            return

        page_kwargs = await self.handle_pages(self.current_pages)
        self._after_handling_pages()
        # self._handle_page_string()

        print(
            "CHILDREN",
            self.view.children,
            list(self.view.walk_children()),
            [i.id for i in list(self.view.walk_children())],
            sep="\n",
        )
        await self._edit(interaction, **page_kwargs)

        if interaction:
            await self.on_page(interaction, previous_page_number, self.current_page_index)

    async def _edit(self, interaction: Optional[discord.Interaction[Any]] = None, /, **kwargs: Any) -> discord.Message:
        """Edits the paginator with the given kwargs.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit. If available. If ``None``, :attr:`.BaseClassPaginator.message` is used.
        **kwargs: Any
            The kwargs to edit the message with.

        Raises
        ------
        ValueError
            If ``interaction`` and :attr:`.BaseClassPaginator.message` are ``None``.

        Returns
        -------
        :class:`discord.Message`
            The edited message.
        """
        kwargs.pop("ephemeral", None)

        files_to_edit: list[discord.File] = []

        atachments_or_Files = kwargs.pop("files", []) + kwargs.pop("attachments", [])
        if atachments_or_Files:
            for file in atachments_or_Files:
                files_to_edit.append(await _utils._new_file(file))

        kwargs["attachments"] = files_to_edit

        res: discord.InteractionCallbackResponse | discord.Message | None = None

        if interaction:
            if interaction.response.is_done():
                res = await interaction.edit_original_response(**kwargs)
            else:
                res = await interaction.response.edit_message(**kwargs)
        elif self.message:
            res = await self.message.edit(**kwargs)

        if self.view.is_finished():
            await self.stop_paginator(is_timeout=True)

        if isinstance(res, discord.Message):
            self.message = res
        elif isinstance(res, discord.InteractionCallbackResponse) and isinstance(res.resource, discord.InteractionMessage):
            self.message = res.resource

        if not self.message:
            raise ValueError("No message to edit. Either provide an interaction or set .message.")

        return self.message

    async def send(
        self,
        destination: Destination,
        *,
        edit_message: bool = False,
        **send_kwargs: Any,
    ) -> discord.Message:
        """Sends the message to the given destination.

        Parameters
        ----------
        destination: Union[:class:`discord.abc.Messageable`, :class:`discord.Interaction`]
            The destination to send the message to. Handles responding to the interaction if given.
        edit_message: :class:`bool`
            Whether to edit the message instead of sending a new one.
            Defaults to ``False``.
        **send_kwargs: Any
            The kwargs to pass to the destination's send method.

        Returns
        -------
        Optional[:class:`discord.Message`]
            The message or response sent.
        """
        return await self._send(destination, edit_message=edit_message, **send_kwargs)

    async def _send(
        self,
        destination: Destination,
        *,
        edit_message: bool = False,
        **send_kwargs: Any,
    ) -> discord.Message:
        page_kwargs: dict[str, Any] = await self.handle_pages(self.current_pages)  # pyright: ignore[reportAssignmentType]
        self._after_handling_pages()

        page_kwargs |= send_kwargs
        if self.allowed_mentions is not None:
            page_kwargs["allowed_mentions"] = self.allowed_mentions

        print(
            "SENDING VIEW",
            self.view,
            self.view.children,
            list(self.view.walk_children()),
            [x.id for x in self.view.walk_children()],
        )

        if edit_message:
            return await self._edit(destination if isinstance(destination, discord.Interaction) else None, **page_kwargs)

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
