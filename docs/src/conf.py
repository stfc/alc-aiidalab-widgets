# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../../src/"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "alc-aiidalab-widgets"
copyright = "2025, Ada Lovelace Centre (STFC)"
author = "Dr. Benjamin T. Speake"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.apidoc",
]

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = ".rst"
master_doc = "index"
html_logo = ""

# -- Options for sphinx.ext.apidoc --------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/apidoc.html
#
# Automatically (re)generates the full API reference from the package's
# docstrings on every build, rather than requiring hand-written autodoc
# directives for every module/class.

apidoc_modules = [
    {
        "path": "../../src/alc_aiidalab_widgets",
        "destination": "api",
        "separate_modules": True,
        "module_first": True,
    },
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "piccolo_theme"
html_static_path = ["_static"]
