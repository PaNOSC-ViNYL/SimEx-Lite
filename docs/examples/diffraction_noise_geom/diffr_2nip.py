from SimExLite.DiffractionCalculators import SingFELPDBDiffractionCalculator
from SimExLite.PhotonBeamData import SimpleBeam
from SimExLite.SampleData import SampleData, ASEFormat

beam_data = SimpleBeam(
    photons_per_pulse=4e12,
    photon_energy=6000, # eV
    beam_size=[228e-9, 228e-9] # meter
)

sample_data = SampleData.from_file("2nip.pdb", ASEFormat, "sample")
# xyz_data = sample_data.write("4V7V.xyz", ASEFormat)

diffraction = SingFELPDBDiffractionCalculator(
    name="LargeD",
    output_filenames="diffr",
    input=[beam_data, sample_data],
    calculator_base_dir="LargeD")
diffraction.parameters["number_of_diffraction_patterns"] = 5
diffraction.parameters["pixels_x"] = 273
diffraction.parameters["pixels_y"] = 314
diffraction.parameters["pixel_size"] = 800e-6 # 4X binning
diffraction.parameters["distance"] = 0.4
diffraction.parameters["clean_previous_run"] = True
diffraction.parameters["uniform_rotation"] = True
print(diffraction.parameters)


diffraction.backengine()
