import h5py
import numpy as np
from libpyvinyl.BaseFormat import BaseFormat
from extra_geom import GenericGeometry
from extra_geom.base import DetectorGeometryBase
from SimExLite.utils.io import parseIndex
from SimExLite.PhotonBeamData import SimpleBeam
from .EMCFormat import writeEMCGeom


class CondorFormat(BaseFormat):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def format_register(self):
        key = "condor"
        description = "Condor format for DiffractionData"
        file_extension = ".h5"
        read_kwargs = ["index"]
        write_kwargs = [""]
        return self._create_format_register(
            key, description, file_extension, read_kwargs, write_kwargs
        )

    @staticmethod
    def direct_convert_formats():
        # Assume the format can be converted directly to the formats supported by these classes:
        # AFormat, BFormat
        # Redefine this `direct_convert_formats` for a concrete format class
        return []

    @classmethod
    def read(cls, filename: str, index=None) -> dict:
        """Read the data from the file with the `filename` to a dictionary."""
        data_dict = {}

        index = parseIndex(index)

        arr_size = len(range(getPatternTotal(filename))[index])
        pattern_shape = getPatternShape(filename)
        if arr_size < 1e9:
            arr = np.zeros((arr_size, pattern_shape[0], pattern_shape[1]))
        else:
            arr = np.memmap(
                "memmap.dat",
                dtype="float16",
                mode="w+",
                shape=(arr_size, pattern_shape[0], pattern_shape[1]),
            )
        # quaternions = np.zeros((arr_size, 4))
        with h5py.File(filename, "r") as h5:
            arr[:] = h5["patterns"][index]
            distance = h5["detectorDistance"][()]

        params = getParameters(filename)
        geom, pixel_mask = params2extra_geom(params["geom"])
        beam = params2SimpleBeam(params["beam"])

        data_dict["img_array"] = arr
        # TODO: Convert rotation angles to quaternions.
        data_dict["quaternions"] = None
        data_dict["geom"] = geom
        data_dict["distance"] = distance
        # good_pixel = 1, bad_pixel = 0.
        data_dict["pixel_mask"] = pixel_mask
        data_dict["beam"] = beam

        return data_dict

    @classmethod
    def write(cls, object, filename: str, arr_poisson=None, key: str = None):
        """Save the data with the `filename`."""
        data_dict = object.get_data()
        # method_desciption = "Written by SimEx-Lite"
        geom = extra_geom2params(data_dict["geom"], data_dict["distance"])
        beam = BeamData2params(data_dict["beam"])

        write_condor(
            filename,
            arr=data_dict["img_array"],
            geom=geom,
            beam=beam,
        )

        if key is None:
            original_key = object.key
            key = original_key + "_to_CondorFormat"
        return object.from_file(filename, cls, key)

    @staticmethod
    def to_emc_geom(in_fn: str, out_fn: str, stoprad: float):
        """Write the Condor geom in EMC geom H5 format

        :param in_fn: input filename
        :type in_fn: str
        :param out_fn: output filename
        :type out_fn: str
        :param stoprad: beamstop radius in pixels
        :type stoprad: float
        """
        return to_emc_geom(in_fn=in_fn, out_fn=out_fn, stoprad=stoprad)


def getPatternShape(filename):
    """Get the shape of a diffraction pattern in the hdf5 file"""
    with h5py.File(filename, "r") as h5:
        return h5["patterns"][0].shape


def getPatternTotal(filename):
    """Get the total number of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, "r") as h5:
        npattern = len(h5["patterns"])
    return npattern


def getParameters(filename):
    """Get a dictionary of the beam parameters and geometry parameters in a condor
    HDF5 file.
    """

    # Setup return dictionary.
    parameters_dict = {"beam": {}, "geom": {}}
    beam = parameters_dict["beam"]
    geom = parameters_dict["geom"]

    # Open file.
    with h5py.File(filename, "r") as h5:
        # Beam parameters
        beam["fluence"] = h5["fluence"][()]
        beam["photonEnergy"] = h5["photonEnergy"][()]
        # Geometry parameters
        # The data in patterns is after binning
        geom["pixelSize"] = h5["pixelSize"][()] * h5["binning"][()]
        geom["distance"] = h5["detectorDistance"][()]
        geom["mask"] = np.ones_like(h5["patterns"][0])
    return parameters_dict


def params2extra_geom(geom_params):
    # The geometry dict from the file
    pixel_size = geom_params["pixelSize"]
    mask = geom_params["mask"]
    center_pixel = (np.array(mask.shape)) / 2
    corner_coordinates = -center_pixel * pixel_size
    corner_coordinates = np.append(corner_coordinates, 0)
    simple_config = {
        "pixel_size": pixel_size,
        "slow_pixels": mask.shape[0],
        "fast_pixels": mask.shape[1],
        "corner_coordinates": [corner_coordinates],
        "ss_vec": np.array([0, 1, 0]),
        "fs_vec": np.array([1, 0, 0]),
    }
    geom = GenericGeometry.from_simple_description(**simple_config)
    pixel_mask = geom_params["mask"]
    return geom, pixel_mask


def params2SimpleBeam(beam_params):
    # Unit of the fluence is mJ/um^2
    pulse_energy = beam_params["fluence"] * 1e-3  # in Joule unit
    focus_area = 1e-12  # um^2 -> m^2
    photon_energy = beam_params["photonEnergy"]
    beam = SimpleBeam(
        photon_energy=photon_energy, focus_area=focus_area, pulse_energy=pulse_energy
    )
    return beam


def extra_geom2params(geom: DetectorGeometryBase, distance):
    if geom.n_modules != 1:
        raise ValueError("Condor can only deal with single-module geometry.")
    # extra_geom only deals with square pixel yet.
    pixel_size = geom.pixel_size
    geom_param = {"distance": distance, "pixelSize": pixel_size}
    return geom_param


def BeamData2params(beam: SimpleBeam):
    focus_area = beam.get_focus_area().magnitude
    photon_energy = beam.get_photon_energy().magnitude
    beam_param = {"focusArea": focus_area, "photonEnergy": photon_energy}
    return beam_param


def write_condor(
    filename,
    arr,
    geom,
    beam,
    quaternions=None,
):
    """
    Save pattern arrays as pysingfel diffraction data.

    :param filename: Output filename.
    :type filename: string
    :param arr_counts: The array of photon counting patterns after adding Poisson noise.
    :type arr_counts: `np.array`
    :param arr_intensity: The array of original diffraction patterns.
    :type arr_intensity: `np.array`
    :param quaternions: The list of the quaternion with which each diffraction pattern was generated.
    :type quaternions: list-like
    :param det: The dictionary of detector parameters.
    :type det: dict
    :param beam: The dictionary of beam parameters.
    :type beam: dict
    :param pmi_file_list: The list of the corresponding pmi output file of each diffraction pattern.
    :type pmi_file_list: list
    """
    # Method Description
    with h5py.File(filename, "a") as f:
        f["binning"] = 1
        f["detectorDistance"] = geom["distance"]
        f["pixelSize"] = geom["pixelSize"]
        f["pixelSize"].attrs[
            "Pixel Size"
        ] = "Physical pixel size in m. Effective pixle size= (Physical pixel size)*binning"
        f["photonEnergy"] = beam["photonEnergy"]  # eV
        f["photonEnergy"].attrs["Photon Energy"] = "Photon Energy in eV"
        # No pulse energy in standard DiffractionData defined.
        # f["fluence"] = (beam["pulseEnergy"] * 1e3) / (
        #     beam["focusArea"] * 1e12
        # )  # mJ/um^2
        # f["fluence"].attrs["Fluence"] = "Incident fluence in mJ/um^2"
        # TODO: angle and direction convert
        # f["angle"] = None
        # f["direction"] = None
        f["patterns"] = arr


def to_emc_geom(in_fn: str, out_fn: str, stoprad: float):
    """Write the Condor geom in EMC geom H5 format

    :param in_fn: input filename
    :type in_fn: str
    :param out_fn: output filename
    :type out_fn: str
    :param stoprad: beamstop radius in pixels
    :type stoprad: float
    """
    # Reference: https://github.com/JunCEEE/Dragonfly/blob/8e9075818f00f5d2c45756d2b98803509be67cf0/utils/convert/geomtodet.py#L23
    params = getParameters(in_fn)
    geom = params["geom"]
    beam = params2SimpleBeam(params["beam"])
    # Sample to detector distance
    det_dist = geom["distance"] * 1e3  # millimeter
    # width number of pixels
    dets_x = geom["mask"].shape[1]
    # height number of pixels
    dets_y = geom["mask"].shape[0]
    # pixel size
    pix_size = geom["pixelSize"] * 1e3  # milimeter
    # wavelength
    in_wavelength = beam.get_wavelength(unit="angstrom")
    # ewald_rad definition: https://github.com/duaneloh/Dragonfly/wiki/Configuration-parameters-for-experimental-data#parameters-

    writeEMCGeom(out_fn, det_dist, dets_x, dets_y, pix_size, in_wavelength, stoprad)
