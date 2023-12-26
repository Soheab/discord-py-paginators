.. discord-py-paginators documentation master file, created by
   sphinx-quickstart on Tue Dec 26 17:07:44 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to discord-py-paginators's documentation!
=================================================
Extension for discord.py that provides various paginators.

Installation
============= 

Stable
-------

.. code-block:: bash

   python -m pip install discord-py-paginators

Dev
----
.. note::
   This requires `git <https://git-scm.com/>`_ to be installed on your system.

.. code-block:: bash	
   
      python -m pip install -U "discord-py-paginators @ git+https://github.com/Soheab/discord-py-paginators"


Usage
======
.. code-block:: python

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


Examples
=========
Examples can be found in the `examples directory <https://github.com/Soheab/discord-py-paginators/tree/main/examples>`_.

Links
======
- `Documentation <https://discord-py-paginators.readthedocs.io/en/latest/>`_
- `Source code <https://github.com/Soheab/discord-py-paginators>`_
- `Discord server <https://discord.gg/yCzcfju>`_


Contact
========
Send a DM on discord at `Soheab_`, join the ``discord server`` or ping me in the `discord.py server <https://discord.gg/dpy>`_.