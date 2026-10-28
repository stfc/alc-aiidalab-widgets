"""Defines a widget for visualisation of chemical structures."""

from collections.abc import Sequence
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


def _build_magnetic_vector_field(
    positions: Sequence[Sequence[float]], moments: Sequence[Sequence[float]]
) -> dict:
    """Build a WeasWidget vector field settings dict from per-atom moments.

    Parameters
    ----------
    positions: Sequence[Sequence[float]]
        One cartesian position per atom.
    moments: Sequence[Sequence[float]]
        One cartesian magnetic moment vector per atom, matching `positions`.

    Returns
    -------
    dict
        A single-group vector field settings dict containing only the sites
        whose moment magnitude exceeds `_MAGNETIC_MOMENT_THRESHOLD`, or an
        empty dict if none do.
    """
    origins = []
    vectors = []
    for position, moment in zip(positions, moments, strict=True):
        if any(abs(component) > _MAGNETIC_MOMENT_THRESHOLD for component in moment):
            origins.append(list(position))
            vectors.append(list(moment))
    return (
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

    positions = []
    moments = []
    for site, position in zip(pmg_structure, atoms.get_positions(), strict=True):
        magmom = site.properties.get("magmom")
        if magmom is not None:
            positions.append(position)
            moments.append(magmom.moment)

    return atoms, _build_magnetic_vector_field(positions, moments)


def _is_magnetic_structure_data(node) -> bool:
    """Return True if `node` is an AiiDA `MagneticStructureData` instance.

    `MagneticStructureData` is defined in the optional, git-only
    `aiida-wannier90-workflows` package (it is not published on PyPI, so it
    cannot be added as a normal dependency). If that package is not
    installed, no node can be an instance of it, so this simply returns
    False rather than raising.
    """
    try:
        from aiida_wannier90_workflows.data.structure import MagneticStructureData
    except ImportError:
        return False
    return isinstance(node, MagneticStructureData)


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
        if _is_magnetic_structure_data(node):
            # Checked before the generic StructureData case below, since
            # MagneticStructureData is itself a StructureData subclass.
            self.assign_structure_from_magnetic_structuredata(node)
        elif isinstance(node, StructureData):
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
            alongside the viewer. Equivalent to calling `set_vector_field`
            after loading `structure`.
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
        self.set_vector_field(magnetic_vectors)
        return

    def set_vector_field(self, settings: dict | None) -> None:
        """Set, update, or clear the viewer's per-atom vector field overlay.

        Generic entry point for any vector field data (magnetic moments,
        forces, etc.), not specific to magnetism; see `set_magnetic_vectors`
        for a convenience wrapper that builds the settings dict for magnetic
        moments from a plain per-atom vector list. Can be called at any time
        after a structure has been assigned (not just at load time) to add,
        replace, or remove the vector arrows in place, without reloading the
        structure's geometry.

        Parameters
        ----------
        settings: dict | None
            A WeasWidget vector field settings dict, e.g. one or more named
            groups each with `origins`, `vectors`, `color`, and optionally
            `radius`/`factor` (see `viewer.avr.vf.settings`). None or an
            empty dict removes the vector field and hides its controls.

        Raises
        ------
        RuntimeError
            If no structure has been assigned yet.
        """
        if self.viewer is None:
            raise RuntimeError(
                "Cannot set a vector field before a structure has been assigned."
            )
        if settings:
            self.viewer.avr.vf.settings = settings
            self.viewer.avr.vf.show = True
            self._ensure_magnetic_controls()
            self._magnetic_toggle.value = True
            self._magnetic_thickness_slider.value = _DEFAULT_ARROW_RADIUS
            self.children = [self._magnetic_controls, self.viewer]
        else:
            self.viewer.avr.vf.settings = {}
            self.children = [self.viewer]
        return

    def set_magnetic_vectors(self, vectors: Sequence[Sequence[float]] | None) -> None:
        """Set, update, or clear the magnetic moment vector field.

        Convenience wrapper around `set_vector_field` for the common case of
        per-atom magnetic moments; pass a raw vector field settings dict to
        `set_vector_field` directly for full control or other vector data.

        Parameters
        ----------
        vectors: Sequence[Sequence[float]] | None
            A sequence with one cartesian 3-vector per currently displayed
            atom (in the same order), from which a single "magnetic moment"
            vector field group is built automatically using the atoms'
            current positions; sites with a near-zero moment are omitted.
            None or an empty sequence removes the vector field.

        Raises
        ------
        RuntimeError
            If no structure has been assigned yet.
        ValueError
            If vectors are given while a trajectory (rather than a single
            structure) is displayed.
        """
        if not vectors:
            self.set_vector_field(None)
            return
        if self.viewer is None:
            raise RuntimeError(
                "Cannot set magnetic vectors before a structure has been assigned."
            )
        atoms = self.viewer.to_ase()
        if isinstance(atoms, list):
            raise ValueError(
                "Cannot derive atom positions for a trajectory; use "
                "set_vector_field with an explicit settings dict instead."
            )
        self.set_vector_field(
            _build_magnetic_vector_field(atoms.get_positions(), vectors)
        )
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

    def assign_structure_from_magnetic_structuredata(self, structure) -> None:
        """Visualise the given AiiDA MagneticStructureData object.

        Follows the same path as loading a .mcif file: the per-kind magnetic
        moments are extracted and drawn as arrows alongside the structure.

        Parameters
        ----------
        structure: MagneticStructureData
            The AiiDA MagneticStructureData object (from the
            `aiida-wannier90-workflows` package), carrying a magnetic moment
            per kind.
        """
        kind_magmoms = {kind.name: kind.magmom for kind in structure.kinds}
        moments = [
            kind_magmoms.get(site.kind_name) or (0.0, 0.0, 0.0)
            for site in structure.sites
        ]
        atoms = structure.get_ase()
        magnetic_vectors = _build_magnetic_vector_field(atoms.get_positions(), moments)
        self.assign_structure_from_ase(atoms, magnetic_vectors=magnetic_vectors)
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
