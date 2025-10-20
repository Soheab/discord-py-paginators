# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import date
from pathlib import Path
import re


project = "discord-py-paginators"

# source:
# https://github.com/Rapptz/discord.py/blob/61eddfcb189f11a293011d43b09fe4ec52641dd2/docs/conf.py#L95C1-L100C18
version = "1.0.0a"
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

import sys


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, str(Path('..').resolve()))


extensions = [
    "sphinx.ext.viewcode",  # https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
    "sphinx.ext.napoleon",  # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
    "sphinx.ext.autodoc",  # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
   # "sphinx_autodoc_typehints",  # https://github.com/tox-dev/sphinx-autodoc-typehints
    "sphinx.ext.intersphinx",  # https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
   # "sphinx_toolbox.more_autodoc.typevars",  # https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typevars.html
    "sphinx.ext.duration",  # https://www.sphinx-doc.org/en/master/usage/extensions/duration.html#module-sphinx.ext.duration
   # "numpydoc", # https://numpydoc.readthedocs.io/en/latest/install.html
    "sphinx_last_updated_by_git",  # https://pypi.org/project/sphinx-last-updated-by-git
]


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
requires_sphinx = ">=8.2.3"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
# full credits to scarlet.cafe aka Devon in the discord.py server
# source: https://canary.discord.com/channels/336642139381301249/336642776609456130/581468512065683467
html_favicon = "_static/dpylogo.svg"
html_logo = "_static/dpylogo.svg"

# autodoc
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#
autodoc_typehints_format = "short"
autodoc_typehints = "description"
autodoc_use_type_comments  = False
autodoc_inherit_docstrings = False

autodoc_member_order = "alphabetical"
autodoc_default_options = {
    "members": True,
}

autodoc_type_aliases = {
    "PageT": ":obj:`discord.ext.paginators._types.BoundPage` | :obj:`discord.ext.paginators._types.BoundV2Page`",
}


always_document_param_types = False
typehints_document_rtype = False


# sphinx.ext.napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = False
napoleon_include_special_with_doc = False
napoleon_use_param = False
napoleon_use_rtype = False


# sphinx_autodoc_typehints
always_document_param_types = True
typehints_document_rtype = False
typehints_defaults = None
simplify_optional_unions = False


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
}

# ??
nitpicky = True
nitpick_ignore = [

]

# https://pradyunsg.me/furo/customisation/announcement/
# Furo theme options
# https://pradyunsg.me/furo/customisation/
# https://pradyunsg.me/furo/customisation/announcement/
# Furo theme options
# https://pradyunsg.me/furo/customisation/
html_theme_options = {
    "announcement": (
        "<b>In Development</b> Please note that this extension is still in development. "
        "If you find any bugs, please report them on the <a href='https://github.com/Soheab/discord-py-paginators/issues'>GitHub repository</a>."
    ),
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/Soheab/discord-py-paginators",
            "html": (
                "<svg stroke='currentColor' fill='currentColor' stroke-width='0' viewBox='0 0 16 16'>"
                "<path fill-rule='evenodd' d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z'></path>"
                "</svg>"
            ),
            "class": "",
        },
    ],

}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-python_use_unqualified_type_names
python_use_unqualified_type_names = True

