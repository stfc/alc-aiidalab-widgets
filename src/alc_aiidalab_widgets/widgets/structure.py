"""Defines a widget for visualisation of chemical structures."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import traitlets
from aiida.orm import Node, SinglefileData, StructureData, TrajectoryData
from ase import Atoms
from ase import io as ase_io
from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox
from weas_widget import WeasWidget

# Magnetic moments below this magnitude (in Bohr magnetons) are treated as
# zero and excluded from the magnetic moment vector field
_MAGNETIC_MOMENT_THRESHOLD = 1e-3

# Default shaft/head radius (in the structure's length units) of the arrows
# used to draw magnetic moment vectors
_DEFAULT_ARROW_RADIUS = 0.1


def _parse_mcif(content: bytes) -> tuple[Atoms, dict]:
    """Parse a magnetic CIF file into an ASE structure and moment vector field.

    Parameters
    ----------
    content: bytes
        The content of the .mcif file.

    Returns
    -------
    tuple[Atoms, dict]
        The parsed structure and a WeasWidget vector field settings dict
        describing the per-site magnetic moments (empty if the file has no
        non-zero moments).

    Raises
    ------
    ImportError
        If the optional `pymatgen` dependency is not installed.
    """
    try:
        from pymatgen.io.ase import AseAtomsAdaptor
        from pymatgen.io.cif import CifParser
    except ImportError as exc:
        raise ImportError(
            "Reading .mcif files requires the optional `pymatgen` dependency. "
            "Install it with `pip install alc-aiidalab-widgets[magnetic]`."
        ) from exc

    pmg_structure = CifParser.from_str(content.decode("utf-8")).parse_structures(
        primitive=False
    )[0]
    atoms = AseAtomsAdaptor.get_atoms(pmg_structure)

    origins = []
    vectors = []
    for site, position in zip(pmg_structure, atoms.get_positions(), strict=True):
        magmom = site.properties.get("magmom")
        moment = magmom.moment if magmom is not None else None
        if moment is not None and any(
            abs(component) > _MAGNETIC_MOMENT_THRESHOLD for component in moment
        ):
            origins.append(list(position))
            vectors.append(list(moment))

    vector_field = (
        {
            "magnetic moment": {
                "origins": origins,
                "vectors": vectors,
                "color": "orange",
                "radius": _DEFAULT_ARROW_RADIUS,
            }
        }
        if vectors
        else {}
    )
    return atoms, vector_field


class StructureViewWidget(VBox):
    """Visualise atom structure using weas_widget."""

    #: True once the user changes the geometry interactively in the viewer. Reset
    #: to False whenever a structure is (re)assigned programmatically.
    edited = traitlets.Bool(False)

    # Configuration for the WeasWidget GUI. The import button is disabled as
    # loading structures is typically handled elsewhere.
    _GUI_CONFIG = {"buttons": {"import": False}}

    def __init__(self, node: Node | None = None, **kwargs):
        """StructureViewWidget constructor."""
        super().__init__(**kwargs)
        self.message = HTML("<p>No Structure Currently Loaded</p>")
        self.viewer = None
        # Controls for the magnetic moment vector field (visibility toggle and
        # arrow thickness slider), created lazily once a structure with
        # magnetic moments has been loaded.
        self._magnetic_toggle = None
        self._magnetic_thickness_slider = None
        self._magnetic_controls = None
        # Guard used to distinguish programmatic structure loads (which set the
        # viewer's atoms trait synchronously) from interactive edits (which
        # arrive asynchronously over the comm) so only the latter set `edited`.
        self._loading = False
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
            filename/extension. Ignored for `.mcif` files, which are parsed
            separately to extract magnetic moment information.
        """
        suffix = "".join(Path(fname).suffixes)
        if Path(fname).suffix.lower() == ".mcif":
            try:
                structure, magnetic_vectors = _parse_mcif(content)
            except ImportError:
                self.message = HTML(
                    "<p>Rendering .mcif files requires the optional "
                    "<code>pymatgen</code> dependency. Install it with "
                    "<code>pip install alc-aiidalab-widgets[magnetic]</code>.</p>"
                )
                self.children = [self.message]
            except Exception:  # noqa: BLE001
                self.message = HTML("<p>Could not visualise structure...</p>")
                self.children = [self.message]
            else:
                self.assign_structure_from_ase(
                    structure, magnetic_vectors=magnetic_vectors
                )
            return
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

    def assign_structure_from_ase(
        self, structure: Atoms | list[Atoms], magnetic_vectors: dict | None = None
    ) -> None:
        """Visualise the given ASE structure.

        The viewer is created once and reused for subsequent structures; the
        displayed geometry is updated in place rather than rebuilding the widget,
        preserving view state and observers across loads.

        Parameters
        ----------
        structure: Atoms | list[Atoms]
            The ASE atoms structure(s) object.
        magnetic_vectors: dict | None
            An optional WeasWidget vector field settings dict describing
            per-site magnetic moments. When given, the moments are drawn as
            arrows and controls for their visibility/thickness are shown
            alongside the viewer.
        """
        self._ensure_viewer()
        # Suppress the edit flag while loading: this sets the viewer's atoms
        # trait synchronously, which would otherwise be seen as an interactive
        # edit by the observer.
        self._loading = True
        try:
            self.viewer.from_ase(structure)
        finally:
            self._loading = False
        # A freshly loaded structure is considered unedited.
        self.edited = False
        if magnetic_vectors:
            self.viewer.avr.vf.settings = magnetic_vectors
            self.viewer.avr.vf.show = True
            self._ensure_magnetic_controls()
            self._magnetic_toggle.value = True
            self._magnetic_thickness_slider.value = _DEFAULT_ARROW_RADIUS
            self.children = [self._magnetic_controls, self.viewer]
        else:
            self.children = [self.viewer]
        return

    def _ensure_magnetic_controls(self) -> None:
        """Create the magnetic moment vector field controls on first use."""
        if self._magnetic_controls is None:
            self._magnetic_toggle = Checkbox(
                description="Show magnetic moments", indent=False
            )
            traitlets.link(
                (self._magnetic_toggle, "value"),
                (self.viewer._widget, "showVectorField"),
            )
            self._magnetic_thickness_slider = FloatSlider(
                value=_DEFAULT_ARROW_RADIUS,
                min=0.02,
                max=0.3,
                step=0.01,
                description="Arrow thickness",
                style={"description_width": "initial"},
            )
            self._magnetic_thickness_slider.observe(
                self._on_arrow_thickness_changed, names="value"
            )
            self._magnetic_controls = HBox(
                [self._magnetic_toggle, self._magnetic_thickness_slider]
            )
        return

    def _on_arrow_thickness_changed(self, change: dict) -> None:
        """Update the radius of every magnetic moment vector field group."""
        for group in self.viewer.avr.vf.settings.values():
            group["radius"] = change["new"]
        return

    def _ensure_viewer(self) -> None:
        """Create the WeasWidget viewer on first use and start observing edits."""
        if self.viewer is None:
            self.viewer = WeasWidget(guiConfig=self._GUI_CONFIG)
            self.viewer._widget.observe(self._on_atoms_changed, names="atoms")
        return

    def _on_atoms_changed(self, change: dict) -> None:
        """Flag interactive geometry edits made by the user in the viewer."""
        if not self._loading:
            self.edited = True
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
        # atoms = [
        #     trajectory.get_step_structure(i).get_ase()
        #     for i in range(trajectory.numsteps)
        # ]
        symbols = trajectory.symbols
        positions = trajectory.get_positions()
        nsteps = trajectory.numsteps
        atoms = []
        for i in range(nsteps):
            step = Atoms(symbols=symbols, positions=positions[i])
            atoms.append(step)
        self.assign_structure_from_ase(atoms)
        return
