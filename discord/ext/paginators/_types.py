from typing import TYPE_CHECKING, Any, Union, TypeVar

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from typing_extensions import TypeVar
    BotT = TypeVar('BotT', bound=commands.Bot, covariant=True, default=commands.Bot)
    ClientT = TypeVar('ClientT', bound=discord.Client, covariant=True, default=discord.Client) 
else:
    ClientT = TypeVar('ClientT', bound=discord.Client, covariant=True)  # type: ignore
    BotT = TypeVar('BotT', bound=commands.Bot, covariant=True)

InteractionT = discord.Interaction[ClientT]
ContextT = commands.Context[BotT] 

PossiblePage = Union[str, discord.Embed, discord.File, list[Union[discord.Embed, discord.File, Any]], dict[str, Any]]
PossibleMessage = Union[discord.InteractionMessage, discord.Message, discord.WebhookMessage]

Page = TypeVar("Page", bound=PossiblePage, covariant=True)
CTI = TypeVar("CTI", InteractionT, ContextT, None, covariant=True)