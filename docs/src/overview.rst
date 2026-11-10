Overview
========

``alc-aiidalab-widgets`` is a collection of reusable `ipywidgets
<https://ipywidgets.readthedocs.io/>`_-based components developed by the Ada
Lovelace Centre (ALC) at STFC. It is intended for use within `AiiDAlab
<https://www.aiidalab.net/>`_ apps, but, since it is built on top of
``ipywidgets`` and `traitlets <https://traitlets.readthedocs.io/>`_, the
widgets can be used in any Jupyter-based environment.

The package exists to avoid re-implementing the same pieces of UI (structure
viewers, code selectors, file upload/download helpers, status indicators,
data tables, ...) across every AiiDAlab plugin maintained by the ALC. Using
these shared widgets keeps the look and feel of ALC-managed apps consistent,
and means that improvements and bug fixes made in one place benefit every
app that depends on this package.

Design principles
------------------

- **Composable** - widgets are plain ``ipywidgets`` containers (``HBox``,
  ``VBox``, ``Button``, ...) so they can be nested inside other widgets or
  Jupyter layouts without any special handling.
- **Traitlets-driven** - where widgets need to expose or react to state, they
  do so through `traitlets <https://traitlets.readthedocs.io/>`_, so they can
  be linked (``traitlets.link``/``dlink``) to other widgets or to an
  application's model, following the patterns established by
  `aiidalab-widgets-base <https://github.com/aiidalab/aiidalab-widgets-base>`_.
- **Optional dependencies stay optional** - functionality that depends on an
  optional package (for example pseudopotential management via
  ``aiida-pseudo``, or magnetic structure support via ``pymatgen``) degrades
  gracefully or is only imported when needed, so the core package stays
  lightweight. See :ref:`optional-dependencies` for details.

Package layout
--------------

The installable package is ``alc_aiidalab_widgets`` and is organised as:

``alc_aiidalab_widgets.widgets``
    The individual widget implementations. Every widget described in
    :doc:`widgets` is re-exported from this subpackage, e.g.
    ``from alc_aiidalab_widgets.widgets import StructureViewWidget``.

``alc_aiidalab_widgets.viewers``
    The ``ALC_AIIDA_VIEWER_MAPPING`` dict, which maps AiiDA node type
    strings (e.g. ``data.core.structure.StructureData.``) to the widget used
    to display them, allowing AiiDA nodes to be rendered automatically using
    the widgets in this package wherever AiiDAlab displays a node.

``alc_aiidalab_widgets.layouts``
    A ``WizardAppWidgetStep`` subclass and helpers for building the
    step-by-step layouts used by AiiDAlab "wizard" apps.

``alc_aiidalab_widgets.types``
    Shared type aliases/definitions used across the package.

``alc_aiidalab_widgets.utils``
    Small, generic helper functions used internally (and useful when
    composing widgets together), such as :func:`~alc_aiidalab_widgets.utils.tab_from_dict`.

See :doc:`usage` to get started, and :doc:`widgets` for a description of
each widget and its public API.
