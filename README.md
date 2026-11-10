# alc-aiidalab-widgets

[![Release](https://img.shields.io/github/v/release/stfc/alc-aiidalab-widgets)](https://github.com/stfc/alc-aiidalab-widgets/releases)
[![PyPI](https://img.shields.io/pypi/v/alc-aiidalab-widgets)](https://pypi.org/project/alc-aiidalab-widgets/)

[![Pipeline Status](https://github.com/stfc/alc-aiidalab-widgets/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/stfc/alc-aiidalab-widgets/actions)
[![Docs status](https://github.com/stfc/alc-aiidalab-widgets/actions/workflows/docs.yml/badge.svg?branch=main)](https://stfc.github.io/alc-aiidalab-widgets/)
[![Coverage Status]( https://coveralls.io/repos/github/stfc/alc-aiidalab-widgets/badge.svg?branch=main)](https://coveralls.io/github/stfc/alc-aiidalab-widgets?branch=main)

[![DOI](https://zenodo.org/badge/1246461744.svg)](https://doi.org/10.5281/zenodo.21223179)

This is a collection of commonly used widgets used across AiiDAlab plugins developed by
the Ada Lovelace Centre (STFC). It provides re-usable components and consistent styling
which can be deployed to any new or developing AiiDAlab plugin.

## Quick Start

Install the package via pip. Some widgets rely on optional extras to keep the base
install lightweight — add `[pseudo]` for `PseudoManagerWidget` (requires `aiida-pseudo`)
and/or `[magnetic]` for magnetic structure support in `StructureViewWidget` (requires
`pymatgen`).

``` sh
pip install alc-aiidalab-widgets
```

Widgets are imported from the `alc_aiidalab_widgets.widgets` subpackage and used like
any other [ipywidgets](https://ipywidgets.readthedocs.io/) widget — most naturally in a
Jupyter notebook or an AiiDAlab app:

``` python
from alc_aiidalab_widgets.widgets import Status, StructureViewWidget
import ipywidgets as ipw

structure_node = ...  # an AiiDA StructureData, TrajectoryData or SinglefileData node

status = Status()
viewer = StructureViewWidget(node=structure_node)
ipw.VBox([status, viewer])
```

AiiDAlab apps can also route AiiDA nodes to the right widget automatically by merging
this package's viewer mapping into `aiidalab-widgets-base`'s own:

``` python
from aiidalab_widgets_base.viewers import AIIDA_VIEWER_MAPPING, viewer
from alc_aiidalab_widgets.viewers import ALC_AIIDA_VIEWER_MAPPING

AIIDA_VIEWER_MAPPING.update(ALC_AIIDA_VIEWER_MAPPING)
widget = viewer(structure_node)  # resolves to StructureViewWidget automatically
```

See the [full documentation](https://stfc.github.io/alc-aiidalab-widgets/) for a
description of every widget, the viewer-routing mechanism, and the complete API
reference.

## For Developers

### Style Checking

This package uses pre-commit hooks to check for style consistency, to use these the ``pre-commit`` tool is required.
This can be installed alongside the base package by running,

``` sh
pip install .[dev]
```

or separately via,

``` sh
pip install pre-commit 
```

Once installed run,

``` sh
pre-commit install 
```

in the base repository to enable the pre-commit hooks.
This will now run style and formatting checks on every commit.

### Testing

This package uses [pytest](https://docs.pytest.org/en/stable/)
to run all unit tests which is included in the ```[dev]``` optional
package dependencies. Once installed it can be run from the project root directory.
The CI workflows are configured to ensure all tests pass
before a pull request can be accepted into the main repository.
It is important that any new additions to the code base are accompanied
by appropriate testing, maintaining a high code coverage. The coverage
can be checked via,

``` sh
pytest --cov=aiidalab_alc 
```

### Documentation

The documentation, including a User Guide, Developer Guide and an API reference,
is built using [sphinx](https://www.sphinx-doc.org/). The source
for which is contained in the ```docs/``` directory. At present
only the html generator has been fully tested. All required packages can
be installed alongside the core package via,

``` sh
pip install .[docs]
```

and then the documentation can be built using sphinx-build,

``` sh
sphinx-build -b html docs/src/ docs/build/html 
```

from the root directory.

## License

[BSD 3-Clause License](LICENSE)

## Funding

Contributors to this project were funded by

<div align="center">
    <a href="https://adalovelacecentre.ac.uk/">
        <img src="images/alc.svg" alt="ALC Logo" style="width: 30%">
    </a>
</div>
