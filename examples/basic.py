# Same as the readme.

import discord
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents(guilds=True, messages=True))

@bot.command()
async def paginate(ctx):
    list_with_many_items = list(range(100))
    paginator = ButtonPaginator(list_with_many_items, author_id=ctx.author.id)
    await paginator.send(ctx)
    # Enjoy!


bot.run("token")