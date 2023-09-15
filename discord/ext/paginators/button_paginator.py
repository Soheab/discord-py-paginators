from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Union,
)

from discord import ButtonStyle, Emoji, PartialEmoji
from discord.ui import Button, Modal, TextInput

from .base_paginator import BaseClassPaginator
from ._types import BotT, Page, InteractionT, ContextT

if TYPE_CHECKING:
    from ._types import Page, PossibleMessage

    from discord.abc import Messageable

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

    def __init__(self, paginator: ButtonPaginator[Any, Any], /, **kwargs: Any) -> None:
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

    async def on_submit(self, interaction: InteractionT) -> None:
        assert isinstance(self.number_input.value, str)

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
        await interaction.response.send_message(f"There is page {self.value + 1} for you <3", ephemeral=True)
        self.stop()


class PaginatorButton(Button["ButtonPaginator[Any, Any]"]):
    view: ButtonPaginator[Any, Any]  # pyright: ignore [reportIncompatibleMethodOverride] # this is better

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
    ):
        super().__init__(emoji=emoji, label=label, custom_id=custom_id, style=style, row=row, disabled=disabled)
        self.position: Optional[int] = position

    async def __handle_modal(self, interaction: InteractionT) -> Optional[int]:
        modal = ChooseNumber(self.view)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal.value

    async def callback(self, interaction: InteractionT) -> None: 
        self.view._interaction = interaction  # pyright: ignore [reportPrivateUsage] # idc

        if self.custom_id == "stop_button":
            await self.view.stop_paginator()
            return

        if self.custom_id == "right_button":
            self.view._current_page += 1  # pyright: ignore [reportPrivateUsage]
        elif self.custom_id == "left_button":
            self.view._current_page -= 1  # pyright: ignore [reportPrivateUsage]
        elif self.custom_id == "first_button":
            self.view._current_page = 0  # pyright: ignore [reportPrivateUsage]
        elif self.custom_id == "last_button":
            self.view._current_page = self.view.max_pages - 1  # pyright: ignore [reportPrivateUsage]
        elif self.custom_id == "page_indicator_button":
            new_page = await self.__handle_modal(interaction)
            if new_page is not None:
                self.view._current_page = new_page  # pyright: ignore [reportPrivateUsage]
            else:
                return

        self.view._update_buttons_state()  # pyright: ignore [reportPrivateUsage]
        pages = self.view.get_page(self.view._current_page)  # pyright: ignore [reportPrivateUsage]
        edit_kwargs = (await self.view.get_kwargs_from_page(pages)).copy()
        edit_kwargs["attachments"] = edit_kwargs.pop("files", [])
        await self.view._edit_message(interaction, **edit_kwargs)  # pyright: ignore [reportPrivateUsage]


class ButtonPaginator(BaseClassPaginator[Page, BotT]):
    FIRST: Optional[PaginatorButton] = None  # filled in __add_buttons
    LEFT: Optional[PaginatorButton] = None  # filled in __add_buttons
    RIGHT: Optional[PaginatorButton] = None  # filled in __add_buttons
    LAST: Optional[PaginatorButton] = None  # filled in __add_buttons
    STOP: Optional[PaginatorButton] = None  # filled in __add_buttons
    PAGE_INDICATOR: Optional[PaginatorButton] = None  # filled in __add_buttons

    def __init__(
        self,
        pages: list[Page],
        *,
        buttons: ValidButtonsDict = {},
        always_show_stop_button: bool = False,
        **kwargs: Any,
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

    def __add_buttons(self) -> None:
        if not self.max_pages > 1:
            if self.always_show_stop_button:
                self.__handle_always_show_stop_button()
                return

            self.stop()
            return

        _buttons: dict[str, PaginatorButton] = {
            name: button for name, button in self._buttons.items() if button
        }
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

            self.add_item(button)

        self._update_buttons_state()

    def _update_buttons_state(self) -> None:
        button: PaginatorButton
        for button in self.children:  # type: ignore
            assert button.custom_id, "Something went wrong... button.custom_id is None"

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

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        self._current_page = value
        self._update_buttons_state()

    async def send(
        self,
        *,
        ctx: Optional[ContextT] = None,
        send_to: Optional[Messageable] = None,
        interaction: Optional[InteractionT] = None,
        override_custom: bool = False,
        force_send: bool = False,
        **kwargs: Any,
    ) -> PossibleMessage:
        page = self.get_page(self.current_page)
        return await super()._handle_send(
            page,
            ctx=ctx,
            send_to=send_to,
            interaction=interaction,
            force_send=force_send,
            override_custom=override_custom,
            **kwargs,
        )
