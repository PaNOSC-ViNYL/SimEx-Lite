.. currentmodule:: SimExLite
===========
Package API
===========
This page lists main classes in this package.

Calculator API
~~~~~~~~~~~~~~
``Calculator`` classes.

SourceCalculators
-----------------
X-ray source calculators

.. autosummary::
   :toctree: generated/

   SourceCalculators.GaussianSourceCalculator
   SourceCalculators.PhenomSourceCalculator

PropagationCalculators
----------------------
Wave propagation calculators

.. autosummary::
   :toctree: generated/

   PropagationCalculators.WPGPropagationCalculator

PMICalculators
----------------------
Photon-matter-interaction calculators

.. autosummary::
   :toctree: generated/

   PMICalculators.SimpleScatteringPMICalculator
   
DiffractionCalculators
----------------------
X-ray diffraction calculators

.. autosummary::
   :toctree: generated/

   DiffractionCalculators.SingFELDiffractionCalculator
   DiffractionCalculators.CrystfelDiffractionCalculator

Data API
~~~~~~~~
``Data`` classes and related ``DataFormat`` classes. 

SampleData
----------------------

.. autosummary::
   :toctree: generated/

   SampleData.SampleData
   SampleData.ASEFormat


DiffractionData
----------------------

.. autosummary::
   :toctree: generated/

   DiffractionData.DiffractionData
   DiffractionData.SingFELFormat
   DiffractionData.EMCFormat
