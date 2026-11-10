Widgets
=======

This page describes every widget publicly exported from
``alc_aiidalab_widgets.widgets``. Each can be imported directly from that
subpackage, e.g.:

.. code-block:: python

   from alc_aiidalab_widgets.widgets import StructureViewWidget

Each section below gives a short description of what the widget does, when
to use it, and (where applicable) a screenshot of it in use. For the full
API reference, see :doc:`api/modules`.

AiiDADatabaseQueryWidget
------------------------

A general-purpose widget for browsing and searching the AiiDA database. It
is initialised with a list of AiiDA node classes to search for (defaulting
to ``CalcJobNode`` and ``WorkChainNode``), and provides a node-type filter,
a creation-mode filter ("all"/"uploaded"/"calculated") and a date-range
filter, listing matching results in a dropdown. Selecting a result sets the
widget's ``data_object`` trait to the corresponding AiiDA node, which can be
linked/observed to display it elsewhere (e.g. with one of the viewer
widgets). This is an ALC-adapted version of the equivalent widget from
``aiidalab-widgets-base``.

.. TODO: screenshot
.. .. image:: _static/screenshots/aiida_database_query_widget.png
..    :alt: AiiDADatabaseQueryWidget

CodeSelector
------------

A single "code dropdown + optional MPI controls" row for picking which
installed AiiDA code to use for a given step of a workflow. It queries the
AiiDA database for installed/containerized/portable codes, can pre-select a
sensible default based on the code's executable name, and optionally shows
MPI enable/process-count controls. It is linked to a model via traitlets,
reading and writing a ``{code_name}_code`` (and optionally
``{code_name}_withmpi``/``{code_name}_num_mpiprocs``) trait, so several
``CodeSelector`` rows can share one model to configure a multi-code
workflow.

.. TODO: screenshot
.. .. image:: _static/screenshots/code_selector.png
..    :alt: CodeSelector widget

CodeSetupWidget
----------------

A widget for registering a new AiiDA code (computer + executable) from a
remote resources database. It extends
``aiidalab_widgets_base.computational_resources.ResourceSetupBaseWidget``
with an editable "Source" field, pre-filled with the ALC resources database
(hosted in the `alc-ux <https://github.com/stfc/alc-ux>`_ repository), so
that users can set up new codes without needing to hand-edit computer/code
configuration files. Use this widget wherever an AiiDAlab app needs to let a
user configure a new AiiDA code, in addition to selecting an existing one
with :class:`CodeSelector`.

.. TODO: screenshot
.. .. image:: _static/screenshots/code_setup_widget.png
..    :alt: CodeSetupWidget

Download
--------

A button that triggers a browser download when clicked. It is constructed
with a filename, a callback returning the data to save (as ``str`` or
``bytes``), and an ``ipywidgets.Output`` used to inject the Javascript that
performs the download - this indirection is required because Jupyter has no
native "save file" mechanism. Use this to let users export results (plots,
structures, logs, ...) generated within a notebook or AiiDAlab app as a
file.

FileUploadWidget
-----------------

A labelled file upload row that wraps ``ipywidgets.FileUpload``. Once a file
is selected, its contents are wrapped into an AiiDA ``SinglefileData`` node
and exposed via the widget's ``file`` trait, and the uploaded filename is
shown next to the upload button. Use this wherever a user needs to supply an
arbitrary input file (e.g. a structure or parameter file) that should end up
stored as an AiiDA data node.

.. TODO: screenshot
.. .. image:: _static/screenshots/file_upload_widget.png
..    :alt: FileUploadWidget

GenericArrayDataTableWidget
----------------------------

A table widget for displaying any AiiDA ``ArrayData`` node, regardless of
the shape of its arrays. A multi-select lets the user choose which of the
node's arrays to show (2D arrays are expanded into one column per
component), rendered as a scrollable HTML table, with the option to pick a
different array to use as the x-axis. Selected columns can also be plotted
interactively via :class:`PlotWidget` at the click of a button. A
``from_file`` classmethod builds the widget directly from a plain text data
file. This is the widget registered for generic ``ArrayData`` nodes in
``alc_aiidalab_widgets.viewers``; use :class:`XYZArrayDataTableWidget`
instead when the array data is specifically XYZ/per-site data.

.. TODO: screenshot
.. .. image:: _static/screenshots/generic_array_data_table_widget.png
..    :alt: GenericArrayDataTableWidget

LoadingWidget
-------------

A simple, reusable loading indicator: a text label next to an animated
spinner icon. Use it as a placeholder to display while a longer-running
operation (a database query, a remote calculation, a download, ...)
completes, then swap it out for the real content once it is ready.

.. TODO: screenshot
.. .. image:: _static/screenshots/loading_widget.png
..    :alt: LoadingWidget

PlotWidget
----------

An interactive line plot for one or more data series, built on top of a
``plotly.graph_objects.FigureWidget`` (itself an ipywidget, so it integrates
natively into an AiiDAlab UI). It accepts a single 1D array or a list of
them, plots each against a shared or per-series set of x values, and gives
the user pan/zoom/hover controls for free. Use this to visualise numeric
AiiDA output (energies, forces, convergence series, ...) without needing to
build a plotly figure by hand; it is also used internally by
:class:`GenericArrayDataTableWidget` to plot selected columns.

.. TODO: screenshot
.. .. image:: _static/screenshots/plot_widget.png
..    :alt: PlotWidget

PseudoManagerWidget
--------------------

A tabbed widget for managing pseudopotential families via
`aiida-pseudo <https://github.com/aiidateam/aiida-pseudo>`_, with one tab
listing the pseudopotential families already installed in the AiiDA profile
and another for installing a new family - either a standard SSSP/PseudoDojo
configuration downloaded on demand, or a family built from an uploaded
pseudopotential archive. This widget requires the optional ``aiida-pseudo``
dependency (install with the ``pseudo`` extra, see
:ref:`optional-dependencies`); without it, a dummy placeholder widget is
used instead so importing the package does not fail.

.. TODO: screenshot
.. .. image:: _static/screenshots/pseudo_manager_widget.png
..    :alt: PseudoManagerWidget

Status
------

A small ``ipywidgets.HTML``-based widget for showing a single coloured
status message - success (green), warning (yellow) or failure (red) - using
consistent styling. Use it to give users feedback about the outcome of an
action (a validation check, a submission, a search, ...) without having to
hand-roll HTML/CSS each time.

StructureViewWidget
--------------------

An interactive 3D viewer for atomic structures, built on top of
`weas_widget <https://github.com/superstar54/weas-widget>`_. It accepts an
AiiDA ``StructureData``, ``TrajectoryData`` or ``SinglefileData`` node (or a
raw structure file) and renders it in the notebook, tracking whether the
user has interactively edited the geometry via its ``edited`` trait. If the
optional ``pymatgen`` dependency is installed (``magnetic`` extra, see
:ref:`optional-dependencies`), it can also parse ``.mcif`` files and
magnetic ``StructureData`` nodes, drawing per-atom magnetic moments as a
vector field with adjustable visibility/thickness controls. This is the
widget registered for structure-like AiiDA nodes in
``alc_aiidalab_widgets.viewers``.

.. TODO: screenshot
.. .. image:: _static/screenshots/structure_view_widget.png
..    :alt: StructureViewWidget

XYZArrayDataTableWidget
-------------------------

A table widget for displaying an AiiDA ``ArrayData`` node whose arrays are
XYZ-based (e.g. atomic positions or forces), such as the per-site data
attached to a relaxation or vibrational calculation. A dropdown lets the
user switch between the arrays stored on the node, each rendered as a
formatted HTML table with one row per site. This is the widget registered
for the ``"xyz_table"`` viewer redirection in
``alc_aiidalab_widgets.viewers``.

.. TODO: screenshot
.. .. image:: _static/screenshots/xyz_array_data_table_widget.png
..    :alt: XYZArrayDataTableWidget
