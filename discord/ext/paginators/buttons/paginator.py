from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, TypeVar, Union
from collections.abc import Sequence

import os

import discord
from discord.ui import Button, Modal, TextInput

from ..base_paginator import BaseClassPaginator
from .button import PaginatorButton, DefaultButtons, _CallbackWrapper, ButtonKey
from .._types import PageT
from .. import utils

if TYPE_CHECKING:
    from typing_extensions import Unpack, Self

    from .._types import BasePaginatorKwargs
    from ._types import (
        OriginalButtonKwargs,
        DecoFunc,
        ButtonOverrideMetadata,
        CustomButtonKwargs,
        DecoCls,
        OriginalButtonKwargsWithPosition,
    )

    ValidButtonKeys = Union[Literal["FIRST", "LEFT", "RIGHT", "LAST", "STOP", "PAGE_INDICATOR"], ButtonKey]
    ValidButtonsDict = dict[ValidButtonKeys, "PaginatorButton"]

    SortOnPositionMappingKT = TypeVar("SortOnPositionMappingKT")
    SortOnPositionMappingVT = TypeVar("SortOnPositionMappingVT")
    SortOnPositionMappingT = dict[SortOnPositionMappingKT, SortOnPositionMappingVT]
    ValidSortKeys = Literal["position", "label", "custom_id"]

    BaseClassPaginator = BaseClassPaginator

__all__: tuple[str, ...] = ("ButtonPaginator", "SortButtonsOn", "callback_for", "custom_button", "customise_button")


class SortButtonsOn(discord.Enum):
    """An enum that represents the position to sort the buttons in the paginator."""

    POSITION = "position"
    """Sort the buttons based on the position attribute of :class:.PaginatorButton`."""
    LABEL = "label"
    """Sort the buttons based on the label attribute."""
    CUSTOM_ID = "custom_id"
    """Sort the buttons based on the custom_id attribute."""

    def _do_sort(
        self, buttons: dict[SortOnPositionMappingKT, SortOnPositionMappingVT]
    ) -> dict[SortOnPositionMappingKT, SortOnPositionMappingVT]:
        predicate: Callable[[tuple[SortOnPositionMappingKT, SortOnPositionMappingVT]], Union[int, str]] = lambda x: 0

        if self is SortButtonsOn.POSITION:
            predicate = lambda x: getattr(x[1], "position", 0) or 0
        elif self is SortButtonsOn.LABEL:
            predicate = lambda x: getattr(x[1], "label", "") or ""
        elif self is SortButtonsOn.CUSTOM_ID:
            predicate = lambda x: getattr(x[1], "custom_id", "") or ""

        return dict(sorted(buttons.items(), key=predicate))


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
        self.number_input.max_length = len(str(paginator.max_pages))
        self.number_input.label = self.number_input.label.format(paginator.max_pages)

        # type checker
        if not self.number_input.placeholder:
            self.number_input.placeholder = f"Current: {paginator.current_page + 1}"
        else:
            self.number_input.placeholder = self.number_input.placeholder.format(paginator.current_page + 1)

    async def on_submit(self, interaction: discord.Interaction[Any]) -> None:
        await interaction.response.defer()

        value = self.number_input.value
        max_pages: int = self.paginator.max_pages
        error_text: str = (
            f"Please enter a valid number between 1 and {self.paginator.max_pages} (but not {self.paginator.current_page})"
        )

        try:
            value = int(value)
        except ValueError:
            await interaction.followup.send(error_text, ephemeral=True)
        else:
            if value < 1 or value > max_pages:
                await interaction.followup.send(error_text, ephemeral=True)

        self.stop()


class PageSwitcherAndStopButtonView(discord.ui.View):
    STOP: Optional[Button["ButtonPaginator[Any]"]] = None  # filled in _add_buttons
    PAGE_INDICATOR: Optional[Button["ButtonPaginator[Any]"]] = None  # filled in _add_buttons

    def __init__(self, paginator: ButtonPaginator[Any], /) -> None:
        super().__init__(timeout=paginator.timeout)

    def _add_buttons(self, paginator: ButtonPaginator[Any], /) -> None:
        self._paginator: ButtonPaginator[Any] = paginator

        error_text = "STOP and PAGE_INDICATOR buttons are required if combine_switcher_and_stop_button is True."

        try:
            org_page_indicator_button: PaginatorButton = paginator._buttons[ButtonKey.PAGE_INDICATOR]  # type: ignore # handled
            org_stop_button: PaginatorButton = paginator._buttons[ButtonKey.STOP]  # type: ignore # handled
        except KeyError:
            raise ValueError(error_text)
        else:
            if not org_page_indicator_button or not org_stop_button:
                raise ValueError(error_text)

        page_indicator_button = org_page_indicator_button._copy(
            label="Switch Page",
            custom_id="page_indicator_button",
            disabled=False,
        )

        stop_button = org_stop_button._copy(
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

    async def _call_button(self, interaction: discord.Interaction[Any], button: PaginatorButton) -> None:
        custom_id = button.custom_id
        if custom_id == "switch_page":
            await interaction.response.send_message(
                view=self,
                ephemeral=True,
            )
            return

        new_page = self._paginator.current_page

        if custom_id == "stop_button":
            await interaction.response.defer()
            await interaction.delete_original_response()
            await self._paginator.stop_paginator(interaction)
            return

        if custom_id == "page_indicator_button":
            modal_value = await self._paginator._handle_modal(interaction)
            await interaction.delete_original_response()
            if modal_value is not None:
                new_page = modal_value

        await self._paginator.switch_page(interaction, new_page)


class ButtonPaginator(BaseClassPaginator[PageT]):
    """A paginator that uses buttons to switch pages.

    This class has a few parameters that differ from the base paginator.

    Just for clarification, here is a list of supported pages:

    - :class:`discord.Embed`
    - :class:`discord.File`
    - :class:`discord.Attachment`
    - :class:`str`
    - :class:`dict`
    - :class:`list` or :class:`tuple` of the above

    See other parameters on :class:`.BaseClassPaginator`.

    Parameters
    ----------
    buttons: Optional[Dict[Union[:class:`str`, :class:`.ButtonKey`], :class:`.PaginatorButton`]]
        A dictionary of buttons to customize. The keys must be one of the following:
        "FIRST", "LEFT", "RIGHT", "LAST", "STOP", "PAGE_INDICATOR" or a :class:`.ButtonKey`.
        The values must be a PaginatorButton or ``None`` to remove the button.
        If not specified, the default buttons will be used.

        Example
        -------
        .. code-block:: python3
            :linenos:

            from discord.ext.paginators import ButtonPaginator, PaginatorButton

            buttons = {
                # change the label of the first button from "First" to "Go to first page"
                "FIRST": PaginatorButton(label="Go to first page"),
                # change the style of the LAST button to red
                "LAST": PaginatorButton(style=ButtonStyle.red),
            }

            # pass the customized buttons to the paginator
            paginator = ButtonPaginator(..., buttons=buttons)
            ... # rest of code

        There are more ways to customize buttons. See :func:`.decorators.callback_for` and
        :func:`.decorators.customise_button`.

    custom_buttons: Optional[List[:class:`.PaginatorButton`]]
        A list of custom buttons to add to the paginator.
        These buttons will be added to the paginator in addition to the default buttons
        and are entirely controlled by you. The libary will not modify these buttons but
        only call the callback when the button is clicked.

        Example
        -------
        .. code-block:: python3
            :linenos:

            import discord
            from discord.ext.paginators import ButtonPaginator, PaginatorButton

            custom_buttons = [
                PaginatorButton(label="Custom Button 1"),
                discord.ui.Button(label="Custom Button 2"), # works too
                PaginatorButton(label="Custom Button 3", position=5), # position but works too
            ]

            paginator = ButtonPaginator(..., custom_buttons=custom_buttons)

        There are more ways to add custom buttons to the paginator. See :func:`.decorators.custom_button` and
        :meth:`.add_custom_buttons`.

        .. versionadded:: 0.3.0

    always_show_stop_button: bool
        Whether to always show the stop button, even if there is only one page.
        Defaults to ``False``.

        .. note::
            If ``always_show_stop_button`` is ``True``, the ``STOP`` key in ``buttons`` cannot be ``None``.
    combine_switcher_and_stop_button: :class:`bool`
        Whether to combine the page switcher and stop button into the paginator indicator which will send another set
        of buttons to switch pages and stop the paginator as an ephemeral message when clicked.
        Defaults to ``False``.

        .. note::
            If ``combine_switcher_and_stop_button`` is ``True``, the ``STOP`` and ``PAGE_INDICATOR`` keys in ``buttons`` cannot be ``None``.
    style_if_clickable: :class:`discord.ButtonStyle`
        The style to change the buttons that are not disabled / clickable to and changes them back to the original style otherwise.
        Defaults to :attr:`discord.ButtonStyle.green`. Pass ``None`` to disable this feature.

        .. versionadded:: 0.3.0
    sort_buttons: Union[:class:`bool`, :class:`SortButtonOn`, :class:`str`]
        Whether to sort the buttons based on the position, label, or custom_id of the button.
        Defaults to :attr:`SortButtonOn.POSITION`. ``True`` is equivalent to :attr:`SortButtonOn.POSITION`.
        ``False`` will not sort the buttons.

        This also works with custom buttons.

        .. versionadded:: 0.3.0
    **kwargs: Unpack[:class:`.BasePaginatorKwargs`]
        See other parameters on :class:`discord.ext.paginator.base_paginator.BaseClassPaginator`.
    """

    FIRST: Optional[PaginatorButton] = None  # filled in __add_buttons
    LEFT: Optional[PaginatorButton] = None  # filled in __add_buttons
    RIGHT: Optional[PaginatorButton] = None  # filled in __add_buttons
    LAST: Optional[PaginatorButton] = None  # filled in __add_buttons
    STOP: Optional[PaginatorButton] = None  # filled in __add_buttons
    PAGE_INDICATOR: Optional[PaginatorButton] = None  # filled in __add_buttons

    __button_overrides__: dict[ButtonKey, ButtonOverrideMetadata] = {}
    __customize_buttons__: dict[ButtonKey, OriginalButtonKwargsWithPosition] = {}
    __custom_buttons__: dict[str, tuple[CustomButtonKwargs, Callable[..., Any]]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        overrides: dict[ButtonKey, ButtonOverrideMetadata] = {}
        custom_buttons: dict[str, tuple[CustomButtonKwargs, Callable[..., Any]]] = {}
        for base in reversed(cls.__mro__):
            for member in base.__dict__.values():
                if hasattr(member, "__dpy_paginator_button_overrides__"):
                    overrides.update(member.__dpy_paginator_button_overrides__)

                if hasattr(member, "__dpy_paginator_custom_button__kws__"):
                    data: CustomButtonKwargs = member.__dpy_paginator_custom_button__kws__
                    custom_buttons[data["custom_id"]] = (data, member)

        cls.__button_overrides__ = overrides
        cls.__custom_buttons__ = custom_buttons

    def __handle_custom_buttons(self) -> None:
        for key, (kwargs, callback) in self.__custom_buttons__.items():
            inst = self._custom_buttons[key] = PaginatorButton(**kwargs, override_callback=True)
            inst.callback = _CallbackWrapper(self, inst, callback)
            inst.callback._is_override = True
            inst._is_custom = True

    def __handle_overrides(self) -> None:
        for key, metadata in self.__button_overrides__.items():
            button = self._buttons.get(key)
            valid_keys = ", ".join(map(str, ButtonKey))
            if not button:
                raise ValueError(f"Button {key} does not exist in the paginator. Valid keys are: {valid_keys}")

            new = button._copy(**(metadata["button"]))
            org_callback: _CallbackWrapper = new.callback  # type: ignore
            org_callback._original_callback = metadata["callback"]
            new.callback = org_callback._copy(
                new,
                is_override=True,
            )
            if metadata["override"]:
                new._override_callback = True
            self._buttons[key] = new

    def __handle_customized_buttons(self) -> None:
        for key, kwargs in self.__customize_buttons__.items():
            button_key = ButtonKey._convert(key)
            valid_keys = ", ".join(map(str, ButtonKey))
            if not button_key:
                raise ValueError(f"Button {key} does not exist in the paginator. Valid keys are: {valid_keys}")

            button = self._buttons.get(button_key)
            if not button:
                raise ValueError(f"Button {key} does not exist in the paginator. Valid keys are: {valid_keys}")

            new = button._copy(**kwargs)
            self._buttons[button_key] = new

    def __init__(
        self,
        pages: Sequence[PageT],
        *,
        buttons: Optional[ValidButtonsDict] = None,
        custom_buttons: Optional[list[PaginatorButton]] = None,
        always_show_stop_button: bool = False,
        combine_switcher_and_stop_button: bool = False,
        style_if_clickable: discord.ButtonStyle | None = discord.utils.MISSING,
        sort_buttons: Union[bool, SortButtonsOn, ValidSortKeys] = SortButtonsOn.POSITION,
        **kwargs: Unpack[BasePaginatorKwargs[Self]],
    ) -> None:
        super().__init__(pages, **kwargs)

        self._stop_button_and_page_switcher_view: Optional[PageSwitcherAndStopButtonView] = (
            PageSwitcherAndStopButtonView(self) if combine_switcher_and_stop_button else None
        )
        self._buttons: dict[ButtonKey, Optional[PaginatorButton]] = DefaultButtons.init(
            self,
            custom_buttons=buttons,  # type: ignore
            combined_page_indicator_view=self._stop_button_and_page_switcher_view,
        )

        # stop_button -> STOP
        # page_indicator_button -> PAGE_INDICATOR
        # ...
        self.__custom_id_to_original: dict[str, ButtonKey] = {}

        self._custom_buttons: dict[str, PaginatorButton] = {}
        if custom_buttons:
            self.custom_buttons = custom_buttons

        self.always_show_stop_button: bool = always_show_stop_button

        if style_if_clickable is discord.utils.MISSING:
            self._style_if_clickable = discord.ButtonStyle.green
        elif style_if_clickable is not None:
            if not isinstance(style_if_clickable, discord.ButtonStyle):
                raise TypeError("style_if_clickable must be a discord.ButtonStyle or None.")
            self._style_if_clickable = style_if_clickable
        else:
            self._style_if_clickable = None

        self._sort_on: Optional[SortButtonsOn] = None
        if isinstance(sort_buttons, bool) and sort_buttons is True:
            self._sort_on = SortButtonsOn.POSITION
        elif isinstance(sort_buttons, str):
            try:
                self._sort_on = SortButtonsOn(sort_buttons)
            except ValueError:
                raise ValueError("sort_buttons must one of the following: 'position', 'label', 'custom_id'.")
        elif isinstance(sort_buttons, SortButtonsOn):
            self._sort_on = sort_buttons
        else:
            raise TypeError("sort_buttons must be a bool, str, or SortButtonOn enum.")

        self.__handle_overrides()
        self.__handle_custom_buttons()
        self.__handle_customized_buttons()
        self.__add_buttons()

    def __handle_always_show_stop_button(self) -> None:
        if not self.always_show_stop_button:
            return

        stop_button_key = ButtonKey.STOP
        stop_button = self._buttons.get(stop_button_key)

        if not stop_button:
            raise ValueError("STOP button is required if always_show_stop_button is True.")

        stop_button.custom_id = f"{stop_button_key.value}_button"
        setattr(self, stop_button_key.value, stop_button)
        self.add_item(stop_button)

    async def _handle_modal(self, interaction: discord.Interaction[Any]) -> Optional[int]:
        modal = ChooseNumber(self)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return (int(modal.number_input.value) - 1) if modal.number_input.value else None

    def add_custom_buttons(self, *buttons: PaginatorButton, reload_all: bool = True) -> None:
        """Add a custom button to the paginator.

        If a button with the same custom id already exists, it will be overwritten.

        .. versionadded:: 0.3.0

        Parameters
        ----------
        buttons: :class:`PaginatorButton`
            The custom buttons to add to the paginator.
            This can be a single button or multiple buttons.
            .. code-block:: python3
                :linenos:

                await <paginator>.add_custom_buttons(
                    PaginatorButton(label="Custom Button 1"),
                    PaginatorButton(label="Custom Button 2"),
                    ...
                )

        reload_all: :class:`bool`
            Whether to reload all buttons in the paginator. Defaults to ``True``.
            Not sure why you would want to set this to ``False`` but it's there if you need it.
        """
        for button in buttons:
            button.custom_id = button.custom_id or os.urandom(16).hex()
            button._is_custom = True
            self._custom_buttons[button.custom_id] = button
        if reload_all:
            self.__add_buttons()

    def remove_custom_buttons(self, *custom_ids: str, reload_all: bool = True) -> None:
        """Remove a custom button from the paginator.

        If no button matches the custom id, nothing will happen.

        .. versionadded:: 0.3.0

        Parameters
        ----------
        custom_id: :class:`str`
            The custom ids of the buttons to remove.
        reload_all: :class:`bool`
            Whether to reload all buttons in the paginator. Defaults to ``True``.
            Not sure why you would want to set this to ``False`` but it's there if you need it.
        """
        for custom_id in custom_ids:
            self._custom_buttons.pop(custom_id, None)
        if reload_all:
            self.__add_buttons()

    def remove_all_custom_buttons(self, *, reload_all: bool = True) -> None:
        """Removes all custom buttons from the paginator.

        .. versionadded:: 0.3.0

        Parameters
        ----------
        reload_all: :class:`bool`
            Whether to reload all buttons in the paginator. Defaults to ``True``.
            Not sure why you would want to set this to ``False`` but it's there if you need it.
        """
        self._custom_buttons.clear()
        if reload_all:
            self.__add_buttons()

    def __add_buttons(self) -> None:
        self.clear_items()
        if not self.max_pages > 1:
            if self.always_show_stop_button:
                self.__handle_always_show_stop_button()
                return

            self.stop()
            return

        buttons = self._buttons | self._custom_buttons
        if self._sort_on is not None:
            buttons = self._sort_on._do_sort(buttons)

        for key, button in buttons.items():  # type: ignore
            if not button:
                continue

            if button._is_custom:
                self.add_item(button)
                continue

            button = button._copy()
            key: ButtonKey = key

            custom_id = f"{key.value.lower()}_button"

            if custom_id == "page_indicator_button":
                button.label = self.page_string
                if self.max_pages <= 2:
                    button.disabled = True

            if custom_id in ("first_button", "last_button"):
                if self.max_pages <= 2:
                    continue

                label = button.label or ""
                if custom_id == "first_button":
                    button.label = f"1 {label}"
                else:
                    button.label = f"{label} {self.max_pages}"

            if self._stop_button_and_page_switcher_view and custom_id == "stop_button":
                continue

            setattr(self, key.value, button)
            button.custom_id = custom_id
            self.__custom_id_to_original[custom_id] = key
            self.add_item(button)

        if self._stop_button_and_page_switcher_view:
            self._stop_button_and_page_switcher_view._add_buttons(self)
            self.PAGE_INDICATOR.custom_id = "switch_page"  # type: ignore

        self._update_buttons_state()

    def _update_buttons_state(self) -> None:
        for button in self.children:
            # type checker
            if not isinstance(button, PaginatorButton):
                continue

            if button._is_custom:
                continue

            custom_id: Optional[str] = button.custom_id
            # type checker
            if not custom_id:
                raise ValueError("Something went wrong... button.custom_id is None")

            if custom_id in ("page_indicator_button", "stop_button"):
                if button.custom_id == "page_indicator_button":
                    button.label = self.page_string
                continue

            if custom_id in ("right_button", "last_button"):
                button.disabled = not self.loop_pages and (self._current_page >= self.max_pages - 1)
            elif custom_id in ("left_button", "first_button"):
                button.disabled = not self.loop_pages and (self._current_page <= 0)

            original_button = self._buttons.get(self.__custom_id_to_original.get(custom_id))  # type: ignore # dwai

            if custom_id in ("first_button", "last_button"):
                if self.max_pages <= 2:
                    button.disabled = True

                if original_button:
                    label = original_button.label or ""
                    if custom_id == "first_button":
                        button.label = f"1 {label}"
                    else:
                        button.label = f"{label} {self.max_pages}"

            if self._style_if_clickable is not None:
                if not button.disabled:
                    button.style = self._style_if_clickable
                else:
                    button.style = original_button.style if original_button else discord.ButtonStyle.secondary

    async def _call_button(
        self,
        interaction: discord.Interaction[Any],
        button: PaginatorButton,
    ) -> Any:
        # type checker
        view: Optional[Union[ButtonPaginator[Any], PageSwitcherAndStopButtonView]] = button.view
        if not view:
            raise ValueError(
                "Something went wrong... there is no view attached to the button. Please report this to the developer."
            )

        if button.custom_id == "stop_button":
            await self.stop_paginator(interaction)
            return

        new_page: int = self.current_page

        if button.custom_id == "right_button":
            new_page += 1
        elif button.custom_id == "left_button":
            new_page -= 1
        elif button.custom_id == "first_button":
            new_page = 0
        elif button.custom_id == "last_button":
            new_page = self.max_pages - 1
        elif button.custom_id == "page_indicator_button":
            modal_value = await self._handle_modal(interaction)
            if modal_value is not None:
                new_page = modal_value

        await self.switch_page(interaction, new_page)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def custom_buttons(self) -> list[PaginatorButton]:
        """List[:class:`PaginatorButton`]: The custom buttons of the paginator.

        .. versionadded:: 0.3.0
        """
        return list(self._custom_buttons.values())

    @custom_buttons.setter
    def custom_buttons(self, value: list[PaginatorButton]) -> None:
        """Set the custom buttons of the paginator.

        This will replace all custom buttons with the given list.

        .. versionadded:: 0.3.0

        Parameters
        ----------
        value: List[:class:`PaginatorButton`]
            A list of custom buttons to set.
        """
        if not isinstance(value, list) or all(not isinstance(button, PaginatorButton) for button in value):
            raise TypeError("custom_buttons must be a list of PaginatorButton instances.")

        self.remove_all_custom_buttons(reload_all=False)
        self.add_custom_buttons(*value)

    @current_page.setter
    def current_page(self, value: int) -> None:
        self._current_page = value
        self._update_buttons_state()

    def _send(self, *args: Any, **kwargs: Any) -> Any:
        self._update_buttons_state()
        return super()._send(*args, **kwargs)


def callback_for(
    key: ValidButtonKeys,
    *,
    override: bool = False,
    **kwargs: Unpack[OriginalButtonKwargs],
) -> Callable[[DecoFunc], DecoFunc]:
    """Customize a default button in the paginator and set a callback for it.

    The function that this decorator is applied to will be called when the button is pressed
    after the internal paginator logic has been handled unless the override parameter is set to True.

    The function must take two arguments:
    - The first argument is the paginator instance (self).
    - The second argument is the :class:`discord.Interaction` object.
    And must be a coroutine.

    .. versionadded:: 0.3.0

    Parameters
    ----------
    key: :class:`str`
        The key to set the callback for. This MUST be one of the following:
        ``"LEFT"``, ``"RIGHT"``, ``"UP"``, ``"DOWN"``, ``"FIRST"``, ``"LAST"``, ``"STOP"``, ``"PAGE_INDICATOR"``
        or a :class:`ButtonKey`.
    override: :class:`bool`
        Whether to override the internal/default behavior of the button. Defaults to ``False``.
        If set to ``True``, the internal/default behavior of the button will be ignored.
    **kwargs: :class:`dict`
        The same kwargs as :class:`discord.ui.Button` to customize the button.
    """

    def decorator(func: DecoFunc) -> DecoFunc:
        if not utils._check_parameters_amount(func, (2,)):
            raise TypeError("The function must take exactly 2 arguments: paginator (self), interaction")

        button_key = ButtonKey._convert(key)
        if button_key is None:
            raise ValueError(f"Invalid key. Must be one of the following: {', '.join(map(str, ButtonKey))}")

        metadata = {button_key: {"button": kwargs, "callback": func, "override": override}}
        try:
            func.__dpy_paginator_button_overrides__.update(metadata)  # type: ignore
        except AttributeError:
            func.__dpy_paginator_button_overrides__ = metadata  # type: ignore

        return func

    return decorator


def custom_button(
    *,
    label: Optional[str] = None,
    emoji: Optional[Union[str, discord.PartialEmoji, discord.Emoji]] = None,
    style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    disabled: bool = False,
    row: Optional[int] = 0,
    custom_id: Optional[str] = None,
    position: Optional[int] = None,
) -> Callable[[DecoFunc], DecoFunc]:
    """Add a custom button to the paginator.

    This decorator can be used to add a custom button to the paginator.
    The function that this decorator is applied to will be called when the button is pressed.

    It takes the same parameters as :class:`discord.ui.Button` with the addition of ``position``.

    The function must take two arguments:
    - The first argument is the paginator instance (self).
    - The second argument is the :class:`discord.Interaction` object.
    And must be a coroutine.

    .. versionadded:: 0.3.0

    Parameters
    ----------
    position: :class:`int`
        The position of the button in the paginator. Defaults to ``0``.
    """

    def decorator(func: DecoFunc) -> DecoFunc:
        if not utils._check_parameters_amount(func, (2,)):
            raise TypeError("The function must take exactly 2 arguments: paginator (self), interaction")

        func.__dpy_paginator_custom_button__kws__ = {  # type: ignore
            "label": label,
            "emoji": emoji,
            "style": style,
            "disabled": disabled,
            "row": row,
            "custom_id": custom_id,
            "position": position,
        }

        return func

    return decorator


def customise_button(
    key: ValidButtonKeys,
    /,
    *,
    label: Optional[str] = discord.utils.MISSING,
    emoji: Optional[Union[str, discord.PartialEmoji, discord.Emoji]] = discord.utils.MISSING,
    style: discord.ButtonStyle = discord.utils.MISSING,
    disabled: bool = discord.utils.MISSING,
    row: Optional[int] = discord.utils.MISSING,
    position: Optional[int] = discord.utils.MISSING,
) -> Callable[[DecoCls], DecoCls]:
    """Decorator to customize a default button in the paginator without changing the callback.

    This must be used on top of a subclass of :class:`ButtonPaginator`.
    It takes the same parameters as :class:`discord.ui.Button` with the addition of ``key`` and ``position``.

    .. versionadded:: 0.3.0

    Parameters
    ----------
    key: :class:`str`
        The key the default button to customize. This MUST be one of the following:
        ``"LEFT"``, ``"RIGHT"``, ``"UP"``, ``"DOWN"``, ``"FIRST"``, ``"LAST"``, ``"STOP"``, ``"PAGE_INDICATOR"``
        or a :class:`ButtonKey`.
    position: :class:`int`
        The position of the button in the paginator. Defaults to ``0``.

    Examples
    -------

    .. code-block:: python3
        :linenos:

        from discord.ext.paginators import ButtonPaginator, customise_button

        @customise_button("FIRST", label="Go to first page", position=1)
        class MyPaginator(ButtonPaginator):
            ...

    Raises
    ------
    ValueError
        The key is not one of the valid keys.
    TypeError
        The decorator is not used on a subclass of :class:`ButtonPaginator`.
    """

    def decorator(cls: DecoCls) -> DecoCls:
        button_key = ButtonKey._convert(key)
        if button_key is None:
            raise ValueError(f"Invalid key. Must be one of the following: {', '.join(map(str, ButtonKey))}")

        if not issubclass(cls, ButtonPaginator):
            raise TypeError("This decorator can only be used on ButtonPaginator subclasses.")

        data = {}
        if label is not discord.utils.MISSING:
            data["label"] = label
        if emoji is not discord.utils.MISSING:
            data["emoji"] = emoji
        if style is not discord.utils.MISSING:
            data["style"] = style
        if disabled is not discord.utils.MISSING:
            data["disabled"] = disabled
        if row is not discord.utils.MISSING:
            data["row"] = row
        if position is not discord.utils.MISSING:
            data["position"] = position

        kwrgs = {key: data}  # type: ignore
        try:
            cls.__customize_buttons__.update(kwrgs)  # type: ignore
        except AttributeError:
            cls.__customize_buttons__ = kwrgs  # type: ignore

        return cls  # type: ignore

    return decorator
