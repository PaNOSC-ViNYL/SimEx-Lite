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

To test the latest updates, try the way of installation for developing below.  

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
1. Enable the `testFiles` submodule.

.. code-block:: bash

    $ git submodule init
    $ git submodule update

2. Run the test

.. code-block:: bash

    $ pytest .


Features
--------

* Provide the python interface of calculators for the SIMEX platform.
    * SourceCalculators
    * PropagationCalculators
    * PMICalculators (PhotonMattterInteractionCalculators)
    * DiffractionCalculators
    * DetectorClaculators
* Provide data APIs for different data formats.
    * PMI (Photon matter interaction) Data
    * Wavefront data
    * Diffraction data

Citation
--------
Please cite the following paper if you use SimEx-Lite for your research:

**E, J. et al. SimEx-Lite: easy access to start-to-end simulation for experiments at advanced light sources. in Advances in Computational Methods for X-Ray Optics VI (eds. Chubar, O. & Tanaka, T.) 22 (SPIE, San Diego, United States, 2023).** `doi.org/10.1117/12.2677299 <https://doi.org/10.1117/12.2677299>`_ 

Publications using SIMEX platform
------------
1. E, J. et al. SimEx-Lite: easy access to start-to-end simulation for experiments at advanced light sources. in Advances in Computational Methods for X-Ray Optics VI (eds. Chubar, O. & Tanaka, T.) 22 (SPIE, San Diego, United States, 2023). doi:10.1117/12.2677299.
2. E, J. et al. Water layer and radiation damage effects on the orientation recovery of proteins in single-particle imaging at an X-ray free-electron laser. Sci Rep 13, 16359 (2023).
3. E, J. et al. Expected resolution limits of x-ray free-electron laser single-particle imaging for realistic source and detector properties. Structural Dynamics 9, 064101 (2022).
4. E, J. et al. Effects of radiation damage and inelastic scattering on single-particle imaging of hydrated proteins with an X-ray Free-Electron Laser. Sci Rep 11, 17976 (2021).
5. E, J. et al. VINYL: The VIrtual Neutron and x-raY Laboratory and its applications. in Advances in Computational Methods for X-Ray Optics V (eds. Sawhney, K. & Chubar, O.) 33 (SPIE, Online Only, United States, 2020). doi:10.1117/12.2570378.
6. Fortmann-Grote, C. et al. Start-to-end simulation of single-particle imaging using ultra-short pulses at the European X-ray Free-Electron Laser. IUCrJ 4, 560–568 (2017).
7. Fortmann-Grote, C. et al. Simulations of ultrafast x–ray laser experiments. in Advances in X-ray Free-Electron Lasers Instrumentation IV (eds. Tschentscher, T. & Patthey, L.) 102370S (Prague, Czech Republic, 2017). doi:10.1117/12.2270552.
8. Fortmann-Grote, C. et al. SIMEX: Simulation of Experiments at Advanced Light Sources. arXiv:1610.05980 [physics] (2016).
9. Yoon, C. H. et al. A comprehensive simulation framework for imaging single particles and biomolecules at the European X-ray Free-Electron Laser. Scientific Reports 6, 24791 (2016).

Acknowledgement
---------------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

This project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No. 823852.

