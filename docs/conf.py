# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import date
import re


project = "discord-py-paginators"

# source:
# https://github.com/Rapptz/discord.py/blob/61eddfcb189f11a293011d43b09fe4ec52641dd2/docs/conf.py#L95C1-L100C18
version = "0.0.0"
author = "Soheab_"
try:
    with open("../discord/ext/paginators/__init__.py") as f:
        read = f.read()
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', read, re.MULTILINE).group(1)  # type: ignore
        author = re.search(r'^__author__\s*=\s*[\'"]([^\'"]*)[\'"]', read, re.MULTILINE).group(1)  # type: ignore
except Exception:
    pass

release = version
author = author

current_year = date.today().year
copyright = f"{current_year}, {author}"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))


extensions = [
    "sphinx.ext.viewcode",  # https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
    "sphinx.ext.autodoc",  # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    "sphinx.ext.napoleon",  # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
    "sphinx_autodoc_typehints",  # https://github.com/tox-dev/sphinx-autodoc-typehints
    "sphinx.ext.intersphinx",  # https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
    "sphinx_toolbox.more_autodoc.typevars",  # https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typevars.html
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]


# autodoc
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#
autodoc_typehints_format = "short"
autodoc_typehints = "both"
autodoc_typehints_description_target = "all"
autodoc_type_aliases = {
    "discord.ext.paginators._types.PageT": "Any",
    "PageT": "Any",
}
autodoc_mock_imports = ["typing"]


# sphinx.ext.napoleon
napoleon_google_docstring = False
napoleon_use_rtype = False

# sphinx_autodoc_typehints
always_document_param_types = True
typehints_document_rtype = False
typehints_defaults = "braces"
simplify_optional_unions = False

# sphinx_toolbox.more_autodoc.typevars
all_typevars = True

# Custom RST roles
rst_prolog = """
.. role:: param
   :class: param-role
"""

# intersphinx
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aio": ("https://docs.aiohttp.org/en/stable/", None),
    "discord": ("https://discordpy.readthedocs.io/en/latest/", None),
    "discord.ext.modal_paginator": ("https://discord-ext-modal-paginator.readthedocs.io/", None),
}

# ??
nitpicky = True
nitpick_ignore = [
    ("py:class", "discord.ext.paginators._types.PageT"),
    ("py:obj", "discord.ext.paginators._types.PageT"),
    ("py:class", "discord.ext.paginator.base_paginator.BaseClassPaginator"),
    ("py:class", "PageSwitcherAndStopButtonView"),
    ("py:class", "ButtonPaginator[Any]"),
    ("py:class", "typing.Unpack"),
    ("py:class", "discord.ext.paginators.button_paginator.PageSwitcherAndStopButtonView"),
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
