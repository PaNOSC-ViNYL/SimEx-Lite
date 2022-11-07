=======
History
=======

1.1.0
------------------

* Add EMC format
* Add CXI format


1.0.0 (2022-09-27)
------------------

* Refactor based on `libpyvinyl <https://github.com/PaNOSC-ViNYL/libpyvinyl>`_.
* Support `instrument` class.
* Updated documents for backengines installation.

0.3.4 - 0.3.7 (2022-09-19)
--------------------------

* Support for the legacy `DiffractionData` class.

0.3.3 (2022-08-05)
------------------

* Fixed reading singfel rewrited data.
* Add chunk functions to `GaussianNoiseCalculator`.

0.3.2 (2021-10-20)
------------------

* Included utils as a subpackage.

0.3.1 (2021-09-29)
------------------

* Updated the interface of data APIs. Details at this `PR link <https://github.com/PaNOSC-ViNYL/SimEx-Lite/pull/4>`_.
* Updated the deployment guide for PyPI in `CONTRIBUTING <https://github.com/PaNOSC-ViNYL/SimEx-Lite/blob/main/CONTRIBUTING.rst>`_.

0.2.1 (2021-04-19)
------------------

* Deploy PyPI with Travis

0.2.0 (2021-04-17)
------------------

* Data API:
    * Added: PhotonBeamData.py
    * Added: SampleData.py
    * Added: DiffractionData.py
    * Added Singfel Diffraction data API
    * Added EMC photon data API

* Calculator:
    * Detector calculators:
        * Added Gaussian noise calculator

* Examples:
    * Added singfel2EMC data analysis example

0.1.0 (2021-02-24)
------------------

* First release on PyPI.
