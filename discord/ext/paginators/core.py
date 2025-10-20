from __future__ import annotations
from typing import TYPE_CHECKING, Any
from typing_extensions import TypeIs
from collections.abc import Callable, Sequence

import logging
from math import ceil

import discord

from .views import PaginatorView, PaginatorLayoutView
from .enums import AfterAction
from . import utils as _utils

if TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import PaginatorCheck, BaseKwargs, BoundPage, BoundV2Page
    from .views import View
else:
    View = discord.ui.View | discord.ui.LayoutView


__all__ = ("BaseClassPaginator",)

_log = logging.getLogger(__name__)


def _is_page[PageT: (BoundPage | BoundV2Page)](page: PageT) -> TypeIs[PageT]:
    expected_items = (str, discord.Embed, discord.ui.Item, dict, discord.File, discord.Attachment)
    if isinstance(page, expected_items):
        return True

    if isinstance(page, Sequence) and not isinstance(page, (str, bytes, bytearray)):
        return all(isinstance(p, expected_items) for p in page)

    return False


class BaseClassPaginator[PageT: (BoundPage, BoundV2Page)]:
    """Base class for all paginators.

    This is implemented as a base class for the following:

    - :class:`.ButtonsPaginator`
    - :class:`.SelectOptionsPaginator`

    Parameters
    -----------
    pages: :class:`collections.abc.Sequence`
        Collection of pages to display. Each page may be:

        - :class:`str`: Appended to message content (or converted to :class:`discord.ui.TextDisplay` with v2).
        - :class:`discord.Embed`: Appended to embeds (disallowed with v2 components).
        - :class:`discord.File`: Attached to the message.
        - :class:`discord.Attachment`: Converted to :class:`discord.File` and attached.
        - :class:`discord.ui.Item`: Added to the underlying view (v2 items switch the paginator into v2 mode).
        - :class:`dict`: Merged into message/edit kwargs (must respect v2 restrictions).
        - :class:`Sequence`: Recursively flattened and processed as above.

        You can hot-swap pages at any time by assigning to :attr:`.pages`.

        .. note::

            - If any v2 component (e.g. :class:`discord.ui.Container`) is present or

            ``components_v2=True``, standard content and embeds are not allowed.
            The paginator adapts as follows:

            - :class:`str` -> :class:`discord.ui.TextDisplay`
            - :class:`discord.Embed` -> raises an error
            - :class:`discord.File` / :class:`discord.Attachment` -> allowed (for use with
                :class:`discord.ui.MediaGallery`, :class:`discord.ui.File`, :class:`discord.ui.Thumbnail`, etc.)

        This not required at initialization and can be set later.
    components_v2: :class:`bool` | None
        Determines the allowed pages and view type:

        - ``True``: Only v2 components allowed.
        - ``False``: v2 components disallowed. Embeds, etc allowed.
        - ``None``: Auto-detects based on page content.

        All pages are validated upon construction and when setting :attr:`.pages`.
        Defaults to ``None``.
    per_page: :class:`int`
        Number of pages to display simultaneously. For example, with ``per_page=2`` and
        ``pages=["1", "2", "3", "4"]``, the first view shows ``["1", "2"]`` and the second shows ``["3", "4"]``.
        Must be at least ``1`` and no greater than the total number of pages.

        Defaults to ``1``.
    author_id: :class:`int` | None
        ID of the user that is allowed to interact with the paginator.
        If set, only this user can use the paginator controls.
        Defaults to ``None``.
    check: :class:`PaginatorCheck` | None
        A function that checks whether a user is allowed to interact with the paginator.
        Must take two parameters: the paginator instance and the interaction. And can
        be async. This is only called when ``author_id`` is ``None`` / not set.
        Defaults to ``None``.
    always_allow_bot_owner: :class:`bool`
        Whether to always allow bot owners to interact with the paginator, regardless of other restrictions.

        Defaults to ``False``.

        .. versionchanged:: 1.0.0
            The default was changed from ``True`` to ``False`` to prevent unexpected behavior.
    message: :class:`discord.Message` | None.
        An existing message to use for the paginator. See :meth:`.edit` for more info.

        Defaults to ``None``.
    add_page_string: :class:`bool`
        Whether to add a page string (e.g. "Page 1/5") to the paginator.

        Defaults to ``True``.
    switch_pages_humanly: :class:`bool`
        Whether to switch pages in a human-friendly way.

        When ``True``, the ``Next`` and ``Previous`` buttons will go to the
        first/last page, respectively.
        If ``False``, the ``Next`` and ``Previous`` buttons will be disabled
        when on the last/first page, respectively.

        Defaults to ``False``.
    timeout: :class:`int` | :class:`float` | None
        The amount of seconds to wait before timing out the paginator.
        If ``None``, the paginator will not time out.

        Defaults to ``180.0`` seconds (3 minutes).
    view_cls: :class:`type`[:class:`View`] | None
        The view class to use for the paginator.

        This must:
        - Subclass :class:`.PaginatorView` if ``components_v2`` is ``False`` or you haven't
        passed any v2 components in ``pages``.
        - Subclass :class:`.PaginatorLayoutView` if ``components_v2`` is ``True`` or you have
        passed any v2 components in ``pages``.
        - Take two parameters in ``__init__``: ``paginator`` and ``timeout``.
          - Don't forget to call ``super().__init__(paginator, timeout=timeout)``.

        If ``None``, the correct view class will be chosen automatically.

        Defaults to ``None``.

        .. versionadded:: 0.3.0
    after_stop: :class:`AfterAction`
        The action to take when the paginator is stopped normally (not timed out).

        Defaults to :attr:`AfterAction.NOTHING`.

        .. versionadded:: 1.0.0
    after_timeout: :class:`AfterAction`
        The action to take when the paginator times out (not stopped).

        Defaults to :attr:`AfterAction.NOTHING`.

        .. versionadded:: 1.0.0
    title: :class:`str` | :class:`discord.ui.TextDisplay` | None
        A title to display on every page.

        This is always on the top of the page.
        :class:`str` will be converted to :class:`discord.ui.TextDisplay` when using v2 components.

        Defaults to ``None``.

        .. versionadded:: 1.0.0
    description: :class:`str` | :class:`discord.ui.TextDisplay` | None
        A description to display on every page.

        This is always below the title.
        :class:`str` will be converted to :class:`discord.ui.TextDisplay` when using v2 components.

        Defaults to ``None``.

        .. versionadded:: 1.0.0
    allowed_mentions: :class:`discord.AllowedMentions` | :class:`bool` | None
        Controls the allowed mentions for the paginator's messages.

        - If :class:`discord.AllowedMentions` is passed, it will be used as is.
        - If ``True`` is passed, :meth:`discord.AllowedMentions.all` will be used.
        - If ``False`` is passed, :meth:`discord.AllowedMentions.none` will be used.
        - If ``None`` is passed, the parameter will be ignored.

        Defaults to ``None``.
    """

    _get_base_kwargs: Callable[[], BaseKwargs]

    def __init__(
        self,
        pages: Sequence[PageT] = discord.utils.MISSING,
        *,
        components_v2: bool | None = None,
        per_page: int = 1,
        author_id: int | None = None,
        check: PaginatorCheck[Self] | None = None,
        always_allow_bot_owner: bool = False,
        message: discord.Message | None = None,
        add_page_string: bool = True,
        switch_pages_humanly: bool = False,
        timeout: int | float | None = 180.0,
        view_cls: type[View[Self]] | None = None,
        after_stop: AfterAction = AfterAction.NOTHING,
        after_timeout: AfterAction = AfterAction.NOTHING,
        title: str | discord.ui.TextDisplay[Any] | None = None,
        description: str | discord.ui.TextDisplay[Any] | None = None,
        allowed_mentions: discord.AllowedMentions | bool | None = None,
    ) -> None:
        self._initial_pages = pages is not discord.utils.MISSING
        self.__components_v2: bool | None = components_v2
        print(self.__components_v2, components_v2, type(components_v2), pages, type(pages))

        if components_v2 not in (True, False, None):
            raise TypeError(f"components_v2 must be one of (True, False, None), not {components_v2.__class__.__name__!r}.")

        if pages is not discord.utils.MISSING and components_v2 is None:
            self.__components_v2 = _utils._has_v2_components(pages)

        print("cv2?", self.__components_v2)
        self.__view: View[Self] = self.__init_view(view_cls=view_cls, timeout=timeout)

        self._per_page: int = per_page
        self._pages: Sequence[PageT] = []
        self.pages = pages or []
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
        """:class:`int`: The current page index. This is zero-indexed."""
        return self._current_page_index

    @current_page_index.setter
    def current_page_index(self, value: int) -> None:
        """:class:`int`: Sets the current page to the given value."""
        if not isinstance(value, int):
            raise TypeError("current_page_index must be an int.")

        max_index = self.max_pages - 1
        self._current_page_index = max(0, min(value, max_index))

    @property
    def current_pages(self) -> Sequence[PageT]:
        """Sequence[PageT]: The pages that are currently being displayed."""
        return self.get_page(self.current_page_index)

    @property
    def page_string(self) -> str:
        """:class:`str`: A string representing the current page and the max pages."""
        return f"Page {self.current_page_index + 1} of {self.max_pages}"

    @property
    def pages(self) -> Sequence[PageT]:
        """Sequence[PageT]: The pages of the paginator."""
        return self._pages

    @pages.setter
    def pages(self, value: Sequence[PageT]) -> None:
        if isinstance(value, str):
            raise TypeError("pages must be a sequence of pages, not str.")

        if self.per_page > len(value):
            raise ValueError("per_page cannot be greater than the amount of pages.")

        if not value:
            self._pages = []
            return

        print("value:", value, type(value), self.__components_v2)
        _utils._check_cv2_and_pages(self.__components_v2, value)
        self._pages = value

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
        """int: The max amount of pages on the current page."""
        return ceil(len(self.pages) / self.per_page)

    @property
    def total_pages(self) -> int:
        """:class:`int`: The total amount of pages in the paginator."""
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
            subclasses = view_cls.__bases__
            print("subclasses:", subclasses, expected_cls, issubclass(view_cls, expected_cls))
            if object in subclasses:
                subclasses = [subcls for subcls in subclasses if subcls is not object]

            if subclasses:
                if len(subclasses) > 1:
                    subclasses = f", not any of ({', '.join(repr(subcls.__name__) for subcls in subclasses)})"
                else:
                    subclasses = f", not {subclasses[0].__name__!r}"  # pyright: ignore[reportGeneralTypeIssues]
            else:
                subclasses = ""

            msg = f"view_cls must be a subclass of '{expected_cls.__name__}' (components_v2: {self.__components_v2}){subclasses}."
            raise TypeError(msg)

        return view_cls(self, timeout=timeout)

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
        if self.allowed_mentions is not None:
            self.__base_kwargs["allowed_mentions"] = self.allowed_mentions

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

    async def stop_paginator(self, interaction: discord.Interaction[Any] | None = None, is_timeout: bool = False) -> None:
        """Stops the paginator.

        This handles the after actions too.

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

    def format_page(self, page: Sequence[PageT]) -> Sequence[PageT]:
        """Sequence[PageT]: An optional coroutine that can be overridden to format the pages before they are processed and sent."""
        return page

    def get_page(self, page_number: int) -> Sequence[PageT]:
        """Gets the pages with the given page number.

        This will return a list of pages with one item, even if there is only one page.

        Parameters
        ----------
        page_number: :class:`int`
            The page number to get.

        Returns
        -------
        Sequence[PageT]
            The pages with the given page number.
        """
        if not self.pages:
            raise ValueError(
                "No pages are available. Either provide a non-empty 'pages' sequence when creating the paginator, or assign to '.pages' before sending."
            )

        if self.per_page == 1:
            page = self.pages[page_number]
            if _is_page(page):
                return [page]
            return page

        base = page_number * self.per_page
        return self.pages[base : base + self.per_page]

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

    async def _handle_single_page(
        self, page: PageT, /, kwargs: dict[str, Any], items: list[discord.ui.Item[Any]]
    ) -> tuple[dict[str, Any], list[discord.ui.Item[Any]]]:
        _kwargs: dict[str, Any] = {}
        _items: list[discord.ui.Item[Any]] = items.copy()

        if isinstance(page, (int, str, discord.ui.TextDisplay)):
            if isinstance(page, discord.ui.TextDisplay):
                items.append(page)
            elif self.__components_v2:
                items.append(discord.ui.TextDisplay[Any](str(page)))
            else:
                content = _kwargs.get("content")
                _kwargs["content"] = f"{content}\n{page}" if content else str(page)
        elif isinstance(page, discord.Embed):
            _kwargs.setdefault("embeds", []).append(page)
        elif isinstance(page, discord.File | discord.Attachment):
            _file = await _utils._new_file(page)
            _kwargs.setdefault("files", []).append(_file)
        elif isinstance(page, discord.ui.Item):
            _items.append(page)
        elif isinstance(page, dict):
            _kwargs.update(page)
        else:
            for _page in page:
                _kwargs, _items = await self._handle_single_page(_page, kwargs=_kwargs, items=_items)  # pyright: ignore[reportArgumentType]

        return _kwargs, _items

    async def handle_pages(self, pages: Sequence[PageT]) -> dict[str, Any]:
        _kwargs: dict[str, Any] = {}
        items: list[discord.ui.Item[Any]] = []

        formatted_pages = await discord.utils.maybe_coroutine(self.format_page, pages)

        for page in formatted_pages:
            _page_kwargs, items = await self._handle_single_page(page, kwargs=_kwargs, items=items)
            _kwargs |= _page_kwargs
            items.extend(items)

        if items:
            for item in items:
                self._add_item(item)

        return _kwargs

    async def switch_page(self, interaction: discord.Interaction[Any] | None, page_number: int) -> None:
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
        await self.edit(interaction, **page_kwargs)

        if interaction:
            await self.on_page(interaction, previous_page_number, self.current_page_index)

    async def edit(
        self, message: discord.Interaction[Any] | discord.Message | None = None, /, **kwargs: Any
    ) -> discord.Message:
        """Edits the message with paginator and the provided kwargs.

        Parameters
        ----------
        message: :class:`discord.Interaction` | :class:`discord.Message` | None
            The message to edit. If ``None``, :attr:`.BaseClassPaginator.message` is used.
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

        if message:
            if isinstance(message, discord.Message):
                self.message = await message.edit(**kwargs)
            elif isinstance(message, discord.Interaction):
                if message.response.is_done():
                    self.message = await message.edit_original_response(**kwargs)
                else:
                    res = await message.response.edit_message(**kwargs)
                    if res and isinstance(res.resource, discord.InteractionMessage):
                        self.message = res.resource
                    else:
                        self.message = await message.original_response()
            else:
                raise TypeError(f"message must be Interaction, Message or None, not {message.__class__.__name__!r}.")
        elif self.message:
            self.message = await self.message.edit(**kwargs)
        else:
            raise ValueError("No message to edit. Either provide an Interaction, Message or set the 'message' attribute.")

        if self.view.is_finished():
            await self.stop_paginator(is_timeout=True)

        return self.message

    async def send(
        self,
        destination: discord.abc.Messageable | discord.Interaction[Any],
        **send_kwargs: Any,
    ) -> discord.Message:
        """Sends the message to the given destination.

        Parameters
        ----------
        destination: :class:`discord.abc.Messageable` | :class:`discord.Interaction`
            The destination to send the message to. Handles responding to the interaction if given.
        **send_kwargs: Any
            The kwargs to pass to the destination's send method.

        Returns
        -------
        :class:`discord.Message`
            The message or response sent.
        """
        return await self._send(destination, **send_kwargs)

    async def _send(
        self,
        destination: discord.abc.Messageable | discord.Interaction[Any],
        **send_kwargs: Any,
    ) -> discord.Message:
        if not isinstance(destination, (discord.abc.Messageable, discord.Interaction)):
            raise TypeError(f"destination must be Messageable or Interaction, not {destination.__class__.__name__!r}.")

        page_kwargs: dict[str, Any] = await self.handle_pages(self.current_pages)  # pyright: ignore[reportAssignmentType]
        self._after_handling_pages()

        page_kwargs |= send_kwargs
        if isinstance(destination, discord.Interaction):
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
