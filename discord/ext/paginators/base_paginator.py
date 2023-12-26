from __future__ import annotations
from typing import TYPE_CHECKING, Any, Coroutine, Generic, Literal, Optional, Union, overload

from collections.abc import Sequence

import inspect

import discord

from ._types import Page
from .errors import NoPages

if TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import PaginatorCheck, BaseKwargs, Interaction, Destination


__all__ = ("BaseClassPaginator",)


class BaseClassPaginator(discord.ui.View, Generic[Page]):
    """Base class for all paginators.

    Parameters
    -----------
    pages: Sequence[:class:`~discord.ext.paginators._types.Page`]
        A sequence of pages to paginate.
        Supported types for pages:

        - :class:`str`: Will be set as the content of the message.
        - :class:`.discord.Embed`: Will be appended to the embeds of the message.
        - :class:`.discord.File`: Will be appended to the files of the message.
        - :class:`.discord.Attachment`: Calls :meth:`~discord.Attachment.to_file()` and appends it to the files of the message.
        - Sequence[:class:`~discord.ext.paginators._types.Page`]: Will be flattened and each page will be handled as above.

        Any other types will probably be ignored.
    per_page: :class:`int`
        The amount of pages to display per page.
        Defaults to ``1``.

        E,g: If ``per_page`` is ``2`` and ``pages`` is ``["1", "2", "3", "4"]``, then the message
        will show ``["1", "2"]`` on the first page and ``["3", "4"]`` on the second page.
    author_id: `Optional[:class:`int`]`
        The id of the user who can interact with the paginator.
        Defaults to ``None``.
    check: `Optional[`PaginatorCheck[Self]`]`
        A callable that checks if the interaction is valid. This must be a callable that takes 2 or 3 parameters.
        The last two parameters represent the interaction and paginator respectively.
        It CAN be a coroutine.

        This is called in :meth:`~discord.ui.View.interaction_check`.

        If ``author_id`` is not ``None``, this won't be called.
        Defaults to ``None``.
    always_allow_bot_owner: :class:`bool`
        Whether to always allow the bot owner to interact with the paginator.
        Defaults to ``True``.
    delete_after: :class:`bool`
        Whether to delete the message after the paginator stops. Only works if ``message`` is not ``None``.
        Defaults to ``False``.
    disable_after: :class:`bool`
        Whether to disable the paginator after the paginator stops. Only works if ``message`` is not ``None``.
        Defaults to ``False``.
    clear_buttons_after: :class:`bool`
        Whether to clear the buttons after the paginator stops. Only works if ``message`` is not ``None``.
        Defaults to ``False``.
    message: `Optional[:class:`.Message`]`
        The message to use for the paginator. This is set automatically when ``_send`` is called.
        Defaults to ``None``.
    timeout: `Optional[`Union[:class:`int`, :class:`float`]`]`
        The timeout for the paginator.
        Defaults to ``180.0``.
    """

    __slots__ = (
        "pages",
        "per_page",
        "max_pages",
        "author_id",
        "delete_after",
        "disable_after",
        "clear_buttons_after",
        "message",
        "_check",
        "_current_page",
        "__base_kwargs",
    )

    def __init__(
        self,
        pages: Sequence[Page],
        *,
        per_page: int = 1,
        author_id: Optional[int] = None,
        check: Optional[PaginatorCheck[Self]] = None,
        always_allow_bot_owner: bool = True,
        delete_after: bool = False,
        disable_after: bool = False,
        clear_buttons_after: bool = False,
        message: Optional[discord.Message] = None,
        timeout: Optional[Union[int, float]] = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)

        if not pages:
            raise NoPages("No pages provided.")
        if per_page < 1:
            raise ValueError("per_page must be greater than 0.")

        self.pages: Sequence[Page] = pages
        self.per_page: int = per_page
        self.max_pages: int = len(pages) // per_page + bool(len(pages) % per_page)

        self._current_page: int = 0

        self.author_id: Optional[int] = author_id
        self._check: Optional[PaginatorCheck[Self]] = None
        if check is not None:
            if not callable(check) or len(inspect.signature(check).parameters) not in (2, 3):
                raise TypeError(
                    (
                        "check must be a callable with exactly 2 or 3 parameters. Last two "
                        "representing the interaction and paginator. `check(self, interaction, "
                        "paginator)` or `check(interaction, paginator)`."
                    )
                )

        self.always_allow_bot_owner: bool = always_allow_bot_owner
        self.delete_after: bool = delete_after
        self.disable_after: bool = disable_after
        self.clear_buttons_after: bool = clear_buttons_after

        self.message: Optional[discord.Message] = message

        self.__reset_base_kwargs()

    def __reset_base_kwargs(self) -> None:
        self.__base_kwargs: BaseKwargs = {"content": None, "embeds": [], "view": self}

    @staticmethod
    def __get_bot_owners_ids_from_interaction(interaction: Interaction) -> list[int]:
        owner_ids: list[int] = []
        client = interaction.client
        if owner_id_attr := getattr(client, "owner_id", None):
            owner_ids.append(owner_id_attr)
        if owner_ids_attr := getattr(client, "owner_ids", set[int]()):
            owner_ids.extend(owner_ids_attr)

        return owner_ids

    @property
    def current_page(self) -> int:
        """:class:`int`: The current page. Starts from ``0``."""
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        """:class:`int`: Sets the current page to the given value."""
        self._current_page = value

    @property
    def page_string(self) -> str:
        """:class:`str`: A string representing the current page and the max pages."""
        return f"Page {self.current_page + 1} of {self.max_pages}"

    def stop(self) -> None:
        """Stops the view and resets the base kwargs."""
        self.__reset_base_kwargs()
        self.message = None
        return super().stop()

    async def on_timeout(self) -> None:
        """This method is called when the paginator times out.

        This method does the following checks (in order):
        - Calls :meth:`.BaseClassPaginator.stop_paginator`.
        - Calls :meth:`discord.ui.View.on_timeout`.
        """
        await self.stop_paginator()
        await super().on_timeout()

    async def interaction_check(self, interaction: Interaction) -> bool:
        """This method is called when the paginator receives an interaction.

        This method does the following checks (in order):
        - If ``always_allow_bot_owner`` is ``True``, it checks if the interaction's author id is one of the bot owners.
        - If ``author_id`` is not ``None``, it checks if the interaction's author id is the same as the one set.
        - If ``checl`` is not ``None``, it calls it and checks if it returns ``True``.
        - If none of the above checks are ``True``, it calls :meth:`discord.ui.View.interaction_check`.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction received.
        """
        user_id = interaction.user.id
        owner_ids: list[int] = []

        if self.always_allow_bot_owner:
            owner_ids = self.__get_bot_owners_ids_from_interaction(interaction)
            if user_id in owner_ids:
                return True

        if self.author_id is not None and user_id == self.author_id:
            return True

        if self._check is not None:
            return await discord.utils.maybe_coroutine(self._check, self, interaction)

        return await super().interaction_check(interaction)

    def _format_page(self, page: Union[Page, Sequence[Page]]) -> Coroutine[Any, Any, Union[Page, Sequence[Page]]]:
        return discord.utils.maybe_coroutine(self.format_page, page)

    async def format_page(self, page: Union[Page, Sequence[Page]]) -> Union[Page, Sequence[Page]]:
        """This method can be overridden to format the page before sending it.
        By default, it returns the page as is.

        Parameters
        ----------
        page: Union[:class:`~discord.ext.paginators._types.Page`], Sequence[:class:`~discord.ext.paginators._types.Page`]]
            The page to format.

        Returns
        -------
        Union[:class:`~discord.ext.paginators._types.Page`], Sequence[:class:`~discord.ext.paginators._types.Page`]]
            The formatted page(s).
        """
        return page

    async def stop_paginator(self) -> None:
        """Stops the paginator.

        This method does the following checks (in order):

        - If ``message`` is not ``None``, it does the following:
            - If ``delete_after`` is ``True``, it deletes the message.
            - If ``disable_after`` is ``True``, it disables the view.
            - If ``clear_buttons_after`` is ``True``, it clears the buttons.
        - It calls :meth:`.BaseClassPaginator.stop`.
        """
        if self.message is not None:
            if self.delete_after:
                await self.message.delete()
            elif self.disable_after:
                self._disable_all_children()
                await self.message.edit(view=self)
            elif self.clear_buttons_after:
                await self.message.edit(view=None)

        self.stop()

    def get_page(self, page_number: int) -> Union[Page, Sequence[Page]]:
        """Gets the page with the given page number.

        Parameters
        ----------
        page_number: :class:`int`
            The page number to get.

        Returns
        -------
        Union[:class:`~discord.ext.paginators._types.Page`], Sequence[:class:`~discord.ext.paginators._types.Page`]]
            The page(s) with the given page number.
        """
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def _handle_page_string(self) -> None:
        if embeds := self.__base_kwargs["embeds"]:
            for embed in embeds:
                to_set = self.page_string
                if footer_text := embed.footer.text:
                    if "|" in footer_text:
                        footer_text = footer_text.split("|")[0].strip()
                        to_set = f"{footer_text} | {self.page_string}"

                embed.set_footer(text=to_set)
        elif content := self.__base_kwargs["content"]:
            self.__base_kwargs["content"] = f"{content}\n{self.page_string}"
        else:
            self.__base_kwargs["content"] = self.page_string

    async def get_page_kwargs(self, _page: Union[Page, Sequence[Page]], /, skip_formatting: bool = False) -> BaseKwargs:
        """Gets the kwargs to send the page with.

        Parameters
        ----------
        _page: Union[:class:`~discord.ext.paginators._types.Page`], Sequence[:class:`~discord.ext.paginators._types.Page`]]
            The page to get the kwargs for.
        skip_formatting: bool
            Whether to not call :meth:`.BaseClassPaginator.format_page` with the given page.
            Defaults to ``False``.

        Returns
        -------
        :class:`.BaseKwargs`
            The kwargs to send the page with.
        """
        kwrgs = self.__base_kwargs
        if not skip_formatting:
            self.__reset_base_kwargs()
            page = await self._format_page(_page)
        else:
            page = _page

        # Sequence
        if isinstance(page, (list, tuple)):
            for __page in page:
                # handles the page kwargs
                await self.get_page_kwargs(__page, skip_formatting=True)  # type: ignore # it's fine, trust me...

        if isinstance(page, (int, str)):
            kwrgs["content"] = str(page)
        elif isinstance(page, discord.Embed):
            kwrgs["embeds"].append(page)
        elif isinstance(page, (discord.File, discord.Attachment)):
            if isinstance(page, discord.Attachment):
                page = await page.to_file()
            if "files" not in kwrgs:
                kwrgs["files"] = [page]
            else:
                kwrgs["files"].append(page)
        elif isinstance(page, dict):
            kwrgs.update(page.copy())  # type: ignore

        self._handle_page_string()
        return kwrgs

    def _disable_all_children(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore

    async def _edit_message(self, interaction: Optional[Interaction] = None, /, **kwargs: Any) -> None:
        """Edits the message with the given kwargs.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit.
            If ``None``, ``.message`` is used, if that's ``None``, a :exc:`ValueError` is raised.
            Defaults to ``None``.
        **kwargs: Any
            The kwargs to edit the message with.

        Raises
        ------
        ValueError
            If ``interaction`` is ``None`` and :attr:`.BaseClassPaginator.message` is ``None``.
        """
        kwargs.pop("ephemeral", None)
        kwargs["attachments"] = kwargs.pop("files", [])

        if interaction is not None:
            if interaction.response.is_done() and interaction.message:
                await interaction.message.edit(**kwargs)
            else:
                await interaction.response.edit_message(**kwargs)
        elif self.message:
            await self.message.edit(**kwargs)
        else:
            ValueError("No interaction or message to edit.")

        if self.is_finished():
            self.message = None
            await self.stop_paginator()

    async def switch_page(self, interaction: Optional[Interaction], page_number: int) -> None:
        """Switches the page to the given page number.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to edit. If ``None``, ``.message`` is used.
        page_number: :class:`int`
            The page number to switch to.
        """
        self.current_page = page_number
        page = self.get_page(self.current_page)
        page_kwargs = await self.get_page_kwargs(page)
        await self._edit_message(interaction, **page_kwargs)

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = ...,
        edit_message: Literal[True] = ...,
        **send_kwargs: Any,
    ) -> None:
        ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: bool = ...,
        edit_message: Literal[False] = ...,
        **send_kwargs: Any,
    ) -> discord.Message:
        ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: Literal[False] = ...,
        edit_message: bool = ...,
    ) -> Optional[discord.Message]:
        ...

    @overload
    async def send(
        self,
        destination: Destination,
        *,
        override_page_kwargs: Literal[True] = ...,
        edit_message: bool = ...,
        **send_kwargs: Any,
    ) -> Optional[discord.Message]:
        ...

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
            Defaults to ``False``.
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
        override_page_kwargs: bool = False,
        edit_message: bool = False,
        **send_kwargs: Any,
    ) -> Optional[discord.Message]:
        page = self.get_page(self.current_page)
        page_kwargs: dict[str, Any] = await self.get_page_kwargs(page)  # type: ignore # it's fine.
        if override_page_kwargs:
            page_kwargs |= send_kwargs

        if edit_message:
            return await self._edit_message(
                destination if isinstance(destination, discord.Interaction) else None, **page_kwargs
            )

        elif isinstance(destination, discord.Interaction):
            if destination.response.is_done():
                self.message = await destination.followup.send(**page_kwargs, wait=True)
            else:
                await destination.response.edit_message(**page_kwargs)
                self.message = await destination.original_response()

        else:
            self.message = await destination.send(**page_kwargs)

        return self.message
