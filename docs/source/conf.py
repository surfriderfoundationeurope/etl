# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import re
import sys
sys.path.insert(0, os.path.relpath('..'))

# -- Project information -----------------------------------------------------

project = 'Surfrider ETL'
copyright = '2020, Clément Leroux, Raphaël Courivaud, Raphaëlle Bertrand-Lalo'
author = 'Clément Leroux, Raphaël Courivaud, Raphaëlle Bertrand-Lalo'


# The full version, including alpha/beta/rc tags
try:
    with open('../../etl/__init__.py') as f:
        release = re.search(r'^__version__\s*=\s*\'(.*)\'', f.read(), re.M).group(1)
except:
    release = '0.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',  # note: this has to go after napoleon
    'sphinx.ext.intersphinx',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

autoclass_content = 'both'  # add class level and __init__ documentation


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
# napoleon_include_init_with_doc = True  # enable this when implemented in Napoleon, instead of autoclass_content = 'both'


# intersphinx mappings
intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3',
        None
    ),
    'numpy': (
        'https://docs.scipy.org/doc/numpy',
        None
    ),
    'scipy': (
        'https://docs.scipy.org/doc/scipy/reference',
        None
    ),
    'pandas': (
        'https://pandas.pydata.org/pandas-docs/stable',
        None,
    ),
    'click': (
        'https://click.palletsprojects.com/en/7.x',
        None,
    )
}

