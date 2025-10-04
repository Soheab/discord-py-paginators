from __future__ import annotations
from typing import Any, Union

from collections.abc import Callable

import inspect
import io

import discord


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


async def _new_file(_file: Union[discord.File, discord.Attachment], /) -> discord.File:  # type: ignore # unused
    """Constructs a new :class:`discord.File` with the same metadata but a new file pointer
    that can be used multiple times as discord.py closes it after it's sent once.

    Parameters
    ----------
    _file: Union[:class:`discord.File`, :class:`discord.Attachment`]
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
