"""Unit tests for the pseudos module."""

import io
import tarfile
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("aiida_pseudo")

from aiida.orm import QueryBuilder  # noqa: E402

from alc_aiidalab_widgets.widgets import pseudos  # noqa: E402

UPF_CONTENT = (
    '<UPF version="2.0.1">\n<PP_HEADER element="Si" z_valence="4.0" />\n</UPF>\n'
)


def _make_tar_archive(files: dict) -> bytes:
    """Build an in-memory tar.gz archive containing the given files."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def _install_dummy_family(label: str) -> "pseudos.PseudoPotentialFamily":
    """Install a bare-bones pseudopotential family through the aiida-pseudo API."""
    with tempfile.TemporaryDirectory() as tmp:
        dirpath = Path(tmp)
        (dirpath / "Si.UPF").write_bytes(b"dummy pseudo content")
        return pseudos.PseudoPotentialFamily.create_from_folder(
            dirpath, label, description="A test family"
        )


def _create_sssp_family(label: str) -> "pseudos.SsspFamily":
    """Install a bare-bones SsspFamily directly through the aiida-pseudo API."""
    with tempfile.TemporaryDirectory() as tmp:
        dirpath = Path(tmp)
        (dirpath / "Si.UPF").write_text(UPF_CONTENT)
        return pseudos.SsspFamily.create_from_folder(dirpath, label)


class _FakeResponse:
    """Minimal stand-in for a ``requests`` response."""

    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        """Pretend the request always succeeds."""


def test_pseudo_family_list_widget(aiida_profile):
    """Test listing installed pseudopotential families."""
    widget = pseudos.PseudoFamilyListWidget()
    assert "No pseudopotential families" in widget.table.value

    _install_dummy_family("dummy-family")
    widget.refresh()

    assert "dummy-family" in widget.table.value
    assert "A test family" in widget.table.value


def test_pseudo_family_install_widget_tabs():
    """Test that the install widget exposes SSSP, PseudoDojo and Custom tabs."""
    widget = pseudos.PseudoFamilyInstallWidget()
    tabs = widget.children[0]

    assert [tabs.get_title(i) for i in range(len(tabs.children))] == [
        "SSSP",
        "PseudoDojo",
        "Custom",
    ]
    assert len(widget._sssp.configuration.options) == len(
        pseudos.SsspFamily.valid_configurations
    )
    assert len(widget._pseudo_dojo.configuration.options) == len(
        pseudos.PseudoDojoFamily.valid_configurations
    )


def test_pseudo_manager_widget_refreshes_after_install(aiida_profile):
    """Test that the manager widget refreshes its list after an install is reported."""
    manager = pseudos.PseudoManagerWidget()
    assert "No pseudopotential families" in manager.list_widget.table.value

    _install_dummy_family("dummy-family")
    manager.install_widget.installed += 1

    assert "dummy-family" in manager.list_widget.table.value


def test_sssp_install_panel_already_installed(aiida_profile, monkeypatch):
    """Test that installing an already-present SSSP configuration only warns."""
    configuration = pseudos.SsspFamily.valid_configurations[0]
    label = pseudos.SsspFamily.format_configuration_label(configuration)
    _create_sssp_family(label)

    called = []
    monkeypatch.setattr(pseudos, "download_sssp", lambda *a, **k: called.append(True))

    installed = []
    panel = pseudos._SsspInstallPanel(installed.append)
    panel.configuration.value = configuration
    panel._install()

    assert not called
    assert not installed
    assert "already installed" in panel.status.value


def test_sssp_install_panel_success(aiida_profile, monkeypatch):
    """Test the SSSP install panel's success path."""
    configuration = pseudos.SsspFamily.valid_configurations[1]
    label = pseudos.SsspFamily.format_configuration_label(configuration)

    def fake_download_sssp(cfg, archive, metadata, traceback=False):
        archive.write_bytes(b"unused")
        metadata.write_text("{}")

    def fake_install_sssp(archive, metadata, lbl, description="", traceback=False):
        with tempfile.TemporaryDirectory() as tmp:
            dirpath = Path(tmp)
            (dirpath / "Si.UPF").write_text(UPF_CONTENT)
            pseudos.SsspFamily.create_from_folder(dirpath, lbl, description=description)

    monkeypatch.setattr(pseudos, "download_sssp", fake_download_sssp)
    monkeypatch.setattr(pseudos, "install_sssp", fake_install_sssp)

    installed = []
    panel = pseudos._SsspInstallPanel(installed.append)
    panel._run_install(configuration, label)

    assert installed
    assert "Installed" in panel.status.value
    query = QueryBuilder().append(pseudos.SsspFamily, filters={"label": label})
    assert query.count() == 1


def test_sssp_install_panel_failure():
    """Test the SSSP install panel's failure path."""
    configuration = pseudos.SsspFamily.valid_configurations[2]
    label = pseudos.SsspFamily.format_configuration_label(configuration)

    def fake_download_sssp(*_args, **_kwargs):
        raise RuntimeError("network unreachable")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(pseudos, "download_sssp", fake_download_sssp)

        installed = []
        panel = pseudos._SsspInstallPanel(installed.append)
        panel._run_install(configuration, label)

    assert not installed
    assert "network unreachable" in panel.status.value


def test_custom_family_install_panel_validation(aiida_profile):
    """Test the custom family install panel's input validation."""
    panel = pseudos._CustomFamilyInstallPanel(lambda _message: None)

    panel._install()
    assert "label is required" in panel.status.value.lower()

    panel.label.value = "custom-family"
    panel._install()
    assert "upload an archive or provide a url" in panel.status.value.lower()


def test_custom_family_install_panel_success(aiida_profile, monkeypatch):
    """Test the custom family install panel's success path using a URL source."""
    archive_bytes = _make_tar_archive({"Si.UPF": b"dummy pseudo content"})
    monkeypatch.setattr(
        pseudos.requests, "get", lambda url, timeout=30: _FakeResponse(archive_bytes)
    )

    installed = []
    panel = pseudos._CustomFamilyInstallPanel(installed.append)
    panel.label.value = "custom-family"
    panel.archive_url.value = "https://example.invalid/archive.tar.gz"
    panel._run_install("custom-family")

    assert installed
    assert "Installed 'custom-family'" in panel.status.value

    family = (
        QueryBuilder()
        .append(pseudos.PseudoPotentialFamily, filters={"label": "custom-family"})
        .one()[0]
    )
    assert family.count() == 1
    assert "Si" in family.elements
