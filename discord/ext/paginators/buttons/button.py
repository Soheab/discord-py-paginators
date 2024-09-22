from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, Optional, TypeVar, Union

import discord

if TYPE_CHECKING:
    from typing_extensions import Never, Unpack
    from .paginator import ButtonPaginator, PageSwitcherAndStopButtonView
    from ._types import OriginalButtonKwargsWithPosition, OriginalButtonKwargs
else:
    T = TypeVar("T")

    class ButtonPaginator(Generic[T]): ...

    class PageSwitcherAndStopButtonView: ...

    OriginalButtonKwargsWithPosition = OriginalButtonKwargs = dict[str, Any]
    Never = Unpack = Any


__all__ = ("PaginatorButton", "ButtonKey")


class ButtonKey(discord.Enum):
    """An enum that represents the keys for the default buttons in the paginator.
    
    .. versionadded:: 0.3.0
    """	
    FIRST = "FIRST"
    """The key for the first button."""
    LEFT = "LEFT"
    """The key for the left button."""
    PAGE_INDICATOR = "PAGE_INDICATOR"
    """The key for the page indicator button."""
    STOP = "STOP"
    """The key for the stop button."""
    RIGHT = "RIGHT"
    """The key for the right button."""
    LAST = "LAST"
    """The key for the last button."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def _convert(cls, value: Union[str, ButtonKey]) -> Optional[ButtonKey]:
        if isinstance(value, ButtonKey):
            return value
        
        try:
            return cls(value.upper())
        except ValueError:
            return None


class PaginatorButton(discord.ui.Button[ButtonPaginator[Any]]):
    """Represents a button for the button paginator.

    This class has a few parameters that differ from the base button.
    This can can be passed to the ``buttons`` parameter in :class:`.ButtonPaginator`
    to customize the default buttons.

    You can also subclass this button and override the :meth:`callback` method.
    Your callback will be called after the internal callback is called
    unless ``override_callback`` is set to ``True``, in which case the internal
    callback will be ignored.

    See other parameters on :class:`discord.ui.Button`.

    Parameters
    ----------
    position: Optional[:class:`int`]
        The position of the button. Defaults to ``None``.
        If not specified, the button will be placed in the order they were added
        or whatever order discord.py adds them in.

        .. note::
            The position is 0-indexed and not guaranteed to be accurate.
    override_callback: :class:`bool`
        Whether to override the internal callback with the your callback.
    """

    view: ButtonPaginator[Any]  # type: ignore # it's fine, we're overriding the type

    def __init__(
        self,
        *,
        position: Optional[int] = None,
        override_callback: bool = False,
        **kwargs: Unpack[OriginalButtonKwargs],
    ) -> None:
        self._original_kwargs: OriginalButtonKwargsWithPosition = {
            "emoji": kwargs.get("emoji"),
            "label": kwargs.get("label"),
            "custom_id": kwargs.get("custom_id"),
            "style": kwargs.get("style", discord.ButtonStyle.secondary),
            "row": kwargs.get("row"),
            "disabled": kwargs.get("disabled", False),
        }
        super().__init__(**self._original_kwargs)  # type: ignore # it's fine
        self._original_kwargs["position"] = position  # type: ignore

        self.position: Optional[int] = position
        self._override_callback: bool = override_callback

        self.__is_converted_from_ui_button: bool = False
        self._is_custom: bool = False

    def __repr__(self) -> str:
        return f"<PaginatorButton label={self.label!r} style={self.style!r} position={self.position}>"

    def _copy(self, **kwargs: Unpack[OriginalButtonKwargsWithPosition]) -> PaginatorButton:
        """Returns a copy of the button using the original kwargs."""
        # not worth to copy anything since we converted it to a PaginatorButton already
        if self.__is_converted_from_ui_button:
            return self

        new_kwargs = self._original_kwargs.copy() | kwargs
        inst = PaginatorButton(**new_kwargs)
        inst._override_callback = self._override_callback
        inst.__is_converted_from_ui_button = self.__is_converted_from_ui_button
        inst.position = self.position
        inst._is_custom = self._is_custom
        if isinstance(self.callback, _CallbackWrapper):
            inst.callback = self.callback._copy(inst)
        return inst

    @classmethod
    def _to_self(cls, button: discord.ui.Button[Any]) -> PaginatorButton:
        if type(button) is cls:
            return button._copy()

        if not isinstance(button, discord.ui.Button):
            raise TypeError(f"Expected discord.ui.Button, got {button.__class__.__name__}")

        inst = cls(
            emoji=button.emoji,
            label=button.label,
            style=button.style,
            disabled=button.disabled,
            row=button.row,
            custom_id=button.custom_id,
        )
        inst.__is_converted_from_ui_button = True
        inst.callback = button.callback
        return inst


def _gen_default_button_doc(button: PaginatorButton) -> str:
    """Generates the docstring for the default buttons for the docs.

    Basically only shows the parameters that were set for the button.
    """

    def format_value(value: Any) -> str:
        """Prettifies the value for the end docstring.

        This is used to show the value in a more readable format.
        E,g: ButtonStyle.danger -> discord.ButtonStyle.danger
        """
        if isinstance(value, (bool, str, int, float, type(None))):
            return repr(value)
        elif isinstance(value, discord.ButtonStyle):
            return f"discord.ButtonStyle.{value.name}"
        elif isinstance(value, (discord.PartialEmoji, discord.Emoji)):
            return repr(str(value))

        return repr(value) or str(value)

    params = ", ".join(f"{key}={format_value(value)}" for key, value in button._original_kwargs.items() if value is not None)
    return f"PaginatorButton({params})"


# just for the pretty repr
class __DefaultButtonsMeta(type):
    _BUTTONS: dict[ButtonKey, PaginatorButton]

    def __repr__(cls) -> str:
        values = [f"{key}={value.__doc__}" for key, value in cls._BUTTONS.items()]
        return f"{cls.__name__}({', '.join(values)})"


class _CallbackWrapper:
    def __init__(
        self,
        view: Union[ButtonPaginator[Any], PageSwitcherAndStopButtonView],
        button: PaginatorButton,
        original_callback: Callable[[discord.Interaction[Any]], Any],
    ) -> None:
        self.__view: Union[ButtonPaginator[Any], PageSwitcherAndStopButtonView] = view
        self.__button: PaginatorButton = button
        self._original_callback = original_callback
        self._is_override: bool = False

    def _copy(self, button: PaginatorButton, is_override: bool | None = None) -> _CallbackWrapper:
        inst = _CallbackWrapper(self.__view, button, self._original_callback)
        inst._is_override = is_override or self._is_override
        inst._original_callback = self._original_callback
        return inst

    async def __call__(self, interaction: discord.Interaction[Any]) -> Any:
        # shouldn't have reached this anyways
        if self.__button._override_callback:
            if self._is_override:
                return await self._original_callback(self.__view, interaction)  # type: ignore

            await self._original_callback(interaction)
            return

        await self.__view._call_button(interaction, self.__button)
        if self._is_override:
            await self._original_callback(self.__view, interaction)  # type: ignore
        else:
            await self._original_callback(interaction)


class DefaultButtons(metaclass=__DefaultButtonsMeta):
    """A class that contains the default buttons for the paginator.

    These buttons are used in :class:`.ButtonPaginator` if no custom button is provided for
    the specific action.

    This is not meant for users to access, but rather for documentation purposes.

    .. versionadded:: 0.3.0

    Attributes
    ----------
    FIRST: :class:`PaginatorButton`
        The button that goes to the first page.
    LEFT: :class:`PaginatorButton`
        The button that goes to the previous page.
    PAGE_INDICATOR: :class:`PaginatorButton`
        The button that shows the current page and the total pages.
    RIGHT: :class:`PaginatorButton`
        The button that goes to the next page.
    LAST: :class:`PaginatorButton`
        The button that goes to the last page.
    STOP: :class:`PaginatorButton`
        The button that stops the paginator.
    """

    FIRST = PaginatorButton(label="First", position=0)
    LEFT = PaginatorButton(label="Left", position=1)
    PAGE_INDICATOR = PaginatorButton(label="Page N/A / N/A", position=2, disabled=False)
    RIGHT = PaginatorButton(label="Right", position=3)
    LAST = PaginatorButton(label="Last", position=4)
    STOP = PaginatorButton(label="Stop", style=discord.ButtonStyle.danger, position=5)

    _BUTTONS: dict[ButtonKey, PaginatorButton] = {
        ButtonKey.FIRST: FIRST,
        ButtonKey.LEFT: LEFT,
        ButtonKey.PAGE_INDICATOR: PAGE_INDICATOR,
        ButtonKey.RIGHT: RIGHT,
        ButtonKey.LAST: LAST,
        ButtonKey.STOP: STOP,
    }
    __slots__: tuple[()] = ()

    @staticmethod
    def _set_button_callback(
        view: Union[ButtonPaginator[Any], PageSwitcherAndStopButtonView], button: PaginatorButton
    ) -> None:
        if button._override_callback:
            return

        button.callback = _CallbackWrapper(view, button, button.callback)

    @classmethod
    def init(
        cls,
        paginator: ButtonPaginator[Any],
        *,
        custom_buttons: dict[Union[str, ButtonKey], Optional[discord.ui.Button[Any]]],
        combined_page_indicator_view: Optional[PageSwitcherAndStopButtonView] = None,
    ) -> Mapping[ButtonKey, Optional[PaginatorButton]]:
        buttons: dict[ButtonKey, Optional[discord.ui.Button[Any]]] = cls._BUTTONS.copy()  # type: ignore

        for button in cls._BUTTONS.values():
            button.__doc__ = _gen_default_button_doc(button)

        if custom_buttons:
            valid_keys = ", ".join(map(str, ButtonKey))
            error_message: str = (
                f"buttons must be a dictionary of keys: {valid_keys} and PaginatorButton or None "
                "to remove the button as the value. Or don't specify the kwarg to use the default buttons."
            )
            if not isinstance(custom_buttons, dict):
                raise TypeError(error_message)

            if any(not ButtonKey._convert(k) for k in custom_buttons):
                invalid_keys = ", ".join(str(k) for k in custom_buttons if not ButtonKey._convert(k))
                invalid_values = ", ".join(
                    f"{k}: {v}" for k, v in custom_buttons.items() if not isinstance(v, (discord.ui.Button, type(None)))
                )
                raise TypeError(f"{error_message}\nInvalid keys: {invalid_keys}\nInvalid values: {invalid_values}")

            buttons.update({ButtonKey._convert(k): v for k, v in custom_buttons.items()})  # type: ignore

        paginator_buttons = {key: PaginatorButton._to_self(button) if button else None for key, button in buttons.items()}
        for key, button in paginator_buttons.items():
            if button:
                if combined_page_indicator_view and key in (ButtonKey.STOP, ButtonKey.PAGE_INDICATOR):
                    cls._set_button_callback(combined_page_indicator_view, button)
                else:
                    cls._set_button_callback(paginator, button)

        return paginator_buttons

    def __new__(cls) -> Never:
        raise TypeError(  # why did you even try?
            f"{cls.__name__} is not meant to be instantiated."
            f" Use the class attributes to access the default buttons: {', '.join(map(str, cls._BUTTONS.keys()))}"
        )
