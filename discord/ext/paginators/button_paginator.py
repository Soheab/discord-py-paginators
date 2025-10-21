from __future__ import annotations
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, NotRequired, Optional, TypedDict, overload

import discord

from .core import BaseClassPaginator

from .enums import _KnownComponentIDs, ButtonKey


if TYPE_CHECKING:
    from typing_extensions import Unpack, Self

    from ._types import BasePaginatorKwargs, BoundPage, BoundV2Page
    from .views import View

    class ButtonsDict(TypedDict, total=False):
        label: str | None
        emoji: discord.Emoji | discord.PartialEmoji | str | None
        style: discord.ButtonStyle
        position: int | None
        disabled: bool
        row: NotRequired[int | None]

    ValidButtonsDict = dict[_KnownComponentIDs, "PaginatorButton | ButtonsDict | None"]

__all__: tuple[str, ...] = (
    "ButtonPaginator",
    "PaginatorButton",
)


class ChooseNumber(discord.ui.Modal):
    number_input: discord.ui.Label[Any] = discord.ui.Label(
        text="Enter a number between 1 and {0}",
        component=discord.ui.TextInput(
            placeholder="Current: {0}",
            custom_id="paginator:textinput:choose_number",
            max_length=0,
            min_length=1,
        ),
    )

    def __init__(self, paginator: ButtonPaginator[Any], /, **kwargs: Any) -> None:
        super().__init__(
            title="Which page would you like to go to?",
            timeout=paginator.view.timeout,
            custom_id="paginator:modal:choose_number",
            **kwargs,
        )
        self.paginator: ButtonPaginator[Any] = paginator

        # type checker
        if not isinstance(self.number_input.component, discord.ui.TextInput):
            raise TypeError("Something went wrong... number_input.component is not a TextInput.")

        self.number_input.component.max_length = paginator.total_pages
        self.number_input.component.label = (self.number_input.component.label or "").format(paginator.total_pages)

        if not self.number_input.component.placeholder:
            self.number_input.component.placeholder = f"Current: {paginator.current_page_index + 1}"
        else:
            self.number_input.component.placeholder = self.number_input.component.placeholder.format(
                paginator.current_page_index + 1
            )

        self.value: Optional[int] = None

    async def on_submit(self, interaction: discord.Interaction[Any]) -> None:
        # can't happen but type checker
        if not isinstance(self.number_input.component, discord.ui.TextInput):
            raise TypeError("Something went wrong... number_input.component is not a TextInput.")
        if not self.number_input.component.value:
            await interaction.response.send_message("Please enter a number!", ephemeral=True)
            self.stop()
            return

        if (
            not self.number_input.component.value.isdigit()
            or int(self.number_input.component.value) <= 0
            or int(self.number_input.component.value) > self.paginator.total_pages
        ):
            await interaction.response.send_message(
                f"Please enter a valid number between 1 and {self.paginator.total_pages}", ephemeral=True
            )
            self.stop()
            return

        number = int(self.number_input.component.value) - 1

        if number == self.paginator.current_page_index:
            await interaction.response.send_message("That is the current page!", ephemeral=True)
            self.stop()
            return

        self.value = number
        await interaction.response.defer()
        self.stop()


class ButtonsKwargsMeta(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
        *,
        buttons: dict[ButtonKey, ButtonsDict | None] | None = None,
    ) -> type:
        attrs["__modified_buttons__"] = {}
        for key, value in (buttons or {}).items():
            if not isinstance(key, ButtonKey):
                raise TypeError(f"Expected ButtonKey, got {type(key).__name__}")

            if not isinstance(value, (dict, type(None))):
                raise TypeError(f"Expected dict or None, got {type(value).__name__}")

            attrs["__modified_buttons__"][key] = value

        self = super().__new__(cls, name, bases, attrs)
        return self


class ButtonPaginator[PageT: (BoundPage, BoundV2Page)](
    BaseClassPaginator[PageT],
    metaclass=ButtonsKwargsMeta,
):
    """A paginator that uses buttons to switch pages.

    This class has a few parameters that differ from the base paginator.

    See the supported page types and lots of parameters on :class:`.BaseClassPaginator`.

    Parameters
    ----------
    buttons: dict[:class:`ButtonKey`, :class:`.PaginatorButton`]
        A dictionary of buttons to use. The keys must be :class:`ButtonKey` enum values.
        The values must be a PaginatorButton or ``None`` to remove the button.
        If not specified, the default buttons will be used.

        Example
        -------

        .. code-block:: python3
            :linenos:

            from discord.ext.paginators import ButtonPaginator, PaginatorButton, ButtonKey

            custom_buttons = {
                # change the label of the first button from "First" to "Go to first page"
                ButtonKey.FIRST: PaginatorButton(label="Go to first page"),
                # change the style of the LAST button to red
                ButtonKey.LAST: PaginatorButton(style=ButtonStyle.red),
            }

            # pass the custom buttons to the paginator
            paginator = ButtonPaginator(pages, buttons=custom_buttons)
            ... # rest of code

        There are 2 more ways to modify the buttons:

        1. Use the :meth:`ButtonPaginator.edit_button` method to edit or remove buttons after the paginator has been created.

        .. code-block:: python3
            :linenos:

            # change the emoji of the first button
            paginator.edit_button(ButtonKey.FIRST, emoji="👈")
            # remove Last button
            paginator.edit_button(ButtonKey.LAST, remove=True)

        2. Use the `buttons=` kwarg with the class when subclassing

        .. code-block:: python3
            :linenos:

            class CustomPaginator(ButtonPaginator, buttons={
                # change the style of the left button
                ButtonKey.LEFT: {"style": discord.ButtonStyle.gray},
                # change the label and emoji of the right button
                ButtonKey.RIGHT: {"label": "Go to next page", "emoji": "🤜"},
                # remove stop button
                ButtonKey.STOP: None,
            }):
                ...

    always_show_stop_button: bool
        Whether to always show the stop button, even if there is only one page.
        Defaults to ``False``.

        .. note::
            If ``always_show_stop_button`` is ``True``, the ``STOP`` key in ``buttons`` cannot be ``None``.
    style_if_clickable: discord.ButtonStyle
        The style to change the buttons that are not disabled / clickable to and changes them back to the original style otherwise.
        Defaults to :attr:`discord.ButtonStyle.green`. Pass ``None`` to disable this feature.

        .. versionadded:: 0.3.0
    **kwargs: Unpack[:class:`.BasePaginatorKwargs`]
        See other parameters on :class:`.BaseClassPaginator`.
    """

    # --- Class configuration -------------------------------------------------
    __buttons__: dict[ButtonKey, ButtonsDict | None] = {
        ButtonKey.FIRST: {
            "label": "First",
            "style": discord.ButtonStyle.primary,
            "emoji": "\u23ea",  # ⏪
            "position": 0,
            "row": None,
        },
        ButtonKey.LEFT: {
            "label": "Left",
            "style": discord.ButtonStyle.primary,
            "emoji": "\u25c0",  # ◀️
            "position": 1,
            "row": None,
        },
        ButtonKey.PAGE_INDICATOR: {
            "label": "Page N/A / N/A",
            "style": discord.ButtonStyle.primary,
            "emoji": "\U0001f522",  # 🔢
            "position": 2,
            "disabled": False,
            "row": None,
        },
        ButtonKey.RIGHT: {
            "label": "Right",
            "style": discord.ButtonStyle.primary,
            "emoji": "\u25b6",  # ▶️
            "position": 3,
            "row": None,
        },
        ButtonKey.LAST: {
            "label": "Last",
            "style": discord.ButtonStyle.primary,
            "emoji": "\u23e9",  # ⏩
            "position": 4,
            "row": None,
        },
        ButtonKey.STOP: {
            "label": "Stop",
            "style": discord.ButtonStyle.danger,
            "emoji": "\u23f9",  # ⏹️
            "position": 5,
            "row": None,
        },
    }

    # --- Initialization ------------------------------------------------------
    def __init__(
        self,
        pages: list[PageT] = discord.utils.MISSING,
        *,
        buttons: ValidButtonsDict = {},
        always_show_stop_button: bool = False,
        # combine_switcher_and_stop_button: bool = False,
        style_if_clickable: discord.ButtonStyle | None = discord.utils.MISSING,
        container: discord.ui.Container[Any] | bool | None = discord.utils.MISSING,
        container_accent_colour: discord.Colour | int | None = discord.utils.MISSING,
        add_buttons_to_container: bool = discord.utils.MISSING,
        **kwargs: Unpack[BasePaginatorKwargs[Self]],
    ) -> None:
        modified_buttons: dict[ButtonKey, ButtonsDict | None] = getattr(self, "__modified_buttons__", {})
        for key, value in modified_buttons.items():
            self.__edit_button(key, value)

        components_v2 = kwargs.get("components_v2", None)
        if components_v2 is None:
            kwargs["components_v2"] = (
                any([
                    container,
                    container_accent_colour,
                    add_buttons_to_container,
                ])
                or None
            )

        if buttons:
            valid_button_dict_keys: tuple[str, ...] = ("label", "style", "emoji", "position", "disabled")
            hint = "Consider using the .edit_button method to modify the default buttons instead."

            if not isinstance(buttons, dict):
                raise TypeError(f"'buttons' must be a dictionary. {hint}")

            for key, value in buttons.items():
                if not isinstance(key, ButtonKey):
                    raise TypeError(f"All keys in 'buttons' must be of type ButtonKey, not {type(key)!r}. {hint}")

                if value is None:
                    self.__buttons__[key] = None
                elif isinstance(value, PaginatorButton):
                    self.__buttons__[key] = value._original_kwargs
                elif isinstance(value, dict):
                    unknown_keys = set(value) - set(valid_button_dict_keys)
                    if unknown_keys:
                        raise TypeError(
                            f"Unknown keys in button dict: {', '.join(unknown_keys)}. "
                            f"Allowed keys: {', '.join(valid_button_dict_keys)}. {hint}"
                        )
                    self.__buttons__[key] = value
                else:
                    raise TypeError(f"Button values must be a PaginatorButton, dict, or None. {hint}")

        self._buttons: dict[ButtonKey, PaginatorButton | None] = {
            k: (PaginatorButton(**v) if v is not None else None) for k, v in self.__buttons__.items()
        }

        self.always_show_stop_button: bool = always_show_stop_button

        if style_if_clickable is discord.utils.MISSING:
            self._style_if_clickable = discord.ButtonStyle.green
        elif style_if_clickable is not None:
            if not isinstance(style_if_clickable, discord.ButtonStyle):
                raise TypeError("style_if_clickable must be a discord.ButtonStyle or None.")
            self._style_if_clickable = style_if_clickable
        else:
            self._style_if_clickable = None

        self._buttons_container: discord.ui.Container[Any] | None = None
        self._add_buttons_to_container = add_buttons_to_container
        self._container: discord.ui.Container[Any] | None = None
        self._button_actionrows: dict[int, discord.ui.ActionRow[Any]] = {}

        self.__initial_container_items_count: int = 0

        if container not in (discord.utils.MISSING, False, None):
            if not isinstance(container, (discord.ui.Container, bool)):
                raise TypeError("container must be a discord.ui.Container or True.")

            self._container = container if isinstance(container, discord.ui.Container) else discord.ui.Container()
            self._container.id = _KnownComponentIDs.CONTAINER
            self.__initial_container_items_count = len(self._container.children)

        if container_accent_colour and self._container:
            self._container.accent_colour = container_accent_colour

        if add_buttons_to_container and not self._container:
            self._buttons_container = discord.ui.Container(id=_KnownComponentIDs.BUTTONS_CONTAINER)

        super().__init__(pages, **kwargs)  # pyright: ignore[reportArgumentType]

    @property
    def current_page_index(self) -> int:
        return super().current_page_index

    @current_page_index.setter
    def current_page_index(self, value: int) -> None:
        super(__class__, type(self)).current_page_index.__set__(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            self, value
        )
        self._update_buttons_state()

    @overload
    def edit_button(
        self,
        key: ButtonKey,
        /,
        *,
        label: str | None = discord.utils.MISSING,
        style: discord.ButtonStyle = discord.utils.MISSING,
        emoji: discord.Emoji | discord.PartialEmoji | str | None = discord.utils.MISSING,
        position: int | None = discord.utils.MISSING,
    ) -> None: ...

    @overload
    def edit_button(
        self,
        key: ButtonKey,
        /,
        *,
        remove: Literal[True] = ...,
    ) -> None: ...

    def edit_button(
        self,
        key: ButtonKey,
        /,
        *,
        label: str | None = discord.utils.MISSING,
        style: discord.ButtonStyle = discord.utils.MISSING,
        emoji: discord.Emoji | discord.PartialEmoji | str | None = discord.utils.MISSING,
        position: int | None = discord.utils.MISSING,
        remove: bool = False,
    ) -> None:
        options: ButtonsDict = {}
        if label is not discord.utils.MISSING:
            options["label"] = label
        if style is not discord.utils.MISSING:
            options["style"] = style
        if emoji is not discord.utils.MISSING:
            options["emoji"] = emoji
        if position is not discord.utils.MISSING:
            options["position"] = position

        self.__edit_button(key, options if not remove else None)

    async def handle_pages(self, pages: Sequence[PageT]) -> dict[str, Any]:
        res = await super().handle_pages(pages)
        self.__add_buttons()
        return res

    def _clear_all_view_items(self) -> None:
        if self._container:
            for item in self._container.children[self.__initial_container_items_count :]:
                self._container.remove_item(item)

        if self._buttons_container:
            self._buttons_container.clear_items()

        super()._clear_all_view_items()

    def _add_item(self, item: discord.ui.Item[Any]) -> discord.ui.Item[Any]:
        if not isinstance(self.view, discord.ui.LayoutView):
            return super()._add_item(item)

        if isinstance(item, discord.ui.Container):
            return super()._add_item(item)

        target = self._container if self._container else self.view
        target.add_item(item)

        if self._container and self._container.children and self._container not in self.view.children:
            self.view.add_item(self._container)

        return item

    def __handle_always_show_stop_button(self) -> None:
        if not self.always_show_stop_button:
            return

        button = self._buttons.get(ButtonKey.STOP)
        if not button:
            raise ValueError("STOP button is required if always_show_stop_button is True.")

        button.id = _KnownComponentIDs.STOP_BUTTON
        self._add_item(button)

    async def _handle_modal(self, interaction: discord.Interaction[Any]) -> Optional[int]:
        modal = ChooseNumber(self)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal.value

    def __add_button(self, button: PaginatorButton) -> None:
        # type checker, cannot happpen.
        if not button.id:
            raise ValueError("Something went wrong... button must have an id set.")

        button_added: bool = False

        if not isinstance(self.view, discord.ui.LayoutView):
            if not self.view.find_item(button.id):
                self._add_item(button)
            return

        # Choose the correct target container
        target: discord.ui.Container[Any] | View[Self] = self.view
        if self._add_buttons_to_container or self._buttons_container:
            if self._buttons_container:
                target = self._buttons_container
            elif self._container and self._add_buttons_to_container:
                target = self._container

        # type checker, cannot happen.
        if not target.id:
            raise ValueError("Something went wrong... target must have an id set.")

        # Find or create action rows
        action_row_1: discord.ui.ActionRow[Any] = (
            target.find_item(_KnownComponentIDs.BUTTON_ACTION_ROW)
            or self._button_actionrows.get(_KnownComponentIDs.BUTTON_ACTION_ROW)
            or discord.ui.ActionRow[Any](id=_KnownComponentIDs.BUTTON_ACTION_ROW)
        )  # pyright: ignore[reportAssignmentType]
        action_row_2: discord.ui.ActionRow[Any] = (
            target.find_item(_KnownComponentIDs.BUTTON_ACTION_ROW2)
            or self._button_actionrows.get(_KnownComponentIDs.BUTTON_ACTION_ROW2)
            or discord.ui.ActionRow[Any](id=_KnownComponentIDs.BUTTON_ACTION_ROW2)
        )  # pyright: ignore[reportAssignmentType]

        if not action_row_1.find_item(button.id) and not len(action_row_1.children) >= 5 and not button_added:
            button_added = True
            action_row_1.add_item(button)

        button_added = button_added or bool(action_row_1.find_item(button.id))

        if (
            action_row_2
            and not action_row_2.find_item(button.id)
            and not len(action_row_2.children) >= 5
            and not button_added
        ):
            action_row_2.add_item(button)

        self._button_actionrows[_KnownComponentIDs.BUTTON_ACTION_ROW] = action_row_1
        self._button_actionrows[_KnownComponentIDs.BUTTON_ACTION_ROW2] = action_row_2

        # type checker, cannot happen.
        if not action_row_1.id:
            raise ValueError("Something went wrong... action_row_1 must have an id set.")

        if not target.find_item(action_row_1.id):
            target.add_item(action_row_1)

        if action_row_2 and action_row_2.children:
            # type checker, cannot happen.
            if not action_row_2.id:
                raise ValueError("Something went wrong... action_row_2 must have an id set.")

            if not target.find_item(action_row_2.id):
                target.add_item(action_row_2)

        if isinstance(target, discord.ui.Container) and not self.view.find_item(target.id):
            self.view.add_item(target)

    def __edit_button(self, key: ButtonKey, options: ButtonsDict | None) -> None:
        if not hasattr(self, "_buttons"):
            self._buttons = {}

        original_button = self.__buttons__[key]
        if original_button is None and options is None:
            return

        if options is None:
            self.__buttons__[key] = None
            self._buttons[key] = None
            return

        if not original_button:
            self.__buttons__[key] = options
        else:
            self.__buttons__[key] = {**original_button, **options}

        self._buttons[key] = PaginatorButton(**self.__buttons__[key])  # pyright: ignore[reportCallIssue]

    @staticmethod
    def __buttons_sort_key(button: tuple[ButtonKey, PaginatorButton] | PaginatorButton | None) -> int:
        if button is None:
            return 0

        if isinstance(button, tuple):
            button = button[1]

        return button.position if button.position is not None else button.id if button.id is not None else 0

    def __add_buttons(self) -> None:
        if self.total_pages <= 1 and self._initial_pages:
            if self.always_show_stop_button:
                self.__handle_always_show_stop_button()
                return

            self.stop()
            return

        _buttons: dict[ButtonKey, PaginatorButton] = {
            key: button.copy() for key, button in self._buttons.copy().items() if button
        }
        sorted_buttons = sorted(_buttons.items(), key=self.__buttons_sort_key)
        for key, button in sorted_buttons:
            button.id = _KnownComponentIDs.from_key(key)
            if button.id == _KnownComponentIDs.PAGE_INDICATOR_BUTTON:
                button.label = self.page_string
                if self.total_pages <= 2:
                    button.disabled = True

            if button.id in (_KnownComponentIDs.FIRST_BUTTON, _KnownComponentIDs.LAST_BUTTON):
                if self.total_pages <= 2:
                    continue

                label = button.label or ""
                if button.id == _KnownComponentIDs.FIRST_BUTTON:
                    button.label = f"1 {label}"
                else:
                    button.label = f"{label} {self.total_pages}"

            self.__add_button(button)

        self._update_buttons_state()

    def _update_buttons_state(
        self,
    ) -> None:
        for button in self.view.walk_children():
            if isinstance(button, discord.ui.ActionRow) and button.id in (
                _KnownComponentIDs.BUTTON_ACTION_ROW,
                _KnownComponentIDs.BUTTON_ACTION_ROW2,
            ):
                button._children.sort(key=self.__buttons_sort_key)  # pyright: ignore[reportArgumentType]
            # type checker
            if not isinstance(button, PaginatorButton):
                continue

            # type checker
            if not button.id:
                raise ValueError("Something went wrong... button.id is None")

            original_button = self._buttons.get(ButtonKey.from_id(button.id))

            if button.id in (_KnownComponentIDs.STOP_BUTTON, _KnownComponentIDs.PAGE_INDICATOR_BUTTON):
                if button.id == _KnownComponentIDs.PAGE_INDICATOR_BUTTON:
                    button.label = self.page_string
                continue

            if button.id in (_KnownComponentIDs.FIRST_BUTTON, _KnownComponentIDs.LAST_BUTTON):
                button.disabled = self.total_pages <= 2

                if original_button:
                    label = original_button.label if original_button.label else ""
                    if button.id == _KnownComponentIDs.FIRST_BUTTON:
                        button.label = f"1 {label}"
                    else:
                        button.label = f"{label} {self.total_pages}"

            if button.id in (_KnownComponentIDs.RIGHT_BUTTON, _KnownComponentIDs.LAST_BUTTON):
                button.disabled = self.current_page_index >= (self.total_pages - 1) and not self.switch_pages_humanly

            elif button.id in (_KnownComponentIDs.LEFT_BUTTON, _KnownComponentIDs.FIRST_BUTTON):
                button.disabled = self.current_page_index <= 0 and not self.switch_pages_humanly

            if self._style_if_clickable is not None:
                if not button.disabled:
                    button.style = self._style_if_clickable
                else:
                    button.style = original_button.style if original_button else discord.ButtonStyle.secondary


class PaginatorButton(
    discord.ui.Button["View[ButtonPaginator[Any]]"],
):
    """A button for the paginator.

    This class has a few parameters that differ from the base button.
    This can can be used passed to the ``buttons`` parameter in :class:`.ButtonPaginator`
    to customize the buttons used.

    See other parameters on :class:`discord.ui.Button`.

    Parameters
    ----------
    position: int | None
        The position of the button. Defaults to ``None``.
        If not specified, the button will be placed in the order they were added
        or whatever order discord.py adds them in.
    """

    view: View[ButtonPaginator[Any]]  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(
        self,
        *,
        emoji: discord.Emoji | discord.PartialEmoji | str | None = None,
        label: str | None = None,
        style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        disabled: bool = False,
        position: int | None = None,
        row: int | None = None,
    ) -> None:
        self._original_kwargs: ButtonsDict = {
            "emoji": emoji,
            "label": label,
            "style": style,
            "disabled": disabled,
            "position": position,
            "row": row,
        }
        super().__init__(emoji=emoji, label=label, style=style, disabled=disabled, row=row)
        self.position: int | None = position

    async def callback(self, interaction: discord.Interaction[Any]) -> None:
        # type checker
        if not self.view:
            msg = "Something went wrong... view is None. Report this to my developer."
            raise ValueError(msg)

        paginator = self.view.paginator

        # if isinstance(paginator, PageSwitcherAndStopButtonView):
        #    await paginator.callback(interaction, self)
        #    return

        if self.id == _KnownComponentIDs.STOP_BUTTON:
            await paginator.stop_paginator(interaction, is_timeout=False)
            return

        next_page_number: int = paginator.current_page_index

        if self.id == _KnownComponentIDs.RIGHT_BUTTON:
            next_page_number += 1
        elif self.id == _KnownComponentIDs.LEFT_BUTTON:
            next_page_number -= 1
        elif self.id == _KnownComponentIDs.FIRST_BUTTON:
            if paginator.current_page_index == 0:
                next_page_number = paginator.total_pages - 1
            else:
                next_page_number = 0
        elif self.id == _KnownComponentIDs.LAST_BUTTON:
            if paginator.current_page_index >= paginator.total_pages - 1:
                next_page_number = 0
            else:
                next_page_number = paginator.total_pages - 1
        elif self.id == _KnownComponentIDs.PAGE_INDICATOR_BUTTON:
            # if self._paginator._stop_button_and_page_switcher_view:
            #     await interaction.response.send_message(
            #         view=self._paginator._stop_button_and_page_switcher_view, ephemeral=True
            #     )
            #     return

            new_page = await paginator._handle_modal(interaction)
            if new_page is not None:
                next_page_number = new_page
            else:
                return

        await paginator.switch_page(interaction, next_page_number)
