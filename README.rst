==========
Quickstart
==========


.. image:: https://img.shields.io/pypi/v/SimEx-Lite.svg
        :target: https://pypi.python.org/pypi/SimEx-Lite

.. image:: https://travis-ci.com/PaNOSC-ViNYL/SimEx-Lite.svg?branch=main
        :target: https://travis-ci.com/PaNOSC-ViNYL/SimEx-Lite

.. image:: https://readthedocs.org/projects/simex-lite/badge/?version=latest
        :target: https://SimEx-Lite.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




SimEx-Lite is the core package of the SIMEX platform providing the calculator interfaces and data APIs.


* Free software: GNU General Public License v3
* Documentation: https://SimEx-Lite.readthedocs.io
* GitHub: https://github.com/PaNOSC-ViNYL/SimEx-Lite


Installing
----------
SimEx-Lite can be installed with Python 3.6 or later:

.. code-block:: bash

    $ pip install SimEx-Lite

Developing
----------
We encourage everyone to contribute to SimEx. For a detailed guide, please visit
https://simex-lite.readthedocs.io/en/latest/contributing.html

1. Clone this Github repository:

.. code-block:: bash

   $ git clone --recursive git@github.com:PaNOSC-ViNYL/SimEx-Lite.git

2. Install the package locally:

.. code-block:: bash

    $ cd SimEx-Lite
    $ pip install -e .

Tests
-----
1. Download the testing files.

.. code-block:: bash

    $ cd tests
    $ git clone https://github.com/PaNOSC-ViNYL/SimEx-Lite-testFiles testFiles

2. Run the test

.. code-block:: bash

    $ pytest .


Features
--------

* Provide the python interface of calculators for the SIMEX platform.
    * PhotonSourceCalculator
    * PhotonPropagationCalculator
    * PhotonMattterInteractor
    * DiffractionCalculator
    * DetectorClaculator
* Provide data APIs for different data formats.
    * Photon beam data
    * Photon matter interaction Data
    * Diffraction data

Acknowledgement
---------------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No. 823852.

