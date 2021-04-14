from SimExLite.DiffractionData import DiffractionData
import SimExLite.DataAPI.EMCPhoton as EMC
from pathlib import Path
import subprocess

singfel_data_path = '../../../tests/testFiles/singfel-multi.h5'
diffr = DiffractionData(singfel_data_path)
emc_file = 't.emc'
diffr.createArray()

# Multiply this value to the array
diffr.multiply(1e8)

# Print geometry
print(diffr.beam.wavelength)
print(diffr.geometry.clen, 'm')
print(diffr.geometry.frag_ss_pixels)
print(diffr.geometry.pixel_size, 'm')
diffr.saveAs('emc', emc_file, with_geom=True)

# Write geometry files in CrystFEL and EMC format
path_geom = Path(emc_file).with_suffix('.geom')
subprocess.run([
    "../../../SimExLite/DataAPI/Dragonfly/utils/convert/geomtodet.py",
    str(path_geom)
])

# Plot one frame in .emc file
EMC.plotEMCPhoton(emc_file, idx=2, log_scale=True)
