"""Widgets for managing pseudopotential families through aiida-pseudo."""

from __future__ import annotations

import logging
import tempfile
import threading
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

import ipywidgets as ipw
from traitlets import Int

from alc_aiidalab_widgets.utils import tab_from_dict
from alc_aiidalab_widgets.widgets.loading import LoadingWidget

# from alc_aiidalab_widgets.widgets.mesages import MessageBox  # uninstall, see below
from alc_aiidalab_widgets.widgets.status import Status

try:
    import aiida_pseudo
except ImportError:
    aiida_pseudo = None


if aiida_pseudo is not None:
    import requests

    # from aiida.orm import Group  # uninstall, see below
    from aiida.orm import QueryBuilder
    from aiida.plugins import DataFactory, GroupFactory
    from aiida.plugins.entry_point import get_entry_point_names
    from aiida_pseudo.cli.install import (
        download_pseudo_dojo,
        download_sssp,
        install_pseudo_dojo,
        install_sssp,
    )
    from aiida_pseudo.cli.utils import create_family_from_archive
    from aiida_pseudo.data.pseudo import JthXmlData, PsmlData, Psp8Data, UpfData
    from aiida_pseudo.groups.family import (
        PseudoDojoConfiguration,
        PseudoDojoFamily,
        PseudoPotentialFamily,
        SsspConfiguration,
        SsspFamily,
    )

    PSEUDO_DOJO_FORMAT_TYPES = {
        "jthxml": JthXmlData,
        "psp8": Psp8Data,
        "psml": PsmlData,
        "upf": UpfData,
    }

    @contextmanager
    def _capture_verdi_log():
        """Temporarily capture messages logged by aiida-pseudo's CLI helpers."""
        logger = logging.getLogger("verdi")
        records: list[str] = []

        class _ListHandler(logging.Handler):
            """Logging handler that appends formatted messages to a list."""

            def emit(self, record: logging.LogRecord) -> None:
                """Append the record's message to the shared list."""
                records.append(record.getMessage())

        handler = _ListHandler()
        previous_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(1)
        try:
            yield records
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

    def _read_file_upload(upload: ipw.FileUpload) -> tuple[str, bytes]:
        """Extract the filename and content from a ``FileUpload`` widget's value."""
        try:
            key = next(iter(upload.value.keys()))
            name = upload.value[key]["metadata"]["name"]
            return name, upload.data[0]
        except AttributeError:
            entry = upload.value[0]
            return entry["name"], bytes(entry["content"])

    class PseudoFamilyListWidget(ipw.VBox):
        """Widget listing the pseudopotential families currently installed."""

        TABLE_STYLE = """
        <style>
        .pseudo-family-table {border-collapse: collapse; width: 100%;}
        .pseudo-family-table, .pseudo-family-table th, .pseudo-family-table td {
            border: 1px solid #ddd;
        }
        .pseudo-family-table th, .pseudo-family-table td {
            padding: 6px 10px; text-align: left;
        }
        .pseudo-family-table tr:nth-child(odd) {background-color: #f9f9f9;}
        </style>
        """

        def __init__(self, **kwargs):
            """PseudoFamilyListWidget constructor."""
            self.refresh_btn = ipw.Button(
                description="Refresh",
                button_style="info",
                tooltip="Refresh the list of installed pseudopotential families",
                icon="refresh",
                layout={"width": "auto"},
            )
            self.refresh_btn.on_click(self.refresh)

            # NOTE: Uninstalling only removes the `Group`, not the underlying pseudo
            # data nodes (which may be shared with other families), so this has been
            # disabled for now rather than risk a misleading "uninstall". Re-enable
            # once orphaned-pseudo cleanup is implemented.
            # self.delete_select = ipw.Dropdown(
            #     description="Family:",
            #     layout={"width": "60%"},
            #     style={"description_width": "80px"},
            # )
            # self.delete_btn = ipw.Button(
            #     description="Uninstall",
            #     button_style="danger",
            #     tooltip="Remove the selected family from the database",
            #     icon="trash",
            #     layout={"width": "auto"},
            # )
            # self.delete_btn.on_click(self._confirm_delete)

            self.table = ipw.HTML()
            self.status = Status()
            # self._confirm_box = ipw.VBox([])

            super().__init__(
                children=[
                    ipw.HBox([self.refresh_btn]),
                    self.table,
                    # ipw.HBox([self.delete_select, self.delete_btn]),
                    # self._confirm_box,
                    self.status,
                ],
                **kwargs,
            )
            self.refresh()

        @staticmethod
        def _families() -> list[PseudoPotentialFamily]:
            """Query all installed pseudopotential families."""
            query = QueryBuilder().append(PseudoPotentialFamily)
            return [family for (family,) in query.iterall()]

        def refresh(self, _=None) -> None:
            """Refresh the table of installed pseudopotential families."""
            self.status.clear()
            families = sorted(self._families(), key=lambda family: family.label)

            if not families:
                self.table.value = (
                    "<p>No pseudopotential families are currently installed.</p>"
                )
                # self.delete_select.options = []
                return

            rows = "".join(
                f"<tr><td>{family.label}</td><td>{family.type_string}</td>"
                f"<td>{family.count()}</td><td>{family.description}</td></tr>"
                for family in families
            )
            self.table.value = (
                self.TABLE_STYLE + "<table class='pseudo-family-table'>"
                "<thead><tr><th>Label</th><th>Type</th><th>Elements</th>"
                "<th>Description</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            )
            # self.delete_select.options = [family.label for family in families]

        # def _confirm_delete(self, _) -> None:
        #     """Ask the user to confirm removal of the selected family."""
        #     if not self.delete_select.value:
        #         return
        #
        #     self.delete_btn.disabled = True
        #     message_box = MessageBox(
        #         f"Are you sure you want to uninstall '{self.delete_select.value}'? "
        #         "The underlying pseudopotential files will not be deleted, only the "
        #         "family grouping."
        #     )
        #     message_box.observe(self._on_delete_decision, "state")
        #     self._confirm_box.children = [message_box]
        #
        # def _on_delete_decision(self, change: dict) -> None:
        #     """Handle the user's decision on deleting the selected family."""
        #     self._confirm_box.children = []
        #     self.delete_btn.disabled = False
        #
        #     if not change["new"]:
        #         return
        #
        #     label = self.delete_select.value
        #     family = (
        #         QueryBuilder()
        #         .append(PseudoPotentialFamily, filters={"label": label})
        #         .one()[0]
        #     )
        #     Group.collection.delete(family.pk)
        #     self.status.success(f"Uninstalled '{label}'.")
        #     self.refresh()

    def _install_sssp_configuration(
        configuration: SsspConfiguration, archive: Path, metadata: Path, label: str
    ) -> None:
        """Install a downloaded SSSP configuration via the generic panel API."""
        install_sssp(archive, metadata, label)

    def _install_pseudo_dojo_configuration(
        configuration: PseudoDojoConfiguration,
        archive: Path,
        metadata: Path,
        label: str,
    ) -> None:
        """Install a downloaded PseudoDojo configuration via the generic API."""
        pseudo_type = PSEUDO_DOJO_FORMAT_TYPES[configuration.pseudo_format]
        family = install_pseudo_dojo(
            configuration, archive, metadata, pseudo_type, label
        )
        family.set_default_stringency("normal")

    class _ConfigurationInstallPanel(ipw.VBox):
        """Generic panel for installing a versioned pseudopotential family.

        Subclasses (or callers) provide the family class together with the
        download/install functions and archive filename suffixes that are specific
        to that pseudopotential source (e.g. SSSP or PseudoDojo).
        """

        def __init__(
            self,
            on_installed: Callable[[str], None],
            *,
            family_class: type[PseudoPotentialFamily],
            display_name: str,
            download: Callable[[object, Path, Path], None],
            install: Callable[[object, Path, Path, str], None],
            archive_suffix: str = ".tar.gz",
            metadata_suffix: str = ".json",
            **kwargs,
        ):
            """_ConfigurationInstallPanel constructor."""
            self._on_installed = on_installed
            self._family_class = family_class
            self._download = download
            self._install_configuration = install
            self._archive_suffix = archive_suffix
            self._metadata_suffix = metadata_suffix

            options = [
                (str(cfg), cfg) for cfg in reversed(family_class.valid_configurations)
            ]
            self.configuration = ipw.Dropdown(
                options=options,
                value=options[0][1],
                description="Configuration:",
                style={"description_width": "120px"},
                layout={"width": "80%"},
            )
            self.install_btn = ipw.Button(
                description="Install",
                button_style="success",
                tooltip=f"Download and install the selected {display_name} config",
                icon="download",
                layout={"width": "auto"},
            )
            self.install_btn.on_click(self._install)
            self.status = Status()
            self._progress_box = ipw.VBox([])

            super().__init__(
                children=[
                    ipw.HBox([self.configuration, self.install_btn]),
                    self._progress_box,
                    self.status,
                ],
                **kwargs,
            )

        def _install(self, _=None) -> None:
            """Install the currently selected configuration."""
            configuration = self.configuration.value
            label = self._family_class.format_configuration_label(configuration)

            self.status.clear()
            query = QueryBuilder().append(self._family_class, filters={"label": label})
            if query.first():
                self.status.warning(f"'{label}' is already installed.")
                return

            self.install_btn.disabled = True
            self._progress_box.children = [
                LoadingWidget(message=f"Installing {label}, this can take a while...")
            ]
            thread = threading.Thread(
                target=self._run_install, args=(configuration, label), daemon=True
            )
            thread.start()

        def _run_install(self, configuration, label: str) -> None:
            """Download and install the configuration in a background thread."""
            log_records: list[str] = []
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    dirpath = Path(tmp)
                    archive = dirpath / f"archive{self._archive_suffix}"
                    metadata = dirpath / f"metadata{self._metadata_suffix}"
                    with _capture_verdi_log() as log_records:
                        self._download(configuration, archive, metadata)
                        self._install_configuration(
                            configuration, archive, metadata, label
                        )
            except SystemExit as exc:
                message = "; ".join(log_records) or (
                    f"Installation failed (exit code {exc.code})."
                )
                self._finish(False, message)
            except Exception as exc:  # noqa: BLE001
                self._finish(False, str(exc))
            else:
                self._finish(True, f"Installed '{label}'.")

        def _finish(self, success: bool, message: str) -> None:
            """Report the result of an install attempt back to the widget."""
            self._progress_box.children = []
            self.install_btn.disabled = False
            if success:
                self.status.success(message)
                self._on_installed(message)
            else:
                self.status.failure(message)

    class _SsspInstallPanel(_ConfigurationInstallPanel):
        """Panel for installing an SSSP pseudopotential family configuration."""

        def __init__(self, on_installed: Callable[[str], None], **kwargs):
            """_SsspInstallPanel constructor."""
            super().__init__(
                on_installed,
                family_class=SsspFamily,
                display_name="SSSP",
                download=download_sssp,
                install=_install_sssp_configuration,
                archive_suffix=".tar.gz",
                metadata_suffix=".json",
                **kwargs,
            )

    class _PseudoDojoInstallPanel(_ConfigurationInstallPanel):
        """Panel for installing a PseudoDojo pseudopotential family configuration."""

        def __init__(self, on_installed: Callable[[str], None], **kwargs):
            """_PseudoDojoInstallPanel constructor."""
            super().__init__(
                on_installed,
                family_class=PseudoDojoFamily,
                display_name="PseudoDojo",
                download=download_pseudo_dojo,
                install=_install_pseudo_dojo_configuration,
                archive_suffix=".tgz",
                metadata_suffix=".tgz",
                **kwargs,
            )

    class _CustomFamilyInstallPanel(ipw.VBox):
        """Panel for installing a pseudopotential family from a custom archive."""

        def __init__(self, on_installed: Callable[[str], None], **kwargs):
            """_CustomFamilyInstallPanel constructor."""
            self._on_installed = on_installed

            data_entry_points = sorted(
                ep
                for ep in get_entry_point_names("aiida.data")
                if ep.startswith("pseudo")
            )
            group_entry_points = sorted(
                ep
                for ep in get_entry_point_names("aiida.groups")
                if ep.startswith("pseudo.family")
                and ep not in ("pseudo.family.sssp", "pseudo.family.pseudo_dojo")
            )

            self.label = ipw.Text(
                description="Label:",
                layout={"width": "80%"},
                style={"description_width": "120px"},
            )
            self.description = ipw.Text(
                description="Description:",
                layout={"width": "80%"},
                style={"description_width": "120px"},
            )
            self.pseudo_type = ipw.Dropdown(
                options=data_entry_points,
                value=(
                    "pseudo" if "pseudo" in data_entry_points else data_entry_points[0]
                ),
                description="Pseudo type:",
                layout={"width": "80%"},
                style={"description_width": "120px"},
            )
            self.family_type = ipw.Dropdown(
                options=group_entry_points,
                value=(
                    "pseudo.family"
                    if "pseudo.family" in group_entry_points
                    else group_entry_points[0]
                ),
                description="Family type:",
                layout={"width": "80%"},
                style={"description_width": "120px"},
            )
            self.archive_upload = ipw.FileUpload(
                description="Upload archive",
                multiple=False,
                layout={"width": "auto"},
            )
            self.archive_url = ipw.Text(
                description="...or URL:",
                placeholder="https://example.com/archive.tar.gz",
                layout={"width": "80%"},
                style={"description_width": "120px"},
            )
            self.install_btn = ipw.Button(
                description="Install",
                button_style="success",
                tooltip="Install the pseudopotential family from the given archive",
                icon="download",
                layout={"width": "auto"},
            )
            self.install_btn.on_click(self._install)
            self.status = Status()
            self._progress_box = ipw.VBox([])

            super().__init__(
                children=[
                    self.label,
                    self.description,
                    self.pseudo_type,
                    self.family_type,
                    ipw.HBox([self.archive_upload, self.archive_url]),
                    self.install_btn,
                    self._progress_box,
                    self.status,
                ],
                **kwargs,
            )

        def _install(self, _=None) -> None:
            """Validate the form and install the custom pseudopotential family."""
            label = self.label.value.strip()
            self.status.clear()

            if not label:
                self.status.failure("A label is required.")
                return

            query = QueryBuilder().append(
                PseudoPotentialFamily, filters={"label": label}
            )
            if query.first():
                self.status.warning(f"A family named '{label}' already exists.")
                return

            if not self.archive_upload.value and not self.archive_url.value.strip():
                self.status.failure("Upload an archive or provide a URL.")
                return

            self.install_btn.disabled = True
            self._progress_box.children = [LoadingWidget(message="Installing...")]
            thread = threading.Thread(
                target=self._run_install, args=(label,), daemon=True
            )
            thread.start()

        def _resolve_archive(self, dirpath: Path) -> Path:
            """Make the archive to install available as a local file in ``dirpath``."""
            if self.archive_upload.value:
                name, content = _read_file_upload(self.archive_upload)
                filepath = dirpath / name
                filepath.write_bytes(content)
                return filepath

            url = self.archive_url.value.strip()
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            filepath = dirpath / (Path(url).name or "archive")
            filepath.write_bytes(response.content)
            return filepath

        def _run_install(self, label: str) -> None:
            """Install the pseudopotential family from the configured archive source."""
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    archive_path = self._resolve_archive(Path(tmp))
                    family_type = GroupFactory(self.family_type.value)
                    pseudo_type = DataFactory(self.pseudo_type.value)
                    family = create_family_from_archive(
                        family_type, label, archive_path, pseudo_type=pseudo_type
                    )
                    family.description = self.description.value
            except Exception as exc:  # noqa: BLE001
                self._finish(False, str(exc))
            else:
                count = family.count()
                self._finish(True, f"Installed '{label}' containing {count} pseudos.")

        def _finish(self, success: bool, message: str) -> None:
            """Report the result of an install attempt back to the widget."""
            self._progress_box.children = []
            self.install_btn.disabled = False
            if success:
                self.status.success(message)
                self._on_installed(message)
            else:
                self.status.failure(message)

    class PseudoFamilyInstallWidget(ipw.VBox):
        """Widget for installing SSSP, PseudoDojo or custom pseudopotential families."""

        installed = Int(0)

        def __init__(self, **kwargs):
            """PseudoFamilyInstallWidget constructor."""
            self._sssp = _SsspInstallPanel(self._notify_installed)
            self._pseudo_dojo = _PseudoDojoInstallPanel(self._notify_installed)
            self._custom = _CustomFamilyInstallPanel(self._notify_installed)

            tabs = tab_from_dict(
                ipw.Tab,
                {
                    "SSSP": self._sssp,
                    "PseudoDojo": self._pseudo_dojo,
                    "Custom": self._custom,
                },
            )
            super().__init__(children=[tabs], **kwargs)

        def _notify_installed(self, _message: str) -> None:
            """Bump the ``installed`` counter whenever a family is installed."""
            self.installed += 1

    class PseudoManagerWidget(ipw.VBox):
        """Widget for listing and installing pseudopotential families."""

        def __init__(self, **kwargs):
            """PseudoManagerWidget constructor."""
            self.list_widget = PseudoFamilyListWidget()
            self.install_widget = PseudoFamilyInstallWidget()
            self.install_widget.observe(self._on_installed, "installed")

            tabs = tab_from_dict(
                ipw.Tab,
                {
                    "Installed Families": self.list_widget,
                    "Install New Family": self.install_widget,
                },
            )
            super().__init__(children=[tabs], **kwargs)

        def _on_installed(self, _change: dict) -> None:
            """Refresh the list of installed families after a new one is installed."""
            self.list_widget.refresh()
