"""Widgets for selecting and configuring code instances for AiiDA workflows."""

import ipywidgets as ipw
import traitlets as tl
from aiida.orm import ContainerizedCode, InstalledCode, PortableCode, QueryBuilder

DEFAULT_MAX_MPIPROCS = 1024


class CodeSelector(ipw.HBox):
    """
    A "code dropdown (+ optional MPI controls)" row, linked to model traits.

    A generic code selection widget that uses a database query to determine
    all available codes, optionally pre-select the best match based on the
    "code_name" and expose optional mpi controls for a given code.
    Requires a model which exposes codes and relevant mpi options as
    ``{code_name}_code`` or ``{code_name}_withmpi`` so they can be appropriately
    linked to the selection widgets.
    """

    def __init__(
        self,
        model,
        code_name: str,
        description: str | None = None,
        auto_default: bool = True,
        show_mpi: bool = False,
        **kwargs,
    ):
        """
        CodeSelectorRow constructor.

        Parameters
        ----------
        model : MultiCodeResourcesModel
            The model holding the resolved code labels.
        code_name : str
            One of the code names in ``REQUIRED_CODES``/``OPTIONAL_CODES``;
            selects which ``{code_name}_code`` trait this row is linked to.
        auto_default : bool
            Whether to pre-select a matching installed code as the default.
            Disabled for optional codes so they stay opt-in rather than being
            silently wired up behind the collapsed "Optional codes" section.
        show_mpi : bool
            Whether to show an MPI checkbox and a number-of-processes
            selector for this code, linked to its ``{code_name}_withmpi``/
            ``{code_name}_num_mpiprocs`` traits. Only set this for codes in
            :data:`~aiidalab_cif2j.models.resources.MPI_CAPABLE_CODES`, i.e.
            ones where ``get_builder_from_protocol`` actually exposes a
            resources override; there is currently no such hook for
            ``pw``/``pw2wannier90``, whose resources are computed internally
            from the protocol/structure.
        **kwargs :
            Keyword arguments passed to the `ipywidgets.HBox.__init__()`.
        """
        self.code_name = code_name
        self.auto_default = auto_default
        self._codes_by_label: dict[
            str, InstalledCode | ContainerizedCode | PortableCode
        ] = {}
        self.code = ipw.Dropdown(
            description=description if description else code_name,
            style={"description_width": "180px"},
            layout={"width": "65%"},
        )
        self.update_codes()
        tl.link((self.code, "value"), (model, f"{code_name}_code"))

        children = [self.code]

        if show_mpi:
            self.withmpi = ipw.Checkbox(
                description="MPI",
                indent=False,
                layout={"width": "15%"},
            )
            tl.link((model, f"{code_name}_withmpi"), (self.withmpi, "value"))

            self.num_mpiprocs = ipw.BoundedIntText(
                min=1,
                max=DEFAULT_MAX_MPIPROCS,
                description="# procs",
                style={"description_width": "60px"},
                layout={"width": "20%"},
                disabled=not self.withmpi.value,
            )
            tl.link((model, f"{code_name}_num_mpiprocs"), (self.num_mpiprocs, "value"))
            self.withmpi.observe(self._on_withmpi_change, "value")
            self.code.observe(self._on_code_change, "value")
            self._update_mpi_limits(self.code.value)

            children += [self.withmpi, self.num_mpiprocs]

        super().__init__(
            children=children,
            layout={"width": "100%"},
            **kwargs,
        )
        return

    def _on_withmpi_change(self, change: dict) -> None:
        """Only let the process-count selector be edited while MPI is enabled."""
        self.num_mpiprocs.disabled = not change["new"]
        return

    def _on_code_change(self, change: dict) -> None:
        """Keep the MPI controls in sync with the resources of the new code."""
        self._update_mpi_limits(change["new"])
        return

    def _update_mpi_limits(self, label: str | None) -> None:
        """Reset the MPI controls to the maximum the selected code supports.

        ``with_mpi`` is an explicit opt-in/opt-out on the code: ``False``
        means MPI is unsupported, ``True`` means it is, and the process
        count is capped by the computer's configured
        ``default_mpiprocs_per_machine`` if set, else by the generic
        :data:`DEFAULT_MAX_MPIPROCS`. Codes created through the AiiDAlab
        "Setup new code" widgets never set ``with_mpi`` though, so when it's
        left as ``None`` we fall back to the computer's configured
        ``default_mpiprocs_per_machine`` to decide both whether MPI is
        possible and how many processes are allowed: a configured value
        greater than 1 means MPI is supported with that many processes,
        otherwise MPI is treated as unsupported.

        Selecting a new code always resets the toggle and process count to
        the maximum it supports, rather than merely capping an existing
        selection.
        """
        code = self._codes_by_label.get(label)
        mpi_capable = False
        max_mpiprocs = 1

        if code is not None:
            configured = code.computer.get_default_mpiprocs_per_machine()
            if code.with_mpi is True:
                mpi_capable = True
                max_mpiprocs = configured or DEFAULT_MAX_MPIPROCS
            elif code.with_mpi is None:
                mpi_capable = bool(configured and configured > 1)
                max_mpiprocs = configured if mpi_capable else 1

        self.num_mpiprocs.max = max_mpiprocs
        self.num_mpiprocs.value = max_mpiprocs if mpi_capable else 1

        self.withmpi.disabled = not mpi_capable
        self.withmpi.value = mpi_capable
        return

    def update_codes(self, _=None) -> None:
        """Update the list of available codes, pre-selecting a sensible default.

        The default is the first code whose executable matches
        ``{code_name}.x`` (e.g. ``pw`` -> ``pw.x``), if any is installed. An
        already-valid selection (manual or previously auto-detected) is left
        untouched.
        """
        qb = QueryBuilder()
        qb.append((InstalledCode, ContainerizedCode, PortableCode))
        codes = [code for (code,) in qb.all()]
        code_labels = [f"{code.label}@{code.computer.label}" for code in codes]
        self._codes_by_label = dict(zip(code_labels, codes, strict=False))
        self.code.options = ["", *code_labels]

        if self.auto_default and self.code.value not in code_labels:
            executable_name = f"{self.code_name}.x".lower()
            for code, label in zip(codes, code_labels, strict=False):
                if code.get_executable().name.lower() == executable_name:
                    self.code.value = label
                    break

        if hasattr(self, "num_mpiprocs"):
            self._update_mpi_limits(self.code.value)
        return
