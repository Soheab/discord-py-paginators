# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'discord-py-paginators'
copyright = '2023, Soheab_'
author = 'Soheab_'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))


extensions = [
    'sphinx.ext.viewcode',  # https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
    'sphinx.ext.autodoc',  # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    'sphinx.ext.napoleon',  # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
    'sphinx_autodoc_typehints',  # https://github.com/tox-dev/sphinx-autodoc-typehints
    "sphinx.ext.intersphinx",  # https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
    'sphinx_toolbox.more_autodoc.typevars',  # https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typevars.html
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']


# sphinx.ext.napoleon
napoleon_google_docstring = False
napoleon_use_rtype = False

# sphinx_autodoc_typehints
always_document_param_types = True
typehints_document_rtype = False
typehints_defaults = 'braces'
simplify_optional_unions = False

# sphinx_toolbox.more_autodoc.typevars
all_typevars = True

# intersphinx 
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
intersphinx_mapping = {
    "py": ("https://docs.python.org/3", None),
    "aio": ("https://docs.aiohttp.org/en/stable/", None),
    "discord": ("https://discordpy.readthedocs.io/en/latest/", None),
    "discord.ext.modal_paginator": ("https://discord-ext-modal-paginator.readthedocs.io/", None),
}

# ??
nitpicky = True
nitpick_ignore = [
    ("py:class", "typing_extensions.Self"),
    ("py:class", "typing.Self"),
    ("py:class", "typing.Unpack"),
    ("py:class", "typing_extensions.Unpack"),
    ("py:class", "ButtonPaginator[Any]"),
    # ????? idk about these, these are from discord.py
    # fixes:
    # <unknown>:1: WARNING: py:data reference target not found: typing.Union`[:py:class:`~discord.emoji.Emoji
    ("py:data", "typing.Union`[:py:class:`~discord.emoji.Emoji"),
    # <unknown>:1: WARNING: py:class reference target not found: discord.enums.ButtonStyle
    ("py:class", "discord.enums.ButtonStyle"),
]

# https://pradyunsg.me/furo/customisation/announcement/
html_theme_options = {
    "announcement": (
        "<b>In Developement</b> Please note that this extension is still in developement. "
        "If you find any bugs, please report them om the <a href='https://github.com/Soheab/discord-py-paginators/issues'>GitHub repository</a>."
    ),
}