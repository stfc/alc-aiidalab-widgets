"""Widget for selecting MLIP model."""
from pathlib import Path
from typing import Generic, TypeVar

import ipywidgets as ipw
from aiida.orm import Node, QueryBuilder, SinglefileData

from alc_aiidalab_widgets.utils import tab_from_dict
from alc_aiidalab_widgets.widgets import AiiDADatabaseQueryWidget, FileUploadWidget
from alc_aiidalab_widgets.widgets.parameters import ParametersBlock

try:
    import aiida_mlip
except ImportError:
    aiida_mlip = None

NT = TypeVar("NT", bound=Node)


class ModelError(Exception): ...


class ModelSelect(ipw.VBox, Generic[NT]):
    """Widget for selecting MLIP model."""

    def __init__(
        self,
        *,
        model_cls: type[NT] | None = None,
        logspace: ipw.Output | None = None,
    ) -> None:

        if logspace is not None:
            self.logspace = logspace
        else:
            self.logspace = ipw.Output()  # Dummy output just dumps nowhere.
        self.model_cls = model_cls
        tabs = {}

        # Remote Model
        self.model_from_uri = ipw.Text(
            value="",
            description="Model:",
            placeholder="file:///Path/To/Model",
            layout=ipw.Layout(width="80%"),
        )
        uri_vbox = ipw.VBox([self.model_from_uri, self.arch], layout={"width": "100%"})
        parameters_block = ParametersBlock(
            "",
            {"model": self.model_from_uri, "arch": self.arch},
            {
                "mace_mp": {
                    "model": "https://github.com/stfc/janus-core/raw/main/tests/models/mace_mp_small.model",
                    "arch": "mace_mp",
                }
            },
        )
        uri_vbox = ipw.HBox([uri_vbox, parameters_block])
        tabs["From URI"] = uri_vbox

        # Local Model
        self.model_from_local = FileUploadWidget()
        tabs["From local"] = self.model_from_local

        # AiiDA Model
        if self.model_cls:
            self.model_from_node = AiiDADatabaseQueryWidget(
                title="AiiDA Database",
                query=[self.model_cls],
            )
            self.refresh_models_button = ipw.Button(
                description="Refresh",
                button_style="info",
                tooltip="Refresh the list of available models",
                icon="refresh",
                layout={"width": "20%"},
            )
            self.refresh_models_button.on_click(self.update_models)
            self.model_node_box = ipw.HBox(
                [self.model_from_node, self.refresh_models_button],
                layout={"width": "100%"},
            )
            node_vbox = ipw.VBox(
                [self.model_node_box, self.arch], layout={"width": "100%"}
            )
            tabs["AiiDA Database"] = node_vbox

        self.arch = ipw.Dropdown(
            options=(
                "mace",
                "mace_mp",
                "mace_off",
                "chgnet",
                "sevennet",
                "nequip",
                "dpa3",
                "orb",
                "mattersim",
                "grace",
                "upet",
                "fairchem",
                "mace_omol",
            ),
            description="Arch:",
            layout=ipw.Layout(width="80%"),
        )

        self.model_type = tab_from_dict(ipw.Tab, tabs)

    def update_models(self, _: ipw.Button | None = None) -> None:
        """Update the list of available models."""
        if not self.model_cls:
            return
        qb = QueryBuilder()
        qb.append(self.model_cls, project=["label", "id"])

        models = qb.all()
        model_labels = [(f"{label or repr(label)}:{idx}", idx) for label, idx in models]
        self.model_from_node.options = model_labels

        if model_labels:
            self.model_from_node.value = model_labels[0]


if aiida_mlip is not None:
    from aiida_mlip.data.model import ModelData

    class AiiDAMlipModelSelect(ModelSelect[ModelData]):
        """Model selector for aiida-mlip."""

        def __init__(self, logspace: ipw.Output | None = None):
            super().__init__(model_cls=ModelData, logspace=logspace)
            assert self.model_cls

        def _load_from_uri(self, model_str: str, arch: str) -> NT:
            if model_str.startswith(("http", "ftp", "sftp")):
                model_uri = model_str
                self.logspace.append_stdout("Loading model from web...")
            else:
                model_pth = Path(model_str).absolute()
                self.logspace.append_stdout("Loading model from file...")

                if not model_pth.is_file():
                    raise ModelError(f"File ({model_str}) not found.")

                model_uri = model_pth.as_uri()

            try:
                mdl = self.model_cls.from_uri(model_uri, architecture=arch)
            except Exception as err:
                raise ModelError(f"Unable to load model from {model_uri}.") from err

            mdl.label = f"{arch}:{model_uri}"
            return mdl

        def _load_from_node(self, node: NT, arch: str) -> NT:
            return node

        def _load_from_local(self, node: SinglefileData, arch: str) -> NT:
            with node.open(None, "rb") as file:
                return self.model_cls(file, architecture=arch)

        def _try_load_model(self, arch: str) -> tuple[str, NT]:

            typ = self.model_type.get_title(self.model_type.selected_index)

            match typ:
                case "From URI":
                    mdl = self._load_from_uri(self.model_from_uri.value, arch)
                case "AiiDA Database":
                    mdl = self._load_from_node(self.model_from_node.data_object, arch)
                case "From Local":
                    mdl = self._load_from_local(
                        self.model_from_local.get_aiida_file_object(), arch
                    )

            return arch, mdl
