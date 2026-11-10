Viewers
=======

In addition to the widgets described in :doc:`widgets`, this package exposes
a routing table, ``ALC_AIIDA_VIEWER_MAPPING``, that maps AiiDA node types to
the widget that should be used to display them. It is designed to be used
alongside the equivalent mapping already provided by
`aiidalab-widgets-base <https://github.com/aiidalab/aiidalab-widgets-base>`_,
rather than as a replacement for it.

How AiiDAlab's viewer dispatch works
-------------------------------------

``aiidalab_widgets_base.viewers`` defines a module-level dict,
``AIIDA_VIEWER_MAPPING``, and a ``viewer(obj, **kwargs)`` function. Given an
AiiDA node, ``viewer()`` looks up the widget to use by the node's
``node_type`` (or, for process nodes, its ``process_type``), instantiates it
as ``widget(obj, **kwargs)``, and returns it - falling back to returning the
node itself if nothing is registered for that type. This is the same lookup
used internally whenever AiiDAlab displays a node (for example in process
monitors or generic node-browsing widgets).

New entries are normally added either by calling
``AIIDA_VIEWER_MAPPING[node_type] = widget`` directly, or via the
``register_viewer_widget(key)`` decorator provided by that module.

``ALC_AIIDA_VIEWER_MAPPING``
------------------------------

``alc_aiidalab_widgets.viewers.ALC_AIIDA_VIEWER_MAPPING`` is a plain dict
with the same shape as ``AIIDA_VIEWER_MAPPING`` - node/process type strings
mapped to the ALC widget that should render them - covering the node types
this package knows how to visualise:

.. list-table::
   :header-rows: 1

   * - Node/process type
     - Widget
   * - ``process.calculation.calcfunction.CalcFunctionNode.``
     - ``ProcessNodeViewerWidget``
   * - ``process.calculation.calcjob.CalcJobNode.``
     - ``ProcessNodeViewerWidget``
   * - ``process.workflow.workfunction.WorkFunctionNode.``
     - ``ProcessNodeViewerWidget``
   * - ``process.workflow.workchain.WorkChainNode.``
     - ``ProcessNodeViewerWidget``
   * - ``data.core.structure.StructureData.``
     - :class:`StructureViewWidget <alc_aiidalab_widgets.widgets.structure.StructureViewWidget>`
   * - ``data.core.singlefile.SinglefileData.``
     - ``SinglefileDataViewer``
   * - ``data.core.array.trajectory.TrajectoryData.``
     - :class:`StructureViewWidget <alc_aiidalab_widgets.widgets.structure.StructureViewWidget>`
   * - ``data.core.array.ArrayData.``
     - :class:`GenericArrayDataTableWidget <alc_aiidalab_widgets.widgets.tables.GenericArrayDataTableWidget>`
   * - ``data.wannier90_workflows.MagneticStructureData.MagneticStructureData.``
     - :class:`StructureViewWidget <alc_aiidalab_widgets.widgets.structure.StructureViewWidget>`
   * - ``xyz_table`` *(custom redirection, see below)*
     - :class:`XYZArrayDataTableWidget <alc_aiidalab_widgets.widgets.tables.XYZArrayDataTableWidget>`

The ``MagneticStructureData`` entry is included defensively: that type is
defined by the optional, git-only ``aiida-wannier90-workflows`` package, so
the key is only ever matched if that package happens to be installed and a
node of that type is encountered.

The ``xyz_table`` key is **not** a real AiiDA ``node_type``/``process_type``
- it is a custom redirection for application code that knows a given
``ArrayData`` node holds XYZ/per-site data (e.g. atomic positions or
forces) and wants the more specific :class:`XYZArrayDataTableWidget` instead
of the generic ``data.core.array.ArrayData.`` entry. Since it will never be
matched automatically by ``viewer()``, an app must look it up and apply it
explicitly, e.g. ``ALC_AIIDA_VIEWER_MAPPING["xyz_table"](array_node)``, when
it knows more about the array's contents than the node type alone conveys.

Using it alongside ``aiidalab-widgets-base``
----------------------------------------------

Merge ``ALC_AIIDA_VIEWER_MAPPING`` into ``AIIDA_VIEWER_MAPPING`` once, early
in your app (for example where it configures its other widgets), so that
``aiidalab_widgets_base.viewers.viewer()`` - and anything built on top of
it, such as ``AiidaNodeViewWidget`` - picks up the ALC widgets too:

.. code-block:: python

   from aiidalab_widgets_base.viewers import AIIDA_VIEWER_MAPPING, viewer
   from alc_aiidalab_widgets.viewers import ALC_AIIDA_VIEWER_MAPPING

   AIIDA_VIEWER_MAPPING.update(ALC_AIIDA_VIEWER_MAPPING)

   # Elsewhere in the app, exactly as if this were a built-in viewer:
   widget = viewer(some_aiida_node)

Because ``dict.update`` is used, entries from ``ALC_AIIDA_VIEWER_MAPPING``
take precedence over any built-in entry for the same node type (for example
``data.core.structure.StructureData.``, which ``aiidalab-widgets-base`` also
registers a default viewer for) - merge them in whichever order matches the
behaviour you want if you need to preserve the base package's own viewer for
a given type instead.
