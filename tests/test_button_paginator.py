from typing import TYPE_CHECKING, Any
import warnings
import discord
import pytest

# audioloop was deprecated at the time of writing this line
# 7 September 2024
warnings.filterwarnings("ignore", category=DeprecationWarning)

if TYPE_CHECKING:
    from ..discord.ext.paginators import ButtonPaginator, SelectOptionsPaginator, PaginatorButton, PaginatorOption
else:
    from discord.ext.paginators import ButtonPaginator, SelectOptionsPaginator, PaginatorButton, PaginatorOption


@pytest.fixture
def pages() -> list[Any]:
    return [1, "2", 3, [4, "5",], (7, "8", 9), 10]


@pytest.fixture
def custom_buttons() -> dict[str, Any]:
    return {
        "FIRST": None,
        "LEFT": None,
        "PAGE_INDICATOR": None,
        "RIGHT": None,
        "LAST": None,
        "STOP": None,
    }

@pytest.mark.asyncio
async def test_constructing( pages: list[Any]):
    ButtonPaginator(pages)
    SelectOptionsPaginator(pages)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "buttons",
    [  # type: ignore
        {
            "FIRST": None,
            "LEFT": discord.ui.Button(label="Left"),
            "RIGHT": discord.ui.Button(label="Right"),
            "LAST": discord.ui.Button(label="Last"),
            "STOp": discord.ui.Button(label="Stop"),
        },
        {
            "wrong_key": None,
            "FIRST": discord.ui.Button(label="First"),
            "LEFT": PaginatorButton(label="Left"),
        },
    ]
)
async def test_buttons( pages: list[Any], buttons: dict[str, Any]):
    with pytest.raises(TypeError):
        ButtonPaginator(pages, buttons=buttons)  # type: ignore

@pytest.mark.asyncio
async def test_required_button_when_always_show_stop_button_is_true(pages: list[Any]) -> None:
    buttons = {
        "STOP": None,
    }
    with pytest.raises(ValueError, match="STOP button is required if always_show_stop_button is True."):
        ButtonPaginator(pages[:1], always_show_stop_button=True, buttons=buttons)  # type: ignore


@pytest.mark.asyncio
async def test_buttons_must_be_dict(pages: list[Any]) -> None:
    with pytest.raises(TypeError, match=r".*buttons must be a dictionary.*"):
        ButtonPaginator(pages, buttons=1)  # type: ignore


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "buttons",
    [  # type: ignore
        {
            "STOP": None,
            "PAGE_INDICATOR": None,
        },
        {
            "PAGE_INDICATOR": None,
        },
        {
            "STOP": None,
        },
    ]
)
async def test_combine_switcher_and_stop_button_required_buttons(pages: list[Any], buttons) -> None:
    with pytest.raises(ValueError, match=".*STOP and PAGE_INDICATOR buttons are required.*"):
        ButtonPaginator(pages, combine_switcher_and_stop_button=True, buttons=buttons)
