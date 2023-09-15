from discord.ext import commands

import discord


bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents(messages=True, guilds=True))

@bot.event
async def setup_hook():
    try:
        await bot.load_extension("jishaku")
    except:
        import os
        os.system("python -m pip install jishaku")
        await bot.load_extension("jishaku")
        pass


bot.run("lol")