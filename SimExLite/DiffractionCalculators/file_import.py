# https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package
# try:
#     import importlib.resources as pkg_resources
# except ImportError:
#     # Try backported to PY<37 `importlib_resources`.
#     import importlib_resources as pkg_resources
import pkg_resources

from SimExLite.DiffractionCalculators import convert_to_cxi

my_name = pkg_resources.resource_filename("convert_to_cxi", "detector_sim.geom")
print(my_name)