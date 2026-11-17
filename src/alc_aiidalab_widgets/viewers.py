"""Defines custom viewers for AiiDA nodes."""

from functools import partial

from alc_aiidalab_widgets.widgets.file_viewer import SinglefileDataViewer
from alc_aiidalab_widgets.widgets.process_node_view import ProcessNodeViewerWidget
from alc_aiidalab_widgets.widgets.structure import StructureViewWidget
from alc_aiidalab_widgets.widgets.tables import (
    GenericArrayDataTableWidget,
    XYZArrayDataTableWidget,
)

ALC_AIIDA_VIEWER_MAPPING = {
    # Process node type labels
    "process.calculation.calcfunction.CalcFunctionNode.": ProcessNodeViewerWidget,
    "process.calculation.calcjob.CalcJobNode.": ProcessNodeViewerWidget,
    "process.workflow.workfunction.WorkFunctionNode.": ProcessNodeViewerWidget,
    "process.workflow.workchain.WorkChainNode.": ProcessNodeViewerWidget,
    # AiiDA data type labels
    "data.core.structure.StructureData.": StructureViewWidget,
    "data.core.singlefile.SinglefileData.": SinglefileDataViewer,
    "data.core.array.trajectory.TrajectoryData.": StructureViewWidget,
    "data.core.array.ArrayData.": GenericArrayDataTableWidget,
    # MagneticStructureData from the optional aiida-wannier90-workflows
    # package; visualised the same way, with magnetic moments drawn as
    # arrows.
    "data.wannier90_workflows.MagneticStructureData.MagneticStructureData.": (
        StructureViewWidget
    ),
    # ExchangeCouplingData from the optional aiida-cif2j package
    "data.cif2j.exchange_coupling.ExchangeCouplingData.": partial(
        GenericArrayDataTableWidget,
        units={"J_iso": "meV", "distance": "Ang", "distance_vector": "Ang"},
    ),
    # DMIVectorData/AnisotropicExchangeData from the optional aiida-cif2j package
    "data.cif2j.dmi_vectors.DMIVectorData.": partial(
        GenericArrayDataTableWidget,
        units={"dmi_vector": "meV", "distance": "Ang", "distance_vector": "Ang"},
    ),
    "data.cif2j.anisotropic_exchange.AnisotropicExchangeData.": partial(
        GenericArrayDataTableWidget,
        units={"J_tensor": "meV", "distance": "Ang", "distance_vector": "Ang"},
    ),
    # Custom redirections
    "xyz_table": XYZArrayDataTableWidget,
}
