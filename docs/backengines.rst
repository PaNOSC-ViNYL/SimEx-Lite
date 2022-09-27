Backengine installation
=======================

This is a list of backengines for the implemented calculators and their installation instruction.

CrystFEL
--------
CrystFEL is required by :class:`SimExLite.DiffractionCalculators.CrystfelCalculator`.

Install CrystFEL
~~~~~~~~~~~~~~~~
The goal is to make ``gen-sfs`` and ``pattern_sim`` available in your ``$PATH``.

WPG
---
WPG is required by :class:`SimExLite.DiffractionCalculators.WPGPropagationCalculator`.

Install WPG
~~~~~~~~~~~

Clone the WPG repository wherever you like (e.g. /opt)

.. code-block:: bash

    cd /opt
    git clone https://github.com/samoylv/WPG.git

build WPG in your SimExLite environment

.. code-block:: bash
    
    cd WPG
    make

Set WPG PATH by adding this to your `.bashrc` or `.zshrc`:

.. code-block:: bash
    
    # If the path where you cloned WPG is opt
    export PYTHONPATH=/opt/WPG:$PYTHONPATH

or adding these lines at the beginning of your python script:

.. code-block:: python

    import sys
    sys.path.insert(0,"/opt/WPG")
