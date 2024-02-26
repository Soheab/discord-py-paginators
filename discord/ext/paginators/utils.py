from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union, Tuple

from collections.abc import Callable

import inspect

import discord

if TYPE_CHECKING:
    from discord.ext.commands import Bot


# kinda like discord's is_owner method on commands.Bot
# but then for Client too and without setting any attributes
# https://github.com/Rapptz/discord.py/blob/bd402b486cc12f0c1bf7377fd65f2fe0a8fabd73/discord/ext/commands/bot.py#L485-L535
async def _fetch_bot_owner_ids(client: Union[discord.Client, Bot]) -> set[int]:  # type: ignore # unused
    owner_ids: list[int] = []
    if owner_id_attr := getattr(client, "owner_id", None):
        owner_ids.append(owner_id_attr)
    if owner_ids_attr := getattr(client, "owner_ids", set[int]()):
        owner_ids.extend(owner_ids_attr)

    # support for team roles is added in dpy v2.4
    if discord.version_info >= (2, 4):
        team_class: Any = getattr(discord, "TeamMemberRole", None)
        if team_class:
            app: discord.AppInfo = client.application or await client.application_info()
            if app.team:
                owner_ids.extend(
                    m.id
                    for m in app.team.members
                    if m.role in (team_class.admin, team_class.developer) and hasattr(m, "role")  # type: ignore
                )
            else:
                owner_ids.append(app.owner.id)

    return set(owner_ids)


def _check_parameters_amount(func: Callable[..., Any], amounts: tuple[int, ...], /) -> bool:  # type: ignore # unused
    parameters = inspect.signature(func).parameters
    return len(parameters) in amounts


async def _call_and_ignore(  # type: ignore # unused
    functions: list[Callable[..., Any]],
    *args: Any,
    **kwargs: Any,
) -> Tuple[bool, Optional[Exception]]:
    if not functions:
        return True, None

    for function in functions[:-1]:
        try:
            await function(*args, **kwargs)
        except Exception:
            pass
        else:
            return True, None

    try:
        await functions[-1]()
    except Exception as e:
        return False, e
    
    return True, None
    
