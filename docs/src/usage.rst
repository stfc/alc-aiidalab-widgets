Usage
=====

Installation
------------

The package is published on PyPI and can be installed with pip:

.. code-block:: sh

   pip install alc-aiidalab-widgets

Some widgets depend on optional third-party packages that are not installed
by default, to keep the base install lightweight. These are exposed as
extras (see :ref:`optional-dependencies`):

.. code-block:: sh

   pip install alc-aiidalab-widgets[pseudo]      # PseudoManagerWidget
   pip install alc-aiidalab-widgets[magnetic]    # magnetic structure support in StructureViewWidget

Since this package is designed to run inside AiiDAlab, it assumes a working
`AiiDA <https://aiida.net/>`_ profile is configured in the environment it is
used in (most widgets query the AiiDA database directly).

Quick start
-----------

Widgets are imported from the ``alc_aiidalab_widgets.widgets`` subpackage and
used like any other ``ipywidgets`` widget, most naturally inside a Jupyter
notebook or an AiiDAlab app:

.. code-block:: python

   from alc_aiidalab_widgets.widgets import StructureViewWidget

   structure_node = ...  # an AiiDA StructureData node
   viewer = StructureViewWidget(node=structure_node)
   viewer  # displays the 3D structure viewer in a Jupyter cell

Because every widget is a standard ``ipywidgets`` container, they can be
combined with plain ``ipywidgets`` layout widgets and composed into larger
applications:

.. code-block:: python

   import ipywidgets as ipw
   from alc_aiidalab_widgets.widgets import Status, StructureViewWidget

   status = Status()
   viewer = StructureViewWidget()
   app = ipw.VBox([status, viewer])
   app

Several widgets expose `traitlets <https://traitlets.readthedocs.io/>`_
attributes rather than, or in addition to, callbacks, so they can be linked
to your application's own state:

.. code-block:: python

   import traitlets as tl
   from alc_aiidalab_widgets.widgets import FileUploadWidget

   upload = FileUploadWidget()
   tl.observe(upload, lambda change: print("Uploaded:", change["new"]), names="file")

.. _optional-dependencies:

Optional dependencies
----------------------

A small number of widgets build on top of optional dependencies that are not
installed by default:

.. list-table::
   :header-rows: 1

   * - Widget
     - Extra
     - Required for
   * - :class:`~alc_aiidalab_widgets.widgets.pseudos.PseudoManagerWidget`
     - ``pseudo``
     - Installing/listing pseudopotential families via ``aiida-pseudo``.
   * - :class:`~alc_aiidalab_widgets.widgets.structure.StructureViewWidget`
     - ``magnetic``
     - Visualising magnetic moments from ``.mcif`` files, via ``pymatgen``.

If the relevant extra is not installed, these widgets either disable the
affected feature or display a dummy/explanatory widget instead of raising an
import error, so it is safe to depend on this package without installing
every extra.

Where to go next
-----------------

See :doc:`widgets` for a description of every widget provided by this
package, along with its full API reference.
