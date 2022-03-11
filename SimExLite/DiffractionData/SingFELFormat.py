import h5py
import numpy as np
from tqdm import tqdm
from libpyvinyl.BaseFormat import BaseFormat
from extra_geom import GenericGeometry
from extra_geom.base import DetectorGeometryBase
import SimExLite
from SimExLite.utils.io import parseIndex
from SimExLite.PhotonBeamData import SimpleBeam


class SingFELFormat(BaseFormat):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def format_register(self):
        key = "singfel"
        description = "Singfel format for DiffractionData"
        file_extension = ".h5"
        read_kwargs = ["index", "poissonize"]
        write_kwargs = ["ideal_arr"]
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
    def read(cls, filename: str, index=None, poissonize=False) -> dict:
        """Read the data from the file with the `filename` to a dictionary. If poissonize=True,
        it will read the poissonized data, instead of the ideal one."""
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
        quaternions = np.zeros((arr_size, 4))
        if isinstance(index, (slice, str)):
            with tqdm(total=arr_size) as progress_bar:
                for i, (pattern, quaternion) in enumerate(
                    ireadPattern(filename, index, poissonize)
                ):
                    arr[i] = pattern
                    quaternions[i] = quaternion
                    progress_bar.update(1)  # update progress
        else:
            # If only reading one pattern
            arr[0], quaternions[0] = next(ireadPattern(filename, index, poissonize))

        params = getParameters(filename)
        geom, distance, pixel_mask = params2extra_geom(params["geom"])
        beam = params2SimpleBeam(params["beam"])

        data_dict["img_array"] = arr
        data_dict["quaternions"] = quaternions
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
        method_desciption = "Written by SimEx-Lite"
        geom = extra_geom2params(
            data_dict["geom"], data_dict["distance"], data_dict["pixel_mask"]
        )
        beam = BeamData2params(data_dict["beam"])

        prepH5(filename)
        write_singfelDiffr(
            filename,
            arr_ideal=data_dict["img_array"],
            geom=geom,
            beam=beam,
            quaternions=data_dict["quaternions"],
            method_desciption=method_desciption,
            arr_poisson=arr_poisson,
        )

        if key is None:
            original_key = object.key
            key = original_key + "_to_SingfelFormat"
        return object.from_file(filename, cls, key)


def ireadPattern(filename, index=None, poissonize=True):
    """Iterator for reading diffraction patterns from a singfel file."""
    index = parseIndex(index)
    pattern_type = getPatternType(poissonize)
    with h5py.File(filename, "r") as h5:
        data_grp = h5["data"]
        data_list = list(data_grp)
        data_list.sort()
        indices = data_list[index]

        for i in indices:
            yield data_grp[i][pattern_type][...], data_grp[i]["angle"][...]


def getPatternType(poissonize: bool) -> str:
    """Get the pattern type for reading h5 files.

    Args:
        poissonize (bool): If it's True, the function returns thegroup name
        of the poissonized diffraction pattern, otherwise the ideal pattern.

    Returns:
        string: The group name of corresponding data.
    """
    if poissonize:
        pattern_type = "data"
    else:
        pattern_type = "diffr"
    return pattern_type


def getPatternShape(filename):
    """Get the shape of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, "r") as h5:
        group_name = list(h5["data"])[0]
        try:
            return h5["data"][group_name]["diffr"].shape
        except KeyError:
            return h5["data"][group_name]["data"].shape


def getPatternTotal(filename):
    """Get the total number of diffraction patterns in the hdf5 file"""
    with h5py.File(filename, "r") as h5:
        npattern = len(h5["data"])
    return npattern


def getParameters(filename):
    """Get a dictionary of the beam parameters and geometry parameters in a Singfel Diffr
    HDF5 file.
    """

    # Setup return dictionary.
    parameters_dict = {"beam": {}, "geom": {}}

    # Open file.
    with h5py.File(filename, "r") as h5:
        # Loop over entries in /params.
        for top_key in ["beam", "geom"]:
            # Loop over groups.
            for key, val in h5["params/%s" % (top_key)].items():
                # Insert into return dictionary.
                parameters_dict[top_key][key] = val[()]
    # Return.
    return parameters_dict


def params2extra_geom(file_geom):
    # The geometry dict from the file
    pixel_size = file_geom["pixelHeight"]
    mask = file_geom["mask"]
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
    distance = file_geom["detectorDist"]
    pixel_mask = file_geom["mask"]
    return geom, distance, pixel_mask


def params2SimpleBeam(file_beam):
    focus_area = file_beam["focusArea"]
    photon_energy = file_beam["photonEnergy"]
    beam = SimpleBeam(photon_energy=photon_energy, focus_area=focus_area)
    return beam


def extra_geom2params(geom: DetectorGeometryBase, distance, pixel_mask):
    if geom.n_modules != 1:
        raise ValueError("pysingfel can only deal with single-module geometry.")
    # extra_geom only deals with square pixel yet.
    pixel_size = geom.pixel_size
    geom_param = {
        "detectorDist": distance,
        "mask": pixel_mask,
        "pixelHeight": pixel_size,
        "pixelWidth": pixel_size,
    }
    return geom_param


def BeamData2params(beam: SimpleBeam):
    focus_area = beam.get_focus_area().magnitude
    photon_energy = beam.get_photon_energy().magnitude
    beam_param = {"focusArea": focus_area, "photonEnergy": photon_energy}
    return beam_param


def prepH5(filename):
    """
    Create output file, prepare top level groups, write metadata.
    """
    with h5py.File(filename, "w") as f:
        # Generate top level groups
        f.create_group("data")
        f.create_group("params")
        f.create_group("misc")
        f.create_group("info")

        # Write metadata
        # Package format version
        f.create_dataset(
            "info/package_version", data=np.string_("SimExLite" + SimExLite.__version__)
        )
        # Contact
        f.create_dataset(
            "info/contact",
            data=np.string_(
                "{} <{}>".format(SimExLite.__author__, SimExLite.__email__)
            ),
        )
        # Data Description
        f.create_dataset(
            "info/data_description",
            data=np.string_(
                "This dataset contains diffraction patterns written using SimEx singfelDiffr API."
            ),
        )
        # Data format version
        f.create_dataset("version", data=np.string_("0.2"))


def write_singfelDiffr(
    filename,
    arr_ideal,
    geom,
    beam,
    arr_poisson=None,
    quaternions=None,
    method_desciption="",
    pmi_file_list=None,
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
    prepH5(filename)
    # Method Description
    with h5py.File(filename, "a") as f:
        f.create_dataset("info/method_description", data=np.string_(method_desciption))
        # Flush to print it before tqdm
        print("Writing singfelDiffr data: diffr...", flush=True)
        for i, pattern_counts in enumerate(tqdm(arr_ideal)):
            group_name = "/data/" + "{0:07}".format(i + 1) + "/"
            f.create_dataset(group_name + "diffr", data=pattern_counts)
            # if pmi_file_list is not None:
            # __write_pmi_file_list(pmi_file_list, group_name, f, i)

        if arr_poisson is not None:
            print("Writing singfelDiffr data: data...", flush=True)
            for i, pattern_counts in enumerate(tqdm(arr_poisson)):
                group_name = "/data/" + "{0:07}".format(i + 1) + "/"
                f.create_dataset(group_name + "data", data=pattern_counts)

        if quaternions is not None:
            print("Writing singfelDiffr data: angle...", flush=True)
            for i, quaternion in enumerate(tqdm(quaternions)):
                group_name = "/data/" + "{0:07}".format(i + 1) + "/"
                f.create_dataset(group_name + "angle", data=quaternion)

        # Geometry
        f.create_dataset("params/geom/detectorDist", data=geom["detectorDist"])
        f.create_dataset("params/geom/pixelWidth", data=geom["pixelWidth"])
        f.create_dataset("params/geom/pixelHeight", data=geom["pixelHeight"])
        f.create_dataset("params/geom/mask", data=geom["mask"])

        # Beam
        f.create_dataset("params/beam/focusArea", data=beam["focusArea"])
        f.create_dataset("params/beam/photonEnergy", data=beam["photonEnergy"])


def __write_pmi_file_list(pmi_file_list, group_name, f, i):
    # Link history from input pmi file into output diffr file
    group_name_history = group_name + "history/parent/detail/"
    group_name_history = "history/parent/detail/"
    f[group_name + "/history/parent/parent"] = h5py.ExternalLink(
        pmi_file_list[i], "history/parent"
    )
    f[group_name_history + "data"] = h5py.ExternalLink(pmi_file_list[i], "data")
    f[group_name_history + "info"] = h5py.ExternalLink(pmi_file_list[i], "info")
    f[group_name_history + "misc"] = h5py.ExternalLink(pmi_file_list[i], "misc")
    f[group_name_history + "params"] = h5py.ExternalLink(pmi_file_list[i], "params")
    f[group_name_history + "version"] = h5py.ExternalLink(pmi_file_list[i], "version")
