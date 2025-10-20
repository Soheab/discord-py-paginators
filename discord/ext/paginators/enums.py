from __future__ import annotations
from enum import IntEnum


__all__ = (
    "AfterAction",
    "ButtonKey",
)


class AfterAction(IntEnum):
    """An enum that represents the action to take after the paginator stops or times out."""

    NOTHING = 0
    """Do nothing. This is the default."""
    DELETE_MESSAGE = 1
    """Delete the original message."""
    DISABLE_ITEMS = 2
    """Disable all interactive items."""
    CLEAR_ITEMS = 3
    """Clear all items from the view."""


class _KnownComponentIDs:
    FIRST_BUTTON: int = 10
    LEFT_BUTTON: int = 20
    PAGE_INDICATOR_BUTTON: int = 30
    RIGHT_BUTTON: int = 40
    LAST_BUTTON: int = 50
    STOP_BUTTON: int = 60

    CONTAINER: int = 70
    BUTTONS_CONTAINER: int = 80
    BUTTON_ACTION_ROW: int = 90
    BUTTON_ACTION_ROW2: int = 100

    @classmethod
    def from_key(cls, key: ButtonKey) -> int:
        key_to_id = {
            ButtonKey.FIRST: cls.FIRST_BUTTON,
            ButtonKey.LEFT: cls.LEFT_BUTTON,
            ButtonKey.RIGHT: cls.RIGHT_BUTTON,
            ButtonKey.LAST: cls.LAST_BUTTON,
            ButtonKey.STOP: cls.STOP_BUTTON,
            ButtonKey.PAGE_INDICATOR: cls.PAGE_INDICATOR_BUTTON,
        }
        return key_to_id[key]


class ButtonKey(IntEnum):
    FIRST = _KnownComponentIDs.FIRST_BUTTON
    LEFT = _KnownComponentIDs.LEFT_BUTTON
    RIGHT = _KnownComponentIDs.RIGHT_BUTTON
    LAST = _KnownComponentIDs.LAST_BUTTON
    STOP = _KnownComponentIDs.STOP_BUTTON
    PAGE_INDICATOR = _KnownComponentIDs.PAGE_INDICATOR_BUTTON

    @classmethod
    def from_id(cls, id: int) -> ButtonKey:
        return cls(id)
