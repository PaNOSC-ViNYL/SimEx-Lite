.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/PaNOSC-ViNYL/SimEx-Lite/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

SimEx-Lite could always use more documentation, whether as part of the
official SimEx-Lite docs, in docstrings, or even on the web in blog posts,
articles, and such.

To build to the official SimEx-Lite docs locally::

    $ cd SimEx-Lite/docs
    $ make html

Open ``_build/html/index.html`` to see the docs.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/PaNOSC-ViNYL/SimEx-Lite/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `SimEx-Lite` for local development.

1. Fork the `SimEx-Lite` repo on GitHub.
2. Clone your fork locally::

    $ git clone --recursive git@github.com:your_name_here/SimEx-Lite.git
    $ git config  user.email your-deveopment-email-address

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv SimEx-Lite
    $ cd SimEx-Lite/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the
   tests, including testing other Python versions with tox::

    $ git clone https://github.com/PaNOSC-ViNYL/SimEx-Lite-testFiles testFiles
    $ python setup.py test or pytest
    $ tox

   To get tox, just install them with :command:`pip`  into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.6, 3.7 and 3.8, and for PyPy. Check
   https://travis-ci.com/PaNOSC-ViNYL/SimEx-Lite/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ pytest tests.test_SimExLite


Deploying
---------

This is a reminder for the maintainers on how to deploy a new version to `PyPI <http://linkhttps://pypi.org/>`_. |br|
In order to :command:`bump2version`, please make sure:

- All your changes are committed.
- The documents in :file:`docs` are updated.
- The version description in :file:`HISTORY.rst` is updated.

bump2version
~~~~~~~~~~~~

Firstly do a dryrun to check if the files are ready for a release::

$ bump2version --dry-run --verbose patch # possible: major / minor / patch

Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.

Deploy to PyPI manually
~~~~~~~~~~~~~~~~~~~~~~~

When Travis CI is not working, one can deploy the package to PyPI manually.

1. Generate the package.::

    $ python setup.py bdist_wheel sdist

2. Test pushing to the testing pypi server.::

    $ twine upload --repository-url https://test.pypi.org/legacy/ dist/*

3. Push to the real pypi server.::

    $ twine check dist/*
    $ twine upload dist/*

.. |br| raw:: html

      <br>