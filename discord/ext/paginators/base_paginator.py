from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Optional, Union, overload

from collections.abc import Sequence, Coroutine

import discord

from ._types import PageT
from . import utils as _utils

if TYPE_CHECKING:
    from typing_extensions import Self

    from ._types import PaginatorCheck, BaseKwargs, Destination
else:
    PaginatorCheck = Callable[[Any, discord.Interaction[Any]], Union[bool, Coroutine[Any, Any, bool]]]


__all__ = ("BaseClassPaginator",)


class BaseClassPaginator(discord.ui.View, Generic[PageT]):
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
        - :class:`dict`: Will be updated with the kwargs of the message.
        - Sequence[Any]: Will be flattened and each entry will be handled as above.

        Sequence = List, Tuple, etc.

        Any other types will probably be ignored.
        This attribute *should* be able to be set after the paginator is created.
        Aka, hotswapping the pages.
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
    message: Optional[:class:`discord.Message`]
        The message to use for the paginator. This is set automatically when ``_send`` is called.
        Defaults to ``None``.
    add_page_string: :class:`bool`
        Whether to add the page string to the page. Defaults to ``True``.
        This is a string that represents the current page and the max pages. E,g: ``"Page 1 of 2"``.

        If the page is an embed, it will be appended to the footer text.
        If the page is a string, it will be appended to the string.
        else, it will be set as the content of the message.

    timeout: Optional[Union[:class:`int`, :class:`float`]]
        The timeout for the paginator.
        Defaults to ``180.0``.
    """

    def __init__(
        self,
        pages: Sequence[PageT],
        *,
        per_page: int = 1,
        author_id: Optional[int] = None,
        check: Optional[PaginatorCheck[Self]] = None,
        always_allow_bot_owner: bool = True,
        delete_after: bool = False,
        disable_after: bool = False,
        clear_buttons_after: bool = False,
        message: Optional[discord.Message] = None,
        add_page_string: bool = True,
        timeout: Optional[Union[int, float]] = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)

        if not pages:
            raise ValueError("No pages provided.")
        if per_page < 1:
            raise ValueError("per_page must be greater than 0.")

        self.pages: Sequence[PageT] = pages
        self.per_page: int = per_page
        self.max_pages: int = len(pages) // per_page + bool(len(pages) % per_page)

        self._current_page: int = 0

        self.author_id: Optional[int] = author_id
        self._check: Optional[PaginatorCheck[Self]] = None
        if check is not None:
            if not callable(check) or not _utils._check_parameters_amount(check, (2, 3)):
                raise TypeError(
                    (
                        "check must be a callable with exactly 2 or 3 parameters. Last two "
                        "representing the interaction and paginator. `(async) def check(self, interaction, "
                        "paginator):` or `(async) def check(interaction, paginator):`."
                    )
                )

        self.always_allow_bot_owner: bool = always_allow_bot_owner
        self.delete_after: bool = delete_after
        self.disable_after: bool = disable_after
        self.clear_buttons_after: bool = clear_buttons_after
        self.add_page_string: bool = add_page_string

        self.message: Optional[discord.Message] = message

        self.__owner_ids: Optional[set[int]] = None

        self._reset_base_kwargs()

    async def __is_bot_owner(self, interaction: discord.Interaction[Any]) -> bool:
        """Checks if the interaction's user is one of the bot owners."""
        if self.__owner_ids is None:
            self.__owner_ids = await _utils._fetch_bot_owner_ids(interaction.client)

        return interaction.user.id in self.__owner_ids

    def _reset_base_kwargs(self) -> None:
        """Resets the base kwargs.

        This sets the base kwargs to ``{"content": None, "embeds": [], "view": self}``.
        """
        self.__base_kwargs: BaseKwargs = {"content": None, "embeds": [], "view": self}

    @property
    def current_page(self) -> int:
        """:class:`int`: The current page. Starts from ``0``."""
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        """:class:`int`: Sets the current page to the given value."""
        self._current_page = max(0, min(value, self.max_pages - 1))

    @property
    def page_string(self) -> str:
        """:class:`str`: A string representing the current page and the max pages."""
        return f"Page {self.current_page + 1} of {self.max_pages}"

    def stop(self) -> None:
        """Stops the view and resets the base kwargs."""
        self._reset_base_kwargs()
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

    async def _handle_checks(self, interaction: discord.Interaction[Any]) -> bool:
        """Handles the checks for the paginator.

        This is called in :meth:`~discord.ui.View.interaction_check`.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction to check.

        Returns
        -------
        :class:`bool`
            Whether the interaction is valid or not.
        """
        if self.always_allow_bot_owner:
            if await self.__is_bot_owner(interaction):
                return True

        if self.author_id is not None and interaction.user.id == self.author_id:
            return True

        if self._check is not None:
            return await discord.utils.maybe_coroutine(self._check, self, interaction)

        return await super().interaction_check(interaction)

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        """This method is called by the library when the paginator receives an interaction.

        This method does the following checks (in order):

        - If ``always_allow_bot_owner`` is ``True``, it checks if the interaction's author id is one of the bot owners.
        - If ``author_id`` is not ``None``, it checks if the interaction's author id is the same as the one set.
        - If ``check`` is not ``None``, it calls it and checks if it returns ``True``.
        - If none of the above checks are ``True``, it calls :meth:`discord.ui.View.interaction_check`.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction received.
        """
        return await self._handle_checks(interaction)

    def _do_format_page(self, page: Union[PageT, Sequence[PageT]]) -> Coroutine[Any, Any, Union[PageT, Sequence[PageT]]]:
        return discord.utils.maybe_coroutine(self.format_page, page)

    async def format_page(self, page: Union[PageT, Sequence[PageT]]) -> Union[PageT, Sequence[PageT]]:
        """This method can be overridden to format the page before sending it.
        By default, it returns the page as is.

        Parameters
        ----------
        page: Union[Any], Sequence[Any]]
            The page to format.

        Returns
        -------
        Union[Any], Sequence[Any]]
            The formatted page(s).
        """
        return page

    async def stop_paginator(self, interaction: Optional[discord.Interaction[Any]] = None) -> None:
        """Stops the paginator.

        This method does handles deleting the message, disabling the paginator and clearing the buttons.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            Optionally, the last interaction to edit. If ``None``, ``.message`` is used.
        """
        success: bool = False
        if self.delete_after:
            error_message: str = "Failed to delete the message. in {cls.__name__}.stop_paginator.\nError: {message}"
            to_call = (
                [
                    self.message.delete,
                ]
                if self.message
                else []
            )
            if interaction:
                to_call = [
                    interaction.delete_original_response,
                ] + to_call
                if not interaction.response.is_done():
                    await interaction.response.defer()
                if interaction.message:
                    to_call.insert(1, interaction.message.delete)

            success, error = await _utils._call_and_ignore(
                to_call,
            )
            if not success:
                logging.debug(error_message.format(cls=self.__class__, message=error))

            self.stop()
            return

        if self.disable_after or self.clear_buttons_after:
            if self.clear_buttons_after:
                self.clear_items()
            else:
                self._disable_all_children()

            to_call: list[Callable[..., Any]] = (
                [
                    self.message.edit,
                ]
                if self.message
                else []
            )
            error_message = "Failed to edit the message. in {cls.__name__}.stop_paginator.\nError: {message}"
            if interaction:
                to_call = [
                    interaction.edit_original_response,
                ] + to_call
                if not interaction.response.is_done():
                    to_call.insert(0, interaction.response.edit_message)
                if interaction.message:
                    to_call.insert(1, interaction.message.edit)

            success, error = await _utils._call_and_ignore(to_call, view=self)
            if not success:
                logging.debug(error_message.format(cls=self.__class__, message=error))

            self.stop()

    def get_page(self, page_number: int) -> Union[PageT, Sequence[PageT]]:
        """Gets the page with the given page number.

        Parameters
        ----------
        page_number: :class:`int`
            The page number to get.

        Returns
        -------
        Union[Any], Sequence[Any]]
            The page(s) with the given page number.
        """
        # handle per_page
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def _handle_page_string(self) -> None:
        if not self.add_page_string:
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

    async def get_page_kwargs(self, page: Union[PageT, Sequence[PageT]], /, skip_formatting: bool = False) -> BaseKwargs:
        """Gets the kwargs to send the page with.

        Parameters
        ----------
        page: Union[Any, Sequence[Any]]
            The page to get the kwargs for.
        skip_formatting: bool
            Whether to not call :meth:`.BaseClassPaginator.format_page` with the given page.
            Defaults to ``False``.

        Returns
        -------
        :class:`.BaseKwargs`
            The kwargs to send the page with.
        """
        if not skip_formatting:
            self._reset_base_kwargs()
            _page = await self._do_format_page(page)
            return await self.get_page_kwargs(_page, skip_formatting=True)

        # Sequence
        if isinstance(page, (list, tuple)):
            inner_page: Any
            for inner_page in page:
                # handles the page kwargs
                await self.get_page_kwargs(inner_page, skip_formatting=True)

        if isinstance(page, (int, str)):
            if self.__base_kwargs["content"]:
                self.__base_kwargs["content"] += str(page)
            else:
                self.__base_kwargs["content"] = str(page)
        elif isinstance(page, discord.Embed):
            self.__base_kwargs["embeds"].append(page)
        elif isinstance(page, (discord.File, discord.Attachment)):
            # you might be wondering, why another var for this?
            # well, because of the following type error:
            # "File" is incompatible with "Sequence[PageT@BaseClassPaginator]"
            if isinstance(page, discord.Attachment):
                file = await page.to_file()
            else:
                file = page

            if "files" not in self.__base_kwargs:
                self.__base_kwargs["files"] = [file]
            else:
                self.__base_kwargs["files"].append(file)
        elif isinstance(page, dict):
            # kinda the same thing as above but it didn't appricate that it
            # didn't know the type of the key&value so it was "dict[Unknown, Unknown]"
            data: dict[Any, Any] = page.copy()
            self.__base_kwargs.update(data)

        return self.__base_kwargs

    def _disable_all_children(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore # not all children have disabled attr.

    async def _edit_message(self, interaction: Optional[discord.Interaction[Any]] = None, /, **kwargs: Any) -> None:
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

        if interaction is None:
            if self.message is None:
                raise ValueError("interaction and self.message are both None.")
            await self.message.edit(**kwargs)

        else:
            if interaction.response.is_done():
                try:
                    await interaction.edit_original_response(**kwargs)
                except Exception:
                    try:
                        await interaction.message.edit(**kwargs)  # type: ignore
                    except Exception:
                        pass
            else:
                await interaction.response.edit_message(**kwargs)

        if self.is_finished():
            await self.stop_paginator()

    async def switch_page(self, interaction: Optional[discord.Interaction[Any]], page_number: int) -> None:
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
        self._handle_page_string()
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
        page_kwargs: dict[str, Any] = await self.get_page_kwargs(page)  # type: ignore # TypedDict don't go well with overloads
        self._handle_page_string()
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
                self.message = await destination.response.send_message(**page_kwargs)
                if not self.message:
                    self.message = await destination.original_response()

        else:
            self.message = await destination.send(**page_kwargs)

        return self.message
