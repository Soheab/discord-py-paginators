from typing import TYPE_CHECKING, Any
import warnings
import discord
import pytest

# audioloop was deprecated at the time of writing this line
# 7 September 2024
warnings.filterwarnings("ignore", category=DeprecationWarning)

if TYPE_CHECKING:
    from ..discord.ext.paginators import SelectOptionsPaginator, PaginatorOption
else:
    from discord.ext.paginators import SelectOptionsPaginator, PaginatorOption

@pytest.fixture
def pages() -> list[Any]:
    return [
        1,
        2,
        3,
        PaginatorOption("content"),
        [PaginatorOption("content"), PaginatorOption("content"), 2, "str"],
        ("content", PaginatorOption("content"), 3),
        ("content", 4, PaginatorOption("content"), 3),
        "str"
    ]


@pytest.mark.asyncio
async def test_constructing(pages: list[Any]):
    SelectOptionsPaginator(pages)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "select_pages",
    [
        ["content", (4, 5, 6), (7, [8, 9], 10)],
        [PaginatorOption("content"), [[PaginatorOption("content")]], [PaginatorOption("content"), 2], 3],
        [[PaginatorOption("content"), (2, ), 4]],
    ],
)
async def test_inner_inner_select_options_not_allowed(select_pages: list[Any]):
    with pytest.raises(ValueError, match=r".*Nested list/tuple as page is not allowed.*"):
        SelectOptionsPaginator(select_pages)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "select_pages",
    [
        [PaginatorOption("content"), discord.SelectOption(label="content"), 1, "content"],
        (discord.SelectOption(label="content"),),
        [[discord.SelectOption(label="content"), PaginatorOption("content")]],
    ],
)
async def test_selectoption_not_allowed_as_page(select_pages: list[Any]):
    with pytest.raises(TypeError, match=r".*A regular SelectOption is not supported.*"):
        SelectOptionsPaginator(select_pages)


@pytest.mark.asyncio
async def test_pages_is_a_list_list(pages: list[Any]):
    paginator = SelectOptionsPaginator(pages)

    assert all(isinstance(page, list) for page in paginator.pages), "All pages should be a list"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "select_pages",
    [
        [PaginatorOption("content")],
        (1,),
        ["content"],
    ],
)
async def test_pages_is_a_list_of_list_of_selectoption(select_pages: list[Any]):
    paginator = SelectOptionsPaginator(select_pages)

    assert all(
        all(type(inner_page) is PaginatorOption for inner_page in page) for page in paginator.pages
    ), "All pages should be a list of PaginatorOption"


@pytest.mark.asyncio
async def test_pages_are_valid(pages: list[Any]):
    print(pages)
    paginator = SelectOptionsPaginator(pages)

    for page in paginator.pages:
        if not isinstance(page, list):
            assert type(page) is PaginatorOption, "All pages should be a list of PaginatorOption"
        else:
            for option in page:  # type: ignore
                assert type(option) is PaginatorOption, "All pages should be a list of PaginatorOption"  # type: ignore
                assert option.label, "PaginatorOption should have a label"
                assert option.value, "PaginatorOption should have a value"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "select_pages",
    [
        ["str", "content", 1, PaginatorOption("content")],
        [PaginatorOption("content", value="bla"), [PaginatorOption("content", value="bla"), "content"]],
        [PaginatorOption("content", value="bla")],
    ],
)
async def test_unique_option_values(select_pages: list[Any]):
    paginator = SelectOptionsPaginator(select_pages)
    checked_values: list[str] = []

    for page in paginator.pages:
        for option in page:
            assert option.value not in checked_values, f"All option values should be unique."
            checked_values.append(option.value)
