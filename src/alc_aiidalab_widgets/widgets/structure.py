"""Defines a widget for visualisation of chemical structures."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from aiida.orm import Node, SinglefileData, StructureData, TrajectoryData
from ase import Atoms
from ase import io as ase_io
from ipywidgets import HTML, VBox
from weas_widget import WeasWidget


class StructureViewWidget(VBox):
    """Visualise atom structure using weas_widget."""

    # Configuration for the WeasWidget GUI. The import button is disabled as
    # loading structures is typically handled elsewhere.
    _GUI_CONFIG = {"buttons": {"import": False}}

    def __init__(self, node: Node | None = None, **kwargs):
        """StructureViewWidget constructor."""
        super().__init__(**kwargs)
        self.message = HTML("<p>No Structure Currently Loaded</p>")
        self.viewer = None
        self.children = [
            self.message,
        ]
        if isinstance(node, StructureData):
            self.assign_structure_from_structuredata(node)
        elif isinstance(node, SinglefileData):
            self.assign_structure_from_file(node.filename, node.content)
        elif isinstance(node, TrajectoryData):
            self.assign_structure_from_trajectorydata(node)
        elif node:
            self.message.value = (
                "<p>AiiDA Node type not supported by the structure viewer."
            )

    def assign_structure_from_file(
        self, fname: str, content: bytes, format: str | None = None
    ) -> None:
        """Visualise the given structure from a file.

        Parameters
        ----------
        fname: str
            The structure file path.
        content: bytes
            The content of the file.
        format: str | None
            An optional format specifier compatible with ASE. By default it is set
            to None which results in ASE auto-detecting the file format from the
            filename/extension.
        """
        suffix = "".join(Path(fname).suffixes)
        with NamedTemporaryFile(suffix=suffix) as tmpf:
            tmpf.write(content)
            tmpf.flush()
            try:
                images = ase_io.read(tmpf.name, index=":", format=format)
            except (KeyError, ase_io.formats.UnknownFileTypeError):
                self.message = HTML("<p>Could not visualise structure...</p>")
                self.children = [
                    self.message,
                ]
            else:
                # Unwrap single-frame files so they aren't shown with a
                # redundant trajectory slider.
                structure = images[0] if len(images) == 1 else images
                self.assign_structure_from_ase(structure)
        return

    def assign_structure_from_ase(self, structure: Atoms | list[Atoms]) -> None:
        """Visualise the given ASE structure.

        Parameters
        ----------
        structure: Atoms | list[Atoms]
            The ASE atoms structure(s) object.
        """
        self.viewer = WeasWidget(guiConfig=self._GUI_CONFIG)
        self.viewer.from_ase(structure)
        self.children = [
            self.viewer,
        ]
        return

    def to_ase(self) -> Atoms | list[Atoms] | None:
        """Return the currently displayed structure as ASE Atoms.

        The returned object reflects any edits made interactively in the viewer,
        not just the structure originally loaded. A single structure is returned
        as an ``Atoms`` object and a trajectory as a ``list[Atoms]``.

        Returns
        -------
        Atoms | list[Atoms] | None
            The displayed structure, or None if no structure is loaded. Note the
            viewer must have been displayed for the returned data to be current.
        """
        if self.viewer is None:
            return None
        return self.viewer.to_ase()

    def to_aiida(self) -> StructureData | TrajectoryData | None:
        """Return the currently displayed structure as an AiiDA node.

        The returned node reflects any edits made interactively in the viewer,
        not just the structure originally loaded. A single structure is returned
        as a ``StructureData`` node and a trajectory as a ``TrajectoryData`` node.

        Returns
        -------
        StructureData | TrajectoryData | None
            The displayed structure, or None if no structure is loaded. Note the
            viewer must have been displayed for the returned node to be current.
        """
        if self.viewer is None:
            return None
        return self.viewer.to_aiida()

    def assign_structure_from_structuredata(self, structure: StructureData) -> None:
        """Visualise the given AiiDA StructureData object.

        Parameters
        ----------
        structure: StructureData
            The AiiDA StructureData object.
        """
        self.assign_structure_from_ase(structure.get_ase())
        return

    def assign_structure_from_trajectorydata(self, trajectory: TrajectoryData) -> None:
        """
        Visualise a series of structures contained in an AiiDA TrajectoryData node.

        Parameters
        ----------
        trajectory: TrajectoryData
            The AiiDA TrajectoryData node containing the structure series to visualise.
        """
        atoms = [
            trajectory.get_step_structure(i).get_ase()
            for i in range(trajectory.numsteps)
        ]
        self.assign_structure_from_ase(atoms)
        return
