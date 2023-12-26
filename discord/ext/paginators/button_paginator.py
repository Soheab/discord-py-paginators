from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal, Optional, Sequence, Union

from discord import ButtonStyle, Emoji, PartialEmoji
import discord
from discord.ui import Button, Modal, TextInput

from .base_paginator import BaseClassPaginator
from ._types import Page

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ._types import Interaction, BasePaginatorKwargs

    ValidButtonKeys = Literal["FIRST", "LEFT", "RIGHT", "LAST", "STOP", "PAGE_INDICATOR"]
    ValidButtonsDict = dict[ValidButtonKeys, "PaginatorButton"]


__all__: tuple[str, ...] = ("ButtonPaginator", "PaginatorButton")


class ChooseNumber(Modal):
    number_input: TextInput[Any] = TextInput(
        placeholder="Current: {0}",
        label="Enter a number between 1 and {0}",
        custom_id="paginator:textinput:choose_number",
        max_length=0,
        min_length=1,
    )

    def __init__(self, paginator: ButtonPaginator[Any], /, **kwargs: Any) -> None:
        super().__init__(
            title="Which page would you like to go to?",
            timeout=paginator.timeout,
            custom_id="paginator:modal:choose_number",
            **kwargs,
        )
        self.paginator: ButtonPaginator[Any] = paginator
        self.number_input.max_length = paginator.max_pages
        self.number_input.label = self.number_input.label.format(paginator.max_pages)
        self.number_input.placeholder = self.number_input.placeholder.format(paginator.current_page + 1)  # type: ignore

        self.value: Optional[int] = None

    async def on_submit(self, interaction: Interaction) -> None:
        # can't happen but type checker
        if not self.number_input.value:
            await interaction.response.send_message("Please enter a number!", ephemeral=True)
            self.stop()
            return

        if (
            not self.number_input.value.isdigit()
            or int(self.number_input.value) <= 0
            or int(self.number_input.value) > self.paginator.max_pages
        ):
            await interaction.response.send_message(
                f"Please enter a valid number between 1 and {self.paginator.max_pages}", ephemeral=True
            )
            self.stop()
            return

        number = int(self.number_input.value) - 1

        if number == self.paginator.current_page:
            await interaction.response.send_message("That is the current page!", ephemeral=True)
            self.stop()
            return

        self.value = number
        await interaction.response.defer()
        # await interaction.response.send_message(f"There is page {self.value + 1} for you <3", ephemeral=True)
        self.stop()


class PageSwitcherAndStopButtonView(discord.ui.View):
    STOP: Optional[Button["ButtonPaginator[Any]"]] = None  # filled in _add_buttons
    PAGE_INDICATOR: Optional[Button["ButtonPaginator[Any]"]] = None  # filled in _add_buttons

    _paginator: ButtonPaginator[Any]  # filled in _add_buttons

    def __init__(self, paginator: ButtonPaginator[Any], /) -> None:
        super().__init__(timeout=paginator.timeout)

    def _add_buttons(self, paginator: ButtonPaginator[Any], /) -> None:
        self._paginator: ButtonPaginator[Any] = paginator
        if not any(key in ("STOP", "PAGE_INDICATOR") for key in paginator._buttons):
            raise ValueError(
                "STOP and PAGE_INDICATOR buttons are required if combine_switcher_and_stop_button is True."
            )

        org_page_indicator_button = paginator._buttons["PAGE_INDICATOR"]
        page_indicator_button = PaginatorButton(
            label="Switch Page",
            emoji=org_page_indicator_button.emoji,
            style=org_page_indicator_button.style,
            custom_id="switch_page",
            disabled=False,
        )

        org_stop_button = paginator._buttons["STOP"]
        stop_button = PaginatorButton(
            label=org_stop_button.label,
            emoji=org_stop_button.emoji,
            style=org_stop_button.style,
            custom_id="stop_button",
            disabled=False,
        )
        buttons: dict[str, PaginatorButton] = {
            "STOP": stop_button,
            "PAGE_INDICATOR": page_indicator_button,
        }
        for name, button in buttons.items():
            setattr(self, name, button)
            self.add_item(button)

    async def callback(self, interaction: Interaction, button: PaginatorButton) -> None:
        if button.custom_id == "stop_button":
            await interaction.response.defer()
            await interaction.delete_original_response()
            await self._paginator.stop_paginator(None)
            return

        if button.custom_id == "switch_page":
            new_page = await self._paginator._handle_modal(interaction)
            await interaction.delete_original_response()
            if new_page is not None:
                self._paginator.current_page = new_page
            else:
                return

        await self._paginator.switch_page(None, self._paginator.current_page)


class PaginatorButton(Button["ButtonPaginator[Any]"]):
    """A button for the paginator.

    This class has a few parameters that differ from the base button.
    This can can be used passed to the ``buttons`` parameter in :class:`ButtonPaginator`
    to customize the buttons used.

    See other parameters on :class:`discord.ui.Button`.

    Parameters
    -----------
    position: Optional[int]
        The position of the button. Defaults to ``None``.
        If not specified, the button will be placed in the order they were added
        or whatever order discord.py adds them in.
    """

    view: ButtonPaginator[Any]  # type: ignore # it's correct.

    def __init__(
        self,
        *,
        emoji: Optional[Union[Emoji, PartialEmoji, str]] = None,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        style: ButtonStyle = ButtonStyle.blurple,
        row: Optional[int] = None,
        disabled: bool = False,
        position: Optional[int] = None,
    ) -> None:
        super().__init__(emoji=emoji, label=label, custom_id=custom_id, style=style, row=row, disabled=disabled)
        self.position: Optional[int] = position

    async def callback(self, interaction: Interaction) -> None:
        if isinstance(self.view, PageSwitcherAndStopButtonView):
            await self.view.callback(interaction, self)
            return

        if self.custom_id == "stop_button":
            await self.view.stop_paginator(interaction)
            return

        if self.custom_id == "right_button":
            self.view.current_page += 1
        elif self.custom_id == "left_button":
            self.view.current_page -= 1
        elif self.custom_id == "first_button":
            self.view.current_page = 0
        elif self.custom_id == "last_button":
            self.view.current_page = self.view.max_pages - 1
        elif self.custom_id == "page_indicator_button":
            if self.view._combine_switcher_and_stop_button and self.view._stop_button_and_page_switcher_view:
                await interaction.response.send_message(
                    view=self.view._stop_button_and_page_switcher_view, ephemeral=True
                )
                return

            new_page = await self.view._handle_modal(interaction)
            if new_page is not None:
                self.view.current_page = new_page
            else:
                return

        await self.view.switch_page(interaction, self.view.current_page)


class ButtonPaginator(BaseClassPaginator[Page]):
    """A paginator that uses buttons to switch pages.

    This class has a few parameters that differ from the base paginator.

    Just for clarification, here is a list of supported pages:

    - :class:`discord.Embed`
    - :class:`discord.File`
    - :class:`discord.Attachment`
    - :class:`str`
    - :class:`list` or :class:`tuple` of the above

    See other parameters on :class:`.BaseClassPaginator`.

    Parameters
    ----------
    buttons: :class:`dict`\\[:class:`str`, :class:`PaginatorButton`]
        A dictionary of buttons to use. The keys must be one of the following:
        "FIRST", "LEFT", "RIGHT", "LAST", "STOP", "PAGE_INDICATOR".
        The values must be a PaginatorButton or ``None`` to remove the button.
        If not specified, the default buttons will be used.

        Example
        -------
        .. code-block:: python3
            :linenos:

            from discord.ext.paginators.button_paginator import ButtonPaginator, PaginatorButton

            custom_buttons = {
                # change the label of the first button from "First" to "Go to first page"
                "FIRST": PaginatorButton(label="Go to first page"),
                # change the style of the LAST button to red
                "LAST": PaginatorButton(style=ButtonStyle.red),
            }

            # pass the custom buttons to the paginator
            paginator = ButtonPaginator(pages, buttons=custom_buttons)
            ... # rest of code

    always_show_stop_button: bool
        Whether to always show the stop button, even if there is only one page.
        Defaults to ``False``.

        .. note::
            If ``always_show_stop_button`` is ``True``, the ``STOP`` key in ``buttons`` cannot be ``None``.
    combine_switcher_and_stop_button: bool
        Whether to combine the page switcher and stop button into the paginator indicator which will send another set
        of buttons to switch pages and stop the paginator as an ephemeral message when clicked.
        Defaults to ``False``.

        .. note::
            If ``combine_switcher_and_stop_button`` is ``True``, the ``STOP`` and ``PAGE_INDICATOR`` keys in ``buttons`` cannot be ``None``.
    **kwargs: Unpack[:class:`.BasePaginatorKwargs`]
        See other parameters on :class:`.BaseClassPaginator`.
    """

    FIRST: Optional[PaginatorButton] = None  # filled in __add_buttons
    LEFT: Optional[PaginatorButton] = None  # filled in __add_buttons
    RIGHT: Optional[PaginatorButton] = None  # filled in __add_buttons
    LAST: Optional[PaginatorButton] = None  # filled in __add_buttons
    STOP: Optional[PaginatorButton] = None  # filled in __add_buttons
    PAGE_INDICATOR: Optional[PaginatorButton] = None  # filled in __add_buttons

    def __init__(
        self,
        pages: Sequence[Page],
        *,
        buttons: ValidButtonsDict = {},
        always_show_stop_button: bool = False,
        combine_switcher_and_stop_button: bool = False,
        **kwargs: Unpack[BasePaginatorKwargs],
    ) -> None:
        """Initialize the Paginator."""
        super().__init__(pages, **kwargs)

        DEFAULT_BUTTONS: dict[ValidButtonKeys, PaginatorButton] = {
            "FIRST": PaginatorButton(label="First", position=0),
            "LEFT": PaginatorButton(label="Left", position=1),
            "PAGE_INDICATOR": PaginatorButton(label="Page N/A / N/A", position=2, disabled=False),
            "RIGHT": PaginatorButton(label="Right", position=3),
            "LAST": PaginatorButton(label="Last", position=4),
            "STOP": PaginatorButton(label="Stop", style=ButtonStyle.danger, position=5),
        }

        self._style_store: dict[str, ButtonStyle] = {}

        self._buttons: dict[ValidButtonKeys, PaginatorButton] = DEFAULT_BUTTONS.copy()
        if buttons:
            self._buttons.update(buttons)

        self._combine_switcher_and_stop_button: bool = combine_switcher_and_stop_button
        self._stop_button_and_page_switcher_view: Optional[PageSwitcherAndStopButtonView] = None
        if self._combine_switcher_and_stop_button:
            self._stop_button_and_page_switcher_view = PageSwitcherAndStopButtonView(self)

        self.always_show_stop_button: bool = always_show_stop_button

        self.__add_buttons()

    def __handle_always_show_stop_button(self) -> None:
        if not self.always_show_stop_button:
            return

        if "STOP" not in self._buttons:
            raise ValueError("STOP button is required if always_show_stop_button is True.")

        name = "STOP"
        button = self._buttons[name]
        button.custom_id = f"{name.lower()}_button"
        setattr(self, name, button)
        self.add_item(button)

    async def _handle_modal(self, interaction: Interaction) -> Optional[int]:
        modal = ChooseNumber(self)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal.value

    def __add_buttons(self) -> None:
        if not self.max_pages > 1:
            if self.always_show_stop_button:
                self.__handle_always_show_stop_button()
                return

            self.stop()
            return

        _buttons: dict[str, PaginatorButton] = {name: button for name, button in self._buttons.items() if button}
        sorted_buttons = sorted(_buttons.items(), key=lambda b: b[1].position if b[1].position is not None else 0)
        for name, button in sorted_buttons:
            CUSTOM_ID = f"{name.lower()}_button"
            button.custom_id = CUSTOM_ID
            self._style_store[CUSTOM_ID] = button.style

            setattr(self, name, button)

            if button.custom_id == "page_indicator_button":
                button.label = self.page_string
                if self.max_pages <= 2:
                    button.disabled = True

            if button.custom_id in ("first_button", "last_button"):
                if self.max_pages <= 2:
                    continue
                else:
                    if button.custom_id == "first_button":
                        button.label = f"1 {button.label if button.label else ''}"
                    else:
                        button.label = f"{button.label if button.label else ''} {self.max_pages}"

            if self._combine_switcher_and_stop_button and button.custom_id == "stop_button":
                continue

            self.add_item(button)

        if self._combine_switcher_and_stop_button and self._stop_button_and_page_switcher_view:
            self._stop_button_and_page_switcher_view._add_buttons(self)

        self._update_buttons_state()

    def _update_buttons_state(self) -> None:
        button: PaginatorButton
        for button in self.children:  # type: ignore
            # type checker
            if not button.custom_id:
                raise ValueError("Something went wrong... button.custom_id is None")

            if button.custom_id in ("page_indicator_button", "stop_button"):
                if button.custom_id == "page_indicator_button":
                    button.label = self.page_string
                continue

            if button.custom_id in ("right_button", "last_button"):
                button.disabled = self._current_page >= self.max_pages - 1
            elif button.custom_id in ("left_button", "first_button"):
                button.disabled = self._current_page <= 0

            if not button.disabled:
                button.style = ButtonStyle.green

            if button.disabled:
                button.style = self._style_store[button.custom_id]

    async def stop_paginator(self, interaction: Optional[Interaction] = None) -> None:
        message = self.message
        if interaction is not None:
            if not interaction.response.is_done():
                if self.disable_after:
                    self._disable_all_children()
                    await interaction.response.edit_message(view=self)
                elif self.clear_buttons_after:
                    await interaction.response.edit_message(view=None)
                elif self.delete_after:
                    if interaction.message is not None:
                        await interaction.message.delete()
                    elif self.message:
                        await interaction.response.defer()
                        await self.message.delete()
                else:
                    await interaction.response.defer()

                self.stop()
                return
            else:
                message = interaction.message or self.message

        if message is not None:
            if self.delete_after:
                await message.delete()
            elif self.disable_after:
                self._disable_all_children()
                await message.edit(view=self)
            elif self.clear_buttons_after:
                await message.edit(view=None)

        self.stop()

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        self._current_page = value
        self._update_buttons_state()
