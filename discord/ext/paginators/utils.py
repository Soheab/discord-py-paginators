from __future__ import annotations
from typing import TYPE_CHECKING, Any, Sequence

from collections.abc import Callable

import inspect
import io

import discord

if TYPE_CHECKING:
    from .views import View


# like discord's is_owner method on commands.Bot
# but then for Client too and without setting any attributes
# https://github.com/Rapptz/discord.py/blob/bd402b486cc12f0c1bf7377fd65f2fe0a8fabd73/discord/ext/commands/bot.py#L485-L535
async def __get_bot_owner_ids(client: discord.Client) -> set[int]:  # pyright: ignore[reportUnusedFunction]
    _owner_ids: list[int] = []
    if owner_id_attr := getattr(client, "owner_id", None):
        _owner_ids.append(owner_id_attr)
    if owner_ids_attr := getattr(client, "owner_ids", set[int]()):
        _owner_ids.extend(owner_ids_attr)

    app: discord.AppInfo = client.application or await client.application_info()
    if app.team:
        _owner_ids.extend(
            m.id for m in app.team.members if m.role in (discord.TeamMemberRole.admin, discord.TeamMemberRole.developer)
        )
    else:
        _owner_ids.append(app.owner.id)

    return set(_owner_ids)


def _check_parameters_amount(func: Callable[..., Any], amounts: tuple[int, ...], /) -> bool:  # type: ignore # unused
    parameters = inspect.signature(func).parameters
    return len(parameters) in amounts


async def _new_file(_file: discord.File | discord.Attachment, /) -> discord.File:  # type: ignore # unused
    """Constructs a new :class:`discord.File` with the same metadata but a new file pointer
    that can be used multiple times as discord.py closes it after it's sent once.

    Parameters
    ----------
    _file: :class:`discord.File` | :class:`discord.Attachment`
        The file to create a new file from.

    Returns
    -------
    :class:`discord.File`
        The new file.
    """
    file = await _file.to_file() if isinstance(_file, discord.Attachment) else _file
    file.reset()
    new_fp = io.BytesIO(file.fp.read())
    return discord.File(new_fp, filename=file.filename, spoiler=file.spoiler, description=file.description)


NON_CV2_ERROR = (
    "Cannot mix non-v2 component (or content) {thing} ({item}) with components_v2 (or other v2 components). Use a {instead} instead."
)


def _has_v2_components(pages: Sequence[Any]) -> bool:
    for page in pages:
        if isinstance(page, (list, tuple)):
            if _has_v2_components(page):  # pyright: ignore[reportUnknownArgumentType]
                return True
        elif isinstance(page, discord.ui.Item) and page._is_v2():
            return True
    return False


def _ensure_only_v2_components(pages: Sequence[Any]) -> None:
    """Validate that pages only contain v2-compatible components."""
    for page in pages:
        if isinstance(page, discord.Embed):
            msg = NON_CV2_ERROR.format(thing="Embed", item=page, instead="Container")
            raise TypeError(msg)
        elif isinstance(page, (discord.ui.Button, discord.ui.Select)):
            msg = NON_CV2_ERROR.format(thing=page.__class__.__name__, item=page, instead="ActionRow")  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            raise TypeError(msg)
        elif isinstance(page, (list, tuple)):
            _ensure_only_v2_components(page)  # pyright: ignore[reportUnknownArgumentType]


def _ensure_no_v2_components(pages: Sequence[Any]) -> None:
    """Validate that pages contain no v2 components."""
    for page in pages:
        if isinstance(page, (list, tuple)):
            _ensure_no_v2_components(page)  # type: ignore
        elif isinstance(page, discord.ui.Item) and page._is_v2():
            msg = (
                f"Cannot mix v2 component {page.__class__.__name__} ({page}) with non-v2 components. "  # pyright: ignore[reportUnknownMemberType]
                "Either remove it, or set components_v2 to True/None."
            )
            raise TypeError(msg)


def _check_cv2_and_pages(  # type: ignore # unused
    components_v2: bool | None, pages: Sequence[Any]
) -> None:
    print("components_v2 check utils:", components_v2)
    if components_v2 is True:
        _ensure_only_v2_components(pages)
    elif components_v2 is False:
        _ensure_no_v2_components(pages)
    elif components_v2 is None and _has_v2_components(pages):
        _ensure_only_v2_components(pages)
