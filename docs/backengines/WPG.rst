WPG
---
`WPG <https://wpg.readthedocs.io/en/latest/index.html>`_ is required by:

+--------------------------------------------------------------------+
| :class:`SimExLite.SourceCalculators.GaussianSourceCalculator`      |
+--------------------------------------------------------------------+
| :class:`SimExLite.PropagationCalculators.WPGPropagationCalculator` |
+--------------------------------------------------------------------+

Install WPG
~~~~~~~~~~~

Clone the WPG repository wherever you like (e.g. ``/opt``)

.. code-block:: bash

    cd /opt
    git clone -b simex https://github.com/JunCEEE/WPG.git

build WPG in your SimExLite environment

.. code-block:: bash
    
    cd WPG
    make

Set WPG PATH by adding this to your ``.bashrc`` or ``.zshrc``:

.. code-block:: bash
    
    # If the path where you cloned WPG is opt
    export PYTHONPATH=/opt/WPG:$PYTHONPATH

or adding these lines at the beginning of your python script:

.. code-block:: python

    import sys
    sys.path.insert(0,"/opt/WPG")
