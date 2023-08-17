
CrystFEL
--------
CrystFEL is required by :class:`SimExLite.DiffractionCalculators.CrystfelCalculator`.

Install Backengine
~~~~~~~~~~~~~~~~
The goal is to make ``sfall`` and ``pattern_sim`` available in your ``$PATH``.

``sfall`` is in CCP4, and ``pattern_sim`` is in CrystFEL (version<=0.10.1).

Install CCP4
============
Please follow the instruction at https://www.ccp4.ac.uk/download/.

Install CrystFEL
============
Please follow the instruction at `CrystFEL 0.10.1 Installation <https://gitlab.desy.de/thomas.white/crystfel/-/blob/3619f795/doc/articles/tutorial.rst>`_.
For different versions, please see https://www.desy.de/~twhite/crystfel/install.html.

On Maxwell
~~~~~~~~~~
CCP4 and CrystFEL are both available on the Maxwell cluster at DESY. They can loaded by:

.. code-block:: bash

    module load maxwell ccp4 crystfel/0.10.1

Tested versions
~~~~~~~~~~~~~~~
+----------+-----------------------+
|  Codes   |       Versions        |
+==========+=======================+
| CCP4     | 7.1                   |
+----------+-----------------------+
| CrystFEL | 0.9.1, 0.10.0, 0.10.1 |
+----------+-----------------------+